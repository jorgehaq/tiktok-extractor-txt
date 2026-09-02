"""Módulo de clasificación de contenido TikTok vía DeepSeek.

Desacoplado de `app.py` (Streamlit). Retorna un dict estructurado con
las claves ``categoria_principal``, ``tipo_contenido`` y ``palabras_clave``.

Funciones públicas:
    clasificar_con_ia(titulo, descripcion, transcripcion) -> dict
"""

from __future__ import annotations

import json
import os

import requests

_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
_MODEL = "deepseek-v4-flash"

_DEFAULT_FALLBACK = {
    "categoria_principal": "Otro",
    "tipo_contenido": "Noticia",
    "palabras_clave": ["error_falta_api_key"],
}

_CONNECTION_FALLBACK = {
    "categoria_principal": "Otro",
    "tipo_contenido": "Noticia",
    "palabras_clave": ["error_conexion_deepseek"],
}

_CATEGORIAS_VALIDAS = [
    "Tecnología",
    "Productividad",
    "Tutoriales",
    "Ocio",
    "Finanzas",
    "Otro",
]

_TIPOS_VALIDOS = [
    "Tip/Truco",
    "Reflexión",
    "Noticia",
    "Comedia",
    "Review",
]


def clasificar_con_ia(
    titulo: str,
    descripcion: str,
    transcripcion: str,
) -> dict:
    """Clasifica contenido de TikTok usando DeepSeek.

    Construye un prompt estricto que pide un JSON con la estructura::

        {
          "categoria_principal": "...",
          "tipo_contenido": "...",
          "palabras_clave": ["...", "..."]
        }

    Args:
        titulo: Título del video.
        descripcion: Descripción original del video.
        transcripcion: Texto transcrito del audio.

    Returns:
        dict con las tres claves estructuradas. En caso de error (API key
        faltante o fallo de conexión) devuelve un dict de fallback con
        ``palabras_clave`` indicando la causa.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return dict(_DEFAULT_FALLBACK)

    prompt = f"""
    Analiza este contenido de TikTok y devuelve ÚNICAMENTE un objeto JSON válido.
    Título: {titulo}
    Descripción: {descripcion}
    Transcripción: {transcripcion}

    Estructura estricta del JSON de salida:
    {{
        "categoria_principal": "Elige una de: [{', '.join(_CATEGORIAS_VALIDAS)}]",
        "tipo_contenido": "Elige una de: [{', '.join(_TIPOS_VALIDOS)}]",
        "palabras_clave": ["keyword1", "keyword2", "keyword3"]
    }}
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": _MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            _DEEPSEEK_URL, headers=headers, json=payload
        )
        response.raise_for_status()
        data = response.json()

        ai_response_text = data["choices"][0]["message"]["content"].strip()
        parsed = json.loads(ai_response_text)

        # Normalizar/garantizar estructura mínima
        return {
            "categoria_principal": parsed.get(
                "categoria_principal", _DEFAULT_FALLBACK["categoria_principal"]
            ),
            "tipo_contenido": parsed.get(
                "tipo_contenido", _DEFAULT_FALLBACK["tipo_contenido"]
            ),
            "palabras_clave": parsed.get("palabras_clave", []),
        }
    except Exception:
        return dict(_CONNECTION_FALLBACK)
