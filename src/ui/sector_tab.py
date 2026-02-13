"""
Sector Analysis tab module.
Renders sector-level aggregates: treemap, comparison bars, summary table,
and sector-relative ROIC view for filtered stocks.
"""

from typing import Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.utils.config import (
    get_currency_symbol,
    SECTOR_TREEMAP_COLOR_SCALE,
    CHART_COLOR_POSITIVE,
    CHART_COLOR_NEGATIVE,
)
from src.ui.styles import (
    get_plotly_theme,
    COLORS,
    FONT_STACK,
    section_header,
    metric_card,
)


# ==================== MAIN ENTRY POINT ====================

def render_sector_section(
    universe_df: pd.DataFrame,
    results_df_raw: pd.DataFrame,
    screening_config: Dict[str, Any],
) -> None:
    """
    Render the Sector Analysis tab.

    Args:
        universe_df: Full screened universe with sector/industry and metrics
        results_df_raw: Filtered stocks that passed all screening criteria
        screening_config: User config (index, thresholds, etc.)
    """
    if universe_df is None or universe_df.empty:
        st.info("Run screening first to enable Sector Analysis.")
        return

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    currency_symbol = get_currency_symbol(screening_config.get('index', 'SP500'))

    # Build sector aggregates
    sector_agg = _build_sector_aggregates(universe_df, results_df_raw)

    if sector_agg.empty:
        st.info("No sector data available for the screened universe.")
        return

    # ---- Summary Metric Cards ----
    st.markdown(section_header("Sector Overview"), unsafe_allow_html=True)

    n_sectors = len(sector_agg)
    top_sector = sector_agg.iloc[0]['sector'] if not sector_agg.empty else "N/A"
    top_sector_roic = sector_agg.iloc[0]['avg_roic'] if not sector_agg.empty else 0
    total_stocks = int(sector_agg['stock_count'].sum())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            metric_card(label="Sectors Represented", value=str(n_sectors), accent="blue"),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            metric_card(
                label="Highest Avg ROIC Sector",
                value=top_sector,
                delta=f"{top_sector_roic:.1f}% avg ROIC",
                accent="green",
            ),
            unsafe_allow_html=True,
        )
    with col3:
        filtered_count = int(sector_agg['filtered_count'].sum())
        st.markdown(
            metric_card(
                label="Stocks in Universe",
                value=str(total_stocks),
                delta=f"{filtered_count} passed filters",
                accent="purple",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Treemap + Comparison side by side ----
    st.markdown(section_header("Sector Composition by Market Cap"), unsafe_allow_html=True)
    st.caption(
        "Rectangle size = total market capitalization. "
        "Color = average ROIC (green = high quality, red = low quality). "
        "Hover for details."
    )
    treemap_fig = create_sector_treemap(sector_agg, currency_symbol)
    if treemap_fig:
        st.plotly_chart(treemap_fig, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Sector Comparison Bar Chart ----
    st.markdown(section_header("Sector ROIC Comparison"), unsafe_allow_html=True)
    st.caption(
        "Average ROIC by sector across the full screened universe. "
        "Green = above 15% (Buffett baseline), amber = 10-15%, red = below 10%."
    )
    comparison_fig = create_sector_comparison_chart(sector_agg)
    if comparison_fig:
        st.plotly_chart(comparison_fig, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Sector Summary Table ----
    st.markdown(section_header("Sector Summary Table"), unsafe_allow_html=True)
    render_sector_metrics_table(sector_agg, currency_symbol)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ---- Sector-Relative ROIC (filtered stocks only) ----
    if not results_df_raw.empty and 'sector' in results_df_raw.columns:
        st.markdown(section_header("Filtered Stocks vs Sector Median ROIC"), unsafe_allow_html=True)
        st.caption(
            "How each filtered stock's ROIC compares to its sector median. "
            "Positive (green) = outperforms sector peers. "
            "Negative (red) = underperforms sector peers."
        )
        relative_fig = create_sector_relative_chart(universe_df, results_df_raw)
        if relative_fig:
            st.plotly_chart(relative_fig, use_container_width=True)
        else:
            st.info("Sector-relative view requires ROIC data for filtered stocks.")


# ==================== SECTOR AGGREGATION ====================

def _build_sector_aggregates(
    universe_df: pd.DataFrame,
    results_df_raw: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute per-sector aggregate metrics from the full universe.

    Args:
        universe_df: Full universe DataFrame with sector, roic, debt_to_equity, market_cap
        results_df_raw: Filtered stocks (used to count how many per sector passed)

    Returns:
        DataFrame with columns: sector, stock_count, avg_roic, avg_de,
        total_market_cap, filtered_count — sorted by avg_roic descending
    """
    if universe_df.empty:
        return pd.DataFrame()

    df = universe_df.copy()

    # Exclude Unknown sector if there are real sectors
    known = df[df['sector'] != 'Unknown']
    if not known.empty:
        df = known

    # Group by sector
    grouped = df.groupby('sector', sort=False)

    agg = grouped.agg(
        stock_count=('ticker', 'count'),
        avg_roic=('roic', lambda x: x.dropna().mean() * 100 if x.dropna().any() else 0),
        avg_de=('debt_to_equity', lambda x: x.dropna().mean() if x.dropna().any() else None),
        total_market_cap=('market_cap', 'sum'),
    ).reset_index()

    # Count filtered stocks per sector
    filtered_sectors = pd.Series(dtype='int64')
    if not results_df_raw.empty and 'sector' in results_df_raw.columns:
        filtered_sectors = results_df_raw.groupby('sector')['ticker'].count()

    agg['filtered_count'] = agg['sector'].map(filtered_sectors).fillna(0).astype(int)

    # Round for display
    agg['avg_roic'] = agg['avg_roic'].round(2)
    agg['avg_de'] = agg['avg_de'].round(2)

    # Sort by avg_roic descending
    agg = agg.sort_values('avg_roic', ascending=False).reset_index(drop=True)

    return agg


# ==================== SECTOR TREEMAP ====================

def create_sector_treemap(
    sector_agg: pd.DataFrame,
    currency_symbol: str = "$",
) -> Optional[go.Figure]:
    """
    Create a treemap of sectors sized by market cap, colored by avg ROIC.

    Args:
        sector_agg: Sector aggregates DataFrame
        currency_symbol: '$', '\u20b9', or '\u00a3'

    Returns:
        Plotly Figure or None
    """
    if sector_agg.empty:
        return None

    df = sector_agg.copy()

    # Format market cap for labels
    df['market_cap_fmt'] = df['total_market_cap'].apply(
        lambda x: _format_market_cap(x, currency_symbol)
    )

    # Custom text for each rectangle
    df['label_text'] = df.apply(
        lambda r: f"{r['sector']}<br>{r['stock_count']} stocks<br>Avg ROIC: {r['avg_roic']:.1f}%",
        axis=1,
    )

    fig = go.Figure(go.Treemap(
        labels=df['sector'],
        values=df['total_market_cap'],
        parents=[""] * len(df),
        text=df['label_text'],
        textinfo="text",
        textfont=dict(
            family=FONT_STACK,
            size=13,
        ),
        marker=dict(
            colors=df['avg_roic'],
            colorscale=SECTOR_TREEMAP_COLOR_SCALE,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Avg ROIC (%)",
                    font=dict(color=COLORS['text_secondary'], size=12),
                ),
                tickfont=dict(color=COLORS['text_secondary']),
                thickness=12,
                len=0.6,
                outlinecolor=COLORS['border'],
                bgcolor=COLORS['surface'],
            ),
            line=dict(width=2, color=COLORS['bg_primary']),
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Stocks: %{customdata[0]}<br>"
            "Avg ROIC: %{customdata[1]:.1f}%<br>"
            "Avg D/E: %{customdata[2]:.2f}<br>"
            "Market Cap: %{customdata[3]}<br>"
            "Passed Filters: %{customdata[4]}"
            "<extra></extra>"
        ),
        customdata=df[['stock_count', 'avg_roic', 'avg_de', 'market_cap_fmt', 'filtered_count']].values,
    ))

    fig.update_layout(
        paper_bgcolor=COLORS['surface'],
        plot_bgcolor=COLORS['surface'],
        font=dict(family=FONT_STACK, color=COLORS['text_secondary']),
        height=450,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    return fig


# ==================== SECTOR COMPARISON BAR CHART ====================

def create_sector_comparison_chart(
    sector_agg: pd.DataFrame,
) -> Optional[go.Figure]:
    """
    Create horizontal bar chart comparing average ROIC across sectors.

    Args:
        sector_agg: Sector aggregates (sorted by avg_roic descending)

    Returns:
        Plotly Figure or None
    """
    if sector_agg.empty:
        return None

    df = sector_agg.sort_values('avg_roic', ascending=True).copy()

    # Color-code bars: green >15%, amber 10-15%, red <10%
    colors = []
    for roic in df['avg_roic']:
        if roic >= 15:
            colors.append(CHART_COLOR_POSITIVE)
        elif roic >= 10:
            colors.append(COLORS['accent_amber'])
        else:
            colors.append(CHART_COLOR_NEGATIVE)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['avg_roic'],
        y=df['sector'],
        orientation='h',
        marker_color=colors,
        text=[f"{r:.1f}%" for r in df['avg_roic']],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary'], size=11),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Avg ROIC: %{x:.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    # 15% reference line
    fig.add_vline(
        x=15,
        line_dash="dash",
        line_color=COLORS['text_muted'],
        annotation_text="15% baseline",
        annotation_position="top right",
        annotation_font_size=10,
        annotation_font_color=COLORS['text_muted'],
    )

    theme = get_plotly_theme()
    fig.update_layout(**theme)
    fig.update_layout(
        yaxis_title="",
        xaxis_title="Average ROIC (%)",
        height=max(300, len(df) * 36 + 80),
        margin=dict(l=160, r=60, t=30, b=50),
        showlegend=False,
    )

    return fig


# ==================== SECTOR METRICS TABLE ====================

def render_sector_metrics_table(
    sector_agg: pd.DataFrame,
    currency_symbol: str = "$",
) -> None:
    """
    Render a formatted sector summary table.

    Args:
        sector_agg: Sector aggregates DataFrame
        currency_symbol: '$', '\u20b9', or '\u00a3'
    """
    if sector_agg.empty:
        st.info("No sector data to display.")
        return

    display_df = sector_agg.copy()

    # Format columns
    display_df['avg_roic_fmt'] = display_df['avg_roic'].apply(lambda x: f"{x:.1f}%")
    display_df['avg_de_fmt'] = display_df['avg_de'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )
    display_df['market_cap_fmt'] = display_df['total_market_cap'].apply(
        lambda x: _format_market_cap(x, currency_symbol)
    )

    table_df = display_df[[
        'sector', 'stock_count', 'avg_roic_fmt', 'avg_de_fmt',
        'market_cap_fmt', 'filtered_count',
    ]]

    column_config = {
        'sector': st.column_config.TextColumn('Sector', width='medium'),
        'stock_count': st.column_config.NumberColumn('Stocks', width='small'),
        'avg_roic_fmt': st.column_config.TextColumn(
            'Avg ROIC',
            width='small',
            help="Average Return on Invested Capital across all stocks in this sector",
        ),
        'avg_de_fmt': st.column_config.TextColumn(
            'Avg D/E',
            width='small',
            help="Average Debt-to-Equity ratio across all stocks in this sector",
        ),
        'market_cap_fmt': st.column_config.TextColumn(
            'Total Market Cap',
            width='small',
            help="Combined market capitalization of all stocks in this sector",
        ),
        'filtered_count': st.column_config.NumberColumn(
            'Passed Filters',
            width='small',
            help="Number of stocks from this sector that passed all screening criteria",
        ),
    }

    st.dataframe(
        table_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=min(400, len(table_df) * 38 + 50),
    )


# ==================== SECTOR-RELATIVE ROIC VIEW ====================

def create_sector_relative_chart(
    universe_df: pd.DataFrame,
    results_df_raw: pd.DataFrame,
) -> Optional[go.Figure]:
    """
    Create diverging bar chart showing each filtered stock's ROIC vs sector median.

    Positive bars (green) = stock outperforms its sector.
    Negative bars (red) = stock underperforms its sector.

    Args:
        universe_df: Full universe with sector and roic columns
        results_df_raw: Filtered stocks

    Returns:
        Plotly Figure or None
    """
    if results_df_raw.empty or universe_df.empty:
        return None

    if 'sector' not in results_df_raw.columns or 'roic' not in results_df_raw.columns:
        return None

    # Compute sector medians from the full universe
    sector_medians = (
        universe_df
        .dropna(subset=['roic'])
        .groupby('sector')['roic']
        .median()
    )

    rows = []
    for _, stock in results_df_raw.iterrows():
        ticker = stock.get('ticker', '')
        roic = stock.get('roic')
        sector = stock.get('sector', 'Unknown')

        if roic is None or pd.isna(roic):
            continue

        median = sector_medians.get(sector)
        if median is None or pd.isna(median):
            continue

        diff_pct = (roic - median) * 100  # Convert to percentage points
        rows.append({
            'ticker': ticker,
            'sector': sector,
            'roic_pct': roic * 100,
            'sector_median_pct': median * 100,
            'diff_pct': round(diff_pct, 2),
        })

    if not rows:
        return None

    df = pd.DataFrame(rows).sort_values('diff_pct', ascending=True)

    colors = [
        CHART_COLOR_POSITIVE if d >= 0 else CHART_COLOR_NEGATIVE
        for d in df['diff_pct']
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['diff_pct'],
        y=df['ticker'],
        orientation='h',
        marker_color=colors,
        text=[f"{d:+.1f}pp" for d in df['diff_pct']],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary'], size=11),
        hovertemplate=(
            "<b>%{y}</b> (%{customdata[0]})<br>"
            "Stock ROIC: %{customdata[1]:.1f}%<br>"
            "Sector Median: %{customdata[2]:.1f}%<br>"
            "Difference: %{x:+.1f}pp"
            "<extra></extra>"
        ),
        customdata=df[['sector', 'roic_pct', 'sector_median_pct']].values,
    ))

    # Zero reference line
    fig.add_vline(
        x=0,
        line_color=COLORS['text_muted'],
        line_width=1,
    )

    theme = get_plotly_theme()
    fig.update_layout(**theme)
    fig.update_layout(
        yaxis_title="",
        xaxis_title="ROIC vs Sector Median (percentage points)",
        height=max(300, len(df) * 36 + 80),
        margin=dict(l=100, r=60, t=30, b=50),
        showlegend=False,
    )

    return fig


# ==================== HELPERS ====================

def _format_market_cap(value: Optional[float], currency_symbol: str = "$") -> str:
    """Format market cap as readable string."""
    if value is None or pd.isna(value):
        return "N/A"

    if value >= 1e12:
        return f"{currency_symbol}{value/1e12:.2f}T"
    elif value >= 1e9:
        return f"{currency_symbol}{value/1e9:.1f}B"
    elif value >= 1e6:
        return f"{currency_symbol}{value/1e6:.0f}M"
    else:
        return f"{currency_symbol}{value:,.0f}"
