# Optimización LLM — Fases A–D (implementadas)

> **Estado: IMPLEMENTADA** — junio 2026

Cuatro fases de reducción de tokens y mejora de rendimiento sin cambiar la lógica de negocio del agente.

---

## Fase A — System / user split + TSV compacto

### Clasificador: separar instrucciones del texto del cliente

| Antes | Después |
|-------|---------|
| Prompt monolítico repetido por mensaje | `classification_system_v2.md` en `system_instruction` |
| Instrucciones + `{texto}` en un solo string | User message = solo el feedback del cliente |

Archivos: `prompts/classification_system_v2.md` · `backend/src/agent/nodes/classifier.py` · `backend/src/tools/gemini_client.py` · `backend/src/tools/groq_client.py`

### Patrones: TSV en lugar de JSON

| Antes | Después |
|-------|---------|
| `json.dumps(lista_clasificaciones)` | TSV con header (`llm_compact.py`) |
| Prompt largo `pattern_summary_v1.md` | `pattern_summary_v2.md` |

Ahorro: ~30–50% vs JSON con claves repetidas. Tests: `test_llm_compact.py`, `test_classifier_prompt.py`.

---

## Fase B — Caché explícito Gemini

El worker precarga el system prompt + few-shot examples en la API de Google al arrancar.

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GEMINI_CACHE_ENABLED` | `true` | Activa caché explícita |
| `GEMINI_CACHE_TTL_SECONDS` | `3600` | TTL del recurso cacheado |
| `GEMINI_CACHE_VERSION` | `v2-fewshot1` | Cambiar al editar prompts → nuevo caché |

**Beneficio:** ~75–90% descuento en tokens del prefijo cacheado.  
**Fallback:** si falla → `system_instruction` clásico (Fase A).

Para rotar prompts: cambiar `GEMINI_CACHE_VERSION` en `.env` y reiniciar worker.

Archivos: `backend/src/core/gemini_cache.py` · `backend/worker.py` · `prompts/classification_fewshot_v1.md`  
Tests: `test_gemini_cache.py`

---

## Fase C — Micro-batch ×8

Agrupa mensajes cortos en lotes para reducir llamadas al LLM.

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CLASSIFY_LLM_BATCH_SIZE` | 8 | Mensajes por llamada; `1` = modo 1-a-1 |
| `CLASSIFY_MAX_TEXT_CHARS` | 300 | Textos más largos van solos |
| `GEMINI_CONCURRENCY` | 3 | Chunks en paralelo |

```
50 mensajes → ~7 llamadas LLM  (vs 50 en modo 1-a-1)
             → fallback 1-a-1 si falla el lote
```

Archivos: `backend/src/agent/nodes/classifier.py` · `backend/src/core/llm_compact.py` · `backend/src/schemas/results.py`

---

## Fase D — Métricas de tokens por tick

Cada tick loguea en `classifier_done`: `llm_calls`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_content_tokens`, `providers`.

Fuente: `usage_metadata` (Gemini) / `usage` (Groq).

---

## Resumen de impacto

| Fase | Técnica | Ahorro |
|------|---------|--------|
| A | System/user split | ~300–450 tokens de instrucciones por mensaje |
| A | TSV patrones | ~30–50% vs JSON |
| B | Caché Gemini | ~75–90% en tokens del prefijo |
| C | Micro-batch ×8 | ~85% menos llamadas LLM (50 msgs → 7 calls) |
