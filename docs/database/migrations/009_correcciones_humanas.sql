-- Fase 3: correcciones humanas para aprendizaje few-shot

CREATE TABLE IF NOT EXISTS feedback_correcciones (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) NOT NULL,
    texto_original TEXT,
    clasificacion_original JSONB,
    clasificacion_corregida JSONB NOT NULL,
    motivo VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_correcciones_external_id ON feedback_correcciones(external_id);
CREATE INDEX IF NOT EXISTS idx_correcciones_created_at ON feedback_correcciones(created_at DESC);
