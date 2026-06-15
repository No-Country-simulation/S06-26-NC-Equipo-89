-- Schema para Feedback Classifier (Supabase / PostgreSQL)

-- 1. Tabla Raw (Ingesta y Cola de Micro-batching)
CREATE TABLE IF NOT EXISTS feedback_raw (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    fuente VARCHAR(50) NOT NULL,
    texto TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'procesando', 'procesado', 'error')),
    retry_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices críticos para la concurrencia y consultas rápidas
CREATE INDEX IF NOT EXISTS idx_feedback_raw_estado ON feedback_raw(estado, timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_raw_external_id ON feedback_raw(external_id);

-- 2. Tabla de Clasificación Estructurada
CREATE TABLE IF NOT EXISTS feedback_clasificado (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL REFERENCES feedback_raw(external_id) ON DELETE CASCADE,
    sentimiento VARCHAR(50) NOT NULL,
    urgencia VARCHAR(50) NOT NULL,
    idioma VARCHAR(50) NOT NULL,
    categorias JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clasificado_sentimiento ON feedback_clasificado(sentimiento);
CREATE INDEX IF NOT EXISTS idx_clasificado_urgencia ON feedback_clasificado(urgencia);

-- 3. Tabla de Métricas (Agregaciones por Batch)
CREATE TABLE IF NOT EXISTS feedback_metricas (
    id BIGSERIAL PRIMARY KEY,
    datos_metricas JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabla de Patrones Detectados
CREATE TABLE IF NOT EXISTS feedback_patrones (
    id BIGSERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    frecuencia VARCHAR(100) NOT NULL,
    impacto VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
