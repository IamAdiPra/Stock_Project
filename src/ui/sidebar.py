"""
Streamlit sidebar controls for user input.
Renders index selector, filter sliders, and action button.
"""

from typing import Dict, Any
import streamlit as st
from src.utils.config import MIN_ROIC, MAX_DEBT_EQUITY


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
    st.sidebar.title("🔍 Stock Screener")
    st.sidebar.markdown("---")

    # ==================== INDEX SELECTION ====================
    st.sidebar.subheader("📊 Select Index")

    index = st.sidebar.radio(
        label="Market",
        options=["Nifty 100", "S&P 500"],
        index=0,
        help="Choose the stock universe to screen"
    )

    # Normalize to internal format
    index_key = "NIFTY100" if index == "Nifty 100" else "SP500"

    st.sidebar.markdown("---")

    # ==================== TICKER LIMIT ====================
    st.sidebar.subheader("🎯 Ticker Limit")

    ticker_limit = st.sidebar.slider(
        label="Number of Stocks to Screen",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Screen only the top N stocks by market capitalization. "
             "Lower values = faster screening, Higher values = broader coverage."
    )

    st.sidebar.markdown("---")

    # ==================== QUALITY FILTERS ====================
    st.sidebar.subheader("⚙️ Quality Filters")

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
    st.sidebar.subheader("💰 Valuation Filter")

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
    st.sidebar.subheader("🚀 Execute")

    run_clicked = st.sidebar.button(
        label="Run Screening",
        type="primary",
        use_container_width=True,
        help="Fetch data and apply filters to selected index"
    )

    # Display current thresholds summary
    if not run_clicked:
        st.sidebar.info(
            f"**Current Filters:**\n"
            f"- ROIC ≥ {min_roic_pct}%\n"
            f"- D/E ≤ {max_de}\n"
            f"- Price within {near_low_pct}% of 52w Low"
        )

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
    st.sidebar.caption("📚 **About**")
    st.sidebar.caption(
        "Professional stock screener for value investors. "
        "Combines fundamental health metrics (ROIC, FCF, D/E) "
        "with price-action discounting."
    )
    st.sidebar.caption("**Data Source:** yfinance")
    st.sidebar.caption("**Version:** 0.7.0")
