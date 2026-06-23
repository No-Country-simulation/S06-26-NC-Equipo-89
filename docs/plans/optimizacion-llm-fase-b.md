# Optimización LLM — Fase B (implementada)

> **Estado: IMPLEMENTADA** — junio 2026

Caché explícito de contexto Gemini para el clasificador: system prompt + few-shot examples precargados en la API de Google.

## Qué hace

1. Al arrancar el **worker**, crea o reutiliza un `CachedContent` en Gemini.
2. El contenido cacheado incluye:
   - `classification_system_v2.md` (system instruction)
   - `classification_fewshot_v1.md` (~25 ejemplos, >6k caracteres → umbral mínimo de caché)
3. Cada clasificación envía solo el **texto variable** (mensaje o micro-batch JSON).
4. Los logs reportan `cached_content_token_count` por llamada.

## Variables

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GEMINI_CACHE_ENABLED` | `true` | Activa caché explícita |
| `GEMINI_CACHE_TTL_SECONDS` | `3600` | TTL del recurso cacheado |
| `GEMINI_CACHE_VERSION` | `v2-fewshot1` | Cambiar al actualizar prompts → nuevo caché |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Modelo del caché y generate |

## Archivos

| Archivo | Rol |
|---------|-----|
| `backend/src/core/gemini_cache.py` | Crear/reutilizar caché por `display_name` |
| `backend/src/tools/gemini_client.py` | `cached_content` en `GenerateContentConfig` |
| `prompts/classification_fewshot_v1.md` | Ejemplos few-shot para umbral + calidad |
| `backend/worker.py` | `warm_classification_cache()` al inicio |

## Beneficio

- **~75–90% descuento** en tokens del prefijo cacheado (tarifa Gemini cached vs input).
- Few-shot en caché mejora consistencia en jerga LATAM sin sumar tokens variables por call.

## Fallback

- Si falla crear caché → `system_instruction` clásico (Fase A).
- Si Gemini falla → Groq sin caché (comportamiento previo).

## Rotar prompts

Cambiar `GEMINI_CACHE_VERSION` en `.env` (ej. `v2-fewshot2`) para forzar nuevo caché tras editar few-shot o system.

## Tests

- `tests/unit/test_gemini_cache.py`

## Referencias

- [Gemini context caching](https://ai.google.dev/gemini-api/docs/caching)
- Fase A: [`optimizacion-llm-fase-a.md`](optimizacion-llm-fase-a.md)
- Fase C: [`optimizacion-llm-microbatch.md`](optimizacion-llm-microbatch.md)
