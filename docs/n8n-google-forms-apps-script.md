# Google Forms → n8n (sin OAuth)

El nodo Google Sheets/Forms Trigger requiere OAuth en Google Cloud y suele fallar en local (`Unable to sign without access token`).

**Alternativa:** Apps Script en el formulario envía un POST al webhook de n8n (igual que WhatsApp).

## 1. Reimportar workflow

Importá `n8n/feedback-ingest.json` y activá el workflow.

Webhook Google Forms:
```
POST http://localhost:5679/webhook/google-forms
```

## 2. Probar sin Google (curl local)

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

## 3. Apps Script en tu formulario

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

## 4. URL pública (importante)

Google **no puede** llamar a `http://localhost:5679` desde sus servidores.

Opciones:

| Entorno | URL del webhook |
|---------|-----------------|
| Local con túnel (ngrok, cloudflared) | `https://xxxx.ngrok.io/webhook/google-forms` |
| n8n Cloud / servidor con dominio | `https://tu-dominio.com/webhook/google-forms` |
| Docker en servidor | URL pública del puerto 5679 |

Actualizá `N8N_WEBHOOK_URL` en el script con esa URL.

## 5. El Sheet vinculado sigue sirviendo

El formulario puede seguir guardando respuestas en el Sheet para backup/BI. El webhook es **adicional** para disparar n8n en tiempo real.
