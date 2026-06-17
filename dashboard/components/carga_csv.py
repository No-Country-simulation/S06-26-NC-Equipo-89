"""
Componente: Carga manual de feedback vía CSV (ADR-003).
Envía el archivo a FastAPI POST /ingest/csv.
"""
import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "")


def render() -> None:
    st.subheader("Carga manual CSV")
    st.caption(
        "Sube un archivo CSV con columna **texto** (obligatoria). "
        "Opcionales: **fuente**, **external_id**."
    )

    st.markdown(
        """
        Ejemplo:
        ```csv
        texto,fuente,external_id
        "La app se cierra sola",csv,csv-001
        "Muy buen servicio",csv,
        ```
        """
    )

    uploaded = st.file_uploader("Seleccionar CSV", type=["csv"])

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.markdown("**Vista previa (primeras 5 filas)**")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo leer el CSV: {e}")
            return

        if "texto" not in df.columns:
            st.error("El CSV debe tener una columna llamada `texto`.")
            return

        if st.button("Enviar a cola de procesamiento", type="primary"):
            if not API_KEY:
                st.error("API_KEY no configurada en .env")
                return

            uploaded.seek(0)
            try:
                with st.spinner("Enviando feedback..."):
                    response = httpx.post(
                        f"{FASTAPI_URL}/ingest/csv",
                        headers={"X-API-Key": API_KEY},
                        files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    result = response.json()
                st.success(
                    f"Listo: {result.get('inserted', 0)} mensajes encolados, "
                    f"{result.get('skipped', 0)} omitidos."
                )
            except httpx.ConnectError:
                st.error(f"No se pudo conectar con FastAPI en {FASTAPI_URL}")
            except httpx.HTTPStatusError as e:
                st.error(f"Error del servidor ({e.response.status_code}): {e.response.text}")
            except Exception:
                st.error("Error inesperado al subir el CSV.")
