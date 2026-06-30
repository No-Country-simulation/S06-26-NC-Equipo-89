-- Migración 010 — motivo_revision en feedback_clasificado
-- Requerida para usar: consistency_check.py --mark-unstable
-- Sin esta migración el script funciona igual (omite el marcado en DB).

ALTER TABLE feedback_clasificado
  ADD COLUMN IF NOT EXISTS motivo_revision TEXT DEFAULT 'baja_confianza';
