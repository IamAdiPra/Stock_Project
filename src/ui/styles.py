"""
Midnight Finance Design System.
Centralized CSS, Plotly theme, and reusable HTML component helpers.
"""

from typing import Optional


# ==================== COLOR PALETTE ====================

COLORS = {
    "bg_primary": "#0E1117",
    "surface": "#1B2332",
    "surface_elevated": "#232F3E",
    "border": "#2D3B4E",
    "text_primary": "#F0F2F5",
    "text_secondary": "#8899A6",
    "text_muted": "#5C6B7A",
    "accent_green": "#10B981",
    "accent_red": "#EF4444",
    "accent_blue": "#6366F1",
    "accent_amber": "#F59E0B",
    "accent_purple": "#8B5CF6",
    "gradient_start": "#1E3A5F",
    "gradient_end": "#1B4D3E",
}

FONT_STACK = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


# ==================== PLOTLY THEME ====================

def get_plotly_theme() -> dict:
    """
    Return a Plotly layout dict for the Midnight Finance dark theme.
    Apply via fig.update_layout(**get_plotly_theme()).
    """
    return {
        "plot_bgcolor": COLORS["surface"],
        "paper_bgcolor": COLORS["surface"],
        "font": {
            "family": FONT_STACK,
            "color": COLORS["text_secondary"],
            "size": 12,
        },
        "title": {
            "font": {
                "family": FONT_STACK,
                "color": COLORS["text_primary"],
                "size": 18,
            },
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickfont": {"color": COLORS["text_secondary"]},
            "title_font": {"color": COLORS["text_secondary"], "size": 13},
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickfont": {"color": COLORS["text_secondary"]},
            "title_font": {"color": COLORS["text_secondary"], "size": 13},
        },
        "hoverlabel": {
            "bgcolor": COLORS["surface_elevated"],
            "font_size": 12,
            "font_family": FONT_STACK,
            "font_color": COLORS["text_primary"],
            "bordercolor": COLORS["border"],
        },
        "coloraxis_colorbar": {
            "title_font": {"color": COLORS["text_secondary"], "size": 12},
            "tickfont": {"color": COLORS["text_secondary"]},
            "outlinecolor": COLORS["border"],
            "bgcolor": COLORS["surface"],
        },
        "legend": {
            "font": {"color": COLORS["text_secondary"]},
            "bgcolor": "rgba(0,0,0,0)",
        },
    }


def get_plotly_theme_with_legend_top() -> dict:
    """Plotly theme with horizontal legend above the chart."""
    theme = get_plotly_theme()
    theme["legend"] = {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
        "font": {"color": COLORS["text_secondary"]},
        "bgcolor": "rgba(0,0,0,0)",
    }
    return theme


# ==================== HTML CARD HELPERS ====================

def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    accent: str = "blue",
) -> str:
    """
    Return HTML for a styled KPI metric card.

    Args:
        label: Muted label above the value
        value: Bold primary value
        delta: Optional delta text below value
        accent: Color key - 'green', 'red', 'blue', 'amber', 'purple'
    """
    accent_color = COLORS.get(f"accent_{accent}", COLORS["accent_blue"])

    delta_html = ""
    if delta is not None:
        delta_color = COLORS["accent_green"] if "+" in delta or "%" in delta else COLORS["text_secondary"]
        if "-" in delta:
            delta_color = COLORS["accent_red"]
        delta_html = f'<div style="font-size:0.8rem;color:{delta_color};margin-top:4px;">{delta}</div>'

    return f"""
    <div style="
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-left: 4px solid {accent_color};
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    ">
        <div style="
            font-size: 0.78rem;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
            font-weight: 500;
        ">{label}</div>
        <div style="
            font-size: 1.6rem;
            font-weight: 700;
            color: {COLORS['text_primary']};
            line-height: 1.2;
        ">{value}</div>
        {delta_html}
    </div>
    """


def section_card(content_html: str, padding: str = "24px") -> str:
    """Wrap content in a styled card container."""
    return f"""
    <div style="
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: {padding};
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    ">
        {content_html}
    </div>
    """


def model_card(title: str, items_html: str, accent: str = "blue") -> str:
    """Card for model breakdown sections in forecast tab."""
    accent_color = COLORS.get(f"accent_{accent}", COLORS["accent_blue"])
    return f"""
    <div style="
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-top: 3px solid {accent_color};
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    ">
        <div style="
            font-size: 1rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-bottom: 14px;
        ">{title}</div>
        <div style="
            font-size: 0.85rem;
            color: {COLORS['text_secondary']};
            line-height: 1.8;
        ">{items_html}</div>
    </div>
    """


def top_pick_card(rank: int, ticker: str, roic: str, score: str) -> str:
    """Card for a single top pick entry."""
    rank_colors = {1: COLORS["accent_green"], 2: COLORS["accent_green"],
                   3: COLORS["accent_blue"], 4: COLORS["accent_blue"],
                   5: COLORS["accent_purple"]}
    ring_color = rank_colors.get(rank, COLORS["accent_blue"])

    return f"""
    <div style="
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    ">
        <div style="
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: {ring_color}22;
            border: 2px solid {ring_color};
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: {ring_color};
            flex-shrink: 0;
        ">{rank}</div>
        <div style="flex:1;min-width:0;">
            <div style="
                font-weight: 600;
                font-size: 0.95rem;
                color: {COLORS['text_primary']};
            ">{ticker}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.78rem;color:{COLORS['text_secondary']};">ROIC</div>
            <div style="font-size:0.85rem;font-weight:600;color:{COLORS['accent_green']};">{roic}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.78rem;color:{COLORS['text_secondary']};">Score</div>
            <div style="font-size:0.85rem;font-weight:600;color:{COLORS['accent_blue']};">{score}</div>
        </div>
    </div>
    """


def filter_chip(text: str) -> str:
    """Render a styled filter badge chip."""
    return f"""<span style="
        display: inline-block;
        background: {COLORS['accent_blue']}18;
        color: {COLORS['accent_blue']};
        border: 1px solid {COLORS['accent_blue']}40;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 3px 2px;
    ">{text}</span>"""


def section_header(text: str) -> str:
    """Styled section header with accent underline."""
    return f"""
    <div style="margin-bottom: 16px;">
        <div style="
            font-size: 1.15rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-bottom: 6px;
        ">{text}</div>
        <div style="
            width: 40px;
            height: 3px;
            background: {COLORS['accent_blue']};
            border-radius: 2px;
        "></div>
    </div>
    """


# ==================== GLOBAL CSS ====================

def get_global_css() -> str:
    """
    Return the full CSS stylesheet for the Midnight Finance theme.
    Inject via st.markdown(f'<style>{get_global_css()}</style>', unsafe_allow_html=True).
    """
    return f"""
    /* ===== Google Fonts ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ===== Global Typography ===== */
    html, body, [class*="css"] {{
        font-family: {FONT_STACK} !important;
    }}

    /* ===== Main Container ===== */
    .stApp {{
        background-color: {COLORS['bg_primary']};
    }}

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['surface']} !important;
        border-right: 1px solid {COLORS['border']} !important;
    }}

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li {{
        color: {COLORS['text_secondary']} !important;
    }}

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: {COLORS['text_primary']} !important;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: {COLORS['border']} !important;
        opacity: 0.5;
    }}

    /* ===== Sidebar Radio Buttons ===== */
    [data-testid="stSidebar"] .stRadio label {{
        color: {COLORS['text_secondary']} !important;
    }}

    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {{
        color: {COLORS['accent_blue']} !important;
        font-weight: 600;
    }}

    /* ===== Sidebar Sliders ===== */
    [data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {{
        color: {COLORS['accent_blue']} !important;
        font-weight: 600;
    }}

    /* ===== Primary Button ===== */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_purple']}) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {{
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-1px) !important;
    }}

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {COLORS['surface']} !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid {COLORS['border']} !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px !important;
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
        padding: 8px 20px !important;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['accent_blue']} !important;
        color: white !important;
        font-weight: 600 !important;
    }}

    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        display: none !important;
    }}

    /* ===== DataFrames / Tables ===== */
    [data-testid="stDataFrame"] {{
        border: 1px solid {COLORS['border']} !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}

    /* ===== Metric Cards ===== */
    [data-testid="stMetric"] {{
        background: {COLORS['surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
    }}

    [data-testid="stMetricValue"] {{
        color: {COLORS['text_primary']} !important;
        font-weight: 700 !important;
    }}

    /* ===== Expander ===== */
    [data-testid="stExpander"] {{
        background: {COLORS['surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 12px !important;
    }}

    [data-testid="stExpander"] summary {{
        color: {COLORS['text_primary']} !important;
    }}

    /* ===== Info / Warning / Success boxes ===== */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        border-left-width: 4px !important;
    }}

    /* ===== Download Button ===== */
    [data-testid="stDownloadButton"] > button {{
        background: {COLORS['surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 10px !important;
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}

    [data-testid="stDownloadButton"] > button:hover {{
        border-color: {COLORS['accent_blue']} !important;
        color: {COLORS['accent_blue']} !important;
        background: {COLORS['surface_elevated']} !important;
    }}

    /* ===== Link Buttons ===== */
    .stLinkButton > a {{
        background: {COLORS['surface']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 10px !important;
        color: {COLORS['accent_blue']} !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}

    .stLinkButton > a:hover {{
        border-color: {COLORS['accent_blue']} !important;
        background: {COLORS['surface_elevated']} !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2) !important;
    }}

    /* ===== Selectbox ===== */
    [data-testid="stSelectbox"] label {{
        color: {COLORS['text_secondary']} !important;
    }}

    /* ===== Subheader ===== */
    .stMarkdown h2, .stMarkdown h3 {{
        color: {COLORS['text_primary']} !important;
    }}

    /* ===== Horizontal Rule ===== */
    .stMarkdown hr {{
        border-color: {COLORS['border']} !important;
        opacity: 0.5;
    }}

    /* ===== Caption ===== */
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: {COLORS['text_muted']} !important;
    }}

    /* ===== Spinner ===== */
    .stSpinner > div {{
        border-top-color: {COLORS['accent_blue']} !important;
    }}

    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {COLORS['bg_primary']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {COLORS['border']};
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['text_muted']};
    }}

    /* ===== Success message after screening ===== */
    .stSuccess {{
        border-radius: 10px !important;
    }}

    /* ===== Progress Bar ===== */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {COLORS['accent_blue']}, {COLORS['accent_purple']}) !important;
        border-radius: 4px !important;
    }}
    """
