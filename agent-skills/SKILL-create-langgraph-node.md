---
name: create-langgraph-node
description: >
  Genera un nodo de procesamiento atómico para el StateGraph del pipeline de clasificación.
  Trigger: "crear nodo langgraph", "nuevo nodo", "agregar paso al agente"
metadata:
  author: Diego Silvestre
  version: "1.0"
---

# SKILL: Generar Nodo LangGraph

## 1. Contexto y Activación
**Cuándo usar:** El usuario requiere un nuevo paso de procesamiento dentro del flujo del agente (ej. detectar patrones, calcular métricas).
**Output esperado:** Un archivo Python (`.py`) en `src/agents/nodes/` exportando una función asíncrona que recibe y devuelve el estado del grafo.

**Información requerida antes de empezar:**
- [ ] Definición del TypedDict del `State` global.
- [ ] Objetivo exacto del nodo (qué lee del estado y qué escribe).

## 2. Flujo de Ejecución (Máximo 6 pasos)
> **Regla de IA:** Este skill es una instrucción atómica para UNA tarea específica.
1. Identificar las variables del `State` que el nodo consumirá.
2. Identificar qué variables del `State` mutará o añadirá.
3. Crear la función del nodo con la firma estricta `async def node_name(state: GraphState) -> dict:`.
4. Implementar validaciones tempranas dentro del nodo (ej. si el batch está vacío, retornar sin procesar).
5. Retornar únicamente el diccionario con las claves del estado que deben actualizarse.

## 3. Patrones Críticos (Critical Patterns)
### Pattern 1: Pureza del Nodo y Retorno Parcial
En LangGraph, los nodos deben retornar un diccionario con *sólo* las claves que se están actualizando. El framework se encarga de hacer el merge con el estado global.
```python
# Good example: Retorno limpio y manejo de errores
import structlog

logger = structlog.get_logger()

async def classify_feedback_node(state: GraphState) -> dict:
    batch = state.get("current_batch", [])
    if not batch:
        logger.info("empty_batch_skipped")
        return {"processed_items": []}
    
    # Lógica de Gemini Flash-Lite aquí...
    
    return {"processed_items": results_list}
```

## 4. Casos de Uso (Code Examples)
Example 1: Nodo de detección de idioma previo a la clasificación.

```python
async def detect_language_node(state: GraphState) -> dict:
    text_to_process = state["raw_text"]
    # ... logica ...
    return {"language": detected_lang}
```

## 5. Anti-Patrones (Reglas Inquebrantables)
Don't: Modificar el estado original y devolverlo completo.
Esto causa problemas de concurrencia y sobreescritura inintencionada de variables manejadas por otros nodos concurrentes.

```python
# Bad example - DON'T do this under any circumstance
async def bad_node(state: GraphState) -> dict:
    state["new_value"] = "xyz" # ❌ Mutación directa
    return state # ❌ Retornar todo el estado
```

## 6. Quick Reference
Tarea Frecuente         Snippet / Comando
Testear nodo            `pytest tests/nodes/test_[nombre].py`
Definir State           `class GraphState(TypedDict):`

## 7. Recursos Externos
LangGraph Docs: https://python.langchain.com/docs/langgraph/
