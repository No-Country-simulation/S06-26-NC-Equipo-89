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
| Carga manual CSV/JSON/Excel | Completo (aliases `content`/`source`; Excel multi-hoja) |
| Retries ADR-006 | Completo (+ backoff classifier, `requeue_errors.py`) |
| Export dashboard | Completo |
| Tests unitarios | Completo (55+ tests) |
| Docker full stack | Completo |
| Health cola dashboard | Completo (pendientes + errores) |
| **Optimización tokens LLM (Fase A)** | Completo (system/user + TSV patrones) |
| **Caché explícito Gemini (Fase B)** | Completo (few-shot + warm-up worker) |
| **Micro-batch LLM (Fase C)** | Completo (×8 adaptativo + fallback 1-a-1) |
| **Métricas tokens/tick (Fase D)** | Completo (logs structlog + cached_tokens) |
| BI read-only | Documentado (`guides/bi-readonly-setup.md`) |
| Guía seguridad / secretos | Completo (`guides/seguridad-y-secretos.md`) |
| Índice docs | Completo (`README.md`) |
| **Producción single-tenant** | Completo (migración 007, recovery, tick_id, CI, docker prod) |
| Runbook producción | Completo (`guides/runbook-produccion.md`) |
| Proxy auth dashboard | Documentado (`guides/dashboard-proxy-auth.md`) |
| CI GitHub Actions | Completo (`.github/workflows/ci.yml`) |

## Matriz ADR

| ADR | Tema | Estado | Notas |
|-----|------|--------|-------|
| 001 | Gemini Flash-Lite | OK | + fallback Groq (`llm_client.py`) |
| 002 | LangGraph | OK | 5 nodos |
| 003 | n8n normalización | OK | Workflow `Feedback-Ingest-3-fuentes-a-FastAPI.json`; API_KEY vía `$env` |
| 004 | FastAPI ingesta | OK | + /copilot (ADR-008) |
| 005 | Supabase | OK | pgvector implementado |
| 006 | Micro-batching | OK | SKIP LOCKED cola DB + micro-batch LLM |
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

- Multi-tenant + RLS (producción actual: single-tenant, sin policies)
- Alertas automáticas urgencia alta (email/Slack)
- LangChain para Copilot (se usó RAG directo)
- API LLM centralizada (escala futura)

## Producción single-tenant

| Ítem | Estado |
|------|--------|
| Migración 007 (CHECK, tick_id, índices) | OK |
| Recovery `procesando` (worker + script) | OK |
| `tick_id` en persister + dashboard | OK |
| Dashboard read-only (`DASHBOARD_READONLY`) | OK |
| API hardening (rate limit, CORS, `/health/deep`) | OK |
| CI (ruff + pytest + gitleaks) | OK |
| `docker-compose.prod.yml` | OK |
| Runbook | OK |

Checklist go-live: [README.md](../README.md#checklist-go-live) · Plan: [plans/plan-produccion-single-tenant.md](plans/plan-produccion-single-tenant.md)

## Operación LLM

| Variable | Valor recomendado | Notas |
|----------|-------------------|-------|
| `CLASSIFY_LLM_BATCH_SIZE` | 8 | `1` desactiva micro-batch |
| `CLASSIFY_MAX_TEXT_CHARS` | 300 | Aísla mensajes largos |
| `GEMINI_CONCURRENCY` | 3 | Paralelismo de chunks |
| `GEMINI_CACHE_ENABLED` | true | Caché explícito (worker warm-up) |
| `GEMINI_CACHE_VERSION` | v2-fewshot1 | Bump al cambiar prompts |
| `CLASSIFY_RETRY_ATTEMPTS` | 3 | Backoff antes de error |
| `GROQ_API_KEY` | Recomendado | Fallback 503/429 |

Reencolar errores: `cd backend && python scripts/requeue_errors.py`

Documentación: [plans/optimizacion-llm-fase-a.md](plans/optimizacion-llm-fase-a.md) · [fase-b](plans/optimizacion-llm-fase-b.md) · [microbatch](plans/optimizacion-llm-microbatch.md)

## Seguridad

| Tema | Estado demo | Producción |
|------|-------------|------------|
| `.env` en Git | Ignorado (`.gitignore`) | Secrets manager |
| `API_KEY` en código | Default vacío | ≥32 chars + `ENV=production` |
| Supabase dashboard | `service_role` | `dashboard_readonly` + flag |
| Workflows n8n | `$env.API_KEY` | Sin claves en JSON |
| Datasets locales | `Data/` gitignored | — |
| CI | — | ruff + pytest + gitleaks |
| Dashboard expuesto | `:8501` público | Proxy TLS + Basic Auth |

Guía: [guides/seguridad-y-secretos.md](guides/seguridad-y-secretos.md) · [runbook-produccion.md](guides/runbook-produccion.md)
