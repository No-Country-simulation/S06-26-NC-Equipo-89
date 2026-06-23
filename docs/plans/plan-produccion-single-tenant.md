# Plan de mejora a producción (single-tenant)

> Documento persistido del plan de endurecimiento. Estado de implementación: ver [estado-implementacion.md](../estado-implementacion.md).

## Contexto

Pipeline completo: n8n → FastAPI → `feedback_raw` → worker LangGraph → tablas derivadas → dashboard/Copilot.

Producción **single-tenant** con dashboard **solo interno** (sin multi-tenant ni RLS por `org_id`).

## Fases implementadas

| Fase | Contenido | Artefactos |
|------|-----------|------------|
| 1 — BD | CHECK enums, `tick_id`, índices, recovery `procesando`, UPSERT clasificado | `007_production_hardening.sql`, `queue_maintenance.py`, `persister.py` |
| 2 — Seguridad | API_KEY ≥32, read-only dashboard, proxy auth | `bi-readonly-setup.md`, `dashboard-proxy-auth.md`, `config.py` |
| 3 — CI | ruff + pytest + gitleaks | `.github/workflows/ci.yml` |
| 4 — Deploy | docker-compose prod, healthchecks | `docker-compose.prod.yml`, `.env.production.example` |
| 5 — Operación | runbook, `/health/deep`, rate limit | `runbook-produccion.md`, `main.py`, `rate_limit.py` |

## Checklist go-live

1. Migración 007 aplicada en Supabase prod
2. `API_KEY` rotada (`openssl rand -hex 32`)
3. Dashboard con usuario read-only + proxy auth
4. CI verde en `main`
5. Worker + recovery script probados con lote de 50 mensajes
6. n8n activo con URL HTTPS de producción
7. Backup Supabase verificado
8. Equipo conoce runbook

## Fuera de scope

- Multi-tenant `org_id` + RLS
- Login de usuarios en Streamlit
- Alertas email/Slack automáticas
- Particionado de tablas o cola externa (SQS/Redis)

## Referencias

- [Runbook producción](../guides/runbook-produccion.md)
- [Seguridad y secretos](../guides/seguridad-y-secretos.md)
- [Proxy dashboard](../guides/dashboard-proxy-auth.md)
- [BI read-only](../guides/bi-readonly-setup.md)
