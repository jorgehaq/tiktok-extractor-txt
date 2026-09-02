"""Módulo de transcripción de audio de TikTok vía Whisper.

Desacoplado de `app.py` (Streamlit). Soporta seleccionar el modelo
Whisper (``tiny``, ``small``, ``base`` ...) mediante ``model_name``.

Funciones públicas:
    get_audio_and_transcribe(url, tmp_dir, model, tikwm_audio_url=None) -> str
    load_whisper_model(model_name="tiny") -> whisper.WhisperModel
"""

from __future__ import annotations

import os
import subprocess
import sys

import requests

# -- 0. AÑADIR FFMPEG LOCAL AL PATH --
_LOCAL_BIN = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin"))
if _LOCAL_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _LOCAL_BIN + os.pathsep + os.environ.get("PATH", "")


def load_whisper_model(model_name: str = "tiny"):
    """Carga y devuelve un modelo Whisper en CPU.

    Args:
        model_name: Tamaño del modelo (``tiny``, ``small``, ``base`` ...).
                    Por defecto ``tiny`` para minimizar tiempo de carga y
                    uso de memoria en modo headless.

    Returns:
        Instancia de ``whisper.WhisperModel``.
    """
    import whisper

    return whisper.load_model(model_name, device="cpu")


def _download_audio_tikwm(tikwm_audio_url: str, tmp_dir: str) -> str | None:
    """Descarga audio desde la URL provista por TikWM.

    Returns:
        Ruta local al archivo ``.mp3`` o ``None`` si falla la descarga.
    """
    try:
        r = requests.get(tikwm_audio_url, timeout=20)
        if r.status_code == 200:
            audio_path = os.path.join(tmp_dir, "temp_audio.mp3")
            with open(audio_path, "wb") as f:
                f.write(r.content)
            if os.path.exists(audio_path):
                return audio_path
    except Exception as e:
        print(f"TikWM audio download failed: {e}", file=sys.stderr)
    return None


def _download_audio_yt_dlp(url: str, tmp_dir: str) -> str | None:
    """Descarga y extrae audio vía yt-dlp (mp3).

    Returns:
        Ruta local al archivo ``temp_audio.mp3`` o ``None`` si falla.
    """
    use_cookies = os.path.exists("cookies.txt")
    cmd_base = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--extractor-args",
        "tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com",
        "-f",
        "b[vcodec^=h264]/b[vcodec^=avc1]/b",
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "-o",
        os.path.join(tmp_dir, "temp_audio.%(ext)s"),
    ]

    success = False
    if use_cookies:
        cmd = cmd_base + ["--cookies", "cookies.txt", url]
        if subprocess.run(cmd).returncode == 0:
            success = True

    if not success:
        cmd = cmd_base + [url]
        if subprocess.run(cmd).returncode == 0:
            success = True

    audio_path = os.path.join(tmp_dir, "temp_audio.mp3")
    return audio_path if os.path.exists(audio_path) else None


def get_audio_and_transcribe(
    url: str,
    tmp_dir: str,
    model,
    tikwm_audio_url: str | None = None,
) -> str:
    """Descarga el audio de un TikTok y lo transcribe con Whisper.

    Prioridad de fuente de audio:
      1. URL directa provista por TikWM (``tikwm_audio_url``).
      2. Descarga vía yt-dlp (con/sin cookies).

    Args:
        url: URL canónica del video.
        tmp_dir: Directorio temporal para artefactos de audio.
        model: Instancia de Whisper cargada (ver ``load_whisper_model``).
        tikwm_audio_url: URL opcional de audio devuelta por TikWM.

    Returns:
        Texto transcrito (string). Cadena vacía ``""`` si no se pudo
        obtener ni transcribir el audio.
    """
    audio_path: str | None = None

    # 1) Fuente TikWM
    if tikwm_audio_url:
        audio_path = _download_audio_tikwm(tikwm_audio_url, tmp_dir)

    # 2) Fallback yt-dlp
    if audio_path is None:
        audio_path = _download_audio_yt_dlp(url, tmp_dir)

    if audio_path is None:
        return ""

    result = model.transcribe(audio_path, fp16=False)
    return result.get("text", "").strip()
