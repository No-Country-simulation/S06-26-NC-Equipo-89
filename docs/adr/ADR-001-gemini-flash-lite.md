# ADR-001 — Gemini Flash-Lite como motor NLP

**Fecha:** 11 de junio de 2026  
**Estado:** Aceptado  
**Etiquetas:** LLM | NLP | Clasificación

## Contexto

El requerimiento técnico especifica BERT, RoBERTa o GPT API. El feedback llega en español coloquial de empresas bolivianas y latinoamericanas.

## Decisión

Elegimos **Gemini Flash-Lite** porque supera a BERT/RoBERTa en texto corto e informal sin dataset de entrenamiento propio. Cubre el requerimiento siendo la tercera opción listada (GPT API), reemplazada por su equivalente Google de menor costo.

## Implementación

- [`backend/src/tools/gemini_client.py`](../../backend/src/tools/gemini_client.py)
- [`backend/src/agent/nodes/classifier.py`](../../backend/src/agent/nodes/classifier.py)
