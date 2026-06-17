# ADR-003 — n8n como capa de normalización

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Automatización | Integración SaaS | Ingesta

## Contexto

Feedback de tres fuentes externas (WhatsApp, Tally, Google Forms) más carga manual CSV desde Streamlit. Cada fuente tiene formato distinto.

## Decisión

**n8n** desacopla el formato de cada fuente del backend. FastAPI recibe siempre el mismo JSON estándar.

## Contrato JSON estándar

```json
{
  "external_id": "fuente_identificador_timestamp",
  "fuente": "whatsapp | tally | google_forms | csv",
  "texto": "mensaje original sin modificar",
  "timestamp": "2026-06-11T14:30:00Z",
  "metadata": {}
}
```

## Implementación

- [`n8n/feedback-ingest.json`](../../n8n/feedback-ingest.json) — webhooks WhatsApp, Tally y Google Forms
- [`n8n/feedback-ingest-simple.json`](../../n8n/feedback-ingest-simple.json) — prueba con un webhook
- [`docker-compose.yml`](../../docker-compose.yml) (n8n local puerto 5679)
- Google Forms: webhook + Apps Script ([`docs/n8n-google-forms-apps-script.md`](../n8n-google-forms-apps-script.md)), sin OAuth en n8n
