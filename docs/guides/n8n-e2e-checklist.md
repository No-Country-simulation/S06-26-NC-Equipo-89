# Checklist E2E — n8n + FastAPI + Worker

## Pre-requisitos

- [ ] FastAPI en `0.0.0.0:8000` (`/health` OK)
- [ ] `docker compose up -d --no-deps n8n` (puerto **5679**)
- [ ] Workflow importado desde [`n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json`](../../n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json)
- [ ] Workflow **activo** (toggle ON) — sin esto los webhooks devuelven 404
- [ ] `worker.py` corriendo
- [ ] Variables en `.env`: `API_KEY`, `FASTAPI_INGEST_URL`, `GROQ_API_KEY` (recomendado)
- [ ] `.env` **no** commiteado — ver [seguridad-y-secretos.md](seguridad-y-secretos.md)

Recrear n8n tras cambiar `.env`:

```bash
docker compose up -d n8n --no-deps --force-recreate
```

## Nodo HTTP — configuración correcta

| Campo | Valor |
|-------|-------|
| URL | `http://host.docker.internal:8000/ingest` o `={{ $env.FASTAPI_INGEST_URL }}` |
| Header `X-API-Key` | `={{ $env.API_KEY }}` |
| Header `Content-Type` | `application/json` |
| Body JSON | `={{ JSON.stringify({ external_id, fuente, texto, timestamp, metadata }) }}` |

**Nota:** el editor n8n puede mostrar `[access to env vars denied]` en rojo al previsualizar `$env`. Es una limitación del UI; al **ejecutar** el workflow suele resolver bien si Docker tiene `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.

Variables n8n en Docker (`docker-compose.yml`):

- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`
- `N8N_EXPRESSIONS_ALLOWED_ENV_VARS=API_KEY,FASTAPI_INGEST_URL`

## Pruebas por fuente

### WhatsApp

Usa el nodo **WhatsApp Trigger** (no `/webhook/whatsapp` genérico).

- Meta Developers → callback = Production URL del nodo (ej. `{WEBHOOK_URL}/webhook/{webhookId}/webhook`)
- Verify token = `webhookId` del nodo
- Credencial WhatsApp OAuth en n8n

### Tally (webhook nativo en Tally → n8n)

Configuración en Tally: **Integrations → Webhooks** → URL `…/webhook/tally`. Guía: [n8n-tally-webhook.md](n8n-tally-webhook.md).

```bash
curl -X POST http://localhost:5679/webhook/tally \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "FORM_RESPONSE",
    "data": {
      "responseId": "tally-001",
      "formId": "FORM123",
      "formName": "Encuesta",
      "fields": [
        {"label": "Comentario", "type": "TEXTAREA", "value": "Problema con la facturación"}
      ]
    }
  }'
```

### Google Forms (Google Sheets Trigger en n8n)

El workflow actual usa **Google Sheets Trigger** (poll ~1 min): formulario vinculado a Sheet + OAuth Google en n8n.

Alternativa sin OAuth: Apps Script → [n8n-google-forms-apps-script.md](n8n-google-forms-apps-script.md).

## Verificación Supabase y dashboard

### Rápido (UI)

1. Dashboard → **Vista General** → **Entradas recientes** (auto-refresh 30 s)
2. Tras el ingest: aparece el mensaje con estado **En cola** (`pendiente` en BD)
3. Tras el worker: pasa a **Clasificado** → ver detalle en **Clasificaciones → Mensajes**

### SQL (opcional)

```sql
SELECT external_id, fuente, estado, created_at
FROM feedback_raw
ORDER BY created_at DESC
LIMIT 10;

SELECT external_id, sentimiento, urgencia, confianza, resumen
FROM feedback_clasificado
ORDER BY created_at DESC
LIMIT 5;
```

Esperado tras ingest: `estado = 'pendiente'`  
Tras worker (~5 min): `estado = 'procesado'` + fila en `feedback_clasificado`

## Troubleshooting

| Síntoma | Solución |
|---------|----------|
| 401 en HTTP node | Verificar `={{ $env.API_KEY }}` y valor en `.env` |
| `$env` denied al ejecutar | `docker compose up -d n8n --no-deps --force-recreate` |
| Connection refused | FastAPI debe usar `--host 0.0.0.0` |
| Queda en pendiente | Verificar `worker.py` corriendo |
| Webhook 404 | Workflow no activo o path incorrecto |
| OAuth Google 403 | Agregar tu Gmail en Usuarios de prueba (Google Cloud) |
| Copilot sin resultados | Verificar embeddings (`worker` o `scripts/backfill_embeddings.py`) |
