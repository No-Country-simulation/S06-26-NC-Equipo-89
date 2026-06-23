"""
Capa de acceso a datos del Dashboard.
Centraliza todas las consultas a Supabase.
Los componentes NO deben importar supabase directamente.
"""
import json
import os

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@st.cache_resource
def get_client() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL y SUPABASE_KEY deben estar en el archivo .env")
    if os.getenv("ENV", "development").lower() == "production":
        if os.getenv("DASHBOARD_READONLY", "").lower() not in ("1", "true", "yes"):
            raise EnvironmentError(
                "En producción use credenciales read-only (DASHBOARD_READONLY=true). "
                "Ver docs/guides/bi-readonly-setup.md"
            )
    return create_client(url, key)


# ─── KPIs ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_kpis() -> dict:
    """Retorna métricas de alto nivel para las tarjetas del dashboard."""
    client = get_client()

    total_res = (
        client.table("feedback_raw")
        .select("id", count="exact")
        .eq("estado", "procesado")
        .execute()
    )
    total_procesados = total_res.count or 0

    # % negativos
    neg_res = (
        client.table("feedback_clasificado")
        .select("id", count="exact")
        .eq("sentimiento", "Negativo")
        .execute()
    )
    total_clas_res = (
        client.table("feedback_clasificado")
        .select("id", count="exact")
        .execute()
    )
    total_clas = total_clas_res.count or 1
    neg_pct = round((neg_res.count or 0) / total_clas * 100, 1)

    # Alertas urgencia alta
    alertas_res = (
        client.table("feedback_clasificado")
        .select("id", count="exact")
        .eq("urgencia", "Alta")
        .execute()
    )

    # Patrones del último tick
    tick_id = get_latest_tick_id()
    patrones_query = client.table("feedback_patrones").select("id", count="exact")
    if tick_id:
        patrones_query = patrones_query.eq("tick_id", tick_id)
    patrones_res = patrones_query.execute()

    return {
        "total_procesados": total_procesados,
        "pct_negativos": neg_pct,
        "alertas_altas": alertas_res.count or 0,
        "total_patrones": patrones_res.count or 0,
    }


# ─── SENTIMIENTO ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_sentimiento_distribucion() -> list[dict]:
    """Distribución de sentimientos para el gráfico de dona."""
    client = get_client()
    res = client.table("feedback_clasificado").select("sentimiento").execute()
    data = res.data or []

    conteo = {"Positivo": 0, "Negativo": 0, "Neutral": 0}
    for row in data:
        s = row.get("sentimiento", "Neutral")
        if s in conteo:
            conteo[s] += 1

    return [{"sentimiento": k, "cantidad": v} for k, v in conteo.items()]


@st.cache_data(ttl=60)
def get_top_categorias(top_n: int = 5) -> list[dict]:
    """Top N categorías más frecuentes (extraídas del array JSONB)."""
    client = get_client()
    res = client.table("feedback_clasificado").select("categorias").execute()
    data = res.data or []

    conteo: dict[str, int] = {}
    for row in data:
        cats = row.get("categorias", [])
        if isinstance(cats, list):
            for cat in cats:
                conteo[cat] = conteo.get(cat, 0) + 1

    sorted_cats = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"categoria": k, "cantidad": v} for k, v in sorted_cats]


# ─── URGENCIA ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_urgencia_distribucion() -> list[dict]:
    """Distribución Alta / Media / Baja para gráficos."""
    client = get_client()
    res = client.table("feedback_clasificado").select("urgencia").execute()
    conteo = {"Alta": 0, "Media": 0, "Baja": 0}
    for row in res.data or []:
        u = row.get("urgencia", "Baja")
        if u in conteo:
            conteo[u] += 1
    return [{"urgencia": k, "cantidad": v} for k, v in conteo.items()]


def _flatten_clasificado_row(item: dict) -> dict:
    """Une fila de feedback_clasificado con su feedback_raw embebido."""
    raw = item.get("feedback_raw") or {}
    return {
        "external_id": item.get("external_id", ""),
        "fuente": raw.get("fuente", ""),
        "texto": raw.get("texto", ""),
        "timestamp": raw.get("timestamp", ""),
        "sentimiento": item.get("sentimiento", ""),
        "urgencia": item.get("urgencia", ""),
        "categorias": item.get("categorias", []),
        "confianza": item.get("confianza"),
        "resumen": item.get("resumen", ""),
        "idioma": item.get("idioma", ""),
        "clasificado_at": item.get("created_at", ""),
    }


@st.cache_data(ttl=30)
def get_mensajes_por_urgencia(urgencia: str | None = None, limit: int = 30) -> list[dict]:
    """Mensajes clasificados filtrados por urgencia, con texto y metadatos."""
    client = get_client()
    query = (
        client.table("feedback_clasificado")
        .select(
            "external_id, sentimiento, urgencia, categorias, confianza, resumen, idioma, "
            "created_at, feedback_raw(fuente, texto, timestamp)"
        )
        .order("created_at", desc=True)
        .limit(limit)
    )
    if urgencia:
        query = query.eq("urgencia", urgencia)
    res = query.execute()
    return [_flatten_clasificado_row(item) for item in (res.data or [])]


# ─── PATRONES ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_latest_tick_id() -> str | None:
    """tick_id del batch más reciente (métricas o patrones)."""
    client = get_client()
    for table in ("feedback_metricas", "feedback_patrones"):
        res = (
            client.table(table)
            .select("tick_id, created_at")
            .not_.is_("tick_id", "null")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if res.data and res.data[0].get("tick_id"):
            return res.data[0]["tick_id"]
    return None


@st.cache_data(ttl=60)
def get_patrones(impacto_filtro: str | None = None, *, latest_tick_only: bool = True) -> list[dict]:
    """Patrones del agente; por defecto solo el último tick del worker."""
    client = get_client()
    query = client.table("feedback_patrones").select("*").order("created_at", desc=True)
    if latest_tick_only:
        tick_id = get_latest_tick_id()
        if tick_id:
            query = query.eq("tick_id", tick_id)
    if impacto_filtro and impacto_filtro != "Todos":
        query = query.eq("impacto", impacto_filtro)
    res = query.execute()
    return res.data or []


# ─── EXPORT / ÚLTIMO LOTE ──────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_clasificados_export() -> list[dict]:
    """Datos clasificados con texto original para export CSV/JSON."""
    client = get_client()
    res = (
        client.table("feedback_clasificado")
        .select(
            "external_id, sentimiento, urgencia, idioma, categorias, confianza, resumen, "
            "created_at, feedback_raw(fuente, texto, timestamp)"
        )
        .order("created_at", desc=True)
        .execute()
    )
    return [_flatten_clasificado_row(item) for item in (res.data or [])]


@st.cache_data(ttl=30)
def get_queue_health() -> dict[str, int]:
    """Resumen de cola de procesamiento (pendientes + errores)."""
    client = get_client()
    pending_res = (
        client.table("feedback_raw")
        .select("id", count="exact")
        .eq("estado", "pendiente")
        .execute()
    )
    error_res = (
        client.table("feedback_raw")
        .select("id", count="exact")
        .eq("estado", "error")
        .execute()
    )
    return {
        "pendientes": pending_res.count or 0,
        "errores": error_res.count or 0,
    }


def get_pending_count() -> int:
    """Cantidad de mensajes en cola sin clasificar."""
    return get_queue_health()["pendientes"]


def get_error_count() -> int:
    """Cantidad de mensajes que agotaron reintentos (estado error)."""
    return get_queue_health()["errores"]


@st.cache_data(ttl=60)
def get_last_activity_at() -> str | None:
    """Timestamp ISO del registro más reciente (raw o clasificado)."""
    client = get_client()
    raw_res = (
        client.table("feedback_raw")
        .select("created_at")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    clas_res = (
        client.table("feedback_clasificado")
        .select("created_at")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    timestamps: list[str] = []
    if raw_res.data:
        timestamps.append(raw_res.data[0].get("created_at", ""))
    if clas_res.data:
        timestamps.append(clas_res.data[0].get("created_at", ""))
    timestamps = [t for t in timestamps if t]
    if not timestamps:
        return None
    return max(timestamps)


@st.cache_data(ttl=60)
def get_ultimo_lote_metricas() -> dict | None:
    """Última fila de feedback_metricas (resumen del batch más reciente)."""
    client = get_client()
    res = (
        client.table("feedback_metricas")
        .select("datos_metricas, created_at, tick_id")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    row = res.data[0]
    datos = row.get("datos_metricas") or {}
    if isinstance(datos, str):
        datos = json.loads(datos)
    return {
        "created_at": row.get("created_at"),
        "tick_id": row.get("tick_id"),
        "datos": datos,
    }
