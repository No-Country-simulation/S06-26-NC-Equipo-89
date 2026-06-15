import structlog
import json
from src.agent.state import FeedbackState
from src.tools.supabase_client import get_db

logger = structlog.get_logger()

async def persister_node(state: FeedbackState) -> dict:
    batch = state.get("current_batch", [])
    processed = state.get("processed_items", [])
    errors = state.get("errors", [])
    patterns = state.get("patterns", [])
    metrics = state.get("metrics", {})
    
    if not batch:
        return {}
        
    pool = await get_db()
    
    # Transacción para persistir todo el lote
    async with pool.acquire() as conn:
        async with conn.transaction():
            success_ids = [item["external_id"] for item in processed]
            error_ids = [item["external_id"] for item in errors]
            
            # 1. Actualizar feedback_raw a 'procesado'
            if success_ids:
                await conn.execute("UPDATE feedback_raw SET estado = 'procesado' WHERE external_id = ANY($1)", success_ids)
                
            # 2. Actualizar feedback_raw a 'error' (para reintentos)
            if error_ids:
                await conn.execute("UPDATE feedback_raw SET estado = 'error' WHERE external_id = ANY($1)", error_ids)
                
            # 3. Insertar en feedback_clasificado
            if processed:
                records = []
                for p in processed:
                    c = p["classification"]
                    records.append((
                        p["external_id"], 
                        c["sentimiento"], 
                        c["urgencia"], 
                        c["idioma"], 
                        json.dumps(c.get("categorias", []))
                    ))
                
                await conn.executemany("""
                    INSERT INTO feedback_clasificado (external_id, sentimiento, urgencia, idioma, categorias)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (external_id) DO NOTHING
                """, records)
                
            # 4. Insertar métricas agregadas del lote
            if metrics:
                await conn.execute(
                    "INSERT INTO feedback_metricas (datos_metricas) VALUES ($1)", 
                    json.dumps(metrics)
                )

            # 5. Insertar patrones detectados
            if patterns:
                pattern_records = [(p["descripcion"], p["frecuencia_estimada"], p["nivel_impacto"]) for p in patterns]
                await conn.executemany("""
                    INSERT INTO feedback_patrones (descripcion, frecuencia, impacto)
                    VALUES ($1, $2, $3)
                """, pattern_records)
            
    logger.info("persister_done", saved_count=len(processed))
    
    # Retornamos el batch vacío para indicar que el ciclo terminó y no repetir
    return {"current_batch": []}
