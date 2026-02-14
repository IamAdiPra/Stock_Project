"""
Stock screening and ranking module.
Applies fundamental health filters, valuation filters, and ranking logic.
"""

from typing import Optional, Dict
import pandas as pd
from src.quant.metrics import calculate_all_metrics, calculate_momentum_score
from src.data.fetcher import fetch_historical_prices
from src.utils.config import (
    MIN_ROIC, MAX_DEBT_EQUITY,
    VALUE_SCORE_ROIC_WEIGHT, VALUE_SCORE_DISCOUNT_WEIGHT,
    HYBRID_VALUE_WEIGHT, HYBRID_MOMENTUM_WEIGHT,
)


# ==================== SCREENING PIPELINE ====================

def screen_stocks(
    stocks_data: Dict[str, Optional[dict]],
    min_roic: float = MIN_ROIC,
    max_debt_equity: float = MAX_DEBT_EQUITY,
    near_low_threshold: float = 10.0,
    require_3y_fcf: bool = True,
    min_earnings_quality: float = 0,
    use_hybrid_ranking: bool = False,
) -> pd.DataFrame:
    """
    Main screening pipeline: Calculate metrics → Filter → Rank.

    Applies STRICT filtering:
    - ROIC > min_roic (default 15%)
    - Debt/Equity < max_debt_equity (default 0.8)
    - 3-year positive FCF (if require_3y_fcf=True)
    - Earnings Quality >= min_earnings_quality (default 0 = disabled)
    - Price within near_low_threshold % of 52-week low (default 10%)

    Args:
        stocks_data: Dictionary mapping ticker -> deep data
        min_roic: Minimum ROIC threshold (as decimal, e.g., 0.15)
        max_debt_equity: Maximum D/E ratio threshold
        near_low_threshold: % threshold for "near 52-week low"
        require_3y_fcf: If True, require 3-year positive FCF
        min_earnings_quality: Minimum earnings quality score 0-100 (0 = disabled)
        use_hybrid_ranking: If True, rank by 70% value + 30% momentum

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

        # Extract sector/industry classification
        sector = data.get('sector') or 'Unknown'
        industry = data.get('industry') or 'Unknown'

        # Combine into result row
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'sector': sector,
            'industry': industry,
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

    # Apply optional earnings quality filter (0 = disabled)
    df = apply_earnings_quality_filter(df, min_score=min_earnings_quality)

    # Apply STRICT valuation filter
    df = apply_valuation_filter(df, near_low_threshold=near_low_threshold)

    # Compute value scores using rank-percentile normalization
    df = compute_rank_percentile_scores(df)

    # Compute momentum scores for filtered stocks (typically 5-20 stocks)
    if not df.empty:
        df = compute_momentum_scores(df, stocks_data)

    # Optionally compute hybrid score and rank by it
    if use_hybrid_ranking and not df.empty:
        df = compute_hybrid_scores(df)
        df = rank_by_value_score(df, score_column='hybrid_score')
    else:
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


# ==================== EARNINGS QUALITY FILTER ====================

def apply_earnings_quality_filter(
    df: pd.DataFrame,
    min_score: float = 0,
) -> pd.DataFrame:
    """
    Apply optional Earnings Quality Score filter.

    Stocks with None score (missing data) always pass — they are not
    penalized for incomplete financial statements.

    Args:
        df: DataFrame with 'earnings_quality_score' column
        min_score: Minimum score threshold (0 = disabled, no filtering)

    Returns:
        Filtered DataFrame
    """
    if df.empty or min_score <= 0:
        return df

    if 'earnings_quality_score' not in df.columns:
        return df

    # Keep stocks where score >= min OR score is None (missing data)
    df = df[
        df['earnings_quality_score'].isna() |
        (df['earnings_quality_score'] >= min_score)
    ]

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

    # Filter: Price within near_low_threshold % of 52-week low
    df = df[df['distance_from_low'].notna() & (df['distance_from_low'] <= near_low_threshold)]

    return df


# ==================== VALUE SCORE (RANK-PERCENTILE) ====================

def compute_rank_percentile_scores(
    df: pd.DataFrame,
    roic_weight: float = VALUE_SCORE_ROIC_WEIGHT,
    discount_weight: float = VALUE_SCORE_DISCOUNT_WEIGHT,
) -> pd.DataFrame:
    """
    Compute value_score using rank-percentile normalization.

    Both ROIC and discount components are normalized to 0-1 range via
    rank percentile within the screened universe. This ensures the
    configured weights (default 60/40) reflect actual influence on
    the final score.

    Previous approach: ROIC/0.15 (range ~0.5-4+) vs |dist|/100 (range 0-0.4)
    meant ROIC dominated ~90% of the score despite 60% weight.

    Args:
        df: Filtered DataFrame with 'roic' and 'distance_from_high' columns
        roic_weight: Weight for ROIC component (default 0.6)
        discount_weight: Weight for discount component (default 0.4)

    Returns:
        DataFrame with 'value_score' column (range 0.0 to 1.0)
    """
    if df.empty:
        return df

    df = df.copy()

    # ROIC: higher is better → highest ROIC gets percentile 1.0
    df['value_score'] = df['roic'].rank(pct=True) * roic_weight

    # Discount: larger |distance_from_high| is better → biggest drop gets 1.0
    if 'distance_from_high' in df.columns:
        discount_pctile = df['distance_from_high'].abs().rank(pct=True)
        df['value_score'] = df['value_score'] + (discount_pctile * discount_weight)

    return df


# ==================== MOMENTUM SCORING ====================

def compute_momentum_scores(
    df: pd.DataFrame,
    stocks_data: Dict[str, Optional[dict]],
) -> pd.DataFrame:
    """
    Compute momentum scores for each stock in the filtered DataFrame.

    Fetches 2y historical prices per ticker (cached 24h), computes RSI,
    MACD, and SMA crossover, then produces a composite 0-100 score.

    Only called for stocks that passed all value filters (typically 5-20),
    so the additional API calls are minimal.

    Args:
        df: Filtered DataFrame with 'ticker' column
        stocks_data: Original stocks_data dict (for normalized ticker lookup)

    Returns:
        DataFrame with 'momentum_score' column added
    """
    if df.empty:
        return df

    df = df.copy()
    momentum_scores = []

    for ticker in df['ticker']:
        data = stocks_data.get(ticker, {}) or {}
        normalized = data.get('normalized_ticker', ticker)

        price_df = fetch_historical_prices(normalized, period="2y")
        momentum = calculate_momentum_score(price_df)
        momentum_scores.append(momentum.get("momentum_score"))

    df['momentum_score'] = momentum_scores
    return df


def compute_hybrid_scores(
    df: pd.DataFrame,
    value_weight: float = HYBRID_VALUE_WEIGHT,
    momentum_weight: float = HYBRID_MOMENTUM_WEIGHT,
) -> pd.DataFrame:
    """
    Compute hybrid score blending value and momentum rank-percentiles.

    hybrid_score = value_score * 0.7 + momentum_pctile * 0.3

    Momentum is normalized to 0-1 via rank-percentile within the filtered
    universe (consistent with value_score's normalization).

    Stocks with None momentum_score are excluded from momentum ranking
    and receive hybrid_score = value_score (pure value fallback).

    Args:
        df: DataFrame with 'value_score' and 'momentum_score' columns
        value_weight: Weight for value component (default 0.7)
        momentum_weight: Weight for momentum component (default 0.3)

    Returns:
        DataFrame with 'hybrid_score' column
    """
    if df.empty:
        return df

    df = df.copy()

    has_momentum = df['momentum_score'].notna()

    if has_momentum.sum() >= 2:
        momentum_pctile = df.loc[has_momentum, 'momentum_score'].rank(pct=True)
        df.loc[has_momentum, 'hybrid_score'] = (
            df.loc[has_momentum, 'value_score'] * value_weight
            + momentum_pctile * momentum_weight
        )
    # Fallback for stocks without momentum data
    df['hybrid_score'] = df['hybrid_score'] if 'hybrid_score' in df.columns else df['value_score']
    df['hybrid_score'] = df['hybrid_score'].fillna(df['value_score'])

    return df


# ==================== RANKING ====================

def rank_by_value_score(
    df: pd.DataFrame,
    score_column: str = 'value_score',
) -> pd.DataFrame:
    """
    Sort stocks by a score column in descending order and add rank column.

    Args:
        df: DataFrame with the specified score column
        score_column: Column to sort by (default 'value_score', or 'hybrid_score')

    Returns:
        Sorted DataFrame with 'rank' column
    """
    if df.empty:
        return df

    # Sort by score (highest first)
    df = df.sort_values(score_column, ascending=False)

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

    # Format Earnings Quality Score as integer
    if 'earnings_quality_score' in display_df.columns:
        display_df['earnings_quality_fmt'] = display_df['earnings_quality_score'].apply(
            lambda x: f"{int(x)}" if pd.notna(x) else "N/A"
        )

    # Format Momentum Score as integer
    if 'momentum_score' in display_df.columns:
        display_df['momentum_score_fmt'] = display_df['momentum_score'].apply(
            lambda x: f"{int(x)}" if pd.notna(x) else "N/A"
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


# ==================== SECTOR UNIVERSE ====================

def build_sector_universe(
    stocks_data: Dict[str, Optional[dict]],
) -> pd.DataFrame:
    """
    Build a DataFrame of ALL stocks with sector/industry and key metrics.

    Used for sector analysis where the full screened universe (not just
    filtered stocks) is needed for meaningful sector aggregates.

    Financial statements are already in-memory from the screening fetch,
    so calculate_all_metrics() performs no API calls — only CPU computation.

    Args:
        stocks_data: Dictionary mapping ticker -> deep data (from batch_fetch_deep_data)

    Returns:
        DataFrame with columns: ticker, company_name, sector, industry,
        market_cap, current_price, roic, debt_to_equity
    """
    rows = []

    for ticker, data in stocks_data.items():
        if data is None:
            continue

        metrics = calculate_all_metrics(data, skip_validation=True)

        rows.append({
            'ticker': ticker,
            'company_name': data.get('longName', ticker),
            'sector': data.get('sector') or 'Unknown',
            'industry': data.get('industry') or 'Unknown',
            'market_cap': data.get('marketCap'),
            'current_price': data.get('currentPrice'),
            'roic': metrics.get('roic'),
            'debt_to_equity': metrics.get('debt_to_equity'),
        })

    df = pd.DataFrame(rows)

    # Drop stocks with no market cap (can't size treemap)
    if not df.empty:
        df = df.dropna(subset=['market_cap'])

    return df


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
