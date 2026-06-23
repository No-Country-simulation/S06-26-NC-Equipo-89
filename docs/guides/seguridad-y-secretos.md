# Seguridad y secretos

Guía para **no exponer credenciales** en el repositorio, en documentación ni en capturas de pantalla.

## Regla de oro

> **Nunca** commitear `.env`, claves API, DSN con password, tokens de ngrok, OAuth de n8n ni exports de Supabase con datos reales.

El repositorio solo incluye plantillas vacías o con placeholders:

- [`.env.example`](../.env.example) — desarrollo local
- [`.env.production.example`](../.env.production.example) — producción

## Qué va en `.env` (local, gitignored)

| Variable | Tipo | Notas |
|----------|------|-------|
| `DB_DSN` | Secreto | Connection string PostgreSQL con password |
| `GEMINI_API_KEY` | Secreto | Google AI |
| `GROQ_API_KEY` | Secreto | Fallback LLM |
| `COHERE_API_KEY` | Secreto | Embeddings RAG |
| `SUPABASE_KEY` | Secreto | Hoy `service_role` en demo — **no** en dashboard público |
| `API_KEY` | Secreto | Header `X-API-Key` para FastAPI (≥32 chars en producción) |
| `WEBHOOK_URL` | Sensible | URL pública ngrok/dominio para Meta WhatsApp |
| `ENV` | Config | `production` activa validación de `API_KEY` y desactiva PII en logs |
| `DASHBOARD_READONLY` | Config | `true` obligatorio en dashboard prod (bloquea `service_role`) |
| `CORS_ORIGINS` | Config | Orígenes permitidos del dashboard (comma-separated) |

Generar `API_KEY` segura:

```bash
openssl rand -hex 32
```

## Qué NO subir a Git

| Archivo / carpeta | Motivo |
|-------------------|--------|
| `.env`, `.env.local` | Contiene todas las claves |
| `Data/`, `1. Data Source/` | Datasets locales con feedback real |
| `n8n_data/` | Credenciales OAuth WhatsApp/Google guardadas por n8n |
| `*.pem`, `credentials.json` | Certificados y service accounts |
| Capturas con tokens visibles | Revisar antes de pegar en issues/PRs |

Ver [`.gitignore`](../.gitignore) — si agregás un archivo con secretos, añadilo ahí **antes** del commit.

## Checklist antes de `git push`

```bash
# 1. Confirmar que .env no está trackeado
git status
git check-ignore -v .env   # debe mostrar regla de .gitignore

# 2. Buscar patrones de claves en archivos staged
git diff --cached | rg -i 'gsk_|sk-|api_key=|password=|postgresql://.*:.*@' || true

# 3. Solo plantillas en el commit
git ls-files | rg '\.env$'   # no debe listar .env (solo .env.example si aplica)
```

Si accidentalmente commiteaste un secreto:

1. **Rotar la clave** en el proveedor (Gemini, Groq, Supabase, etc.) de inmediato.
2. No confiar solo en `git revert` — el secreto puede quedar en el historial.
3. Considerar `git filter-repo` o soporte de GitHub para secret scanning.

## Código y defaults

- `backend/src/core/config.py` — `api_key` default **vacío**; obligatorio definir `API_KEY` en `.env`.
- Tests usan `test-api-key` vía `tests/conftest.py` — no son credenciales reales.
- n8n workflows usan `={{ $env.API_KEY }}` — **sin** claves hardcodeadas en JSON exportado.

## Producción (recomendado)

| Práctica | Demo actual | Producción |
|----------|-------------|------------|
| `API_KEY` | Puede ser débil en local | `openssl rand -hex 32` obligatorio (`ENV=production`) |
| Supabase dashboard | `service_role` | Rol `dashboard_readonly` + `DASHBOARD_READONLY=true` |
| RLS | Desactivado | Single-tenant sin RLS (scope actual) |
| Secretos en servidor | Archivo `.env` | Secrets manager / variables CI |
| Logs | structlog con métricas tokens | `LOG_PII=false` automático en producción |
| Acceso dashboard | Puerto 8501 abierto | Proxy TLS + Basic Auth ([guía](dashboard-proxy-auth.md)) |

Ver también: [bi-readonly-setup.md](bi-readonly-setup.md) para acceso de solo lectura.

## Documentación y demos

- En README y guías solo aparecen **nombres de variables**, no valores.
- Ejemplos `curl` usan `$API_KEY` (variable de shell), no literales.
- Plantilla CSV de ejemplo: [`samples/plantilla_feedback.csv`](../samples/plantilla_feedback.csv) — datos ficticios.

## Contacto ante fuga

Si detectás una clave en el historial del repo: rotar en el proveedor, abrir issue interno y limpiar historial antes de hacer el repo público.
