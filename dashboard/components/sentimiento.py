"""
Componente: Distribución de Sentimiento y Top Categorías.
Gráfico de dona (sentimiento) y barras horizontales (categorías).
"""
import altair as alt
import pandas as pd
import streamlit as st

from dashboard.components.ui import empty_state, section_header
from dashboard.supabase_queries import get_sentimiento_distribucion, get_top_categorias
from dashboard.theme import ALTAIR_THEME, CHART_ACCENT, SENTIMENT_COLORS

alt.theme.enable("default")
alt.themes.register("fc_theme", lambda: ALTAIR_THEME)
alt.theme.enable("fc_theme")


def _add_pct_column(df: pd.DataFrame, value_col: str = "cantidad") -> pd.DataFrame:
    total = df[value_col].sum() or 1
    df = df.copy()
    df["porcentaje"] = (df[value_col] / total * 100).round(1)
    return df


def render():
    section_header(
        "Sentimiento y categorías",
        "Distribución emocional y temas más mencionados por los clientes.",
    )

    col_dona, col_barras = st.columns([1, 1], gap="large")

    with col_dona:
        st.markdown("**Distribución de sentimiento**")
        try:
            datos_sent = get_sentimiento_distribucion()
            df_sent = pd.DataFrame(datos_sent)

            if df_sent.empty or df_sent["cantidad"].sum() == 0:
                empty_state(
                    "Aún no hay feedback clasificado. Cargá datos o esperá al worker."
                )
            else:
                df_sent = _add_pct_column(df_sent)
                chart_dona = (
                    alt.Chart(df_sent)
                    .mark_arc(innerRadius=60, outerRadius=110)
                    .encode(
                        theta=alt.Theta("cantidad:Q", title="Cantidad"),
                        color=alt.Color(
                            "sentimiento:N",
                            scale=alt.Scale(
                                domain=list(SENTIMENT_COLORS.keys()),
                                range=list(SENTIMENT_COLORS.values()),
                            ),
                            legend=alt.Legend(title="Sentimiento"),
                        ),
                        tooltip=[
                            alt.Tooltip("sentimiento:N", title="Sentimiento"),
                            alt.Tooltip("cantidad:Q", title="Cantidad"),
                            alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".1f"),
                        ],
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_dona, width="stretch")
        except Exception as e:
            st.error(f"Error cargando sentimientos: {e}")

    with col_barras:
        st.markdown("**Top 5 categorías**")
        try:
            datos_cats = get_top_categorias(top_n=5)
            df_cats = pd.DataFrame(datos_cats)

            if df_cats.empty:
                empty_state("Sin categorías detectadas todavía.")
            else:
                df_cats = _add_pct_column(df_cats)
                chart_barras = (
                    alt.Chart(df_cats)
                    .mark_bar(color=CHART_ACCENT, cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("cantidad:Q", title="Menciones"),
                        y=alt.Y(
                            "categoria:N",
                            sort="-x",
                            title="Categoría",
                            axis=alt.Axis(labelLimit=180),
                        ),
                        tooltip=[
                            alt.Tooltip("categoria:N", title="Categoría"),
                            alt.Tooltip("cantidad:Q", title="Menciones"),
                            alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".1f"),
                        ],
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_barras, width="stretch")
        except Exception as e:
            st.error(f"Error cargando categorías: {e}")
