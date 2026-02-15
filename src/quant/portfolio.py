"""
Portfolio construction module.
Provides allocation strategies (equal-weight, inverse-volatility, max-diversification)
and portfolio-level risk analytics (expected return, volatility, Sharpe, max drawdown).
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from src.data.fetcher import fetch_historical_prices, normalize_ticker
from src.utils.config import (
    RISK_FREE_RATES,
    PORTFOLIO_CONCENTRATION_LIMITS,
)


# ==================== DATA PREPARATION ====================

def _get_exchange(index: str) -> Optional[str]:
    """Return exchange string for ticker normalization."""
    exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
    return exchange_map.get(index)


def build_returns_matrix(
    tickers: List[str],
    stocks_data: Dict[str, Optional[dict]],
    index: str,
) -> Optional[pd.DataFrame]:
    """
    Build a daily returns matrix for the given tickers using cached 1y prices.

    Args:
        tickers: List of raw ticker symbols
        stocks_data: Raw yfinance data dict per ticker
        index: Market index key (NIFTY100, SP500, FTSE100)

    Returns:
        DataFrame with columns=tickers, rows=dates, values=daily returns.
        None if fewer than 2 tickers have valid price data.
    """
    exchange = _get_exchange(index)
    price_series: Dict[str, pd.Series] = {}

    for ticker in tickers:
        norm_ticker = normalize_ticker(ticker, exchange)
        price_df = fetch_historical_prices(norm_ticker, period="1y")
        if price_df is not None and len(price_df) > 20:
            close = price_df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            price_series[ticker] = close

    if len(price_series) < 2:
        return None

    prices_df = pd.DataFrame(price_series).dropna()
    if len(prices_df) < 20:
        return None

    returns_df = prices_df.pct_change().dropna()
    return returns_df


# ==================== ALLOCATION STRATEGIES ====================

def allocate_equal_weight(n: int) -> np.ndarray:
    """Equal-weight allocation: 1/N per stock."""
    return np.ones(n) / n


def allocate_inverse_volatility(cov_matrix: np.ndarray) -> np.ndarray:
    """
    Inverse-volatility allocation: weight inversely proportional to annualized vol.
    Lower-volatility stocks get higher weight.
    """
    vols = np.sqrt(np.diag(cov_matrix) * 252)
    # Guard against zero volatility
    vols = np.maximum(vols, 1e-8)
    inv_vols = 1.0 / vols
    return inv_vols / inv_vols.sum()


def allocate_max_diversification(cov_matrix: np.ndarray, iterations: int = 1000) -> np.ndarray:
    """
    Max-diversification allocation (risk-parity variant).
    Maximizes the diversification ratio: (w' * sigma) / sqrt(w' * Cov * w).

    Uses iterative proportional fitting (no scipy dependency):
    Start from inverse-vol weights, iteratively adjust toward higher
    diversification ratio.

    Args:
        cov_matrix: Annualized covariance matrix (N x N)
        iterations: Number of optimization iterations

    Returns:
        Optimal weight array summing to 1.0
    """
    n = cov_matrix.shape[0]
    vols = np.sqrt(np.diag(cov_matrix))
    vols = np.maximum(vols, 1e-8)

    # Correlation matrix
    vol_outer = np.outer(vols, vols)
    corr_matrix = cov_matrix / vol_outer
    np.fill_diagonal(corr_matrix, 1.0)

    # Start from inverse-vol weights
    weights = 1.0 / vols
    weights = weights / weights.sum()

    for _ in range(iterations):
        # Portfolio vol
        port_var = weights @ cov_matrix @ weights
        port_vol = np.sqrt(max(port_var, 1e-16))

        # Marginal contribution to risk
        marginal_risk = (cov_matrix @ weights) / port_vol

        # Target: equalize risk contribution relative to volatility
        # Stocks with lower marginal risk / vol get more weight
        risk_contribution = weights * marginal_risk
        target = vols / vols.sum()

        # Adjust weights: reduce overcontributing, increase undercontributing
        adjustment = target / np.maximum(risk_contribution, 1e-12)
        new_weights = weights * adjustment
        new_weights = np.maximum(new_weights, 0.0)
        total = new_weights.sum()
        if total > 0:
            new_weights = new_weights / total

        # Check convergence
        if np.max(np.abs(new_weights - weights)) < 1e-8:
            break
        weights = new_weights

    return weights


# ==================== CONCENTRATION LIMITS ====================

def apply_concentration_limits(weights: np.ndarray, max_weight: float) -> np.ndarray:
    """
    Clip weights to max_weight and redistribute excess proportionally.

    Args:
        weights: Raw allocation weights (sum to 1.0)
        max_weight: Maximum allowed weight per stock (e.g. 0.15 for 15%)

    Returns:
        Adjusted weights respecting concentration limit, summing to 1.0
    """
    adjusted = weights.copy()

    for _ in range(50):  # Iterative clipping
        excess_mask = adjusted > max_weight
        if not excess_mask.any():
            break

        excess = adjusted[excess_mask].sum() - max_weight * excess_mask.sum()
        adjusted[excess_mask] = max_weight

        # Redistribute excess to uncapped stocks proportionally
        uncapped = ~excess_mask
        if uncapped.any() and adjusted[uncapped].sum() > 0:
            adjusted[uncapped] += excess * (adjusted[uncapped] / adjusted[uncapped].sum())

    # Final normalization
    total = adjusted.sum()
    if total > 0:
        adjusted = adjusted / total

    return adjusted


# ==================== PORTFOLIO METRICS ====================

def compute_portfolio_metrics(
    weights: np.ndarray,
    returns_matrix: pd.DataFrame,
    risk_free_rate: float,
) -> Dict[str, float]:
    """
    Compute portfolio-level risk and return metrics.

    Args:
        weights: Allocation weights array
        returns_matrix: Daily returns DataFrame (columns = tickers)
        risk_free_rate: Annual risk-free rate (e.g. 0.045)

    Returns:
        Dict with expected_return, volatility, sharpe_ratio, max_drawdown
    """
    daily_returns = returns_matrix.values
    portfolio_daily = daily_returns @ weights

    # Annualized expected return
    mean_daily = np.mean(portfolio_daily)
    expected_return = mean_daily * 252

    # Annualized volatility
    volatility = np.std(portfolio_daily, ddof=1) * np.sqrt(252)

    # Sharpe ratio
    sharpe = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0.0

    # Max drawdown
    cumulative = (1 + pd.Series(portfolio_daily)).cumprod()
    rolling_max = cumulative.cummax()
    drawdowns = (cumulative - rolling_max) / rolling_max
    max_drawdown = float(drawdowns.min())

    return {
        "expected_return": float(expected_return),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_drawdown),
    }


# ==================== ORCHESTRATOR ====================

def build_portfolio(
    results_df: pd.DataFrame,
    stocks_data: Dict[str, Optional[dict]],
    index: str,
    investment_amount: float,
    risk_tolerance: str,
    method: str,
) -> Optional[Dict[str, Any]]:
    """
    Build a portfolio from screened stocks.

    Args:
        results_df: Raw screening results (results_df_raw)
        stocks_data: Cached deep data dict
        index: Market index key
        investment_amount: Total investment amount in local currency
        risk_tolerance: "Conservative", "Moderate", or "Aggressive"
        method: "Equal Weight", "Inverse Volatility", or "Max Diversification"

    Returns:
        Dict with keys: allocations (list of dicts), metrics (dict),
        correlation_matrix (DataFrame), tickers (list).
        None if insufficient data.
    """
    if results_df.empty:
        return None

    tickers = results_df["ticker"].tolist()

    # Build returns matrix
    returns_matrix = build_returns_matrix(tickers, stocks_data, index)
    if returns_matrix is None:
        return None

    # Only keep tickers that have valid return data
    valid_tickers = [t for t in tickers if t in returns_matrix.columns]
    if len(valid_tickers) < 2:
        return None

    returns_matrix = returns_matrix[valid_tickers]
    n = len(valid_tickers)

    # Annualized covariance matrix
    cov_matrix = returns_matrix.cov().values * 252

    # Compute raw weights by method
    if method == "Equal Weight":
        weights = allocate_equal_weight(n)
    elif method == "Inverse Volatility":
        weights = allocate_inverse_volatility(cov_matrix)
    elif method == "Max Diversification":
        weights = allocate_max_diversification(cov_matrix)
    else:
        weights = allocate_equal_weight(n)

    # Apply concentration limits based on risk tolerance
    max_weight = PORTFOLIO_CONCENTRATION_LIMITS.get(risk_tolerance, 0.20)
    weights = apply_concentration_limits(weights, max_weight)

    # Risk-free rate
    risk_free = RISK_FREE_RATES.get(index, 0.045)

    # Portfolio metrics
    metrics = compute_portfolio_metrics(weights, returns_matrix, risk_free)

    # Build allocation details
    allocations = []
    for i, ticker in enumerate(valid_tickers):
        row = results_df[results_df["ticker"] == ticker]
        company = str(row["company_name"].iloc[0]) if not row.empty and "company_name" in row.columns else ticker
        roic = float(row["roic"].iloc[0]) if not row.empty and "roic" in row.columns else None
        value_score = float(row["value_score"].iloc[0]) if not row.empty and "value_score" in row.columns else None

        allocations.append({
            "ticker": ticker,
            "company_name": company,
            "weight": float(weights[i]),
            "amount": float(weights[i] * investment_amount),
            "roic": roic,
            "value_score": value_score,
        })

    # Sort by weight descending
    allocations.sort(key=lambda x: x["weight"], reverse=True)

    # Correlation matrix for heatmap
    corr_matrix = returns_matrix[valid_tickers].corr()

    return {
        "allocations": allocations,
        "metrics": metrics,
        "correlation_matrix": corr_matrix,
        "tickers": valid_tickers,
    }
