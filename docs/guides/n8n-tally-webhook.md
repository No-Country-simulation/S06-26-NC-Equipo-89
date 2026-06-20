# Tally → n8n → FastAPI (ingesta automática)

Cuando alguien envía un formulario o encuesta en **Tally**, Tally hace un POST al webhook de n8n. n8n normaliza el JSON y lo reenvía a FastAPI (`POST /ingest`).

En n8n el nodo **Webhook** *es* el trigger: no hace falta un nodo “Trigger” aparte. Solo hay que **activar el workflow** y registrar la URL del webhook en Tally.

## Flujo

```
Usuario envía formulario Tally
        │
        ▼
Tally POST JSON → n8n /webhook/tally
        │
        ▼
Set Formato API Tally (normaliza contrato)
        │
        ▼
POST a FastAPI /ingest → feedback_raw (estado: pendiente)
        │
        ▼
worker.py procesa el feedback
```

## 1. n8n: importar y activar

1. Levantá n8n: `docker compose up -d --no-deps n8n`
2. Abrí http://localhost:5679
3. Importá [`n8n/feedback-ingest.json`](../n8n/feedback-ingest.json)
4. **Activá el workflow** (toggle ON arriba a la derecha)

Sin el toggle ON, Tally recibirá **404** al enviar el formulario.

Webhook local (solo pruebas desde tu máquina):

```
POST http://localhost:5679/webhook/tally
```

## 2. Tally: conectar el webhook

1. Publicá el formulario en Tally
2. Pestaña **Integrations** → **Webhooks** → **Connect**
3. **Endpoint URL**: la URL **pública HTTPS** de n8n + `/webhook/tally`

| Entorno | URL de ejemplo |
|---------|----------------|
| Local con túnel (ngrok, cloudflared) | `https://xxxx.ngrok-free.app/webhook/tally` |
| Servidor con dominio | `https://tu-dominio.com/webhook/tally` |
| n8n Cloud | URL de producción que muestra el nodo Webhook Tally |

Tally exige:

- Método **POST** con JSON
- Respuesta **2XX** en menos de **10 segundos**

Opcional: **Signing secret** en Tally (`Tally-Signature`). Este proyecto no lo valida en n8n; podés dejarlo vacío en desarrollo.

## 3. Variable `WEBHOOK_URL` (Docker)

En `.env` definí la URL base pública para que n8n genere URLs de producción correctas:

```env
WEBHOOK_URL=https://xxxx.ngrok-free.app/
```

Reiniciá n8n tras cambiarla:

```bash
docker compose restart n8n
```

## 4. Probar sin Tally (curl local)

Con el workflow **activo**:

```bash
curl -X POST http://localhost:5679/webhook/tally \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "FORM_RESPONSE",
    "createdAt": "2026-06-18T12:00:00.000Z",
    "data": {
      "responseId": "tally-test-001",
      "formId": "FORM123",
      "formName": "Encuesta feedback",
      "createdAt": "2026-06-18T12:00:00.000Z",
      "fields": [
        {"label": "Comentario", "type": "TEXTAREA", "value": "El soporte tardó 3 días"},
        {"label": "Email", "type": "INPUT_EMAIL", "value": "usuario@ejemplo.com"}
      ]
    }
  }'
```

Verificá en Supabase:

```sql
SELECT external_id, fuente, texto, estado
FROM feedback_raw
WHERE fuente = 'tally'
ORDER BY created_at DESC
LIMIT 5;
```

Esperado: `external_id = tally-test-001`, `fuente = tally`, `estado = pendiente`.

## 5. Payload real de Tally

Tally envía (entre otros campos):

```json
{
  "eventType": "FORM_RESPONSE",
  "data": {
    "responseId": "2wgx4n",
    "formId": "VwbNEw",
    "formName": "Mi encuesta",
    "fields": [
      {"label": "Comentario", "type": "TEXTAREA", "value": "Texto del usuario"}
    ]
  }
}
```

El nodo **Set Formato API Tally** concatena `label: value` de cada campo en `texto` y mapea `responseId` → `external_id`.

Documentación oficial: [Tally Webhooks](https://tally.so/help/webhooks)

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Tally no dispara nada | Workflow n8n inactivo | Toggle ON en n8n |
| 404 en Tally | URL incorrecta o workflow inactivo | Copiar URL del nodo Webhook Tally (Production URL) |
| Tally reintenta / falla | Timeout > 10 s | Verificar que FastAPI responda rápido; revisar logs n8n |
| No llega a Supabase | API_KEY incorrecta | Header `X-API-Key` en nodo POST a FastAPI = `API_KEY` del `.env` |
| localhost en Tally | Tally no alcanza tu PC | Usar túnel HTTPS (ngrok/cloudflared) y `WEBHOOK_URL` |

Checklist completo: [n8n-e2e-checklist.md](n8n-e2e-checklist.md)
