"""Tests de serialización compacta para prompts LLM."""

from src.core.llm_compact import classifications_to_tsv


def test_classifications_to_tsv_header_and_rows():
    items = [
        {
            "external_id": "ext-1",
            "classification": {
                "sentimiento": "Negativo",
                "urgencia": "Alta",
                "categorias": ["App", "Pagos"],
                "confianza": 0.91,
                "resumen": "Falla al pagar",
            },
        },
        {
            "external_id": "ext-2",
            "classification": {
                "sentimiento": "Positivo",
                "urgencia": "Baja",
                "categorias": ["Soporte"],
                "confianza": 0.88,
                "resumen": "Excelente atención",
            },
        },
    ]
    tsv = classifications_to_tsv(items)
    lines = tsv.splitlines()
    assert lines[0] == "external_id\tsentimiento\turgencia\tcategorias\tconfianza\tresumen"
    assert "ext-1\tNegativo\tAlta\tApp,Pagos\t0.91\tFalla al pagar" in lines[1]
    assert "ext-2\tPositivo\tBaja\tSoporte\t0.88\tExcelente atención" in lines[2]


def test_classifications_to_tsv_escapes_newlines():
    items = [
        {
            "external_id": "x",
            "classification": {
                "sentimiento": "Neutral",
                "urgencia": "Media",
                "categorias": [],
                "confianza": 0.5,
                "resumen": "Línea uno\nLínea dos",
            },
        }
    ]
    tsv = classifications_to_tsv(items)
    assert "\n" not in tsv.splitlines()[1]  # una sola fila de datos
    assert "Línea uno Línea dos" in tsv
