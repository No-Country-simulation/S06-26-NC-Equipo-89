# Checklist E2E — n8n + FastAPI + Worker

## Pre-requisitos

- [ ] FastAPI en `0.0.0.0:8000` (`/health` OK)
- [ ] `docker compose up -d --no-deps n8n` (puerto **5679**)
- [ ] Workflow importado desde [`n8n/feedback-ingest.json`](../n8n/feedback-ingest.json)
- [ ] Workflow **activo** (toggle ON) — sin esto los webhooks devuelven 404
- [ ] `worker.py` corriendo
- [ ] Variables en `.env`: `API_KEY`, `FASTAPI_INGEST_URL`

## Nodo HTTP — configuración correcta

| Campo | Valor |
|-------|-------|
| URL | `http://host.docker.internal:8000/ingest` o `={{ $env.FASTAPI_INGEST_URL }}` |
| Header `X-API-Key` | `={{ $env.API_KEY }}` o valor fijo de `.env` |
| Header `Content-Type` | `application/json` |
| Path | `/ingest` (no `/api/ingest`) |

Si `$env` muestra error en el editor, usar valores fijos. El contenedor n8n carga `.env` vía `docker-compose.yml`.

Variables n8n en Docker (`docker-compose.yml`):

- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`
- `N8N_EXPRESSIONS_ALLOWED_ENV_VARS=API_KEY,FASTAPI_INGEST_URL`

## Pruebas por fuente

### WhatsApp

```bash
curl -X POST http://localhost:5679/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"id_mensaje":"wa-test-001","fuente":"whatsapp","mensaje":"El soporte tardó 3 días"}'
```

### Tally

```bash
curl -X POST http://localhost:5679/webhook/tally \
  -H "Content-Type: application/json" \
  -d '{"responseId":"tally-001","mensaje":"Problema con la facturación"}'
```

### Google Forms (webhook + Apps Script)

Sin OAuth en n8n. Ver [`docs/n8n-google-forms-apps-script.md`](n8n-google-forms-apps-script.md).

```bash
curl -X POST http://localhost:5679/webhook/google-forms \
  -H "Content-Type: application/json" \
  -d '{"id_mensaje":"gf-001","mensaje":"Prueba formulario Google"}'
```

Para producción: Apps Script en el formulario → URL pública del webhook (ngrok o servidor).

## Verificación Supabase

```sql
SELECT external_id, fuente, estado, created_at
FROM feedback_raw
ORDER BY created_at DESC
LIMIT 10;
```

Esperado tras ingest: `estado = 'pendiente'`  
Tras worker (~5 min): `estado = 'procesado'`

## Troubleshooting

| Síntoma | Solución |
|---------|----------|
| 401 en HTTP node | Verificar header `X-API-Key` |
| Connection refused | FastAPI debe usar `--host 0.0.0.0` |
| Queda en pendiente | Verificar `worker.py` corriendo |
| Webhook 404 | Workflow no activo (toggle OFF) o path incorrecto |
| OAuth Google 403 | Agregar tu Gmail en Usuarios de prueba (Google Cloud) |
| OAuth error 431 | Probar en ventana incógnito o usar webhook Google Forms |
| `$env` denied | `docker compose restart n8n` tras cambios en `.env` |
