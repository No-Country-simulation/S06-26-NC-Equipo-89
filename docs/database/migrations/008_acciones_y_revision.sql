-- Fase 2: acciones sugeridas y flags de revisión humana

CREATE TABLE IF NOT EXISTS feedback_acciones (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) REFERENCES feedback_raw(external_id) ON DELETE SET NULL,
    tick_id UUID,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('urgente', 'oportunidad', 'patron', 'revision')),
    titulo TEXT NOT NULL,
    descripcion TEXT,
    prioridad INT DEFAULT 50,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'hecha', 'descartada')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_acciones_estado_prioridad ON feedback_acciones(estado, prioridad);
CREATE INDEX IF NOT EXISTS idx_acciones_tick_id ON feedback_acciones(tick_id);
CREATE INDEX IF NOT EXISTS idx_acciones_created_at ON feedback_acciones(created_at DESC);

ALTER TABLE feedback_clasificado
    ADD COLUMN IF NOT EXISTS requiere_revision BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS revision_estado VARCHAR(20) DEFAULT 'auto';

-- CHECK en columna existente: solo si no hay violaciones previas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'feedback_clasificado_revision_estado_check'
    ) THEN
        ALTER TABLE feedback_clasificado
            ADD CONSTRAINT feedback_clasificado_revision_estado_check
            CHECK (revision_estado IN ('auto', 'pendiente', 'confirmado', 'corregido'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_clasificado_revision ON feedback_clasificado(requiere_revision, revision_estado);
