"""Design tokens — Feedback Classifier Dashboard v3."""

from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
STYLES_DIR = Path(__file__).parent / "styles"

# ── Paleta (light) ────────────────────────────────────────────────────────────
PRIMARY = "#2563eb"
PRIMARY_SOFT = "#eff6ff"
SURFACE = "#ffffff"
SURFACE_MUTED = "#f8fafc"
BORDER = "#e2e8f0"
TEXT = "#0f172a"
TEXT_MUTED = "#64748b"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
WARNING = "#d97706"
NEUTRAL = "#94a3b8"
CHART_ACCENT = "#6366f1"

# ── Paleta (dark) ─────────────────────────────────────────────────────────────
DARK_SURFACE = "#0f172a"
DARK_SURFACE_MUTED = "#1e293b"
DARK_BORDER = "#334155"
DARK_TEXT = "#f1f5f9"
DARK_TEXT_MUTED = "#94a3b8"
DARK_PRIMARY_SOFT = "#1e3a5f"

SENTIMENT_COLORS = {
    "Positivo": SUCCESS,
    "Negativo": DANGER,
    "Neutral": NEUTRAL,
}

IMPACT_BADGES = {
    "Alta": ("Alta", "#fee2e2", "#991b1b"),
    "Media": ("Media", "#fef9c3", "#854d0e"),
    "Baja": ("Baja", "#dcfce7", "#166534"),
    "Alto": ("Alto", "#fee2e2", "#991b1b"),
    "Medio": ("Medio", "#fef9c3", "#854d0e"),
    "Bajo": ("Bajo", "#dcfce7", "#166534"),
}

IMPACT_ORDER = {"Alto": 0, "Alta": 0, "Medio": 1, "Media": 1, "Bajo": 2, "Baja": 2}

FREQ_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}

SOURCE_BADGES: dict[str, tuple[str, str, str]] = {
    "whatsapp": ("WhatsApp", "#dcfce7", "#166534"),
    "tally": ("Tally", "#f3e8ff", "#6b21a8"),
    "google_forms": ("Google Forms", "#dbeafe", "#1e40af"),
    "google_forms_sheet": ("Google Forms", "#dbeafe", "#1e40af"),
    "csv": ("CSV", "#f1f5f9", "#475569"),
    "json": ("JSON", "#f1f5f9", "#475569"),
    "excel": ("Excel", "#fef9c3", "#854d0e"),
}

# ── Navegación agrupada ───────────────────────────────────────────────────────
NAV_GROUPS: dict[str, list[dict[str, str]]] = {
    "Análisis": [
        {"id": "general", "label": "Vista General", "icon": "📊", "url_path": "general"},
        {
            "id": "sentimiento",
            "label": "Sentimiento y Categorías",
            "icon": "💬",
            "url_path": "sentimiento",
        },
        {"id": "urgencia", "label": "Alertas de Urgencia", "icon": "🚨", "url_path": "urgencia"},
        {
            "id": "mensajes",
            "label": "Mensajes Clasificados",
            "icon": "📋",
            "url_path": "mensajes",
        },
        {"id": "patrones", "label": "Patrones Detectados", "icon": "🔍", "url_path": "patrones"},
    ],
    "Datos": [
        {"id": "exportar", "label": "Exportar Datos", "icon": "⬇️", "url_path": "exportar"},
        {"id": "carga", "label": "Carga de datos", "icon": "⬆️", "url_path": "carga"},
    ],
}

# Compatibilidad con código que aún use NAV_ITEMS plano
NAV_ITEMS: list[dict[str, str]] = [
    item for group in NAV_GROUPS.values() for item in group
]

PAGE_TITLES: dict[str, tuple[str, str]] = {
    "general": ("Vista General", "Monitoreo de feedback en tiempo casi real"),
    "sentimiento": ("Sentimiento y Categorías", "Distribución emocional y temas recurrentes"),
    "urgencia": ("Alertas de Urgencia", "Mensajes por nivel de urgencia y distribución"),
    "mensajes": (
        "Mensajes Clasificados",
        "Detalle de cada feedback: resumen, confianza, idioma y categorías",
    ),
    "patrones": ("Patrones Detectados", "Insights extraídos por el agente LangGraph"),
    "exportar": ("Exportar Datos", "Descarga de feedback ya clasificado"),
    "carga": ("Carga de datos", "Sube CSV, JSON o Excel para encolar procesamiento"),
}

# ── Altair theme ──────────────────────────────────────────────────────────────
ALTAIR_THEME = {
    "background": SURFACE,
    "view": {"stroke": BORDER},
    "title": {"font": "DM Sans", "fontSize": 14, "color": TEXT},
    "axis": {
        "labelFont": "DM Sans",
        "titleFont": "DM Sans",
        "labelColor": TEXT_MUTED,
        "titleColor": TEXT,
        "gridColor": BORDER,
    },
    "legend": {"labelFont": "DM Sans", "titleFont": "DM Sans", "labelColor": TEXT_MUTED},
    "range": {"category": list(SENTIMENT_COLORS.values()) + [CHART_ACCENT]},
}

COPILOT_SPINNER_MESSAGES = [
    "Buscando feedback similar...",
    "Consultando embeddings indexados...",
    "Generando respuesta...",
]
