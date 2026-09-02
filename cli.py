"""Entrypoint headless (CLI) para TikTok Extractor.

Reemplaza a ``app.py`` (Streamlit) en contextos no-UI y sirve como target
para el wrapper ``run-tiktok-extract.mjs`` del Tool Centralizer.

Uso típico::

    python3 cli.py --url <tiktok_url> --json --model tiny --timeout 60

Contrato de salida JSON (``--json``)::

    {
      "url": "...",
      "title": "...",
      "author": "...",
      "description": "...",
      "tags": ["...", "..."],
      "transcript": "...",
      "classification": {
        "categoria_principal": "...",
        "tipo_contenido": "...",
        "palabras_clave": ["...", "..."]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import tempfile
from typing import Any

from classifier import clasificar_con_ia
from extractor import get_full_metadata
from transcriber import get_audio_and_transcribe, load_whisper_model

# Timeout por defecto (segundos). Whisper + yt-dlp pueden tardar.
_DEFAULT_TIMEOUT = 60
_DEFAULT_MODEL = "tiny"


class TimeoutError(Exception):
    """Excepción interna para control de timeout dentro del pipeline."""


def _load_env() -> None:
    """Carga variables de entorno desde ``.env`` si existe (compatibilidad)."""
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()


def _build_error(message: str) -> dict[str, Any]:
    """Construye un dict de error estandarizado para stdout."""
    return {"ok": False, "error": message}


def run_pipeline(
    url: str,
    model_name: str = _DEFAULT_MODEL,
    timeout: int = _DEFAULT_TIMEOUT,
    persist: bool = True,
    db_path: str = "tiktok_knowledge.db",
) -> dict[str, Any]:
    """Ejecuta el pipeline completo de extracción + transcripción + clasificación.

    Args:
        url: URL del video de TikTok.
        model_name: Modelo Whisper (``tiny``, ``small``, ``base`` ...).
        timeout: Tiempo máximo (segundos) antes de abortar. ``0`` desactiva.
        persist: Si ``True``, inserta el resultado en SQLite.
        db_path: Ruta al archivo SQLite.

    Returns:
        dict con el contrato JSON definido en el módulo docstring.
    """
    from db import init_db, persist_video  # import diferido para evitar ciclo

    # ---- Control de timeout ----
    timed_out = False

    def _timeout_handler(signum, frame):
        nonlocal timed_out
        timed_out = True
        raise TimeoutError(
            f"timeout excedido ({timeout}s)"
        )

    if timeout > 0:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    try:
        model = load_whisper_model(model_name)

        with tempfile.TemporaryDirectory() as tmp:
            meta = get_full_metadata(url, tmp)

            titulo = meta.get("title", "Sin Título")
            descripcion = meta.get("description", "Sin Descripción")
            autor = meta.get("uploader", "Autor Desconocido")
            tags = meta.get("tags", [])
            tikwm_audio_url = meta.get("tikwm_audio_url")

            transcripcion = get_audio_and_transcribe(
                url, tmp, model, tikwm_audio_url
            )

        clasificacion = clasificar_con_ia(titulo, descripcion, transcripcion)

        result: dict[str, Any] = {
            "url": url,
            "title": titulo,
            "author": autor,
            "description": descripcion,
            "tags": tags,
            "transcript": transcripcion,
            "classification": {
                "categoria_principal": clasificacion["categoria_principal"],
                "tipo_contenido": clasificacion["tipo_contenido"],
                "palabras_clave": clasificacion["palabras_clave"],
            },
        }

        if persist:
            init_db(db_path)
            persist_video(
                {
                    "url": url,
                    "title": titulo,
                    "author": autor,
                    "description": descripcion,
                    "tags": tags,
                    "transcript": transcripcion,
                    "main_category": clasificacion["categoria_principal"],
                    "keywords": clasificacion["palabras_clave"],
                },
                db_path=db_path,
            )

        return result

    except TimeoutError as e:
        return _build_error(str(e))
    except Exception as e:
        return _build_error(f"pipeline error: {e}")
    finally:
        if timeout > 0:
            signal.alarm(0)  # cancelar alarma pendiente


def main(argv: list[str] | None = None) -> int:
    """Parsea argumentos y ejecuta el pipeline. Imprime JSON a stdout.

    Args:
        argv: Lista de argumentos (por defecto ``sys.argv[1:]``).

    Returns:
        Código de salida: ``0`` éxito, ``1`` error/timeout.
    """
    _load_env()

    parser = argparse.ArgumentParser(
        prog="cli",
        description="TikTok Extractor — pipeline headless (extrae, transcribe, clasifica).",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL canónica del video de TikTok.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Imprimir resultado como JSON estructurado a stdout.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Ruta de salida para escribir el JSON (por defecto: stdout).",
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "small", "base"],
        default=_DEFAULT_MODEL,
        help="Modelo Whisper a usar (default: tiny).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=_DEFAULT_TIMEOUT,
        help="Timeout máximo en segundos (default: 60, 0 = sin límite).",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        default=False,
        help="No guardar el resultado en SQLite.",
    )

    args = parser.parse_args(argv)

    result = run_pipeline(
        url=args.url,
        model_name=args.model,
        timeout=args.timeout,
        persist=not args.no_persist,
    )

    if not args.as_json:
        # Modo legado compacto (solo título y transcript abreviado)
        print(f"Título: {result.get('title', 'N/A')}")
        transcript = result.get("transcript", "")
        print(f"Transcript: {transcript[:200]}{'...' if len(transcript) > 200 else ''}")
        return 0 if "error" not in result else 1

    # Modo JSON estructurado
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
    else:
        print(output)

    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
