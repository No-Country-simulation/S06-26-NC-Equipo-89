# Runbook — producción single-tenant

Guía operativa para incidentes frecuentes del Feedback Classifier en producción.

## Servicios

| Componente | Comando / URL | Credenciales |
|------------|---------------|--------------|
| FastAPI | `/health`, `/health/deep` | `X-API-Key` |
| Worker | `python worker.py` | `DB_DSN` escritura |
| Dashboard | Streamlit `:8501` (proxy) | `SUPABASE_KEY` read-only |
| n8n | Webhooks HTTPS | `API_KEY` vía `$env` |

## Incidentes

### Mensajes en estado `error`

**Síntoma:** `get_queue_health` muestra errores > 0; clasificación falló tras `MAX_RETRIES`.

**Acción:**

```bash
cd backend
python scripts/requeue_errors.py
# Revisar logs del worker: docker logs feedback-classifier-worker -f
```

Verificar causa (429 Gemini, JSON inválido, CHECK constraint en sentimiento/urgencia).

### Atascados en `procesando`

**Síntoma:** Cola no avanza; filas quedan en `procesando` tras crash del worker.

**Acción automática:** el worker ejecuta `recover_stuck_processing()` al inicio de cada tick.

**Acción manual:**

```bash
cd backend
python scripts/recover_stuck_processing.py
python scripts/recover_stuck_processing.py --minutes 45
```

**Cron opcional** (cada 15 min en VPS):

```cron
*/15 * * * * cd /app/backend && /app/.venv/bin/python scripts/recover_stuck_processing.py
```

### 429 / 503 en Gemini

**Síntoma:** Logs `gemini_rate_limit` o clasificador con reintentos.

**Acción:**

1. Verificar `GROQ_API_KEY` (fallback activo)
2. Bajar `GEMINI_CONCURRENCY` (ej. 2 o 1)
3. Reducir `CLASSIFY_LLM_BATCH_SIZE` temporalmente
4. Esperar ventana de cuota y reencolar errores

### Copilot sin resultados

**Síntoma:** Respuesta vacía o "No encontré feedback indexado".

**Acción:**

1. Verificar embeddings: `SELECT COUNT(*) FROM feedback_clasificado WHERE embedding IS NOT NULL`
2. Confirmar worker completó tick (logs `embed_done`)
3. Probar `/health/deep` y `/copilot/ask` con `X-API-Key`
4. Revisar `COHERE_API_KEY`

### API no responde / health degradado

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/deep
```

Si `database: unavailable` → revisar `DB_DSN`, pooler Supabase, firewall.

### Rate limit 429 en ingest

**Síntoma:** n8n recibe 429 desde FastAPI.

**Acción:** Ajustar `RATE_LIMIT_INGEST_PER_MINUTE` o espaciar triggers en n8n.

## Migraciones

Orden recomendado en Supabase SQL Editor:

1. `docs/database/supabase_schema.sql` (instalación nueva)
2. Migraciones incrementales `005` → `007_production_hardening.sql`

Tras `007`, patrones y métricas del dashboard filtran por `tick_id` del último batch.

## Backups

| Recurso | Método |
|---------|--------|
| PostgreSQL (Supabase) | PITR / backups automáticos (plan Pro) o `pg_dump` diario |
| n8n workflows | Export JSON al repo (sin credenciales) |
| n8n credenciales OAuth | Backup del volume `n8n_data` |
| `.env` producción | Secrets manager del host — **no** en Git |

Verificar restore mensual con dump de prueba en entorno staging.

## Rotación de secretos

| Secreto | Frecuencia | Procedimiento |
|---------|------------|---------------|
| `API_KEY` | 90 días | `openssl rand -hex 32` → actualizar n8n + dashboard |
| `dashboard_readonly` password | 90 días | `ALTER ROLE ... PASSWORD` + actualizar `SUPABASE_KEY` |
| LLM keys | Según política | Panel del proveedor |

## Logs útiles

```bash
# Docker
docker logs feedback-classifier-api -f --tail 100
docker logs feedback-classifier-worker -f --tail 100

# Eventos structlog clave
# ingest_success, classifier_done, persister_done, recover_stuck_processing, copilot_ask_success
```

En producción (`ENV=production`) no se registran textos completos de feedback en logs de API.

## Escalado

Single-tenant v1: **un worker** es suficiente hasta ~10k mensajes/día. Para más volumen:

- Aumentar `BATCH_SIZE` con cuidado en cuota LLM
- Segundo worker requiere revisar `SKIP LOCKED` (ya soportado en loader)

## Contactos

Documentar en wiki interna: on-call, acceso Supabase, acceso Fly/VPS.
