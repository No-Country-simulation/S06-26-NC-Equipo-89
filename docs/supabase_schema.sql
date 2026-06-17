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

CREATE TABLE IF NOT EXISTS feedback_clasificado (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL REFERENCES feedback_raw(external_id) ON DELETE CASCADE,
    sentimiento VARCHAR(50) NOT NULL,
    urgencia VARCHAR(50) NOT NULL,
    idioma VARCHAR(50) NOT NULL,
    categorias JSONB NOT NULL DEFAULT '[]'::jsonb,
    confianza FLOAT,
    resumen TEXT,
    embedding vector(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clasificado_sentimiento ON feedback_clasificado(sentimiento);
CREATE INDEX IF NOT EXISTS idx_clasificado_urgencia ON feedback_clasificado(urgencia);
CREATE INDEX IF NOT EXISTS idx_clasificado_embedding
  ON feedback_clasificado USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS feedback_metricas (
    id BIGSERIAL PRIMARY KEY,
    datos_metricas JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback_patrones (
    id BIGSERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    frecuencia VARCHAR(100) NOT NULL,
    impacto VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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
