# ADR-007 — Streamlit y BI directo

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Frontend | Infraestructura

## Decisión

**Streamlit** para CS Managers. **BI** (Power BI, Metabase) conecta directo a Supabase PostgreSQL.

## Streamlit muestra (v3 — implementado)

- Navegación híbrida: Operación / Prioridades / Análisis / Datos
- Vista General: status bar, **Entradas recientes** (últimas 10 de `feedback_raw`, auto-refresh), KPIs, alertas, sentimiento
- Clasificaciones: mensajes clasificados + revisión humana
- Urgencia y señales (distribución + acciones)
- Tendencias: Temas recurrentes + Patrones (filtro de período)
- Export CSV/JSON · Carga CSV/JSON/Excel
- Copilot RAG (modal sidebar, ADR-008; `on_dismiss` mantiene el modal cerrado)
- Health banner, status bar, auto-refresh 30 s

## BI

- Credenciales read-only (ver [`docs/guides/bi-readonly-setup.md`](../guides/bi-readonly-setup.md))
- Tablas: `feedback_clasificado`, `feedback_patrones`, `feedback_metricas`

## Implementación

- [`dashboard/`](../../dashboard/)
