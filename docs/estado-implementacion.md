# Estado de implementación vs plan original

Última actualización: junio 2026

## Resumen

| Área | Estado |
|------|--------|
| Pipeline LangGraph | Completo |
| n8n 3 fuentes | Completo (webhooks WhatsApp/Tally/Forms) |
| RAG Copilot | Completo (adelantado) |
| CSV manual | Completo |
| Retries ADR-006 | Completo |
| Export dashboard | Completo |
| Tests | Completo |
| Docker full stack | Completo |
| BI read-only | Documentado |

## Matriz ADR

| ADR | Tema | Estado | Notas |
|-----|------|--------|-------|
| 001 | Gemini Flash-Lite | OK | Sin groq_client |
| 002 | LangGraph | OK | 5 nodos |
| 003 | n8n normalización | OK | Webhooks + CSV Streamlit; Forms vía Apps Script |
| 004 | FastAPI ingesta | OK | + /copilot (ADR-008) |
| 005 | Supabase | OK | pgvector implementado |
| 006 | Micro-batching | OK | SKIP LOCKED + retries |
| 007 | Streamlit + BI | OK | Export + carga CSV |
| 008 | Copilot RAG | OK | Cohere + FastAPI |

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
