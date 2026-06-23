"""Parsers de archivos para carga manual (CSV, JSON, Excel)."""

from __future__ import annotations

import io
import json
import uuid
from typing import Any

import pandas as pd

from shared.ingest_fields import SOURCE_COLUMN_ALIASES, TEXT_COLUMN_ALIASES

REQUIRED_COLUMN = "texto"
OPTIONAL_COLUMNS = ("fuente", "external_id")
MAX_ROWS_WARNING = 500


class LoaderError(ValueError):
    """Error de validación al parsear un archivo de carga."""


def _records_from_json(raw: bytes) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise LoaderError(f"JSON inválido: {e}") from e

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise LoaderError("El JSON debe ser un objeto o un array de objetos.")


def _column_lookup(df: pd.DataFrame) -> dict[str, str]:
    """Mapa nombre en minúsculas → nombre real en el DataFrame."""
    return {str(c).strip().lower(): str(c) for c in df.columns}


def _sheet_has_text_column(df: pd.DataFrame) -> bool:
    """True si la hoja tiene columna texto o alias reconocido."""
    lookup = _column_lookup(_apply_column_aliases(df))
    return "texto" in lookup


def _apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza columnas de datasets externos (content/source) al esquema de ingesta.
    Prioriza `content` sobre `content_sanitized` para el texto original.
    """
    df = df.copy()
    lookup = _column_lookup(df)
    rename: dict[str, str] = {}

    if "texto" not in lookup:
        for alias in TEXT_COLUMN_ALIASES:
            if alias in lookup:
                rename[lookup[alias]] = "texto"
                break

    if "fuente" not in lookup:
        for alias in SOURCE_COLUMN_ALIASES:
            if alias in lookup:
                rename[lookup[alias]] = "fuente"
                break

    if rename:
        df = df.rename(columns=rename)
    return df


def _normalize_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        raise LoaderError("El archivo no contiene registros.")

    df = pd.DataFrame(records)
    df = _apply_column_aliases(df)
    if REQUIRED_COLUMN not in df.columns:
        raise LoaderError(
            f"Falta la columna obligatoria `{REQUIRED_COLUMN}`. "
            f"Usá `texto` o alias como `content`. "
            f"Columnas encontradas: {', '.join(df.columns.astype(str))}"
        )

    df[REQUIRED_COLUMN] = df[REQUIRED_COLUMN].astype(str).str.strip()
    df = df[
        df[REQUIRED_COLUMN].notna()
        & (df[REQUIRED_COLUMN] != "")
        & (df[REQUIRED_COLUMN].str.lower() != "nan")
    ].copy()

    if df.empty:
        raise LoaderError("No hay filas con texto no vacío.")

    if "fuente" not in df.columns:
        df["fuente"] = "csv"
    else:
        df["fuente"] = df["fuente"].fillna("csv").astype(str).str.strip()
        df.loc[df["fuente"] == "", "fuente"] = "csv"

    if "external_id" not in df.columns:
        df["external_id"] = [f"upload-{uuid.uuid4()}" for _ in range(len(df))]
    else:
        df["external_id"] = df["external_id"].fillna("").astype(str).str.strip()
        missing = df["external_id"] == ""
        df.loc[missing, "external_id"] = [f"upload-{uuid.uuid4()}" for _ in range(missing.sum())]

    return df[[REQUIRED_COLUMN, *OPTIONAL_COLUMNS]]


def parse_csv(raw: bytes) -> pd.DataFrame:
    """Parsea CSV con columna texto obligatoria."""
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise LoaderError(f"No se pudo leer el CSV: {e}") from e
    return _normalize_records(df.to_dict(orient="records"))


def parse_json(raw: bytes) -> pd.DataFrame:
    """Parsea JSON (objeto único o array)."""
    records = _records_from_json(raw)
    return _normalize_records(records)


def parse_excel(raw: bytes, filename: str) -> pd.DataFrame:
    """Parsea XLS/XLSX — usa la primera hoja con columna texto/content."""
    engine = "xlrd" if filename.lower().endswith(".xls") else "openpyxl"
    try:
        xl = pd.ExcelFile(io.BytesIO(raw), engine=engine)
    except Exception as e:
        raise LoaderError(f"No se pudo leer el Excel: {e}") from e

    last_error: LoaderError | None = None
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        if df.empty or not _sheet_has_text_column(df):
            continue
        try:
            return _normalize_records(df.to_dict(orient="records"))
        except LoaderError as e:
            last_error = e

    if last_error:
        raise last_error
    raise LoaderError(
        "Ninguna hoja del Excel tiene columna texto/content. "
        f"Hojas encontradas: {', '.join(xl.sheet_names)}"
    )


def parse_upload(filename: str, raw: bytes) -> tuple[pd.DataFrame, str]:
    """
    Auto-detecta formato por extensión.

    Returns:
        (dataframe normalizado, nombre del formato)
    """
    lower = filename.lower()
    if lower.endswith(".csv"):
        return parse_csv(raw), "CSV"
    if lower.endswith(".json"):
        return parse_json(raw), "JSON"
    if lower.endswith((".xlsx", ".xls")):
        return parse_excel(raw, filename), "Excel"
    raise LoaderError("Formato no soportado. Usa CSV, JSON, XLS o XLSX.")


def count_skipped_rows(filename: str, raw: bytes) -> int:
    """Cuenta filas descartadas por texto vacío antes de normalizar."""
    lower = filename.lower()
    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
            records = df.to_dict(orient="records")
        elif lower.endswith(".json"):
            records = _records_from_json(raw)
        elif lower.endswith((".xlsx", ".xls")):
            engine = "xlrd" if lower.endswith(".xls") else "openpyxl"
            xl = pd.ExcelFile(io.BytesIO(raw), engine=engine)
            records = []
            for sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet)
                if df.empty or not _sheet_has_text_column(df):
                    continue
                records = df.to_dict(orient="records")
                break
        else:
            return 0
    except Exception:
        return 0

    if not records:
        return 0
    df_raw = pd.DataFrame(records)
    df_raw = _apply_column_aliases(df_raw)
    if REQUIRED_COLUMN not in df_raw.columns:
        return 0
    total = len(df_raw)
    valid = df_raw[REQUIRED_COLUMN].astype(str).str.strip()
    valid = valid.notna() & (valid != "") & (valid.str.lower() != "nan")
    return total - int(valid.sum())


def sample_csv_template() -> bytes:
    """CSV de ejemplo para descarga."""
    sample = "texto,fuente,external_id\nLa app falla al pagar,csv,ejemplo-001\nExcelente atención,csv,ejemplo-002\n"
    return sample.encode("utf-8")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convierte DataFrame normalizado a CSV para POST /ingest/csv."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
