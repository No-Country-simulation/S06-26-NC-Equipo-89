"""Constantes y helpers compartidos entre API /ingest/csv y parsers del dashboard."""

TEXT_FIELD_ALIASES = (
    "texto",
    "content",
    "message",
    "comentario",
    "comment",
    "text",
    "content_sanitized",
)
SOURCE_FIELD_ALIASES = ("fuente", "source")

# Alias sin el nombre canónico (para renombrado de columnas en pandas)
TEXT_COLUMN_ALIASES = TEXT_FIELD_ALIASES[1:]
SOURCE_COLUMN_ALIASES = SOURCE_FIELD_ALIASES[1:]


def pick_field(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    """Obtiene el primer valor no vacío según alias (case-insensitive)."""
    lower_map = {k.strip().lower(): (v or "") for k, v in row.items()}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias].strip()
    return ""
