"""
Backtest module.
Tests current screening criteria against historical prices using an
equal-weight portfolio of filtered stocks vs a market benchmark.

IMPORTANT LIMITATION: yfinance provides NO historical fundamentals.
This backtest uses *current* fundamentals as a proxy — it answers
"if I had bought today's filtered stocks N years ago, how would they
have performed?" This has survivorship bias (delisted/failed companies
are excluded from the current universe).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from src.data.fetcher import fetch_historical_prices, normalize_ticker
from src.utils.config import (
    RISK_FREE_RATES,
    BENCHMARK_TICKERS,
    BACKTEST_PERIODS,
)


# ==================== HELPERS ====================

def _get_exchange(index: str) -> Optional[str]:
    """Return exchange string for ticker normalization."""
    exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
    return exchange_map.get(index)


def _fetch_and_slice_prices(
    ticker: str,
    start_date: pd.Timestamp,
) -> Optional[pd.Series]:
    """
    Fetch 5y prices and slice from start_date onward.

    Returns:
        Close price Series indexed by date, or None if insufficient data.
    """
    price_df = fetch_historical_prices(ticker, period="5y")
    if price_df is None or price_df.empty:
        return None

    close = price_df["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    # Handle timezone-aware vs timezone-naive comparison
    # LSE stocks have timezone-aware index (Europe/London), others may be naive
    if close.index.tz is not None:
        # Index is timezone-aware, ensure start_date matches
        if start_date.tz is None:
            start_date = start_date.tz_localize("UTC").tz_convert(close.index.tz)
    elif start_date.tz is not None:
        # Index is timezone-naive, strip timezone from start_date
        start_date = start_date.tz_localize(None)

    # Slice from start_date
    close = close[close.index >= start_date]
    if len(close) < 20:
        return None

    return close


# ==================== CORE BACKTEST ====================

def _build_portfolio_cumulative(
    tickers: List[str],
    index: str,
    start_date: pd.Timestamp,
) -> Optional[Dict[str, Any]]:
    """
    Build equal-weight portfolio cumulative returns from start_date.

    Returns:
        Dict with 'cumulative' (Series), 'valid_tickers' (list),
        'stock_returns' (dict ticker->total return), or None if <2 stocks.
    """
    exchange = _get_exchange(index)
    price_dict: Dict[str, pd.Series] = {}

    for ticker in tickers:
        norm_ticker = normalize_ticker(ticker, exchange)
        close = _fetch_and_slice_prices(norm_ticker, start_date)
        if close is not None:
            price_dict[ticker] = close

    if len(price_dict) < 2:
        return None

    # Align all price series on common dates
    prices_df = pd.DataFrame(price_dict).dropna()
    if len(prices_df) < 20:
        return None

    # Per-stock total returns
    stock_returns = {}
    for ticker in prices_df.columns:
        first = prices_df[ticker].iloc[0]
        last = prices_df[ticker].iloc[-1]
        stock_returns[ticker] = float((last - first) / first) if first > 0 else 0.0

    # Equal-weight daily returns -> cumulative
    daily_returns = prices_df.pct_change().dropna()
    portfolio_daily = daily_returns.mean(axis=1)  # equal weight
    cumulative = (1 + portfolio_daily).cumprod()

    return {
        "cumulative": cumulative,
        "daily_returns": portfolio_daily,
        "valid_tickers": list(prices_df.columns),
        "stock_returns": stock_returns,
    }


def _build_benchmark_cumulative(
    index: str,
    start_date: pd.Timestamp,
) -> Optional[pd.Series]:
    """
    Fetch benchmark index cumulative returns from start_date.

    Returns:
        Cumulative return Series, or None if data unavailable.
    """
    benchmark_ticker = BENCHMARK_TICKERS.get(index)
    if not benchmark_ticker:
        return None

    close = _fetch_and_slice_prices(benchmark_ticker, start_date)
    if close is None:
        return None

    daily_returns = close.pct_change().dropna()
    cumulative = (1 + daily_returns).cumprod()
    return cumulative


def _compute_metrics(
    portfolio_daily: pd.Series,
    portfolio_cumulative: pd.Series,
    benchmark_cumulative: Optional[pd.Series],
    risk_free_rate: float,
    trading_days: int,
) -> Dict[str, float]:
    """
    Compute backtest performance metrics.

    Returns:
        Dict with total_return, annualized_return, benchmark_return,
        alpha, max_drawdown, sharpe, volatility.
    """
    # Total return
    total_return = float(portfolio_cumulative.iloc[-1] - 1.0)

    # Annualized return
    n_days = len(portfolio_daily)
    years = n_days / 252.0
    annualized_return = float((1 + total_return) ** (1.0 / max(years, 0.01)) - 1.0)

    # Benchmark return
    benchmark_return = 0.0
    if benchmark_cumulative is not None and len(benchmark_cumulative) > 0:
        benchmark_return = float(benchmark_cumulative.iloc[-1] - 1.0)

    # Alpha
    alpha = annualized_return - float(
        (1 + benchmark_return) ** (1.0 / max(years, 0.01)) - 1.0
    )

    # Max drawdown
    rolling_max = portfolio_cumulative.cummax()
    drawdowns = (portfolio_cumulative - rolling_max) / rolling_max
    max_drawdown = float(drawdowns.min())

    # Volatility and Sharpe
    volatility = float(np.std(portfolio_daily, ddof=1) * np.sqrt(252))
    sharpe = float(
        (annualized_return - risk_free_rate) / volatility
    ) if volatility > 0 else 0.0

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "benchmark_return": benchmark_return,
        "alpha": alpha,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "volatility": volatility,
    }


# ==================== ORCHESTRATOR ====================

def run_backtest(
    results_df: pd.DataFrame,
    index: str,
    period: str,
) -> Optional[Dict[str, Any]]:
    """
    Run a historical backtest on the currently filtered stocks.

    Args:
        results_df: Raw screening results (results_df_raw)
        index: Market index key (NIFTY100, SP500, FTSE100)
        period: Lookback period key ("1Y", "3Y", "5Y")

    Returns:
        Dict with keys:
            portfolio_cumulative: Series (indexed by date)
            benchmark_cumulative: Series or None
            metrics: dict of performance metrics
            stock_details: list of dicts (ticker, company, return, beat_benchmark)
            valid_tickers: list of tickers with data
            period_label: human-readable period string
        None if insufficient data.
    """
    if results_df.empty:
        return None

    tickers = results_df["ticker"].tolist()
    trading_days = BACKTEST_PERIODS.get(period, 252)

    # Compute start date
    start_date = pd.Timestamp(datetime.now() - timedelta(days=int(trading_days / 252 * 365)))

    # Build portfolio
    portfolio_result = _build_portfolio_cumulative(tickers, index, start_date)
    if portfolio_result is None:
        return None

    # Build benchmark
    benchmark_cumulative = _build_benchmark_cumulative(index, start_date)

    # Compute metrics
    risk_free = RISK_FREE_RATES.get(index, 0.045)
    metrics = _compute_metrics(
        portfolio_daily=portfolio_result["daily_returns"],
        portfolio_cumulative=portfolio_result["cumulative"],
        benchmark_cumulative=benchmark_cumulative,
        risk_free_rate=risk_free,
        trading_days=trading_days,
    )

    # Benchmark total return for win-rate calculation
    benchmark_total = metrics["benchmark_return"]

    # Per-stock details
    stock_details = []
    valid_tickers = portfolio_result["valid_tickers"]
    stock_returns = portfolio_result["stock_returns"]
    winners = 0

    for ticker in valid_tickers:
        row = results_df[results_df["ticker"] == ticker]
        company = str(row["company_name"].iloc[0]) if not row.empty and "company_name" in row.columns else ticker
        ret = stock_returns.get(ticker, 0.0)
        beat = ret > benchmark_total
        if beat:
            winners += 1
        stock_details.append({
            "ticker": ticker,
            "company_name": company,
            "total_return": ret,
            "beat_benchmark": beat,
        })

    # Sort by return descending
    stock_details.sort(key=lambda x: x["total_return"], reverse=True)

    # Win rate
    win_rate = winners / len(valid_tickers) if valid_tickers else 0.0
    metrics["win_rate"] = win_rate

    period_labels = {"1Y": "1 Year", "3Y": "3 Years", "5Y": "5 Years"}

    return {
        "portfolio_cumulative": portfolio_result["cumulative"],
        "benchmark_cumulative": benchmark_cumulative,
        "metrics": metrics,
        "stock_details": stock_details,
        "valid_tickers": valid_tickers,
        "period_label": period_labels.get(period, period),
    }
