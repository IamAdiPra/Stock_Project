"""
Test script for Quant Layer screening logic.
"""
from src.data.fetcher import batch_fetch_deep_data
from src.quant.screener import screen_stocks, format_results_for_display
from src.utils.ticker_lists import get_all_tickers

# 1. Pick 5 tickers to test (so it doesn't take too long)
sample_tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ITC"]

print("Starting Quant Layer Test...")

# 2. Fetch data (This takes 30-60 seconds)
stocks_data = batch_fetch_deep_data(sample_tickers, exchange="NSE")

# 3. Apply the 'Veteran Quant' filters
results = screen_stocks(
    stocks_data,
    min_roic=0.15,         # 15% ROIC
    max_debt_equity=0.8,   # 0.8 Debt/Equity
    near_low_threshold=10.0 # Within 10% of 52w Low
)

# 4. Show the results
if not results.empty:
    display = format_results_for_display(results)
    print(display[['rank', 'ticker', 'roic_pct', 'value_score']])
else:
    print("No stocks passed the strict filters. This is normal!")