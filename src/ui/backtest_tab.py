"""
Backtest tab module.
Renders survivorship bias disclaimer, period selector, performance chart,
summary metrics, and per-stock return table.
"""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.quant.backtest import run_backtest
from src.utils.config import (
    get_currency_symbol,
    BENCHMARK_TICKERS,
    CHART_COLOR_POSITIVE,
    CHART_COLOR_MARKET,
)
from src.ui.styles import (
    get_plotly_theme,
    COLORS,
    FONT_STACK,
    section_header,
    metric_card,
)


# ==================== MAIN ENTRY POINT ====================

def render_backtest_section(
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
) -> None:
    """
    Main entry point for the Backtest tab.

    Args:
        results_df_raw: Raw screening results DataFrame
        screening_config: User config (index, etc.)
    """
    if results_df_raw.empty:
        st.info("No stocks passed filters. Relax thresholds to run a backtest.")
        return

    if len(results_df_raw) < 2:
        st.info("At least 2 stocks are needed for backtesting. Relax filter thresholds.")
        return

    index = screening_config["index"]

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ==================== SURVIVORSHIP BIAS DISCLAIMER ====================
    _render_disclaimer()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ==================== PERIOD SELECTOR ====================
    period = st.radio(
        "Lookback Period",
        options=["1Y", "3Y", "5Y"],
        index=0,
        horizontal=True,
        help=(
            "How far back to test the portfolio. "
            "Uses current filtered stocks — does NOT use historical fundamentals."
        ),
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ==================== RUN BACKTEST ====================
    with st.spinner("Computing backtest..."):
        result = run_backtest(
            results_df=results_df_raw,
            index=index,
            period=period,
        )

    if result is None:
        st.warning(
            "Insufficient historical price data for backtesting. "
            "At least 2 stocks need price history for the selected period."
        )
        return

    metrics = result["metrics"]
    stock_details = result["stock_details"]
    period_label = result["period_label"]

    # ==================== METRICS CARDS ====================
    st.markdown(
        section_header(f"Performance Summary ({period_label})"),
        unsafe_allow_html=True,
    )
    _render_metrics_cards(metrics)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ==================== PERFORMANCE CHART ====================
    st.markdown(
        section_header("Portfolio vs Benchmark"),
        unsafe_allow_html=True,
    )
    chart = _create_performance_chart(
        portfolio_cumulative=result["portfolio_cumulative"],
        benchmark_cumulative=result["benchmark_cumulative"],
        index=index,
    )
    if chart:
        st.plotly_chart(chart, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ==================== PER-STOCK TABLE ====================
    st.markdown(
        section_header(f"Individual Stock Returns ({period_label})"),
        unsafe_allow_html=True,
    )
    _render_stock_table(stock_details, metrics["benchmark_return"])


# ==================== DISCLAIMER ====================

def _render_disclaimer() -> None:
    """Render survivorship bias warning card."""
    st.markdown(
        f"""<div style="
            background: {COLORS['surface']};
            border: 1px solid {COLORS['accent_amber']};
            border-left: 4px solid {COLORS['accent_amber']};
            border-radius: 10px;
            padding: 16px 20px;
            color: {COLORS['text_secondary']};
            font-size: 0.88rem;
            line-height: 1.7;
        ">
            <strong style="color:{COLORS['accent_amber']};">Survivorship Bias Warning</strong><br>
            This backtest uses <strong>current</strong> screening criteria applied to
            <strong>today's</strong> stock universe. Companies that failed, were delisted,
            or were acquired in the past are excluded — inflating historical returns.
            yfinance does not provide historical fundamentals, so we cannot reconstruct
            what the screener would have selected N years ago.
            <strong>Treat results as directional, not predictive.</strong>
        </div>""",
        unsafe_allow_html=True,
    )


# ==================== METRICS CARDS ====================

def _render_metrics_cards(metrics: Dict[str, float]) -> None:
    """Render 5 backtest metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_ret = metrics["total_return"]
    ann_ret = metrics["annualized_return"]
    alpha = metrics["alpha"]
    max_dd = metrics["max_drawdown"]
    win_rate = metrics.get("win_rate", 0.0)

    with col1:
        accent = "green" if total_ret > 0 else "red"
        st.markdown(
            metric_card(
                label="Total Return",
                value=f"{total_ret * 100:+.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        accent = "green" if ann_ret > 0 else "red"
        st.markdown(
            metric_card(
                label="Annualized Return",
                value=f"{ann_ret * 100:+.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col3:
        accent = "green" if alpha > 0 else "red"
        st.markdown(
            metric_card(
                label="Alpha vs Benchmark",
                value=f"{alpha * 100:+.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col4:
        accent = "green" if max_dd > -0.10 else ("amber" if max_dd > -0.20 else "red")
        st.markdown(
            metric_card(
                label="Max Drawdown",
                value=f"{max_dd * 100:.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col5:
        accent = "green" if win_rate >= 0.6 else ("amber" if win_rate >= 0.4 else "red")
        st.markdown(
            metric_card(
                label="Win Rate vs Benchmark",
                value=f"{win_rate * 100:.0f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )


# ==================== PERFORMANCE CHART ====================

def _create_performance_chart(
    portfolio_cumulative: pd.Series,
    benchmark_cumulative: Optional[pd.Series],
    index: str,
) -> Optional[go.Figure]:
    """Create portfolio vs benchmark cumulative return chart."""
    if portfolio_cumulative is None or portfolio_cumulative.empty:
        return None

    fig = go.Figure()

    # Portfolio line
    fig.add_trace(
        go.Scatter(
            x=portfolio_cumulative.index,
            y=(portfolio_cumulative - 1) * 100,  # convert to %
            mode="lines",
            name="Screened Portfolio (EW)",
            line=dict(color=CHART_COLOR_POSITIVE, width=2.5),
            hovertemplate="Date: %{x|%b %d, %Y}<br>Return: %{y:+.1f}%<extra></extra>",
        )
    )

    # Benchmark line
    if benchmark_cumulative is not None and not benchmark_cumulative.empty:
        benchmark_name = BENCHMARK_TICKERS.get(index, "Benchmark")
        index_labels = {"NIFTY100": "Nifty 50", "SP500": "S&P 500", "FTSE100": "FTSE 100"}
        label = index_labels.get(index, benchmark_name)

        fig.add_trace(
            go.Scatter(
                x=benchmark_cumulative.index,
                y=(benchmark_cumulative - 1) * 100,
                mode="lines",
                name=label,
                line=dict(color=CHART_COLOR_MARKET, width=2, dash="dot"),
                hovertemplate="Date: %{x|%b %d, %Y}<br>Return: %{y:+.1f}%<extra></extra>",
            )
        )

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["text_muted"], line_width=1)

    theme = get_plotly_theme()
    fig.update_layout(**theme)
    fig.update_layout(
        height=420,
        yaxis_title="Cumulative Return (%)",
        xaxis_title="",
        margin=dict(t=40, b=40, l=60, r=20),
        hovermode="x unified",
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11, color=COLORS["text_secondary"]),
        ),
    )

    return fig


# ==================== STOCK TABLE ====================

def _render_stock_table(
    stock_details: list,
    benchmark_return: float,
) -> None:
    """Render per-stock return table."""
    if not stock_details:
        return

    rows = []
    for s in stock_details:
        rows.append({
            "Ticker": s["ticker"],
            "Company": s["company_name"],
            "Total Return": s["total_return"],
            "Beat Benchmark": "Yes" if s["beat_benchmark"] else "No",
        })

    df = pd.DataFrame(rows)

    column_config = {
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Company": st.column_config.TextColumn("Company", width="medium"),
        "Total Return": st.column_config.NumberColumn(
            "Total Return",
            format="%+.1f%%",
            width="small",
            help="Total cumulative return over the backtest period",
        ),
        "Beat Benchmark": st.column_config.TextColumn(
            "Beat Benchmark",
            width="small",
            help=f"Whether the stock outperformed the benchmark ({benchmark_return * 100:+.1f}%)",
        ),
    }

    # Convert to percentage for display
    df["Total Return"] = df["Total Return"] * 100

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=min(400, 40 + len(df) * 35),
    )
