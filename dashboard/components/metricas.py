"""
Componente: KPIs de alto nivel.
Muestra 4 tarjetas de métricas en la parte superior del dashboard.
"""
import streamlit as st

from dashboard.components.ui import metric_card, section_header, skeleton_metrics
from dashboard.supabase_queries import get_kpis, get_ultimo_lote_metricas, schema_migration_hint


def _batch_delta(ultimo: dict | None, key: str, subkey: str | None = None) -> str | None:
    """Calcula delta descriptivo desde el último lote."""
    if not ultimo or not ultimo.get("datos"):
        return None
    datos = ultimo["datos"]
    if subkey:
        val = datos.get(key, {}).get(subkey)
    else:
        val = datos.get(key)
    if val is None:
        return None
    return f"+{val} en último lote"


def render():
    section_header("Indicadores clave", "Resumen del feedback procesado por el agente.")

    placeholder = st.empty()
    with placeholder.container():
        skeleton_metrics(4)

    try:
        kpis = get_kpis()
        ultimo = get_ultimo_lote_metricas()
    except EnvironmentError as e:
        placeholder.empty()
        st.error(f"Error de configuración: {e}")
        return
    except Exception as e:
        placeholder.empty()
        st.error(f"No se pudieron cargar las métricas: {e}")
        return

    placeholder.empty()
    hint = schema_migration_hint()
    if hint:
        st.warning(hint)

    col1, col2, col3, col4 = st.columns(4)

    neg_pct = kpis["pct_negativos"]
    neg_delta = None
    if ultimo and ultimo.get("datos"):
        sent = ultimo["datos"].get("sentimientos", {})
        total_lote = sum(sent.values()) or 1
        lote_neg = round(sent.get("Negativo", 0) / total_lote * 100, 1)
        diff = round(neg_pct - lote_neg, 1)
        if diff != 0:
            neg_delta = f"{diff:+.1f}% vs lote"

    with col1:
        metric_card(
            "Mensajes procesados",
            f"{kpis['total_procesados']:,}",
            delta=_batch_delta(ultimo, "total_procesados"),
        )

    with col2:
        metric_card(
            "Sentimiento negativo",
            f"{neg_pct}%",
            delta=neg_delta,
            delta_color="inverse" if neg_pct > 30 else "normal",
            help_text="Porcentaje de mensajes clasificados como negativos.",
        )
        if neg_pct > 30:
            st.caption("⚠️ Por encima del umbral recomendado (30%)")

    with col3:
        metric_card(
            "Alertas urgencia alta",
            f"{kpis['alertas_altas']:,}",
            delta=_batch_delta(ultimo, "urgencias", "Alta"),
            delta_color="inverse" if kpis["alertas_altas"] > 0 else "off",
        )
        if kpis["alertas_altas"] > 0:
            st.caption("🔴 Requieren atención inmediata")

    with col4:
        metric_card(
            "Patrones detectados",
            f"{kpis['total_patrones']:,}",
        )

    if ultimo and ultimo.get("datos"):
        datos = ultimo["datos"]
        st.markdown("---")
        section_header("Último ciclo del agente")
        if ultimo.get("created_at"):
            st.caption(f"Registrado {format_relative_iso(ultimo['created_at'])}")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Tamaño del lote", datos.get("tamano_lote", datos.get("total_procesados", 0)))
        with c2:
            st.metric("Clasificados OK", datos.get("total_procesados", 0))
        with c3:
            st.metric("Fallidos en ciclo", datos.get("errores_en_lote", 0))
        with c4:
            sent = datos.get("sentimientos", {})
            st.metric(
                "Negativos (lote)",
                sent.get("Negativo", 0),
            )
        if datos.get("urgencias"):
            urg = datos.get("urgencias", {})
            st.caption(
                f"Urgencia alta: {urg.get('Alta', 0)} · "
                f"Media: {urg.get('Media', 0)} · "
                f"Baja: {urg.get('Baja', 0)}"
            )
        if datos.get("categorias_top"):
            st.caption(
                "Top categorías: "
                + ", ".join(f"{k} ({v})" for k, v in datos["categorias_top"].items())
            )
