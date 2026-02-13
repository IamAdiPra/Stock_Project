"""
Financial metrics calculation module.
Pure functions that compute ROIC, FCF, D/E, and valuation metrics from raw data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from src.utils.config import (
    ROIC_CAP, METRIC_SANITY_BOUNDS, EARNINGS_QUALITY_WEIGHTS,
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    SMA_SHORT_PERIOD, SMA_LONG_PERIOD, MOMENTUM_WEIGHTS,
)
from src.utils.logger import log_data_issue


# ==================== ROIC CALCULATION (NOPAT-Based) ====================

def calculate_roic_for_year(
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
    year_index: int = 0
) -> Optional[float]:
    """
    Calculate ROIC for a specific fiscal year using NOPAT method.

    Formula:
        ROIC = NOPAT / Invested Capital

    Where:
        NOPAT = Operating Income × (1 - Tax Rate)
        Invested Capital = Total Debt + Total Equity - Cash

    Args:
        income_statement: Income statement DataFrame (columns = fiscal years)
        balance_sheet: Balance sheet DataFrame (columns = fiscal years)
        year_index: Column index (0 = most recent, 1 = previous year, etc.)

    Returns:
        ROIC as a decimal (e.g., 0.18 for 18%) or None if calculation fails
    """
    if income_statement is None or balance_sheet is None:
        return None

    if income_statement.empty or balance_sheet.empty:
        return None

    if year_index >= income_statement.shape[1] or year_index >= balance_sheet.shape[1]:
        return None

    try:
        income = income_statement.iloc[:, year_index]
        balance = balance_sheet.iloc[:, year_index]

        # Extract Operating Income (EBIT)
        operating_income = _extract_value(income, [
            'Operating Income', 'EBIT', 'Operating Revenue'
        ])

        # Extract Tax Rate (calculate from Tax Provision / Pretax Income)
        tax_provision = _extract_value(income, [
            'Tax Provision', 'Income Tax Expense', 'Tax Effect Of Unusual Items'
        ])
        pretax_income = _extract_value(income, [
            'Pretax Income', 'Income Before Tax'
        ])

        # Calculate effective tax rate
        if pretax_income and pretax_income != 0:
            tax_rate = abs(tax_provision) / abs(pretax_income)
        else:
            tax_rate = 0.25  # 25% default

        # Calculate NOPAT
        if operating_income is None:
            return None

        nopat = operating_income * (1 - tax_rate)

        # Extract Invested Capital components
        total_debt = _extract_value(balance, [
            'Total Debt', 'Long Term Debt', 'Net Debt'
        ])
        total_equity = _extract_value(balance, [
            'Stockholders Equity', 'Total Equity Gross Minority Interest',
            'Total Stockholder Equity'
        ])
        cash = _extract_value(balance, [
            'Cash And Cash Equivalents', 'Cash', 'Cash Cash Equivalents And Short Term Investments'
        ])

        # Calculate Invested Capital
        if total_debt is None or total_equity is None:
            return None

        invested_capital = total_debt + total_equity - (cash or 0)

        # Fallback: Capital Employed = Total Assets - Current Liabilities
        # Handles cash-rich companies (Apple, Google, Indian IT) where
        # Cash > Total Debt + Total Equity produces negative invested capital
        if invested_capital <= 0:
            total_assets = _extract_value(balance, [
                'Total Assets'
            ])
            current_liabilities = _extract_value(balance, [
                'Current Liabilities', 'Total Current Liabilities'
            ])

            if total_assets is not None and current_liabilities is not None:
                invested_capital = total_assets - current_liabilities

            if invested_capital <= 0:
                return None

        roic = nopat / invested_capital

        # Cap at ROIC_CAP (100%) — prevents absurd values from near-zero denominators
        roic = min(roic, ROIC_CAP)

        return roic

    except Exception:
        return None


def calculate_roic(
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame]
) -> Optional[float]:
    """
    Calculate ROIC for the most recent fiscal year (convenience wrapper).

    Args:
        income_statement: Income statement DataFrame (columns = fiscal years)
        balance_sheet: Balance sheet DataFrame (columns = fiscal years)

    Returns:
        ROIC as a decimal (e.g., 0.18 for 18%) or None if calculation fails
    """
    return calculate_roic_for_year(income_statement, balance_sheet, year_index=0)


def _extract_value(series: pd.Series, possible_keys: List[str]) -> Optional[float]:
    """
    Extract a value from a pandas Series by trying multiple possible keys.

    Args:
        series: Pandas Series (financial statement row)
        possible_keys: List of possible row names to try

    Returns:
        Float value or None if not found
    """
    for key in possible_keys:
        if key in series.index:
            value = series[key]
            if pd.notna(value) and value != 0:
                return float(value)

    return None


# ==================== METRIC SANITY VALIDATION ====================

def validate_metric_bounds(
    ticker: str,
    metric_name: str,
    value: Optional[float],
) -> None:
    """
    Check a computed metric against sanity bounds and log violations.

    Values outside bounds are flagged as 'validation_error' in the
    Data Quality Report. The value itself is NOT modified — this is
    purely informational.

    Args:
        ticker: Stock ticker symbol (for logging)
        metric_name: Key in METRIC_SANITY_BOUNDS dict
        value: Computed metric value (None is silently skipped)
    """
    if value is None:
        return

    bounds = METRIC_SANITY_BOUNDS.get(metric_name)
    if bounds is None:
        return

    lower, upper = bounds

    if value < lower:
        log_data_issue(
            ticker,
            "validation_error",
            f"{metric_name} = {value:.4f} below lower bound ({lower})"
        )
    elif value > upper:
        log_data_issue(
            ticker,
            "validation_error",
            f"{metric_name} = {value:.4f} exceeds upper bound ({upper})"
        )


# ==================== DEBT-TO-EQUITY RATIO ====================

def calculate_debt_to_equity(balance_sheet: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Calculate Debt-to-Equity ratio.

    Formula:
        D/E = Total Debt / Total Equity

    Args:
        balance_sheet: Balance sheet DataFrame

    Returns:
        D/E ratio as a decimal or None if calculation fails
    """
    if balance_sheet is None or balance_sheet.empty:
        return None

    try:
        balance = balance_sheet.iloc[:, 0]

        total_debt = _extract_value(balance, [
            'Total Debt', 'Long Term Debt', 'Net Debt'
        ])
        total_equity = _extract_value(balance, [
            'Stockholders Equity', 'Total Equity Gross Minority Interest',
            'Total Stockholder Equity'
        ])

        if total_debt is None or total_equity is None:
            return None

        if total_equity == 0 or total_equity < 0:
            return 999.0  # Distressed company marker (will be filtered out)

        return total_debt / total_equity

    except Exception:
        return None


# ==================== FREE CASH FLOW VALIDATION ====================

def has_positive_fcf_3y(cashflow_statement: Optional[pd.DataFrame]) -> bool:
    """
    Check if Free Cash Flow is positive for each of the last 3 years.

    Args:
        cashflow_statement: Cash flow statement DataFrame (columns = fiscal years)

    Returns:
        True if FCF > 0 for all 3 years, False otherwise
    """
    if cashflow_statement is None or cashflow_statement.empty:
        return False

    try:
        # Get Free Cash Flow row
        fcf_keys = ['Free Cash Flow', 'FreeCashFlow']
        fcf_row = None

        for key in fcf_keys:
            if key in cashflow_statement.index:
                fcf_row = cashflow_statement.loc[key]
                break

        if fcf_row is None:
            return False

        # Get last 3 years (most recent 3 columns)
        fcf_3y = fcf_row.iloc[:3]

        # Check if all 3 years are positive
        return (fcf_3y > 0).all()

    except Exception:
        return False


def get_ttm_fcf(data: dict) -> Optional[float]:
    """
    Get trailing twelve months (TTM) Free Cash Flow from .info dict.

    Args:
        data: yfinance .info dictionary

    Returns:
        FCF value or None
    """
    fcf = data.get('freeCashflow')

    if fcf is None or pd.isna(fcf):
        return None

    return float(fcf)


# ==================== PRICE DISCOUNT METRICS ====================

def calculate_distance_from_high(data: dict) -> Optional[float]:
    """
    Calculate percentage distance from 52-week high.

    Formula:
        Distance = ((Current Price - 52w High) / 52w High) × 100

    Args:
        data: Dictionary with currentPrice and fiftyTwoWeekHigh

    Returns:
        Percentage (negative value, e.g., -35.5 for 35.5% below high) or None
    """
    current_price = data.get('currentPrice')
    week_52_high = data.get('fiftyTwoWeekHigh')

    if current_price is None or week_52_high is None:
        return None

    if week_52_high == 0:
        return None

    distance = ((current_price - week_52_high) / week_52_high) * 100

    return distance


def calculate_distance_from_low(data: dict) -> Optional[float]:
    """
    Calculate percentage distance from 52-week low.

    Formula:
        Distance = ((Current Price - 52w Low) / 52w Low) × 100

    Args:
        data: Dictionary with currentPrice and fiftyTwoWeekLow

    Returns:
        Percentage (positive value, e.g., 8.5 for 8.5% above low) or None
    """
    current_price = data.get('currentPrice')
    week_52_low = data.get('fiftyTwoWeekLow')

    if current_price is None or week_52_low is None:
        return None

    if week_52_low == 0:
        return None

    distance = ((current_price - week_52_low) / week_52_low) * 100

    return distance


def is_near_52w_low(data: dict, threshold_pct: float = 10.0) -> bool:
    """
    Check if current price is within threshold % of 52-week low.

    Default threshold: 10% (Buy-the-Dip filter)

    Args:
        data: Dictionary with currentPrice and fiftyTwoWeekLow
        threshold_pct: Percentage threshold (default 10%)

    Returns:
        True if price <= 52w_low * (1 + threshold/100)
    """
    current_price = data.get('currentPrice')
    week_52_low = data.get('fiftyTwoWeekLow')

    if current_price is None or week_52_low is None:
        return False

    threshold_price = week_52_low * (1 + threshold_pct / 100)

    return current_price <= threshold_price


# ==================== VALUE SCORE (RANKING) ====================

def calculate_value_score(
    roic: Optional[float],
    distance_from_high: Optional[float],
    roic_weight: float = 0.6,
    discount_weight: float = 0.4
) -> Optional[float]:
    """
    Calculate composite Value Score for ranking.

    Formula:
        Value Score = (ROIC_normalized × roic_weight) + (Discount_Factor × discount_weight)

    Where:
        ROIC_normalized = ROIC / 0.15  (15% baseline)
        Discount_Factor = abs(Distance from High) / 100

    Args:
        roic: ROIC as decimal (e.g., 0.25 for 25%)
        distance_from_high: Distance from high as % (e.g., -40.0 for 40% drop)
        roic_weight: Weight for ROIC component (default 0.6 = 60%)
        discount_weight: Weight for discount component (default 0.4 = 40%)

    Returns:
        Value Score (higher is better) or None if calculation fails

    Example:
        ROIC = 25%, Distance from High = -40%
        Value Score = (25/15 × 0.6) + (40/100 × 0.4)
                    = (1.67 × 0.6) + (0.4 × 0.4)
                    = 1.0 + 0.16 = 1.16
    """
    if roic is None or distance_from_high is None:
        return None

    # Normalize ROIC (15% is baseline = 1.0)
    roic_normalized = roic / 0.15

    # Convert distance from high to discount factor (positive value)
    discount_factor = abs(distance_from_high) / 100

    # Calculate weighted score
    value_score = (roic_normalized * roic_weight) + (discount_factor * discount_weight)

    return value_score


# ==================== TREND & DEEP DIVE METRICS ====================

def calculate_roic_trend(
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
    years: int = 3
) -> List[Dict[str, Any]]:
    """
    Calculate ROIC for the last N fiscal years.

    Args:
        income_statement: Income statement DataFrame (columns = fiscal years)
        balance_sheet: Balance sheet DataFrame (columns = fiscal years)
        years: Number of years to compute (default 3)

    Returns:
        List of dicts sorted chronologically (oldest first):
        [{"year": "2022", "roic": 0.18}, {"year": "2023", "roic": 0.20}, ...]
        Empty list if calculation fails.
    """
    if income_statement is None or balance_sheet is None:
        return []

    num_years = min(years, income_statement.shape[1], balance_sheet.shape[1])
    trend = []

    for i in range(num_years):
        try:
            year_label = str(income_statement.columns[i].year)
        except AttributeError:
            year_label = str(income_statement.columns[i])

        roic = calculate_roic_for_year(income_statement, balance_sheet, year_index=i)
        trend.append({"year": year_label, "roic": roic})

    # Reverse to chronological order (oldest first)
    trend.reverse()
    return trend


def calculate_fcf_trend(
    cashflow_statement: Optional[pd.DataFrame],
    years: int = 3
) -> List[Dict[str, Any]]:
    """
    Extract Free Cash Flow for the last N fiscal years.

    Args:
        cashflow_statement: Cash flow statement DataFrame (columns = fiscal years)
        years: Number of years to extract (default 3)

    Returns:
        List of dicts sorted chronologically (oldest first):
        [{"year": "2022", "fcf": 5000000000}, ...]
        Empty list if extraction fails.
    """
    if cashflow_statement is None or cashflow_statement.empty:
        return []

    try:
        fcf_keys = ['Free Cash Flow', 'FreeCashFlow']
        fcf_row = None

        for key in fcf_keys:
            if key in cashflow_statement.index:
                fcf_row = cashflow_statement.loc[key]
                break

        if fcf_row is None:
            return []

        num_years = min(years, len(fcf_row))
        trend = []

        for i in range(num_years):
            try:
                year_label = str(cashflow_statement.columns[i].year)
            except AttributeError:
                year_label = str(cashflow_statement.columns[i])

            val = fcf_row.iloc[i]
            fcf_val = float(val) if pd.notna(val) else None
            trend.append({"year": year_label, "fcf": fcf_val})

        trend.reverse()
        return trend

    except Exception:
        return []


def calculate_normalized_pe(
    data: dict,
    income_statement: Optional[pd.DataFrame]
) -> Dict[str, Optional[float]]:
    """
    Calculate current P/E and normalized (3-year average) P/E for mean reversion analysis.

    Args:
        data: yfinance .info dictionary (needs trailingPE, currentPrice, sharesOutstanding)
        income_statement: Income statement DataFrame for historical Net Income

    Returns:
        {
            "current_pe": float or None,
            "normalized_pe": float or None,
            "pe_premium_pct": float or None  # (current/normalized - 1) * 100
        }
    """
    result: Dict[str, Optional[float]] = {
        "current_pe": None,
        "normalized_pe": None,
        "pe_premium_pct": None
    }

    # Current P/E from .info
    current_pe = data.get('trailingPE')
    if current_pe is not None and not pd.isna(current_pe) and current_pe > 0:
        result["current_pe"] = float(current_pe)

    # Normalized P/E from 3-year average earnings
    current_price = data.get('currentPrice')
    shares_outstanding = data.get('sharesOutstanding')

    if income_statement is None or current_price is None or shares_outstanding is None:
        return result
    if shares_outstanding <= 0:
        return result

    # Extract Net Income for last 3 years
    net_income_keys = ['Net Income', 'Net Income Common Stockholders']
    net_incomes: List[float] = []

    for key in net_income_keys:
        if key in income_statement.index:
            row = income_statement.loc[key]
            for i in range(min(3, len(row))):
                val = row.iloc[i]
                if pd.notna(val) and val != 0:
                    net_incomes.append(float(val))
            break

    if len(net_incomes) >= 2:
        avg_net_income = sum(net_incomes) / len(net_incomes)
        avg_eps = avg_net_income / shares_outstanding
        if avg_eps > 0:
            result["normalized_pe"] = current_price / avg_eps

    # Calculate premium/discount
    if result["current_pe"] is not None and result["normalized_pe"] is not None:
        result["pe_premium_pct"] = (
            (result["current_pe"] / result["normalized_pe"]) - 1
        ) * 100

    return result


def calculate_bollinger_bands(
    price_df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands from historical price data.

    Args:
        price_df: DataFrame with 'Close' column (from fetch_historical_prices)
        window: Moving average window in days (default 20)
        num_std: Number of standard deviations for bands (default 2.0)

    Returns:
        DataFrame with columns: Close, SMA_20, BB_Upper, BB_Lower
    """
    close = price_df['Close']
    sma = close.rolling(window=window, min_periods=window).mean()
    rolling_std = close.rolling(window=window, min_periods=window).std()

    return pd.DataFrame({
        'Open': price_df['Open'] if 'Open' in price_df.columns else close,
        'High': price_df['High'] if 'High' in price_df.columns else close,
        'Low': price_df['Low'] if 'Low' in price_df.columns else close,
        'Close': close,
        'SMA_20': sma,
        'BB_Upper': sma + (num_std * rolling_std),
        'BB_Lower': sma - (num_std * rolling_std),
    }, index=price_df.index)


# ==================== EARNINGS QUALITY SCORE ====================

def _score_accrual_ratio(ratio: float) -> float:
    """
    Score accrual ratio on 0-100 scale. Lower accrual ratio = better.

    Accrual ratio = (Net Income - Operating Cash Flow) / Total Assets.
    Low/negative means cash generation backs reported income.
    High means income exceeds actual cash — potential manipulation.

    Scoring:
        <= -0.10 → 100 (excellent: cash well exceeds income)
        >= +0.20 → 0   (poor: income far exceeds cash)
        Linear interpolation between.
    """
    if ratio <= -0.10:
        return 100.0
    if ratio >= 0.20:
        return 0.0
    return max(0.0, min(100.0, (0.20 - ratio) / 0.30 * 100.0))


def _score_fcf_to_ni(ratio: float) -> float:
    """
    Score FCF-to-Net-Income ratio on 0-100 scale. Higher = better.

    FCF/NI > 1.0 means free cash flow exceeds reported profit (gold standard).

    Scoring:
        >= 1.50 → 100 (exceptional cash conversion)
        <= 0.00 → 0   (negative FCF despite positive income)
        Linear interpolation between.
    """
    if ratio >= 1.50:
        return 100.0
    if ratio <= 0.0:
        return 0.0
    return max(0.0, min(100.0, ratio / 1.50 * 100.0))


def _score_rev_rec_divergence(divergence: float) -> float:
    """
    Score revenue vs receivables growth divergence on 0-100 scale.

    Divergence = Revenue growth - Receivables growth.
    Positive means revenue growing faster than receivables (healthy).
    Negative means receivables outpacing revenue (red flag).

    Scoring:
        >= +0.10 → 100 (revenue growing 10%+ faster)
        <= -0.10 → 0   (receivables growing 10%+ faster)
        Linear interpolation between.
    """
    if divergence >= 0.10:
        return 100.0
    if divergence <= -0.10:
        return 0.0
    return max(0.0, min(100.0, (divergence + 0.10) / 0.20 * 100.0))


def calculate_earnings_quality(data: dict) -> Dict[str, Optional[float]]:
    """
    Calculate Earnings Quality Score from three sub-metrics.

    Sub-metrics:
        1. Accrual Ratio: (Net Income - Operating Cash Flow) / Total Assets
        2. FCF-to-NI Ratio: Free Cash Flow / Net Income
        3. Rev/Rec Divergence: Revenue growth - Receivables growth

    Composite score is the weighted average of available sub-scores (0-100).
    Weights from config: accrual 40%, FCF/NI 35%, rev/rec divergence 25%.

    Args:
        data: Complete stock data dict (from fetch_deep_data)

    Returns:
        Dict with raw values and composite score:
        {
            "accrual_ratio": float or None,
            "fcf_to_ni_ratio": float or None,
            "rev_rec_divergence": float or None,
            "earnings_quality_score": float (0-100) or None,
        }
    """
    result: Dict[str, Optional[float]] = {
        "accrual_ratio": None,
        "fcf_to_ni_ratio": None,
        "rev_rec_divergence": None,
        "earnings_quality_score": None,
    }

    income_stmt = data.get('income_statement')
    balance_sheet = data.get('balance_sheet')
    cashflow_stmt = data.get('cashflow_statement')

    # ---- Sub-metric 1: Accrual Ratio ----
    accrual_ratio = _compute_accrual_ratio(income_stmt, cashflow_stmt, balance_sheet)
    result["accrual_ratio"] = accrual_ratio

    # ---- Sub-metric 2: FCF-to-Net-Income Ratio ----
    fcf_to_ni = _compute_fcf_to_ni_ratio(income_stmt, cashflow_stmt)
    result["fcf_to_ni_ratio"] = fcf_to_ni

    # ---- Sub-metric 3: Revenue vs Receivables Growth Divergence ----
    rev_rec_div = _compute_rev_rec_divergence(income_stmt, balance_sheet)
    result["rev_rec_divergence"] = rev_rec_div

    # ---- Composite Score (weighted average of available sub-scores) ----
    weights = EARNINGS_QUALITY_WEIGHTS
    sub_scores = []
    total_weight = 0.0

    if accrual_ratio is not None:
        sub_scores.append(_score_accrual_ratio(accrual_ratio) * weights["accrual_ratio"])
        total_weight += weights["accrual_ratio"]

    if fcf_to_ni is not None:
        sub_scores.append(_score_fcf_to_ni(fcf_to_ni) * weights["fcf_to_ni"])
        total_weight += weights["fcf_to_ni"]

    if rev_rec_div is not None:
        sub_scores.append(_score_rev_rec_divergence(rev_rec_div) * weights["rev_rec_divergence"])
        total_weight += weights["rev_rec_divergence"]

    if total_weight > 0:
        result["earnings_quality_score"] = round(sum(sub_scores) / total_weight, 1)

    return result


def _compute_accrual_ratio(
    income_stmt: Optional[pd.DataFrame],
    cashflow_stmt: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
) -> Optional[float]:
    """Compute (Net Income - Operating Cash Flow) / Total Assets for most recent year."""
    if income_stmt is None or cashflow_stmt is None or balance_sheet is None:
        return None
    if income_stmt.empty or cashflow_stmt.empty or balance_sheet.empty:
        return None

    try:
        income = income_stmt.iloc[:, 0]
        cashflow = cashflow_stmt.iloc[:, 0]
        balance = balance_sheet.iloc[:, 0]

        net_income = _extract_value(income, [
            'Net Income', 'Net Income Common Stockholders'
        ])
        operating_cf = _extract_value(cashflow, [
            'Operating Cash Flow', 'Cash Flow From Continuing Operating Activities',
            'Total Cash From Operating Activities'
        ])
        total_assets = _extract_value(balance, ['Total Assets'])

        if net_income is None or operating_cf is None or total_assets is None:
            return None
        if total_assets <= 0:
            return None

        return (net_income - operating_cf) / total_assets
    except Exception:
        return None


def _compute_fcf_to_ni_ratio(
    income_stmt: Optional[pd.DataFrame],
    cashflow_stmt: Optional[pd.DataFrame],
) -> Optional[float]:
    """Compute Free Cash Flow / Net Income for most recent year."""
    if income_stmt is None or cashflow_stmt is None:
        return None
    if income_stmt.empty or cashflow_stmt.empty:
        return None

    try:
        income = income_stmt.iloc[:, 0]
        cashflow = cashflow_stmt.iloc[:, 0]

        net_income = _extract_value(income, [
            'Net Income', 'Net Income Common Stockholders'
        ])
        fcf = _extract_value(cashflow, ['Free Cash Flow', 'FreeCashFlow'])

        if net_income is None or fcf is None:
            return None
        if net_income <= 0:
            return None  # Ratio meaningless for loss-making companies

        return fcf / net_income
    except Exception:
        return None


def _compute_rev_rec_divergence(
    income_stmt: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
) -> Optional[float]:
    """Compute Revenue growth - Receivables growth (YoY) for most recent year."""
    if income_stmt is None or balance_sheet is None:
        return None
    if income_stmt.empty or balance_sheet.empty:
        return None
    if income_stmt.shape[1] < 2 or balance_sheet.shape[1] < 2:
        return None  # Need at least 2 years for growth calculation

    try:
        income_y0 = income_stmt.iloc[:, 0]
        income_y1 = income_stmt.iloc[:, 1]
        balance_y0 = balance_sheet.iloc[:, 0]
        balance_y1 = balance_sheet.iloc[:, 1]

        revenue_y0 = _extract_value(income_y0, [
            'Total Revenue', 'Revenue', 'Net Revenue'
        ])
        revenue_y1 = _extract_value(income_y1, [
            'Total Revenue', 'Revenue', 'Net Revenue'
        ])
        receivable_y0 = _extract_value(balance_y0, [
            'Accounts Receivable', 'Net Receivable', 'Receivables',
            'Gross Accounts Receivable'
        ])
        receivable_y1 = _extract_value(balance_y1, [
            'Accounts Receivable', 'Net Receivable', 'Receivables',
            'Gross Accounts Receivable'
        ])

        if revenue_y0 is None or revenue_y1 is None:
            return None
        if receivable_y0 is None or receivable_y1 is None:
            return None
        if revenue_y1 <= 0 or receivable_y1 <= 0:
            return None

        revenue_growth = (revenue_y0 - revenue_y1) / abs(revenue_y1)
        receivable_growth = (receivable_y0 - receivable_y1) / abs(receivable_y1)

        return revenue_growth - receivable_growth
    except Exception:
        return None


# ==================== MOMENTUM INDICATORS ====================

def calculate_rsi(
    price_df: pd.DataFrame,
    period: int = RSI_PERIOD,
) -> Optional[float]:
    """
    Calculate the current RSI (Relative Strength Index) value.

    Uses Wilder's smoothing method (exponential moving average).

    Args:
        price_df: DataFrame with 'Close' column
        period: Lookback period in days (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if price_df is None or price_df.empty:
        return None

    close = price_df['Close']
    if len(close) < period + 1:
        return None

    try:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)

        # Wilder's smoothing (EMA with alpha = 1/period)
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        last_avg_gain = avg_gain.iloc[-1]
        last_avg_loss = avg_loss.iloc[-1]

        if last_avg_loss == 0:
            return 100.0 if last_avg_gain > 0 else 50.0

        rs = last_avg_gain / last_avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi)
    except Exception:
        return None


def calculate_macd(
    price_df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> Dict[str, Optional[float]]:
    """
    Calculate current MACD line, signal line, and histogram values.

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal)
    Histogram = MACD Line - Signal Line

    Args:
        price_df: DataFrame with 'Close' column
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Dict with macd_line, signal_line, histogram (or None values)
    """
    result: Dict[str, Optional[float]] = {
        "macd_line": None,
        "signal_line": None,
        "histogram": None,
    }

    if price_df is None or price_df.empty:
        return result

    close = price_df['Close']
    if len(close) < slow + signal:
        return result

    try:
        ema_fast = close.ewm(span=fast, min_periods=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, min_periods=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, min_periods=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        result["macd_line"] = float(macd_line.iloc[-1])
        result["signal_line"] = float(signal_line.iloc[-1])
        result["histogram"] = float(histogram.iloc[-1])
        return result
    except Exception:
        return result


def calculate_sma_crossover(
    price_df: pd.DataFrame,
    short: int = SMA_SHORT_PERIOD,
    long: int = SMA_LONG_PERIOD,
) -> Dict[str, Any]:
    """
    Calculate SMA values and golden/death cross status.

    Golden Cross: SMA(short) > SMA(long) — bullish signal.
    Death Cross: SMA(short) < SMA(long) — bearish signal.

    Args:
        price_df: DataFrame with 'Close' column
        short: Short SMA period (default 50)
        long: Long SMA period (default 200)

    Returns:
        Dict with sma_short, sma_long, price, golden_cross,
        price_above_short, price_above_long (None values if insufficient data)
    """
    result: Dict[str, Any] = {
        "sma_short": None,
        "sma_long": None,
        "price": None,
        "golden_cross": None,
        "price_above_short": None,
        "price_above_long": None,
    }

    if price_df is None or price_df.empty:
        return result

    close = price_df['Close']

    try:
        current_price = float(close.iloc[-1])
        result["price"] = current_price

        if len(close) >= short:
            sma_s = float(close.rolling(window=short).mean().iloc[-1])
            result["sma_short"] = sma_s
            result["price_above_short"] = current_price > sma_s

        if len(close) >= long:
            sma_l = float(close.rolling(window=long).mean().iloc[-1])
            result["sma_long"] = sma_l
            result["price_above_long"] = current_price > sma_l

        if result["sma_short"] is not None and result["sma_long"] is not None:
            result["golden_cross"] = result["sma_short"] > result["sma_long"]

        return result
    except Exception:
        return result


def _score_rsi(rsi: float) -> float:
    """
    Score RSI for value-investor momentum blend (0-100).

    Sweet spot: RSI 40-55 (recovering from oversold, emerging momentum).
    Penalizes overbought (>70) and deeply oversold (<20).

    Scoring:
        <= 20 → 20 (deeply oversold, no upward momentum yet)
        20→40 → linear 20→100 (recovery zone)
        40→55 → 100 (ideal value entry)
        55→80 → linear 100→0 (increasingly overbought)
        >= 80 → 0 (overbought, avoid)
    """
    if rsi <= 20:
        return 20.0
    if rsi <= 40:
        return 20.0 + (rsi - 20.0) / 20.0 * 80.0
    if rsi <= 55:
        return 100.0
    if rsi <= 80:
        return 100.0 - (rsi - 55.0) / 25.0 * 100.0
    return 0.0


def _score_macd(histogram: float, price: float) -> float:
    """
    Score MACD histogram normalized to price (0-100).

    Normalizes histogram as % of price, then maps [-2%, +2%] to [0, 100].
    Bullish (positive histogram) → score > 50.
    Bearish (negative histogram) → score < 50.
    """
    if price <= 0:
        return 50.0

    ratio = histogram / price
    # Map [-0.02, +0.02] to [0, 100]
    score = (ratio + 0.02) / 0.04 * 100.0
    return max(0.0, min(100.0, score))


def _score_sma(
    price: float,
    sma_short: Optional[float],
    sma_long: Optional[float],
) -> float:
    """
    Score SMA crossover status (0-100).

    +30 points if price > SMA50 (short-term uptrend)
    +30 points if price > SMA200 (long-term uptrend)
    +40 points if SMA50 > SMA200 (golden cross)
    """
    score = 0.0

    if sma_short is not None and price > sma_short:
        score += 30.0
    if sma_long is not None and price > sma_long:
        score += 30.0
    if sma_short is not None and sma_long is not None and sma_short > sma_long:
        score += 40.0

    return score


def calculate_momentum_score(
    price_df: pd.DataFrame,
) -> Dict[str, Optional[float]]:
    """
    Compute RSI, MACD, SMA indicators and composite momentum score (0-100).

    Composite is weighted average of available sub-scores:
    RSI 35%, MACD 35%, SMA 30% (from config).

    Args:
        price_df: DataFrame with 'Close' column (ideally 2y of data)

    Returns:
        Dict with raw indicator values and composite momentum_score:
        {
            "rsi": float or None,
            "macd_histogram": float or None,
            "sma_short": float or None,
            "sma_long": float or None,
            "golden_cross": bool or None,
            "momentum_score": float (0-100) or None,
        }
    """
    result: Dict[str, Optional[float]] = {
        "rsi": None,
        "macd_histogram": None,
        "sma_short": None,
        "sma_long": None,
        "golden_cross": None,
        "momentum_score": None,
    }

    if price_df is None or price_df.empty:
        return result

    # Compute raw indicators
    rsi = calculate_rsi(price_df)
    result["rsi"] = rsi

    macd_data = calculate_macd(price_df)
    result["macd_histogram"] = macd_data.get("histogram")

    sma_data = calculate_sma_crossover(price_df)
    result["sma_short"] = sma_data.get("sma_short")
    result["sma_long"] = sma_data.get("sma_long")
    result["golden_cross"] = sma_data.get("golden_cross")

    # Score each component
    weights = MOMENTUM_WEIGHTS
    sub_scores: List[float] = []
    total_weight = 0.0

    if rsi is not None:
        sub_scores.append(_score_rsi(rsi) * weights["rsi"])
        total_weight += weights["rsi"]

    histogram = macd_data.get("histogram")
    price = sma_data.get("price")
    if histogram is not None and price is not None and price > 0:
        sub_scores.append(_score_macd(histogram, price) * weights["macd"])
        total_weight += weights["macd"]

    sma_s = sma_data.get("sma_short")
    sma_l = sma_data.get("sma_long")
    if price is not None and (sma_s is not None or sma_l is not None):
        sub_scores.append(_score_sma(price, sma_s, sma_l) * weights["sma"])
        total_weight += weights["sma"]

    if total_weight > 0:
        result["momentum_score"] = round(sum(sub_scores) / total_weight, 1)

    return result


def calculate_momentum_indicators(
    price_df: pd.DataFrame,
) -> Optional[pd.DataFrame]:
    """
    Compute full time-series momentum indicators for chart overlays.

    Returns DataFrame with columns:
    RSI, MACD, MACD_Signal, MACD_Histogram, SMA_50, SMA_200

    Args:
        price_df: DataFrame with 'Close' column (ideally 2y of data)

    Returns:
        DataFrame with indicator columns, or None if insufficient data
    """
    if price_df is None or price_df.empty:
        return None

    close = price_df['Close']
    if len(close) < MACD_SLOW + MACD_SIGNAL:
        return None

    try:
        result = pd.DataFrame(index=price_df.index)

        # RSI time series
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1.0 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        result['RSI'] = 100.0 - (100.0 / (1.0 + rs))

        # MACD time series
        ema_fast = close.ewm(span=MACD_FAST, min_periods=MACD_FAST, adjust=False).mean()
        ema_slow = close.ewm(span=MACD_SLOW, min_periods=MACD_SLOW, adjust=False).mean()
        result['MACD'] = ema_fast - ema_slow
        result['MACD_Signal'] = result['MACD'].ewm(
            span=MACD_SIGNAL, min_periods=MACD_SIGNAL, adjust=False
        ).mean()
        result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']

        # SMA time series
        if len(close) >= SMA_SHORT_PERIOD:
            result['SMA_50'] = close.rolling(window=SMA_SHORT_PERIOD).mean()
        if len(close) >= SMA_LONG_PERIOD:
            result['SMA_200'] = close.rolling(window=SMA_LONG_PERIOD).mean()

        return result
    except Exception:
        return None


# ==================== DATA CONFIDENCE ASSESSMENT ====================

def calculate_data_confidence(data: dict) -> str:
    """
    Assess data completeness for a stock and return a confidence level.

    Criteria:
        High:   All 3 financial statements present, each with 3+ years, beta available
        Medium: All 3 statements present but missing beta or any statement has < 3 years
        Low:    Any financial statement missing entirely

    Args:
        data: Complete stock data dict (from fetch_deep_data)

    Returns:
        "High", "Medium", or "Low"
    """
    income_stmt = data.get('income_statement')
    balance_sheet = data.get('balance_sheet')
    cashflow_stmt = data.get('cashflow_statement')

    has_income = income_stmt is not None and not income_stmt.empty
    has_balance = balance_sheet is not None and not balance_sheet.empty
    has_cashflow = cashflow_stmt is not None and not cashflow_stmt.empty

    if not (has_income and has_balance and has_cashflow):
        return "Low"

    income_years = income_stmt.shape[1]
    balance_years = balance_sheet.shape[1]
    cashflow_years = cashflow_stmt.shape[1]
    all_3y = income_years >= 3 and balance_years >= 3 and cashflow_years >= 3

    beta = data.get('beta')
    has_beta = beta is not None and not pd.isna(beta)

    if all_3y and has_beta:
        return "High"

    return "Medium"


# ==================== HELPER: CALCULATE ALL METRICS ====================

def calculate_all_metrics(data: dict) -> dict:
    """
    Calculate all metrics for a stock and return as dictionary.

    This is a convenience function that computes all metrics at once.

    Args:
        data: Complete stock data (from fetch_deep_data)

    Returns:
        Dictionary with all calculated metrics
    """
    # Extract financial statements
    income_stmt = data.get('income_statement')
    balance_sheet = data.get('balance_sheet')
    cashflow_stmt = data.get('cashflow_statement')

    ticker = data.get('symbol', data.get('ticker', 'UNKNOWN'))

    # Calculate fundamental metrics
    roic = calculate_roic(income_stmt, balance_sheet)
    debt_to_equity = calculate_debt_to_equity(balance_sheet)
    fcf_3y_positive = has_positive_fcf_3y(cashflow_stmt)
    ttm_fcf = get_ttm_fcf(data)

    # Calculate price metrics
    distance_from_high = calculate_distance_from_high(data)
    distance_from_low = calculate_distance_from_low(data)
    near_low = is_near_52w_low(data, threshold_pct=10.0)

    # Validate computed metrics against sanity bounds
    validate_metric_bounds(ticker, "roic", roic)
    validate_metric_bounds(ticker, "debt_to_equity", debt_to_equity)

    # Validate trailing P/E from raw data (not computed, but worth flagging)
    trailing_pe = data.get('trailingPE')
    if trailing_pe is not None and not pd.isna(trailing_pe):
        validate_metric_bounds(ticker, "trailing_pe", float(trailing_pe))

    # Assess data completeness
    confidence = calculate_data_confidence(data)

    # Calculate earnings quality score
    eq = calculate_earnings_quality(data)
    earnings_quality_score = eq.get("earnings_quality_score")

    # value_score is computed post-filtering in screener.py via rank-percentile
    # normalization (requires full universe context, not per-stock)

    return {
        'roic': roic,
        'debt_to_equity': debt_to_equity,
        'fcf_3y_positive': fcf_3y_positive,
        'ttm_fcf': ttm_fcf,
        'distance_from_high': distance_from_high,
        'distance_from_low': distance_from_low,
        'near_52w_low': near_low,
        'value_score': None,
        'confidence': confidence,
        'earnings_quality_score': earnings_quality_score,
    }
