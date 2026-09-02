"""Módulo de extracción de metadatos de TikTok.

Desacoplado de `app.py` (Streamlit). Usa yt-dlp como subprocess y, como
fallback, la API pública de TikWM cuando yt-dlp no puede atravesar el
bloqueo de IP (403).

Funciones públicas:
    get_full_metadata(url, tmp_dir) -> dict
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import requests

# -- 0. AÑADIR FFMPEG LOCAL AL PATH --
_LOCAL_BIN = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin"))
if _LOCAL_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _LOCAL_BIN + os.pathsep + os.environ.get("PATH", "")


def _run_yt_dlp(url: str, tmp_dir: str, use_cookies: bool) -> dict | None:
    """Ejecuta yt-dlp y devuelve el JSON parseado o None si falla."""
    cmd_base = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--extractor-args",
        "tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com",
        "--no-playlist",
        "--dump-json",
        "--quiet",
        "-o",
        os.path.join(tmp_dir, "%(id)s.%(ext)s"),
    ]

    cmd = cmd_base + (["--cookies", "cookies.txt"] if use_cookies else []) + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout.strip().splitlines()[-1])
        except Exception:
            return None
    return None


def _fallback_tikwm(url: str) -> dict | None:
    """Fallback a la API pública de TikWM cuando yt-dlp falla."""
    try:
        r = requests.get(
            f"https://www.tikwm.com/api/?url={url}", timeout=10
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("code") == 0 and "data" in res:
                data = res["data"]
                title_desc = data.get("title", "")
                tags = [
                    t.replace("#", "")
                    for t in title_desc.split()
                    if t.startswith("#")
                ]
                return {
                    "title": title_desc,
                    "description": (
                        " ".join(data.get("content_desc", []))
                        if data.get("content_desc")
                        else title_desc
                    ),
                    "uploader": data.get("author", {}).get(
                        "unique_id", "Autor Desconocido"
                    ),
                    "tags": tags,
                    "tikwm_audio_url": data.get("music"),
                }
    except Exception as e:
        print(f"Fallback TikWM failed: {e}", file=sys.stderr)
    return None


def get_full_metadata(url: str, tmp_dir: str) -> dict:
    """Extrae metadatos completos de un video de TikTok.

    Estrategia:
      1. yt-dlp con cookies (si existe ``cookies.txt``).
      2. yt-dlp sin cookies.
      3. Fallback a API TikWM.

    Args:
        url: URL canónica del video de TikTok.
        tmp_dir: Directorio temporal donde yt-dlp puede volcar artefactos.

    Returns:
        dict con al menos las claves ``title``, ``description``, ``uploader``,
        ``tags`` y opcionalmente ``tikwm_audio_url`` (usado por el transcriptor).
        Dict vacío ``{}`` si ninguna estrategia funciona.
    """
    use_cookies = os.path.exists("cookies.txt")

    # 1) Con cookies
    if use_cookies:
        meta = _run_yt_dlp(url, tmp_dir, use_cookies=True)
        if meta:
            return meta

    # 2) Sin cookies
    meta = _run_yt_dlp(url, tmp_dir, use_cookies=False)
    if meta:
        return meta

    # 3) Fallback TikWM
    meta = _fallback_tikwm(url)
    if meta:
        return meta

    return {}
