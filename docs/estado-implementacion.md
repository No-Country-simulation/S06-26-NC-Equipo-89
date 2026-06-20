# Estado de implementación

Última actualización: junio 2026

Este documento resume el **estado actual del producto** respecto al plan original.  
Para decisiones de diseño, ver [ADRs](adr/README.md). Para navegar toda la documentación, ver [docs/README.md](README.md).

## Resumen

| Área | Estado |
|------|--------|
| Pipeline LangGraph | Completo |
| Fallback Groq (503/429) | Completo |
| n8n 3 fuentes | Completo (WhatsApp Trigger, Tally, Google Sheets) |
| RAG Copilot | Completo |
| Embeddings en worker | Completo (automático tras cada tick) |
| Dashboard v3 Streamlit | Completo (mensajes clasificados, Copilot modal, dark mode) |
| Carga manual CSV/JSON/Excel | Completo |
| Retries ADR-006 | Completo |
| Export dashboard | Completo |
| Tests unitarios | Completo |
| Docker full stack | Completo |
| BI read-only | Documentado (`guides/bi-readonly-setup.md`) |
| Índice docs | Completo (`README.md`) |

## Matriz ADR

| ADR | Tema | Estado | Notas |
|-----|------|--------|-------|
| 001 | Gemini Flash-Lite | OK | + fallback Groq (`llm_client.py`) |
| 002 | LangGraph | OK | 5 nodos |
| 003 | n8n normalización | OK | Workflow `Feedback-Ingest-3-fuentes-a-FastAPI.json`; API_KEY vía `$env` |
| 004 | FastAPI ingesta | OK | + /copilot (ADR-008) |
| 005 | Supabase | OK | pgvector implementado |
| 006 | Micro-batching | OK | SKIP LOCKED + retries |
| 007 | Streamlit + BI | OK | Dashboard v3 + export + carga archivos + bandeja clasificados |
| 008 | Copilot RAG | OK | Cohere + FastAPI; texto vía Gemini/Groq |

## Schema: simplificaciones MVP

| Plan original | Implementado |
|---------------|--------------|
| `payload` JSONB en raw | `texto` TEXT + `metadata` JSONB |
| `categoria` singular | `categorias` JSONB array |
| Métricas desglosadas | `datos_metricas` JSONB blob |
| `lote_id` en tablas | No (timestamp en `created_at`) |

## Pendiente (Later)

- Multi-tenant
- Alertas automáticas urgencia alta (email/Slack)
- LangChain para Copilot (se usó RAG directo)
- API LLM centralizada (escala futura)
