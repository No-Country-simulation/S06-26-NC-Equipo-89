# Estado de implementación

Última actualización: junio 2026

Resumen del producto respecto al **brief del reto Feedback Classifier** y extensiones implementadas.  
ADRs: [adr/README.md](adr/README.md) · Índice docs: [README.md](README.md)

---

## Cumplimiento del brief (reto No-Country)

| Requerimiento | Estado | Implementación |
|---------------|--------|----------------|
| Carga manual o automática de feedback | Completo | CSV/JSON/Excel en dashboard; n8n → WhatsApp, Tally, Google Forms → `/ingest` |
| Clasificación: sentimiento, categoría, urgencia | Completo | LangGraph `classifier` → `feedback_clasificado` |
| Resumir mensajes | Completo | Campo `resumen` por clasificación |
| Detección de temas recurrentes | Completo | `pattern_detector` → `feedback_patrones` |
| Export CSV/JSON | Completo | Vista Exportar |
| Panel con insights | Completo | Dashboard v3: KPIs, sentimiento, urgencia, mensajes, patrones |
| NLP vía API (GPT/Gemini) | Completo | Gemini Flash-Lite + fallback Groq |
| Base relacional | Completo | PostgreSQL (Supabase) |
| Pipeline modular | Completo | LangGraph por nodos; FastAPI desacoplado del worker |
| Demo + documentación | Completo | Docker, samples, ADRs, guías E2E |

---

## Resumen técnico

| Área | Estado |
|------|--------|
| Pipeline LangGraph (6 nodos) | Completo |
| Fallback Groq (503/429) | Completo |
| n8n — 3 fuentes | Completo |
| RAG Copilot | Completo |
| Embeddings automáticos (worker) | Completo |
| Dashboard Streamlit v3 | Completo |
| Carga CSV bulk + JSON + Excel | Completo |
| Retries + reintento automático de `error` | Completo |
| Export + Copilot modal | Completo |
| Optimización LLM (fases A–D) | Completo |
| Producción single-tenant (007, CI, docker prod) | Completo |
| **Automejora acotada (008–010)** | Completo — [plan](plans/plan-clasificador-automejora.md) |
| Confianza + KPI alta confianza | Completo |
| Acciones sugeridas + alertas in-app | Completo |
| Revisión humana + few-shot dinámico | Completo |
| Taxonomía cerrada de categorías | Completo — [ADR-010](adr/ADR-010-taxonomia-y-estabilidad.md) |
| Consistency check (estabilidad) | Completo — manual + job semanal |
| Tests (`pytest`) | Completo (79+ tests) |

---

## Pipeline LangGraph (aplicado)

```
loader → classifier → pattern_detector → actions → metrics → persister
```

| Nodo | Función |
|------|---------|
| `loader` | Cola `pendiente` + reintento de `error` (SKIP LOCKED) |
| `classifier` | Sentimiento, urgencia, categorías, confianza, resumen |
| `pattern_detector` | Patrones del lote (TSV + LLM) |
| `actions` | Acciones sugeridas (urgente, revisión, patrón, oportunidad) |
| `metrics` | Agregados del tick (+ heartbeat si falla todo el lote) |
| `persister` | Supabase: clasificado, patrones, métricas, acciones |

Worker: ciclo cada `BATCH_INTERVAL_MINUTES` (default 5).

---

## Dashboard (aplicado)

| Vista | Contenido |
|-------|-----------|
| Vista General | KPIs, alertas, cola, sentimiento, calidad y estabilidad del clasificador |
| Acciones sugeridas | Bandeja de tareas del agente |
| Revisar clasificaciones | Confirmar / corregir baja confianza o inestabilidad |
| Sentimiento y Categorías | Gráficos |
| Alertas de Urgencia | Distribución y listado |
| Mensajes Clasificados | Detalle con confianza |
| Patrones Detectados | Último tick |
| Exportar / Carga | CSV/JSON out · CSV/JSON/Excel in |
| Copilot (sidebar) | Preguntas RAG sobre feedback |

Auto-refresh cola cada 30 s (toggle sidebar).

---

## Migraciones de base de datos

| Migración | Aplicar en Supabase | Contenido |
|-----------|---------------------|-----------|
| 006 | Si DB antigua | `confianza`, `error_mensaje` |
| 007 | Recomendado | CHECK enums, `tick_id`, índices |
| **008** | **Requerida para acciones** | `feedback_acciones`, `requiere_revision` |
| **009** | **Requerida para revisión** | `feedback_correcciones` |
| **010** | Para marcar inestables | `motivo_revision` (baja_confianza / inestabilidad) |

Archivos: [database/migrations/](database/migrations/) · Schema: [supabase_schema.sql](database/supabase_schema.sql)

---

## Extensiones automejora (Fases 1–4)

| Fase | Qué se aplicó |
|------|----------------|
| 1 | `CONFIDENCE_REVIEW_THRESHOLD`, KPI confianza, worker activity, requeue errores en loader |
| 2 | Migración 008, nodo `actions`, vistas Acciones + alertas, `health_banner` |
| 3 | Migración 009, API `PATCH /classifications`, vista Revisar, scripts export/eval |
| 4 | Taxonomía cerrada de categorías, `consistency_check.py` (manual + job semanal), migración 010, sección Estabilidad en dashboard |

Demo: [guides/demo-e2e-clasificador.md](guides/demo-e2e-clasificador.md)

---

## Matriz ADR

| ADR | Tema | Estado |
|-----|------|--------|
| 001 | Gemini Flash-Lite + Groq | OK |
| 002 | LangGraph (6 nodos) | OK |
| 003 | n8n normalización | OK |
| 004 | FastAPI ingesta | OK |
| 005 | Supabase + pgvector | OK |
| 006 | Micro-batching | OK |
| 007 | Dashboard Streamlit | OK |
| 008 | Copilot RAG | OK |
| 009 | Human-in-the-loop | OK |
| 010 | Taxonomía cerrada + estabilidad | OK |

---

## Pendiente / propuesta (no bloquea la demo)

| Tema | Notas |
|------|-------|
| Más fuentes de feedback | Propuesta: [futuro-ai-native.md](plans/futuro-ai-native.md) |
| Alertas Slack/email | In-app ya implementado |
| Multi-tenant + RLS | Single-tenant actual |
| LangChain Copilot | RAG directo implementado |

---

## Operación LLM

| Variable | Default | Notas |
|----------|---------|-------|
| `CONFIDENCE_REVIEW_THRESHOLD` | 0.7 | Revisión humana |
| `CLASSIFY_LLM_BATCH_SIZE` | 8 | Micro-batch |
| `GEMINI_CACHE_ENABLED` | true | Few-shot en caché |
| `GEMINI_CACHE_VERSION` | v3-taxonomia1 | Bump al editar prompts cacheados |
| `CONSISTENCY_CHECK_INTERVAL_DAYS` | 7 | Job estabilidad (0 = off) |
| `CONSISTENCY_CHECK_RUNS` | 3 | Runs por mensaje |
| `GROQ_API_KEY` | — | Fallback recomendado |

Reencolar manual (opcional): `cd backend && ../.venv/bin/python scripts/requeue_errors.py`

Aprendizaje tras correcciones: `export_fewshot_from_corrections.py` + bump `GEMINI_CACHE_VERSION` + restart worker.

Calidad y estabilidad: `eval_classification.py` (exactitud) y `consistency_check.py` (estabilidad) contra el golden set.

---

## Seguridad (resumen)

| Tema | Demo | Producción |
|------|------|------------|
| Secretos | `.env` gitignored | Secrets manager |
| Dashboard Supabase | service_role | read-only + proxy |
| API | `X-API-Key` | rate limit + CORS |
| CI | — | ruff + pytest + gitleaks |

Guías: [seguridad-y-secretos.md](guides/seguridad-y-secretos.md) · [runbook-produccion.md](guides/runbook-produccion.md)
