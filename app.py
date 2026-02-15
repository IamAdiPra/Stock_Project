"""
Stock Value Screener - Main Application
Professional-grade stock screening dashboard for value investors.
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd

# Data Layer
from src.data.fetcher import batch_fetch_deep_data
from src.data.macro_fetcher import fetch_macro_indicators
from src.utils.ticker_lists import get_all_tickers, get_ticker_count
from src.utils.logger import clear_data_quality_log

# Quant Layer
from src.quant.screener import screen_stocks, format_results_for_display, build_sector_universe

# UI Layer
from src.ui.sidebar import render_sidebar, render_sidebar_footer
from src.ui.visualizations import create_value_scatter_plot
from src.ui.deep_dive import render_deep_dive_section
from src.ui.forecast_tab import render_forecast_section
from src.ui.sector_tab import render_sector_section
from src.ui.portfolio_tab import render_portfolio_section
from src.ui.backtest_tab import render_backtest_section
from src.ui.components import (
    render_header,
    render_metric_cards,
    render_macro_context,
    render_results_table,
    render_data_quality_report,
    render_empty_state,
    render_footer,
    render_top_5_cards,
)
from src.ui.styles import get_global_css, section_header, COLORS

# Utils
from src.utils.config import get_currency_symbol


# ==================== PAGE CONFIGURATION ====================

st.set_page_config(
    page_title="Stock Value Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INJECT GLOBAL CSS ====================

st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)


# ==================== SESSION STATE INITIALIZATION ====================

def initialize_session_state() -> None:
    """Initialize session state variables if they don't exist."""
    if 'results_df_raw' not in st.session_state:
        st.session_state.results_df_raw = None

    if 'results_df_formatted' not in st.session_state:
        st.session_state.results_df_formatted = None

    if 'screening_config' not in st.session_state:
        st.session_state.screening_config = None

    if 'total_screened' not in st.session_state:
        st.session_state.total_screened = 0

    if 'passed_filters' not in st.session_state:
        st.session_state.passed_filters = 0

    if 'stocks_data' not in st.session_state:
        st.session_state.stocks_data = None

    if 'universe_df' not in st.session_state:
        st.session_state.universe_df = None

    if 'forecast_df' not in st.session_state:
        st.session_state.forecast_df = None

    if 'forecast_data' not in st.session_state:
        st.session_state.forecast_data = None

    if 'forecast_index' not in st.session_state:
        st.session_state.forecast_index = None

    if 'forecast_tickers' not in st.session_state:
        st.session_state.forecast_tickers = None


# ==================== HELPER FUNCTIONS ====================

def config_requires_refetch(new_config: Dict[str, Any], old_config: Optional[Dict[str, Any]]) -> bool:
    """
    Check if the new config requires re-fetching data.

    Re-fetch is needed if:
    - Index changed (Nifty 100 ↔ S&P 500)
    - Ticker limit changed

    Filter changes (ROIC, D/E, Price) do NOT require re-fetch.

    Args:
        new_config: New user configuration from sidebar
        old_config: Previous configuration from session state

    Returns:
        True if data needs to be re-fetched, False otherwise
    """
    if old_config is None:
        return True  # First run, always fetch

    # Check if index or ticker limit changed
    index_changed = new_config['index'] != old_config['index']
    limit_changed = new_config['ticker_limit'] != old_config['ticker_limit']

    return index_changed or limit_changed


# ==================== MAIN SCREENING LOGIC ====================

def run_screening(config: Dict[str, Any]) -> None:
    """
    Execute the screening pipeline with user-selected configuration.

    Args:
        config: User configuration from sidebar (index, filters, thresholds)
    """
    # Clear previous data quality log
    clear_data_quality_log()

    # Extract configuration
    index = config['index']
    ticker_limit = config['ticker_limit']
    min_roic = config['min_roic']
    max_de = config['max_de']
    near_low_pct = config['near_low_pct']
    min_earnings_quality = config.get('min_earnings_quality', 0)
    use_hybrid_ranking = config.get('use_hybrid_ranking', False)

    # Get ticker list (limited to top N by market cap)
    tickers = get_all_tickers(index, limit=ticker_limit)
    total_tickers = len(tickers)

    # Determine exchange suffix
    exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
    exchange = exchange_map.get(index)  # None for US markets

    # Step 1: Fetch data with progress bar
    with st.spinner(f"Fetching data for {total_tickers} tickers from {index}..."):
        progress_bar = st.progress(0)
        progress_text = st.empty()

        progress_text.text(f"Fetching deep financial data... (0/{total_tickers} tickers)")

        # Progress callback: called from main thread via as_completed()
        def on_ticker_fetched(completed: int, total: int) -> None:
            pct = int(completed / total * 70)  # 0-70% for fetching
            progress_bar.progress(pct)
            progress_text.text(f"Fetching deep financial data... ({completed}/{total} tickers)")

        stocks_data = batch_fetch_deep_data(
            tickers=tickers,
            exchange=exchange,
            max_workers=10,
            progress_callback=on_ticker_fetched
        )

        # Store raw stocks_data for Deep Dive analysis
        st.session_state.stocks_data = stocks_data

        progress_bar.progress(75)
        progress_text.text(f"Data fetched. Applying quality filters...")

        # Step 2: Screen stocks
        results_df = screen_stocks(
            stocks_data=stocks_data,
            min_roic=min_roic,
            max_debt_equity=max_de,
            near_low_threshold=near_low_pct,
            require_3y_fcf=True,
            min_earnings_quality=min_earnings_quality,
            use_hybrid_ranking=use_hybrid_ranking,
        )

        progress_bar.progress(75)
        progress_text.text(f"Formatting results for display...")

        # Step 3: Store raw DataFrame and create formatted version
        # Raw DataFrame: For visualizations (needs numeric columns)
        # Formatted DataFrame: For table display (prettified strings)
        currency_symbol = get_currency_symbol(index)
        if not results_df.empty:
            formatted_df = format_results_for_display(results_df, currency_symbol=currency_symbol)
        else:
            formatted_df = results_df

        progress_bar.progress(100)
        progress_text.text(f"Screening complete!")

        # Store BOTH raw and formatted results in session state
        st.session_state.results_df_raw = results_df  # For visualizations
        st.session_state.results_df_formatted = formatted_df  # For table display
        st.session_state.screening_config = config
        st.session_state.total_screened = total_tickers
        st.session_state.passed_filters = len(results_df)

        # Build sector universe (all stocks, pre-filter) for Sector Analysis tab
        st.session_state.universe_df = build_sector_universe(stocks_data)

        # Invalidate forecast cache (new screening = new data)
        st.session_state.forecast_df = None
        st.session_state.forecast_data = None
        st.session_state.forecast_tickers = None

        # Clear progress indicators
        progress_bar.empty()
        progress_text.empty()

    st.success(
        f"Screening complete! {len(formatted_df)} of {total_tickers} stocks passed all filters."
    )


# ==================== MAIN APPLICATION ====================

def main() -> None:
    """Main application entry point."""

    # Initialize session state
    initialize_session_state()

    # Render header
    render_header()

    # Render sidebar and capture user input
    config = render_sidebar()
    render_sidebar_footer()

    # Handle "Run Screening" button click
    if config['run_clicked']:
        # Check if we need to re-fetch data
        needs_refetch = config_requires_refetch(config, st.session_state.screening_config)

        if needs_refetch:
            # Index or ticker limit changed - re-fetch data
            run_screening(config)
        else:
            # Only filter thresholds changed - re-apply filters to existing data
            st.info("Filter thresholds updated. Re-applying filters to cached data...")
            # TODO: Implement filter-only update (future optimization)
            # For now, still re-run full screening
            run_screening(config)

    # Display results if available
    if st.session_state.results_df_raw is not None:
        results_df_raw = st.session_state.results_df_raw  # For visualizations
        results_df_formatted = st.session_state.results_df_formatted  # For table
        total_screened = st.session_state.total_screened
        passed_filters = st.session_state.passed_filters
        screening_config = st.session_state.screening_config

        # Display ticker range info
        index_display_names = {"NIFTY100": "Nifty 100", "SP500": "S&P 500", "FTSE100": "FTSE 100"}
        index_name = index_display_names.get(screening_config['index'], screening_config['index'])

        st.markdown(
            f"""<div style="
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-left: 4px solid {COLORS['accent_blue']};
                border-radius: 10px;
                padding: 12px 20px;
                margin-bottom: 20px;
                color: {COLORS['text_secondary']};
                font-size: 0.9rem;
            ">
                Screening <strong style="color:{COLORS['text_primary']}">Top {total_screened}</strong>
                stocks from <strong style="color:{COLORS['text_primary']}">{index_name}</strong>
                by Market Capitalization
            </div>""",
            unsafe_allow_html=True
        )

        # Metric Cards
        st.markdown(section_header("Screening Summary"), unsafe_allow_html=True)
        render_metric_cards(total_screened, passed_filters)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Derive currency symbol for display
        currency_symbol = get_currency_symbol(screening_config['index'])

        # Main Results Display
        if not results_df_raw.empty:
            # Tabbed layout: Screening Results | Deep Dive | Forecast | Sector Analysis | Portfolio | Backtest
            tab_results, tab_deep_dive, tab_forecast, tab_sector, tab_portfolio, tab_backtest = st.tabs(
                ["Screening Results", "Deep Dive Analysis", "Forecast & Valuation", "Sector Analysis", "Portfolio Builder", "Backtest"]
            )

            with tab_results:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

                # Market Context — macro indicator cards
                try:
                    macro_data = fetch_macro_indicators()
                    # Only render if at least one indicator succeeded
                    if any(v is not None for v in macro_data.values()):
                        st.markdown(section_header("Market Context"), unsafe_allow_html=True)
                        render_macro_context(macro_data)
                        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                except Exception:
                    pass  # Macro fetch failure never blocks screening results

                # Create two columns: Scatter plot (left), Summary stats (right)
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(section_header("Value Discovery Map"), unsafe_allow_html=True)
                    scatter_fig = create_value_scatter_plot(results_df_raw)
                    if scatter_fig:
                        st.plotly_chart(scatter_fig, use_container_width=True)

                with col2:
                    st.markdown(section_header("Top 5 Picks"), unsafe_allow_html=True)
                    render_top_5_cards(results_df_raw)

                    st.markdown(
                        f"""<div style="
                            background: {COLORS['surface']};
                            border: 1px solid {COLORS['border']};
                            border-radius: 10px;
                            padding: 14px 18px;
                            margin-top: 12px;
                            font-size: 0.82rem;
                            color: {COLORS['text_secondary']};
                            line-height: 1.6;
                        ">
                            <strong style="color:{COLORS['text_primary']}">How to Read:</strong><br>
                            <span style="color:{COLORS['accent_green']};">Top-Right</span> = High ROIC + Near 52w Low (Best)<br>
                            <strong>Bubble Size</strong> = Higher Value Score<br>
                            <span style="color:{COLORS['accent_green']};">Green</span> = Strong Buy &nbsp;
                            <span style="color:{COLORS['accent_red']};">Red</span> = Caution
                        </div>""",
                        unsafe_allow_html=True
                    )

                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

                # Results Table
                st.markdown(section_header("Detailed Results"), unsafe_allow_html=True)
                render_results_table(
                    results_df_formatted,
                    currency_symbol=currency_symbol
                )

            with tab_deep_dive:
                render_deep_dive_section(
                    results_df_raw=results_df_raw,
                    screening_config=screening_config,
                    stocks_data=st.session_state.stocks_data,
                    universe_df=st.session_state.universe_df,
                )

            with tab_forecast:
                render_forecast_section(
                    results_df_raw=results_df_raw,
                    screening_config=screening_config,
                    stocks_data=st.session_state.stocks_data,
                )

            with tab_sector:
                render_sector_section(
                    universe_df=st.session_state.universe_df,
                    results_df_raw=results_df_raw,
                    screening_config=screening_config,
                )

            with tab_portfolio:
                render_portfolio_section(
                    results_df_raw=results_df_raw,
                    screening_config=screening_config,
                    stocks_data=st.session_state.stocks_data,
                )

            with tab_backtest:
                render_backtest_section(
                    results_df_raw=results_df_raw,
                    screening_config=screening_config,
                )

        else:
            st.warning("No stocks passed all filters.")
            st.info(
                "**Suggestions to adjust filters:**\n"
                "- Lower the **Minimum ROIC** threshold (try 10-12%)\n"
                "- Increase the **Max Debt/Equity** ratio (try 1.0-1.5)\n"
                "- Widen the **Price Near 52w Low** percentage (try 15-20%)"
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Data Quality Report (always show after screening)
        render_data_quality_report()

    else:
        # No screening run yet - show empty state
        render_empty_state(
            "Click 'Run Screening' in the sidebar to analyze stocks from your selected index."
        )

    # Render footer
    render_footer()


# ==================== APPLICATION ENTRY POINT ====================

if __name__ == "__main__":
    main()
