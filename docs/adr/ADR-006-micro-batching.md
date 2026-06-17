# ADR-006 — Micro-batching con máquina de estados

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** Orquestación | Base de Datos

## Decisión

Micro-batching con `SELECT FOR UPDATE SKIP LOCKED` en Supabase. Sin cola externa.

## Estados

```
pendiente → procesando → procesado
                      → error (retry_count, error_mensaje)
```

## Parámetros

| Parámetro | Env |
|-----------|-----|
| Tamaño lote | `BATCH_SIZE=50` |
| Concurrencia Gemini | `GEMINI_CONCURRENCY=10` |
| Reintentos | `MAX_RETRIES=2` |
| Intervalo | `BATCH_INTERVAL_MINUTES=5` |

## Implementación

- [`backend/src/agent/nodes/loader.py`](../../backend/src/agent/nodes/loader.py)
- [`backend/src/agent/nodes/persister.py`](../../backend/src/agent/nodes/persister.py)
