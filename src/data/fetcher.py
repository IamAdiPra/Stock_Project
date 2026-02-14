"""
Data fetching layer with yfinance API integration.
Handles ticker normalization (.NS suffix), retry logic, concurrent fetching,
and error logging.
"""

import time
from typing import Optional, List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import pandas as pd

from src.data.cache import cache_fundamental_data, cache_price_data
from src.utils.logger import log_data_issue
from src.utils.config import (
    MAX_RETRIES, RETRY_DELAY, API_TIMEOUT, EXCHANGE_SUFFIXES,
    RATE_LIMIT_MAX_RETRIES, RATE_LIMIT_BASE_DELAY,
)


# Default concurrency for batch fetching
# 3 workers × ~5 API calls/ticker = ~15 in-flight requests
# Conservative pacing to avoid Yahoo Finance rate limiting on 500-ticker runs
DEFAULT_MAX_WORKERS: int = 3

# Small delay (seconds) between processing completed futures in batch fetches
# Smooths request bursts when multiple futures complete simultaneously
INTER_TICKER_DELAY: float = 0.3


def normalize_ticker(ticker: str, exchange: str = "NSE") -> str:
    """
    Normalize ticker symbol with appropriate exchange suffix.

    For US markets (NYSE, NASDAQ), converts dots to dashes (e.g., BRK.B → BRK-B)
    to match Yahoo Finance's expected format.

    Args:
        ticker: Raw ticker symbol (e.g., "RELIANCE", "AAPL", "BRK.B")
        exchange: Exchange identifier ("NSE", "BSE", "NYSE", "NASDAQ")

    Returns:
        Normalized ticker with suffix (e.g., "RELIANCE.NS", "AAPL", "BRK-B")
    """
    ticker = ticker.strip().upper()

    # For US markets (no suffix), convert dots to dashes
    # Yahoo Finance uses BRK-B instead of BRK.B
    if exchange in ["NYSE", "NASDAQ", None]:
        ticker = ticker.replace(".", "-")

    suffix = EXCHANGE_SUFFIXES.get(exchange, "")

    # Don't add suffix if it already exists
    if suffix and not ticker.endswith(suffix):
        return f"{ticker}{suffix}"

    return ticker


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if an exception is a Yahoo Finance rate limit error."""
    error_str = str(error).lower()
    return "rate" in error_str or "too many requests" in error_str or "429" in error_str


def _retry_fetch(
    fetch_func,
    ticker: str,
    max_retries: int = MAX_RETRIES,
    failure_message: str = "Data unavailable after retries"
) -> Optional[any]:
    """
    Internal retry wrapper for yfinance API calls.
    Logs a SINGLE error after all retries are exhausted (not per-attempt).

    Uses exponential backoff for rate limit errors (5s, 10s, 20s, 40s, 80s)
    and standard fixed delay for other errors.

    Args:
        fetch_func: Function to execute with retry logic
        ticker: Ticker symbol (for error logging)
        max_retries: Maximum number of retry attempts
        failure_message: Message to log if all retries return None

    Returns:
        Result from fetch_func or None if all retries fail
    """
    last_error = None
    retries = max_retries
    attempt = 0

    while attempt < retries:
        try:
            result = fetch_func()
            if result is not None:
                return result
        except Exception as e:
            last_error = e
            # Rate limit: switch to longer exponential backoff with more retries
            if _is_rate_limit_error(e) and retries == max_retries:
                retries = RATE_LIMIT_MAX_RETRIES
            if attempt < retries - 1:
                if _is_rate_limit_error(e):
                    delay = RATE_LIMIT_BASE_DELAY * (2 ** attempt)
                else:
                    delay = RETRY_DELAY
                time.sleep(delay)
        attempt += 1

    # All retries exhausted — log once
    if last_error:
        log_data_issue(
            ticker=ticker,
            issue_type="fetch_failure",
            error_message=f"Max retries exceeded: {str(last_error)}"
        )
    else:
        log_data_issue(
            ticker=ticker,
            issue_type="incomplete_data",
            error_message=failure_message
        )
    return None


@cache_fundamental_data
def fetch_fundamental_data(ticker: str) -> Optional[dict]:
    """
    Fetch fundamental data for a ticker (cached for 24 hours).

    Returns yfinance .info dict containing:
    - Financial ratios (P/E, P/B, ROE, ROA, ROIC)
    - Balance sheet metrics (totalDebt, totalAssets, equity)
    - Income statement metrics (revenue, netIncome, margins)
    - Cash flow metrics (freeCashflow, operatingCashflow)

    Args:
        ticker: Normalized ticker symbol

    Returns:
        Dictionary of fundamental data or None if fetch fails
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        info = stock.info

        # Validate that we got meaningful data
        # Return None silently for empty/minimal data to avoid log spam
        # (some tickers like FI consistently return empty from yfinance)
        if not info or len(info) < 5:
            return None

        return info

    return _retry_fetch(_fetch, ticker)


@cache_price_data
def fetch_price_data(ticker: str) -> Optional[dict]:
    """
    Fetch current price and 52-week metrics (cached for 1 hour).

    Returns:
    - currentPrice: Latest trading price
    - fiftyTwoWeekHigh: Highest price in last 52 weeks
    - fiftyTwoWeekLow: Lowest price in last 52 weeks
    - fiftyTwoWeekChange: Percentage change from 52-week start

    Args:
        ticker: Normalized ticker symbol

    Returns:
        Dictionary with price metrics or None if fetch fails
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        info = stock.info

        required_fields = ['currentPrice', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']
        price_data = {field: info.get(field) for field in required_fields}

        # Check if we got valid price data
        if not any(price_data.values()):
            return None

        # Calculate distance from 52-week high
        if price_data['currentPrice'] and price_data['fiftyTwoWeekHigh']:
            price_data['distance_from_52w_high'] = (
                (price_data['currentPrice'] - price_data['fiftyTwoWeekHigh'])
                / price_data['fiftyTwoWeekHigh']
            ) * 100  # Percentage

        return price_data

    return _retry_fetch(
        _fetch, ticker,
        failure_message="Missing price data (currentPrice, 52-week metrics)"
    )


@cache_fundamental_data
def fetch_historical_prices(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Fetch historical price data (cached for 24 hours).

    Args:
        ticker: Normalized ticker symbol
        period: Time period ("1mo", "3mo", "6mo", "1y", "2y", "5y")

    Returns:
        DataFrame with OHLCV data or None if fetch fails
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, timeout=API_TIMEOUT)

        if hist.empty:
            return None

        return hist

    return _retry_fetch(
        _fetch, ticker,
        failure_message=f"No historical data for period: {period}"
    )


def fetch_complete_data(ticker: str, exchange: str = "NSE") -> Optional[dict]:
    """
    Fetch all data (fundamental + price) for a single ticker.

    This is a convenience function that combines fundamental and price data
    into a single dictionary.

    Args:
        ticker: Raw ticker symbol
        exchange: Exchange identifier

    Returns:
        Combined dictionary with all data or None if fetch fails
    """
    normalized_ticker = normalize_ticker(ticker, exchange)

    fundamental = fetch_fundamental_data(normalized_ticker)
    price = fetch_price_data(normalized_ticker)

    if fundamental is None and price is None:
        return None

    # Merge both dictionaries
    complete_data = {
        "ticker": ticker,
        "normalized_ticker": normalized_ticker,
        "exchange": exchange,
        **(fundamental or {}),
        **(price or {})
    }

    return complete_data


@cache_fundamental_data
def fetch_income_statement(ticker: str) -> Optional[pd.DataFrame]:
    """
    Fetch income statement (financials) for ROIC calculation (cached 24h).

    Returns DataFrame with:
    - Operating Income (EBIT)
    - Tax Rate / Tax Provision
    - Net Income
    - Revenue

    Args:
        ticker: Normalized ticker symbol

    Returns:
        DataFrame with income statement data (columns = fiscal years) or None
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        financials = stock.financials  # Annual income statement

        if financials is None or financials.empty:
            return None

        return financials

    return _retry_fetch(
        _fetch, ticker,
        failure_message="Income statement data unavailable"
    )


@cache_fundamental_data
def fetch_balance_sheet(ticker: str) -> Optional[pd.DataFrame]:
    """
    Fetch balance sheet for Invested Capital calculation (cached 24h).

    Returns DataFrame with:
    - Total Debt
    - Total Stockholder Equity
    - Cash and Cash Equivalents
    - Total Assets
    - Current Liabilities

    Args:
        ticker: Normalized ticker symbol

    Returns:
        DataFrame with balance sheet data (columns = fiscal years) or None
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet  # Annual balance sheet

        if balance_sheet is None or balance_sheet.empty:
            return None

        return balance_sheet

    return _retry_fetch(
        _fetch, ticker,
        failure_message="Balance sheet data unavailable"
    )


@cache_fundamental_data
def fetch_cashflow_statement(ticker: str) -> Optional[pd.DataFrame]:
    """
    Fetch cash flow statement for 3-year FCF validation (cached 24h).

    Returns DataFrame with:
    - Free Cash Flow
    - Operating Cash Flow
    - Capital Expenditures

    Args:
        ticker: Normalized ticker symbol

    Returns:
        DataFrame with cash flow data (columns = fiscal years) or None
    """
    def _fetch():
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow  # Annual cash flow statement

        if cashflow is None or cashflow.empty:
            return None

        return cashflow

    return _retry_fetch(
        _fetch, ticker,
        failure_message="Cash flow statement data unavailable"
    )


def fetch_deep_data(ticker: str, exchange: str = "NSE") -> Optional[dict]:
    """
    Fetch comprehensive financial data including statements (for deep analysis).

    Returns:
    - All data from fetch_complete_data()
    - income_statement: Income statement DataFrame
    - balance_sheet: Balance sheet DataFrame
    - cashflow_statement: Cash flow statement DataFrame

    Args:
        ticker: Raw ticker symbol
        exchange: Exchange identifier

    Returns:
        Dictionary with complete data + financial statements or None
    """
    normalized_ticker = normalize_ticker(ticker, exchange)

    # Fetch basic data
    complete_data = fetch_complete_data(ticker, exchange)

    if complete_data is None:
        return None

    # Fetch financial statements
    income_stmt = fetch_income_statement(normalized_ticker)
    balance_sheet = fetch_balance_sheet(normalized_ticker)
    cashflow_stmt = fetch_cashflow_statement(normalized_ticker)

    # Add statements to data dict
    complete_data.update({
        "income_statement": income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow_statement": cashflow_stmt
    })

    return complete_data


def batch_fetch_data(
    tickers: List[str],
    exchange: str = "NSE",
    max_workers: int = DEFAULT_MAX_WORKERS,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Optional[dict]]:
    """
    Fetch data for multiple tickers concurrently using ThreadPoolExecutor.

    Args:
        tickers: List of ticker symbols
        exchange: Exchange identifier for all tickers
        max_workers: Number of concurrent fetch threads (default: 10)
        progress_callback: Optional callback(completed, total) for progress updates.
                           Called from the main thread (safe for Streamlit UI).

    Returns:
        Dictionary mapping ticker -> data (or None if failed)
    """
    results = {}
    total = len(tickers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_complete_data, ticker, exchange): ticker
            for ticker in tickers
        }
        for i, future in enumerate(as_completed(future_to_ticker), start=1):
            ticker = future_to_ticker[future]
            try:
                results[ticker] = future.result()
            except Exception as e:
                results[ticker] = None
                log_data_issue(ticker, "fetch_failure", f"Thread error: {str(e)}")
            if progress_callback:
                progress_callback(i, total)
            time.sleep(INTER_TICKER_DELAY)

    return results


def batch_fetch_deep_data(
    tickers: List[str],
    exchange: str = "NSE",
    max_workers: int = DEFAULT_MAX_WORKERS,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Optional[dict]]:
    """
    Fetch deep financial data (with statements) for multiple tickers concurrently.

    Uses ThreadPoolExecutor to fetch multiple tickers in parallel.

    Args:
        tickers: List of ticker symbols
        exchange: Exchange identifier for all tickers
        max_workers: Number of concurrent fetch threads (default: 10)
        progress_callback: Optional callback(completed, total) for progress updates.
                           Called from the main thread (safe for Streamlit UI).

    Returns:
        Dictionary mapping ticker -> deep data (or None if failed)
    """
    results = {}
    total = len(tickers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_deep_data, ticker, exchange): ticker
            for ticker in tickers
        }
        for i, future in enumerate(as_completed(future_to_ticker), start=1):
            ticker = future_to_ticker[future]
            try:
                results[ticker] = future.result()
            except Exception as e:
                results[ticker] = None
                log_data_issue(ticker, "fetch_failure", f"Thread error: {str(e)}")
            if progress_callback:
                progress_callback(i, total)
            time.sleep(INTER_TICKER_DELAY)

    return results
