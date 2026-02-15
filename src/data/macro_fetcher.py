"""
Macro indicator fetcher for the Market Context overlay.

Fetches real-time macro indicators (US 10Y yield, VIX, DXY, Crude Oil)
via yfinance with 30-minute caching. Each indicator is fetched independently
so one failure doesn't block the others.
"""

from typing import Optional, Dict, Any
import streamlit as st
import yfinance as yf

from src.utils.config import MACRO_INDICATORS, MACRO_DATA_TTL


@st.cache_data(ttl=MACRO_DATA_TTL, show_spinner=False)
def _fetch_single_indicator(yf_ticker: str) -> Optional[Dict[str, float]]:
    """
    Fetch latest price and daily change for a single macro indicator.

    Uses 5-day history to reliably get both current and previous close,
    even across weekends/holidays.

    Args:
        yf_ticker: yfinance ticker symbol (e.g., "^TNX", "^VIX")

    Returns:
        Dict with 'value' and 'change_pct', or None on failure
    """
    try:
        ticker = yf.Ticker(yf_ticker)
        hist = ticker.history(period="5d")

        if hist is None or hist.empty or len(hist) < 2:
            return None

        current = float(hist['Close'].iloc[-1])
        previous = float(hist['Close'].iloc[-2])

        if previous == 0:
            return None

        change_pct = ((current - previous) / previous) * 100

        return {
            "value": current,
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return None


def fetch_macro_indicators() -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch all macro indicators defined in MACRO_INDICATORS config.

    Each indicator is fetched independently — a failure on one (e.g., DXY)
    does not prevent the others from displaying.

    Returns:
        Dict mapping indicator key (e.g., "US10Y", "VIX") to:
        {
            "value": float,        # Current value
            "change_pct": float,   # Daily change %
            "label": str,          # Display name
            "unit": str,           # Unit prefix ("$", "%", "")
        }
        Value is None for indicators that failed to fetch.
    """
    results = {}

    for key, config in MACRO_INDICATORS.items():
        raw = _fetch_single_indicator(config["ticker"])

        if raw is not None:
            results[key] = {
                "value": raw["value"],
                "change_pct": raw["change_pct"],
                "label": config["label"],
                "unit": config["unit"],
            }
        else:
            results[key] = None

    return results
