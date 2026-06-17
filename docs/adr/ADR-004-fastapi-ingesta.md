# ADR-004 — FastAPI como capa de entrada HTTP

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado (ampliado por ADR-008)  
**Etiquetas:** Backend | API | Infraestructura

## Decisión

FastAPI recibe, valida con Pydantic y persiste en Supabase. No clasifica ni invoca al agente LangGraph.

## Endpoints

| Endpoint | Responsabilidad |
|----------|-----------------|
| `POST /ingest` | JSON de n8n → `feedback_raw` |
| `POST /ingest/csv` | CSV de Streamlit → `feedback_raw` |
| `POST /copilot/ask` | Copilot RAG (ver ADR-008) |

## Lo que FastAPI NO hace

- No llama al agente LangGraph directamente
- No expone consultas de KPIs (Streamlit lee Supabase directo)

## Implementación

- [`backend/src/api/routes/ingest.py`](../../backend/src/api/routes/ingest.py)
