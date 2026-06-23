"""
Componente: Copilot RAG — chat para consultas en lenguaje natural.
Comunica con FastAPI POST /copilot/ask (claves en backend).
"""
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

from dashboard.components.ui import scope_badge, source_card
from dashboard.theme import COPILOT_SPINNER_MESSAGES

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "")

SUGGESTED_QUESTIONS = [
    "¿Cuáles son las quejas más frecuentes?",
    "¿Qué temas tienen urgencia alta?",
    "Resume el sentimiento general del feedback.",
]


def _init_session() -> None:
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    if "copilot_limit_period" not in st.session_state:
        st.session_state.copilot_limit_period = False
    if "copilot_since_days" not in st.session_state:
        st.session_state.copilot_since_days = 30


def _ask_copilot(question: str, since_days: int | None) -> dict:
    if not API_KEY:
        raise EnvironmentError("API_KEY no configurada en .env")

    body: dict = {"question": question}
    if since_days is not None:
        body["since_days"] = since_days

    response = httpx.post(
        f"{FASTAPI_URL}/copilot/ask",
        headers={"X-API-Key": API_KEY},
        json=body,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    st.markdown(f"**Fuentes consultadas ({len(sources)})**")
    for src in sources:
        st.markdown(
            source_card(
                src.get("external_id", ""),
                src.get("sentimiento", ""),
                float(src.get("similarity", 0)),
                src.get("texto", ""),
            ),
            unsafe_allow_html=True,
        )


def _resolve_since_days(*, compact: bool) -> int | None:
    """Filtro de fecha inline con badge de alcance."""
    _ = compact
    limit = st.checkbox(
        "Filtrar por fecha",
        value=st.session_state.copilot_limit_period,
        key="copilot_filter_checkbox",
    )
    st.session_state.copilot_limit_period = limit

    if limit:
        days = st.slider(
            "Últimos días",
            1,
            365,
            st.session_state.copilot_since_days,
            key="copilot_days_slider",
        )
        st.session_state.copilot_since_days = days
        scope_badge(f"Últimos {days} días")
        return days

    scope_badge("Todo el histórico")
    return None


def _render_suggestions() -> None:
    st.markdown("**Preguntas sugeridas**")
    cols = st.columns(3)
    for i, question in enumerate(SUGGESTED_QUESTIONS):
        with cols[i]:
            if st.button(question, key=f"copilot_suggest_{i}", use_container_width=True):
                st.session_state.copilot_pending_question = question
                st.rerun()


def _handle_question(prompt: str, since_days: int | None) -> None:
    """Procesa pregunta y guarda en sesión."""
    st.session_state.copilot_messages.append({"role": "user", "content": prompt})
    try:
        result = _ask_copilot(prompt, since_days)
        answer = result.get("answer", "Sin respuesta.")
        sources = result.get("sources", [])
        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )
    except httpx.ConnectError:
        st.session_state.copilot_messages.append(
            {
                "role": "assistant",
                "content": (
                    f"FastAPI no responde en {FASTAPI_URL}. "
                    "Verificá que el servicio esté activo en el puerto 8000."
                ),
                "sources": [],
            }
        )
    except httpx.HTTPStatusError as e:
        msg = "API Key inválida." if e.response.status_code == 401 else f"Error {e.response.status_code}."
        st.session_state.copilot_messages.append({"role": "assistant", "content": msg, "sources": []})
    except EnvironmentError as e:
        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": str(e), "sources": []}
        )
    except Exception:
        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": "Error inesperado. Intenta de nuevo.", "sources": []}
        )


def render_chat(*, compact: bool = False) -> None:
    """Renderiza el chat."""
    _init_session()
    since_days = _resolve_since_days(compact=compact)

    pending = st.session_state.pop("copilot_pending_question", None)
    if pending:
        with st.spinner(COPILOT_SPINNER_MESSAGES[0]):
            _handle_question(pending, since_days)

    if not st.session_state.copilot_messages and compact:
        _render_suggestions()
        st.divider()

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                _render_sources(msg["sources"])

    if prompt := st.chat_input("Escribí tu pregunta sobre el feedback...", key="copilot_chat_input"):
        with st.spinner(COPILOT_SPINNER_MESSAGES[-1]):
            _handle_question(prompt, since_days)
        st.rerun()
