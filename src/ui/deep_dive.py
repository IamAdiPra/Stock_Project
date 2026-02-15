"""
Deep Dive analysis module.
Renders per-stock charts: Price with Bollinger Bands, Quality Trends, P/E Valuation.
Also provides due diligence external links.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import numpy as np
from src.data.fetcher import fetch_historical_prices, normalize_ticker
from src.quant.metrics import (
    calculate_bollinger_bands,
    calculate_roic_trend,
    calculate_fcf_trend,
    calculate_normalized_pe,
    calculate_earnings_quality,
    calculate_momentum_score,
    calculate_momentum_indicators,
    calculate_all_metrics,
)
from plotly.subplots import make_subplots
from src.utils.config import (
    get_currency_symbol,
    DUE_DILIGENCE_URLS,
    CHART_COLOR_POSITIVE,
    CHART_COLOR_NEGATIVE,
    CHART_COLOR_NEUTRAL,
    PEER_COMPARISON_COUNT,
)
from src.ui.styles import (
    get_plotly_theme,
    get_plotly_theme_with_legend_top,
    COLORS,
    FONT_STACK,
    section_header,
    metric_card,
)


# ==================== MAIN ENTRY POINT ====================

def render_deep_dive_section(
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
    stocks_data: Optional[Dict[str, Optional[dict]]],
    universe_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the Deep Dive Analysis tab.

    Args:
        results_df_raw: Raw screening results (for populating selectbox)
        screening_config: User config (index, ticker_limit, etc.)
        stocks_data: Cached deep data dict from screening run
        universe_df: Full universe DataFrame for peer comparison (optional)
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

    # Fetch 2y historical data once (reused for Bollinger, SMA overlay, and momentum charts)
    price_df_2y = fetch_historical_prices(normalized, period="2y")

    # ---- Price Chart with Bollinger Bands & SMA ----
    st.markdown(section_header("1-Year Price Action with Bollinger Bands & SMA"), unsafe_allow_html=True)
    st.caption(
        "Bollinger Bands are statistical boundaries (20-day average +/- 2 standard deviations). "
        "SMA 50 (amber) and SMA 200 (purple) show short- and long-term trends. "
        "Golden Cross (50 > 200) is a bullish signal."
    )
    bollinger_fig = create_price_bollinger_chart(
        ticker=selected_ticker,
        normalized_ticker=normalized,
        currency_symbol=currency_symbol,
        price_df_2y=price_df_2y,
    )
    if bollinger_fig:
        st.plotly_chart(bollinger_fig, use_container_width=True)
    else:
        st.warning(f"Historical price data unavailable for {selected_ticker}.")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Momentum Indicators ----
    st.markdown(section_header("Momentum Indicators"), unsafe_allow_html=True)
    st.caption(
        "RSI measures overbought/oversold conditions (sweet spot 30-55 for value investors). "
        "MACD shows trend strength and direction. "
        "Histogram above zero = bullish momentum."
    )
    render_momentum_section(price_df_2y, selected_ticker)

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

    # ---- Earnings Quality Assessment ----
    st.markdown(section_header("Earnings Quality Assessment"), unsafe_allow_html=True)
    st.caption(
        "Evaluates how trustworthy reported earnings are by checking if profits are "
        "backed by actual cash. Combines accrual ratio, FCF/NI conversion, and "
        "revenue vs receivables growth divergence."
    )
    render_earnings_quality_section(data)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Peer Comparison Panel ----
    if universe_df is not None and not universe_df.empty:
        st.markdown(section_header("Peer Comparison"), unsafe_allow_html=True)
        st.caption(
            "Compares the selected stock against 5-8 peers from the same sector/industry. "
            "Radar chart axes are normalized 0-100 within the peer group. "
            "Outward = better on each dimension."
        )
        render_peer_comparison_section(
            selected_ticker=selected_ticker,
            data=data,
            universe_df=universe_df,
            stocks_data=stocks_data,
            currency_symbol=currency_symbol,
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Due Diligence Links ----
    render_due_diligence_links(selected_ticker, index)


# ==================== PRICE CHART WITH BOLLINGER BANDS ====================

def create_price_bollinger_chart(
    ticker: str,
    normalized_ticker: str,
    currency_symbol: str,
    price_df_2y: Optional[pd.DataFrame] = None,
) -> Optional[go.Figure]:
    """
    Create 1-year candlestick chart with Bollinger Bands and SMA overlays.

    If 2y price data is provided, SMA 50 and SMA 200 are computed from the
    full 2y history and overlaid on the last 1y of the chart.

    Args:
        ticker: Raw ticker symbol (for display)
        normalized_ticker: Yahoo Finance normalized ticker (for fetching)
        currency_symbol: '$' or '\u20b9'
        price_df_2y: Optional pre-fetched 2y price DataFrame for SMA computation

    Returns:
        Plotly Figure or None if data unavailable
    """
    # Use 2y data if provided, otherwise fallback to 1y fetch
    if price_df_2y is not None and not price_df_2y.empty:
        full_df = price_df_2y
    else:
        full_df = fetch_historical_prices(normalized_ticker, period="1y")

    if full_df is None or full_df.empty:
        return None

    # Compute Bollinger Bands on last 1y slice
    # Determine 1y cutoff (~252 trading days)
    one_year_rows = min(252, len(full_df))
    display_df = full_df.iloc[-one_year_rows:]
    bb_df = calculate_bollinger_bands(display_df)

    # Compute SMAs on full 2y history, then slice to display range
    sma_50 = None
    sma_200 = None
    close = full_df['Close']
    if len(close) >= 50:
        sma_50_full = close.rolling(window=50).mean()
        sma_50 = sma_50_full.iloc[-one_year_rows:]
    if len(close) >= 200:
        sma_200_full = close.rolling(window=200).mean()
        sma_200 = sma_200_full.iloc[-one_year_rows:]

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

    # 20-day SMA (Bollinger midline)
    fig.add_trace(go.Scatter(
        x=bb_df.index,
        y=bb_df['SMA_20'],
        mode='lines',
        name='SMA 20',
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

    # SMA 50 overlay (amber)
    if sma_50 is not None:
        fig.add_trace(go.Scatter(
            x=sma_50.index,
            y=sma_50,
            mode='lines',
            name='SMA 50',
            line=dict(color=COLORS['accent_amber'], width=1.5, dash='dot'),
        ))

    # SMA 200 overlay (purple)
    if sma_200 is not None:
        fig.add_trace(go.Scatter(
            x=sma_200.index,
            y=sma_200,
            mode='lines',
            name='SMA 200',
            line=dict(color=COLORS['accent_purple'], width=1.5, dash='dot'),
        ))

    # Apply theme
    theme = get_plotly_theme_with_legend_top()
    fig.update_layout(**theme)

    fig.update_layout(
        title=dict(
            text=f"{ticker} — 1 Year Price with Bollinger Bands & SMA",
        ),
        yaxis_title=f"Price ({currency_symbol})",
        xaxis_title="Date",
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode='x unified',
    )

    fig.update_xaxes(rangeslider=dict(visible=False))

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


# ==================== EARNINGS QUALITY ====================

def render_earnings_quality_section(data: dict) -> None:
    """
    Render earnings quality gauge chart and component breakdown.

    Args:
        data: Complete stock data dict (from fetch_deep_data)
    """
    eq = calculate_earnings_quality(data)
    score = eq.get("earnings_quality_score")

    if score is None:
        st.info("Earnings quality data unavailable (insufficient financial statements).")
        return

    col_gauge, col_breakdown = st.columns([1, 1])

    with col_gauge:
        fig = create_earnings_quality_gauge(score)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with col_breakdown:
        # Accrual Ratio card
        accrual = eq.get("accrual_ratio")
        if accrual is not None:
            accrual_accent = "green" if accrual < 0.05 else ("amber" if accrual < 0.15 else "red")
            st.markdown(
                metric_card(
                    label="Accrual Ratio",
                    value=f"{accrual:.3f}",
                    delta="Lower = better (cash backs income)" if accrual < 0.05 else "High accruals — verify cash quality",
                    accent=accrual_accent,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                metric_card(label="Accrual Ratio", value="N/A", accent="blue"),
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # FCF/NI Ratio card
        fcf_ni = eq.get("fcf_to_ni_ratio")
        if fcf_ni is not None:
            fcf_accent = "green" if fcf_ni >= 0.8 else ("amber" if fcf_ni >= 0.4 else "red")
            st.markdown(
                metric_card(
                    label="FCF / Net Income",
                    value=f"{fcf_ni:.2f}x",
                    delta="Strong cash conversion" if fcf_ni >= 1.0 else "Cash lags reported profit",
                    accent=fcf_accent,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                metric_card(label="FCF / Net Income", value="N/A", accent="blue"),
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Rev/Rec Divergence card
        rev_rec = eq.get("rev_rec_divergence")
        if rev_rec is not None:
            rr_accent = "green" if rev_rec >= 0.0 else ("amber" if rev_rec >= -0.05 else "red")
            rr_pct = f"{rev_rec * 100:+.1f}%"
            st.markdown(
                metric_card(
                    label="Revenue vs Receivables Gap",
                    value=rr_pct,
                    delta="Healthy collections" if rev_rec >= 0.0 else "Receivables outpacing revenue",
                    accent=rr_accent,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                metric_card(label="Revenue vs Receivables Gap", value="N/A", accent="blue"),
                unsafe_allow_html=True,
            )


def create_earnings_quality_gauge(score: float) -> Optional[go.Figure]:
    """
    Create a Plotly gauge chart for the Earnings Quality Score.

    Args:
        score: Composite score 0-100

    Returns:
        Plotly Figure or None
    """
    if score >= 70:
        bar_color = COLORS["accent_green"]
    elif score >= 40:
        bar_color = COLORS["accent_amber"]
    else:
        bar_color = COLORS["accent_red"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 42, "color": COLORS["text_primary"]}, "suffix": ""},
        title={"text": "Earnings Quality", "font": {"size": 16, "color": COLORS["text_secondary"]}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": COLORS["border"],
                "dtick": 20,
                "tickfont": {"color": COLORS["text_muted"], "size": 11},
            },
            "bar": {"color": bar_color, "thickness": 0.7},
            "bgcolor": COLORS["surface"],
            "borderwidth": 1,
            "bordercolor": COLORS["border"],
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.12)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.12)"},
                {"range": [70, 100], "color": "rgba(16,185,129,0.12)"},
            ],
            "threshold": {
                "line": {"color": COLORS["text_muted"], "width": 2},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))

    fig.update_layout(
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"family": FONT_STACK, "color": COLORS["text_secondary"]},
        height=280,
        margin=dict(l=30, r=30, t=60, b=20),
    )

    return fig


# ==================== MOMENTUM INDICATORS ====================

def render_momentum_section(
    price_df_2y: Optional[pd.DataFrame],
    ticker: str,
) -> None:
    """
    Render momentum indicators: RSI/MACD chart and summary metric cards.

    Args:
        price_df_2y: 2-year historical price DataFrame
        ticker: Raw ticker symbol (for display)
    """
    if price_df_2y is None or price_df_2y.empty:
        st.info("Historical price data unavailable for momentum analysis.")
        return

    # Compute current momentum score for metric cards
    momentum = calculate_momentum_score(price_df_2y)
    score = momentum.get("momentum_score")

    if score is None:
        st.info("Insufficient price history for momentum indicators.")
        return

    # Chart and cards side by side
    col_chart, col_cards = st.columns([2, 1])

    with col_chart:
        momentum_fig = create_momentum_chart(price_df_2y, ticker)
        if momentum_fig:
            st.plotly_chart(momentum_fig, use_container_width=True)

    with col_cards:
        # Momentum Score gauge-like card
        if score >= 60:
            score_accent = "green"
            score_delta = "Bullish momentum"
        elif score >= 40:
            score_accent = "amber"
            score_delta = "Neutral momentum"
        else:
            score_accent = "red"
            score_delta = "Bearish momentum"

        st.markdown(
            metric_card(
                label="Momentum Score",
                value=f"{int(score)}",
                delta=score_delta,
                accent=score_accent,
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # RSI card
        rsi = momentum.get("rsi")
        if rsi is not None:
            if rsi < 30:
                rsi_accent, rsi_label = "green", "Oversold"
            elif rsi < 50:
                rsi_accent, rsi_label = "green", "Recovery zone"
            elif rsi < 70:
                rsi_accent, rsi_label = "amber", "Neutral-bullish"
            else:
                rsi_accent, rsi_label = "red", "Overbought"
            st.markdown(
                metric_card(label="RSI (14)", value=f"{rsi:.1f}", delta=rsi_label, accent=rsi_accent),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(metric_card(label="RSI (14)", value="N/A", accent="blue"), unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # SMA crossover card
        golden = momentum.get("golden_cross")
        if golden is True:
            sma_accent, sma_label = "green", "Golden Cross"
        elif golden is False:
            sma_accent, sma_label = "red", "Death Cross"
        else:
            sma_accent, sma_label = "blue", "N/A"
        sma_val = "50 > 200" if golden else ("50 < 200" if golden is False else "N/A")
        st.markdown(
            metric_card(label="SMA Crossover", value=sma_val, delta=sma_label, accent=sma_accent),
            unsafe_allow_html=True,
        )


def create_momentum_chart(
    price_df_2y: pd.DataFrame,
    ticker: str,
) -> Optional[go.Figure]:
    """
    Create a 2-row subplot with RSI and MACD indicators (last 1y displayed).

    Row 1: RSI line with 30/70 reference lines and colored zones.
    Row 2: MACD line + signal line + histogram bars.

    Args:
        price_df_2y: 2-year historical price DataFrame
        ticker: Raw ticker symbol (for title)

    Returns:
        Plotly Figure or None if insufficient data
    """
    indicators = calculate_momentum_indicators(price_df_2y)
    if indicators is None:
        return None

    # Slice to last 1 year for display
    one_year_rows = min(252, len(indicators))
    ind = indicators.iloc[-one_year_rows:]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.45, 0.55],
        subplot_titles=("RSI (14-Day)", "MACD (12/26/9)"),
    )

    # ---- Row 1: RSI ----
    if 'RSI' in ind.columns:
        fig.add_trace(
            go.Scatter(
                x=ind.index, y=ind['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color=CHART_COLOR_NEUTRAL, width=1.5),
            ),
            row=1, col=1,
        )

        # Overbought reference line (70)
        fig.add_hline(
            y=70, line_dash="dash", line_color=COLORS['accent_red'],
            line_width=1, row=1, col=1,
            annotation_text="70", annotation_position="right",
            annotation_font_size=10, annotation_font_color=COLORS['accent_red'],
        )

        # Oversold reference line (30)
        fig.add_hline(
            y=30, line_dash="dash", line_color=COLORS['accent_green'],
            line_width=1, row=1, col=1,
            annotation_text="30", annotation_position="right",
            annotation_font_size=10, annotation_font_color=COLORS['accent_green'],
        )

        # Neutral line (50)
        fig.add_hline(
            y=50, line_dash="dot", line_color=COLORS['text_muted'],
            line_width=1, row=1, col=1,
        )

    # ---- Row 2: MACD ----
    if 'MACD' in ind.columns and 'MACD_Signal' in ind.columns:
        # MACD line
        fig.add_trace(
            go.Scatter(
                x=ind.index, y=ind['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color=CHART_COLOR_NEUTRAL, width=1.5),
            ),
            row=2, col=1,
        )

        # Signal line
        fig.add_trace(
            go.Scatter(
                x=ind.index, y=ind['MACD_Signal'],
                mode='lines',
                name='Signal',
                line=dict(color=COLORS['accent_amber'], width=1.5),
            ),
            row=2, col=1,
        )

    if 'MACD_Histogram' in ind.columns:
        # Histogram bars (green for positive, red for negative)
        hist = ind['MACD_Histogram'].dropna()
        colors = [
            CHART_COLOR_POSITIVE if v >= 0 else CHART_COLOR_NEGATIVE
            for v in hist
        ]
        fig.add_trace(
            go.Bar(
                x=hist.index, y=hist,
                name='Histogram',
                marker_color=colors,
                opacity=0.6,
            ),
            row=2, col=1,
        )

    # Apply theme
    theme = get_plotly_theme()
    fig.update_layout(**theme)

    fig.update_layout(
        height=450,
        margin=dict(l=50, r=30, t=40, b=40),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(color=COLORS['text_secondary']),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode='x unified',
    )

    # Style subplots
    fig.update_yaxes(
        title_text="RSI", row=1, col=1,
        range=[0, 100],
        gridcolor=COLORS['border'],
    )
    fig.update_yaxes(
        title_text="MACD", row=2, col=1,
        gridcolor=COLORS['border'],
    )

    # Style subplot titles
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(color=COLORS['text_secondary'], size=13)

    return fig


# ==================== PEER COMPARISON PANEL ====================

def _get_sector_peers(
    selected_ticker: str,
    universe_df: pd.DataFrame,
    stocks_data: Dict[str, Optional[dict]],
    max_peers: int = PEER_COMPARISON_COUNT,
) -> pd.DataFrame:
    """
    Find sector/industry peers for a stock from the full universe.

    Strategy: same industry first, expand to sector if < 5, sort by
    market cap proximity to the selected stock.

    Args:
        selected_ticker: The stock to find peers for
        universe_df: Full screened universe with sector/industry/metrics
        stocks_data: Raw deep data dict (for computing extra metrics)
        max_peers: Maximum peers to return

    Returns:
        DataFrame with peer rows including extra computed metrics
    """
    if universe_df is None or universe_df.empty:
        return pd.DataFrame()

    row = universe_df[universe_df['ticker'] == selected_ticker]
    if row.empty:
        return pd.DataFrame()

    stock_sector = row.iloc[0]['sector']
    stock_industry = row.iloc[0]['industry']
    stock_mcap = row.iloc[0].get('market_cap') or 0

    # Exclude the selected stock itself
    others = universe_df[universe_df['ticker'] != selected_ticker].copy()

    # Try industry peers first
    industry_peers = others[others['industry'] == stock_industry]

    if len(industry_peers) >= 5:
        candidates = industry_peers
    else:
        # Expand to sector
        sector_peers = others[others['sector'] == stock_sector]
        candidates = sector_peers

    if candidates.empty:
        return pd.DataFrame()

    # Sort by market cap proximity
    candidates = candidates.copy()
    candidates['_mcap_dist'] = (candidates['market_cap'].fillna(0) - stock_mcap).abs()
    candidates = candidates.sort_values('_mcap_dist').head(max_peers)
    candidates = candidates.drop(columns=['_mcap_dist'])

    # Compute extra metrics from stocks_data for each peer
    eq_scores = []
    dist_from_high_vals = []
    for _, peer_row in candidates.iterrows():
        peer_ticker = peer_row['ticker']
        peer_data = stocks_data.get(peer_ticker)
        if peer_data is not None:
            metrics = calculate_all_metrics(peer_data)
            eq_scores.append(metrics.get('earnings_quality_score'))
            dist_from_high_vals.append(metrics.get('distance_from_high'))
        else:
            eq_scores.append(None)
            dist_from_high_vals.append(None)

    candidates = candidates.copy()
    candidates['earnings_quality_score'] = eq_scores
    candidates['distance_from_high'] = dist_from_high_vals

    return candidates.reset_index(drop=True)


def render_peer_comparison_section(
    selected_ticker: str,
    data: dict,
    universe_df: pd.DataFrame,
    stocks_data: Dict[str, Optional[dict]],
    currency_symbol: str,
) -> None:
    """
    Render the peer comparison panel: table + radar chart.

    Args:
        selected_ticker: Currently selected stock ticker
        data: Selected stock's deep data dict
        universe_df: Full universe DataFrame
        stocks_data: Raw deep data for all stocks
        currency_symbol: '$', etc.
    """
    if universe_df is None or universe_df.empty:
        st.info("Run screening first to enable peer comparison.")
        return

    peers_df = _get_sector_peers(selected_ticker, universe_df, stocks_data)

    if peers_df.empty:
        st.info("No sector peers found for this stock.")
        return

    # Get selected stock's own metrics
    stock_row = universe_df[universe_df['ticker'] == selected_ticker]
    if stock_row.empty:
        st.info("Selected stock not found in universe data.")
        return

    stock_metrics = calculate_all_metrics(data)
    stock_roic = stock_row.iloc[0].get('roic')
    stock_de = stock_row.iloc[0].get('debt_to_equity')
    stock_mcap = stock_row.iloc[0].get('market_cap')
    stock_eq = stock_metrics.get('earnings_quality_score')
    stock_dist_high = stock_metrics.get('distance_from_high')
    stock_sector = stock_row.iloc[0].get('sector', 'Unknown')

    # ---- Comparison Table ----
    _render_peer_table(
        selected_ticker, stock_roic, stock_de, stock_mcap, stock_eq,
        peers_df, currency_symbol,
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ---- Radar Chart ----
    radar_fig = _create_peer_radar_chart(
        selected_ticker, stock_roic, stock_de, stock_mcap, stock_eq, stock_dist_high,
        peers_df, stock_sector,
    )
    if radar_fig:
        st.plotly_chart(radar_fig, use_container_width=True)


def _render_peer_table(
    selected_ticker: str,
    stock_roic: Optional[float],
    stock_de: Optional[float],
    stock_mcap: Optional[float],
    stock_eq: Optional[float],
    peers_df: pd.DataFrame,
    currency_symbol: str,
) -> None:
    """Render the peer comparison table with the selected stock highlighted."""
    # Build rows: selected stock first, then peers
    rows = []

    # Selected stock row
    rows.append({
        'Ticker': selected_ticker,
        'Company': '(Selected)',
        'ROIC (%)': f"{stock_roic * 100:.1f}" if stock_roic is not None else "N/A",
        'D/E': f"{stock_de:.2f}" if stock_de is not None else "N/A",
        'Market Cap': _format_large_number(stock_mcap or 0, currency_symbol) if stock_mcap else "N/A",
        'EQ Score': f"{int(stock_eq)}" if stock_eq is not None else "N/A",
    })

    # Peer rows
    for _, peer in peers_df.iterrows():
        p_roic = peer.get('roic')
        p_de = peer.get('debt_to_equity')
        p_mcap = peer.get('market_cap')
        p_eq = peer.get('earnings_quality_score')
        rows.append({
            'Ticker': peer['ticker'],
            'Company': peer.get('company_name', peer['ticker']),
            'ROIC (%)': f"{p_roic * 100:.1f}" if p_roic is not None and not pd.isna(p_roic) else "N/A",
            'D/E': f"{p_de:.2f}" if p_de is not None and not pd.isna(p_de) else "N/A",
            'Market Cap': _format_large_number(p_mcap or 0, currency_symbol) if p_mcap and not pd.isna(p_mcap) else "N/A",
            'EQ Score': f"{int(p_eq)}" if p_eq is not None and not pd.isna(p_eq) else "N/A",
        })

    table_df = pd.DataFrame(rows)

    column_config = {
        'Ticker': st.column_config.TextColumn('Ticker', width='small'),
        'Company': st.column_config.TextColumn('Company', width='medium'),
        'ROIC (%)': st.column_config.TextColumn(
            'ROIC (%)', width='small',
            help="Return on Invested Capital — higher is better",
        ),
        'D/E': st.column_config.TextColumn(
            'D/E', width='small',
            help="Debt-to-Equity ratio — lower is better",
        ),
        'Market Cap': st.column_config.TextColumn('Market Cap', width='small'),
        'EQ Score': st.column_config.TextColumn(
            'EQ Score', width='small',
            help="Earnings Quality Score (0-100) — higher means more cash-backed earnings",
        ),
    }

    st.dataframe(
        table_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=min(400, len(table_df) * 38 + 50),
    )


def _create_peer_radar_chart(
    selected_ticker: str,
    stock_roic: Optional[float],
    stock_de: Optional[float],
    stock_mcap: Optional[float],
    stock_eq: Optional[float],
    stock_dist_high: Optional[float],
    peers_df: pd.DataFrame,
    sector_name: str,
) -> Optional[go.Figure]:
    """
    Create a radar/spider chart comparing the selected stock vs sector median.

    Axes (all normalized 0-100 within the peer+stock group):
    - ROIC: higher = outward
    - Capital Efficiency: 1/(1+D/E), lower debt = outward
    - Scale: log10(market_cap) normalized
    - Earnings Quality: raw 0-100
    - Price Discount: abs(distance_from_high), bigger drop = outward

    Args:
        selected_ticker: Ticker for display
        stock_*: Selected stock's metric values
        peers_df: Peer DataFrame with metrics
        sector_name: For chart title

    Returns:
        Plotly Figure or None
    """
    # Collect all values (stock + peers) for normalization
    all_roic = [stock_roic] + peers_df['roic'].tolist()
    all_de = [stock_de] + peers_df['debt_to_equity'].tolist()
    all_mcap = [stock_mcap] + peers_df['market_cap'].tolist()
    all_eq = [stock_eq] + peers_df['earnings_quality_score'].tolist()
    all_dist = [stock_dist_high] + peers_df['distance_from_high'].tolist()

    def _normalize(values: list) -> List[Optional[float]]:
        """Min-max normalize a list to 0-100, handling Nones."""
        numeric = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if len(numeric) < 2:
            return [50.0 if v is not None else None for v in values]
        lo, hi = min(numeric), max(numeric)
        if hi == lo:
            return [50.0 if v is not None else None for v in values]
        return [
            ((v - lo) / (hi - lo)) * 100 if v is not None and not (isinstance(v, float) and np.isnan(v)) else None
            for v in values
        ]

    # Compute capital efficiency: 1/(1+D/E) — higher is better
    all_cap_eff = [
        1.0 / (1.0 + de) if de is not None and not (isinstance(de, float) and np.isnan(de)) and de >= 0 else None
        for de in all_de
    ]

    # Log-scale market cap
    all_log_mcap = [
        np.log10(mc) if mc is not None and not (isinstance(mc, float) and np.isnan(mc)) and mc > 0 else None
        for mc in all_mcap
    ]

    # Absolute distance from high (bigger discount = better for value investor)
    all_abs_dist = [
        abs(d) if d is not None and not (isinstance(d, float) and np.isnan(d)) else None
        for d in all_dist
    ]

    # Normalize all axes
    norm_roic = _normalize(all_roic)
    norm_cap_eff = _normalize(all_cap_eff)
    norm_scale = _normalize(all_log_mcap)
    norm_eq = _normalize(all_eq)
    norm_discount = _normalize(all_abs_dist)

    # Extract stock values (index 0)
    stock_vals = [
        norm_roic[0], norm_cap_eff[0], norm_scale[0], norm_eq[0], norm_discount[0],
    ]

    # Compute sector median from peers (indices 1..N)
    def _median_of(normed: list) -> float:
        peer_vals = [v for v in normed[1:] if v is not None]
        return float(np.median(peer_vals)) if peer_vals else 50.0

    median_vals = [
        _median_of(norm_roic),
        _median_of(norm_cap_eff),
        _median_of(norm_scale),
        _median_of(norm_eq),
        _median_of(norm_discount),
    ]

    categories = ['ROIC', 'Capital Efficiency', 'Scale', 'Earnings Quality', 'Price Discount']

    # Replace None with 0 for plotting
    stock_plot = [v if v is not None else 0 for v in stock_vals]
    median_plot = [v if v is not None else 0 for v in median_vals]

    # Close the polygon (repeat first value)
    stock_plot_closed = stock_plot + [stock_plot[0]]
    median_plot_closed = median_plot + [median_plot[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    # Sector median polygon (dashed, gray fill)
    fig.add_trace(go.Scatterpolar(
        r=median_plot_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(136, 153, 166, 0.08)',
        line=dict(color=COLORS['text_muted'], width=1.5, dash='dash'),
        name=f'{sector_name} Median',
        hovertemplate='%{theta}: %{r:.0f}<extra>Sector Median</extra>',
    ))

    # Selected stock polygon (filled emerald)
    fig.add_trace(go.Scatterpolar(
        r=stock_plot_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.15)',
        line=dict(color=COLORS['accent_green'], width=2.5),
        name=selected_ticker,
        hovertemplate='%{theta}: %{r:.0f}<extra>' + selected_ticker + '</extra>',
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=COLORS['surface'],
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=True,
                tickfont=dict(size=9, color=COLORS['text_muted']),
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=COLORS['text_secondary']),
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
            ),
        ),
        paper_bgcolor=COLORS['surface'],
        font=dict(family=FONT_STACK, color=COLORS['text_secondary']),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(color=COLORS['text_secondary']),
            bgcolor='rgba(0,0,0,0)',
        ),
        height=420,
        margin=dict(l=60, r=60, t=40, b=60),
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
