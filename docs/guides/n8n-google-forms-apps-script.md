# Google Forms → n8n (alternativa sin OAuth)

> **Nota:** El workflow de producción [`Feedback-Ingest-3-fuentes-a-FastAPI.json`](../../n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json) usa **Google Sheets Trigger** (OAuth Google en n8n).  
> Esta guía es una **alternativa** si OAuth falla en local o preferís Apps Script.

El nodo Google Sheets Trigger requiere OAuth en Google Cloud y a veces falla en local (`Unable to sign without access token`).

**Alternativa:** Apps Script en el formulario envía un POST a un webhook de n8n.

## Opción A — Workflow simple con webhook Forms

Importá [`n8n/feedback-ingest-simple.json`](../../n8n/feedback-ingest-simple.json) o añadí un nodo **Webhook** con path `google-forms` al workflow activo.

Webhook local:
```
POST http://localhost:5679/webhook/google-forms
```

## Probar sin Google (curl local)

```bash
curl -X POST http://localhost:5679/webhook/google-forms \
  -H "Content-Type: application/json" \
  -d '{
    "id_mensaje": "gf-test-001",
    "mensaje": "Respuesta de prueba desde Google Forms",
    "email": "test@ejemplo.com"
  }'
```

Verificá en Supabase: `feedback_raw` con `fuente = google_forms`.

## Apps Script en tu formulario

1. Abrí el formulario en Google Forms
2. **⋮ → Editor de secuencias de comandos** (Apps Script)
3. Pegá y guardá:

```javascript
var N8N_WEBHOOK_URL = 'https://TU-URL-PUBLICA/webhook/google-forms';

function onFormSubmit(e) {
  var pairs = [];
  for (var key in e.namedValues) {
    pairs.push(key + ': ' + e.namedValues[key][0]);
  }

  var payload = {
    id_mensaje: 'gf-' + new Date().getTime(),
    mensaje: pairs.join(' | '),
    timestamp: new Date().toISOString(),
    email: (e.namedValues['Dirección de correo electrónico'] || [''])[0]
  };

  UrlFetchApp.fetch(N8N_WEBHOOK_URL, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
}
```

4. **Activadores** (reloj izquierda) → **Añadir activador**
   - Función: `onFormSubmit`
   - Origen del evento: **Del formulario**
   - Tipo: **Al enviar el formulario**
5. Autorizá el script cuando Google lo pida

## URL pública (importante)

Google **no puede** llamar a `http://localhost:5679` desde sus servidores.

| Entorno | URL del webhook |
|---------|-----------------|
| Local con túnel (ngrok) | `https://xxxx.ngrok.io/webhook/google-forms` |
| n8n Cloud / servidor | `https://tu-dominio.com/webhook/google-forms` |

Actualizá `N8N_WEBHOOK_URL` en el script con esa URL.

## Opción B — Google Sheets Trigger (recomendado en producción)

Ver [ADR-003](../adr/ADR-003-n8n-normalizacion.md) y [checklist E2E](n8n-e2e-checklist.md).

## El Sheet vinculado sigue sirviendo

El formulario puede seguir guardando respuestas en el Sheet para backup/BI. El webhook Apps Script es **adicional** para disparar n8n en tiempo real.
