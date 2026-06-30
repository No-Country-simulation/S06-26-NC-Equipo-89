# Propuesta de expansión — más fuentes, mejores decisiones

Documento de **propuesta post-simulación**. No forma parte del entregable del reto No-Country; describe cómo el mismo pipeline podría ampliarse cuando la empresa conecte más canales de feedback.

## Idea central

Hoy Feedback Classifier unifica **WhatsApp, formularios web y encuestas** en un solo flujo de clasificación. Una organización con visión **data-driven** podría **añadir fuentes** al mismo pipeline para enriquecer patrones, acciones sugeridas y el Copilot — y así **priorizar mejoras con más contexto**, sin cambiar la arquitectura base.

```
Nuevas fuentes → n8n / API ingest → feedback_raw → mismo agente LangGraph → dashboard
```

## Fuentes candidatas (propuesta)

| Fuente | Valor para decisiones |
|--------|------------------------|
| Zendesk / Intercom | Tickets de soporte recurrentes |
| App Store / Play Store | Reseñas públicas por versión |
| NPS / encuestas post-compra | Tendencias de satisfacción |
| Email / chat interno | Escalaciones no visibles en WhatsApp |
| CRM (HubSpot, etc.) | Vincular queja con cliente/plan |

Cada fuente se normaliza a `texto + fuente + timestamp` (igual que hoy) y entra por `/ingest` o workflow n8n nuevo.

## Qué ganaría la empresa

- **Patrones más representativos** (no solo WhatsApp).
- **Acciones sugeridas** con mayor cobertura de canales.
- **Copilot RAG** respondiendo sobre todo el feedback indexado.
- **Dashboard único** de sentimiento y urgencia cross-canal.

## Qué no incluye esta propuesta

- Entrenamiento de modelos propios (fine-tuning) — fuera de alcance.
- Plataformas cloud de ML (Vertex, Azure ML) — no necesarias para esta expansión.
- Multi-tenant / RLS — otro eje de evolución operativa.

## Cómo encaja con lo ya construido

| Componente actual | Reutilizable |
|-------------------|--------------|
| FastAPI `/ingest` | Sí — nuevo conector = mismo contrato |
| Worker LangGraph | Sí — sin cambios de grafo |
| Supabase `feedback_raw` | Sí — campo `fuente` distingue origen |
| Dashboard + export | Sí — filtros por fuente ya existen |
| Acciones + revisión humana | Sí — mismas reglas |

## Referencias

- [Estado de implementación](../estado-implementacion.md)
- [Plan clasificador automejora](plan-clasificador-automejora.md)
- [ADR-003 n8n](../adr/ADR-003-n8n-normalizacion.md)
