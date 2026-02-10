"""
Data validation and quality checks for fetched financial data.
Ensures minimum data completeness before passing to quant layer.
"""

from typing import Optional, List
from src.utils.logger import log_data_issue
from src.utils.config import MIN_DATA_COMPLETENESS


# Critical fields required for screening
REQUIRED_FUNDAMENTAL_FIELDS = [
    'marketCap',
    'totalRevenue',
    'freeCashflow',
    'totalDebt',
    'totalAssets',
]

REQUIRED_PRICE_FIELDS = [
    'currentPrice',
    'fiftyTwoWeekHigh',
    'fiftyTwoWeekLow',
]


def validate_data_completeness(
    data: dict,
    required_fields: List[str],
    ticker: str
) -> bool:
    """
    Check if data contains minimum required fields.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        ticker: Ticker symbol (for error logging)

    Returns:
        True if data passes validation, False otherwise
    """
    if not data:
        log_data_issue(
            ticker=ticker,
            issue_type="validation_error",
            error_message="Data dictionary is empty"
        )
        return False

    missing_fields = [field for field in required_fields if field not in data or data[field] is None]

    if missing_fields:
        completeness = 1 - (len(missing_fields) / len(required_fields))

        if completeness < MIN_DATA_COMPLETENESS:
            log_data_issue(
                ticker=ticker,
                issue_type="incomplete_data",
                error_message=f"Missing critical fields: {', '.join(missing_fields)}"
            )
            return False

    return True


def validate_fundamental_data(data: Optional[dict], ticker: str) -> bool:
    """
    Validate fundamental data quality.

    Args:
        data: Fundamental data dictionary
        ticker: Ticker symbol

    Returns:
        True if data is valid for screening
    """
    if data is None:
        return False

    return validate_data_completeness(data, REQUIRED_FUNDAMENTAL_FIELDS, ticker)


def validate_price_data(data: Optional[dict], ticker: str) -> bool:
    """
    Validate price data quality.

    Args:
        data: Price data dictionary
        ticker: Ticker symbol

    Returns:
        True if data is valid for analysis
    """
    if data is None:
        return False

    return validate_data_completeness(data, REQUIRED_PRICE_FIELDS, ticker)


def sanitize_numeric_value(value: any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def clean_financial_data(data: dict) -> dict:
    """
    Clean and normalize financial data dictionary.

    Handles:
    - None values
    - String numbers ("1.5B" -> 1500000000)
    - Percentage formatting

    Args:
        data: Raw data dictionary

    Returns:
        Cleaned data dictionary
    """
    cleaned = data.copy()

    # Common fields that should be numeric
    numeric_fields = [
        'marketCap', 'totalRevenue', 'freeCashflow', 'totalDebt',
        'totalAssets', 'currentPrice', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
        'returnOnEquity', 'returnOnAssets', 'profitMargins'
    ]

    for field in numeric_fields:
        if field in cleaned:
            cleaned[field] = sanitize_numeric_value(cleaned[field])

    return cleaned
