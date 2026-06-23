# Optimización LLM — Fase A (implementada)

> **Estado: IMPLEMENTADA** — junio 2026

Técnicas para reducir tokens de entrada sin recortar el texto del cliente ni las reglas de negocio.

## Cambios

### 1. Clasificador — system / user split

| Antes | Después |
|-------|---------|
| Prompt monolítico (`classification_v1.md`) repetido por mensaje | `classification_system_v2.md` en **system_instruction** |
| Instrucciones + `{texto}` en un solo string | **User message** = solo el feedback del cliente |

Archivos:
- `prompts/classification_system_v2.md`
- `backend/src/agent/nodes/classifier.py`
- `backend/src/tools/gemini_client.py` — `system_instruction` en `GenerateContentConfig`
- `backend/src/tools/groq_client.py` — mensaje `system` + `user` en fallback

**Calidad:** el texto del cliente va íntegro; el schema Pydantic (`FeedbackClassification`) sigue forzando la salida JSON.

### 2. Patrones — TSV compacto

| Antes | Después |
|-------|---------|
| `json.dumps(lista_clasificaciones)` | TSV con header (`llm_compact.py`) |
| Prompt largo en `pattern_summary_v1.md` | `pattern_summary_v2.md` |

Archivos:
- `backend/src/core/llm_compact.py` — `classifications_to_tsv()`
- `backend/src/agent/nodes/pattern_detector.py`

### 3. Carga centralizada de prompts

- `backend/src/core/prompt_loader.py` — resuelve `prompts/` desde la raíz del repo (Docker + local).

## Impacto estimado

| Nodo | Ahorro aprox. |
|------|----------------|
| Clasificador (por mensaje) | ~300–450 tokens de instrucciones ya no van en el user prompt |
| Patrones (por tick) | ~30–50% vs JSON con claves repetidas |

## Próximas fases

| Fase | Tema | Doc |
|------|------|-----|
| B | Context caching Gemini (tier pago) | — |
| C | Micro-batch ×8 | [`optimizacion-llm-microbatch.md`](optimizacion-llm-microbatch.md) |
| D | Métricas tokens/tick | log `classifier_done` |

## Tests

- `tests/unit/test_llm_compact.py`
- `tests/unit/test_classifier_prompt.py`
