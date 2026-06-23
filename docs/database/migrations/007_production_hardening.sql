-- Fase producción single-tenant: constraints, tick_id, índices

-- Validar enums del clasificador (ejecutar solo si datos existentes cumplen)
ALTER TABLE feedback_clasificado
  DROP CONSTRAINT IF EXISTS chk_sentimiento,
  DROP CONSTRAINT IF EXISTS chk_urgencia;

ALTER TABLE feedback_clasificado
  ADD CONSTRAINT chk_sentimiento
    CHECK (sentimiento IN ('Positivo', 'Negativo', 'Neutral')),
  ADD CONSTRAINT chk_urgencia
    CHECK (urgencia IN ('Alta', 'Media', 'Baja'));

-- Trazabilidad por tick del worker
ALTER TABLE feedback_metricas
  ADD COLUMN IF NOT EXISTS tick_id UUID DEFAULT gen_random_uuid();

ALTER TABLE feedback_patrones
  ADD COLUMN IF NOT EXISTS tick_id UUID;

CREATE INDEX IF NOT EXISTS idx_raw_created_at ON feedback_raw(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clasificado_created_at ON feedback_clasificado(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patrones_created_at ON feedback_patrones(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patrones_tick_id ON feedback_patrones(tick_id);
CREATE INDEX IF NOT EXISTS idx_metricas_tick_id ON feedback_metricas(tick_id);
CREATE INDEX IF NOT EXISTS idx_clasificado_categorias ON feedback_clasificado USING GIN (categorias);
