"""Tests para parsers de carga manual del dashboard."""

import json

import pandas as pd
import pytest

from dashboard.components.loaders import (
    LoaderError,
    parse_csv,
    parse_json,
    parse_upload,
    to_csv_bytes,
)


def test_parse_csv_ok():
    raw = b"texto,fuente,external_id\nHola mundo,csv,id-1\n"
    df = parse_csv(raw)
    assert len(df) == 1
    assert df.iloc[0]["texto"] == "Hola mundo"
    assert df.iloc[0]["fuente"] == "csv"
    assert df.iloc[0]["external_id"] == "id-1"


def test_parse_csv_skips_empty_texto():
    raw = b"texto,fuente\n,csv\nValido,csv\n"
    df = parse_csv(raw)
    assert len(df) == 1
    assert df.iloc[0]["texto"] == "Valido"


def test_parse_csv_missing_texto_column():
    with pytest.raises(LoaderError, match="texto"):
        parse_csv(b"fuente\nwhatsapp\n")


def test_parse_json_array():
    raw = json.dumps(
        [{"texto": "Queja de envío", "fuente": "json", "external_id": "j-1"}]
    ).encode()
    df = parse_json(raw)
    assert len(df) == 1
    assert df.iloc[0]["external_id"] == "j-1"


def test_parse_json_single_object():
    raw = json.dumps({"texto": "Un solo mensaje"}).encode()
    df = parse_json(raw)
    assert len(df) == 1
    assert df.iloc[0]["fuente"] == "csv"


def test_parse_json_invalid():
    with pytest.raises(LoaderError):
        parse_json(b"{ no json")


def test_parse_upload_detects_csv():
    df, fmt = parse_upload("datos.csv", b"texto\nHola\n")
    assert fmt == "CSV"
    assert len(df) == 1


def test_to_csv_bytes_roundtrip():
    df = pd.DataFrame([{"texto": "A", "fuente": "csv", "external_id": "x-1"}])
    out = to_csv_bytes(df)
    assert b"texto" in out
    assert b"A" in out
