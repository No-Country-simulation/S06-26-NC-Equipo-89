-- Migración 011 — temas_recurrentes
-- Tabla para análisis cross-tick: qué temas se repiten en los últimos N días.
-- Combinación de estadísticas por categoría (parte A) y resumen semántico LLM (parte B).

CREATE TABLE IF NOT EXISTS feedback_temas_recurrentes (
    id           BIGSERIAL PRIMARY KEY,
    periodo_dias INT       NOT NULL DEFAULT 7,
    temas        JSONB     NOT NULL,
    resumen_llm  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_temas_recurrentes_created_at
    ON feedback_temas_recurrentes(created_at DESC);

-- temas es un array de objetos con la estructura:
-- [
--   {
--     "categoria":           "Pagos",
--     "menciones":           47,
--     "dias_activos":        5,
--     "pct_urgencia_alta":   0.68,
--     "tendencia":           "subiendo",   -- subiendo | estable | bajando
--     "variantes_semanticas": ["falla QR", "error tarjeta"]
--   }
-- ]
