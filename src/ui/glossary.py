"""
Financial Glossary Module - Educational Layer

Centralized dictionary of all financial terms, metrics, and concepts used
throughout the Stock Value Screener application. Each term includes:
- Simple explanation (10-year-old friendly)
- Real-world analogy
- Formula (where applicable)
- "Good value" threshold
- Related terms for cross-linking
- Category for filtering

Author: Claude (Senior Quant Developer)
Version: 1.10.0
"""

from typing import Dict, List, Optional, Any


# ============================================================================
# FINANCIAL GLOSSARY - 80+ Terms Across 10 Categories
# ============================================================================

FINANCIAL_GLOSSARY: Dict[str, Dict[str, Any]] = {
    # ========================================================================
    # CATEGORY: Quality Metrics
    # ========================================================================
    "ROIC": {
        "full_name": "Return on Invested Capital",
        "simple": "How efficiently a company converts invested money into profit",
        "analogy": "Like getting ₹15 profit for every ₹100 you invest in a lemonade stand",
        "formula": "NOPAT ÷ Invested Capital",
        "good_value": "> 15% (Warren Buffett's baseline for quality businesses)",
        "related": ["D/E", "FCF", "Invested Capital", "NOPAT"],
        "category": "Quality Metrics"
    },
    "D/E": {
        "full_name": "Debt-to-Equity Ratio",
        "simple": "How much money a company owes compared to what it owns",
        "analogy": "Like comparing your home loan to your savings account balance",
        "formula": "Total Debt ÷ Total Equity",
        "good_value": "< 0.8 (less debt = more stable, especially in downturns)",
        "related": ["ROIC", "Total Debt", "Total Equity"],
        "category": "Quality Metrics"
    },
    "FCF": {
        "full_name": "Free Cash Flow",
        "simple": "Cash left over after a company pays all its bills and expenses",
        "analogy": "Like your pocket money after paying for snacks and bus fare",
        "formula": "Operating Cash Flow - Capital Expenditures",
        "good_value": "Positive and growing for 3+ years (consistent cash generation)",
        "related": ["ROIC", "Operating Cash Flow", "CapEx"],
        "category": "Quality Metrics"
    },
    "Invested Capital": {
        "full_name": "Invested Capital",
        "simple": "The total money invested in a company to run its business",
        "analogy": "Like the startup money you need to open a store (rent, inventory, equipment)",
        "formula": "Total Debt + Total Equity - Cash",
        "good_value": "N/A (used in ROIC calculation)",
        "related": ["ROIC", "Total Debt", "Total Equity"],
        "category": "Quality Metrics"
    },
    "NOPAT": {
        "full_name": "Net Operating Profit After Tax",
        "simple": "How much profit a company makes from its core business after taxes",
        "analogy": "Like your total earnings from a job after government cuts its share",
        "formula": "Operating Income × (1 - Tax Rate)",
        "good_value": "N/A (used in ROIC calculation)",
        "related": ["ROIC", "Operating Income"],
        "category": "Quality Metrics"
    },

    # ========================================================================
    # CATEGORY: Valuation Metrics
    # ========================================================================
    "P/E": {
        "full_name": "Price-to-Earnings Ratio",
        "simple": "How many years of profit you're paying for when buying a stock",
        "analogy": "Like paying ₹20 for a business that earns ₹1 per year (P/E = 20)",
        "formula": "Stock Price ÷ Earnings Per Share",
        "good_value": "< 20 for value stocks (cheaper = better margin of safety)",
        "related": ["EPS", "Market Cap", "Margin of Safety"],
        "category": "Valuation"
    },
    "EPS": {
        "full_name": "Earnings Per Share",
        "simple": "How much profit a company makes for each share of its stock",
        "analogy": "Like dividing a pizza's profit among all the friends who chipped in to buy it",
        "formula": "Net Income ÷ Total Shares Outstanding",
        "good_value": "Growing year-over-year (consistent profitability)",
        "related": ["P/E", "Net Income"],
        "category": "Valuation"
    },
    "Market Cap": {
        "full_name": "Market Capitalization",
        "simple": "The total value of all a company's shares combined",
        "analogy": "Like the price if you wanted to buy an entire company at today's stock price",
        "formula": "Stock Price × Total Shares Outstanding",
        "good_value": "N/A (size indicator: > $10B = large-cap, stable)",
        "related": ["Stock Price"],
        "category": "Valuation"
    },
    "52w High": {
        "full_name": "52-Week High",
        "simple": "The highest price a stock reached in the past year",
        "analogy": "Like the most expensive a toy has been in the last 12 months",
        "formula": "max(Daily Close Prices) over 252 trading days",
        "good_value": "N/A (reference point for discount calculation)",
        "related": ["52w Low", "Distance from High"],
        "category": "Valuation"
    },
    "52w Low": {
        "full_name": "52-Week Low",
        "simple": "The lowest price a stock reached in the past year",
        "analogy": "Like the cheapest a toy has been in the last 12 months (might be on sale!)",
        "formula": "min(Daily Close Prices) over 252 trading days",
        "good_value": "Near 52w low = potential value opportunity",
        "related": ["52w High", "Distance from Low"],
        "category": "Valuation"
    },
    "Distance from High": {
        "full_name": "Distance from 52-Week High",
        "simple": "How far below its peak price a stock is currently trading",
        "analogy": "Like a discount label showing 30% off the original price",
        "formula": "(Current Price - 52w High) ÷ 52w High × 100",
        "good_value": "-20% or more (stock on sale, but check why it dropped!)",
        "related": ["52w High", "Distance from Low"],
        "category": "Valuation"
    },
    "Margin of Safety": {
        "full_name": "Margin of Safety",
        "simple": "The gap between a stock's fair value and its current price",
        "analogy": "Like buying a ₹100 bill for ₹60 — the ₹40 difference is your safety cushion",
        "formula": "(Intrinsic Value - Current Price) ÷ Intrinsic Value × 100",
        "good_value": "> 20% (bigger cushion = less risk if you're wrong about value)",
        "related": ["DCF Intrinsic Value", "P/E"],
        "category": "Valuation"
    },

    # ========================================================================
    # CATEGORY: Earnings Quality
    # ========================================================================
    "EQ Score": {
        "full_name": "Earnings Quality Score",
        "simple": "How trustworthy a company's reported profits are (0-100 scale)",
        "analogy": "Like a report card showing if a student's grades are real or inflated",
        "formula": "Weighted average of Accrual Ratio, FCF/NI, Revenue vs Receivables",
        "good_value": "> 70 (high-quality, cash-backed earnings)",
        "related": ["Accrual Ratio", "FCF/NI", "Revenue vs Receivables"],
        "category": "Earnings Quality"
    },
    "Accrual Ratio": {
        "full_name": "Accrual Ratio",
        "simple": "Difference between reported profit and actual cash collected",
        "analogy": "Like claiming you earned ₹100 but only ₹60 reached your wallet (₹40 is accruals)",
        "formula": "(Net Income - Operating Cash Flow) ÷ Total Assets",
        "good_value": "< 0.05 (low = profits match cash, high = earnings might be inflated)",
        "related": ["FCF", "Net Income", "Operating Cash Flow"],
        "category": "Earnings Quality"
    },
    "FCF/NI": {
        "full_name": "Free Cash Flow to Net Income Ratio",
        "simple": "How much of reported profit actually becomes usable cash",
        "analogy": "Like getting ₹10 cash for every ₹10 salary (ratio = 1.0 = perfect!)",
        "formula": "Free Cash Flow ÷ Net Income",
        "good_value": "> 1.0 (cash exceeds reported profit = gold standard)",
        "related": ["FCF", "Net Income", "Accrual Ratio"],
        "category": "Earnings Quality"
    },
    "Revenue vs Receivables": {
        "full_name": "Revenue vs Receivables Gap",
        "simple": "Whether customers are actually paying for purchases or just promising to pay later",
        "analogy": "Like selling 100 lemonades but only getting paid for 70 (30 are IOUs)",
        "formula": "Revenue Growth % - Receivables Growth %",
        "good_value": "> 0% (positive = healthy, revenue growing faster than unpaid bills)",
        "related": ["Accrual Ratio", "Revenue"],
        "category": "Earnings Quality"
    },

    # ========================================================================
    # CATEGORY: Momentum & Technical Indicators
    # ========================================================================
    "RSI": {
        "full_name": "Relative Strength Index",
        "simple": "Measures if a stock is overbought (too expensive) or oversold (on sale)",
        "analogy": "Like a thermometer for stock prices: above 70 = too hot, below 30 = too cold",
        "formula": "100 - (100 ÷ (1 + Average Gain ÷ Average Loss))",
        "good_value": "30-55 (recovery zone for value investors)",
        "related": ["MACD", "SMA", "Momentum Score"],
        "category": "Momentum & Technical"
    },
    "MACD": {
        "full_name": "Moving Average Convergence Divergence",
        "simple": "Shows if a stock's price trend is getting stronger or weaker",
        "analogy": "Like watching two runners: when the fast one catches the slow one, momentum is building",
        "formula": "12-day EMA - 26-day EMA (histogram = MACD - 9-day signal line)",
        "good_value": "Positive histogram = bullish momentum building",
        "related": ["RSI", "SMA", "Momentum Score"],
        "category": "Momentum & Technical"
    },
    "SMA": {
        "full_name": "Simple Moving Average",
        "simple": "The average stock price over a certain number of days",
        "analogy": "Like your average test score over the last 10 exams (smooths out daily ups and downs)",
        "formula": "Sum of Closing Prices ÷ Number of Days",
        "good_value": "Price above SMA 200 = long-term uptrend",
        "related": ["Golden Cross", "Death Cross", "Bollinger Bands"],
        "category": "Momentum & Technical"
    },
    "Golden Cross": {
        "full_name": "Golden Cross",
        "simple": "When short-term average price crosses above long-term average (bullish signal)",
        "analogy": "Like a speedboat overtaking a cruise ship — fast momentum catching up",
        "formula": "SMA 50 > SMA 200 (50-day average crosses above 200-day average)",
        "good_value": "Bullish signal (momentum turning positive)",
        "related": ["Death Cross", "SMA"],
        "category": "Momentum & Technical"
    },
    "Death Cross": {
        "full_name": "Death Cross",
        "simple": "When short-term average price crosses below long-term average (bearish signal)",
        "analogy": "Like a speedboat falling behind a cruise ship — losing momentum",
        "formula": "SMA 50 < SMA 200 (50-day average crosses below 200-day average)",
        "good_value": "Bearish signal (momentum turning negative, caution!)",
        "related": ["Golden Cross", "SMA"],
        "category": "Momentum & Technical"
    },
    "Momentum Score": {
        "full_name": "Momentum Score",
        "simple": "Combined score (0-100) measuring if a stock's price trend is improving",
        "analogy": "Like a report card combining math, science, and English grades into one GPA",
        "formula": "Weighted average of RSI, MACD, and SMA signals",
        "good_value": "> 60 (strong momentum, price likely to continue rising)",
        "related": ["RSI", "MACD", "SMA"],
        "category": "Momentum & Technical"
    },
    "Bollinger Bands": {
        "full_name": "Bollinger Bands",
        "simple": "Statistical boundaries showing normal price range for a stock",
        "analogy": "Like a tunnel the stock price usually stays within (breaking out = big move coming)",
        "formula": "Middle = 20-day SMA, Upper/Lower = SMA ± (2 × Standard Deviation)",
        "good_value": "Price near lower band = potential bounce, near upper = overbought",
        "related": ["SMA", "Mean Reversion"],
        "category": "Momentum & Technical"
    },
    "Mean Reversion": {
        "full_name": "Mean Reversion",
        "simple": "The tendency of prices to return to their average over time",
        "analogy": "Like a rubber band — stretch it too far and it snaps back to normal",
        "formula": "N/A (concept, not a metric)",
        "good_value": "Stock trading far from average = likely to revert",
        "related": ["P/E", "Bollinger Bands"],
        "category": "Momentum & Technical"
    },

    # ========================================================================
    # CATEGORY: Risk Metrics
    # ========================================================================
    "Beta": {
        "full_name": "Beta (Market Risk)",
        "simple": "How much a stock moves compared to the overall market",
        "analogy": "Like comparing a sports car (high beta = fast, volatile) to a sedan (low beta = steady)",
        "formula": "Covariance(Stock Returns, Market Returns) ÷ Variance(Market Returns)",
        "good_value": "< 1.0 (less volatile than market = safer for conservative investors)",
        "related": ["Annual Volatility", "Sharpe Ratio"],
        "category": "Risk Metrics"
    },
    "Annual Volatility": {
        "full_name": "Annual Volatility",
        "simple": "How much a stock's price jumps around over a year",
        "analogy": "Like a rollercoaster: high volatility = lots of big ups and downs, low = gentle ride",
        "formula": "Standard Deviation of Daily Returns × √252",
        "good_value": "< 25% (lower = smoother ride, less stomach-churning drops)",
        "related": ["Beta", "Max Drawdown", "Sharpe Ratio"],
        "category": "Risk Metrics"
    },
    "Max Drawdown": {
        "full_name": "Maximum Drawdown",
        "simple": "The biggest drop from peak to bottom a stock has experienced",
        "analogy": "Like falling from the 10th floor to the 3rd floor — that's your worst-case loss",
        "formula": "(Trough Value - Peak Value) ÷ Peak Value",
        "good_value": "> -20% (smaller drops = less pain during market crashes)",
        "related": ["Annual Volatility", "Beta"],
        "category": "Risk Metrics"
    },
    "Sharpe Ratio": {
        "full_name": "Sharpe Ratio",
        "simple": "How much extra return you get for each unit of risk you take",
        "analogy": "Like comparing salary to work hours: ₹100/hour is better than ₹50/hour",
        "formula": "(Portfolio Return - Risk-Free Rate) ÷ Portfolio Volatility",
        "good_value": "> 1.0 (reward exceeds risk, > 2.0 = excellent)",
        "related": ["Annual Volatility", "Beta", "Risk-Free Rate"],
        "category": "Risk Metrics"
    },
    "Risk-Free Rate": {
        "full_name": "Risk-Free Rate (Rf)",
        "simple": "The return you'd get from the safest investment (government bonds)",
        "analogy": "Like interest on a savings account — guaranteed, but low returns",
        "formula": "10-Year Government Bond Yield",
        "good_value": "N/A (benchmark: India ~7%, US ~4.5%, UK ~4.5%)",
        "related": ["Sharpe Ratio", "WACC", "ERP"],
        "category": "Risk Metrics"
    },
    "ERP": {
        "full_name": "Equity Risk Premium",
        "simple": "Extra return investors demand for taking stock market risk vs safe bonds",
        "analogy": "Like charging extra for a risky job (skydiving instructor vs librarian)",
        "formula": "Expected Market Return - Risk-Free Rate",
        "good_value": "N/A (benchmark: India ~7.5%, US ~5%, UK ~5.5%)",
        "related": ["Risk-Free Rate", "WACC"],
        "category": "Risk Metrics"
    },
    "WACC": {
        "full_name": "Weighted Average Cost of Capital",
        "simple": "The average interest rate a company pays to finance its business",
        "analogy": "Like the blended interest rate on all your loans (home + car + credit card)",
        "formula": "(Cost of Equity × % Equity) + (Cost of Debt × % Debt × (1 - Tax Rate))",
        "good_value": "< 10% (lower = cheaper financing, higher returns to shareholders)",
        "related": ["Beta", "Risk-Free Rate", "ERP"],
        "category": "Risk Metrics"
    },

    # ========================================================================
    # CATEGORY: Valuation Models
    # ========================================================================
    "DCF": {
        "full_name": "Discounted Cash Flow Model",
        "simple": "Estimates a company's fair value by adding up all its future cash flows",
        "analogy": "Like valuing a rental property by adding up 20 years of rent (adjusted for inflation)",
        "formula": "Sum of (Future FCF ÷ (1 + WACC)^Year) + Terminal Value",
        "good_value": "DCF > Current Price (stock is undervalued)",
        "related": ["FCF", "WACC", "Terminal Growth"],
        "category": "Valuation Models"
    },
    "Earnings Multiple": {
        "full_name": "Earnings Multiple Model",
        "simple": "Values a company by multiplying its earnings by a typical industry ratio",
        "analogy": "Like selling a house at '10× annual rent' (if similar houses sell for that multiple)",
        "formula": "Future EPS × Target P/E Ratio",
        "good_value": "Projected value > Current Price (undervalued)",
        "related": ["EPS", "P/E"],
        "category": "Valuation Models"
    },
    "ROIC Growth": {
        "full_name": "ROIC Growth Model",
        "simple": "Estimates growth by how much profit a company can reinvest at high returns",
        "analogy": "Like compound interest: reinvest ₹15 profit at 20% ROIC → grows to ₹18 next year",
        "formula": "Sustainable Growth = Reinvestment Rate × ROIC",
        "good_value": "High ROIC + high reinvestment = compounding machine",
        "related": ["ROIC", "Reinvestment Rate"],
        "category": "Valuation Models"
    },
    "Terminal Growth": {
        "full_name": "Terminal Growth Rate",
        "simple": "The long-term growth rate a company is expected to sustain forever",
        "analogy": "Like assuming your salary grows 3% per year until retirement (steady, not explosive)",
        "formula": "GDP Growth Rate (India ~5%, US ~3%, UK ~2.5%)",
        "good_value": "N/A (conservative estimate matching country's economy)",
        "related": ["DCF"],
        "category": "Valuation Models"
    },
    "Bull Case": {
        "full_name": "Bull Case Scenario",
        "simple": "The optimistic forecast assuming everything goes right for the company",
        "analogy": "Like planning for all A+ grades on your report card",
        "formula": "Historical growth maintained (capped at 30% max)",
        "good_value": "Best-case price target for upside potential",
        "related": ["Base Case", "Bear Case"],
        "category": "Valuation Models"
    },
    "Base Case": {
        "full_name": "Base Case Scenario",
        "simple": "The realistic forecast assuming normal business conditions",
        "analogy": "Like planning for a B+ average on your report card (solid but not perfect)",
        "formula": "Growth decays from historical to terminal growth over 5 years",
        "good_value": "Most likely price target for moderate expectations",
        "related": ["Bull Case", "Bear Case"],
        "category": "Valuation Models"
    },
    "Bear Case": {
        "full_name": "Bear Case Scenario",
        "simple": "The pessimistic forecast assuming challenges slow the company down",
        "analogy": "Like planning for C grades on your report card (passing but disappointing)",
        "formula": "50% of historical growth",
        "good_value": "Worst-case price target for downside risk",
        "related": ["Bull Case", "Base Case"],
        "category": "Valuation Models"
    },

    # ========================================================================
    # CATEGORY: Portfolio Metrics
    # ========================================================================
    "Expected Return": {
        "full_name": "Expected Portfolio Return",
        "simple": "The average gain you expect from your portfolio over a year",
        "analogy": "Like predicting you'll earn ₹12 profit for every ₹100 invested",
        "formula": "Weighted average of individual stock returns",
        "good_value": "> 12% (beat market average for Nifty/S&P 500)",
        "related": ["Portfolio Volatility", "Sharpe Ratio"],
        "category": "Portfolio Metrics"
    },
    "Portfolio Volatility": {
        "full_name": "Portfolio Volatility",
        "simple": "How much your portfolio value bounces around over time",
        "analogy": "Like measuring how bumpy a car ride is (smooth road vs potholed street)",
        "formula": "√(Weights × Covariance Matrix × Weights)",
        "good_value": "< 20% (less bouncing = better sleep at night)",
        "related": ["Annual Volatility", "Correlation"],
        "category": "Portfolio Metrics"
    },
    "Concentration Limit": {
        "full_name": "Concentration Limit",
        "simple": "Maximum percentage of portfolio allowed in a single stock",
        "analogy": "Like not putting all eggs in one basket — limit each basket to 20% of eggs",
        "formula": "% cap per stock (Conservative 15%, Moderate 20%, Aggressive 30%)",
        "good_value": "Lower = safer diversification, higher = higher conviction bets",
        "related": ["Portfolio Weight"],
        "category": "Portfolio Metrics"
    },
    "Equal Weight": {
        "full_name": "Equal Weight Allocation",
        "simple": "Splitting your money evenly among all selected stocks",
        "analogy": "Like dividing a pizza equally among friends (everyone gets the same slice)",
        "formula": "1 ÷ Number of Stocks",
        "good_value": "Simple baseline (hard to beat in practice!)",
        "related": ["Inverse Volatility", "Max Diversification"],
        "category": "Portfolio Metrics"
    },
    "Inverse Volatility": {
        "full_name": "Inverse Volatility Allocation",
        "simple": "Putting more money in calmer stocks, less in volatile ones",
        "analogy": "Like betting more on the steady student, less on the unpredictable one",
        "formula": "Weight ∝ 1 ÷ Stock Volatility",
        "good_value": "Reduces portfolio bumpiness (lower overall risk)",
        "related": ["Annual Volatility", "Equal Weight"],
        "category": "Portfolio Metrics"
    },
    "Max Diversification": {
        "full_name": "Maximum Diversification Allocation",
        "simple": "Balancing weights so each stock contributes equally to total risk",
        "analogy": "Like adjusting pizza slices so everyone gets equal crust (the risky part)",
        "formula": "Iterative risk-parity optimization",
        "good_value": "Best risk-adjusted returns (advanced strategy)",
        "related": ["Inverse Volatility", "Correlation"],
        "category": "Portfolio Metrics"
    },
    "Correlation": {
        "full_name": "Correlation Matrix",
        "simple": "How much stocks move together (+1) or opposite (-1)",
        "analogy": "Like twins (high correlation, always together) vs opposites (negative correlation)",
        "formula": "Covariance(Stock A, Stock B) ÷ (σ_A × σ_B)",
        "good_value": "Low correlation = better diversification (stocks don't all crash together)",
        "related": ["Portfolio Volatility", "Max Diversification"],
        "category": "Portfolio Metrics"
    },

    # ========================================================================
    # CATEGORY: Backtest Metrics
    # ========================================================================
    "Total Return": {
        "full_name": "Total Return",
        "simple": "The overall percentage gain or loss from start to finish",
        "analogy": "Like investing ₹100 and ending with ₹130 (30% total return)",
        "formula": "(Ending Value - Starting Value) ÷ Starting Value",
        "good_value": "> 0% (positive = made money!)",
        "related": ["Annualized Return"],
        "category": "Backtest Metrics"
    },
    "Annualized Return": {
        "full_name": "Annualized Return",
        "simple": "The average yearly gain if the total return is spread evenly per year",
        "analogy": "Like earning ₹10 per year for 5 years instead of ₹50 all at once",
        "formula": "(1 + Total Return)^(1 / Years) - 1",
        "good_value": "> 12% (beat market average)",
        "related": ["Total Return", "Alpha"],
        "category": "Backtest Metrics"
    },
    "Alpha": {
        "full_name": "Alpha (Excess Return)",
        "simple": "How much better (or worse) a portfolio performed vs the market benchmark",
        "analogy": "Like scoring 90% when the class average is 75% (you outperformed by +15%)",
        "formula": "Portfolio Return - Benchmark Return",
        "good_value": "> 0% (positive alpha = beat the market!)",
        "related": ["Beta", "Benchmark"],
        "category": "Backtest Metrics"
    },
    "Win Rate": {
        "full_name": "Win Rate",
        "simple": "Percentage of stocks that beat the market benchmark",
        "analogy": "Like 7 out of 10 students passing an exam (70% win rate)",
        "formula": "Number of Stocks Beating Benchmark ÷ Total Stocks",
        "good_value": "> 60% (most picks outperformed)",
        "related": ["Alpha"],
        "category": "Backtest Metrics"
    },
    "Survivorship Bias": {
        "full_name": "Survivorship Bias",
        "simple": "Only looking at companies that survived, ignoring those that failed or got delisted",
        "analogy": "Like interviewing only successful entrepreneurs (ignoring all the failed startups)",
        "formula": "N/A (caution: backtest results may look better than reality!)",
        "good_value": "Awareness: real results likely lower than backtest shows",
        "related": ["Backtest"],
        "category": "Backtest Metrics"
    },
    "Benchmark": {
        "full_name": "Market Benchmark",
        "simple": "The reference index to compare your portfolio against",
        "analogy": "Like comparing your 5K race time to the average runner's time",
        "formula": "Nifty 50 (India), S&P 500 (US), FTSE 100 (UK)",
        "good_value": "Beat benchmark = successful stock picking",
        "related": ["Alpha"],
        "category": "Backtest Metrics"
    },

    # ========================================================================
    # CATEGORY: Sector & Industry
    # ========================================================================
    "GICS Sector": {
        "full_name": "Global Industry Classification Standard Sector",
        "simple": "The broad business category a company belongs to",
        "analogy": "Like grouping restaurants (food industry) vs car dealers (auto industry)",
        "formula": "N/A (11 sectors: Technology, Healthcare, Financials, etc.)",
        "good_value": "Diversify across 3+ sectors (don't put all bets in one industry)",
        "related": ["Industry", "Sector Median"],
        "category": "Sector & Industry"
    },
    "Industry": {
        "full_name": "Industry Sub-Classification",
        "simple": "The specific type of business within a sector",
        "analogy": "Like 'Semiconductors' within Technology sector (more specific than just 'Tech')",
        "formula": "N/A (sub-level of GICS Sector)",
        "good_value": "Compare companies within same industry for fair peer analysis",
        "related": ["GICS Sector", "Peer Comparison"],
        "category": "Sector & Industry"
    },
    "Sector Median": {
        "full_name": "Sector Median ROIC",
        "simple": "The middle value of ROIC for all companies in a sector",
        "analogy": "Like the median test score in a class (half above, half below)",
        "formula": "Median(All Stock ROICs in Sector)",
        "good_value": "Stock ROIC > Sector Median (company outperforms its peers)",
        "related": ["ROIC", "Peer Comparison"],
        "category": "Sector & Industry"
    },
    "Peer Comparison": {
        "full_name": "Peer Comparison Analysis",
        "simple": "Comparing a stock's metrics to similar companies in the same industry",
        "analogy": "Like comparing your grades to classmates in the same school year",
        "formula": "N/A (visual: radar chart with normalized metrics)",
        "good_value": "Stock outperforming sector peers across multiple metrics",
        "related": ["GICS Sector", "Sector Median"],
        "category": "Sector & Industry"
    },

    # ========================================================================
    # CATEGORY: Macro Indicators
    # ========================================================================
    "US10Y": {
        "full_name": "US 10-Year Treasury Yield",
        "simple": "Interest rate on 10-year US government bonds (global risk-free benchmark)",
        "analogy": "Like the baseline savings account rate the whole world watches",
        "formula": "N/A (set by bond market supply and demand)",
        "good_value": "Rising = stocks may fall (bonds become more attractive)",
        "related": ["Risk-Free Rate", "VIX"],
        "category": "Macro Indicators"
    },
    "VIX": {
        "full_name": "CBOE Volatility Index (Fear Index)",
        "simple": "Measures how scared investors are about the stock market",
        "analogy": "Like a thermometer for investor panic: high VIX = lots of fear",
        "formula": "Implied volatility of S&P 500 options",
        "good_value": "< 15 = calm market, 15-25 = normal, > 25 = fear/crisis mode",
        "related": ["Annual Volatility", "Beta"],
        "category": "Macro Indicators"
    },
    "DXY": {
        "full_name": "US Dollar Index",
        "simple": "Measures the strength of the US dollar vs other major currencies",
        "analogy": "Like tracking how much your dollar bill can buy in foreign countries",
        "formula": "Weighted average vs EUR, JPY, GBP, CAD, SEK, CHF",
        "good_value": "Rising DXY = bad for emerging markets (India, etc.) and commodities",
        "related": ["Crude Oil"],
        "category": "Macro Indicators"
    },
    "Crude Oil": {
        "full_name": "Crude Oil (WTI)",
        "simple": "The global price of oil (affects inflation, transport, and energy stocks)",
        "analogy": "Like the price of gas at the pump — impacts your travel budget",
        "formula": "N/A (set by global supply/demand, OPEC)",
        "good_value": "Stable oil = predictable inflation, spiking oil = economic stress",
        "related": ["DXY"],
        "category": "Macro Indicators"
    },

    # ========================================================================
    # CATEGORY: Screening & Filtering
    # ========================================================================
    "Value Score": {
        "full_name": "Value Score",
        "simple": "Combined ranking of quality (ROIC) and price discount (0-1 scale)",
        "analogy": "Like grading a deal: A+ quality product at 40% off = high value score",
        "formula": "(ROIC Rank × 0.6) + (Discount Rank × 0.4)",
        "good_value": "> 0.7 (top 30% of filtered stocks)",
        "related": ["ROIC", "Distance from High"],
        "category": "Screening & Filtering"
    },
    "Hybrid Ranking": {
        "full_name": "Hybrid Ranking (Value + Momentum)",
        "simple": "Blends value score (quality + discount) with momentum score (price trend)",
        "analogy": "Like picking stocks that are both cheap and starting to rise",
        "formula": "(Value Score × 0.7) + (Momentum Score × 0.3)",
        "good_value": "Balances long-term value with short-term price strength",
        "related": ["Value Score", "Momentum Score"],
        "category": "Screening & Filtering"
    },
    "Data Confidence": {
        "full_name": "Data Confidence Level",
        "simple": "How complete the financial data is for a stock (High/Medium/Low)",
        "analogy": "Like a report card: High = all grades available, Low = missing half the subjects",
        "formula": "High = 3 statements + 3 years + beta, Medium = some missing, Low = major gaps",
        "good_value": "High confidence (more reliable metrics)",
        "related": ["Income Statement", "Balance Sheet", "Cash Flow Statement"],
        "category": "Screening & Filtering"
    },

    # ========================================================================
    # CATEGORY: Financial Statements
    # ========================================================================
    "Income Statement": {
        "full_name": "Income Statement",
        "simple": "Report showing how much money a company earned and spent",
        "analogy": "Like your monthly budget showing salary minus all expenses",
        "formula": "Revenue - Expenses = Net Income",
        "good_value": "Growing revenue + stable profit margins = healthy business",
        "related": ["Net Income", "Operating Income", "EPS"],
        "category": "Financial Statements"
    },
    "Balance Sheet": {
        "full_name": "Balance Sheet",
        "simple": "Snapshot of what a company owns (assets) and owes (liabilities)",
        "analogy": "Like a net worth statement: house + savings - loans = your equity",
        "formula": "Assets = Liabilities + Equity",
        "good_value": "More assets than liabilities = financially strong",
        "related": ["Total Assets", "Total Debt", "Total Equity"],
        "category": "Financial Statements"
    },
    "Cash Flow Statement": {
        "full_name": "Cash Flow Statement",
        "simple": "Shows actual cash coming in and going out of a company",
        "analogy": "Like tracking every rupee you deposit and withdraw from your bank account",
        "formula": "Operating Cash Flow + Investing + Financing = Net Cash Change",
        "good_value": "Positive operating cash flow = business generates real cash",
        "related": ["FCF", "Operating Cash Flow"],
        "category": "Financial Statements"
    },
    "Operating Cash Flow": {
        "full_name": "Operating Cash Flow",
        "simple": "Cash generated from a company's core business operations",
        "analogy": "Like your take-home salary (before spending on investments or loans)",
        "formula": "Net Income + Depreciation - Changes in Working Capital",
        "good_value": "> Net Income (cash matches or exceeds reported profit)",
        "related": ["FCF", "Accrual Ratio"],
        "category": "Financial Statements"
    },
    "Total Assets": {
        "full_name": "Total Assets",
        "simple": "Everything a company owns (cash, buildings, equipment, inventory)",
        "analogy": "Like adding up your house, car, savings, and all possessions",
        "formula": "Current Assets + Fixed Assets + Intangible Assets",
        "good_value": "N/A (size indicator, used in ratios like Accrual Ratio)",
        "related": ["Balance Sheet", "Total Debt"],
        "category": "Financial Statements"
    },
    "Total Debt": {
        "full_name": "Total Debt",
        "simple": "All money a company owes to lenders",
        "analogy": "Like adding up your home loan, car loan, and credit card balance",
        "formula": "Short-Term Debt + Long-Term Debt",
        "good_value": "< 0.5 × Total Equity (debt should be less than half of what company owns)",
        "related": ["D/E", "Total Equity"],
        "category": "Financial Statements"
    },
    "Total Equity": {
        "full_name": "Total Equity (Shareholders' Equity)",
        "simple": "The value left for shareholders after subtracting all debts",
        "analogy": "Like your home's value minus the remaining mortgage (your actual ownership)",
        "formula": "Total Assets - Total Liabilities",
        "good_value": "Positive and growing (company's net worth increasing)",
        "related": ["D/E", "Total Debt"],
        "category": "Financial Statements"
    },
    "Net Income": {
        "full_name": "Net Income",
        "simple": "The final profit after all expenses, taxes, and interest",
        "analogy": "Like your take-home pay after all deductions (the money you actually keep)",
        "formula": "Revenue - All Expenses - Taxes - Interest",
        "good_value": "Positive and growing (profitable and improving)",
        "related": ["EPS", "FCF/NI", "Operating Income"],
        "category": "Financial Statements"
    },
    "Operating Income": {
        "full_name": "Operating Income (EBIT)",
        "simple": "Profit from core business before interest and taxes",
        "analogy": "Like your salary before tax deductions (raw business earnings)",
        "formula": "Revenue - Operating Expenses",
        "good_value": "Growing faster than revenue (improving efficiency)",
        "related": ["NOPAT", "Net Income"],
        "category": "Financial Statements"
    },
    "Reinvestment Rate": {
        "full_name": "Reinvestment Rate",
        "simple": "Percentage of profit a company puts back into growing the business",
        "analogy": "Like saving 60% of your salary to invest in education or a side business",
        "formula": "1 - Payout Ratio (or Retained Earnings ÷ Net Income)",
        "good_value": "60% (balanced: 40% to shareholders, 60% for growth)",
        "related": ["ROIC Growth", "Payout Ratio"],
        "category": "Financial Statements"
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_definition(term: str) -> Optional[Dict[str, Any]]:
    """
    Returns the complete glossary entry for a given financial term.

    Args:
        term: Financial term key (e.g., "ROIC", "Beta", "P/E")

    Returns:
        Dictionary with all glossary fields, or None if term not found
    """
    return FINANCIAL_GLOSSARY.get(term.upper())


def get_simple_explanation(term: str) -> str:
    """
    Returns only the simple explanation for a term (for inline tooltips).

    Args:
        term: Financial term key

    Returns:
        Simple explanation string, or "Term not found in glossary" if missing
    """
    entry = get_definition(term)
    if entry:
        return entry["simple"]
    return f"Term '{term}' not found in glossary"


def get_category_terms(category: str) -> List[str]:
    """
    Returns all terms belonging to a specific category.

    Args:
        category: Category name (e.g., "Quality Metrics", "Risk Metrics")

    Returns:
        List of term keys in alphabetical order
    """
    if category == "All":
        return sorted(FINANCIAL_GLOSSARY.keys())

    return sorted([
        term for term, entry in FINANCIAL_GLOSSARY.items()
        if entry["category"] == category
    ])


def search_glossary(query: str) -> List[str]:
    """
    Searches glossary by term name, full name, or keywords in simple/analogy text.

    Args:
        query: Search string (case-insensitive)

    Returns:
        List of matching term keys, sorted by relevance
    """
    if not query:
        return []

    query_lower = query.lower()
    matches = []

    for term, entry in FINANCIAL_GLOSSARY.items():
        # Check term acronym (highest priority)
        if query_lower in term.lower():
            matches.insert(0, term)
            continue

        # Check full name
        if query_lower in entry["full_name"].lower():
            matches.append(term)
            continue

        # Check simple explanation or analogy
        if (query_lower in entry["simple"].lower() or
            query_lower in entry["analogy"].lower()):
            matches.append(term)

    return matches


def render_glossary_card(term: str) -> str:
    """
    Returns HTML for a glossary card with full definition.

    Args:
        term: Financial term key

    Returns:
        HTML string styled for Midnight Finance theme
    """
    entry = get_definition(term)
    if not entry:
        return f"<p style='color: #EF4444;'>Term '{term}' not found</p>"

    # Build related terms links (clickable, styled as chips)
    related_html = " ".join([
        f"<span style='background: #1B2332; color: #6366F1; padding: 2px 8px; "
        f"border-radius: 4px; font-size: 0.75rem; margin-right: 4px;'>{r}</span>"
        for r in entry.get("related", [])
    ])

    return f"""
    <div style="background: #1B2332; padding: 12px; border-radius: 6px; margin-bottom: 12px; border-left: 3px solid #10B981;">
        <div style="color: #10B981; font-weight: 600; margin-bottom: 4px;">
            {entry['full_name']} ({term})
        </div>
        <div style="color: #F0F2F5; font-size: 0.9rem; margin-bottom: 6px;">
            {entry['simple']}
        </div>
        <div style="color: #8899A6; font-size: 0.85rem; font-style: italic; margin-bottom: 6px;">
            💡 {entry['analogy']}
        </div>
        <div style="color: #6366F1; font-size: 0.85rem; margin-bottom: 4px;">
            <strong>Good value:</strong> {entry['good_value']}
        </div>
        <div style="color: #8899A6; font-size: 0.8rem; margin-bottom: 4px;">
            <strong>Formula:</strong> <code style="background: #0E1117; padding: 2px 6px; border-radius: 3px;">{entry['formula']}</code>
        </div>
        <div style="color: #5C6B7A; font-size: 0.8rem; margin-top: 6px;">
            <strong>Related:</strong> {related_html if related_html else "None"}
        </div>
    </div>
    """


def get_all_categories() -> List[str]:
    """
    Returns list of all unique categories in the glossary.

    Returns:
        Sorted list of category names
    """
    categories = set(entry["category"] for entry in FINANCIAL_GLOSSARY.values())
    return sorted(categories)
