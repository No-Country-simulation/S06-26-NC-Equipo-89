# ADR-003 — n8n como capa de normalización

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Automatización | Integración SaaS | Ingesta

## Contexto

Feedback de tres fuentes externas (WhatsApp, Tally, Google Forms) más carga manual CSV/JSON/Excel desde Streamlit. Cada fuente tiene formato distinto.

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

## Implementación (workflow actual)

| Fuente | Nodo n8n | Notas |
|--------|----------|-------|
| **WhatsApp** | `WhatsApp Trigger` | OAuth Meta; callback = Production URL del nodo |
| **Tally** | `Webhook Tally` | `POST …/webhook/tally` — ver [guía Tally](../guides/n8n-tally-webhook.md) |
| **Google Forms** | `Google Sheets Trigger` | Form vinculado a Sheet; poll ~1 min; OAuth Google |
| **CSV manual** | — | Streamlit → `POST /ingest/csv` (sin n8n) |

- Workflow producción: [`n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json`](../../n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json)
- Workflow prueba: [`n8n/feedback-ingest-simple.json`](../../n8n/feedback-ingest-simple.json)
- Docker: [`docker-compose.yml`](../../docker-compose.yml) (n8n puerto **5679**)
- Header `X-API-Key`: `={{ $env.API_KEY }}` (desde `.env`, no hardcodeado)
- Checklist E2E: [`docs/guides/n8n-e2e-checklist.md`](../guides/n8n-e2e-checklist.md)

### Google Forms — alternativa sin OAuth

Si Google Sheets Trigger falla en local, usar Apps Script → webhook. Ver [`docs/guides/n8n-google-forms-apps-script.md`](../guides/n8n-google-forms-apps-script.md).
