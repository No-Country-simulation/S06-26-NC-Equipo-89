-- Fase 4: Schema hardening — retries y campos de clasificación

ALTER TABLE feedback_raw
  ADD COLUMN IF NOT EXISTS error_mensaje TEXT;

ALTER TABLE feedback_clasificado
  ADD COLUMN IF NOT EXISTS confianza FLOAT,
  ADD COLUMN IF NOT EXISTS resumen TEXT;
