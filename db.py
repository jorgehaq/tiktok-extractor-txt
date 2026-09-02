"""Módulo de persistencia en SQLite para TikTok Extractor.

Desacoplado de `app.py` (Streamlit). Centraliza la inicialización de
base de datos y la inserción de videos procesados.

Funciones públicas:
    init_db(db_path="tiktok_knowledge.db") -> None
    persist_video(data: dict, db_path="tiktok_knowledge.db") -> int
"""

from __future__ import annotations

import sqlite3
from typing import Any

_DEFAULT_DB = "tiktok_knowledge.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    title TEXT,
    author TEXT,
    description TEXT,
    tags TEXT,
    transcript TEXT,
    main_category TEXT,
    keywords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def init_db(db_path: str = _DEFAULT_DB) -> None:
    """Crea (si no existe) la tabla ``videos`` en la base de datos.

    Args:
        db_path: Ruta al archivo SQLite. Por defecto ``tiktok_knowledge.db``.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(_CREATE_TABLE_SQL)


def persist_video(data: dict[str, Any], db_path: str = _DEFAULT_DB) -> int:
    """Inserta un video procesado en la tabla ``videos``.

    Args:
        data: Dict con las claves esperadas:
              ``url``, ``title``, ``author``, ``description``, ``tags``,
              ``transcript``, ``main_category``, ``keywords``.
              ``tags`` y ``keywords`` pueden ser listas (se join-ean con
              ``", "``) o strings.
        db_path: Ruta al archivo SQLite.

    Returns:
        ``id`` (int) del registro insertado.
    """
    tags = data.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)

    keywords = data.get("keywords", "")
    if isinstance(keywords, list):
        keywords = ", ".join(keywords)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO videos
                (url, title, author, description, tags, transcript,
                 main_category, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("url"),
                data.get("title"),
                data.get("author"),
                data.get("description"),
                tags,
                data.get("transcript"),
                data.get("main_category"),
                keywords,
            ),
        )
        return cursor.lastrowid
