# ADR-007 — Streamlit y BI directo

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Frontend | Infraestructura

## Decisión

**Streamlit** para CS Managers. **BI** (Power BI, Metabase) conecta directo a Supabase PostgreSQL.

## Streamlit muestra

- Distribución sentimiento y categorías
- Alertas urgencia alta
- Patrones detectados
- Carga CSV manual
- Export CSV/JSON
- Copilot RAG (vía FastAPI, ADR-008)

## BI

- Credenciales read-only (ver [`docs/bi-readonly-setup.md`](../bi-readonly-setup.md))
- Tablas: `feedback_clasificado`, `feedback_patrones`, `feedback_metricas`

## Implementación

- [`dashboard/`](../../dashboard/)
