"""Revisión humana de clasificaciones de baja confianza."""

from __future__ import annotations

import os

import httpx
import streamlit as st

from dashboard.components.ui import section_header
from dashboard.supabase_queries import get_clasificados_revision, schema_migration_hint
from shared.confidence import get_confidence_review_threshold

SENTIMIENTOS = ["Positivo", "Negativo", "Neutral"]
URGENCIAS = ["Alta", "Media", "Baja"]


def _api_base() -> str:
    return os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")


def _api_key() -> str:
    return os.getenv("API_KEY", "")


def _patch(path: str, json_body: dict) -> tuple[bool, str]:
    key = _api_key()
    if not key:
        return False, "API_KEY no configurada en .env"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.patch(
                f"{_api_base()}{path}",
                json=json_body,
                headers={"X-API-Key": key},
            )
        if resp.status_code == 200:
            return True, "OK"
        return False, f"Error {resp.status_code}: {resp.text[:200]}"
    except httpx.ConnectError:
        return False, f"No se pudo conectar con FastAPI en {_api_base()}"
    except Exception as e:
        return False, str(e)


def render() -> None:
    threshold = get_confidence_review_threshold()
    section_header(
        "Revisar clasificaciones",
        f"Mensajes con confianza < {threshold:.0%} o marcados por el agente.",
    )

    hint = schema_migration_hint()
    if hint:
        st.warning(hint)

    try:
        items = get_clasificados_revision()
    except Exception as e:
        st.error(f"No se pudieron cargar mensajes: {e}")
        return

    if not items:
        st.success("No hay mensajes pendientes de revisión.")
        return

    st.caption(f"{len(items)} mensaje(s) en cola de revisión.")

    for item in items:
        eid = item.get("external_id", "")
        conf = item.get("confianza")
        pct = f"{(conf or 0) * 100:.0f}%" if conf is not None else "—"
        motivo = item.get("motivo_revision") or "baja_confianza"
        motivo_label = "🔴 Inestable" if motivo == "inestabilidad" else f"conf. {pct}"
        with st.expander(
            f"{eid} — {item.get('sentimiento')} / {item.get('urgencia')} ({motivo_label})",
            expanded=False,
        ):
            if motivo == "inestabilidad":
                st.warning("El modelo dio respuestas distintas en runs repetidos para este mensaje.")
            st.write(item.get("texto") or "—")
            st.caption(f"Resumen IA: {item.get('resumen') or '—'}")
            st.caption(f"Categorías: {', '.join(item.get('categorias') or []) or '—'}")

            if st.button("Confirmar clasificación", key=f"confirm_{eid}"):
                ok, msg = _patch(
                    f"/classifications/{eid}/confirm",
                    {"motivo": "confirmacion_humana"},
                )
                if ok:
                    st.success("Confirmado.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)

            with st.form(key=f"correct_{eid}"):
                sent = st.selectbox(
                    "Sentimiento",
                    SENTIMIENTOS,
                    index=SENTIMIENTOS.index(item.get("sentimiento", "Neutral"))
                    if item.get("sentimiento") in SENTIMIENTOS
                    else 0,
                )
                urg = st.selectbox(
                    "Urgencia",
                    URGENCIAS,
                    index=URGENCIAS.index(item.get("urgencia", "Media"))
                    if item.get("urgencia") in URGENCIAS
                    else 1,
                )
                cats = st.text_input(
                    "Categorías (coma-separadas)",
                    ", ".join(item.get("categorias") or []),
                )
                resumen = st.text_area("Resumen", value=item.get("resumen") or "")
                confianza = st.slider(
                    "Confianza humana",
                    0.0,
                    1.0,
                    float(conf or 0.85),
                    0.05,
                )
                if st.form_submit_button("Guardar corrección"):
                    body = {
                        "sentimiento": sent,
                        "urgencia": urg,
                        "idioma": item.get("idioma") or "Español",
                        "categorias": [c.strip() for c in cats.split(",") if c.strip()],
                        "confianza": confianza,
                        "resumen": resumen,
                        "motivo": "correccion_humana",
                    }
                    ok, msg = _patch(f"/classifications/{eid}", body)
                    if ok:
                        st.success("Corrección guardada. Ejecutá export_fewshot_from_corrections.py para aprendizaje.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
