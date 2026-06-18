"""
Componente: Carga manual de feedback — CSV, JSON, Excel (ADR-003).
Wizard de 3 pasos: subir → preview → confirmar.
"""
import os
import time

import httpx
import streamlit as st
from dotenv import load_dotenv

from dashboard.components.loaders import (
    LoaderError,
    MAX_ROWS_WARNING,
    count_skipped_rows,
    parse_upload,
    sample_csv_template,
    to_csv_bytes,
)
from dashboard.components.ui import section_header
from dashboard.health import check_fastapi_health

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "")

STEP_LABELS = {1: "Subir archivo", 2: "Vista previa", 3: "Confirmar envío"}


def _init_wizard() -> None:
    if "upload_step" not in st.session_state:
        st.session_state.upload_step = 1
    if "upload_df" not in st.session_state:
        st.session_state.upload_df = None
    if "upload_fmt" not in st.session_state:
        st.session_state.upload_fmt = ""
    if "upload_skipped" not in st.session_state:
        st.session_state.upload_skipped = 0
    if "upload_success_msg" not in st.session_state:
        st.session_state.upload_success_msg = None


def _reset_wizard() -> None:
    st.session_state.upload_step = 1
    st.session_state.upload_df = None
    st.session_state.upload_fmt = ""
    st.session_state.upload_skipped = 0


def render() -> None:
    _init_wizard()
    section_header(
        "Carga de datos",
        "Sube CSV, JSON o Excel. El agente procesará los mensajes en el próximo ciclo del worker.",
    )

    ok, health_msg = check_fastapi_health()
    if not ok:
        st.warning(health_msg)

    if st.session_state.upload_success_msg:
        st.success(st.session_state.upload_success_msg)
        if st.button("Nueva carga", key="upload_new"):
            st.session_state.upload_success_msg = None
            _reset_wizard()
            st.rerun()

    step = st.session_state.upload_step
    st.progress(step / 3, text=f"Paso {step}/3 — {STEP_LABELS[step]}")

    # ── Paso 1: Subir ─────────────────────────────────────────────────────────
    if step == 1:
        st.markdown(
            '<div class="fc-upload-zone">Arrastrá o seleccioná un archivo</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            label="Descargar plantilla CSV de ejemplo",
            data=sample_csv_template(),
            file_name="plantilla_feedback.csv",
            mime="text/csv",
        )
        uploaded = st.file_uploader(
            "Seleccionar archivo",
            type=["csv", "json", "xlsx", "xls"],
            help="Máximo recomendado: 500 filas por carga",
            key="upload_file_input",
        )
        if uploaded is None:
            return

        try:
            skipped = count_skipped_rows(uploaded.name, uploaded.getvalue())
            df, fmt = parse_upload(uploaded.name, uploaded.getvalue())
            st.session_state.upload_df = df
            st.session_state.upload_fmt = fmt
            st.session_state.upload_skipped = skipped
            st.session_state.upload_step = 2
            st.rerun()
        except LoaderError as e:
            st.error(str(e))

    # ── Paso 2: Preview ───────────────────────────────────────────────────────
    elif step == 2:
        df = st.session_state.upload_df
        fmt = st.session_state.upload_fmt
        skipped = st.session_state.upload_skipped

        if df is None:
            _reset_wizard()
            st.rerun()
            return

        st.success(f"✓ **{len(df)}** fila(s) válida(s) · ✗ **{skipped}** sin texto")
        if len(df) > MAX_ROWS_WARNING:
            st.warning(
                f"El archivo tiene más de {MAX_ROWS_WARNING} filas. "
                "La carga puede tardar unos segundos."
            )

        st.markdown("**Vista previa (primeras 5 filas)**")
        st.dataframe(df.head(), use_container_width=True)

        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("← Volver", use_container_width=True):
                _reset_wizard()
                st.rerun()
        with col_next:
            if st.button("Continuar →", type="primary", use_container_width=True):
                st.session_state.upload_step = 3
                st.rerun()

    # ── Paso 3: Confirmar ─────────────────────────────────────────────────────
    elif step == 3:
        df = st.session_state.upload_df
        if df is None:
            _reset_wizard()
            st.rerun()
            return

        st.info(f"Se enviarán **{len(df)}** mensajes a la cola de procesamiento.")

        col_back, col_send = st.columns(2)
        with col_back:
            if st.button("← Volver", use_container_width=True):
                st.session_state.upload_step = 2
                st.rerun()
        with col_send:
            if st.button("Enviar a cola de procesamiento", type="primary", use_container_width=True):
                if not API_KEY:
                    st.error("API_KEY no configurada en .env")
                    return

                csv_bytes = to_csv_bytes(df)
                try:
                    with st.spinner("Enviando feedback a FastAPI..."):
                        response = httpx.post(
                            f"{FASTAPI_URL}/ingest/csv",
                            headers={"X-API-Key": API_KEY},
                            files={"file": ("upload.csv", csv_bytes, "text/csv")},
                            timeout=120.0,
                        )
                        response.raise_for_status()
                        result = response.json()
                    st.session_state.upload_success_msg = (
                        f"Listo: **{result.get('inserted', 0)}** mensajes encolados, "
                        f"**{result.get('skipped', 0)}** omitidos. "
                        "El worker los clasificará en el próximo ciclo (~5 min)."
                    )
                    _reset_wizard()
                    st.cache_data.clear()
                    time.sleep(0.5)
                    st.rerun()
                except httpx.ConnectError:
                    st.error(
                        f"FastAPI no responde en {FASTAPI_URL} — verificar puerto 8000"
                    )
                except httpx.HTTPStatusError as e:
                    st.error(f"Error del servidor ({e.response.status_code}): {e.response.text}")
                except Exception:
                    st.error("Error inesperado al subir el archivo.")
