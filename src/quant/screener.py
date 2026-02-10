"""
Stock screening and ranking module.
Applies fundamental health filters, valuation filters, and ranking logic.
"""

from typing import Optional, Dict
import pandas as pd
from src.quant.metrics import calculate_all_metrics
from src.utils.config import MIN_ROIC, MAX_DEBT_EQUITY


# ==================== SCREENING PIPELINE ====================

def screen_stocks(
    stocks_data: Dict[str, Optional[dict]],
    min_roic: float = MIN_ROIC,
    max_debt_equity: float = MAX_DEBT_EQUITY,
    near_low_threshold: float = 10.0,
    require_3y_fcf: bool = True
) -> pd.DataFrame:
    """
    Main screening pipeline: Calculate metrics → Filter → Rank.

    Applies STRICT filtering:
    - ROIC > min_roic (default 15%)
    - Debt/Equity < max_debt_equity (default 0.8)
    - 3-year positive FCF (if require_3y_fcf=True)
    - Price within near_low_threshold % of 52-week low (default 10%)

    Args:
        stocks_data: Dictionary mapping ticker -> deep data
        min_roic: Minimum ROIC threshold (as decimal, e.g., 0.15)
        max_debt_equity: Maximum D/E ratio threshold
        near_low_threshold: % threshold for "near 52-week low"
        require_3y_fcf: If True, require 3-year positive FCF

    Returns:
        DataFrame with passing stocks, sorted by value_score (descending)
    """
    results = []

    for ticker, data in stocks_data.items():
        if data is None:
            continue

        # Calculate all metrics
        metrics = calculate_all_metrics(data)

        # Extract basic info
        company_name = data.get('longName', ticker)
        current_price = data.get('currentPrice')
        market_cap = data.get('marketCap')

        # Extract 52-week data
        fifty_two_week_high = data.get('fiftyTwoWeekHigh')
        fifty_two_week_low = data.get('fiftyTwoWeekLow')

        # Combine into result row
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'market_cap': market_cap,
            'fifty_two_week_high': fifty_two_week_high,
            'fifty_two_week_low': fifty_two_week_low,
            **metrics
        }

        results.append(result)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    if df.empty:
        return df

    # Apply STRICT quality filters
    df = apply_quality_filters(
        df,
        min_roic=min_roic,
        max_debt_equity=max_debt_equity,
        require_3y_fcf=require_3y_fcf
    )

    # Apply STRICT valuation filter
    df = apply_valuation_filter(df, near_low_threshold=near_low_threshold)

    # Rank by value score
    df = rank_by_value_score(df)

    return df


# ==================== QUALITY FILTERS ====================

def apply_quality_filters(
    df: pd.DataFrame,
    min_roic: float = 0.15,
    max_debt_equity: float = 0.8,
    require_3y_fcf: bool = True
) -> pd.DataFrame:
    """
    Apply fundamental health filters (STRICT exclusion).

    Filters:
    1. ROIC > min_roic
    2. Debt/Equity < max_debt_equity
    3. 3-year positive FCF (optional)

    Args:
        df: DataFrame with calculated metrics
        min_roic: Minimum ROIC threshold
        max_debt_equity: Maximum D/E threshold
        require_3y_fcf: If True, require FCF > 0 for 3 years

    Returns:
        Filtered DataFrame (stocks failing ANY filter are excluded)
    """
    if df.empty:
        return df

    # Filter 1: ROIC > min_roic
    df = df[df['roic'] > min_roic]

    # Filter 2: Debt/Equity < max_debt_equity
    df = df[df['debt_to_equity'] < max_debt_equity]

    # Filter 3: 3-year positive FCF (strict)
    if require_3y_fcf:
        df = df[df['fcf_3y_positive'] == True]

    return df


# ==================== VALUATION FILTER ====================

def apply_valuation_filter(
    df: pd.DataFrame,
    near_low_threshold: float = 10.0
) -> pd.DataFrame:
    """
    Apply 'Buy-the-Dip' price filter (STRICT exclusion).

    Filter:
    - Current price must be within near_low_threshold % of 52-week low

    Args:
        df: DataFrame with calculated metrics
        near_low_threshold: Percentage threshold (default 10%)

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    # Filter: Price near 52-week low
    df = df[df['near_52w_low'] == True]

    return df


# ==================== RANKING ====================

def rank_by_value_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort stocks by value_score in descending order and add rank column.

    Args:
        df: DataFrame with value_score column

    Returns:
        Sorted DataFrame with 'rank' column
    """
    if df.empty:
        return df

    # Sort by value_score (highest first)
    df = df.sort_values('value_score', ascending=False)

    # Add rank column
    df.insert(0, 'rank', range(1, len(df) + 1))

    # Reset index
    df = df.reset_index(drop=True)

    return df


# ==================== SUMMARY STATISTICS ====================

def get_screening_summary(
    total_tickers: int,
    passed_tickers: int,
    filters_applied: dict
) -> dict:
    """
    Generate summary statistics for screening results.

    Args:
        total_tickers: Total number of tickers screened
        passed_tickers: Number of tickers that passed all filters
        filters_applied: Dictionary of filter criteria used

    Returns:
        Summary dictionary
    """
    pass_rate = (passed_tickers / total_tickers * 100) if total_tickers > 0 else 0

    return {
        'total_tickers_screened': total_tickers,
        'tickers_passed': passed_tickers,
        'tickers_failed': total_tickers - passed_tickers,
        'pass_rate_pct': round(pass_rate, 2),
        'filters_applied': filters_applied
    }


# ==================== CONVENIENCE FUNCTIONS ====================

def format_results_for_display(
    df: pd.DataFrame,
    currency_symbol: str = "$"
) -> pd.DataFrame:
    """
    Format screening results for UI display.

    Adds:
    - Percentage formatting for ROIC, distances
    - Readable market cap with currency symbol
    - Currency-prefixed price columns
    - 52-week high/low formatted columns

    Args:
        df: Raw screening results DataFrame
        currency_symbol: Currency symbol ('$' or '\u20b9')

    Returns:
        Formatted DataFrame
    """
    if df.empty:
        return df

    display_df = df.copy()

    # Format ROIC as percentage
    if 'roic' in display_df.columns:
        display_df['roic_pct'] = display_df['roic'].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
        )

    # Format Debt/Equity
    if 'debt_to_equity' in display_df.columns:
        display_df['de_ratio'] = display_df['debt_to_equity'].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
        )

    # Format Distance from High
    if 'distance_from_high' in display_df.columns:
        display_df['discount_pct'] = display_df['distance_from_high'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

    # Format Value Score
    if 'value_score' in display_df.columns:
        display_df['value_score'] = display_df['value_score'].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
        )

    # Format Market Cap with currency
    if 'market_cap' in display_df.columns:
        display_df['market_cap_fmt'] = display_df['market_cap'].apply(
            lambda x: _format_market_cap(x, currency_symbol)
        )

    # Format current price with currency
    if 'current_price' in display_df.columns:
        display_df['current_price_fmt'] = display_df['current_price'].apply(
            lambda x: f"{currency_symbol}{x:,.2f}" if pd.notna(x) else "N/A"
        )

    # Format 52-week high/low with currency
    if 'fifty_two_week_high' in display_df.columns:
        display_df['fifty_two_week_high_fmt'] = display_df['fifty_two_week_high'].apply(
            lambda x: f"{currency_symbol}{x:,.2f}" if pd.notna(x) else "N/A"
        )

    if 'fifty_two_week_low' in display_df.columns:
        display_df['fifty_two_week_low_fmt'] = display_df['fifty_two_week_low'].apply(
            lambda x: f"{currency_symbol}{x:,.2f}" if pd.notna(x) else "N/A"
        )

    return display_df


def _format_market_cap(value: Optional[float], currency_symbol: str = "$") -> str:
    """Format market cap as readable string (e.g., $1.5T, \u20b9450B, $25M)."""
    if value is None or pd.isna(value):
        return "N/A"

    if value >= 1e12:
        return f"{currency_symbol}{value/1e12:.2f}T"
    elif value >= 1e9:
        return f"{currency_symbol}{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{currency_symbol}{value/1e6:.2f}M"
    else:
        return f"{currency_symbol}{value:,.0f}"


# ==================== EXPORT FUNCTIONS ====================

def get_top_n_stocks(df: pd.DataFrame, n: int = 25) -> pd.DataFrame:
    """
    Get top N stocks by value_score.

    Args:
        df: Screened and ranked DataFrame
        n: Number of top stocks to return

    Returns:
        DataFrame with top N stocks
    """
    if df.empty:
        return df

    return df.head(n)


def get_stocks_by_roic(df: pd.DataFrame, min_roic: float = 0.20) -> pd.DataFrame:
    """
    Filter results to show only high-ROIC stocks.

    Args:
        df: Screened DataFrame
        min_roic: Minimum ROIC threshold (e.g., 0.20 for 20%)

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    return df[df['roic'] >= min_roic]
