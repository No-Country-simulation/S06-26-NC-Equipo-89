-- Fase 5: RAG Copilot — pgvector + búsqueda semántica
-- Ejecutar en el SQL Editor de Supabase

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE feedback_clasificado
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

CREATE INDEX IF NOT EXISTS idx_clasificado_embedding
  ON feedback_clasificado USING hnsw (embedding vector_cosine_ops);

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
