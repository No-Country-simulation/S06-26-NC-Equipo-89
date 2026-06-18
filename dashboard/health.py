"""Health checks del dashboard — FastAPI y estado del pipeline."""

from __future__ import annotations

import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=30)
def check_fastapi_health() -> tuple[bool, str]:
    """
    Verifica que FastAPI responda en /health.

    Returns:
        (ok, mensaje descriptivo)
    """
    try:
        response = httpx.get(f"{FASTAPI_URL}/health", timeout=3.0)
        if response.status_code == 200:
            return True, "FastAPI operativo"
        return False, f"FastAPI respondió con código {response.status_code}"
    except httpx.ConnectError:
        return False, f"FastAPI no responde en {FASTAPI_URL} — verificar puerto 8000"
    except httpx.TimeoutException:
        return False, "FastAPI no respondió a tiempo — verificar que el servicio esté activo"
    except Exception as e:
        return False, f"Error al verificar FastAPI: {e}"
