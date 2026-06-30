# ADR-002 — LangGraph como framework del agente

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** LLM | Orquestación | Agentes

## Contexto

El agente ejecuta múltiples operaciones en secuencia: cargar, clasificar, detectar patrones, calcular métricas y persistir.

## Decisión

Elegimos **LangGraph** porque el flujo tiene pasos predecibles modelables como máquina de estados. LangChain AgentExecutor aplica al Copilot (ADR-008), no al pipeline de clasificación.

## Implementación

```
loader → classifier → pattern_detector → actions → metrics → persister
```

El nodo `actions` genera tareas sugeridas (urgente, revisión, patrón, oportunidad). Ver [ADR-009](ADR-009-human-in-the-loop.md) para revisión humana y few-shot dinámico.

- [`backend/src/agent/graph.py`](../../backend/src/agent/graph.py)
- [`backend/worker.py`](../../backend/worker.py)
