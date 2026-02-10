"""
Reusable UI components for the stock screener dashboard.
Includes metric cards, data tables, and data quality reports.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st
from src.utils.logger import get_data_quality_log, get_failure_summary


def render_metric_cards(total_screened: int, passed_filters: int) -> None:
    """
    Render metric cards showing screening summary statistics.

    Displays two cards side-by-side:
    1. Total Stocks Screened
    2. Stocks Passing All Filters (with pass rate %)

    Args:
        total_screened: Total number of tickers screened
        passed_filters: Number of tickers that passed all filters
    """
    # Calculate pass rate
    pass_rate = (passed_filters / total_screened * 100) if total_screened > 0 else 0

    # Create two columns for side-by-side metrics
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="📊 Total Stocks Screened",
            value=f"{total_screened:,}",
            help="Number of tickers fetched and analyzed from the selected index"
        )

    with col2:
        st.metric(
            label="✅ Passed All Filters",
            value=f"{passed_filters:,}",
            delta=f"{pass_rate:.1f}% Pass Rate",
            delta_color="normal",
            help="Stocks meeting ALL quality and valuation criteria"
        )


def render_results_table(
    df: pd.DataFrame,
    max_rows: int = 50,
    currency_symbol: str = "$"
) -> None:
    """
    Render searchable and sortable results table with metric tooltips.

    Displays key columns:
    - Rank, Ticker, Company Name
    - ROIC (%), D/E Ratio, Value Score (with educational tooltips)
    - Market Cap, Current Price
    - 52w High, 52w Low, % from High, % Above 52w Low

    Args:
        df: Screened and formatted results DataFrame
        max_rows: Maximum number of rows to display (default 50)
        currency_symbol: Currency symbol ('$' or '\u20b9')
    """
    if df.empty:
        st.warning("No stocks passed all filters. Try relaxing the filter thresholds.")
        st.info(
            "**Suggestions:**\n"
            "- Lower the Minimum ROIC threshold\n"
            "- Increase the Max Debt/Equity ratio\n"
            "- Widen the 'Price Near 52w Low' percentage"
        )
        return

    # Select and order columns for display
    display_columns = [
        'rank',
        'ticker',
        'company_name',
        'roic_pct',
        'de_ratio',
        'value_score',
        'market_cap_fmt',
        'current_price_fmt',
        'fifty_two_week_high_fmt',
        'fifty_two_week_low_fmt',
        'discount_pct',
        'distance_from_low',
    ]

    # Filter to only available columns (in case some are missing)
    available_columns = [col for col in display_columns if col in df.columns]

    display_df = df[available_columns].head(max_rows)

    # Column config with educational tooltips (help parameter)
    column_config = {
        'rank': st.column_config.NumberColumn('Rank', width='small'),
        'ticker': st.column_config.TextColumn('Ticker', width='small'),
        'company_name': st.column_config.TextColumn('Company', width='medium'),
        'roic_pct': st.column_config.TextColumn(
            'ROIC',
            width='small',
            help="Return on Invested Capital: how efficiently the company converts "
                 "invested capital into profit. Above 15% is excellent."
        ),
        'de_ratio': st.column_config.TextColumn(
            'D/E',
            width='small',
            help="Debt-to-Equity Ratio: total debt divided by total equity. "
                 "Below 0.8 indicates conservative financial leverage."
        ),
        'value_score': st.column_config.TextColumn(
            'Value Score',
            width='small',
            help="Composite score: 60% quality (ROIC) + 40% price discount from peak. "
                 "Higher score = better value opportunity."
        ),
        'market_cap_fmt': st.column_config.TextColumn('Market Cap', width='small'),
        'current_price_fmt': st.column_config.TextColumn(
            'Price',
            width='small',
            help="Current trading price"
        ),
        'fifty_two_week_high_fmt': st.column_config.TextColumn(
            '52w High',
            width='small',
            help="Highest trading price in the last 52 weeks"
        ),
        'fifty_two_week_low_fmt': st.column_config.TextColumn(
            '52w Low',
            width='small',
            help="Lowest trading price in the last 52 weeks"
        ),
        'discount_pct': st.column_config.TextColumn(
            '% from High',
            width='small',
            help="How far below the 52-week high (negative = below peak). "
                 "Larger discounts may signal value opportunities."
        ),
        'distance_from_low': st.column_config.NumberColumn(
            '% Above Low',
            format='%.2f%%',
            width='small',
            help="Percentage above the 52-week low"
        ),
    }

    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Add download button for CSV export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Results (CSV)",
        data=csv,
        file_name="stock_screening_results.csv",
        mime="text/csv",
        help="Download complete screening results as CSV"
    )


def render_data_quality_report() -> None:
    """
    Render data quality report in an expander.

    Shows:
    - Total fetch failures
    - Breakdown by issue type (fetch_failure, validation_error, incomplete_data)
    - Detailed list of failed tickers with error messages
    """
    quality_log = get_data_quality_log()
    failure_summary = get_failure_summary()

    # Count total issues
    total_issues = len(quality_log)

    # Create expander (collapsed by default if no issues)
    with st.expander(
        f"🔍 Data Quality Report ({total_issues} issues)",
        expanded=(total_issues > 0)
    ):
        if total_issues == 0:
            st.success("✅ All tickers fetched successfully with complete data!")
            return

        # Display summary counts
        st.subheader("Issue Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Fetch Failures",
                failure_summary.get('fetch_failure', 0),
                help="Tickers that could not be fetched from yfinance API"
            )

        with col2:
            st.metric(
                "Validation Errors",
                failure_summary.get('validation_error', 0),
                help="Tickers with missing required financial fields"
            )

        with col3:
            st.metric(
                "Incomplete Data",
                failure_summary.get('incomplete_data', 0),
                help="Tickers with partial data (< 70% completeness)"
            )

        st.markdown("---")

        # Display detailed issue log
        st.subheader("Detailed Issues")

        # Convert log to DataFrame for better display
        if quality_log:
            log_data = []
            for issue in quality_log:
                log_data.append({
                    'Ticker': issue.ticker,
                    'Issue Type': issue.issue_type.replace('_', ' ').title(),
                    'Error': issue.error_message,
                    'Timestamp': issue.timestamp.strftime('%H:%M:%S')
                })

            log_df = pd.DataFrame(log_data)

            st.dataframe(
                log_df,
                use_container_width=True,
                hide_index=True,
                height=200
            )
        else:
            st.info("No issues to display.")


def render_empty_state(message: str = "No data to display") -> None:
    """
    Render empty state placeholder when no screening has been run.

    Args:
        message: Custom message to display
    """
    st.info(f"ℹ️ {message}")
    st.markdown(
        """
        **To get started:**
        1. Select an index (Nifty 100 or S&P 500) in the sidebar
        2. Adjust filter thresholds (ROIC, D/E, Price Near Low)
        3. Click **Run Screening** to fetch data and see results
        """
    )


def render_loading_placeholder(step: str = "Fetching data...") -> None:
    """
    Render loading placeholder with spinner and progress message.

    Args:
        step: Current processing step description
    """
    with st.spinner(f"⏳ {step}"):
        st.empty()


def render_header() -> None:
    """
    Render application header with title and description.
    """
    st.title("📈 Stock Value Screener")
    st.markdown(
        """
        **Professional-grade stock screening for value investors.**
        Combines fundamental health metrics (ROIC, FCF, Debt/Equity) with price-action
        discounting to identify undervalued quality companies.
        """
    )
    st.markdown("---")


def render_footer() -> None:
    """
    Render application footer with disclaimers and credits.
    """
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer:** This tool is for educational and research purposes only. "
        "Not investment advice. Always conduct your own due diligence before investing."
    )
    st.caption(
        "🔧 **Built with:** Streamlit, Plotly, yfinance | "
        "**Data Refresh:** Fundamentals (24h), Price (1h)"
    )
