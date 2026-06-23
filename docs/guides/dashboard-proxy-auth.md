# Proxy auth y TLS para dashboard interno

El dashboard Streamlit es **solo para equipo interno**. No implementamos login de usuarios en v1 — el acceso se controla con reverse proxy + TLS.

## Opciones equivalentes

| Entorno | Enfoque recomendado |
|---------|---------------------|
| Fly.io | Red `internal` + `fly proxy 8501:8501 -a feedback-dashboard` |
| VPS | Caddy/Nginx con Basic Auth + Let's Encrypt |
| Local dev | `127.0.0.1:8501` + túnel SSH |

## Opción A — Caddy (VPS)

`Caddyfile`:

```caddy
dashboard.tudominio.com {
    basicauth {
        analista $2a$14$HASH_BCRYPT_AQUI
    }
    reverse_proxy 127.0.0.1:8501
}
```

Generar hash bcrypt:

```bash
caddy hash-password --plaintext 'tu-password-segura'
```

Levantar:

```bash
caddy run --config Caddyfile
```

En `docker-compose.prod.yml` el servicio `dashboard` **no** publica puerto 8501 al host; solo Caddy en el host hace proxy.

## Opción B — Nginx

```nginx
server {
    listen 443 ssl;
    server_name dashboard.tudominio.com;

    ssl_certificate     /etc/letsencrypt/live/dashboard.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.tudominio.com/privkey.pem;

    auth_basic "Dashboard interno";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Crear `.htpasswd`:

```bash
htpasswd -c /etc/nginx/.htpasswd analista
```

## Opción C — Fly.io (acceso interno)

```bash
# Dashboard sin puerto público en fly.toml
fly scale count 1 -a feedback-dashboard

# Acceso del equipo
fly proxy 8501:8501 -a feedback-dashboard
# Abrir http://localhost:8501
```

Para HTTPS público con auth, combinar con Caddy en una máquina bastion o usar Fly certificates + middleware de auth.

## FastAPI — CORS en producción

Si el dashboard llama a la API desde el navegador, restringir orígenes:

```bash
CORS_ORIGINS=https://dashboard.tudominio.com
ENV=production
```

La ingesta desde n8n no usa CORS (server-to-server).

## Firewall (VPS)

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

No exponer `8501` ni `8000` directamente; solo el reverse proxy en 443.

## Checklist

- [ ] Dashboard no accesible sin auth
- [ ] TLS válido (Let's Encrypt o certificado corporativo)
- [ ] `SUPABASE_KEY` del dashboard es read-only (`DASHBOARD_READONLY=true`)
- [ ] `API_KEY` de FastAPI no aparece en logs del proxy
- [ ] Equipo documenta URL y credenciales en gestor de secretos interno

Ver también: [bi-readonly-setup.md](bi-readonly-setup.md) · [seguridad-y-secretos.md](seguridad-y-secretos.md)
