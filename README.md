<p align="center">
  <img src="/Banner Github.png" alt="Banner del proyecto" width="100%">
</p>

<p align="center">
  <a href="docs/README.md">
    <img src="https://img.shields.io/badge/📚_Documentación-0F172A?style=for-the-badge&logo=readthedocs&logoColor=38BDF8">
  </a>
  <a href="docs/adr/README.md">
    <img src="https://img.shields.io/badge/🏛️_Arquitectura-1E1B4B?style=for-the-badge&logo=github&logoColor=A78BFA">
  </a>
  <a href="docs/estado-implementacion.md">
    <img src="https://img.shields.io/badge/🚀_Roadmap-111827?style=for-the-badge&logo=rocket&logoColor=22D3EE">
  </a>
</p>


# Feedback Classifier

Sistema de clasificación automática de feedback de clientes con LangGraph, FastAPI, Supabase, n8n y dashboard Streamlit.


## Arquitectura

<p align="center">
  <img src="/Arquitectura.png" alt="Banner del proyecto" width="100%">
</p>



```
WhatsApp / Tally / Google Forms ──► n8n (normaliza JSON)
CSV manual ──► Streamlit ──► FastAPI /ingest/csv
                                      │
                                      ▼
                               feedback_raw (Supabase)
                                      │
                               worker.py (LangGraph + embeddings Cohere)
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           feedback_clasificado  feedback_patrones  feedback_metricas
                    │
              Copilot RAG (/copilot/ask) — Gemini con fallback Groq
```

## Requisitos

- Python 3.12+
- Docker (para n8n)
- Cuenta Supabase, Gemini API, Cohere API
- Groq API (opcional, fallback cuando Gemini devuelve 503/429)

## Configuración

```bash
cp .env.example .env
# Completar DB_DSN, SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, COHERE_API_KEY, API_KEY
# Opcional: GROQ_API_KEY (fallback LLM)
pip install -r requirements.txt
```

Variables clave en `.env`:

| Variable | Uso |
|----------|-----|
| `DB_DSN` | FastAPI + worker (Session pooler Supabase) |
| `API_KEY` | Header `X-API-Key` para n8n y dashboard |
| `GROQ_API_KEY` | Fallback LLM (clasificador, patrones, Copilot) |
| `FASTAPI_INGEST_URL` | URL que usa n8n Docker → `http://host.docker.internal:8000/ingest` |
| `FASTAPI_URL` | Dashboard/Copilot → `http://localhost:8000` |
| `WEBHOOK_URL` | Base pública HTTPS para Meta/WhatsApp (ngrok en local) |

Aplicar schema en Supabase SQL Editor:

1. [`docs/database/supabase_schema.sql`](docs/database/supabase_schema.sql) (schema completo)
2. Si ya tenías tablas creadas: [`docs/database/migrations/006_schema_hardening.sql`](docs/database/migrations/006_schema_hardening.sql)

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

Abrir http://localhost:5679 → importar [`n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json`](n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json) → **activar workflow** (toggle ON) → reasignar credenciales Google/WhatsApp si hace falta.

Recrear n8n tras cambiar `.env`:

```bash
docker compose up -d n8n --no-deps --force-recreate
```

### Embeddings Copilot

El **worker** indexa embeddings automáticamente tras cada tick. Para backfill manual:

```bash
cd backend && ../.venv/bin/python scripts/backfill_embeddings.py
# o
cd backend && ../.venv/bin/python embed_job.py
```

## URLs locales

| Servicio | URL |
|----------|-----|
| FastAPI health | http://localhost:8000/health |
| FastAPI docs | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |
| n8n | http://localhost:5679 |

### Dashboard Streamlit (v3)

Navegación multipágina: Vista General, Sentimiento, Urgencia, **Mensajes Clasificados** (resumen, confianza, idioma), Patrones, Exportar, Carga. Copilot IA en sidebar. Modo oscuro en sidebar.

## n8n — workflows y fuentes

| Archivo | Uso |
|---------|-----|
| [`n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json`](n8n/Feedback-Ingest-3-fuentes-a-FastAPI.json) | Producción: WhatsApp Trigger, Tally webhook, Google Sheets (Forms) |
| [`n8n/feedback-ingest-simple.json`](n8n/feedback-ingest-simple.json) | Prueba con un solo webhook |

Tras importar y **activar** el workflow:

| Fuente | Cómo llega a n8n |
|--------|------------------|
| **WhatsApp** | Nodo **WhatsApp Trigger** — callback Meta = `{WEBHOOK_URL}/webhook/{webhookId}/webhook` (Production URL del nodo) |
| **Tally** | Webhook POST → `http://localhost:5679/webhook/tally` (o URL pública ngrok) |
| **Google Forms** | **Google Sheets Trigger** (~1 min) — formulario vinculado a Sheet; OAuth Google en n8n |

**Tally:** [`docs/guides/n8n-tally-webhook.md`](docs/guides/n8n-tally-webhook.md)

**Google Forms (alternativa sin OAuth):** [`docs/guides/n8n-google-forms-apps-script.md`](docs/guides/n8n-google-forms-apps-script.md)

**Nodo POST a FastAPI** (compartido por las 3 fuentes):

- URL: `http://host.docker.internal:8000/ingest` (o `={{ $env.FASTAPI_INGEST_URL }}`)
- Header: `X-API-Key: ={{ $env.API_KEY }}` (desde `.env`; preview rojo de `$env` en n8n es normal al editar)

WhatsApp requiere credencial **WhatsApp OAuth**; Google Sheets requiere **Google OAuth** en n8n.

Checklist completo: [`docs/guides/n8n-e2e-checklist.md`](docs/guides/n8n-e2e-checklist.md)

## Prueba E2E rápida

```bash
# 1. Ingest directo a FastAPI
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"external_id":"test-001","fuente":"manual","texto":"La app falla al pagar","timestamp":"2026-06-17T12:00:00Z","metadata":{}}'

# 2. Webhook Tally (workflow n8n activo)
curl -X POST http://localhost:5679/webhook/tally \
  -H "Content-Type: application/json" \
  -d '{"eventType":"FORM_RESPONSE","data":{"responseId":"tally-001","fields":[{"label":"Comentario","value":"Soporte muy lento"}]}}'
```

Verificar en Supabase y en el dashboard (**Mensajes Clasificados**):

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

Documentación completa en [`docs/`](docs/README.md). Punto de entrada según tu rol:

| Rol | Empezar por |
|-----|-------------|
| **Evaluador / revisor** | [Estado de implementación](docs/estado-implementacion.md) → [ADRs](docs/adr/README.md) |
| **Desarrollador** | [README](README.md) (instalación) → [Schema DB](docs/database/supabase_schema.sql) |
| **Operador (n8n)** | [Checklist E2E](docs/guides/n8n-e2e-checklist.md) |

### Decisiones de arquitectura (ADR)

El diseño del sistema está documentado en [Architecture Decision Records](docs/adr/README.md):

- LLM y clasificación (Gemini + Groq)
- Pipeline LangGraph
- Ingestión n8n (WhatsApp, Tally, Google Forms)
- Supabase + RAG Copilot
- Dashboard Streamlit v3

### Más recursos

- [Guías operativas](docs/guides/) — n8n, Tally, Forms, BI
- [Base de datos](docs/database/) — schema y migraciones

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
docs/            # Índice en docs/README.md
tests/           # Suite pytest
```
