# Optimización LLM — micro-batch (Fase C)

> **Estado: IMPLEMENTADA** — junio 2026  
> Ver también: [`optimizacion-llm-fase-a.md`](optimizacion-llm-fase-a.md)

## Comportamiento

El clasificador agrupa mensajes cortos en **micro-lotes** (`CLASSIFY_LLM_BATCH_SIZE`, default **8**) y envía **una llamada LLM por lote**.

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CLASSIFY_LLM_BATCH_SIZE` | 8 | Mensajes por llamada; `1` = modo 1-a-1 |
| `CLASSIFY_MAX_TEXT_CHARS` | 300 | Textos más largos van solos (1-a-1) |
| `GEMINI_CONCURRENCY` | 3 | Chunks procesados en paralelo |

## Flujo

```
50 mensajes DB
  → chunk_for_llm_batch (8 + aislar largos)
  → ~7 llamadas LLM (vs 50 en 1-a-1)
  → validación external_id
  → fallback 1-a-1 si falla el lote
```

## Archivos

- `backend/src/agent/nodes/classifier.py` — `classify_batch_chunk`, métricas por tick
- `backend/src/core/llm_compact.py` — `chunk_for_llm_batch`, `build_batch_classify_prompt`
- `backend/src/schemas/results.py` — `BatchClassificationResult`

## Métricas (Fase D)

Cada tick loguea en `classifier_done`:

- `llm_calls`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `providers`

Fuente: `usage_metadata` (Gemini) / `usage` (Groq).

## Calidad

- Texto del cliente **íntegro** en el array de entrada
- Validación de IDs antes de persistir
- Fallback automático a 1-a-1 por chunk fallido

## Desactivar micro-batch

```env
CLASSIFY_LLM_BATCH_SIZE=1
```
