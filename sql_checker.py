"""
sql_checker.py — analiza el contenido de un archivo .sql
y detecta sentencias DROP TABLE y CREATE TABLE.
"""
import re


def analizar_sql(contenido: str) -> tuple[bool, bool]:
    """
    Retorna (hasDrop, hasCreate).
    Ignora comentarios SQL para evitar falsos positivos.
    """
    limpio = _quitar_comentarios(contenido)

    has_drop   = bool(re.search(r'\bDROP\s+TABLE\b',   limpio, re.IGNORECASE))
    has_create = bool(re.search(r'\bCREATE\s+TABLE\b', limpio, re.IGNORECASE))

    return has_drop, has_create


def _quitar_comentarios(sql: str) -> str:
    """Elimina comentarios -- de línea y /* */ de bloque."""
    # Bloques /* ... */
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    # Líneas -- comentario
    sql = re.sub(r'--[^\n]*', '', sql)
    return sql
