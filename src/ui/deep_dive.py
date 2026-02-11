"""
Deep Dive analysis module.
Renders per-stock charts: Price with Bollinger Bands, Quality Trends, P/E Valuation.
Also provides due diligence external links.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.fetcher import fetch_historical_prices, normalize_ticker
from src.quant.metrics import (
    calculate_bollinger_bands,
    calculate_roic_trend,
    calculate_fcf_trend,
    calculate_normalized_pe,
)
from src.utils.config import (
    get_currency_symbol,
    DUE_DILIGENCE_URLS,
    CHART_COLOR_POSITIVE,
    CHART_COLOR_NEGATIVE,
    CHART_COLOR_NEUTRAL,
)
from src.ui.styles import (
    get_plotly_theme,
    get_plotly_theme_with_legend_top,
    COLORS,
    FONT_STACK,
    section_header,
)


# ==================== MAIN ENTRY POINT ====================

def render_deep_dive_section(
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
    stocks_data: Optional[Dict[str, Optional[dict]]]
) -> None:
    """
    Render the Deep Dive Analysis tab.

    Args:
        results_df_raw: Raw screening results (for populating selectbox)
        screening_config: User config (index, ticker_limit, etc.)
        stocks_data: Cached deep data dict from screening run
    """
    if stocks_data is None:
        st.info("Run screening first to enable Deep Dive analysis.")
        return

    if results_df_raw.empty:
        st.info("No stocks passed filters. Relax thresholds to explore individual stocks.")
        return

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Build selectbox options
    options = []
    ticker_map = {}
    for _, row in results_df_raw.iterrows():
        ticker = row['ticker']
        name = row.get('company_name', ticker)
        label = f"{ticker} - {name}"
        options.append(label)
        ticker_map[label] = ticker

    selected_label = st.selectbox(
        "Select a stock for deep analysis",
        options=options,
        help="Choose from stocks that passed all screening filters"
    )

    if not selected_label:
        return

    selected_ticker = ticker_map[selected_label]
    data = stocks_data.get(selected_ticker)

    if data is None:
        st.warning(f"No data available for {selected_ticker}.")
        return

    # Derive exchange and currency
    index = screening_config.get('index', 'SP500')
    exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
    exchange = exchange_map.get(index)
    currency_symbol = get_currency_symbol(index)
    normalized = normalize_ticker(selected_ticker, exchange=exchange or "NYSE")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ---- Price Chart with Bollinger Bands ----
    st.markdown(section_header("1-Year Price Action with Bollinger Bands"), unsafe_allow_html=True)
    st.caption(
        "Bollinger Bands are statistical boundaries (20-day average +/- 2 standard deviations). "
        "Price near the lower band may indicate oversold conditions."
    )
    bollinger_fig = create_price_bollinger_chart(
        ticker=selected_ticker,
        normalized_ticker=normalized,
        currency_symbol=currency_symbol
    )
    if bollinger_fig:
        st.plotly_chart(bollinger_fig, use_container_width=True)
    else:
        st.warning(f"Historical price data unavailable for {selected_ticker}.")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Quality Trends (ROIC + FCF) ----
    st.markdown(section_header("3-Year Quality Trends"), unsafe_allow_html=True)

    income_stmt = data.get('income_statement')
    balance_sheet = data.get('balance_sheet')
    cashflow_stmt = data.get('cashflow_statement')

    col_roic, col_fcf = st.columns(2)

    with col_roic:
        roic_fig = create_roic_trend_chart(income_stmt, balance_sheet)
        if roic_fig:
            st.plotly_chart(roic_fig, use_container_width=True)
        else:
            st.info("ROIC trend data unavailable.")

    with col_fcf:
        fcf_fig = create_fcf_trend_chart(cashflow_stmt, currency_symbol)
        if fcf_fig:
            st.plotly_chart(fcf_fig, use_container_width=True)
        else:
            st.info("Free Cash Flow trend data unavailable.")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- P/E Valuation (Mean Reversion) ----
    st.markdown(section_header("P/E Valuation: Mean Reversion"), unsafe_allow_html=True)
    st.caption(
        "Mean Reversion: stocks tend to return to their long-term average P/E ratio. "
        "A current P/E below the 3-year average may signal undervaluation."
    )
    pe_fig = create_pe_valuation_chart(data, income_stmt)
    if pe_fig:
        st.plotly_chart(pe_fig, use_container_width=True)
    else:
        st.info("P/E valuation data unavailable (company may have negative earnings).")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Due Diligence Links ----
    render_due_diligence_links(selected_ticker, index)


# ==================== PRICE CHART WITH BOLLINGER BANDS ====================

def create_price_bollinger_chart(
    ticker: str,
    normalized_ticker: str,
    currency_symbol: str
) -> Optional[go.Figure]:
    """
    Create 1-year candlestick chart with Bollinger Bands overlay.

    Args:
        ticker: Raw ticker symbol (for display)
        normalized_ticker: Yahoo Finance normalized ticker (for fetching)
        currency_symbol: '$' or '\u20b9'

    Returns:
        Plotly Figure or None if data unavailable
    """
    price_df = fetch_historical_prices(normalized_ticker, period="1y")

    if price_df is None or price_df.empty:
        return None

    bb_df = calculate_bollinger_bands(price_df)

    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=bb_df.index,
        open=bb_df['Open'],
        high=bb_df['High'],
        low=bb_df['Low'],
        close=bb_df['Close'],
        name='Price',
        increasing_line_color=CHART_COLOR_POSITIVE,
        decreasing_line_color=CHART_COLOR_NEGATIVE,
    ))

    # 20-day SMA
    fig.add_trace(go.Scatter(
        x=bb_df.index,
        y=bb_df['SMA_20'],
        mode='lines',
        name='20-Day SMA',
        line=dict(color=CHART_COLOR_NEUTRAL, width=1.5),
    ))

    # Upper Bollinger Band
    fig.add_trace(go.Scatter(
        x=bb_df.index,
        y=bb_df['BB_Upper'],
        mode='lines',
        name='Upper Band',
        line=dict(color='rgba(99, 102, 241, 0.4)', width=1, dash='dash'),
    ))

    # Lower Bollinger Band (with fill between upper and lower)
    fig.add_trace(go.Scatter(
        x=bb_df.index,
        y=bb_df['BB_Lower'],
        mode='lines',
        name='Lower Band',
        line=dict(color='rgba(99, 102, 241, 0.4)', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(99, 102, 241, 0.08)',
    ))

    # Apply theme
    theme = get_plotly_theme_with_legend_top()
    fig.update_layout(**theme)

    fig.update_layout(
        title=dict(
            text=f"{ticker} — 1 Year Price with Bollinger Bands",
        ),
        yaxis_title=f"Price ({currency_symbol})",
        xaxis_title="Date",
        xaxis=dict(rangeslider=dict(visible=False)),
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode='x unified',
    )

    return fig


# ==================== ROIC TREND CHART ====================

def create_roic_trend_chart(
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame]
) -> Optional[go.Figure]:
    """
    Create 3-year ROIC bar chart with 15% reference line.

    Returns:
        Plotly Figure or None if data unavailable
    """
    trend = calculate_roic_trend(income_statement, balance_sheet, years=3)

    if not trend:
        return None

    # Filter out entries with None ROIC
    valid = [t for t in trend if t['roic'] is not None]
    if not valid:
        return None

    years = [t['year'] for t in valid]
    roic_pcts = [t['roic'] * 100 for t in valid]

    # Color-code bars: green >15%, amber 10-15%, red <10%
    colors = []
    for r in roic_pcts:
        if r >= 15:
            colors.append(CHART_COLOR_POSITIVE)
        elif r >= 10:
            colors.append(COLORS['accent_amber'])
        else:
            colors.append(CHART_COLOR_NEGATIVE)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=years,
        y=roic_pcts,
        marker_color=colors,
        text=[f"{r:.1f}%" for r in roic_pcts],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary']),
        name='ROIC',
    ))

    # 15% reference line (Buffett baseline)
    fig.add_hline(
        y=15,
        line_dash="dash",
        line_color=COLORS['text_muted'],
        annotation_text="15% baseline",
        annotation_position="top right",
        annotation_font_size=10,
        annotation_font_color=COLORS['text_muted'],
    )

    # Apply theme
    fig.update_layout(**get_plotly_theme())
    fig.update_layout(
        title=dict(text="ROIC Trend (3-Year)"),
        yaxis_title="ROIC (%)",
        xaxis_title="Fiscal Year",
        height=350,
        margin=dict(l=50, r=30, t=60, b=50),
        showlegend=False,
    )

    return fig


# ==================== FCF TREND CHART ====================

def create_fcf_trend_chart(
    cashflow_statement: Optional[pd.DataFrame],
    currency_symbol: str = "$"
) -> Optional[go.Figure]:
    """
    Create 3-year Free Cash Flow bar chart.

    Returns:
        Plotly Figure or None if data unavailable
    """
    trend = calculate_fcf_trend(cashflow_statement, years=3)

    if not trend:
        return None

    valid = [t for t in trend if t['fcf'] is not None]
    if not valid:
        return None

    years = [t['year'] for t in valid]
    fcf_values = [t['fcf'] for t in valid]

    colors = [CHART_COLOR_POSITIVE if v >= 0 else CHART_COLOR_NEGATIVE for v in fcf_values]

    # Format labels
    labels = [_format_large_number(v, currency_symbol) for v in fcf_values]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=years,
        y=fcf_values,
        marker_color=colors,
        text=labels,
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary']),
        name='FCF',
    ))

    # Apply theme
    fig.update_layout(**get_plotly_theme())
    fig.update_layout(
        title=dict(text="Free Cash Flow Trend (3-Year)"),
        yaxis_title=f"FCF ({currency_symbol})",
        xaxis_title="Fiscal Year",
        height=350,
        margin=dict(l=50, r=30, t=60, b=50),
        showlegend=False,
    )

    return fig


# ==================== P/E VALUATION CHART ====================

def create_pe_valuation_chart(
    data: dict,
    income_statement: Optional[pd.DataFrame]
) -> Optional[go.Figure]:
    """
    Create P/E mean reversion comparison chart.
    Shows Current P/E vs 3-Year Normalized P/E.

    Returns:
        Plotly Figure or None if data unavailable
    """
    pe_data = calculate_normalized_pe(data, income_statement)

    current_pe = pe_data.get("current_pe")
    normalized_pe = pe_data.get("normalized_pe")

    if current_pe is None and normalized_pe is None:
        return None

    categories = []
    values = []
    colors = []

    if current_pe is not None:
        categories.append("Current P/E")
        values.append(round(current_pe, 1))
        colors.append(CHART_COLOR_NEUTRAL)

    if normalized_pe is not None:
        categories.append("3-Year Avg P/E")
        values.append(round(normalized_pe, 1))
        colors.append(COLORS['text_muted'])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f"{v:.1f}x" for v in values],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary']),
        width=0.5,
    ))

    # Add premium/discount annotation
    pe_premium = pe_data.get("pe_premium_pct")
    if pe_premium is not None:
        if pe_premium > 0:
            annotation_text = f"Trading at {pe_premium:.1f}% PREMIUM to 3-yr avg"
            annotation_color = CHART_COLOR_NEGATIVE
        else:
            annotation_text = f"Trading at {abs(pe_premium):.1f}% DISCOUNT to 3-yr avg"
            annotation_color = CHART_COLOR_POSITIVE

        fig.add_annotation(
            text=annotation_text,
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=13, color=annotation_color, family=FONT_STACK),
        )

    # Apply theme
    fig.update_layout(**get_plotly_theme())
    fig.update_layout(
        title=dict(text="P/E Ratio: Mean Reversion Analysis"),
        yaxis_title="P/E Ratio (x)",
        height=350,
        margin=dict(l=50, r=30, t=60, b=80),
        showlegend=False,
    )

    return fig


# ==================== DUE DILIGENCE LINKS ====================

def render_due_diligence_links(ticker: str, index: str) -> None:
    """
    Render external due diligence link buttons.

    Args:
        ticker: Raw ticker symbol (without exchange suffix)
        index: 'NIFTY100' or 'SP500'
    """
    st.markdown(section_header("Due Diligence"), unsafe_allow_html=True)

    urls = DUE_DILIGENCE_URLS.get(index, {})

    if not urls:
        st.info("No external links configured for this index.")
        return

    cols = st.columns(len(urls))

    for i, (name, url_template) in enumerate(urls.items()):
        url = url_template.format(ticker=ticker)
        with cols[i]:
            st.link_button(
                label=f"Open {name}",
                url=url,
                use_container_width=True,
            )


# ==================== HELPERS ====================

def _format_large_number(value: float, currency_symbol: str = "$") -> str:
    """Format a large number as readable string (e.g., $1.5B, \u20b9450Cr)."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1e12:
        return f"{sign}{currency_symbol}{abs_val/1e12:.1f}T"
    elif abs_val >= 1e9:
        return f"{sign}{currency_symbol}{abs_val/1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"{sign}{currency_symbol}{abs_val/1e6:.1f}M"
    else:
        return f"{sign}{currency_symbol}{abs_val:,.0f}"
