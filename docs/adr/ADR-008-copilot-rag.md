# ADR-008 — Copilot RAG vía FastAPI

**Fecha:** 17 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** RAG | Copilot | Cohere | Gemini

## Contexto

Preguntas en lenguaje natural sobre feedback clasificado. Originalmente planificado como "Next" con LangChain.

## Decisión

- **Cohere** `embed-multilingual-v3.0` (1024 dims) para embeddings
- **Job desacoplado** `embed_job.py` — 3x/día, solo filas con `embedding IS NULL`
- **`POST /copilot/ask`** en FastAPI — claves IA solo en backend
- Dashboard Copilot usa httpx → FastAPI; KPIs siguen ADR-007 (Supabase directo)

## Flujo

```
Pregunta → Cohere embed query → match_feedback (pgvector) → Gemini respuesta
```

## Implementación

- [`backend/src/api/routes/copilot.py`](../../backend/src/api/routes/copilot.py)
- [`backend/embed_job.py`](../../backend/embed_job.py)
- [`dashboard/components/copilot.py`](../../dashboard/components/copilot.py)
- [`prompts/copilot_v1.md`](../../prompts/copilot_v1.md)
