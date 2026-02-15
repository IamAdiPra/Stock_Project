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

    # Min Earnings Quality Score Slider (optional, default 0 = disabled)
    min_earnings_quality = st.sidebar.slider(
        label="Min Earnings Quality Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        help="Filter stocks by earnings quality (0-100). "
             "0 = disabled. Higher scores indicate cash-backed, high-quality earnings. "
             "Combines accrual ratio, FCF/NI ratio, and revenue/receivables divergence."
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

    # ==================== MOMENTUM ====================
    st.sidebar.markdown(
        f'<div style="font-size:0.82rem;font-weight:600;color:{COLORS["text_secondary"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Momentum</div>',
        unsafe_allow_html=True
    )

    use_hybrid_ranking = st.sidebar.checkbox(
        label="Hybrid Ranking (Value + Momentum)",
        value=False,
        help="Blend 70% Value Score + 30% Momentum Score for ranking. "
             "Momentum is computed from RSI, MACD, and SMA crossover signals "
             "for stocks that pass all value filters."
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
        eq_chip = f'{filter_chip(f"EQ >= {min_earnings_quality}")}' if min_earnings_quality > 0 else ""
        hybrid_chip = f'{filter_chip("Hybrid Ranking")}' if use_hybrid_ranking else ""
        chips_html = (
            f'<div style="margin-top:12px;text-align:center;">'
            f'{filter_chip(f"ROIC >= {min_roic_pct}%")}'
            f'{filter_chip(f"D/E <= {max_de}")}'
            f'{filter_chip(f"Near 52w Low <= {near_low_pct}%")}'
            f'{eq_chip}'
            f'{hybrid_chip}'
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
        'min_earnings_quality': min_earnings_quality,
        'use_hybrid_ranking': use_hybrid_ranking,
        'run_clicked': run_clicked
    }


def render_quant_mentor() -> None:
    """
    Render the Financial Dictionary expander in the sidebar.
    Searchable glossary with 80+ financial terms explained like to a 10-year-old.
    """
    from src.ui.glossary import (
        search_glossary,
        get_category_terms,
        render_glossary_card,
        get_all_categories,
        FINANCIAL_GLOSSARY
    )

    with st.sidebar.expander("📚 Financial Dictionary", expanded=False):
        # Search box
        search_query = st.text_input(
            "Search terms...",
            placeholder="e.g., ROIC, Beta, Sharpe",
            key="glossary_search",
            label_visibility="collapsed"
        )

        # Category filter
        all_categories = ["All"] + get_all_categories()
        category = st.selectbox(
            "Filter by category",
            all_categories,
            key="glossary_category",
            label_visibility="collapsed"
        )

        # Spacer
        st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)

        # Render filtered glossary
        if search_query:
            results = search_glossary(search_query)
            if results:
                st.caption(f"✓ {len(results)} term{'s' if len(results) > 1 else ''} found")
                for term in results:
                    st.markdown(render_glossary_card(term), unsafe_allow_html=True)
            else:
                st.caption("No matching terms found. Try 'ROIC', 'Beta', or 'Sharpe'.")
        else:
            # Get terms for selected category
            if category == "All":
                terms = sorted(FINANCIAL_GLOSSARY.keys())
            else:
                terms = get_category_terms(category)

            st.caption(f"📖 Showing {len(terms)} term{'s' if len(terms) > 1 else ''}")

            # Render cards
            for term in terms:
                st.markdown(render_glossary_card(term), unsafe_allow_html=True)


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
            <strong>Version:</strong> 1.10.0
        </div>""",
        unsafe_allow_html=True
    )
