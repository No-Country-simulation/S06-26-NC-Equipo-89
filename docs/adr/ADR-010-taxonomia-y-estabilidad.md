# ADR-010 — Taxonomía cerrada de categorías y medición de estabilidad

**Fecha:** junio 2026  
**Estado:** Aceptado  
**Etiquetas:** LLM | Calidad | Evaluación

## Contexto

El clasificador devolvía `categorias` como tags de texto libre (`"tags relevantes"`). Esto causaba dos problemas medibles contra el golden set:

1. **Baja exactitud de categorías (40%)** — el modelo generaba sinónimos y variantes ("Pago" vs "Pagos", "Portal", "Error Técnico", "Variedad de Opciones") que no coincidían con el set esperado.
2. **Inestabilidad** — el mismo mensaje producía categorías distintas entre ejecuciones repetidas, sin forma de detectarlo.

El `eval_classification.py` existente medía exactitud con **una sola** ejecución, por lo que no detectaba inestabilidad (un modelo puede acertar por azar y ser inconsistente).

## Decisión

### 1. Taxonomía cerrada de categorías

`prompts/classification_system_v2.md` ahora define una **lista cerrada** de categorías; el modelo debe elegir solo de ella y no inventar sinónimos:

```
App · Pagos · Facturación · Atención al Cliente · Logística
Producto · Cuenta · Sitio Web · Error Técnico · Precios
```

El golden set (`tests/fixtures/golden_classifications.json`) y los ejemplos few-shot (`classification_fewshot_v1.md`) se alinearon a esta taxonomía.

### 2. Medición de estabilidad (consistency check)

Nuevo script `backend/scripts/consistency_check.py` que clasifica cada mensaje del golden set **N veces** (default 3) y reporta:

- **Estabilidad por campo** — % de runs que coinciden entre sí
- **Exactitud por campo** — coincidencia con el golden set
- **Confianza** promedio / min / max
- **Mensajes inestables** — estabilidad < `CONSISTENCY_CHECK_STABILITY_THRESHOLD` (default 0.70)

Modos de ejecución:

| Modo | Disparo |
|------|---------|
| Manual | `python scripts/consistency_check.py --runs 3 --save-metrics` |
| Automático | Job en `worker.py` cada `CONSISTENCY_CHECK_INTERVAL_DAYS` (default 7; 0 = off) |

Resultados se guardan en `feedback_metricas` (`tipo: consistency_run`) y se visualizan en el dashboard (sección **Estabilidad del clasificador**). Con `--mark-unstable`, los mensajes inestables se marcan para revisión humana (`motivo_revision = 'inestabilidad'`, migración 010).

## Resultados

Exactitud contra el golden set tras la taxonomía cerrada (fallback Groq, sin few-shot cacheado):

| Campo | Antes | Después |
|-------|-------|---------|
| Exact match total | 30% | 60% |
| Categorías | 40% | 70% |
| Sentimiento | 90% | 100% |
| Estabilidad promedio | — | 93.3% |

## Implementación

- [prompts/classification_system_v2.md](../../prompts/classification_system_v2.md) — taxonomía cerrada
- [backend/scripts/consistency_check.py](../../backend/scripts/consistency_check.py)
- [backend/worker.py](../../backend/worker.py) — `consistency_job()`
- [dashboard/components/metricas.py](../../dashboard/components/metricas.py) — sección Estabilidad
- [docs/database/migrations/010_motivo_revision.sql](../database/migrations/010_motivo_revision.sql)

## Consecuencias

- Cambiar la taxonomía o los ejemplos requiere bump de `GEMINI_CACHE_VERSION` (actual: `v3-taxonomia1`).
- El consistency check consume N× llamadas LLM; por eso es semanal/manual, no por cada tick.
- Complementa a [ADR-009](ADR-009-human-in-the-loop.md): la revisión humana ahora recibe candidatos por baja confianza **y** por inestabilidad.
