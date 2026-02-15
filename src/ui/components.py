"""
Reusable UI components for the stock screener dashboard.
Includes metric cards, data tables, and data quality reports.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st
from src.utils.logger import get_data_quality_log, get_failure_summary
from src.utils.config import VIX_THRESHOLDS
from src.ui.styles import COLORS, metric_card, top_pick_card, section_header


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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            metric_card(
                label="Total Stocks Screened",
                value=f"{total_screened:,}",
                accent="blue",
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            metric_card(
                label="Passed All Filters",
                value=f"{passed_filters:,}",
                delta=f"{pass_rate:.1f}% Pass Rate",
                accent="green",
            ),
            unsafe_allow_html=True
        )


def render_macro_context(macro_data: Dict[str, Optional[Dict[str, Any]]]) -> None:
    """
    Render macro indicator cards in a 4-column row.

    VIX uses traffic-light accent coloring:
    - Green: < 15 (low fear)
    - Amber: 15-25 (moderate)
    - Red: > 25 (high fear)

    Other indicators use neutral blue accent.

    Args:
        macro_data: Dict from fetch_macro_indicators(), keys are indicator IDs
    """
    vix_green, vix_amber = VIX_THRESHOLDS

    col1, col2, col3, col4 = st.columns(4)
    columns = {"US10Y": col1, "VIX": col2, "DXY": col3, "OIL": col4}

    for key, col in columns.items():
        data = macro_data.get(key)

        with col:
            if data is None:
                st.markdown(
                    metric_card(label=key, value="N/A", accent="blue"),
                    unsafe_allow_html=True,
                )
                continue

            value = data["value"]
            change_pct = data["change_pct"]
            label = data["label"]
            unit = data["unit"]

            # Format value
            if key == "US10Y":
                value_str = f"{value:.2f}%"
            elif key == "OIL":
                value_str = f"${value:.2f}"
            else:
                value_str = f"{value:.2f}"

            # Format delta
            sign = "+" if change_pct >= 0 else ""
            delta_str = f"{sign}{change_pct:.2f}%"

            # Determine accent color
            if key == "VIX":
                if value < vix_green:
                    accent = "green"
                elif value <= vix_amber:
                    accent = "amber"
                else:
                    accent = "red"
            else:
                accent = "blue"

            st.markdown(
                metric_card(
                    label=label,
                    value=value_str,
                    delta=delta_str,
                    accent=accent,
                ),
                unsafe_allow_html=True,
            )


def render_top_5_cards(results_df_raw: pd.DataFrame) -> None:
    """
    Render the Top 5 picks as styled card components.

    Args:
        results_df_raw: Raw screening results DataFrame
    """
    top_5 = results_df_raw.head(5)

    if top_5.empty:
        st.info("No stocks to display.")
        return

    cards_html = ""
    for _, row in top_5.iterrows():
        rank = int(row.get('rank', 0))
        ticker = str(row.get('ticker', 'N/A'))
        roic_val = row.get('roic', 0)
        roic_str = f"{roic_val * 100:.1f}%" if pd.notna(roic_val) else "N/A"
        score_val = row.get('value_score', 0)
        score_str = f"{score_val:.3f}" if pd.notna(score_val) else "N/A"
        confidence = str(row.get('confidence', '')) if pd.notna(row.get('confidence')) else None

        cards_html += top_pick_card(rank, ticker, roic_str, score_str, confidence=confidence)

    st.markdown(cards_html, unsafe_allow_html=True)


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
        'confidence',
        'roic_pct',
        'de_ratio',
        'value_score',
        'momentum_score_fmt',
        'earnings_quality_fmt',
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
        'confidence': st.column_config.TextColumn(
            'Confidence',
            width='small',
            help="How complete the financial data is for a stock. "
                 "Like a report card: High = all grades available, Low = missing half the subjects. "
                 "Good: High confidence (more reliable metrics)"
        ),
        'roic_pct': st.column_config.TextColumn(
            'ROIC',
            width='small',
            help="How efficiently a company converts invested money into profit. "
                 "Like getting ₹15 profit for every ₹100 you invest in a business. "
                 "Good: > 15% (Warren Buffett's baseline)"
        ),
        'de_ratio': st.column_config.TextColumn(
            'D/E',
            width='small',
            help="How much money a company owes compared to what it owns. "
                 "Like comparing your home loan to your savings account balance. "
                 "Good: < 0.8 (less debt = more stable)"
        ),
        'value_score': st.column_config.TextColumn(
            'Value Score',
            width='small',
            help="Combined ranking of quality (ROIC 60%) and price discount (40%). "
                 "Like grading a deal: A+ quality product at 40% off = high value score. "
                 "Good: > 0.7 (top 30% of filtered stocks)"
        ),
        'momentum_score_fmt': st.column_config.TextColumn(
            'Momentum',
            width='small',
            help="Measures if a stock's price trend is improving (0-100). "
                 "Like a report card combining multiple grades into one GPA. "
                 "Good: > 60 (strong momentum, price likely to continue rising)"
        ),
        'earnings_quality_fmt': st.column_config.TextColumn(
            'EQ Score',
            width='small',
            help="How trustworthy a company's reported profits are (0-100). "
                 "Like a report card showing if grades are real or inflated. "
                 "Good: > 70 (high-quality, cash-backed earnings)"
        ),
        'market_cap_fmt': st.column_config.TextColumn(
            'Market Cap',
            width='small',
            help="The total value of all a company's shares combined. "
                 "Like the price if you wanted to buy an entire company at today's stock price."
        ),
        'current_price_fmt': st.column_config.TextColumn(
            'Price',
            width='small',
            help="Current trading price per share"
        ),
        'fifty_two_week_high_fmt': st.column_config.TextColumn(
            '52w High',
            width='small',
            help="The highest price a stock reached in the past year. "
                 "Like the most expensive a toy has been in the last 12 months."
        ),
        'fifty_two_week_low_fmt': st.column_config.TextColumn(
            '52w Low',
            width='small',
            help="The lowest price a stock reached in the past year. "
                 "Like the cheapest a toy has been in the last 12 months (might be on sale!)"
        ),
        'discount_pct': st.column_config.TextColumn(
            '% from High',
            width='small',
            help="How far below its peak price a stock is currently trading. "
                 "Like a discount label showing 30% off the original price. "
                 "Good: -20% or more (stock on sale, but check why it dropped!)"
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
        f"Data Quality Report ({total_issues} issues)",
        expanded=(total_issues > 0)
    ):
        if total_issues == 0:
            st.success("All tickers fetched successfully with complete data!")
            return

        # Display summary counts
        st.markdown(section_header("Issue Summary"), unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                metric_card(
                    label="Fetch Failures",
                    value=str(failure_summary.get('fetch_failure', 0)),
                    accent="red",
                ),
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                metric_card(
                    label="Validation Errors",
                    value=str(failure_summary.get('validation_error', 0)),
                    accent="amber",
                ),
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                metric_card(
                    label="Incomplete Data",
                    value=str(failure_summary.get('incomplete_data', 0)),
                    accent="blue",
                ),
                unsafe_allow_html=True
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Display detailed issue log
        st.markdown(section_header("Detailed Issues"), unsafe_allow_html=True)

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
    st.markdown(
        f"""<div style="
            text-align: center;
            padding: 60px 20px;
            color: {COLORS['text_secondary']};
        ">
            <div style="
                font-size: 3rem;
                margin-bottom: 16px;
                opacity: 0.3;
            ">&#9776;</div>
            <div style="
                font-size: 1.1rem;
                color: {COLORS['text_primary']};
                font-weight: 500;
                margin-bottom: 12px;
            ">{message}</div>
            <div style="
                font-size: 0.88rem;
                line-height: 1.8;
                max-width: 400px;
                margin: 0 auto;
            ">
                <strong>1.</strong> Select an index in the sidebar<br>
                <strong>2.</strong> Adjust filter thresholds (ROIC, D/E, Price)<br>
                <strong>3.</strong> Click <strong>Run Screening</strong> to analyze
            </div>
        </div>""",
        unsafe_allow_html=True
    )


def render_loading_placeholder(step: str = "Fetching data...") -> None:
    """
    Render loading placeholder with spinner and progress message.

    Args:
        step: Current processing step description
    """
    with st.spinner(f"{step}"):
        st.empty()


def render_header() -> None:
    """
    Render application header with title and description.
    """
    st.markdown(
        f"""<div style="padding: 12px 0 20px 0;">
            <div style="
                font-size: 2rem;
                font-weight: 700;
                color: {COLORS['text_primary']};
                letter-spacing: -0.03em;
                line-height: 1.2;
            ">Stock Value Screener</div>
            <div style="
                font-size: 0.95rem;
                color: {COLORS['text_secondary']};
                margin-top: 6px;
                max-width: 600px;
            ">
                Professional-grade screening for value investors.
                Combines fundamental health metrics with price-action
                discounting to identify undervalued quality companies.
            </div>
        </div>""",
        unsafe_allow_html=True
    )


def render_footer() -> None:
    """
    Render application footer with disclaimers and credits.
    """
    st.markdown(
        f"""<div style="
            margin-top: 40px;
            padding: 20px 0;
            border-top: 1px solid {COLORS['border']};
            text-align: center;
            font-size: 0.75rem;
            color: {COLORS['text_muted']};
            line-height: 1.8;
        ">
            <strong style="color:{COLORS['text_secondary']}">Disclaimer:</strong>
            This tool is for educational and research purposes only.
            Not investment advice. Always conduct your own due diligence.<br>
            Built with Streamlit, Plotly, yfinance &nbsp;&bull;&nbsp;
            Fundamentals: 24h cache &nbsp;&bull;&nbsp; Price: 1h cache &nbsp;&bull;&nbsp;
            <strong>Stock Value Screener v1.10.0</strong>
        </div>""",
        unsafe_allow_html=True
    )
