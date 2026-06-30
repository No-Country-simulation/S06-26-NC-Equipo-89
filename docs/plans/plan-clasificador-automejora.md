# Plan — Clasificador con automejora acotada

Extensiones implementadas sobre el MVP del reto **Feedback Classifier** (clasificar, resumir, detectar patrones). Complementa los requerimientos funcionales del brief con confianza, acciones concretas y revisión humana.

## Objetivo del brief (referencia)

Agente IA para clasificar, resumir y detectar patrones en feedback de WhatsApp, formularios y encuestas, con panel simple y export.

## Fases implementadas

| Fase | Meta | Estado |
|------|------|--------|
| **1** | Clasificador confiable (confianza visible, worker autónomo, reintento de errores) | Implementado |
| **2** | Acciones sugeridas + alertas in-app | Implementado |
| **3** | Revisión humana + few-shot dinámico + eval de calidad | Implementado |
| **4** | Taxonomía cerrada + medición de estabilidad (consistency check) | Implementado |

## Fase 1 — Base

- Umbral `CONFIDENCE_REVIEW_THRESHOLD` (default 0.7)
- KPI **Alta confianza** en dashboard
- Worker reintenta mensajes en `error` automáticamente (loader)
- Visibilidad de ciclos del agente (`worker_activity`)
- Checklist demo: [demo-e2e-clasificador.md](../guides/demo-e2e-clasificador.md)

## Fase 2 — Acciones y alertas

- Tabla `feedback_acciones` — migración **008**
- Nodo `actions` en LangGraph (6 nodos en total)
- Vistas **Acciones sugeridas** y **alertas** en Vista General
- Reglas: urgente, revisión, patrón alto impacto, oportunidad positiva
- Banners en `health_banner` cuando hay acciones o revisiones pendientes

## Fase 3 — Revisión humana y mejora por ejemplos

- Tabla `feedback_correcciones` — migración **009**
- API `PATCH /classifications/{id}` y `PATCH .../confirm`
- Vista **Revisar clasificaciones**
- Scripts: `export_fewshot_from_corrections.py`, `eval_classification.py`
- Few-shot dinámico: `prompts/classification_fewshot_dynamic.md` (caché Gemini)

Ver [ADR-009](../adr/ADR-009-human-in-the-loop.md).

## Fase 4 — Taxonomía cerrada y estabilidad

- **Taxonomía cerrada** de 10 categorías en `classification_system_v2.md` (el modelo elige solo de la lista; sin sinónimos). Subió la exactitud de categorías de 40% a 70% y el exact match total de 30% a 60%.
- **Consistency check** (`consistency_check.py`): clasifica el golden set N veces y mide estabilidad (% de runs coincidentes) además de exactitud.
- **Ejecución manual y automática** (job semanal en el worker, `CONSISTENCY_CHECK_INTERVAL_DAYS`).
- Dashboard: sección **Estabilidad del clasificador** en Vista General.
- Mensajes inestables (`--mark-unstable`) → revisión humana con `motivo_revision = 'inestabilidad'` (migración **010**).

Ver [ADR-010](../adr/ADR-010-taxonomia-y-estabilidad.md).

## Migraciones SQL a aplicar

| # | Archivo | Contenido |
|---|---------|-----------|
| 007 | `007_production_hardening.sql` | CHECK, tick_id, índices (si no aplicada) |
| 008 | `008_acciones_y_revision.sql` | `feedback_acciones`, flags revisión en clasificado |
| 009 | `009_correcciones_humanas.sql` | `feedback_correcciones` |
| 010 | `010_motivo_revision.sql` | `motivo_revision` (baja_confianza / inestabilidad) |

Schema completo: [database/supabase_schema.sql](../database/supabase_schema.sql)

## Criterios de éxito (demo)

| Criterio | Evidencia |
|----------|-----------|
| Clasificación autónoma | Worker + mensajes clasificados |
| Confianza visible | KPI + badges «revisar» |
| Patrones | Vista Patrones detectados |
| Acciones priorizadas | Vista Acciones sugeridas |
| Alertas | Vista General |
| Revisión humana | Vista Revisar + API |
| Calidad medible | Eval + Estabilidad en Vista General |
| Export | Vista Exportar CSV/JSON |

## Propuesta post-simulación

Expansión a más fuentes de feedback para enriquecer decisiones: [futuro-ai-native.md](futuro-ai-native.md) (propuesta de expansión, no entregable del reto).
