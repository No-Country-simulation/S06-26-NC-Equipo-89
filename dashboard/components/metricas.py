"""
Componente: KPIs de alto nivel.
Muestra tarjetas de métricas en la parte superior del dashboard.
"""
import streamlit as st

from dashboard.components.ui import metric_card, section_header, skeleton_metrics
from dashboard.supabase_queries import (
    format_relative_iso,
    get_kpis,
    get_ultimo_consistency_run,
    get_ultimo_eval,
    get_ultimo_lote_metricas,
    schema_migration_hint,
)


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
        ultimo_eval = get_ultimo_eval()
        ultimo_consistency = get_ultimo_consistency_run()
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
    conf_pct = kpis.get("pct_alta_confianza", 0)
    threshold = kpis.get("confidence_threshold", 0.7)

    with col1:
        metric_card(
            "Mensajes procesados",
            f"{kpis['total_procesados']:,}",
            delta=_batch_delta(ultimo, "total_procesados"),
        )

    with col2:
        metric_card(
            "Alta confianza",
            f"{conf_pct}%",
            delta=f"Umbral ≥ {threshold:.0%}",
            delta_color="normal" if conf_pct >= 70 else "inverse",
            help_text="Clasificaciones con confianza por encima del umbral configurado.",
        )

    with col3:
        metric_card(
            "Sentimiento negativo",
            f"{neg_pct}%",
            delta_color="inverse" if neg_pct > 30 else "normal",
            help_text="Porcentaje de mensajes clasificados como negativos.",
        )
        if neg_pct > 30:
            st.caption("Por encima del umbral recomendado (30%)")

    with col4:
        acciones = kpis.get("acciones_abiertas", 0)
        revision = kpis.get("pendientes_revision", 0)
        metric_card(
            "Acciones / revisión",
            f"{acciones} / {revision}",
            delta_color="inverse" if acciones + revision > 0 else "off",
            help_text="Acciones sugeridas pendientes / mensajes que requieren revisión humana.",
        )

    if ultimo and ultimo.get("datos"):
        datos = ultimo["datos"]
        st.markdown("---")
        section_header("Último ciclo del agente")
        if ultimo.get("created_at"):
            st.caption(f"Registrado {format_relative_iso(ultimo['created_at'])}")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Tamaño del lote", datos.get("tamano_lote", datos.get("total_procesados", 0)))
        with c2:
            st.metric("Clasificados OK", datos.get("total_procesados", 0))
        with c3:
            st.metric("Fallidos en ciclo", datos.get("errores_en_lote", 0))
        with c4:
            st.metric("Acciones generadas", datos.get("acciones_generadas", 0))
        with c5:
            sent = datos.get("sentimientos", {})
            st.metric("Negativos (lote)", sent.get("Negativo", 0))
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

    if ultimo_eval and ultimo_eval.get("datos"):
        st.markdown("---")
        section_header("Calidad del clasificador")
        ev = ultimo_eval["datos"]
        e1, e2, e3 = st.columns(3)
        with e1:
            st.metric("Precisión exacta (eval)", f"{ev.get('exact_match_pct', 0)}%")
        with e2:
            st.metric("Casos evaluados", ev.get("total", 0))
        with e3:
            por_campo = ev.get("por_campo") or {}
            st.caption(
                "Por campo: "
                + ", ".join(f"{k} {v}%" for k, v in por_campo.items())
                if por_campo
                else "Sin detalle"
            )
        if ultimo_eval.get("created_at"):
            st.caption(f"Última eval: {format_relative_iso(ultimo_eval['created_at'])}")

    if ultimo_consistency and ultimo_consistency.get("datos"):
        st.markdown("---")
        section_header(
            "Estabilidad del clasificador",
            "Mide si el modelo clasifica igual cuando se le envía el mismo mensaje varias veces.",
        )
        cs = ultimo_consistency["datos"]
        runs = cs.get("runs", "?")
        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            estab = cs.get("estabilidad_promedio", 0)
            st.metric(
                "Estabilidad promedio",
                f"{estab}%",
                delta_color="normal" if estab >= 80 else "inverse",
                help=f"% de veces que el modelo da el mismo resultado en {runs} runs. ≥80% = bueno.",
            )
        with cs2:
            st.metric(
                "Exactitud (vs golden)",
                f"{cs.get('exact_match_pct', 0)}%",
                help="Porcentaje de mensajes clasificados correctamente (vs respuesta esperada).",
            )
        with cs3:
            inestables = cs.get("inestables") or []
            st.metric(
                "Mensajes inestables",
                len(inestables),
                delta_color="inverse" if inestables else "off",
                help="Mensajes donde el modelo cambió de opinión entre runs.",
            )

        por_campo = cs.get("por_campo") or {}
        if por_campo:
            st.caption(
                "Estabilidad por campo: "
                + " · ".join(
                    f"{campo} {v.get('estabilidad', 0)}% estab / {v.get('exactitud', 0)}% exactitud"
                    for campo, v in por_campo.items()
                )
            )
        if inestables:
            st.caption(f"Inestables: {', '.join(inestables)}")
        if ultimo_consistency.get("created_at"):
            st.caption(f"Última corrida: {format_relative_iso(ultimo_consistency['created_at'])} · {runs} runs/mensaje")
