"""Serialización compacta de datos para prompts LLM (menos tokens)."""

from __future__ import annotations

import json


def _escape_tsv(value: str) -> str:
    """Evita saltos de línea y tabs dentro de celdas TSV."""
    return (value or "").replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def classifications_to_tsv(processed_items: list[dict]) -> str:
    """
    Convierte clasificaciones del batch a TSV para el nodo de patrones.

    Columnas: external_id, sentimiento, urgencia, categorias, confianza, resumen
    """
    header = "external_id\tsentimiento\turgencia\tcategorias\tconfianza\tresumen"
    rows = [header]
    for item in processed_items:
        c = item.get("classification") or {}
        ext_id = _escape_tsv(str(item.get("external_id", "")))
        sent = _escape_tsv(str(c.get("sentimiento", "")))
        urg = _escape_tsv(str(c.get("urgencia", "")))
        cats = c.get("categorias") or []
        cat_str = _escape_tsv(",".join(cats) if isinstance(cats, list) else str(cats))
        conf = c.get("confianza")
        conf_str = "" if conf is None else str(conf)
        resumen = _escape_tsv(str(c.get("resumen", "")))
        rows.append(f"{ext_id}\t{sent}\t{urg}\t{cat_str}\t{conf_str}\t{resumen}")
    return "\n".join(rows)


def chunk_for_llm_batch(
    items: list[dict],
    batch_size: int,
    max_text_chars: int,
) -> list[list[dict]]:
    """
    Agrupa mensajes para micro-batch LLM.

    Mensajes largos (> max_text_chars) van solos para no degradar calidad.
    """
    if batch_size <= 1:
        return [[item] for item in items]

    chunks: list[list[dict]] = []
    current: list[dict] = []

    for item in items:
        texto = str(item.get("texto") or "")
        if len(texto) > max_text_chars:
            if current:
                chunks.append(current)
                current = []
            chunks.append([item])
            continue

        current.append(item)
        if len(current) >= batch_size:
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)
    return chunks


def build_batch_classify_prompt(chunk: list[dict]) -> str:
    """Prompt user compacto: array JSON mínimo + instrucción de salida."""
    payload = [
        {"external_id": item.get("external_id", ""), "texto": item.get("texto", "")}
        for item in chunk
    ]
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        "Clasifica cada elemento del array. Devuelve JSON con lista 'resultados'; "
        "cada item debe incluir external_id y todos los campos de clasificación.\n"
        f"{body}"
    )
