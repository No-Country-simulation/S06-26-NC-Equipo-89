# ADR-007 — Streamlit y BI directo

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Frontend | Infraestructura

## Decisión

**Streamlit** para CS Managers. **BI** (Power BI, Metabase) conecta directo a Supabase PostgreSQL.

## Streamlit muestra (v3 — implementado)

- Vista General (KPIs, sentimiento)
- Sentimiento y categorías (gráficos)
- Urgencia (distribución Alta/Media/Baja + mensajes)
- **Mensajes clasificados** (resumen, confianza, idioma, categorías)
- Patrones detectados
- Export CSV/JSON con filtros
- Carga CSV/JSON/Excel
- Copilot RAG (modal sidebar, ADR-008)
- Modo oscuro, health banner, status bar

## BI

- Credenciales read-only (ver [`docs/guides/bi-readonly-setup.md`](../guides/bi-readonly-setup.md))
- Tablas: `feedback_clasificado`, `feedback_patrones`, `feedback_metricas`

## Implementación

- [`dashboard/`](../../dashboard/)
