# Desarrollo local vs producción

Guía rápida para saber **qué necesitás hoy** (local/demo) y **qué activar solo al desplegar** (producción).

> El código incluye endurecimiento de producción, pero **no obliga** a usarlo en local. Producción es **opt-in** vía variables de entorno.

---

## Resumen en una frase

| Modo | Cuándo | Qué hacer |
|------|--------|-----------|
| **Local / demo** | Desarrollo, bootcamp, pruebas | Seguir como siempre — sin `ENV=production` |
| **Producción** | Servidor real, clientes, HTTPS | Checklist go-live + `.env.production.example` |

---

## Desarrollo local (como antes)

### Variables que **no** hace falta tocar

Si no definís `ENV` en `.env`, el sistema asume **`development`**:

- `API_KEY` puede ser corta (la que ya uses en local)
- Dashboard puede usar `service_role` en `SUPABASE_KEY`
- **No** hace falta `DASHBOARD_READONLY=true`
- **No** hace falta proxy TLS ni Basic Auth
- **No** hace falta `CORS_ORIGINS` (CORS desactivado si está vacío)

### Levantar el stack

```bash
# API
cd backend && ../.venv/bin/uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Worker
cd backend && python worker.py

# Dashboard
streamlit run dashboard/main.py
```

O con Docker de desarrollo:

```bash
docker compose up
```

Usá **`docker-compose.yml`** (no `docker-compose.prod.yml`).

### Único cambio de BD recomendado en local

Si actualizaste el código del worker/dashboard, aplicá la migración **007** en tu Supabase (dev):

→ [`docs/database/migrations/007_production_hardening.sql`](../database/migrations/007_production_hardening.sql)

Sin ella, el persister puede fallar al escribir `tick_id` en métricas y patrones.

### Qué sí cambió en local (benigno)

- El worker **recupera mensajes atascados** en `procesando` al inicio de cada tick
- Rate limit suave en ingest/copilot (60/30 req/min por IP — no afecta uso normal)
- Patrones del dashboard filtran por **último `tick_id`** del worker

---

## Producción (opt-in)

### Cómo se activa

En el servidor, en `.env` (o secrets manager):

```bash
ENV=production
API_KEY=<openssl rand -hex 32>   # mínimo 32 caracteres
DASHBOARD_READONLY=true
SUPABASE_KEY=<credencial dashboard_readonly>
CORS_ORIGINS=https://dashboard.tu-dominio.com
```

Plantilla completa: [`.env.production.example`](../../.env.production.example)

### Qué exige el código en `ENV=production`

| Requisito | Motivo |
|-----------|--------|
| `API_KEY` ≥ 32 chars | Validación al arrancar FastAPI |
| `DASHBOARD_READONLY=true` | Bloquea arrancar dashboard con `service_role` por error |
| Rol `dashboard_readonly` en Supabase | Solo SELECT — ver [bi-readonly-setup.md](bi-readonly-setup.md) |
| Proxy TLS + auth delante de Streamlit | Ver [dashboard-proxy-auth.md](dashboard-proxy-auth.md) |
| Migración 007 en Supabase **prod** | CHECK, `tick_id`, índices |

### Despliegue

```bash
docker compose -f docker-compose.prod.yml --env-file /path/to/.env up -d
```

### Código listo ≠ deploy hecho

El repositorio incluye CI, healthchecks, runbook y compose prod, pero **vos** debés:

1. Ejecutar migración 007 en Supabase prod
2. Rotar secretos y configurar n8n con HTTPS fijo
3. Configurar proxy del dashboard
4. Verificar backups en Supabase
5. Probar recovery con un lote (~50 mensajes)

Checklist detallado: [README — Producción](../../README.md#producción-single-tenant)

---

## Tabla comparativa

| Aspecto | Local (`development`) | Producción (`ENV=production`) |
|---------|------------------------|-------------------------------|
| `API_KEY` | Cualquier valor en `.env` | ≥ 32 caracteres, obligatorio |
| Dashboard Supabase | `service_role` OK | Rol `dashboard_readonly` |
| Acceso dashboard | `localhost:8501` | Proxy + TLS + Basic Auth |
| Docker | `docker-compose.yml` | `docker-compose.prod.yml` |
| CORS | No configurado | `CORS_ORIGINS` del dashboard |
| Logs con texto feedback | Permitido | PII desactivado automáticamente |
| n8n webhooks | ngrok / localhost OK | HTTPS fijo en dominio real |

---

## Documentación relacionada

| Tema | Guía |
|------|------|
| Secretos y Git | [seguridad-y-secretos.md](seguridad-y-secretos.md) |
| Usuario read-only | [bi-readonly-setup.md](bi-readonly-setup.md) |
| Proxy dashboard | [dashboard-proxy-auth.md](dashboard-proxy-auth.md) |
| Incidentes y backups | [runbook-produccion.md](runbook-produccion.md) |
| Plan completo | [plan-produccion-single-tenant.md](../plans/plan-produccion-single-tenant.md) |
| Estado implementación | [estado-implementacion.md](../estado-implementacion.md) |
