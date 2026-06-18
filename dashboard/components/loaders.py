"""Parsers de archivos para carga manual (CSV, JSON, Excel)."""

from __future__ import annotations

import io
import json
import uuid
from typing import Any

import pandas as pd

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


def _normalize_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        raise LoaderError("El archivo no contiene registros.")

    df = pd.DataFrame(records)
    if REQUIRED_COLUMN not in df.columns:
        raise LoaderError(
            f"Falta la columna obligatoria `{REQUIRED_COLUMN}`. "
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
    """Parsea XLS/XLSX — primera hoja."""
    engine = "xlrd" if filename.lower().endswith(".xls") else "openpyxl"
    try:
        df = pd.read_excel(io.BytesIO(raw), engine=engine)
    except Exception as e:
        raise LoaderError(f"No se pudo leer el Excel: {e}") from e
    return _normalize_records(df.to_dict(orient="records"))


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
            df = pd.read_excel(io.BytesIO(raw), engine=engine)
            records = df.to_dict(orient="records")
        else:
            return 0
    except Exception:
        return 0

    if not records:
        return 0
    df_raw = pd.DataFrame(records)
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
