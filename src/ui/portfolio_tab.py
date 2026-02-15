"""
Portfolio Builder tab module.
Renders allocation inputs, allocation table, pie chart, portfolio metrics,
and correlation heatmap.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.quant.portfolio import build_portfolio
from src.utils.config import (
    get_currency_symbol,
    PORTFOLIO_DEFAULT_AMOUNT,
    PORTFOLIO_CONCENTRATION_LIMITS,
)
from src.ui.styles import (
    get_plotly_theme,
    COLORS,
    FONT_STACK,
    section_header,
    metric_card,
)


# ==================== MAIN ENTRY POINT ====================

def render_portfolio_section(
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
    stocks_data: Optional[Dict[str, Optional[dict]]],
) -> None:
    """
    Main entry point for the Portfolio Builder tab.

    Args:
        results_df_raw: Raw screening results DataFrame
        screening_config: User config (index, ticker_limit, etc.)
        stocks_data: Cached deep data dict from screening run
    """
    if stocks_data is None:
        st.info("Run screening first to build a portfolio.")
        return

    if results_df_raw.empty:
        st.info("No stocks passed filters. Relax thresholds to build a portfolio.")
        return

    if len(results_df_raw) < 2:
        st.info("At least 2 stocks are needed to build a portfolio. Relax filter thresholds.")
        return

    index = screening_config["index"]
    currency_symbol = get_currency_symbol(index)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ==================== PORTFOLIO INPUTS ====================
    st.markdown(section_header("Portfolio Configuration"), unsafe_allow_html=True)

    col_amt, col_risk, col_method = st.columns(3)

    with col_amt:
        investment_amount = st.number_input(
            "Investment Amount",
            min_value=1000,
            max_value=100_000_000,
            value=PORTFOLIO_DEFAULT_AMOUNT,
            step=10000,
            help=f"Total amount to invest ({currency_symbol})",
        )

    with col_risk:
        risk_tolerance = st.radio(
            "Risk Tolerance",
            options=["Conservative", "Moderate", "Aggressive"],
            index=1,
            help=(
                f"Conservative: max {PORTFOLIO_CONCENTRATION_LIMITS['Conservative']:.0%}/stock. "
                f"Moderate: max {PORTFOLIO_CONCENTRATION_LIMITS['Moderate']:.0%}/stock. "
                f"Aggressive: max {PORTFOLIO_CONCENTRATION_LIMITS['Aggressive']:.0%}/stock."
            ),
            horizontal=True,
        )

    with col_method:
        method = st.selectbox(
            "Allocation Method",
            options=["Equal Weight", "Inverse Volatility", "Max Diversification"],
            index=0,
            help=(
                "Equal Weight: uniform 1/N allocation. "
                "Inverse Volatility: lower-vol stocks get higher weight. "
                "Max Diversification: risk-parity variant maximizing diversification ratio."
            ),
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ==================== BUILD PORTFOLIO ====================
    with st.spinner("Computing portfolio allocation..."):
        result = build_portfolio(
            results_df=results_df_raw,
            stocks_data=stocks_data,
            index=index,
            investment_amount=float(investment_amount),
            risk_tolerance=risk_tolerance,
            method=method,
        )

    if result is None:
        st.warning(
            "Insufficient price data to build portfolio. "
            "At least 2 stocks need 1 year of trading history."
        )
        return

    allocations = result["allocations"]
    metrics = result["metrics"]
    corr_matrix = result["correlation_matrix"]

    # ==================== PORTFOLIO METRICS ====================
    st.markdown(section_header("Portfolio Metrics"), unsafe_allow_html=True)
    _render_metrics_cards(metrics)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ==================== ALLOCATION TABLE + PIE CHART ====================
    col_table, col_pie = st.columns([3, 2])

    with col_table:
        st.markdown(section_header("Allocation Table"), unsafe_allow_html=True)
        _render_allocation_table(allocations, currency_symbol)

    with col_pie:
        st.markdown(section_header("Weight Distribution"), unsafe_allow_html=True)
        pie_fig = _create_allocation_pie(allocations)
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ==================== CORRELATION HEATMAP ====================
    st.markdown(section_header("Correlation Matrix"), unsafe_allow_html=True)
    heatmap_fig = _create_correlation_heatmap(corr_matrix)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)


# ==================== METRICS CARDS ====================

def _render_metrics_cards(metrics: Dict[str, float]) -> None:
    """Render 4 portfolio metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    exp_ret = metrics["expected_return"]
    vol = metrics["volatility"]
    sharpe = metrics["sharpe_ratio"]
    max_dd = metrics["max_drawdown"]

    with col1:
        accent = "green" if exp_ret > 0 else "red"
        st.markdown(
            metric_card(
                label="Expected Return (1Y)",
                value=f"{exp_ret * 100:.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        accent = "green" if vol < 0.20 else ("amber" if vol < 0.30 else "red")
        st.markdown(
            metric_card(
                label="Portfolio Volatility",
                value=f"{vol * 100:.1f}%",
                accent=accent,
            ),
            unsafe_allow_html=True,
        )

    with col3:
        accent = "green" if sharpe > 1.0 else ("amber" if sharpe > 0.5 else "red")
        st.markdown(
            metric_card(
                label="Sharpe Ratio",
                value=f"{sharpe:.2f}",
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


# ==================== ALLOCATION TABLE ====================

def _render_allocation_table(
    allocations: list,
    currency_symbol: str,
) -> None:
    """Render allocation details as a Streamlit DataFrame."""
    rows = []
    for alloc in allocations:
        roic = alloc["roic"]
        vs = alloc["value_score"]
        rows.append({
            "Ticker": alloc["ticker"],
            "Company": alloc["company_name"],
            "Weight": alloc["weight"],
            "Amount": alloc["amount"],
            "ROIC": roic,
            "Value Score": vs,
        })

    df = pd.DataFrame(rows)

    column_config = {
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Company": st.column_config.TextColumn("Company", width="medium"),
        "Weight": st.column_config.NumberColumn(
            "Weight %",
            format="%.1f%%",
            width="small",
            help="Portfolio weight as percentage",
        ),
        "Amount": st.column_config.NumberColumn(
            f"Amount ({currency_symbol})",
            format=f"{currency_symbol}%,.0f",
            width="small",
        ),
        "ROIC": st.column_config.NumberColumn(
            "ROIC",
            format="%.1f%%",
            width="small",
            help="Return on Invested Capital",
        ),
        "Value Score": st.column_config.NumberColumn(
            "Score",
            format="%.3f",
            width="small",
            help="Value Score (0-1)",
        ),
    }

    # Convert weight to percentage for display
    df["Weight"] = df["Weight"] * 100
    # Convert ROIC to percentage for display
    df["ROIC"] = df["ROIC"].apply(lambda x: x * 100 if pd.notna(x) else None)

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=min(400, 40 + len(df) * 35),
    )

    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Allocation (CSV)",
        data=csv,
        file_name="portfolio_allocation.csv",
        mime="text/csv",
    )


# ==================== PIE CHART ====================

def _create_allocation_pie(allocations: list) -> Optional[go.Figure]:
    """Create a Plotly pie chart of portfolio weights."""
    if not allocations:
        return None

    tickers = [a["ticker"] for a in allocations]
    weights = [a["weight"] * 100 for a in allocations]

    # Color palette — cycle through accent colors
    palette = [
        COLORS["accent_green"],
        COLORS["accent_blue"],
        COLORS["accent_amber"],
        COLORS["accent_purple"],
        COLORS["accent_red"],
        "#34D399",  # light emerald
        "#818CF8",  # light indigo
        "#FBBF24",  # light amber
        "#A78BFA",  # light violet
        "#FB7185",  # light rose
    ]
    colors = [palette[i % len(palette)] for i in range(len(tickers))]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=tickers,
                values=weights,
                hole=0.45,
                marker=dict(colors=colors, line=dict(color=COLORS["surface"], width=2)),
                textinfo="label+percent",
                textfont=dict(size=11, family=FONT_STACK, color=COLORS["text_primary"]),
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>",
            )
        ]
    )

    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        showlegend=False,
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
    )

    return fig


# ==================== CORRELATION HEATMAP ====================

def _create_correlation_heatmap(corr_matrix: pd.DataFrame) -> Optional[go.Figure]:
    """Create a Plotly heatmap of stock return correlations."""
    if corr_matrix is None or corr_matrix.empty:
        return None

    tickers = corr_matrix.columns.tolist()
    values = corr_matrix.values

    # Colorscale: blue (negative) -> surface (zero) -> red (positive)
    colorscale = [
        [0.0, COLORS["accent_blue"]],
        [0.5, COLORS["surface_elevated"]],
        [1.0, COLORS["accent_red"]],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=values,
            x=tickers,
            y=tickers,
            colorscale=colorscale,
            zmin=-1,
            zmax=1,
            text=np.round(values, 2),
            texttemplate="%{text}",
            textfont=dict(size=10, color=COLORS["text_primary"]),
            hovertemplate="%{x} vs %{y}: %{z:.2f}<extra></extra>",
            colorbar=dict(
                title=dict(
                    text="Corr",
                    font=dict(color=COLORS["text_secondary"], size=11),
                ),
                tickfont=dict(color=COLORS["text_secondary"], size=10),
                thickness=12,
                len=0.7,
            ),
        )
    )

    theme = get_plotly_theme()
    fig.update_layout(**theme)
    fig.update_layout(
        height=max(300, 50 + len(tickers) * 30),
        margin=dict(t=20, b=40, l=60, r=20),
    )
    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
    )
    fig.update_yaxes(
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
        autorange="reversed",
    )

    return fig
