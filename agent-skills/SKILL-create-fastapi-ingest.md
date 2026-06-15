---
name: create-fastapi-endpoint
description: >
  Genera un endpoint de entrada para recibir JSON, validar con Pydantic y persistir.
  Trigger: "crear endpoint fastapi", "nueva ruta de ingesta", "recibir datos de n8n"
metadata:
  author: Diego Silvestre
  version: "1.0"
---

# SKILL: Generar Endpoint FastAPI de Ingesta

## 1. Contexto y Activación
**Cuándo usar:** El usuario pide crear o modificar una ruta de la API para recibir datos externos (n8n, CSV manual).
**Output esperado:** Modelo Pydantic para validación y función asíncrona de endpoint en `src/api/routes/`.

**Información requerida antes de empezar:**
- [ ] Estructura exacta del JSON que enviará la fuente.
- [ ] Nombre de la tabla de Supabase destino.

## 2. Flujo de Ejecución (Máximo 6 pasos)
> **Regla de IA:** Este skill es una instrucción atómica para UNA tarea específica.
1. Definir el esquema de validación Pydantic (`BaseModel`) basado en el JSON esperado.
2. Crear el endpoint `APIRouter` usando dependencias de inyección para el cliente de BD.
3. Parsear y validar el payload entrante automáticamente vía FastAPI.
4. Ejecutar la inserción en Supabase (tabla `feedback_raw`).
5. Retornar un `202 Accepted` si es asíncrono o `200 OK` si es persistencia síncrona, sin esperar procesamiento del agente.

## 3. Patrones Críticos (Critical Patterns)
### Pattern 1: Aislamiento del Backend (ADR-004)
FastAPI es una pasarela "tonta". Su única responsabilidad es asegurar que la basura no entre a la BD. No invoca a LangGraph.
```python
# Good example: Ingesta pura
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class FeedbackPayload(BaseModel):
    external_id: str
    fuente: str
    texto: str
    timestamp: datetime
    metadata: dict = {}

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_feedback(payload: FeedbackPayload, db=Depends(get_db)):
    # Persistir en tabla raw, devolver confirmación inmediata.
    await db.insert("feedback_raw", payload.model_dump())
    return {"status": "success", "id": payload.external_id}
```

## 4. Casos de Uso (Code Examples)
Example 1: Ingesta manual por CSV desde Streamlit.

```python
@router.post("/ingest/csv", status_code=status.HTTP_202_ACCEPTED)
async def ingest_csv(file: UploadFile = File(...), db=Depends(get_db)):
    # Parseo de CSV en memoria y guardado en DB
    # ...
    return {"status": "queued_for_processing"}
```

## 5. Anti-Patrones (Reglas Inquebrantables)
Don't: Invocar al pipeline de LangGraph o Gemini directamente desde el router.
Esto rompe el modelo de micro-batching (ADR-006) y el diseño arquitectónico de desacoplamiento.

```python
# Bad example - DON'T do this under any circumstance
@router.post("/ingest")
async def bad_ingest(payload: FeedbackPayload):
    # ❌ LLAMAR AL AGENTE DIRECTAMENTE
    result = await agent.invoke({"text": payload.texto}) 
    return result
```

## 6. Quick Reference
Tarea Frecuente         Snippet / Comando
Run server              `fastapi dev src/api/main.py`
Validación estricta     `model_config = ConfigDict(extra='forbid')`

## 7. Recursos Externos
FastAPI Pydantic Docs: https://fastapi.tiangolo.com/tutorial/body/
