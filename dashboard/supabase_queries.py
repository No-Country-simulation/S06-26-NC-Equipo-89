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

from shared.confidence import get_confidence_review_threshold, is_high_confidence

load_dotenv()


def _is_missing_tick_id_column(exc: BaseException) -> bool:
    """True si Supabase/PostgREST reporta que tick_id no existe (migración 007 pendiente)."""
    text = str(exc).lower()
    return "tick_id" in text and ("42703" in text or "does not exist" in text)


@st.cache_data(ttl=300)
def _schema_has_tick_id() -> bool:
    """Detecta si migración 007 está aplicada (columna tick_id en feedback_metricas)."""
    client = get_client()
    try:
        client.table("feedback_metricas").select("tick_id").limit(1).execute()
        return True
    except Exception as e:
        if _is_missing_tick_id_column(e):
            return False
        raise


def schema_migration_hint() -> str | None:
    """Aviso si falta migración 007 en Supabase."""
    if _schema_has_tick_id():
        hints: list[str] = []
        if not _schema_has_acciones():
            hints.append(
                "Migración **008** pendiente (`feedback_acciones`). "
                "Aplicá `docs/database/migrations/008_acciones_y_revision.sql`."
            )
        if not _schema_has_correcciones():
            hints.append(
                "Migración **009** pendiente (`feedback_correcciones`). "
                "Aplicá `docs/database/migrations/009_correcciones_humanas.sql`."
            )
        return " · ".join(hints) if hints else None
    return (
        "Migración **007** pendiente en Supabase (`tick_id`). "
        "El dashboard funciona en modo compatible; aplicá "
        "`docs/database/migrations/007_production_hardening.sql` en el SQL Editor."
    )


@st.cache_data(ttl=300)
def _schema_has_acciones() -> bool:
    client = get_client()
    try:
        client.table("feedback_acciones").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "feedback_acciones" in str(e).lower() and (
            "does not exist" in str(e).lower() or "42P01" in str(e)
        ):
            return False
        raise


@st.cache_data(ttl=300)
def _schema_has_correcciones() -> bool:
    client = get_client()
    try:
        client.table("feedback_correcciones").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "feedback_correcciones" in str(e).lower() and (
            "does not exist" in str(e).lower() or "42P01" in str(e)
        ):
            return False
        raise


@st.cache_data(ttl=300)
def _schema_has_revision_columns() -> bool:
    client = get_client()
    try:
        client.table("feedback_clasificado").select("requiere_revision").limit(1).execute()
        return True
    except Exception as e:
        if "requiere_revision" in str(e).lower() and (
            "does not exist" in str(e).lower() or "42703" in str(e)
        ):
            return False
        raise


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

    # Patrones del último tick (o todos si migración 007 pendiente)
    patrones_query = client.table("feedback_patrones").select("id", count="exact")
    if _schema_has_tick_id():
        tick_id = get_latest_tick_id()
        if tick_id:
            patrones_query = patrones_query.eq("tick_id", tick_id)
    patrones_res = patrones_query.execute()

    threshold = get_confidence_review_threshold()
    clas_all_res = (
        client.table("feedback_clasificado")
        .select("confianza")
        .execute()
    )
    clas_rows = clas_all_res.data or []
    total_clas_count = len(clas_rows) or 1
    alta_conf = sum(
        1 for row in clas_rows if is_high_confidence(row.get("confianza"), threshold)
    )
    pct_alta_confianza = round(alta_conf / total_clas_count * 100, 1)

    acciones_abiertas = 0
    if _schema_has_acciones():
        acc_res = (
            client.table("feedback_acciones")
            .select("id", count="exact")
            .eq("estado", "pendiente")
            .execute()
        )
        acciones_abiertas = acc_res.count or 0

    pendientes_revision = 0
    if _schema_has_revision_columns():
        rev_res = (
            client.table("feedback_clasificado")
            .select("id", count="exact")
            .eq("requiere_revision", True)
            .in_("revision_estado", ["pendiente", "auto"])
            .execute()
        )
        pendientes_revision = rev_res.count or 0

    return {
        "total_procesados": total_procesados,
        "pct_negativos": neg_pct,
        "alertas_altas": alertas_res.count or 0,
        "total_patrones": patrones_res.count or 0,
        "pct_alta_confianza": pct_alta_confianza,
        "acciones_abiertas": acciones_abiertas,
        "pendientes_revision": pendientes_revision,
        "confidence_threshold": threshold,
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
    """tick_id del batch más reciente (métricas o patrones). None si migración 007 pendiente."""
    if not _schema_has_tick_id():
        return None
    client = get_client()
    for table in ("feedback_metricas", "feedback_patrones"):
        try:
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
        except Exception as e:
            if _is_missing_tick_id_column(e):
                return None
            raise
    return None


@st.cache_data(ttl=60)
def get_patrones(impacto_filtro: str | None = None, *, latest_tick_only: bool = True) -> list[dict]:
    """Patrones del agente; por defecto solo el último tick del worker."""
    client = get_client()
    query = client.table("feedback_patrones").select("*").order("created_at", desc=True)
    if latest_tick_only and _schema_has_tick_id():
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
    """Resumen de cola de procesamiento (pendientes, procesando, errores)."""
    client = get_client()
    pending_res = (
        client.table("feedback_raw")
        .select("id", count="exact")
        .eq("estado", "pendiente")
        .execute()
    )
    processing_res = (
        client.table("feedback_raw")
        .select("id", count="exact")
        .eq("estado", "procesando")
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
        "procesando": processing_res.count or 0,
        "errores": error_res.count or 0,
    }


def get_pending_count() -> int:
    """Cantidad de mensajes en cola sin clasificar."""
    return get_queue_health()["pendientes"]


def get_error_count() -> int:
    """Cantidad de mensajes que agotaron reintentos (estado error)."""
    return get_queue_health()["errores"]


@st.cache_data(ttl=30)
def get_worker_activity() -> dict:
    """
    Señales de actividad del worker para el dashboard.

    Combina cola actual, último tick en feedback_metricas y clasificados recientes.
    """
    health = get_queue_health()
    ultimo = get_ultimo_lote_metricas()
    client = get_client()

    clas_5m_res = (
        client.table("feedback_clasificado")
        .select("id", count="exact")
        .gte("created_at", _iso_minutes_ago(5))
        .execute()
    )
    clasificados_ultimos_5m = clas_5m_res.count or 0

    ultimo_ciclo_at = ultimo.get("created_at") if ultimo else None
    datos = (ultimo or {}).get("datos") or {}
    exitos_ultimo = int(datos.get("total_procesados") or 0)
    errores_ultimo = int(datos.get("errores_en_lote") or 0)
    tamano_ultimo = int(datos.get("tamano_lote") or exitos_ultimo + errores_ultimo or 0)
    acciones_ultimo = int(datos.get("acciones_generadas") or 0)

    if health["procesando"] > 0:
        estado_agente = "procesando"
    elif ultimo_ciclo_at and _minutes_since(ultimo_ciclo_at) <= _worker_interval_minutes() + 1:
        estado_agente = "ciclo_reciente"
    else:
        estado_agente = "en_espera"

    return {
        **health,
        "ultimo_ciclo_at": ultimo_ciclo_at,
        "exitos_ultimo_ciclo": exitos_ultimo,
        "errores_ultimo_ciclo": errores_ultimo,
        "tamano_ultimo_ciclo": tamano_ultimo,
        "acciones_ultimo_ciclo": acciones_ultimo,
        "clasificados_ultimos_5m": clasificados_ultimos_5m,
        "estado_agente": estado_agente,
        "intervalo_minutos": _worker_interval_minutes(),
    }


def _worker_interval_minutes() -> int:
    raw = os.getenv("BATCH_INTERVAL_MINUTES", "5")
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def _iso_minutes_ago(minutes: int) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _minutes_since(iso_ts: str) -> int:
    from datetime import datetime, timezone

    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return int((now - ts).total_seconds() // 60)
    except (ValueError, TypeError):
        return 9999


def format_relative_iso(iso_ts: str) -> str:
    """Texto relativo en español para timestamps ISO."""
    minutes = _minutes_since(iso_ts)
    if minutes < 1:
        return "hace un momento"
    if minutes == 1:
        return "hace 1 min"
    if minutes < 60:
        return f"hace {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"hace {hours} h"
    days = hours // 24
    return f"hace {days} d"


@st.cache_data(ttl=60)
def get_last_activity_at() -> str | None:
    """Timestamp ISO del registro más reciente (raw, clasificado o ciclo del worker)."""
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
    metricas_res = (
        client.table("feedback_metricas")
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
    if metricas_res.data:
        timestamps.append(metricas_res.data[0].get("created_at", ""))
    timestamps = [t for t in timestamps if t]
    if not timestamps:
        return None
    return max(timestamps)


@st.cache_data(ttl=60)
def get_ultimo_lote_metricas() -> dict | None:
    """Última fila de feedback_metricas (resumen del batch más reciente)."""
    client = get_client()
    columns = "datos_metricas, created_at, tick_id" if _schema_has_tick_id() else "datos_metricas, created_at"
    res = (
        client.table("feedback_metricas")
        .select(columns)
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
        "tick_id": row.get("tick_id") if _schema_has_tick_id() else None,
        "datos": datos,
    }


# ─── ACCIONES Y ALERTAS (Fase 2) ───────────────────────────────────────────────


@st.cache_data(ttl=30)
def get_acciones_pendientes(limit: int = 50) -> list[dict]:
    """Acciones sugeridas por el agente, ordenadas por prioridad."""
    if not _schema_has_acciones():
        return []
    client = get_client()
    res = (
        client.table("feedback_acciones")
        .select("*")
        .eq("estado", "pendiente")
        .order("prioridad")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


@st.cache_data(ttl=30)
def get_acciones_resumen() -> dict[str, int]:
    """Conteo de acciones pendientes por tipo."""
    if not _schema_has_acciones():
        return {}
    client = get_client()
    res = (
        client.table("feedback_acciones")
        .select("tipo")
        .eq("estado", "pendiente")
        .execute()
    )
    summary: dict[str, int] = {}
    for row in res.data or []:
        t = row.get("tipo", "otro")
        summary[t] = summary.get(t, 0) + 1
    return summary


@st.cache_data(ttl=60)
def get_alertas() -> list[dict]:
    """Alertas in-app derivadas de KPIs y patrones recientes."""
    alerts: list[dict] = []
    kpis = get_kpis()
    threshold = int(os.getenv("ALERT_URGENCIA_ALTA_THRESHOLD", "5"))
    spike_pct = float(os.getenv("ALERT_NEGATIVO_SPIKE_PCT", "50"))

    if kpis["alertas_altas"] >= threshold:
        alerts.append(
            {
                "nivel": "error",
                "titulo": f"{kpis['alertas_altas']} mensajes con urgencia alta",
                "detalle": "Revisá la bandeja de acciones y alertas de urgencia.",
            }
        )

    if kpis["pct_negativos"] >= spike_pct:
        alerts.append(
            {
                "nivel": "warning",
                "titulo": f"Sentimiento negativo en {kpis['pct_negativos']}% del total",
                "detalle": f"Umbral configurado: {spike_pct}%.",
            }
        )

    if kpis.get("pendientes_revision", 0) > 0:
        alerts.append(
            {
                "nivel": "info",
                "titulo": f"{kpis['pendientes_revision']} clasificaciones requieren revisión",
                "detalle": "Confianza por debajo del umbral o marcadas por el agente.",
            }
        )

    if _schema_has_acciones() and kpis.get("acciones_abiertas", 0) > 0:
        alerts.append(
            {
                "nivel": "info",
                "titulo": f"{kpis['acciones_abiertas']} acciones sugeridas pendientes",
                "detalle": "El agente generó tareas concretas en el último ciclo.",
            }
        )

    if _schema_has_tick_id():
        tick_id = get_latest_tick_id()
        if tick_id:
            client = get_client()
            pat_res = (
                client.table("feedback_patrones")
                .select("descripcion, impacto")
                .eq("tick_id", tick_id)
                .in_("impacto", ["Alto", "Alta"])
                .limit(3)
                .execute()
            )
            for pat in pat_res.data or []:
                alerts.append(
                    {
                        "nivel": "warning",
                        "titulo": f"Patrón nuevo de alto impacto",
                        "detalle": pat.get("descripcion", "")[:120],
                    }
                )

    return alerts


# ─── REVISIÓN HUMANA (Fase 3) ──────────────────────────────────────────────────


@st.cache_data(ttl=30)
def get_clasificados_revision(limit: int = 50) -> list[dict]:
    """Mensajes que requieren confirmación o corrección humana."""
    client = get_client()
    threshold = get_confidence_review_threshold()
    query = (
        client.table("feedback_clasificado")
        .select(
            "external_id, sentimiento, urgencia, categorias, confianza, resumen, idioma, "
            "requiere_revision, revision_estado, "
            "feedback_raw(fuente, texto, timestamp)"
        )
        .order("created_at", desc=True)
        .limit(limit)
    )
    if _schema_has_revision_columns():
        query = query.eq("requiere_revision", True).in_(
            "revision_estado", ["pendiente", "auto"]
        )
    else:
        query = query.lt("confianza", threshold)
    res = query.execute()
    return [_flatten_clasificado_row(item) for item in (res.data or [])]


@st.cache_data(ttl=120)
def get_ultimo_eval() -> dict | None:
    """Último resultado de eval_classification guardado en feedback_metricas."""
    client = get_client()
    res = (
        client.table("feedback_metricas")
        .select("datos_metricas, created_at")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    for row in res.data or []:
        datos = row.get("datos_metricas") or {}
        if isinstance(datos, str):
            datos = json.loads(datos)
        if datos.get("tipo") == "eval_run":
            return {"created_at": row.get("created_at"), "datos": datos}
    return None


def get_ultimo_consistency_run() -> dict | None:
    """Último resultado de consistency_check guardado en feedback_metricas."""
    client = get_client()
    res = (
        client.table("feedback_metricas")
        .select("datos_metricas, created_at")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    for row in res.data or []:
        datos = row.get("datos_metricas") or {}
        if isinstance(datos, str):
            datos = json.loads(datos)
        if datos.get("tipo") == "consistency_run":
            return {"created_at": row.get("created_at"), "datos": datos}
    return None
