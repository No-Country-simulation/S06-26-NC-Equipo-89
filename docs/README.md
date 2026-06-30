# Documentación — Feedback Classifier

> Punto de entrada para evaluadores, desarrolladores y operadores.  
> README del repositorio: [../README.md](../README.md)

---

## Por dónde empezar

| Si sos… | Empezá por |
|---------|------------|
| **Evaluador del reto** | [estado-implementacion.md](estado-implementacion.md) → [adr/README.md](adr/README.md) |
| **Dev que clona el repo** | [../README.md](../README.md) (instalación) → [database/supabase_schema.sql](database/supabase_schema.sql) |
| **Demo / presentación** | [guides/demo-e2e-clasificador.md](guides/demo-e2e-clasificador.md) |
| **Configurar n8n** | [guides/n8n-e2e-checklist.md](guides/n8n-e2e-checklist.md) |

---

## Estado del proyecto

**[estado-implementacion.md](estado-implementacion.md)**  
Cumplimiento del brief del reto + extensiones implementadas. Punto de partida para evaluar el proyecto.

---

## Decisiones de arquitectura

**[adr/README.md](adr/README.md)** — 10 ADRs que documentan el *por qué* de cada decisión técnica.

| ADR | Decisión |
|-----|----------|
| [ADR-001](adr/ADR-001-gemini-flash-lite.md) | Gemini Flash-Lite como motor NLP + fallback Groq |
| [ADR-002](adr/ADR-002-langgraph.md) | LangGraph — pipeline de 6 nodos |
| [ADR-003](adr/ADR-003-n8n-normalizacion.md) | n8n como capa de normalización (3 fuentes) |
| [ADR-004](adr/ADR-004-fastapi-ingesta.md) | FastAPI como API de ingesta |
| [ADR-005](adr/ADR-005-supabase.md) | Supabase (PostgreSQL + pgvector) |
| [ADR-006](adr/ADR-006-micro-batching.md) | Micro-batching y reintentos |
| [ADR-007](adr/ADR-007-streamlit-dashboard.md) | Dashboard Streamlit v3 |
| [ADR-008](adr/ADR-008-copilot-rag.md) | Copilot RAG (Cohere + pgvector) |
| [ADR-009](adr/ADR-009-human-in-the-loop.md) | Human-in-the-loop y few-shot dinámico |
| [ADR-010](adr/ADR-010-taxonomia-y-estabilidad.md) | Taxonomía cerrada de categorías y medición de estabilidad |

---

## Base de datos

| Archivo | Uso |
|---------|-----|
| [database/supabase_schema.sql](database/supabase_schema.sql) | Schema completo (proyecto nuevo) |
| [database/migrations/006_schema_hardening.sql](database/migrations/006_schema_hardening.sql) | Hardening tablas existentes |
| [database/migrations/007_production_hardening.sql](database/migrations/007_production_hardening.sql) | CHECK enums, `tick_id`, índices |
| [database/migrations/008_acciones_y_revision.sql](database/migrations/008_acciones_y_revision.sql) | Acciones sugeridas + flags revisión |
| [database/migrations/009_correcciones_humanas.sql](database/migrations/009_correcciones_humanas.sql) | Correcciones humanas (few-shot dinámico) |
| [database/migrations/010_motivo_revision.sql](database/migrations/010_motivo_revision.sql) | `motivo_revision` (baja confianza / inestabilidad) |

---

## Guías operativas

| Guía | Para qué |
|------|----------|
| [guides/demo-e2e-clasificador.md](guides/demo-e2e-clasificador.md) | Checklist de demo de las 3 fases |
| [guides/entornos-dev-y-prod.md](guides/entornos-dev-y-prod.md) | Diferencias entre local y producción |
| [guides/n8n-e2e-checklist.md](guides/n8n-e2e-checklist.md) | Flujo completo n8n → FastAPI → worker |
| [guides/n8n-tally-webhook.md](guides/n8n-tally-webhook.md) | Conectar Tally como fuente |
| [guides/n8n-google-forms-apps-script.md](guides/n8n-google-forms-apps-script.md) | Google Forms sin OAuth |
| [guides/seguridad-y-secretos.md](guides/seguridad-y-secretos.md) | Qué no subir a Git, manejo de `.env` |
| [guides/bi-readonly-setup.md](guides/bi-readonly-setup.md) | Dashboard en modo read-only |
| [guides/dashboard-proxy-auth.md](guides/dashboard-proxy-auth.md) | Proxy TLS delante del dashboard |
| [guides/runbook-produccion.md](guides/runbook-produccion.md) | Operación en producción |

---

## Planes y propuestas

| Documento | Estado |
|-----------|--------|
| [plans/plan-clasificador-automejora.md](plans/plan-clasificador-automejora.md) | **Implementado** — confianza, acciones, revisión humana, taxonomía y estabilidad |
| [plans/optimizacion-llm.md](plans/optimizacion-llm.md) | **Implementado** — fases A–D de reducción de tokens |
| [plans/plan-dashboard-ux-v3.md](plans/plan-dashboard-ux-v3.md) | **Implementado** — diseño del dashboard v3 |
| [plans/plan-produccion-single-tenant.md](plans/plan-produccion-single-tenant.md) | **Implementado** — hardening, CI, docker prod |
| [plans/futuro-ai-native.md](plans/futuro-ai-native.md) | **Propuesta** — conectar más fuentes post-simulación |

---

## Estructura

```
docs/
├── README.md                    ← este índice
├── estado-implementacion.md     ← qué está hecho y cumplimiento del brief
├── adr/                         ← 10 decisiones de arquitectura
├── database/                    ← schema SQL + migraciones 006–009
├── guides/                      ← procedimientos operativos
└── plans/                       ← diseños implementados y propuestas futuras
```
