# ADR-005 — Supabase como base de datos

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Base de Datos | Infraestructura

## Decisión

Supabase (PostgreSQL + JSONB + pgvector) para texto crudo, datos estructurados y embeddings RAG.

## Tablas

| Tabla | Quién escribe | Quién lee |
|-------|---------------|-----------|
| `feedback_raw` | FastAPI | Agente |
| `feedback_clasificado` | Agente, embed_job | Streamlit, BI, Copilot |
| `feedback_patrones` | Agente | Streamlit, BI |
| `feedback_metricas` | Agente | Streamlit, BI |

## Implementación

- [`docs/database/supabase_schema.sql`](../database/supabase_schema.sql)
- [`docs/database/migrations/`](../database/migrations/)
- Embeddings: worker (`run_embed_indexing`) + [`backend/scripts/backfill_embeddings.py`](../../backend/scripts/backfill_embeddings.py)
