"""
Caching layer using Streamlit's @st.cache_data decorator.
Implements dual TTL strategy: 24h for fundamentals, 1h for price data.

NOTE: Compatible with Python 3.9+ (no ParamSpec dependency)
"""

import streamlit as st
from functools import wraps
from typing import Callable, Any

from src.utils.config import FUNDAMENTAL_DATA_TTL, PRICE_DATA_TTL


def cache_fundamental_data(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for caching fundamental data (24-hour TTL).

    Use for: Balance sheet, income statement, cash flow, ratios.

    Args:
        func: Function to cache

    Returns:
        Cached function with 24-hour TTL
    """
    @st.cache_data(ttl=FUNDAMENTAL_DATA_TTL, show_spinner=False)
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def cache_price_data(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for caching price-related data (1-hour TTL).

    Use for: Current price, 52-week high/low, intraday metrics.

    Args:
        func: Function to cache

    Returns:
        Cached function with 1-hour TTL
    """
    @st.cache_data(ttl=PRICE_DATA_TTL, show_spinner=False)
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def clear_all_caches() -> None:
    """
    Clear all Streamlit caches.
    Useful for forcing fresh data fetch.
    """
    st.cache_data.clear()
