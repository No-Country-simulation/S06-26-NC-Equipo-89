"""Utilidades para serializar vectores pgvector."""


def vector_to_pg(vector: list[float]) -> str:
    """Convierte embedding a literal compatible con columna vector de Postgres."""
    return "[" + ",".join(str(v) for v in vector) + "]"
