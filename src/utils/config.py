"""
Application-wide configuration constants.
Defines cache durations, API settings, and screening thresholds.
"""

from typing import Final, Dict

# ==================== CACHE CONFIGURATION ====================
# Cache TTL (Time To Live) in seconds

FUNDAMENTAL_DATA_TTL: Final[int] = 86400  # 24 hours (60*60*24)
PRICE_DATA_TTL: Final[int] = 3600          # 1 hour (60*60)

# ==================== API CONFIGURATION ====================

# yfinance retry configuration
MAX_RETRIES: Final[int] = 3
RETRY_DELAY: Final[float] = 2.0  # seconds between retries

# API timeout
API_TIMEOUT: Final[int] = 10  # seconds

# ==================== MARKET CONFIGURATION ====================

# Ticker suffix mapping for different exchanges
EXCHANGE_SUFFIXES: Final[Dict[str, str]] = {
    "NSE": ".NS",      # National Stock Exchange of India
    "BSE": ".BO",      # Bombay Stock Exchange
    "NYSE": "",        # New York Stock Exchange
    "NASDAQ": "",      # NASDAQ
}

# ==================== CURRENCY CONFIGURATION ====================

CURRENCY_CONFIG: Final[Dict[str, Dict[str, str]]] = {
    "NIFTY100": {"symbol": "\u20b9", "code": "INR"},
    "SP500": {"symbol": "$", "code": "USD"},
}

# ==================== DUE DILIGENCE LINKS ====================

DUE_DILIGENCE_URLS: Final[Dict[str, Dict[str, str]]] = {
    "NIFTY100": {
        "Yahoo Finance": "https://finance.yahoo.com/quote/{ticker}.NS",
        "Screener.in": "https://www.screener.in/company/{ticker}/consolidated/",
    },
    "SP500": {
        "Yahoo Finance": "https://finance.yahoo.com/quote/{ticker}",
    },
}


def get_currency_symbol(index: str) -> str:
    """Return currency symbol for a given index ('$' or '\u20b9')."""
    return CURRENCY_CONFIG.get(index, CURRENCY_CONFIG["SP500"])["symbol"]


# ==================== SCREENING THRESHOLDS ====================
# Default values for quality filters

MIN_ROIC: Final[float] = 0.12           # 12% minimum ROIC
MIN_FCF_YIELD: Final[float] = 0.05      # 5% minimum FCF yield
MAX_DEBT_EQUITY: Final[float] = 1.0     # Maximum D/E ratio
MIN_MARKET_CAP: Final[int] = 1_000_000_000  # $1B or ₹1000 Cr

# ==================== UI CONFIGURATION ====================

# Number of stocks to display in results
DEFAULT_RESULT_LIMIT: Final[int] = 25

# Chart color scheme
CHART_COLOR_POSITIVE: Final[str] = "#00CC96"  # Green
CHART_COLOR_NEGATIVE: Final[str] = "#EF553B"  # Red
CHART_COLOR_NEUTRAL: Final[str] = "#636EFA"   # Blue

# ==================== DATA QUALITY ====================

# Minimum required data completeness
MIN_DATA_COMPLETENESS: Final[float] = 0.7  # 70% of fields must be non-null
