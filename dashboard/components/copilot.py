"""
Componente: Copilot RAG — chat para consultas en lenguaje natural.
Comunica con FastAPI POST /copilot/ask (claves en backend).
"""
import os
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "")


def _init_session() -> None:
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []


def _ask_copilot(question: str, since_days: int) -> dict:
    if not API_KEY:
        raise EnvironmentError("API_KEY no configurada en .env")

    response = httpx.post(
        f"{FASTAPI_URL}/copilot/ask",
        headers={"X-API-Key": API_KEY},
        json={"question": question, "since_days": since_days},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def render() -> None:
    _init_session()

    st.subheader("Copilot — Asistente de Feedback")
    st.caption(
        "Pregunta en lenguaje natural sobre el feedback de tus clientes. "
        "Las respuestas se basan en datos reales indexados semánticamente."
    )

    since_days = st.slider(
        "Período de búsqueda (días)",
        min_value=1,
        max_value=90,
        value=7,
        help="Limita la búsqueda vectorial a feedback reciente.",
    )

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"Fuentes consultadas ({len(msg['sources'])})"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"**{src['external_id']}** · {src['sentimiento']} · "
                            f"similitud {src['similarity']:.2f}"
                        )
                        st.caption(src["texto"][:200] + ("..." if len(src["texto"]) > 200 else ""))

    if prompt := st.chat_input("Ej: ¿Cuáles son las quejas más frecuentes esta semana?"):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Buscando feedback relevante y generando respuesta..."):
                try:
                    result = _ask_copilot(prompt, since_days)
                    answer = result.get("answer", "Sin respuesta.")
                    sources = result.get("sources", [])
                    st.markdown(answer)
                    if sources:
                        with st.expander(f"Fuentes consultadas ({len(sources)})"):
                            for src in sources:
                                st.markdown(
                                    f"**{src['external_id']}** · {src['sentimiento']} · "
                                    f"similitud {src['similarity']:.2f}"
                                )
                                texto = src.get("texto", "")
                                st.caption(texto[:200] + ("..." if len(texto) > 200 else ""))
                    st.session_state.copilot_messages.append(
                        {"role": "assistant", "content": answer, "sources": sources}
                    )
                except httpx.ConnectError:
                    st.error(
                        "No se pudo conectar con el backend FastAPI. "
                        f"Verifica que esté corriendo en {FASTAPI_URL}."
                    )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        st.error("API Key inválida. Revisa API_KEY en tu .env.")
                    else:
                        st.error(f"Error del servidor ({e.response.status_code}). Intenta de nuevo.")
                except EnvironmentError as e:
                    st.error(str(e))
                except Exception:
                    st.error("Ocurrió un error inesperado. Intenta de nuevo en unos segundos.")
