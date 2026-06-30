# Demo E2E — Clasificador con automejora acotada

Checklist para demostrar las 4 fases del roadmap en la simulación.

## Prerrequisitos

1. Migraciones aplicadas en Supabase (en orden): 007, 008, 009, 010
2. Stack levantado: `docker compose up -d --build` o servicios locales
3. `.env` con `CONFIDENCE_REVIEW_THRESHOLD=0.7`, `API_KEY`, LLM keys
4. Comando Python local: usar `../.venv/bin/python` (no `python`)

## Fase 1 — Clasificador confiable

- [ ] Subir CSV de prueba (`samples/plantilla_feedback.csv` o `Data/`)
- [ ] Worker procesa cola (barra de estado: «Agente corrió»)
- [ ] Dashboard muestra KPI **Alta confianza** (%)
- [ ] Mensajes en **Mensajes Clasificados** con badge de confianza

## Fase 2 — Acciones y alertas

- [ ] Tras un ciclo, aparecen ítems en **Acciones sugeridas**
- [ ] Vista General muestra **alertas in-app** (urgencia, revisión, etc.)
- [ ] Banner indica acciones pendientes si las hay
- [ ] Último ciclo muestra «Acciones generadas» > 0 (si aplica)

## Fase 3 — Humano en el loop

- [ ] Mensajes con confianza baja en **Revisar clasificaciones**
- [ ] **Confirmar** o **Corregir** vía FastAPI (`PATCH /classifications/...`)
- [ ] `cd backend && ../.venv/bin/python scripts/export_fewshot_from_corrections.py`
- [ ] Reiniciar worker tras bump de `GEMINI_CACHE_VERSION`
- [ ] (Opcional) `../.venv/bin/python scripts/eval_classification.py --save-metrics` → KPI calidad

## Fase 4 — Taxonomía y estabilidad

- [ ] Categorías acotadas a la taxonomía cerrada (`classification_system_v2.md`)
- [ ] `cd backend && ../.venv/bin/python scripts/consistency_check.py --runs 3 --save-metrics`
- [ ] Dashboard → Vista General → sección **Estabilidad del clasificador**
- [ ] (Opcional) `--mark-unstable` → mensajes inestables en **Revisar clasificaciones** con badge «Inestable»
- [ ] Detalle por mensaje con `--verbose` (esperado vs modelo en categorías)

## Script de verificación rápida

```bash
# Cola
curl -s http://localhost:8000/health/deep | jq .

# Ingest de prueba
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"external_id":"demo-001","fuente":"manual","texto":"La app falla al pagar","timestamp":"2026-06-16T12:00:00Z","metadata":{}}'
```

## Pitch de 30 segundos

> Clasificamos feedback de clientes de forma autónoma cada 5 minutos. Cuando la IA no está segura, escala al humano. Convertimos señales en acciones concretas — urgentes, oportunidades y patrones — no solo gráficos. Medimos la calidad y la estabilidad del modelo contra un golden set, y las correcciones humanas alimentan el few-shot para mejorar el siguiente ciclo.
