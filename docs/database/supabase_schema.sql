-- Schema completo Feedback Classifier — ejecutar en Supabase SQL Editor
-- Crea tablas, índices, extensión pgvector y función match_feedback (Copilot RAG)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS feedback_raw (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    fuente VARCHAR(50) NOT NULL,
    texto TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'procesando', 'procesado', 'error')),
    retry_count INT DEFAULT 0,
    error_mensaje TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_raw_estado ON feedback_raw(estado, timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_raw_external_id ON feedback_raw(external_id);
CREATE INDEX IF NOT EXISTS idx_raw_created_at ON feedback_raw(created_at DESC);

CREATE TABLE IF NOT EXISTS feedback_clasificado (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL REFERENCES feedback_raw(external_id) ON DELETE CASCADE,
    sentimiento VARCHAR(50) NOT NULL CHECK (sentimiento IN ('Positivo', 'Negativo', 'Neutral')),
    urgencia VARCHAR(50) NOT NULL CHECK (urgencia IN ('Alta', 'Media', 'Baja')),
    idioma VARCHAR(50) NOT NULL,
    categorias JSONB NOT NULL DEFAULT '[]'::jsonb,
    confianza FLOAT,
    resumen TEXT,
    requiere_revision BOOLEAN DEFAULT FALSE,
    revision_estado VARCHAR(20) DEFAULT 'auto'
        CHECK (revision_estado IN ('auto', 'pendiente', 'confirmado', 'corregido')),
    embedding vector(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clasificado_sentimiento ON feedback_clasificado(sentimiento);
CREATE INDEX IF NOT EXISTS idx_clasificado_urgencia ON feedback_clasificado(urgencia);
CREATE INDEX IF NOT EXISTS idx_clasificado_created_at ON feedback_clasificado(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clasificado_categorias ON feedback_clasificado USING GIN (categorias);
CREATE INDEX IF NOT EXISTS idx_clasificado_embedding
  ON feedback_clasificado USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS feedback_metricas (
    id BIGSERIAL PRIMARY KEY,
    datos_metricas JSONB NOT NULL,
    tick_id UUID DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metricas_tick_id ON feedback_metricas(tick_id);

CREATE TABLE IF NOT EXISTS feedback_patrones (
    id BIGSERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    frecuencia VARCHAR(100) NOT NULL,
    impacto VARCHAR(50) NOT NULL,
    tick_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patrones_created_at ON feedback_patrones(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patrones_tick_id ON feedback_patrones(tick_id);

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
CREATE INDEX IF NOT EXISTS idx_clasificado_revision ON feedback_clasificado(requiere_revision, revision_estado);

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

CREATE TABLE IF NOT EXISTS feedback_temas_recurrentes (
    id           BIGSERIAL PRIMARY KEY,
    periodo_dias INT       NOT NULL DEFAULT 7,
    temas        JSONB     NOT NULL,
    resumen_llm  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_temas_recurrentes_created_at
    ON feedback_temas_recurrentes(created_at DESC);

CREATE OR REPLACE FUNCTION match_feedback(
  query_embedding vector(1024),
  match_count int DEFAULT 10,
  since_date timestamptz DEFAULT NULL
)
RETURNS TABLE (
  external_id varchar,
  texto text,
  sentimiento varchar,
  urgencia varchar,
  categorias jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    fc.external_id,
    fr.texto,
    fc.sentimiento,
    fc.urgencia,
    fc.categorias,
    1 - (fc.embedding <=> query_embedding) AS similarity
  FROM feedback_clasificado fc
  JOIN feedback_raw fr ON fr.external_id = fc.external_id
  WHERE fc.embedding IS NOT NULL
    AND (since_date IS NULL OR fr.timestamp >= since_date)
  ORDER BY fc.embedding <=> query_embedding
  LIMIT match_count;
$$;
