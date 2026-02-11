"""
Forecasting and valuation models for stock price projection.
Pure functions that compute DCF, earnings multiple, ROIC-based growth,
risk metrics, and composite forecasts from raw financial data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from src.quant.metrics import _extract_value, calculate_roic
from src.utils.config import (
    RISK_FREE_RATES,
    EQUITY_RISK_PREMIUM,
    MARKET_ANNUAL_RETURNS,
    TERMINAL_GROWTH_RATE,
    MAX_PROJECTION_GROWTH,
)


# ==================== CONSTANTS ====================

HORIZONS: List[float] = [0.5, 1.0, 2.0, 5.0]
HORIZON_LABELS: List[str] = ["6 Months", "1 Year", "2 Years", "5 Years"]

DEFAULT_BETA: float = 1.0
PROJECTION_YEARS: int = 5


# ==================== HELPERS ====================

def _apply_scenario_growth(
    historical_growth: float,
    scenario: str,
    year: int,
    total_years: int = PROJECTION_YEARS,
    terminal_growth: float = TERMINAL_GROWTH_RATE,
    max_growth: float = MAX_PROJECTION_GROWTH,
) -> float:
    """
    Apply scenario adjustment to growth rate for a given projection year.

    Bull: historical rate maintained (no decay), capped at max_growth.
    Base: linear decay from historical toward terminal_growth over total_years.
    Bear: 50% of historical, same decay pattern.

    Args:
        historical_growth: Base historical CAGR (decimal)
        scenario: "bull", "base", or "bear"
        year: Projection year (1-indexed)
        total_years: Total projection horizon
        terminal_growth: Long-term growth target
        max_growth: Cap on projected growth rate

    Returns:
        Adjusted growth rate for the given year.
    """
    if scenario == "bull":
        return min(historical_growth, max_growth)

    starting_growth = historical_growth
    if scenario == "bear":
        starting_growth = historical_growth * 0.5

    # Linear decay from starting_growth toward terminal_growth
    decay_factor = year / total_years
    growth = starting_growth * (1 - decay_factor) + terminal_growth * decay_factor

    return min(growth, max_growth)


# ==================== GROWTH RATE CALCULATORS ====================

def calculate_fcf_cagr(
    cashflow_statement: Optional[pd.DataFrame],
    years: int = 3,
) -> Optional[float]:
    """
    Calculate Free Cash Flow compound annual growth rate.

    Args:
        cashflow_statement: Cash flow DataFrame (columns = fiscal years, most recent first)
        years: Number of years for CAGR calculation

    Returns:
        FCF CAGR as decimal (e.g., 0.12 for 12%) or None if insufficient data.
    """
    if cashflow_statement is None or cashflow_statement.empty:
        return None

    try:
        fcf_keys = ['Free Cash Flow', 'FreeCashFlow']
        fcf_row = None
        for key in fcf_keys:
            if key in cashflow_statement.index:
                fcf_row = cashflow_statement.loc[key]
                break

        if fcf_row is None:
            return None

        num_points = min(years, len(fcf_row))
        if num_points < 2:
            return None

        newest = float(fcf_row.iloc[0])
        oldest = float(fcf_row.iloc[num_points - 1])

        if oldest <= 0 or newest <= 0:
            return None

        cagr = (newest / oldest) ** (1 / (num_points - 1)) - 1
        return cagr

    except Exception:
        return None


def calculate_eps_cagr(
    income_statement: Optional[pd.DataFrame],
    shares_outstanding: Optional[float],
    years: int = 3,
) -> Optional[float]:
    """
    Calculate EPS compound annual growth rate from income statement.

    Args:
        income_statement: Income statement DataFrame
        shares_outstanding: Current shares outstanding
        years: Number of years for CAGR

    Returns:
        EPS CAGR as decimal or None if insufficient data.
    """
    if income_statement is None or income_statement.empty:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None

    try:
        net_income_keys = ['Net Income', 'Net Income Common Stockholders']
        ni_row = None
        for key in net_income_keys:
            if key in income_statement.index:
                ni_row = income_statement.loc[key]
                break

        if ni_row is None:
            return None

        num_points = min(years, len(ni_row))
        if num_points < 2:
            return None

        newest_eps = float(ni_row.iloc[0]) / shares_outstanding
        oldest_eps = float(ni_row.iloc[num_points - 1]) / shares_outstanding

        if oldest_eps <= 0 or newest_eps <= 0:
            return None

        cagr = (newest_eps / oldest_eps) ** (1 / (num_points - 1)) - 1
        return cagr

    except Exception:
        return None


# ==================== COST OF CAPITAL ====================

def calculate_wacc(
    data: dict,
    balance_sheet: Optional[pd.DataFrame],
    income_statement: Optional[pd.DataFrame],
    risk_free_rate: float = 0.045,
    equity_risk_premium: float = EQUITY_RISK_PREMIUM,
) -> Optional[float]:
    """
    Calculate Weighted Average Cost of Capital using CAPM.

    Cost of Equity = Rf + Beta * ERP
    Cost of Debt = Interest Expense / Total Debt
    WACC = (E/(D+E)) * Ke + (D/(D+E)) * Kd * (1 - tax_rate)

    Falls back to cost of equity if debt data is unavailable.

    Args:
        data: yfinance .info dict
        balance_sheet: Balance sheet DataFrame
        income_statement: Income statement DataFrame
        risk_free_rate: Risk-free rate
        equity_risk_premium: Market risk premium

    Returns:
        WACC as decimal (e.g., 0.10 for 10%) or None if calculation fails.
    """
    beta = data.get('beta')
    if beta is None or pd.isna(beta) or beta <= 0:
        beta = DEFAULT_BETA

    cost_of_equity = risk_free_rate + beta * equity_risk_premium

    # Try to compute full WACC with debt component
    market_cap = data.get('marketCap')
    if market_cap is None or balance_sheet is None or balance_sheet.empty:
        return cost_of_equity

    try:
        balance = balance_sheet.iloc[:, 0]
        total_debt = _extract_value(balance, [
            'Total Debt', 'Long Term Debt', 'Net Debt'
        ])

        if total_debt is None or total_debt <= 0:
            return cost_of_equity

        # Cost of debt approximation
        cost_of_debt = 0.05  # Default 5%
        if income_statement is not None and not income_statement.empty:
            income = income_statement.iloc[:, 0]
            interest_expense = _extract_value(income, [
                'Interest Expense', 'Interest Expense Non Operating',
            ])
            if interest_expense is not None and total_debt > 0:
                cost_of_debt = abs(interest_expense) / total_debt

        # Tax rate
        tax_rate = 0.25
        if income_statement is not None and not income_statement.empty:
            income = income_statement.iloc[:, 0]
            tax_provision = _extract_value(income, [
                'Tax Provision', 'Income Tax Expense',
            ])
            pretax_income = _extract_value(income, [
                'Pretax Income', 'Income Before Tax',
            ])
            if pretax_income and pretax_income > 0 and tax_provision:
                tax_rate = abs(tax_provision) / pretax_income

        # WACC calculation
        equity_value = float(market_cap)
        debt_value = total_debt
        total_value = equity_value + debt_value

        if total_value <= 0:
            return cost_of_equity

        wacc = (
            (equity_value / total_value) * cost_of_equity
            + (debt_value / total_value) * cost_of_debt * (1 - tax_rate)
        )

        return wacc

    except Exception:
        return cost_of_equity


# ==================== MODEL 1: DCF VALUATION ====================

def calculate_dcf_valuation(
    data: dict,
    cashflow_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
    income_statement: Optional[pd.DataFrame],
    risk_free_rate: float = 0.045,
    equity_risk_premium: float = EQUITY_RISK_PREMIUM,
    terminal_growth: float = TERMINAL_GROWTH_RATE,
    scenario: str = "base",
) -> Optional[Dict[str, Any]]:
    """
    Simplified DCF valuation with scenario analysis.

    Projects FCF forward 5 years with decaying growth, applies terminal value.

    Returns:
        Dict with intrinsic_value_per_share, margin_of_safety_pct,
        horizon_prices, wacc, fcf_cagr, projected_fcfs, etc.
        None if calculation fails.
    """
    current_price = data.get('currentPrice')
    shares = data.get('sharesOutstanding')
    if current_price is None or shares is None or shares <= 0:
        return None

    # Get TTM FCF
    ttm_fcf = data.get('freeCashflow')
    if ttm_fcf is None or pd.isna(ttm_fcf) or ttm_fcf <= 0:
        # Try from cashflow statement
        if cashflow_statement is not None and not cashflow_statement.empty:
            fcf_keys = ['Free Cash Flow', 'FreeCashFlow']
            for key in fcf_keys:
                if key in cashflow_statement.index:
                    val = cashflow_statement.loc[key].iloc[0]
                    if pd.notna(val) and val > 0:
                        ttm_fcf = float(val)
                        break
        if ttm_fcf is None or ttm_fcf <= 0:
            return None

    ttm_fcf = float(ttm_fcf)

    # FCF growth rate
    fcf_cagr = calculate_fcf_cagr(cashflow_statement)
    if fcf_cagr is None:
        # Fallback to earnings growth from .info
        eg = data.get('earningsGrowth')
        if eg is not None and not pd.isna(eg):
            fcf_cagr = float(eg)
        else:
            fcf_cagr = 0.05  # Conservative 5% default

    # WACC
    wacc = calculate_wacc(data, balance_sheet, income_statement,
                          risk_free_rate, equity_risk_premium)
    if wacc is None or wacc <= terminal_growth:
        return None

    # Project FCF forward
    projected_fcfs: List[float] = []
    fcf = ttm_fcf
    for year in range(1, PROJECTION_YEARS + 1):
        growth = _apply_scenario_growth(fcf_cagr, scenario, year,
                                        terminal_growth=terminal_growth)
        fcf = fcf * (1 + growth)
        projected_fcfs.append(fcf)

    # Terminal value
    terminal_value = projected_fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    if terminal_value < 0:
        terminal_value = 0

    # Present values
    pv_fcfs = sum(
        fcf_i / (1 + wacc) ** i
        for i, fcf_i in enumerate(projected_fcfs, start=1)
    )
    pv_terminal = terminal_value / (1 + wacc) ** PROJECTION_YEARS

    enterprise_value = pv_fcfs + pv_terminal

    # Subtract net debt for equity value
    net_debt = 0.0
    if balance_sheet is not None and not balance_sheet.empty:
        balance = balance_sheet.iloc[:, 0]
        total_debt = _extract_value(balance, ['Total Debt', 'Long Term Debt', 'Net Debt'])
        cash = _extract_value(balance, [
            'Cash And Cash Equivalents', 'Cash',
            'Cash Cash Equivalents And Short Term Investments',
        ])
        if total_debt is not None:
            net_debt = total_debt - (cash or 0)

    equity_value = enterprise_value - net_debt
    if equity_value <= 0:
        equity_value = enterprise_value  # Fallback: ignore net debt if negative equity

    intrinsic_per_share = equity_value / shares
    margin_of_safety = (intrinsic_per_share - current_price) / intrinsic_per_share * 100

    # Horizon prices: converge from current price to intrinsic value
    # Convergence weights: 6mo=10%, 1y=20%, 2y=40%, 5y=100%
    convergence = [0.10, 0.20, 0.40, 1.00]
    horizon_prices: Dict[str, float] = {}
    for label, conv in zip(HORIZON_LABELS, convergence):
        horizon_prices[label] = current_price + (intrinsic_per_share - current_price) * conv

    return {
        "intrinsic_value_per_share": intrinsic_per_share,
        "current_price": current_price,
        "margin_of_safety_pct": margin_of_safety,
        "wacc": wacc,
        "fcf_cagr": fcf_cagr,
        "projected_fcfs": projected_fcfs,
        "terminal_value": terminal_value,
        "pv_fcfs": pv_fcfs,
        "pv_terminal": pv_terminal,
        "horizon_prices": horizon_prices,
    }


# ==================== MODEL 2: EARNINGS MULTIPLE ====================

def calculate_earnings_multiple_valuation(
    data: dict,
    income_statement: Optional[pd.DataFrame],
    scenario: str = "base",
) -> Optional[Dict[str, Any]]:
    """
    Earnings multiple (P/E) based price projection.

    Projects EPS forward using historical growth, applies target P/E multiple.

    Returns:
        Dict with current_eps, eps_cagr, target_pe, horizon_prices,
        horizon_returns_pct, or None if calculation fails.
    """
    current_price = data.get('currentPrice')
    shares = data.get('sharesOutstanding')
    if current_price is None or shares is None or shares <= 0:
        return None

    # Current EPS
    trailing_pe = data.get('trailingPE')
    if trailing_pe is not None and not pd.isna(trailing_pe) and trailing_pe > 0:
        current_eps = current_price / trailing_pe
    elif income_statement is not None and not income_statement.empty:
        net_income_keys = ['Net Income', 'Net Income Common Stockholders']
        for key in net_income_keys:
            if key in income_statement.index:
                ni = income_statement.loc[key].iloc[0]
                if pd.notna(ni) and ni > 0:
                    current_eps = float(ni) / shares
                    break
        else:
            return None
    else:
        return None

    if current_eps <= 0:
        return None

    # EPS growth rate
    eps_cagr = calculate_eps_cagr(income_statement, shares)
    if eps_cagr is None:
        eg = data.get('earningsGrowth')
        if eg is not None and not pd.isna(eg):
            eps_cagr = float(eg)
        else:
            eps_cagr = 0.05

    # Target P/E: prefer normalized (3-yr avg), then forwardPE, then trailingPE
    target_pe = None

    # 3-year normalized P/E
    if income_statement is not None and not income_statement.empty:
        net_income_keys = ['Net Income', 'Net Income Common Stockholders']
        net_incomes: List[float] = []
        for key in net_income_keys:
            if key in income_statement.index:
                row = income_statement.loc[key]
                for i in range(min(3, len(row))):
                    val = row.iloc[i]
                    if pd.notna(val) and val > 0:
                        net_incomes.append(float(val))
                break
        if len(net_incomes) >= 2:
            avg_eps = (sum(net_incomes) / len(net_incomes)) / shares
            if avg_eps > 0:
                target_pe = current_price / avg_eps

    if target_pe is None:
        forward_pe = data.get('forwardPE')
        if forward_pe is not None and not pd.isna(forward_pe) and forward_pe > 0:
            target_pe = float(forward_pe)

    if target_pe is None:
        if trailing_pe is not None and not pd.isna(trailing_pe) and trailing_pe > 0:
            target_pe = float(trailing_pe)

    if target_pe is None or target_pe <= 0:
        return None

    # Project EPS and price at each horizon
    horizon_prices: Dict[str, float] = {}
    horizon_returns: Dict[str, float] = {}

    for label, h in zip(HORIZON_LABELS, HORIZONS):
        # For fractional years, use fractional growth
        growth = _apply_scenario_growth(eps_cagr, scenario,
                                        year=max(1, int(h)),
                                        terminal_growth=TERMINAL_GROWTH_RATE)
        projected_eps = current_eps * (1 + growth) ** h
        price_target = projected_eps * target_pe
        horizon_prices[label] = price_target
        horizon_returns[label] = (price_target - current_price) / current_price * 100

    return {
        "current_eps": current_eps,
        "eps_cagr": eps_cagr,
        "target_pe": target_pe,
        "horizon_prices": horizon_prices,
        "horizon_returns_pct": horizon_returns,
    }


# ==================== MODEL 3: ROIC GROWTH ====================

def calculate_roic_growth_valuation(
    data: dict,
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
    cashflow_statement: Optional[pd.DataFrame],
    scenario: str = "base",
) -> Optional[Dict[str, Any]]:
    """
    ROIC-based sustainable growth model.

    Sustainable Growth = Reinvestment Rate x ROIC
    Projects earnings at sustainable growth rate, derives price via P/E.

    Returns:
        Dict with roic, reinvestment_rate, sustainable_growth, horizon_prices,
        horizon_returns_pct, or None if calculation fails.
    """
    current_price = data.get('currentPrice')
    shares = data.get('sharesOutstanding')
    if current_price is None or shares is None or shares <= 0:
        return None

    # ROIC
    roic = calculate_roic(income_statement, balance_sheet)
    if roic is None or roic <= 0:
        return None

    # Reinvestment rate approximation
    # Method: 1 - payout ratio. If payout not available, estimate from CapEx/NOPAT.
    payout_ratio = data.get('payoutRatio')
    if payout_ratio is not None and not pd.isna(payout_ratio) and 0 <= payout_ratio <= 1:
        reinvestment_rate = 1 - float(payout_ratio)
    else:
        reinvestment_rate = 0.60  # Default 60% reinvestment

    sustainable_growth = reinvestment_rate * roic

    # Current earnings
    trailing_pe = data.get('trailingPE')
    if trailing_pe is not None and not pd.isna(trailing_pe) and trailing_pe > 0:
        current_eps = current_price / trailing_pe
        target_pe = float(trailing_pe)
    elif income_statement is not None and not income_statement.empty:
        ni_keys = ['Net Income', 'Net Income Common Stockholders']
        current_eps = None
        for key in ni_keys:
            if key in income_statement.index:
                ni = income_statement.loc[key].iloc[0]
                if pd.notna(ni) and ni > 0:
                    current_eps = float(ni) / shares
                    break
        if current_eps is None or current_eps <= 0:
            return None
        target_pe = current_price / current_eps
    else:
        return None

    if current_eps <= 0 or target_pe <= 0:
        return None

    # Project forward using sustainable growth with scenario decay
    horizon_prices: Dict[str, float] = {}
    horizon_returns: Dict[str, float] = {}

    for label, h in zip(HORIZON_LABELS, HORIZONS):
        growth = _apply_scenario_growth(sustainable_growth, scenario,
                                        year=max(1, int(h)),
                                        terminal_growth=TERMINAL_GROWTH_RATE)
        projected_eps = current_eps * (1 + growth) ** h
        price_target = projected_eps * target_pe
        horizon_prices[label] = price_target
        horizon_returns[label] = (price_target - current_price) / current_price * 100

    return {
        "roic": roic,
        "reinvestment_rate": reinvestment_rate,
        "sustainable_growth": sustainable_growth,
        "current_eps": current_eps,
        "target_pe": target_pe,
        "horizon_prices": horizon_prices,
        "horizon_returns_pct": horizon_returns,
    }


# ==================== MARKET BENCHMARK ====================

def calculate_market_benchmark_returns(
    index: str,
    current_price: float,
) -> Dict[str, float]:
    """
    Calculate expected market benchmark returns at each horizon.

    Compounds the market's long-term average annual return forward,
    expressed as an equivalent price trajectory starting from current_price.

    Args:
        index: Market index key (SP500, NIFTY100, FTSE100)
        current_price: Current stock price

    Returns:
        Dict mapping horizon labels to equivalent market price at that horizon.
    """
    annual_return = MARKET_ANNUAL_RETURNS.get(index, 0.10)

    result: Dict[str, float] = {}
    for label, h in zip(HORIZON_LABELS, HORIZONS):
        result[label] = current_price * (1 + annual_return) ** h

    return result


# ==================== RISK METRICS ====================

def calculate_risk_metrics(
    data: dict,
    historical_prices: Optional[pd.DataFrame],
    risk_free_rate: float = 0.045,
    projected_annual_return: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate per-stock risk metrics from historical price data.

    Args:
        data: yfinance .info dict (for beta)
        historical_prices: 1-year OHLCV DataFrame
        risk_free_rate: Risk-free rate for Sharpe calculation
        projected_annual_return: Projected annual return (for Sharpe, if available)

    Returns:
        Dict with beta, annual_volatility, max_drawdown_pct, sharpe_ratio.
        None if historical prices unavailable.
    """
    beta = data.get('beta')
    if beta is None or pd.isna(beta) or beta <= 0:
        beta = DEFAULT_BETA

    if historical_prices is None or historical_prices.empty:
        return {
            "beta": beta,
            "annual_volatility": None,
            "max_drawdown_pct": None,
            "sharpe_ratio": None,
        }

    try:
        close = historical_prices['Close']
        if len(close) < 20:
            return {"beta": beta, "annual_volatility": None,
                    "max_drawdown_pct": None, "sharpe_ratio": None}

        # Daily returns
        daily_returns = close.pct_change().dropna()

        # Annualized volatility
        annual_volatility = float(daily_returns.std() * np.sqrt(252))

        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min()) * 100  # As percentage

        # Sharpe ratio
        sharpe = None
        if projected_annual_return is not None and annual_volatility > 0:
            sharpe = (projected_annual_return - risk_free_rate) / annual_volatility
        elif annual_volatility > 0:
            # Use historical return as proxy
            total_return = float(close.iloc[-1] / close.iloc[0]) - 1
            annualized_return = (1 + total_return) ** (252 / len(close)) - 1
            sharpe = (annualized_return - risk_free_rate) / annual_volatility

        return {
            "beta": beta,
            "annual_volatility": annual_volatility,
            "max_drawdown_pct": max_drawdown,
            "sharpe_ratio": sharpe,
        }

    except Exception:
        return {"beta": beta, "annual_volatility": None,
                "max_drawdown_pct": None, "sharpe_ratio": None}


# ==================== COMPOSITE FORECAST ====================

def calculate_composite_forecast(
    data: dict,
    income_statement: Optional[pd.DataFrame],
    balance_sheet: Optional[pd.DataFrame],
    cashflow_statement: Optional[pd.DataFrame],
    historical_prices: Optional[pd.DataFrame],
    index: str = "SP500",
) -> Optional[Dict[str, Any]]:
    """
    Run all models and produce a composite forecast for a single stock.

    Combines DCF, Earnings Multiple, and ROIC Growth models.
    Runs all three scenarios (bull/base/bear).

    Args:
        data: yfinance .info dict
        income_statement: Income statement DataFrame
        balance_sheet: Balance sheet DataFrame
        cashflow_statement: Cash flow DataFrame
        historical_prices: 1-year OHLCV DataFrame
        index: Market index for benchmark and risk-free rate

    Returns:
        Composite forecast dict or None if no models succeed.
    """
    current_price = data.get('currentPrice')
    if current_price is None:
        return None

    risk_free = RISK_FREE_RATES.get(index, 0.045)

    # Run all 3 models in all 3 scenarios
    scenarios = ["bull", "base", "bear"]

    dcf_results: Dict[str, Any] = {}
    earnings_results: Dict[str, Any] = {}
    roic_results: Dict[str, Any] = {}

    for sc in scenarios:
        dcf_results[sc] = calculate_dcf_valuation(
            data, cashflow_statement, balance_sheet, income_statement,
            risk_free_rate=risk_free, scenario=sc,
        )
        earnings_results[sc] = calculate_earnings_multiple_valuation(
            data, income_statement, scenario=sc,
        )
        roic_results[sc] = calculate_roic_growth_valuation(
            data, income_statement, balance_sheet, cashflow_statement, scenario=sc,
        )

    # Check at least one model succeeded for base scenario
    base_models = [dcf_results["base"], earnings_results["base"], roic_results["base"]]
    successful_models = [m for m in base_models if m is not None]
    if not successful_models:
        return None

    models_used = sum(1 for m in base_models if m is not None)

    # Composite horizon prices: average of available models per scenario
    composite_horizon_prices: Dict[str, Dict[str, float]] = {}
    for sc in scenarios:
        models = [
            dcf_results[sc],
            earnings_results[sc],
            roic_results[sc],
        ]
        available = [m for m in models if m is not None]
        if not available:
            composite_horizon_prices[sc] = {
                label: current_price for label in HORIZON_LABELS
            }
            continue

        sc_prices: Dict[str, float] = {}
        for label in HORIZON_LABELS:
            prices = [m["horizon_prices"][label] for m in available
                      if label in m.get("horizon_prices", {})]
            sc_prices[label] = sum(prices) / len(prices) if prices else current_price
        composite_horizon_prices[sc] = sc_prices

    # Market benchmark
    market_benchmark = calculate_market_benchmark_returns(index, current_price)

    # Risk metrics
    base_1y = composite_horizon_prices["base"].get("1 Year", current_price)
    projected_annual_return = (base_1y - current_price) / current_price
    risk = calculate_risk_metrics(data, historical_prices,
                                  risk_free_rate=risk_free,
                                  projected_annual_return=projected_annual_return)

    # Margin of safety from base DCF
    dcf_intrinsic = None
    margin_of_safety = None
    if dcf_results["base"] is not None:
        dcf_intrinsic = dcf_results["base"]["intrinsic_value_per_share"]
        margin_of_safety = dcf_results["base"]["margin_of_safety_pct"]

    # Alpha: base 1Y return vs market 1Y return
    base_1y_return = (base_1y - current_price) / current_price * 100
    market_1y_return = (market_benchmark["1 Year"] - current_price) / current_price * 100
    alpha_1y = base_1y_return - market_1y_return

    return {
        "ticker": data.get("ticker", ""),
        "company_name": data.get("longName", data.get("ticker", "")),
        "current_price": current_price,
        "dcf": dcf_results,
        "earnings_multiple": earnings_results,
        "roic_growth": roic_results,
        "composite_horizon_prices": composite_horizon_prices,
        "market_benchmark": market_benchmark,
        "risk": risk,
        "dcf_intrinsic_value": dcf_intrinsic,
        "margin_of_safety_pct": margin_of_safety,
        "alpha_1y": alpha_1y,
        "models_used": models_used,
    }


def batch_calculate_forecasts(
    results_df_raw: pd.DataFrame,
    stocks_data: Dict[str, Optional[dict]],
    index: str = "SP500",
) -> pd.DataFrame:
    """
    Calculate composite forecasts for all stocks that passed screening.

    Args:
        results_df_raw: Filtered screening results DataFrame
        stocks_data: Raw deep data dict from session state
        index: Market index

    Returns:
        Summary DataFrame with forecast columns for each stock.
    """
    from src.data.fetcher import fetch_historical_prices, normalize_ticker

    exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}
    exchange = exchange_map.get(index)

    rows: List[Dict[str, Any]] = []

    for _, row in results_df_raw.iterrows():
        ticker = row['ticker']
        data = stocks_data.get(ticker)
        if data is None:
            continue

        # Fetch historical prices for risk metrics
        norm_ticker = data.get('normalized_ticker', normalize_ticker(ticker, exchange or ""))
        hist_prices = fetch_historical_prices(norm_ticker, period="1y")

        forecast = calculate_composite_forecast(
            data=data,
            income_statement=data.get('income_statement'),
            balance_sheet=data.get('balance_sheet'),
            cashflow_statement=data.get('cashflow_statement'),
            historical_prices=hist_prices,
            index=index,
        )

        if forecast is None:
            continue

        base_prices = forecast["composite_horizon_prices"]["base"]
        current = forecast["current_price"]

        summary_row: Dict[str, Any] = {
            "ticker": ticker,
            "company_name": forecast["company_name"],
            "current_price": current,
            "dcf_fair_value": forecast.get("dcf_intrinsic_value"),
            "margin_of_safety_pct": forecast.get("margin_of_safety_pct"),
            "target_6mo": base_prices.get("6 Months"),
            "target_1y": base_prices.get("1 Year"),
            "target_2y": base_prices.get("2 Years"),
            "target_5y": base_prices.get("5 Years"),
            "return_1y_pct": (base_prices.get("1 Year", current) - current) / current * 100
                if current > 0 else None,
            "market_return_1y": (forecast["market_benchmark"]["1 Year"] - current) / current * 100
                if current > 0 else None,
            "alpha_1y": forecast.get("alpha_1y"),
            "beta": forecast["risk"]["beta"] if forecast.get("risk") else None,
            "volatility": forecast["risk"]["annual_volatility"] if forecast.get("risk") else None,
            "models_used": forecast.get("models_used", 0),
        }

        rows.append(summary_row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)
