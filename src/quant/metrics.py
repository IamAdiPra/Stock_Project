"""
Financial metrics calculation module.
Pure functions that compute ROIC, FCF, D/E, and valuation metrics from raw data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


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

        if invested_capital == 0 or invested_capital < 0:
            return None

        roic = nopat / invested_capital

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

    # Calculate fundamental metrics
    roic = calculate_roic(income_stmt, balance_sheet)
    debt_to_equity = calculate_debt_to_equity(balance_sheet)
    fcf_3y_positive = has_positive_fcf_3y(cashflow_stmt)
    ttm_fcf = get_ttm_fcf(data)

    # Calculate price metrics
    distance_from_high = calculate_distance_from_high(data)
    distance_from_low = calculate_distance_from_low(data)
    near_low = is_near_52w_low(data, threshold_pct=10.0)

    # Calculate value score
    value_score = calculate_value_score(roic, distance_from_high)

    return {
        'roic': roic,
        'debt_to_equity': debt_to_equity,
        'fcf_3y_positive': fcf_3y_positive,
        'ttm_fcf': ttm_fcf,
        'distance_from_high': distance_from_high,
        'distance_from_low': distance_from_low,
        'near_52w_low': near_low,
        'value_score': value_score
    }
