# ADR-009 — Human-in-the-loop y few-shot dinámico

**Fecha:** junio 2026  
**Estado:** Aceptado  
**Etiquetas:** LLM | Calidad | Aprendizaje

## Contexto

El clasificador devuelve `confianza` 0–1. Por debajo del umbral (`CONFIDENCE_REVIEW_THRESHOLD`, default 0.7) el mensaje requiere revisión humana. Se implementó un bucle de mejora con **ejemplos en prompt** (few-shot dinámico), acorde al alcance del reto.

## Decisión

1. **Human-in-the-loop:** Dashboard «Revisar clasificaciones» + API FastAPI `PATCH /classifications/{external_id}`.
2. **Persistencia:** Tabla `feedback_correcciones` con original y corregido.
3. **Mejora por ejemplos:** Export a `classification_fewshot_dynamic.md` + caché Gemini. Bump de `GEMINI_CACHE_VERSION` al exportar.
4. **Evaluación:** Script `eval_classification.py` + golden set; resultado opcional en `feedback_metricas`.

## Implementación

- [backend/src/api/routes/classifications.py](../../backend/src/api/routes/classifications.py)
- [backend/scripts/export_fewshot_from_corrections.py](../../backend/scripts/export_fewshot_from_corrections.py)
- [backend/scripts/eval_classification.py](../../backend/scripts/eval_classification.py)
- [dashboard/components/revision.py](../../dashboard/components/revision.py)
- Migración 009

## Consecuencias

- Tras corregir, hay que exportar few-shot y reiniciar worker para aplicar aprendizaje.
- Requiere migración 009 y `API_KEY` en dashboard para correcciones vía API.
