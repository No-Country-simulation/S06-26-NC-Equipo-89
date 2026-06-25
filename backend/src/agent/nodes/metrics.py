import structlog
from collections import Counter
from src.agent.state import FeedbackState

logger = structlog.get_logger()

async def metrics_node(state: FeedbackState) -> dict:
    processed = state.get("processed_items", [])
    errors = state.get("errors", [])
    batch = state.get("current_batch", [])
    if not batch:
        return {"metrics": {}}

    metrics: dict = {
        "total_procesados": len(processed),
        "errores_en_lote": len(errors),
        "tamano_lote": len(batch),
    }

    if not processed:
        logger.info("metrics_heartbeat", **metrics)
        return {"metrics": metrics}

    sentimientos = Counter(item["classification"]["sentimiento"] for item in processed)
    urgencias = Counter(item["classification"]["urgencia"] for item in processed)

    # Extraemos categorías, que son listas
    todas_categorias = []
    for item in processed:
        todas_categorias.extend(item["classification"].get("categorias", []))
    categorias_counter = Counter(todas_categorias)

    metrics.update(
        {
            "sentimientos": dict(sentimientos),
            "urgencias": dict(urgencias),
            "categorias_top": dict(categorias_counter.most_common(5)),
        }
    )

    logger.info("metrics_calculated", total=metrics["total_procesados"])
    return {"metrics": metrics}
