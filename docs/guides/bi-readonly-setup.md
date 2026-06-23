# BI read-only — Power BI / Metabase / Dashboard Streamlit (ADR-007)

Configuración para conectar herramientas de BI y el **dashboard Streamlit** a Supabase sin acceso de escritura.

> **Producción:** nunca usar `service_role` en Streamlit. Usar el rol `dashboard_readonly` descrito abajo.

## 1. Rol read-only para dashboard (Streamlit)

Ejecutar en el **SQL Editor** de Supabase (ajustar contraseña):

```sql
CREATE ROLE dashboard_readonly LOGIN PASSWORD 'cambiar-por-password-segura';

GRANT CONNECT ON DATABASE postgres TO dashboard_readonly;
GRANT USAGE ON SCHEMA public TO dashboard_readonly;

GRANT SELECT ON feedback_raw TO dashboard_readonly;
GRANT SELECT ON feedback_clasificado TO dashboard_readonly;
GRANT SELECT ON feedback_patrones TO dashboard_readonly;
GRANT SELECT ON feedback_metricas TO dashboard_readonly;
```

En Supabase gestionado, si `CREATE ROLE` no está permitido, crear un usuario con permisos SELECT limitados desde **Database → Roles** o usar JWT custom con políticas RLS (fuera de scope single-tenant).

### Variables del dashboard en producción

```bash
ENV=production
DASHBOARD_READONLY=true
SUPABASE_URL=https://[proyecto].supabase.co
# JWT del rol dashboard_readonly o API key con permisos SELECT únicamente
SUPABASE_KEY=[credencial-read-only]
```

El dashboard valida `DASHBOARD_READONLY=true` cuando `ENV=production` para evitar arrancar con `service_role` por error.

## 2. Usuario read-only para BI externo

Ejecutar en el **SQL Editor** de Supabase (ajustar contraseña):

```sql
-- Usuario dedicado para BI (solo lectura)
CREATE USER bi_readonly WITH PASSWORD 'cambiar-por-password-segura';

GRANT CONNECT ON DATABASE postgres TO bi_readonly;
GRANT USAGE ON SCHEMA public TO bi_readonly;

-- Tablas expuestas al dashboard y reportes
GRANT SELECT ON feedback_clasificado TO bi_readonly;
GRANT SELECT ON feedback_patrones TO bi_readonly;
GRANT SELECT ON feedback_metricas TO bi_readonly;

-- Opcional: vista de raw procesados (sin metadata sensible)
CREATE OR REPLACE VIEW v_feedback_export AS
SELECT
  fc.external_id,
  fr.fuente,
  fr.texto,
  fr.timestamp,
  fc.sentimiento,
  fc.urgencia,
  fc.idioma,
  fc.categorias,
  fc.confianza,
  fc.resumen,
  fc.created_at AS clasificado_at
FROM feedback_clasificado fc
JOIN feedback_raw fr ON fr.external_id = fc.external_id
WHERE fr.estado = 'procesado';

GRANT SELECT ON v_feedback_export TO bi_readonly;
```

> **Nota:** En planes Supabase gestionados, si `CREATE USER` no está permitido, usar un rol de solo lectura vía **Database → Roles** o la connection string del pooler con credenciales limitadas creadas desde el panel.

## 2. Connection string

Usar el **Session pooler** (puerto 5432) o **Transaction pooler** (6543) según la herramienta:

```
postgresql://bi_readonly:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

Obtener host y proyecto en: Supabase → Project Settings → Database.

## 3. Tablas recomendadas

| Tabla / Vista | Uso |
|---------------|-----|
| `feedback_clasificado` | Sentimiento, urgencia, categorías por mensaje |
| `feedback_patrones` | Patrones detectados por el agente |
| `feedback_metricas` | Agregados por lote (`datos_metricas` JSONB) |
| `v_feedback_export` | Vista unificada con texto original |

## 4. Power BI

1. Obtener datos → PostgreSQL
2. Servidor: host del pooler (sin `postgresql://`)
3. Base de datos: `postgres`
4. Modo: Import o DirectQuery según volumen
5. Usuario: `bi_readonly`

Consultas típicas:

```sql
SELECT sentimiento, COUNT(*) AS total
FROM feedback_clasificado
GROUP BY sentimiento;

SELECT datos_metricas, created_at
FROM feedback_metricas
ORDER BY created_at DESC
LIMIT 1;
```

## 5. Metabase

1. Admin → Databases → Add database → PostgreSQL
2. Pegar connection string o campos individuales
3. Desactivar escritura (solo lectura por grants)
4. Sincronizar schema y crear preguntas sobre las tablas anteriores

## 6. Seguridad

- No usar `service_role` en Streamlit ni en herramientas BI
- Worker y FastAPI siguen con `DB_DSN` de escritura (pooler Supabase)
- Rotar password de `dashboard_readonly` / `bi_readonly` periódicamente
- No exponer `feedback_raw` con metadata completa si contiene PII no necesaria para reportes
- Proteger el dashboard con proxy TLS + Basic Auth: [dashboard-proxy-auth.md](dashboard-proxy-auth.md)
