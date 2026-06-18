# Feedback Classifier

Sistema de clasificación automática de feedback de clientes con LangGraph, FastAPI, Supabase, n8n y dashboard Streamlit.

## Arquitectura

```
WhatsApp / Tally / Google Forms ──► n8n (normaliza JSON)
CSV manual ──► Streamlit ──► FastAPI /ingest/csv
                                      │
                                      ▼
                               feedback_raw (Supabase)
                                      │
                               worker.py (LangGraph)
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           feedback_clasificado  feedback_patrones  feedback_metricas
                    │
              embed_job.py (Cohere)
                    │
              Copilot RAG (/copilot/ask)
```

## Requisitos

- Python 3.12+
- Docker (para n8n)
- Cuenta Supabase, Gemini API, Cohere API

## Configuración

```bash
cp .env.example .env
# Completar DB_DSN, SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, COHERE_API_KEY, API_KEY
pip install -r requirements.txt
```

Variables clave en `.env`:

| Variable | Uso |
|----------|-----|
| `DB_DSN` | FastAPI + worker (Session pooler Supabase) |
| `API_KEY` | Header `X-API-Key` para n8n y dashboard |
| `FASTAPI_INGEST_URL` | URL que usa n8n Docker → `http://host.docker.internal:8000/ingest` |
| `FASTAPI_URL` | Dashboard/Copilot → `http://localhost:8000` |

Aplicar schema en Supabase SQL Editor:

1. [`docs/supabase_schema.sql`](docs/supabase_schema.sql) (schema completo)
2. Si ya tenías tablas creadas: [`docs/migrations/006_schema_hardening.sql`](docs/migrations/006_schema_hardening.sql)

## Levantar en local

### Terminal 1 — FastAPI (accesible desde n8n Docker)

```bash
cd backend
../.venv/bin/uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 — Worker LangGraph

```bash
cd backend
../.venv/bin/python worker.py
```

### Terminal 3 — Dashboard

```bash
.venv/bin/streamlit run dashboard/main.py
```

### Terminal 4 — n8n (solo el contenedor, sin chocar con FastAPI local)

```bash
docker compose up -d --no-deps n8n
```

Abrir http://localhost:5679 → importar [`n8n/feedback-ingest.json`](n8n/feedback-ingest.json) → **activar workflow** (toggle ON).

### Embeddings Copilot (manual o cron 3x/día)

```bash
cd backend && ../.venv/bin/python embed_job.py
```

## URLs locales

| Servicio | URL |
|----------|-----|
| FastAPI health | http://localhost:8000/health |
| FastAPI docs | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |
| n8n | http://localhost:5679 |

## n8n — workflows y webhooks

| Archivo | Uso |
|---------|-----|
| [`n8n/feedback-ingest.json`](n8n/feedback-ingest.json) | Producción: WhatsApp, Tally, Google Forms |
| [`n8n/feedback-ingest-simple.json`](n8n/feedback-ingest-simple.json) | Prueba con un solo webhook |

Tras importar y **activar** el workflow:

| Fuente | Webhook (POST) |
|--------|----------------|
| WhatsApp | `http://localhost:5679/webhook/whatsapp` |
| Tally | `http://localhost:5679/webhook/tally` |
| Google Forms | `http://localhost:5679/webhook/google-forms` |

**Google Forms:** sin OAuth en n8n. Usar Apps Script en el formulario → ver [`docs/n8n-google-forms-apps-script.md`](docs/n8n-google-forms-apps-script.md).

**Tally:** webhook nativo en el formulario (Integrations → Webhooks) → ver [`docs/n8n-tally-webhook.md`](docs/n8n-tally-webhook.md).

**Nodo POST a FastAPI** (compartido por las 3 fuentes):

- URL: `http://host.docker.internal:8000/ingest` (o `={{ $env.FASTAPI_INGEST_URL }}`)
- Header: `X-API-Key: token-secreto-n8n-12345` (valor de `API_KEY` en `.env`)

WhatsApp y Tally **no requieren credenciales OAuth en n8n**; activar el workflow y registrar la URL del webhook en cada fuente (Tally: Integrations → Webhooks).

Checklist completo: [`docs/n8n-e2e-checklist.md`](docs/n8n-e2e-checklist.md)

## Prueba E2E rápida

```bash
# 1. Ingest directo a FastAPI
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"external_id":"test-001","fuente":"manual","texto":"La app falla al pagar","timestamp":"2026-06-17T12:00:00Z","metadata":{}}'

# 2. Webhook WhatsApp (workflow n8n activo)
curl -X POST http://localhost:5679/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"id_mensaje":"wa-001","mensaje":"Soporte muy lento"}'

# 3. Webhook Tally
curl -X POST http://localhost:5679/webhook/tally \
  -H "Content-Type: application/json" \
  -d '{"responseId":"tally-001","mensaje":"Problema con la facturación"}'
```

Verificar en Supabase:

```sql
SELECT external_id, fuente, estado FROM feedback_raw ORDER BY created_at DESC;
```

## Docker (stack completo)

```bash
docker compose up -d --build
```

Servicios: `api`, `worker`, `dashboard`, `n8n`. Para desarrollo local con FastAPI en el host, usar solo `docker compose up -d --no-deps n8n`.

Plantilla producción: [`.env.production.example`](.env.production.example)

## Documentación

- ADRs: [`docs/adr/`](docs/adr/)
- Estado implementación: [`docs/estado-implementacion.md`](docs/estado-implementacion.md)
- BI read-only: [`docs/bi-readonly-setup.md`](docs/bi-readonly-setup.md)
- Checklist n8n: [`docs/n8n-e2e-checklist.md`](docs/n8n-e2e-checklist.md)
- Google Forms + Apps Script: [`docs/n8n-google-forms-apps-script.md`](docs/n8n-google-forms-apps-script.md)

## Formato CSV para carga manual

```csv
texto,fuente,external_id
"La app se cierra sola",csv,csv-001
"Muy buen servicio",csv,
```

Columnas: `texto` (obligatorio), `fuente` (opcional, default `csv`), `external_id` (opcional, se genera UUID).

## Tests

```bash
PYTHONPATH=backend .venv/bin/pytest tests/ -v
```

## Estructura del proyecto

```
backend/src/     # FastAPI, LangGraph, RAG
dashboard/       # Streamlit
n8n/             # Workflows exportados
prompts/         # Prompts Gemini
docs/            # Schema, ADRs, migraciones
tests/           # Suite pytest
```
