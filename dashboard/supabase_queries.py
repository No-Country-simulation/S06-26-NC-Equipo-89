"""
Capa de acceso a datos del Dashboard.
Centraliza todas las consultas a Supabase.
Los componentes NO deben importar supabase directamente.
"""
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_client() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL y SUPABASE_KEY deben estar en el archivo .env")
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

    # Patrones del último batch
    patrones_res = (
        client.table("feedback_patrones")
        .select("id", count="exact")
        .execute()
    )

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

@st.cache_data(ttl=30)
def get_alertas_urgencia_alta(limit: int = 20) -> list[dict]:
    """Últimos N mensajes con urgencia Alta, incluyendo texto original."""
    client = get_client()
    res = (
        client.table("feedback_clasificado")
        .select("external_id, urgencia, categorias, created_at, feedback_raw(fuente, texto, timestamp)")
        .eq("urgencia", "Alta")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = []
    for item in (res.data or []):
        raw = item.get("feedback_raw") or {}
        rows.append({
            "external_id": item.get("external_id", ""),
            "fuente": raw.get("fuente", ""),
            "texto": raw.get("texto", ""),
            "categorias": ", ".join(item.get("categorias", [])),
            "timestamp": raw.get("timestamp", ""),
        })
    return rows


# ─── PATRONES ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_patrones(impacto_filtro: str | None = None) -> list[dict]:
    """Patrones detectados por el agente, opcionalmente filtrados por impacto."""
    client = get_client()
    query = client.table("feedback_patrones").select("*").order("created_at", desc=True)
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
    rows = []
    for item in (res.data or []):
        raw = item.get("feedback_raw") or {}
        rows.append({
            "external_id": item.get("external_id", ""),
            "fuente": raw.get("fuente", ""),
            "texto": raw.get("texto", ""),
            "timestamp": raw.get("timestamp", ""),
            "sentimiento": item.get("sentimiento", ""),
            "urgencia": item.get("urgencia", ""),
            "idioma": item.get("idioma", ""),
            "categorias": item.get("categorias", []),
            "confianza": item.get("confianza"),
            "resumen": item.get("resumen", ""),
            "clasificado_at": item.get("created_at", ""),
        })
    return rows


@st.cache_data(ttl=60)
def get_ultimo_lote_metricas() -> dict | None:
    """Última fila de feedback_metricas (resumen del batch más reciente)."""
    client = get_client()
    res = (
        client.table("feedback_metricas")
        .select("datos_metricas, created_at")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    row = res.data[0]
    datos = row.get("datos_metricas") or {}
    if isinstance(datos, str):
        import json
        datos = json.loads(datos)
    return {
        "created_at": row.get("created_at"),
        "datos": datos,
    }
