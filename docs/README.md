# Documentación — Feedback Classifier

Documentación técnica del proyecto. Punto de entrada para evaluadores, desarrolladores y operadores.

**Inicio rápido del repositorio:** [README principal](../README.md)

---

## Rutas según tu rol

### Evaluador / revisor (bootcamp, PR, auditoría)

Recorrido recomendado (~15 min):

1. [estado-implementacion.md](estado-implementacion.md) — qué está implementado y qué queda pendiente
2. [adr/README.md](adr/README.md) — decisiones de arquitectura (el *por qué*)
3. [guides/n8n-e2e-checklist.md](guides/n8n-e2e-checklist.md) — cómo verificar el flujo completo
4. Código: `backend/src/agent/`, `dashboard/`, `n8n/`

### Desarrollador (clonar y levantar)

1. [README principal](../README.md) — instalación y variables de entorno
2. [database/supabase_schema.sql](database/supabase_schema.sql) — schema de base de datos
3. [guides/n8n-e2e-checklist.md](guides/n8n-e2e-checklist.md) — integración n8n
4. [adr/](adr/) — antes de proponer cambios de arquitectura

### Operador (configurar integraciones)

| Integración | Guía |
|-------------|------|
| n8n + FastAPI + worker | [guides/n8n-e2e-checklist.md](guides/n8n-e2e-checklist.md) |
| Tally | [guides/n8n-tally-webhook.md](guides/n8n-tally-webhook.md) |
| Google Forms (alternativa) | [guides/n8n-google-forms-apps-script.md](guides/n8n-google-forms-apps-script.md) |
| BI read-only | [guides/bi-readonly-setup.md](guides/bi-readonly-setup.md) |
| **Secretos y Git** | [guides/seguridad-y-secretos.md](guides/seguridad-y-secretos.md) |

---

## Etapas del proyecto

| Fase | Documentación | Estado |
|------|---------------|--------|
| **1. Arquitectura** | [adr/](adr/) | Completo (8 ADRs) |
| **2. Base de datos** | [database/](database/) | Schema + migraciones |
| **3. Ingestión** | ADR-003, ADR-004, [guides/](guides/) | n8n + FastAPI + carga manual |
| **4. Agente IA** | ADR-001, ADR-002, ADR-006, `prompts/` | LangGraph + optimización tokens (fases A–D) |
| **5. Dashboard** | ADR-007, [plans/plan-dashboard-ux-v3.md](plans/plan-dashboard-ux-v3.md) | v3 implementado |
| **6. Copilot RAG** | ADR-008 | Cohere + pgvector |

Detalle de implementación: [estado-implementacion.md](estado-implementacion.md)

---

## Contenido por carpeta

### `adr/` — Decisiones de arquitectura

Registro permanente de decisiones técnicas. **Empezar aquí** para entender el diseño del sistema.

→ [Índice de ADRs](adr/README.md)

### `database/` — Esquema y migraciones

| Archivo | Uso |
|---------|-----|
| [supabase_schema.sql](database/supabase_schema.sql) | Proyecto nuevo |
| [migrations/005_rag_copilot.sql](database/migrations/005_rag_copilot.sql) | Añadir RAG a DB existente |
| [migrations/006_schema_hardening.sql](database/migrations/006_schema_hardening.sql) | Hardening de tablas previas |

### `guides/` — Guías operativas

Procedimientos paso a paso para configurar y verificar el sistema en local o producción.

### `plans/` — Especificaciones de diseño (archivo)

| Plan | Estado |
|------|--------|
| [plan-dashboard-streamlit-v2.md](plans/plan-dashboard-streamlit-v2.md) | Superseded |
| [plan-dashboard-ux-v3.md](plans/plan-dashboard-ux-v3.md) | Implementado — ver `dashboard/` |
| [optimizacion-llm-fase-a.md](plans/optimizacion-llm-fase-a.md) | **Implementada** — system/user + TSV patrones |
| [optimizacion-llm-fase-b.md](plans/optimizacion-llm-fase-b.md) | **Implementada** — caché explícito Gemini + few-shot |
| [optimizacion-llm-microbatch.md](plans/optimizacion-llm-microbatch.md) | **Implementada** — micro-batch ×8 + métricas tokens |

Los planes documentan el *diseño previo* a la implementación. El código fuente es la referencia final.

### Optimización LLM (implementada)

| Fase | Doc | Técnica |
|------|-----|---------|
| A | [optimizacion-llm-fase-a.md](plans/optimizacion-llm-fase-a.md) | System/user split + TSV patrones |
| B | [optimizacion-llm-fase-b.md](plans/optimizacion-llm-fase-b.md) | Caché explícito Gemini + few-shot |
| C | [optimizacion-llm-microbatch.md](plans/optimizacion-llm-microbatch.md) | Micro-batch ×8 + fallback 1-a-1 |
| D | (logs `classifier_done`) | Métricas tokens + `cached_content_tokens` |

---

## Estructura

```
docs/
├── README.md                 ← este índice
├── estado-implementacion.md  ← estado actual del producto
├── adr/                      ← decisiones de arquitectura
├── database/                 ← SQL
├── guides/                   ← how-to
└── plans/                    ← specs históricas
```
