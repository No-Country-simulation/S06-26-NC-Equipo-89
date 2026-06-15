from langgraph.graph import StateGraph, END
from src.agent.state import FeedbackState
from src.agent.nodes.loader import loader_node
from src.agent.nodes.classifier import classifier_node
from src.agent.nodes.pattern_detector import pattern_detector_node
from src.agent.nodes.metrics import metrics_node
from src.agent.nodes.persister import persister_node

def should_continue(state: FeedbackState):
    if not state.get("current_batch"):
        # Si el lote está vacío, termina el grafo
        return END
    return "classifier"

# Inicializar grafo
workflow = StateGraph(FeedbackState)

# Añadir nodos
workflow.add_node("loader", loader_node)
workflow.add_node("classifier", classifier_node)
workflow.add_node("pattern_detector", pattern_detector_node)
workflow.add_node("metrics", metrics_node)
workflow.add_node("persister", persister_node)

# Punto de entrada
workflow.set_entry_point("loader")

# Conexiones condicionales
workflow.add_conditional_edges("loader", should_continue)

# Flujo secuencial
workflow.add_edge("classifier", "pattern_detector")
workflow.add_edge("pattern_detector", "metrics")
workflow.add_edge("metrics", "persister")
workflow.add_edge("persister", END)

# Compilación
app = workflow.compile()
