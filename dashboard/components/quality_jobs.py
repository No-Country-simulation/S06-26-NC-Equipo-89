"""Botones del sidebar para correr eval y consistency vía FastAPI."""

from __future__ import annotations

import os

import httpx
import streamlit as st

_JOB_TIMEOUT_S = 600.0


def _api_base() -> str:
    return os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")


def _api_key() -> str:
    return os.getenv("API_KEY", "")


def _post_quality(path: str) -> tuple[bool, dict | str]:
    key = _api_key()
    if not key:
        return False, "API_KEY no configurada en .env"
    try:
        with httpx.Client(timeout=_JOB_TIMEOUT_S) as client:
            resp = client.post(
                f"{_api_base()}{path}",
                headers={"X-API-Key": key},
            )
        if resp.status_code == 200:
            return True, resp.json()
        return False, f"Error {resp.status_code}: {resp.text[:300]}"
    except httpx.TimeoutException:
        return False, "Tiempo de espera agotado (>10 min). Revisá logs del API."
    except httpx.ConnectError:
        return False, f"No se pudo conectar con FastAPI en {_api_base()}"
    except Exception as e:
        return False, str(e)


def render_sidebar() -> None:
    """Controles manuales de calidad del clasificador."""
    st.markdown("**Calidad del modelo**")
    st.caption(
        "Corre evaluación y estabilidad contra el golden set. "
        "Los resultados aparecen en **Vista General**."
    )

    if st.button(
        "Ejecutar evaluación",
        key="run_quality_eval",
        width="stretch",
        type="secondary",
        help="Exactitud vs golden set (~10 casos, 1 llamada LLM c/u).",
    ):
        with st.spinner("Evaluando clasificador… puede tardar varios minutos."):
            ok, result = _post_quality("/quality/eval")
        if ok and isinstance(result, dict):
            st.session_state["fc_last_quality_msg"] = (
                f"Eval OK — exactitud {result.get('exact_match_pct', 0)}% "
                f"({result.get('exact_match', 0)}/{result.get('total', 0)} casos)."
            )
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(str(result))

    if st.button(
        "Ejecutar estabilidad",
        key="run_quality_consistency",
        width="stretch",
        type="secondary",
        help="Mismo golden set varias veces por mensaje (más lento).",
    ):
        with st.spinner("Midiendo estabilidad… puede tardar varios minutos."):
            ok, result = _post_quality("/quality/consistency")
        if ok and isinstance(result, dict):
            st.session_state["fc_last_quality_msg"] = (
                f"Estabilidad OK — promedio {result.get('estabilidad_promedio', 0)}% · "
                f"exactitud {result.get('exact_match_pct', 0)}%."
            )
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(str(result))

    msg = st.session_state.pop("fc_last_quality_msg", None)
    if msg:
        st.success(msg)
