"""
Application-wide configuration constants.
Defines cache durations, API settings, and screening thresholds.
"""

from typing import Final, Dict, Tuple

# ==================== CACHE CONFIGURATION ====================
# Cache TTL (Time To Live) in seconds

FUNDAMENTAL_DATA_TTL: Final[int] = 86400  # 24 hours (60*60*24)
PRICE_DATA_TTL: Final[int] = 3600          # 1 hour (60*60)

# ==================== API CONFIGURATION ====================

# yfinance retry configuration
MAX_RETRIES: Final[int] = 3
RETRY_DELAY: Final[float] = 2.0  # seconds between retries

# Rate limit handling (Yahoo Finance throttling)
RATE_LIMIT_MAX_RETRIES: Final[int] = 5
RATE_LIMIT_BASE_DELAY: Final[float] = 5.0  # seconds, doubles each retry (5, 10, 20, 40, 80)

# API timeout
API_TIMEOUT: Final[int] = 10  # seconds

# ==================== MARKET CONFIGURATION ====================

# Ticker suffix mapping for different exchanges
EXCHANGE_SUFFIXES: Final[Dict[str, str]] = {
    "NSE": ".NS",      # National Stock Exchange of India
    "BSE": ".BO",      # Bombay Stock Exchange
    "NYSE": "",        # New York Stock Exchange
    "NASDAQ": "",      # NASDAQ
    "LSE": ".L",       # London Stock Exchange
}

# ==================== CURRENCY CONFIGURATION ====================

CURRENCY_CONFIG: Final[Dict[str, Dict[str, str]]] = {
    "NIFTY100": {"symbol": "\u20b9", "code": "INR"},
    "SP500": {"symbol": "$", "code": "USD"},
    "FTSE100": {"symbol": "\u00a3", "code": "GBP"},
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
    "FTSE100": {
        "Yahoo Finance": "https://finance.yahoo.com/quote/{ticker}.L",
    },
}


def get_currency_symbol(index: str) -> str:
    """Return currency symbol for a given index ('$' or '\u20b9')."""
    return CURRENCY_CONFIG.get(index, CURRENCY_CONFIG["SP500"])["symbol"]


def convert_gbx_to_gbp(value: float, index: str) -> float:
    """
    Convert GBX (pence) to GBP (pounds) for FTSE100 stocks.

    Yahoo Finance returns LSE stock prices in pence (GBX) but we display in pounds (GBP).
    For non-FTSE indices, returns value unchanged.

    Args:
        value: Price or financial value (potentially in pence)
        index: Index identifier ("NIFTY100", "SP500", "FTSE100")

    Returns:
        Converted value (divided by 100 for FTSE100, unchanged otherwise)
    """
    if index == "FTSE100" and value is not None:
        return value / 100.0
    return value


# ==================== SCREENING THRESHOLDS ====================
# Default values for quality filters

MIN_ROIC: Final[float] = 0.12           # 12% minimum ROIC
ROIC_CAP: Final[float] = 1.0            # 100% cap — no sustainable business exceeds this
MIN_FCF_YIELD: Final[float] = 0.05      # 5% minimum FCF yield
MAX_DEBT_EQUITY: Final[float] = 1.0     # Maximum D/E ratio
MIN_MARKET_CAP: Final[int] = 1_000_000_000  # $1B or ₹1000 Cr

# Value Score component weights (must sum to 1.0)
VALUE_SCORE_ROIC_WEIGHT: Final[float] = 0.6    # 60% quality (ROIC rank-percentile)
VALUE_SCORE_DISCOUNT_WEIGHT: Final[float] = 0.4 # 40% price discount rank-percentile

# Earnings Quality Score component weights (must sum to 1.0)
EARNINGS_QUALITY_WEIGHTS: Final[Dict[str, float]] = {
    "accrual_ratio": 0.40,       # Most established academic signal (Sloan 1996)
    "fcf_to_ni": 0.35,           # Direct cash conversion check
    "rev_rec_divergence": 0.25,  # Supplementary red flag detector
}

# Metric sanity bounds: (min, max) — values outside flagged as suspect in Data Quality Report
METRIC_SANITY_BOUNDS: Final[Dict[str, Tuple[float, float]]] = {
    "roic":           (-0.50, 1.00),    # -50% to 100% (ROIC_CAP already enforces upper)
    "debt_to_equity": (0.0,   50.0),    # 0x to 50x
    "trailing_pe":    (0.0,   200.0),   # 0x to 200x (loss-making = negative = suspect)
    "fcf_cagr":       (-0.50, 2.00),    # -50% to 200%
}

# ==================== UI CONFIGURATION ====================

# Number of stocks to display in results
DEFAULT_RESULT_LIMIT: Final[int] = 25

# Chart color scheme (Midnight Finance palette)
CHART_COLOR_POSITIVE: Final[str] = "#10B981"  # Emerald green
CHART_COLOR_NEGATIVE: Final[str] = "#EF4444"  # Rose red
CHART_COLOR_NEUTRAL: Final[str] = "#6366F1"   # Indigo blue

# ==================== FORECASTING CONFIGURATION ====================

# Risk-free rates by market (approximate current government bond yields)
RISK_FREE_RATES: Final[Dict[str, float]] = {
    "NIFTY100": 0.070,   # India 10Y govt bond ~7.0%
    "SP500": 0.045,       # US 10Y Treasury ~4.5%
    "FTSE100": 0.045,     # UK 10Y Gilt ~4.5%
}

# Equity risk premiums by market
EQUITY_RISK_PREMIUMS: Final[Dict[str, float]] = {
    "NIFTY100": 0.075,    # India: higher country risk, emerging market premium
    "SP500": 0.050,        # US: Damodaran estimate ~5.0%
    "FTSE100": 0.055,      # UK: developed market, slightly above US (Brexit risk)
}

# Long-term average annual market returns (nominal)
MARKET_ANNUAL_RETURNS: Final[Dict[str, float]] = {
    "NIFTY100": 0.12,    # Nifty long-term ~12%
    "SP500": 0.10,        # S&P long-term ~10%
    "FTSE100": 0.08,      # FTSE long-term ~8%
}

# Terminal growth rates by market (long-term nominal GDP proxy)
TERMINAL_GROWTH_RATES: Final[Dict[str, float]] = {
    "NIFTY100": 0.05,     # India nominal GDP ~6-7%, conservative 5%
    "SP500": 0.03,         # US nominal GDP ~3-4%, standard 3%
    "FTSE100": 0.025,      # UK nominal GDP ~2-3%, conservative 2.5%
}


def get_terminal_growth_rate(index: str) -> float:
    """Return terminal growth rate for a given market index."""
    return TERMINAL_GROWTH_RATES.get(index, 0.03)


def get_equity_risk_premium(index: str) -> float:
    """Return equity risk premium for a given market index."""
    return EQUITY_RISK_PREMIUMS.get(index, 0.05)

# ==================== MOMENTUM CONFIGURATION ====================

# RSI (Relative Strength Index)
RSI_PERIOD: Final[int] = 14  # Standard Wilder RSI lookback

# MACD (Moving Average Convergence Divergence)
MACD_FAST: Final[int] = 12    # Fast EMA period
MACD_SLOW: Final[int] = 26    # Slow EMA period
MACD_SIGNAL: Final[int] = 9   # Signal line EMA period

# Simple Moving Averages
SMA_SHORT_PERIOD: Final[int] = 50   # Short-term trend
SMA_LONG_PERIOD: Final[int] = 200   # Long-term trend

# Momentum score component weights (must sum to 1.0)
MOMENTUM_WEIGHTS: Final[Dict[str, float]] = {
    "rsi": 0.35,    # Overbought/oversold signal
    "macd": 0.35,   # Trend strength and direction
    "sma": 0.30,    # Trend confirmation (golden/death cross)
}

# Hybrid score blend: Value × 0.7 + Momentum × 0.3
HYBRID_VALUE_WEIGHT: Final[float] = 0.70
HYBRID_MOMENTUM_WEIGHT: Final[float] = 0.30

# Peer comparison panel
PEER_COMPARISON_COUNT: Final[int] = 7  # Number of sector/industry peers to show in Deep Dive

# Sector treemap color scale (ROIC-based: red → amber → green)
SECTOR_TREEMAP_COLOR_SCALE: Final[list] = [
    [0.0, "#EF4444"],   # Red (low ROIC)
    [0.4, "#F59E0B"],   # Amber (mid ROIC)
    [0.7, "#10B981"],   # Emerald (good ROIC)
    [1.0, "#34D399"],   # Light emerald (high ROIC)
]

# Maximum allowed growth rate for projections (sanity cap)
MAX_PROJECTION_GROWTH: Final[float] = 0.30  # 30%

# Forecast scenario chart colors (Midnight Finance palette)
CHART_COLOR_BULL: Final[str] = "#10B981"    # Emerald green
CHART_COLOR_BASE: Final[str] = "#6366F1"    # Indigo blue
CHART_COLOR_BEAR: Final[str] = "#EF4444"    # Rose red
CHART_COLOR_MARKET: Final[str] = "#8B5CF6"  # Violet purple

# ==================== MACRO OVERLAY CONFIGURATION ====================

# Macro indicator tickers (yfinance symbols)
MACRO_INDICATORS: Final[Dict[str, Dict[str, str]]] = {
    "US10Y": {"ticker": "^TNX", "label": "US 10Y Yield", "unit": "%"},
    "VIX": {"ticker": "^VIX", "label": "VIX (Fear Index)", "unit": ""},
    "DXY": {"ticker": "DX-Y.NYB", "label": "US Dollar Index", "unit": ""},
    "OIL": {"ticker": "CL=F", "label": "Crude Oil (WTI)", "unit": "$"},
}

# VIX traffic-light thresholds: (green_upper, amber_upper)
# Green: <15 (low fear), Amber: 15-25 (moderate), Red: >25 (high fear)
VIX_THRESHOLDS: Final[Tuple[float, float]] = (15.0, 25.0)

# Macro data cache TTL — 30 minutes (more frequent than stock price cache)
MACRO_DATA_TTL: Final[int] = 1800  # 30 minutes (60*30)

# ==================== BACKTEST CONFIGURATION ====================

# Benchmark index tickers for backtest comparison
BENCHMARK_TICKERS: Final[Dict[str, str]] = {
    "NIFTY100": "^NSEI",    # Nifty 50 index
    "SP500": "^GSPC",        # S&P 500 index
    "FTSE100": "^FTSE",      # FTSE 100 index
}

# Backtest lookback periods in approximate trading days
BACKTEST_PERIODS: Final[Dict[str, int]] = {
    "1Y": 252,
    "3Y": 756,
    "5Y": 1260,
}

# ==================== PORTFOLIO CONFIGURATION ====================

# Concentration limits by risk tolerance (max weight per stock)
PORTFOLIO_CONCENTRATION_LIMITS: Final[Dict[str, float]] = {
    "Conservative": 0.15,    # Max 15% per stock
    "Moderate": 0.20,        # Max 20% per stock
    "Aggressive": 0.30,      # Max 30% per stock
}

# Default investment amount for portfolio builder
PORTFOLIO_DEFAULT_AMOUNT: Final[int] = 100_000

# ==================== DATA QUALITY ====================

# Minimum required data completeness
MIN_DATA_COMPLETENESS: Final[float] = 0.7  # 70% of fields must be non-null
