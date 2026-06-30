# Architecture Decision Records (ADR)

Registro formal de decisiones técnicas del proyecto **Feedback Classifier**.  
Cada ADR documenta el **contexto**, la **decisión** tomada y su **implementación** en el repositorio.

> Los ADR son la fuente de verdad para entender *por qué* el sistema está construido así.  
> Para el estado actual del código, ver [estado-implementacion.md](../estado-implementacion.md).

## Índice

| ID | Decisión | Estado |
|----|----------|--------|
| [ADR-001](ADR-001-gemini-flash-lite.md) | Gemini Flash-Lite como motor NLP (+ fallback Groq) | Aceptado |
| [ADR-002](ADR-002-langgraph.md) | LangGraph para orquestación del agente | Aceptado |
| [ADR-003](ADR-003-n8n-normalizacion.md) | n8n como capa de normalización (3 fuentes) | Aceptado |
| [ADR-004](ADR-004-fastapi-ingesta.md) | FastAPI como API de ingesta | Aceptado |
| [ADR-005](ADR-005-supabase.md) | Supabase (PostgreSQL + pgvector) | Aceptado |
| [ADR-006](ADR-006-micro-batching.md) | Micro-batching y reintentos | Aceptado |
| [ADR-007](ADR-007-streamlit-dashboard.md) | Dashboard Streamlit + BI | Aceptado |
| [ADR-008](ADR-008-copilot-rag.md) | Copilot RAG (Cohere + FastAPI) | Aceptado |
| [ADR-009](ADR-009-human-in-the-loop.md) | Human-in-the-loop y few-shot dinámico | Aceptado |
| [ADR-010](ADR-010-taxonomia-y-estabilidad.md) | Taxonomía cerrada de categorías y medición de estabilidad | Aceptado |

## Cómo leerlos

1. Empezá por **ADR-003** (fuentes de datos) y **ADR-002** (pipeline del agente) para entender el flujo.
2. **ADR-001** y **ADR-008** explican las decisiones de LLM y RAG.
3. **ADR-005** y **ADR-006** cubren persistencia y procesamiento por lotes.
4. **ADR-009** y **ADR-010** documentan revisión humana, mejora por few-shot, taxonomía cerrada y medición de estabilidad.

## Formato

Seguimos el formato estándar: *Contexto → Decisión → Implementación*.  
Nuevas decisiones arquitectónicas deben agregarse como `ADR-00X-titulo.md` en esta carpeta.
