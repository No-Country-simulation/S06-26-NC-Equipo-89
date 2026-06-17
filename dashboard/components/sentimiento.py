"""
Componente: Distribución de Sentimiento y Top Categorías.
Gráfico de dona (sentimiento) y barras horizontales (categorías).
"""
import streamlit as st
import altair as alt
import pandas as pd
from dashboard.supabase_queries import get_sentimiento_distribucion, get_top_categorias

# Paleta de colores fija por sentimiento
COLOR_MAP = {
    "Positivo": "#22c55e",   # verde
    "Negativo": "#ef4444",   # rojo
    "Neutral":  "#94a3b8",   # gris azulado
}


def render():
    st.subheader("💬 Sentimiento y Categorías")

    col_dona, col_barras = st.columns([1, 1], gap="large")

    # ── Gráfico de Dona ────────────────────────────────────────────────────────
    with col_dona:
        st.markdown("**Distribución de Sentimiento**")
        try:
            datos_sent = get_sentimiento_distribucion()
            df_sent = pd.DataFrame(datos_sent)

            if df_sent.empty or df_sent["cantidad"].sum() == 0:
                st.info("Sin datos de clasificación aún.")
            else:
                df_sent["color"] = df_sent["sentimiento"].map(COLOR_MAP)

                chart_dona = (
                    alt.Chart(df_sent)
                    .mark_arc(innerRadius=60, outerRadius=110)
                    .encode(
                        theta=alt.Theta("cantidad:Q"),
                        color=alt.Color(
                            "sentimiento:N",
                            scale=alt.Scale(
                                domain=list(COLOR_MAP.keys()),
                                range=list(COLOR_MAP.values())
                            ),
                            legend=alt.Legend(title="Sentimiento")
                        ),
                        tooltip=["sentimiento:N", "cantidad:Q"]
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_dona, use_container_width=True)
        except Exception as e:
            st.error(f"Error cargando sentimientos: {e}")

    # ── Barras Horizontales de Categorías ─────────────────────────────────────
    with col_barras:
        st.markdown("**Top 5 Categorías más Frecuentes**")
        try:
            datos_cats = get_top_categorias(top_n=5)
            df_cats = pd.DataFrame(datos_cats)

            if df_cats.empty:
                st.info("Sin datos de categorías aún.")
            else:
                chart_barras = (
                    alt.Chart(df_cats)
                    .mark_bar(color="#6366f1", cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("cantidad:Q", title="Cantidad de menciones"),
                        y=alt.Y(
                            "categoria:N",
                            sort="-x",
                            title=None,
                            axis=alt.Axis(labelLimit=180)
                        ),
                        tooltip=["categoria:N", "cantidad:Q"]
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_barras, use_container_width=True)
        except Exception as e:
            st.error(f"Error cargando categorías: {e}")
