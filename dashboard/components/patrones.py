"""
Componente: Patrones detectados por el Agente LangGraph.
Muestra cards con descripción, frecuencia e impacto, filtrables.
"""
import streamlit as st
from dashboard.supabase_queries import get_patrones

# Colores de badge por nivel
BADGE_COLORS = {
    "Alta":  ("🔴", "#fee2e2", "#991b1b"),
    "Media": ("🟡", "#fef9c3", "#854d0e"),
    "Baja":  ("🟢", "#dcfce7", "#166534"),
    "Alto":  ("🔴", "#fee2e2", "#991b1b"),
    "Medio": ("🟡", "#fef9c3", "#854d0e"),
    "Bajo":  ("🟢", "#dcfce7", "#166534"),
}


def _badge(label: str, value: str) -> str:
    emoji, bg, text_color = BADGE_COLORS.get(value, ("⚪", "#f1f5f9", "#475569"))
    return (
        f'<span style="background:{bg}; color:{text_color}; padding:2px 10px; '
        f'border-radius:12px; font-size:0.78rem; font-weight:600;">'
        f'{emoji} {label}: {value}</span>'
    )


def render():
    st.subheader("🔍 Patrones Detectados por el Agente")
    st.caption("Insights de negocio extraídos automáticamente por el pipeline de IA.")

    # Filtro de impacto
    filtro = st.selectbox(
        "Filtrar por nivel de impacto:",
        options=["Todos", "Alto", "Medio", "Bajo"],
        index=0,
        key="filtro_impacto"
    )

    try:
        patrones = get_patrones(impacto_filtro=filtro)

        if not patrones:
            st.info("Sin patrones detectados aún. El agente necesita procesar al menos un batch.")
            return

        for patron in patrones:
            descripcion  = patron.get("descripcion", "Sin descripción")
            frecuencia   = patron.get("frecuencia", "Desconocida")
            impacto      = patron.get("impacto", "Desconocido")
            created_at   = patron.get("created_at", "")

            badge_frec   = _badge("Frecuencia", frecuencia)
            badge_imp    = _badge("Impacto", impacto)

            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        border:1px solid #e2e8f0;
                        border-radius:12px;
                        padding:16px 20px;
                        margin-bottom:12px;
                        background:#ffffff;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                    ">
                        <p style="font-size:0.95rem; color:#1e293b; margin:0 0 10px 0;">
                            📌 {descripcion}
                        </p>
                        <div style="display:flex; gap:8px; flex-wrap:wrap;">
                            {badge_frec}
                            {badge_imp}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.caption(f"{len(patrones)} patrón(es) encontrado(s).")

    except Exception as e:
        st.error(f"Error cargando patrones: {e}")
