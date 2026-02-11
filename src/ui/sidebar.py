"""
Streamlit sidebar controls for user input.
Renders index selector, filter sliders, and action button.
"""

from typing import Dict, Any
import streamlit as st
from src.utils.config import MIN_ROIC, MAX_DEBT_EQUITY
from src.ui.styles import COLORS, filter_chip


def render_sidebar() -> Dict[str, Any]:
    """
    Render interactive sidebar controls and capture user selections.

    Returns:
        Dictionary with user configuration:
        {
            'index': str,              # "NIFTY100" or "SP500"
            'min_roic': float,         # Minimum ROIC threshold (as decimal)
            'max_de': float,           # Maximum D/E ratio
            'near_low_pct': float,     # Price near 52w low threshold (%)
            'run_clicked': bool        # True if "Run Screening" button clicked
        }
    """
    # Sidebar title
    st.sidebar.markdown(
        f"""<div style="
            font-size: 1.3rem;
            font-weight: 700;
            color: {COLORS['text_primary']};
            padding: 4px 0 8px 0;
            letter-spacing: -0.02em;
        ">Stock Screener</div>""",
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")

    # ==================== INDEX SELECTION ====================
    st.sidebar.markdown(
        f'<div style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Market Index</div>',
        unsafe_allow_html=True
    )

    index = st.sidebar.radio(
        label="Market",
        options=["Nifty 100", "S&P 500", "FTSE 100"],
        index=0,
        help="Choose the stock universe to screen",
        label_visibility="collapsed"
    )

    # Normalize to internal format
    index_map = {
        "Nifty 100": "NIFTY100",
        "S&P 500": "SP500",
        "FTSE 100": "FTSE100",
    }
    index_key = index_map[index]

    st.sidebar.markdown("---")

    # ==================== TICKER LIMIT ====================
    st.sidebar.markdown(
        f'<div style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Ticker Limit</div>',
        unsafe_allow_html=True
    )

    ticker_limit = st.sidebar.slider(
        label="Number of Stocks to Screen",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Screen only the top N stocks by market capitalization. "
             "Lower values = faster screening, Higher values = broader coverage.",
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # ==================== QUALITY FILTERS ====================
    st.sidebar.markdown(
        f'<div style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Quality Filters</div>',
        unsafe_allow_html=True
    )

    # Min ROIC Slider
    min_roic_pct = st.sidebar.slider(
        label="Minimum ROIC (%)",
        min_value=5,
        max_value=30,
        value=15,
        step=1,
        help="Filter stocks with Return on Invested Capital above this threshold. "
             "15% is Warren Buffett's baseline for quality businesses."
    )

    # Convert percentage to decimal
    min_roic = min_roic_pct / 100.0

    # Max Debt/Equity Slider
    max_de = st.sidebar.slider(
        label="Max Debt/Equity Ratio",
        min_value=0.1,
        max_value=2.0,
        value=0.8,
        step=0.1,
        help="Maximum acceptable debt-to-equity ratio. "
             "Lower values indicate conservative financial leverage."
    )

    st.sidebar.markdown("---")

    # ==================== VALUATION FILTER ====================
    st.sidebar.markdown(
        f'<div style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Valuation Filter</div>',
        unsafe_allow_html=True
    )

    near_low_pct = st.sidebar.slider(
        label="Price Near 52-Week Low (%)",
        min_value=5,
        max_value=20,
        value=10,
        step=1,
        help="Only show stocks trading within this % of their 52-week low. "
             "10% captures 'Buy-the-Dip' opportunities."
    )

    st.sidebar.markdown("---")

    # ==================== ACTION BUTTON ====================
    run_clicked = st.sidebar.button(
        label="Run Screening",
        type="primary",
        use_container_width=True,
        help="Fetch data and apply filters to selected index"
    )

    # Display current thresholds as styled chips
    if not run_clicked:
        chips_html = (
            f'<div style="margin-top:12px;text-align:center;">'
            f'{filter_chip(f"ROIC >= {min_roic_pct}%")}'
            f'{filter_chip(f"D/E <= {max_de}")}'
            f'{filter_chip(f"Near 52w Low <= {near_low_pct}%")}'
            f'</div>'
        )
        st.sidebar.markdown(chips_html, unsafe_allow_html=True)

    # ==================== QUANT MENTOR (EDUCATION LAYER) ====================
    st.sidebar.markdown("---")
    render_quant_mentor()

    # ==================== RETURN CONFIG ====================
    return {
        'index': index_key,
        'ticker_limit': ticker_limit,
        'min_roic': min_roic,
        'max_de': max_de,
        'near_low_pct': near_low_pct,
        'run_clicked': run_clicked
    }


def render_quant_mentor() -> None:
    """
    Render the 'How to Read This' educational expander in the sidebar.
    Contains a financial glossary with plain-English explanations.
    """
    with st.sidebar.expander("How to Read This", expanded=False):
        st.markdown(
            "**ROIC** (Return on Invested Capital)\n"
            "How much profit the company makes for every $1 of capital invested. "
            "Above 15% = Excellent. Below 10% = Concerning."
        )
        st.markdown(
            "**Debt/Equity Ratio**\n"
            "How much the company owes vs what it owns. "
            "Think of it as household leverage: mortgage vs home equity. "
            "Below 0.5 = Conservative. Above 1.5 = Aggressive."
        )
        st.markdown(
            "**Free Cash Flow (FCF)**\n"
            "Cash left over after running the business and reinvesting in growth. "
            "3 consecutive positive years = healthy cash engine."
        )
        st.markdown(
            "**Value Score**\n"
            "Composite metric: 60% quality (ROIC) + 40% price discount from peak. "
            "Higher = a great business on sale."
        )
        st.markdown(
            "**Bollinger Bands**\n"
            "Statistical 'safety rails' around a stock's price "
            "(20-day average +/- 2 standard deviations). "
            "Price near the bottom band may signal oversold conditions. "
            "Not a buy signal alone - combine with fundamental quality."
        )
        st.markdown(
            "**Mean Reversion (P/E)**\n"
            "The idea that a stock's P/E ratio tends to return to its long-term average. "
            "Current P/E below 3-year average = potentially undervalued. "
            "Above = potentially overvalued."
        )
        st.markdown(
            "**52-Week High/Low**\n"
            "The highest and lowest prices over the past year. "
            "Stocks near 52-week lows with strong fundamentals = potential value opportunities."
        )


def render_sidebar_footer() -> None:
    """
    Render informational footer in sidebar.

    Displays project version, data source, and help text.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""<div style="
            color: {COLORS['text_muted']};
            font-size: 0.75rem;
            line-height: 1.6;
            padding: 4px 0;
        ">
            <div style="font-weight:600;color:{COLORS['text_secondary']};margin-bottom:4px;">About</div>
            Professional stock screener for value investors.
            Combines fundamental health metrics (ROIC, FCF, D/E)
            with price-action discounting.<br><br>
            <strong>Data:</strong> yfinance&emsp;
            <strong>Version:</strong> 1.1.0
        </div>""",
        unsafe_allow_html=True
    )
