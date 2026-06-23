"""Carga de prompts desde el directorio compartido del repo."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


def load_prompt(filename: str, *, fallback: str = "") -> str:
    """Lee un archivo de prompt; retorna fallback si no existe."""
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback
