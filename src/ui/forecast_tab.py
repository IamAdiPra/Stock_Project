"""
Forecast & Valuation tab module.
Renders summary table, per-stock price projections, scenario charts,
model breakdowns, and risk dashboard.
"""

from typing import Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.fetcher import fetch_historical_prices, normalize_ticker
from src.quant.forecast import (
    calculate_composite_forecast,
    batch_calculate_forecasts,
    HORIZON_LABELS,
)
from src.utils.config import (
    get_currency_symbol,
    get_terminal_growth_rate,
    get_equity_risk_premium,
    RISK_FREE_RATES,
    MARKET_ANNUAL_RETURNS,
    CHART_COLOR_BULL,
    CHART_COLOR_BASE,
    CHART_COLOR_BEAR,
    CHART_COLOR_MARKET,
)
from src.ui.styles import (
    get_plotly_theme,
    get_plotly_theme_with_legend_top,
    COLORS,
    FONT_STACK,
    section_header,
    metric_card,
    model_card,
)


# ==================== MAIN ENTRY POINT ====================

def render_forecast_section(
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
    stocks_data: Optional[Dict[str, Optional[dict]]],
) -> None:
    """
    Main entry point for the Forecast & Valuation tab.

    Args:
        results_df_raw: Raw screening results DataFrame
        screening_config: User config (index, ticker_limit, etc.)
        stocks_data: Cached deep data dict from screening run
    """
    if stocks_data is None:
        st.info("Run screening first to enable forecasting.")
        return

    if results_df_raw.empty:
        st.info("No stocks passed filters. Relax thresholds to generate forecasts.")
        return

    index = screening_config.get('index', 'SP500')
    currency_symbol = get_currency_symbol(index)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Compute forecasts (cached in session state)
    if (st.session_state.get('forecast_df') is None
            or st.session_state.get('forecast_index') != index
            or st.session_state.get('forecast_tickers')
            != list(results_df_raw['ticker'])):
        with st.spinner("Computing forecasts for all filtered stocks..."):
            forecast_df = batch_calculate_forecasts(
                results_df_raw, stocks_data, index=index
            )

            # Also compute per-stock detailed forecasts
            exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
            exchange = exchange_map.get(index)
            forecast_data: Dict[str, Dict[str, Any]] = {}

            for _, row in results_df_raw.iterrows():
                ticker = row['ticker']
                data = stocks_data.get(ticker)
                if data is None:
                    continue
                norm_ticker = data.get(
                    'normalized_ticker',
                    normalize_ticker(ticker, exchange or ""),
                )
                hist_prices = fetch_historical_prices(norm_ticker, period="1y")
                result = calculate_composite_forecast(
                    data=data,
                    income_statement=data.get('income_statement'),
                    balance_sheet=data.get('balance_sheet'),
                    cashflow_statement=data.get('cashflow_statement'),
                    historical_prices=hist_prices,
                    index=index,
                )
                if result is not None:
                    forecast_data[ticker] = result

            st.session_state.forecast_df = forecast_df
            st.session_state.forecast_data = forecast_data
            st.session_state.forecast_index = index
            st.session_state.forecast_tickers = list(results_df_raw['ticker'])

    forecast_df = st.session_state.forecast_df
    forecast_data = st.session_state.forecast_data

    if forecast_df is None or forecast_df.empty:
        st.warning("Could not generate forecasts — insufficient financial data for filtered stocks.")
        return

    # ---- Summary Table ----
    st.markdown(section_header("Forecast Summary — All Filtered Stocks"), unsafe_allow_html=True)
    st.caption(
        "Base-case projections using a composite of DCF, Earnings Multiple, and ROIC Growth models. "
        "Alpha = projected stock return minus expected market return."
    )
    render_forecast_summary_table(forecast_df, currency_symbol)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Per-Stock Detailed Forecast ----
    st.markdown(section_header("Detailed Stock Forecast"), unsafe_allow_html=True)

    options = []
    ticker_map = {}
    for ticker in forecast_data:
        fc = forecast_data[ticker]
        name = fc.get('company_name', ticker)
        label = f"{ticker} - {name}"
        options.append(label)
        ticker_map[label] = ticker

    if not options:
        st.info("No detailed forecasts available.")
        return

    selected_label = st.selectbox(
        "Select a stock for detailed forecast",
        options=options,
        help="Choose from stocks with successful forecast models",
    )

    if not selected_label:
        return

    selected_ticker = ticker_map[selected_label]
    forecast = forecast_data.get(selected_ticker)

    if forecast is None:
        st.warning(f"No forecast data for {selected_ticker}.")
        return

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Valuation Summary Cards
    render_valuation_summary_card(forecast, currency_symbol)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Price Target Chart (Bull / Base / Bear)
    st.markdown(section_header("5-Year Price Projection"), unsafe_allow_html=True)
    terminal_pct = get_terminal_growth_rate(index) * 100
    st.caption(
        f"Bull = historical growth maintained | Base = growth decays toward GDP ({terminal_pct:.0f}%) | "
        "Bear = 50% of historical growth. Market line = long-term index average return."
    )
    fig = create_price_target_chart(forecast, currency_symbol)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Model Breakdown
    st.markdown(section_header("Model Breakdown"), unsafe_allow_html=True)
    render_model_breakdown(forecast, currency_symbol, index=index)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Risk Dashboard
    st.markdown(section_header("Risk Assessment"), unsafe_allow_html=True)
    render_risk_dashboard(forecast)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Assumptions Table
    render_assumptions_table(forecast, index)


# ==================== SUMMARY TABLE ====================

def render_forecast_summary_table(
    forecast_df: pd.DataFrame,
    currency_symbol: str,
) -> None:
    """Render the top-level summary table with all stocks' forecast data."""
    display_df = forecast_df.copy()

    # Format columns
    fmt_price = lambda x: f"{currency_symbol}{x:,.2f}" if pd.notna(x) else "N/A"
    fmt_pct = lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
    fmt_float = lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"

    column_config = {
        "ticker": st.column_config.TextColumn("Ticker", width="small"),
        "company_name": st.column_config.TextColumn("Company", width="medium"),
        "current_price": st.column_config.TextColumn(
            "Current Price",
            help="Current market price",
        ),
        "dcf_fair_value": st.column_config.TextColumn(
            "DCF Fair Value",
            help="Intrinsic value per share from Discounted Cash Flow model",
        ),
        "margin_of_safety_pct": st.column_config.TextColumn(
            "Margin of Safety",
            help="(DCF Value - Price) / DCF Value. Positive = undervalued.",
        ),
        "target_6mo": st.column_config.TextColumn("6mo Target"),
        "target_1y": st.column_config.TextColumn("1Y Target"),
        "target_2y": st.column_config.TextColumn("2Y Target"),
        "target_5y": st.column_config.TextColumn("5Y Target"),
        "return_1y_pct": st.column_config.TextColumn(
            "1Y Return",
            help="Projected 1-year return from composite model (base case)",
        ),
        "market_return_1y": st.column_config.TextColumn(
            "Market 1Y",
            help="Expected 1-year return from market benchmark",
        ),
        "alpha_1y": st.column_config.TextColumn(
            "Alpha (1Y)",
            help="Excess return over market = Stock Return - Market Return",
        ),
        "beta": st.column_config.TextColumn(
            "Beta",
            help="Systematic risk. 1.0 = market average. >1 = more volatile.",
        ),
        "volatility": st.column_config.TextColumn(
            "Volatility",
            help="Annualized standard deviation of daily returns",
        ),
        "models_used": st.column_config.NumberColumn(
            "Models",
            help="Number of valuation models that produced results (max 3)",
        ),
    }

    # Apply formatting
    for col in ['current_price', 'dcf_fair_value', 'target_6mo',
                'target_1y', 'target_2y', 'target_5y']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_price)

    for col in ['margin_of_safety_pct', 'return_1y_pct', 'market_return_1y', 'alpha_1y']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_pct)

    for col in ['beta']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_float)

    if 'volatility' in display_df.columns:
        display_df['volatility'] = display_df['volatility'].apply(
            lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
        )

    display_columns = [c for c in column_config if c in display_df.columns]

    st.dataframe(
        display_df[display_columns],
        column_config={k: v for k, v in column_config.items() if k in display_columns},
        use_container_width=True,
        hide_index=True,
        height=min(400, 50 + len(display_df) * 40),
    )

    # Download CSV
    csv = forecast_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Forecast Data (CSV)",
        data=csv,
        file_name="stock_forecasts.csv",
        mime="text/csv",
    )


# ==================== VALUATION SUMMARY CARD ====================

def render_valuation_summary_card(
    forecast: Dict[str, Any],
    currency_symbol: str,
) -> None:
    """Render valuation summary as styled metric cards."""
    current = forecast["current_price"]
    dcf_val = forecast.get("dcf_intrinsic_value")
    margin = forecast.get("margin_of_safety_pct")

    # Get earnings-based value from earnings multiple model (base)
    earnings_val = None
    em_base = forecast.get("earnings_multiple", {}).get("base")
    if em_base is not None:
        earnings_val = em_base.get("horizon_prices", {}).get("5 Years")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            metric_card(
                label="Current Price",
                value=f"{currency_symbol}{current:,.2f}",
                accent="blue",
            ),
            unsafe_allow_html=True
        )

    with col2:
        if dcf_val is not None:
            delta_pct = (dcf_val - current) / current * 100
            st.markdown(
                metric_card(
                    label="DCF Intrinsic Value",
                    value=f"{currency_symbol}{dcf_val:,.2f}",
                    delta=f"{delta_pct:+.1f}% vs price",
                    accent="green" if delta_pct > 0 else "red",
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                metric_card(label="DCF Intrinsic Value", value="N/A", accent="blue"),
                unsafe_allow_html=True
            )

    with col3:
        if earnings_val is not None:
            delta_pct = (earnings_val - current) / current * 100
            st.markdown(
                metric_card(
                    label="Earnings Model (5Y)",
                    value=f"{currency_symbol}{earnings_val:,.2f}",
                    delta=f"{delta_pct:+.1f}% vs price",
                    accent="green" if delta_pct > 0 else "red",
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                metric_card(label="Earnings Model (5Y)", value="N/A", accent="blue"),
                unsafe_allow_html=True
            )

    with col4:
        if margin is not None:
            st.markdown(
                metric_card(
                    label="Margin of Safety",
                    value=f"{margin:+.1f}%",
                    delta="Undervalued" if margin > 0 else "Overvalued",
                    accent="green" if margin > 0 else "red",
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                metric_card(label="Margin of Safety", value="N/A", accent="blue"),
                unsafe_allow_html=True
            )


# ==================== PRICE TARGET CHART ====================

def create_price_target_chart(
    forecast: Dict[str, Any],
    currency_symbol: str,
) -> Optional[go.Figure]:
    """
    Create line chart showing bull/base/bear price paths + market benchmark.

    X-axis: Now, 6 Months, 1 Year, 2 Years, 5 Years
    Lines: Bull (green dashed), Base (blue solid), Bear (red dashed), Market (purple dotted)
    """
    composite = forecast.get("composite_horizon_prices")
    market = forecast.get("market_benchmark")
    current = forecast["current_price"]

    if composite is None:
        return None

    x_labels = ["Now"] + HORIZON_LABELS

    fig = go.Figure()

    # Plot each scenario
    scenario_styles = [
        ("bull", "Bull Case", CHART_COLOR_BULL, "dash"),
        ("base", "Base Case", CHART_COLOR_BASE, "solid"),
        ("bear", "Bear Case", CHART_COLOR_BEAR, "dash"),
    ]

    for sc_key, sc_name, color, dash in scenario_styles:
        if sc_key not in composite:
            continue
        prices = composite[sc_key]
        y_values = [current]
        for label in HORIZON_LABELS:
            y_values.append(prices.get(label, current))

        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode='lines+markers',
            name=sc_name,
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=7),
            hovertemplate=f"{sc_name}: {currency_symbol}%{{y:,.2f}}<extra></extra>",
        ))

    # Market benchmark line
    if market is not None:
        market_y = [current]
        for label in HORIZON_LABELS:
            market_y.append(market.get(label, current))

        fig.add_trace(go.Scatter(
            x=x_labels,
            y=market_y,
            mode='lines+markers',
            name="Market Benchmark",
            line=dict(color=CHART_COLOR_MARKET, width=2, dash="dot"),
            marker=dict(size=5, symbol="diamond"),
            hovertemplate=f"Market: {currency_symbol}%{{y:,.2f}}<extra></extra>",
        ))

    # Current price reference line
    fig.add_hline(
        y=current,
        line_dash="dot",
        line_color=COLORS['text_muted'],
        annotation_text=f"Current: {currency_symbol}{current:,.2f}",
        annotation_position="top left",
        annotation_font_size=10,
        annotation_font_color=COLORS['text_secondary'],
    )

    ticker = forecast.get("ticker", "")

    # Apply theme
    theme = get_plotly_theme_with_legend_top()
    fig.update_layout(**theme)

    fig.update_layout(
        title=dict(
            text=f"{ticker} — 5-Year Price Projection (Bull / Base / Bear)",
        ),
        yaxis_title=f"Projected Price ({currency_symbol})",
        xaxis_title="Time Horizon",
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode='x unified',
    )

    return fig


# ==================== MODEL BREAKDOWN ====================

def render_model_breakdown(
    forecast: Dict[str, Any],
    currency_symbol: str,
    index: str = "SP500",
) -> None:
    """Show individual model outputs in styled card containers."""
    col1, col2, col3 = st.columns(3)

    # DCF Model
    with col1:
        dcf_base = forecast.get("dcf", {}).get("base")
        if dcf_base is not None:
            intrinsic = dcf_base['intrinsic_value_per_share']
            terminal_g = get_terminal_growth_rate(index)
            items = (
                f"WACC: <strong>{dcf_base['wacc']*100:.1f}%</strong><br>"
                f"FCF CAGR: <strong>{dcf_base['fcf_cagr']*100:.1f}%</strong><br>"
                f"Terminal Growth: <strong>{terminal_g*100:.0f}%</strong><br>"
                f"Intrinsic Value: <strong>{currency_symbol}{intrinsic:,.2f}</strong><br>"
            )
            for label in ["1 Year", "5 Years"]:
                price = dcf_base["horizon_prices"].get(label)
                if price is not None:
                    items += f"{label} Target: {currency_symbol}{price:,.2f}<br>"
            st.markdown(model_card("DCF Model", items, accent="green"), unsafe_allow_html=True)
        else:
            st.markdown(
                model_card("DCF Model", "<em>Insufficient data for DCF model.</em>", accent="green"),
                unsafe_allow_html=True
            )

    # Earnings Multiple Model
    with col2:
        em_base = forecast.get("earnings_multiple", {}).get("base")
        if em_base is not None:
            items = (
                f"EPS CAGR: <strong>{em_base['eps_cagr']*100:.1f}%</strong><br>"
                f"Target P/E: <strong>{em_base['target_pe']:.1f}x</strong><br>"
                f"Current EPS: <strong>{currency_symbol}{em_base['current_eps']:,.2f}</strong><br>"
            )
            for label in ["1 Year", "5 Years"]:
                price = em_base["horizon_prices"].get(label)
                if price is not None:
                    items += f"{label} Target: {currency_symbol}{price:,.2f}<br>"
            st.markdown(model_card("Earnings Multiple Model", items, accent="blue"), unsafe_allow_html=True)
        else:
            st.markdown(
                model_card("Earnings Multiple Model", "<em>Insufficient data for Earnings model.</em>", accent="blue"),
                unsafe_allow_html=True
            )

    # ROIC Growth Model
    with col3:
        roic_base = forecast.get("roic_growth", {}).get("base")
        if roic_base is not None:
            items = (
                f"ROIC: <strong>{roic_base['roic']*100:.1f}%</strong><br>"
                f"Reinvestment Rate: <strong>{roic_base['reinvestment_rate']*100:.0f}%</strong><br>"
                f"Sustainable Growth: <strong>{roic_base['sustainable_growth']*100:.1f}%</strong><br>"
            )
            for label in ["1 Year", "5 Years"]:
                price = roic_base["horizon_prices"].get(label)
                if price is not None:
                    items += f"{label} Target: {currency_symbol}{price:,.2f}<br>"
            st.markdown(model_card("ROIC Growth Model", items, accent="purple"), unsafe_allow_html=True)
        else:
            st.markdown(
                model_card("ROIC Growth Model", "<em>Insufficient data for ROIC model.</em>", accent="purple"),
                unsafe_allow_html=True
            )

    # Models used indicator
    models_used = forecast.get("models_used", 0)
    if models_used < 3:
        st.warning(f"Only {models_used} of 3 models produced results. Forecast reliability is reduced.")


# ==================== RISK DASHBOARD ====================

def render_risk_dashboard(forecast: Dict[str, Any]) -> None:
    """Render risk metrics as styled metric cards."""
    risk = forecast.get("risk")
    if risk is None:
        st.info("Risk metrics unavailable.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        beta = risk.get("beta")
        if beta is not None:
            risk_level = "Low" if beta < 0.8 else ("High" if beta > 1.3 else "Medium")
            accent = "green" if beta < 0.8 else ("red" if beta > 1.3 else "amber")
            st.markdown(
                metric_card(
                    label="Beta",
                    value=f"{beta:.2f}",
                    delta=risk_level,
                    accent=accent,
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(metric_card(label="Beta", value="N/A", accent="blue"), unsafe_allow_html=True)

    with col2:
        vol = risk.get("annual_volatility")
        if vol is not None:
            accent = "green" if vol < 0.20 else ("red" if vol > 0.40 else "amber")
            st.markdown(
                metric_card(
                    label="Annual Volatility",
                    value=f"{vol*100:.1f}%",
                    accent=accent,
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(metric_card(label="Annual Volatility", value="N/A", accent="blue"), unsafe_allow_html=True)

    with col3:
        mdd = risk.get("max_drawdown_pct")
        if mdd is not None:
            accent = "green" if mdd > -15 else ("red" if mdd < -30 else "amber")
            st.markdown(
                metric_card(
                    label="Max Drawdown (1Y)",
                    value=f"{mdd:.1f}%",
                    accent=accent,
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(metric_card(label="Max Drawdown (1Y)", value="N/A", accent="blue"), unsafe_allow_html=True)

    with col4:
        sharpe = risk.get("sharpe_ratio")
        if sharpe is not None:
            quality = "Excellent" if sharpe > 1.0 else ("Good" if sharpe > 0.5 else "Poor")
            accent = "green" if sharpe > 1.0 else ("amber" if sharpe > 0.5 else "red")
            st.markdown(
                metric_card(
                    label="Sharpe Ratio",
                    value=f"{sharpe:.2f}",
                    delta=quality,
                    accent=accent,
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(metric_card(label="Sharpe Ratio", value="N/A", accent="blue"), unsafe_allow_html=True)


# ==================== ASSUMPTIONS TABLE ====================

def render_assumptions_table(
    forecast: Dict[str, Any],
    index: str,
) -> None:
    """Show all model assumptions in a clean table."""
    st.markdown(section_header("Model Assumptions"), unsafe_allow_html=True)
    st.caption(
        "All models use publicly available financial data. "
        "Projections are not investment advice — they illustrate what valuations "
        "look like under different growth assumptions."
    )

    risk_free = RISK_FREE_RATES.get(index, 0.045)
    erp = get_equity_risk_premium(index)
    terminal_growth = get_terminal_growth_rate(index)
    market_return = MARKET_ANNUAL_RETURNS.get(index, 0.10)

    assumptions: list = [
        ("Risk-Free Rate", f"{risk_free*100:.1f}%"),
        ("Equity Risk Premium", f"{erp*100:.1f}%"),
        ("Terminal Growth Rate", f"{terminal_growth*100:.1f}%"),
        ("Market Annual Return", f"{market_return*100:.1f}%"),
    ]

    # Add model-specific assumptions
    dcf_base = forecast.get("dcf", {}).get("base")
    if dcf_base is not None:
        assumptions.append(("WACC (DCF)", f"{dcf_base['wacc']*100:.1f}%"))
        assumptions.append(("FCF CAGR (Historical)", f"{dcf_base['fcf_cagr']*100:.1f}%"))

    em_base = forecast.get("earnings_multiple", {}).get("base")
    if em_base is not None:
        assumptions.append(("EPS CAGR (Historical)", f"{em_base['eps_cagr']*100:.1f}%"))
        assumptions.append(("Target P/E Multiple", f"{em_base['target_pe']:.1f}x"))

    roic_base = forecast.get("roic_growth", {}).get("base")
    if roic_base is not None:
        assumptions.append(("ROIC", f"{roic_base['roic']*100:.1f}%"))
        assumptions.append(("Reinvestment Rate", f"{roic_base['reinvestment_rate']*100:.0f}%"))
        assumptions.append(("Sustainable Growth", f"{roic_base['sustainable_growth']*100:.1f}%"))

    assumption_df = pd.DataFrame(assumptions, columns=["Parameter", "Value"])

    st.dataframe(
        assumption_df,
        use_container_width=True,
        hide_index=True,
        height=min(400, 50 + len(assumptions) * 40),
    )
