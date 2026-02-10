"""
Plotly visualizations for stock screening results.
Creates interactive scatter plots and charts for value discovery.
"""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def create_value_scatter_plot(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create interactive scatter plot: ROIC vs Distance from 52w Low.

    Bubble characteristics:
    - X-axis: Distance from 52-week Low (%)
    - Y-axis: ROIC (%)
    - Bubble Size: Scaled by Value Score (larger = better)
    - Bubble Color: RdYlGn gradient (Green = high value, Red = low value)

    Args:
        df: Screening results DataFrame with columns:
            - distance_from_low (float)
            - roic (float)
            - value_score (float)
            - ticker (str)
            - company_name (str)
            - market_cap (float)

    Returns:
        Plotly Figure object or None if DataFrame is empty
    """
    if df.empty:
        return None

    # Prepare data for plotting
    plot_df = df.copy()

    # ==================== ROBUST TYPE CONVERSION ====================
    # Convert all numeric columns to float (handles string formatted values)
    numeric_columns = ['roic', 'distance_from_low', 'value_score', 'market_cap']

    for col in numeric_columns:
        if col in plot_df.columns:
            plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce')

    # Drop rows with NaN in critical columns (roic, value_score)
    plot_df = plot_df.dropna(subset=['roic', 'value_score', 'distance_from_low'])

    if plot_df.empty:
        return None

    # Convert ROIC to percentage for Y-axis
    plot_df['roic_pct'] = plot_df['roic'] * 100

    # Ensure distance_from_low is positive (% above 52w low)
    plot_df['distance_from_low_pct'] = plot_df['distance_from_low']

    # Scale bubble size based on value_score (min 10, max 50)
    plot_df['bubble_size'] = plot_df['value_score'] * 20

    # Format market cap for hover
    plot_df['market_cap_fmt'] = plot_df['market_cap'].apply(_format_market_cap)

    # Create scatter plot using Plotly Express (easier for color scales)
    fig = px.scatter(
        plot_df,
        x='distance_from_low_pct',
        y='roic_pct',
        size='bubble_size',
        color='value_score',
        color_continuous_scale='RdYlGn',  # Red-Yellow-Green gradient
        hover_name='ticker',
        hover_data={
            'company_name': True,
            'roic_pct': ':.2f',
            'distance_from_low_pct': ':.2f',
            'value_score': ':.3f',
            'market_cap_fmt': True,
            'bubble_size': False  # Hide internal calculation
        },
        labels={
            'distance_from_low_pct': 'Distance from 52-Week Low (%)',
            'roic_pct': 'ROIC (%)',
            'value_score': 'Value Score',
            'market_cap_fmt': 'Market Cap'
        },
        title='📈 Value Discovery Map: ROIC vs Price Discount'
    )

    # Customize layout for professional appearance
    fig.update_layout(
        # Title styling
        title_font_size=20,
        title_font_color='#2C3E50',
        title_x=0.5,  # Center title
        title_xanchor='center',

        # Plot area styling
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',

        # Axes styling
        xaxis=dict(
            title_font_size=14,
            showgrid=True,
            gridcolor='#E0E0E0',
            zeroline=True,
            zerolinecolor='#BDBDBD',
            zerolinewidth=2
        ),
        yaxis=dict(
            title_font_size=14,
            showgrid=True,
            gridcolor='#E0E0E0',
            zeroline=True,
            zerolinecolor='#BDBDBD',
            zerolinewidth=2
        ),

        # Hover styling
        hovermode='closest',
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        ),

        # Legend/Colorbar styling
        coloraxis_colorbar=dict(
            title='Value Score',
            title_font_size=12,
            thickness=15,
            len=0.7
        ),

        # Responsive sizing
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    # Update marker styling
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='#34495E'),  # Dark border for bubbles
            opacity=0.8,
            sizemode='diameter',
            sizemin=4
        )
    )

    return fig


def create_roic_distribution_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create histogram showing ROIC distribution of screened stocks.

    Args:
        df: Screening results DataFrame with 'roic' column

    Returns:
        Plotly Figure object or None if DataFrame is empty
    """
    if df.empty:
        return None

    plot_df = df.copy()
    plot_df['roic_pct'] = plot_df['roic'] * 100

    fig = px.histogram(
        plot_df,
        x='roic_pct',
        nbins=20,
        color_discrete_sequence=['#00CC96'],
        labels={'roic_pct': 'ROIC (%)'},
        title='ROIC Distribution'
    )

    fig.update_layout(
        title_font_size=16,
        title_x=0.5,
        title_xanchor='center',
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        height=300,
        showlegend=False
    )

    return fig


def create_debt_equity_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create bar chart showing debt-to-equity ratios of top stocks.

    Args:
        df: Screening results DataFrame with 'debt_to_equity' and 'ticker' columns

    Returns:
        Plotly Figure object or None if DataFrame is empty
    """
    if df.empty:
        return None

    # Take top 10 stocks by value_score
    plot_df = df.head(10).copy()

    fig = px.bar(
        plot_df,
        x='ticker',
        y='debt_to_equity',
        color='debt_to_equity',
        color_continuous_scale='RdYlGn_r',  # Reversed (low debt = green)
        labels={'debt_to_equity': 'Debt/Equity Ratio', 'ticker': 'Ticker'},
        title='Debt/Equity Ratios (Top 10 Stocks)'
    )

    fig.update_layout(
        title_font_size=16,
        title_x=0.5,
        title_xanchor='center',
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        height=350,
        showlegend=False
    )

    return fig


def _format_market_cap(value: Optional[float]) -> str:
    """
    Format market cap as readable string (e.g., $1.5T, $450B, $25M).

    Args:
        value: Market cap in dollars

    Returns:
        Formatted string with currency and abbreviation
    """
    if value is None or pd.isna(value):
        return "N/A"

    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.0f}"
