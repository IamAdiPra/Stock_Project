# Stock Value Screener - Project Documentation

## Project Identity & Vision

**Mission**: Professional-grade stock screening engine for long-term value investors targeting Nifty 100 and S&P 500 equities.

**Core Philosophy**: High-fidelity fundamental analysis combined with price-action discounting to identify undervalued quality companies.

**Screening Pillars**:
1. **Fundamental Health Metrics**
   - Return on Invested Capital (ROIC)
   - Free Cash Flow (FCF) Generation
   - Debt/Equity Ratio
   - Profitability Margins (Gross, Operating, Net)

2. **Price-Action Discount Indicators**
   - 52-Week High/Low Positioning
   - Distance from Historical Peaks
   - Value vs Growth Signal Strength

3. **Quality Filters**
   - Consistent Revenue Growth
   - Earnings Stability
   - Management Efficiency (ROE, ROA)

---

## Environment Constraints

### Virtual Environment
- **Active Environment**: `.venv` (local)
- **Python Version**: [TBD - to be verified]
- **Activation Command**:
  ```bash
  .\.venv\Scripts\activate  # Windows
  ```

### Core Dependencies
```
streamlit      # UI Framework
pandas         # Data Processing
plotly         # Interactive Visualizations
yfinance       # Financial Data API
```

### Development Tools (Future)
- pytest (unit testing)
- black (code formatting)
- mypy (static type checking)

---

## Strict Operational Workflow

### Phase 1: Research & Inquiry
**Objective**: Understand existing codebase and clarify requirements
**Actions**:
- Read all relevant existing files before proposing changes
- Use Glob/Grep to identify architectural patterns
- Ask clarifying questions about ambiguous requirements
- Validate assumptions with user before proceeding

### Phase 2: Technical Design Proposal
**Objective**: Present implementation plan for approval
**Requirements**:
- Provide detailed technical approach in chat
- Include file structure, module dependencies, and data flow
- Identify potential edge cases and error scenarios
- **CRITICAL**: Wait for user to respond with 'APPROVED' before coding

### Phase 3: Implementation
**Objective**: Write production-quality code
**Standards**:
- Modular, DRY (Don't Repeat Yourself) design
- Type hints for all function signatures
- Comprehensive error handling with graceful degradation
- Functional programming paradigm for data pipelines
- No hardcoded values (use constants/config)

### Phase 4: Verification
**Objective**: Ensure code runs correctly
**Deliverables**:
- Provide exact command to run the application
- Test critical paths manually
- Document any known limitations

### Phase 5: Documentation
**Objective**: Update project memory
**Actions**:
- Update this CLAUDE.md file's "Current Status" section
- Increment version number
- Log implementation details in "Implementation History"

---

## Senior Coding Standards

### 1. Functional Programming for Data Pipelines
```python
# GOOD: Functional chain
def screen_stocks(tickers: list[str]) -> pd.DataFrame:
    return (
        fetch_fundamentals(tickers)
        .pipe(calculate_roic)
        .pipe(calculate_fcf_yield)
        .pipe(filter_quality_metrics)
        .pipe(rank_by_value)
    )

# BAD: Procedural mutation
def screen_stocks(tickers):
    df = fetch_fundamentals(tickers)
    df = calculate_roic(df)
    df = calculate_fcf_yield(df)
    # ...
```

### 2. Caching Strategy
```python
@st.cache_data(ttl=3600)  # 1-hour cache
def fetch_ticker_data(ticker: str) -> dict:
    """Fetch financial data with caching to reduce API calls."""
    try:
        return yf.Ticker(ticker).info
    except Exception as e:
        log_data_failure(ticker, str(e))
        return {}
```

### 3. Error Handling & Data Integrity
- **Log all ticker-fetch failures** to a dedicated UI section
- Use `Optional[T]` type hints for nullable data
- Implement retry logic for transient API failures
- Never fail silently - always surface data quality issues to user

### 4. Code Organization
- **Separation of Concerns**: UI, Data, Quant Logic in separate modules
- **Single Responsibility**: Each function does ONE thing
- **Interface Contracts**: Use TypedDict/dataclass for data structures

---

## Current Status

### Version
**v0.7.0** - Professional Analytics & Education Layer (Phase 3)

### Last Implementation
- **Deep Dive Analysis (v0.7.0)**:
  - `src/ui/deep_dive.py`: NEW - Interactive per-stock analysis module
    - 1-year candlestick chart with Bollinger Bands (20-day SMA ± 2 std dev)
    - 3-year ROIC trend bar chart with 15% baseline reference
    - 3-year Free Cash Flow trend bar chart
    - P/E Mean Reversion chart (Current P/E vs 3-Year Normalized P/E)
    - Due Diligence external links (Yahoo Finance, Screener.in)
  - `app.py`: Tabbed layout ("Screening Results" | "Deep Dive Analysis")
  - `app.py`: `stocks_data` stored in session state for deep dive reuse

- **Enhanced Results Table (v0.7.0)**:
  - `src/ui/components.py`: Added 52w High, 52w Low, % from High columns
  - `src/ui/components.py`: Metric tooltips on ROIC, D/E, Value Score headers
  - `src/quant/screener.py`: 52-week fields included in screening results

- **Education Layer (v0.7.0)**:
  - `src/ui/sidebar.py`: "How to Read This" expander with financial glossary
  - Plain-English definitions: ROIC, D/E, FCF, Value Score, Bollinger Bands, Mean Reversion, 52w High/Low

- **Currency & Data Reliability (v0.7.0)**:
  - `src/utils/config.py`: Auto-detect currency (INR/USD) from index selection
  - `src/quant/screener.py`: Currency-aware formatting for prices, market cap
  - BRK.B dot-to-dash logic preserved from v0.6.0

- **New Quant Functions (v0.7.0)**:
  - `src/quant/metrics.py`: `calculate_roic_for_year()` - year-indexed ROIC
  - `src/quant/metrics.py`: `calculate_roic_trend()` - 3-year ROIC history
  - `src/quant/metrics.py`: `calculate_fcf_trend()` - 3-year FCF history
  - `src/quant/metrics.py`: `calculate_normalized_pe()` - P/E mean reversion
  - `src/quant/metrics.py`: `calculate_bollinger_bands()` - technical analysis

### Pending Tasks
1. ✅ ~~Define project directory structure~~
2. ✅ ~~Create data layer module (yfinance integration)~~
3. ✅ ~~Implement caching layer~~
4. ✅ ~~Add error logging system~~
5. ✅ ~~Create Nifty 100 and S&P 500 ticker lists~~
6. ✅ ~~Create quant logic module (ROIC, FCF, D/E calculations)~~
7. ✅ ~~Create UI module (Streamlit interface with 52-week visualization)~~
8. ✅ ~~Implement main app.py orchestrator~~
9. ✅ ~~Phase 3: Professional Analytics & Education Layer~~
10. Test full screening on Nifty 100 / S&P 500 in production

### Known Issues
None

---

## Implementation History

### 2026-02-10 (Session 7) - Professional Analytics & Education Layer (v0.7.0)
**New Files Created**:
- `src/ui/deep_dive.py` (~310 lines)
  - `render_deep_dive_section()`: Main entry point with stock selectbox
  - `create_price_bollinger_chart()`: 1-year candlestick + Bollinger Bands overlay
  - `create_roic_trend_chart()`: 3-year ROIC bar chart with 15% baseline
  - `create_fcf_trend_chart()`: 3-year FCF bar chart (green/red for +/-)
  - `create_pe_valuation_chart()`: Current P/E vs 3-Year Normalized P/E
  - `render_due_diligence_links()`: Yahoo Finance + Screener.in link buttons
  - `_format_large_number()`: Helper for readable financial numbers

**Files Enhanced**:
- `src/quant/metrics.py` (5 new functions):
  - `calculate_roic_for_year()`: Year-indexed ROIC (refactored from calculate_roic)
  - `calculate_roic_trend()`: 3-year ROIC history, sorted chronologically
  - `calculate_fcf_trend()`: 3-year FCF extraction from cashflow statement
  - `calculate_normalized_pe()`: Current P/E, 3-year avg P/E, premium/discount %
  - `calculate_bollinger_bands()`: 20-day SMA ± 2 std dev from OHLCV data

- `src/quant/screener.py`:
  - `screen_stocks()`: Added fifty_two_week_high/low to result dict
  - `format_results_for_display()`: Accepts currency_symbol parameter
  - `_format_market_cap()`: Accepts currency_symbol parameter
  - New formatted columns: current_price_fmt, fifty_two_week_high_fmt, fifty_two_week_low_fmt

- `src/ui/components.py`:
  - `render_results_table()`: Accepts currency_symbol, new columns (52w High/Low, % from High)
  - Added `help` tooltips on ROIC, D/E, Value Score, 52w columns

- `src/ui/sidebar.py`:
  - `render_quant_mentor()`: NEW - "How to Read This" expander with financial glossary
  - Called automatically within `render_sidebar()` before return
  - Version bumped to 0.7.0 in footer

- `src/utils/config.py`:
  - `CURRENCY_CONFIG`: INR for NIFTY100, USD for SP500
  - `DUE_DILIGENCE_URLS`: Yahoo Finance + Screener.in URL templates
  - `get_currency_symbol()`: Helper to derive currency from index

- `app.py`:
  - Tabbed layout: "Screening Results" | "Deep Dive Analysis"
  - `stocks_data` stored in session state for deep dive reuse
  - Currency symbol derived from index and passed through pipeline

**Design Decisions**:
- **Tabbed Layout**: Chose st.tabs over linear scroll for clean UX separation
  - "Screening Results": Existing scatter plot + Top 5 + table (unchanged)
  - "Deep Dive Analysis": New per-stock analysis with 4 chart types
  - Rationale: Avoids overwhelming users with too much content at once

- **ROIC Refactoring**: Extracted `calculate_roic_for_year()` with year_index parameter
  - `calculate_roic()` is now a thin wrapper calling `...(year_index=0)`
  - Enables trend analysis without code duplication
  - Backward compatible - no changes to existing callers

- **P/E Mean Reversion**: Compute normalized P/E from 3-year avg Net Income / sharesOutstanding
  - `trailingPE` from .info for current P/E
  - Historical: avg EPS from income statement × sharesOutstanding
  - Premium/discount annotation in chart (green = discount, red = premium)

- **Bollinger Bands**: Standard 20-day SMA ± 2 std dev
  - Candlestick chart (not line) for professional appearance
  - Filled region between upper/lower bands (light blue translucent)
  - Educational caption explains "statistical boundaries"

- **Currency Auto-Detection**: NIFTY100 → INR (symbol), SP500 → USD ($)
  - Flows through: format_results_for_display → render_results_table → deep_dive charts
  - Market cap formatting now currency-aware

- **Session State for stocks_data**: Store raw batch_fetch_deep_data result
  - Deep dive reuses financial statements without additional API calls
  - Historical prices still fetched per-ticker via cached fetch_historical_prices()

**Technical Notes**:
- Python 3.9.13 compatibility maintained (typing.Dict, typing.List, typing.Optional)
- All new functions return Optional types with None/empty-list for graceful degradation
- Bollinger Bands: first 19 rows have NaN (insufficient window) - Plotly handles gracefully
- P/E chart shows "N/A" message for loss-making companies (avg_eps <= 0)
- st.link_button used for due diligence links (requires Streamlit >= 1.28)
- No additional batch API calls - deep dive leverages existing cached data

### 2026-02-10 (Session 6) - Enhanced Flexibility & Bug Fixes (v0.6.0)
**Enhancements**:
- **Ticker Limit Slider** (`src/ui/sidebar.py`):
  - Range: 10-500 stocks, default 100, step 10
  - Help text: "Screen only the top N stocks by market capitalization"
  - Returns `ticker_limit` in config dict

- **Dynamic Top N Selection** (`src/utils/ticker_lists.py`):
  - Updated `get_all_tickers(index, limit)` to accept optional limit parameter
  - Ticker lists are SORTED BY MARKET CAP (descending)
  - When limit applied, returns top N largest companies

- **BRK.B Fix** (`src/data/fetcher.py`):
  - Updated `normalize_ticker()` to convert dots to dashes for US tickers
  - BRK.B → BRK-B (Yahoo Finance format)
  - Applies to NYSE, NASDAQ, and None exchange

- **Display Label** (`app.py`):
  - Added info banner: "🎯 Screening Top {N} stocks from {Index} by Market Capitalization"
  - Shown above metric cards for transparency

- **Session State Optimization** (`app.py`):
  - Added `config_requires_refetch()` helper function
  - Detects if index or ticker_limit changed
  - Filter changes (ROIC, D/E, Price) do NOT trigger re-fetch
  - Future-ready for filter-only updates without re-fetching

**Technical Notes**:
- Maintains Python 3.9.13 compatibility (typing.Optional, typing.Dict)
- Ticker lists assume pre-sorted by market cap (RELIANCE, TCS, INFY for Nifty; AAPL, MSFT, GOOGL for S&P)
- BRK.B fix prevents yfinance fetch failures for class B shares
- Session state now tracks previous config for smart re-fetch detection

### 2026-02-10 (Session 5) - Type Safety & Bug Fixes (v0.5.0)
**Bug Fixes**:
- **Type Conversion Issue** (`src/ui/visualizations.py`):
  - Added robust type conversion with `pd.to_numeric(errors='coerce')`
  - Converts numeric columns: roic, distance_from_low, value_score, market_cap
  - Drops rows with NaN in critical columns before plotting
  - Prevents TypeError when formatted strings passed to Plotly

- **DataFrame Separation** (`app.py`):
  - Session state now stores TWO DataFrames:
    - `results_df_raw`: Numeric columns for visualizations
    - `results_df_formatted`: Prettified strings for table display
  - Scatter plot uses raw DataFrame (numeric values)
  - Results table uses formatted DataFrame (readable display)
  - Top 5 picks formatted inline from raw DataFrame

**Root Cause**:
- `format_results_for_display()` converts numeric columns to strings (e.g., "1.234")
- When formatted DataFrame passed to scatter plot, Plotly multiplication failed
- Solution: Keep raw numeric DataFrame for visualizations only

**Technical Notes**:
- `pd.to_numeric(errors='coerce')` converts invalid values to NaN
- `dropna(subset=['roic', 'value_score', 'distance_from_low'])` ensures clean data
- Two-DataFrame approach separates concerns: computation vs presentation

### 2026-02-10 (Session 4) - UI Layer Implementation (Professional MVP Dashboard)
**Files Created**:
- `src/ui/sidebar.py` (121 lines)
  - `render_sidebar()`: Returns config dict with user selections (index, min_roic, max_de, near_low_pct, run_clicked)
  - Index selector: Radio buttons for Nifty 100 vs S&P 500
  - Interactive sliders:
    - Min ROIC: 5-30%, default 15%, step 1%
    - Max D/E: 0.1-2.0, default 0.8, step 0.1
    - Price Near 52w Low: 5-20%, default 10%, step 1%
  - "Run Screening" primary button with filter summary
  - `render_sidebar_footer()`: Version info, data source, help text

- `src/ui/visualizations.py` (169 lines)
  - `create_value_scatter_plot()`: Main visualization - ROIC vs Distance from 52w Low
    - X-axis: Distance from 52-week Low (%)
    - Y-axis: ROIC (%)
    - Bubble size: Scaled by Value Score (larger = better)
    - Color scale: RdYlGn (Red-Yellow-Green gradient, green = high value)
    - Hover data: Ticker, Company Name, Market Cap, Value Score
    - Professional styling: Gridlines, centered title, responsive sizing
  - `create_roic_distribution_chart()`: Histogram for ROIC distribution (future use)
  - `create_debt_equity_chart()`: Bar chart for D/E ratios (future use)
  - `_format_market_cap()`: Helper for readable market cap formatting

- `src/ui/components.py` (196 lines)
  - `render_metric_cards()`: Two-column layout with Total Screened and Passed Filters metrics
  - `render_results_table()`: Searchable/sortable DataFrame with key columns:
    - Rank, Ticker, Company, ROIC, D/E, Value Score, Market Cap, Price, % Above 52w Low
    - Download CSV button for export
    - Empty state guidance if no results
  - `render_data_quality_report()`: Expander with issue summary and detailed log
    - Three metrics: Fetch Failures, Validation Errors, Incomplete Data
    - DataFrame display of all issues with timestamps
  - `render_header()`: App title and mission statement
  - `render_footer()`: Disclaimer and credits
  - `render_empty_state()`: Placeholder when no screening run

- `app.py` (186 lines)
  - Main orchestrator with session state management
  - `initialize_session_state()`: Store results_df, config, counts
  - `run_screening()`: Execute pipeline with progress bar
    - Fetch deep data with batch_fetch_deep_data()
    - Apply screen_stocks() with user filters
    - Format results with format_results_for_display()
    - Store in session state
  - `main()`: Render workflow
    - Header → Sidebar → Run Screening (on click) → Metric Cards → Scatter Plot + Top 5 → Results Table → Data Quality Report → Footer
  - Two-column layout: Scatter plot (2/3 width) + Top 5 picks (1/3 width)
  - Responsive design with wide layout, expandable sidebar

**Design Decisions**:
- **Session State for Performance**: Store screening results in `st.session_state` to avoid re-fetching on UI interactions
  - `results_df`: Formatted DataFrame
  - `screening_config`: User selections (index, filters)
  - `total_screened`, `passed_filters`: Summary counts

- **RdYlGn Color Scale**: Red-Yellow-Green gradient for scatter plot
  - High ROIC + High Discount (top-right) = Bright Green (Best Value)
  - Low ROIC + Low Discount (bottom-left) = Red (Avoid)
  - Bubble size reinforces Value Score (larger = better)

- **Modular UI Architecture**: Separation of concerns
  - `sidebar.py`: User input controls
  - `visualizations.py`: Plotly charts (isolated, reusable)
  - `components.py`: Reusable widgets (metric cards, tables, reports)
  - `app.py`: Orchestration only (no business logic)

- **Python 3.9.13 Compatibility**: All type hints use `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Any`
  - No use of `dict[]`, `list[]` syntax (requires Python 3.9+)

- **Progressive Disclosure**: Data Quality Report in expander (collapsed if no issues)
  - Avoids overwhelming user with technical details
  - Expands automatically if issues exist

- **Empty State Handling**: Graceful UX when no stocks pass filters
  - Show warning message
  - Provide actionable suggestions (relax thresholds)
  - Still display Data Quality Report

**Technical Notes**:
- Progress bar shows fetch (50%), filtering (75%), formatting (100%)
- CSV export uses `df.to_csv().encode('utf-8')` for download
- Scatter plot hover includes formatted market cap ($1.5T, $450B)
- Wide page layout (`layout="wide"`) for better scatter plot visibility
- Session state persists results across Streamlit re-runs (e.g., slider adjustments)

### 2026-02-10 (Session 3) - Quant Layer Implementation ("Deep Dive" Analysis)
**Files Created**:
- `src/quant/metrics.py` (368 lines)
  - `calculate_roic()`: NOPAT-based ROIC from income statement and balance sheet
    - ROIC = NOPAT / Invested Capital
    - NOPAT = Operating Income × (1 - Tax Rate)
    - Invested Capital = Total Debt + Total Equity - Cash
  - `calculate_debt_to_equity()`: D/E ratio from balance sheet
  - `has_positive_fcf_3y()`: Validates 3 consecutive years of positive FCF
  - `get_ttm_fcf()`: Trailing twelve months FCF from .info
  - `calculate_distance_from_high()`: % distance from 52-week high (negative)
  - `calculate_distance_from_low()`: % distance from 52-week low (positive)
  - `is_near_52w_low()`: Checks if price <= 52w_low × 1.10 (10% threshold)
  - `calculate_value_score()`: Weighted formula = (ROIC/0.15 × 0.6) + (Discount/100 × 0.4)
  - `calculate_all_metrics()`: Convenience function for batch calculation
  - `_extract_value()`: Helper to safely extract values from financial statements

- `src/quant/screener.py` (280 lines)
  - `screen_stocks()`: Main pipeline - calculate → filter → rank
  - `apply_quality_filters()`: STRICT filtering for ROIC, D/E, 3-year FCF
  - `apply_valuation_filter()`: STRICT filtering for "near 52-week low"
  - `rank_by_value_score()`: Sort by value score descending, add rank column
  - `get_screening_summary()`: Summary statistics (pass rate, filters applied)
  - `format_results_for_display()`: UI-friendly formatting (%, market cap)
  - `get_top_n_stocks()`: Extract top N stocks by rank
  - `get_stocks_by_roic()`: Filter for high-ROIC subset

- `src/utils/ticker_lists.py` (145 lines)
  - `NIFTY_100`: Complete list of 100 NSE tickers
  - `SP500_TOP100`: Top 100 S&P 500 tickers by market cap
  - `get_nifty_100()`, `get_sp500_top100()`: Getter functions
  - `get_all_tickers()`: Unified interface for index selection
  - `get_ticker_count()`: Returns ticker count for an index

**Files Enhanced**:
- `src/data/fetcher.py` (extended to 368 lines)
  - Added `fetch_income_statement()`: Annual income statement (EBIT, Tax, Revenue)
  - Added `fetch_balance_sheet()`: Annual balance sheet (Debt, Equity, Cash, Assets)
  - Added `fetch_cashflow_statement()`: Annual cash flow (FCF, Operating CF, CapEx)
  - Added `fetch_deep_data()`: Combines .info + all 3 financial statements
  - Added `batch_fetch_deep_data()`: Batch version of deep fetch
  - All statement fetches use 24h caching via `@cache_fundamental_data`

**Design Decisions**:
- **ROIC Calculation**: Chose NOPAT-based approach over ROA proxy for precision
  - Extracts Operating Income, Tax Rate from income statement
  - Extracts Total Debt, Total Equity, Cash from balance sheet
  - Handles multiple possible row names in financial statements (e.g., "Stockholders Equity" vs "Total Equity")

- **3-Year FCF Validation**: Strict requirement - all 3 years must be positive
  - Uses `cashflow_statement.loc['Free Cash Flow'].iloc[:3]`
  - No tolerance for cash-burning companies

- **Filtering Philosophy**: STRICT exclusion (Screener, not Ranker)
  - Stocks failing ANY single filter are completely excluded
  - No partial credit or "warning" tiers
  - Ensures only "Gold Standard" stocks appear in results

- **Value Score Formula**: Weighted sum (60% ROIC, 40% Discount)
  - Emphasizes quality (ROIC) over price discount
  - ROIC normalized to 15% baseline (1.0 = 15%, 2.0 = 30%)
  - Discount factor = abs(distance from high) / 100

**Technical Notes**:
- Financial statement DataFrames have columns = fiscal years (most recent first)
- Used `_extract_value()` helper to handle varying yfinance schema row names
- All metrics return `Optional[float]` or `bool` - None indicates calculation failure
- Screening pipeline converts dict → DataFrame → filtered DataFrame → ranked DataFrame
- Display formatting includes percentage conversion, market cap abbreviation (T/B/M)

### 2026-02-10 (Session 2) - Data Layer Implementation
**Files Created**:
- `src/data/fetcher.py` (171 lines)
  - `normalize_ticker()`: Handles .NS suffix for Indian stocks
  - `fetch_fundamental_data()`: Cached 24h, returns yfinance .info dict
  - `fetch_price_data()`: Cached 1h, returns current price + 52-week metrics
  - `fetch_complete_data()`: Convenience wrapper for both datasets
  - `batch_fetch_data()`: Multi-ticker fetching
  - Internal `_retry_fetch()` with configurable retry logic

- `src/data/cache.py` (58 lines)
  - `@cache_fundamental_data`: 24-hour TTL decorator
  - `@cache_price_data`: 1-hour TTL decorator
  - Uses Streamlit's native caching infrastructure

- `src/data/validator.py` (135 lines)
  - `validate_fundamental_data()`: Checks for required financial fields
  - `validate_price_data()`: Checks for price metrics
  - `clean_financial_data()`: Sanitizes None values and type conversions
  - Integrates with logger for data quality tracking

- `src/utils/config.py` (64 lines)
  - Cache TTL constants (FUNDAMENTAL_DATA_TTL, PRICE_DATA_TTL)
  - API retry configuration (MAX_RETRIES, RETRY_DELAY)
  - Exchange suffix mapping (NSE: .NS, BSE: .BO)
  - Screening thresholds (MIN_ROIC, MAX_DEBT_EQUITY, etc.)

- `src/utils/logger.py` (78 lines)
  - In-memory data quality issue tracking
  - `DataQualityIssue` dataclass for structured logging
  - `log_data_issue()`, `get_data_quality_log()` for UI integration
  - Issue type categories: fetch_failure, validation_error, incomplete_data

**Design Decisions**:
- Chose Streamlit's `@st.cache_data` over custom caching for simplicity
- Implemented dual TTL strategy to balance freshness vs API rate limits
- Used in-memory logging (not file-based) for real-time UI feedback
- Retry logic uses simple exponential backoff (2-second delay)

**Technical Notes**:
- All functions use type hints (Optional[dict], Optional[pd.DataFrame])
- Error handling never fails silently - all issues logged
- NSE tickers automatically get .NS suffix via `normalize_ticker()`
- yfinance .info dict is the primary data contract

### 2026-02-10 (Session 1) - Project Initialization
- Created `.venv` environment
- Installed core dependencies: streamlit, pandas, plotly, yfinance
- Established CLAUDE.md as living documentation
- Defined operational workflow and coding standards

---

## Architecture Notes

### Data Flow (Conceptual)
```
User Input (Tickers)
  → Data Layer (yfinance API + Caching)
    → Quant Layer (Metric Calculations)
      → Filtering & Ranking
        → UI Layer (Streamlit Display)
```

### Module Responsibilities

#### `src/data/` (✅ IMPLEMENTED)
- **fetcher.py**: yfinance API wrapper with retry logic, ticker normalization, financial statement fetching
- **cache.py**: Dual TTL caching decorators (24h fundamentals, 1h price)
- **validator.py**: Data quality validation, field sanitization

#### `src/utils/` (✅ IMPLEMENTED)
- **config.py**: Application constants (cache TTL, thresholds, exchange suffixes)
- **logger.py**: In-memory data quality issue tracking for UI display
- **ticker_lists.py**: Nifty 100 and S&P 500 ticker lists

#### `src/quant/` (✅ IMPLEMENTED)
- **metrics.py**: NOPAT-based ROIC, 3-year FCF validation, D/E ratio, value score calculation
- **screener.py**: Strict filtering pipeline, ranking algorithm, display formatting

#### `src/ui/` (✅ IMPLEMENTED)
- **sidebar.py**: Interactive controls (index selector, ROIC/D/E/price sliders, run button, Quant Mentor glossary)
- **components.py**: Reusable Streamlit widgets (metric cards, data table with tooltips, data quality report)
- **visualizations.py**: Plotly scatter plot with RdYlGn color scale (ROIC vs Price Discount)
- **deep_dive.py**: Per-stock analysis (Bollinger Bands, ROIC/FCF trends, P/E Mean Reversion, due diligence links)

---

## Decision Log

### 2026-02-10 (Session 7) - Professional Analytics & Education
- **Decision**: Tabbed layout for Results vs Deep Dive
  - **Rationale**: Clean UX separation prevents information overload
  - **Implementation**: `st.tabs(["Screening Results", "Deep Dive Analysis"])`
  - **Trade-off**: Extra click to access deep dive vs cluttered single-page scroll

- **Decision**: Refactor calculate_roic into year-indexed function
  - **Rationale**: Enables 3-year trend without duplicating NOPAT logic
  - **Implementation**: `calculate_roic_for_year(stmt, bs, year_index)`, original becomes wrapper
  - **Trade-off**: Slight indirection vs clean code reuse

- **Decision**: Compute normalized P/E from income statement Net Income
  - **Rationale**: yfinance .info only has point-in-time P/E, no historical P/E
  - **Implementation**: avg(Net Income / sharesOutstanding) for 3 years → normalized P/E
  - **Trade-off**: Approximation (uses current shares outstanding), but sufficient for mean reversion signal

- **Decision**: Store stocks_data in session state for deep dive
  - **Rationale**: Avoid redundant API calls; financial statements already fetched during screening
  - **Implementation**: `st.session_state.stocks_data = stocks_data` after batch_fetch
  - **Trade-off**: Higher memory (~480KB for 100 tickers) vs repeated API calls

- **Decision**: Currency auto-detection from index selection
  - **Rationale**: NIFTY100 trades in INR, SP500 trades in USD - obvious mapping
  - **Implementation**: `CURRENCY_CONFIG` dict in config.py, `get_currency_symbol()` helper
  - **Trade-off**: Simple mapping vs reading currency from yfinance .info (less reliable)

- **Decision**: Educational tooltips via st.column_config help parameter
  - **Rationale**: Non-intrusive - visible only on hover, doesn't clutter UI
  - **Implementation**: `help="..."` on ROIC, D/E, Value Score, 52w columns
  - **Trade-off**: Discoverability (users may not know to hover) vs always-visible descriptions

### 2026-02-10 (Session 6) - Ticker Limit & Data Sourcing
- **Decision**: Add dynamic ticker limit slider (10-500, default 100)
  - **Rationale**: Faster testing with small samples, flexibility for deep dives
  - **Implementation**: Slider in sidebar, `get_all_tickers(index, limit)` returns top N
  - **Trade-off**: Requires ticker lists to be pre-sorted by market cap

- **Decision**: Convert BRK.B → BRK-B for US tickers
  - **Rationale**: Yahoo Finance uses dashes for share classes, not dots
  - **Implementation**: `normalize_ticker()` replaces "." with "-" for NYSE/NASDAQ
  - **Trade-off**: Assumes all dot-containing US tickers need conversion

- **Decision**: Display "Screening Top N stocks by Market Cap" label
  - **Rationale**: Transparency about ticker selection, clarify not screening entire index
  - **Implementation**: Info banner above metric cards
  - **Trade-off**: Adds visual clutter vs user clarity (clarity wins)

- **Decision**: Smart re-fetch detection based on index/limit changes
  - **Rationale**: Avoid unnecessary API calls when only filters changed
  - **Implementation**: `config_requires_refetch()` checks index/limit, not ROIC/D/E
  - **Trade-off**: More complex state logic vs performance gain (future-ready)

### 2026-02-10 (Session 5) - Type Safety & DataFrame Separation
- **Decision**: Separate raw and formatted DataFrames
  - **Rationale**: Visualizations need numeric types, tables need readable strings
  - **Implementation**: Store both `results_df_raw` and `results_df_formatted` in session state
  - **Trade-off**: Doubled memory usage vs clean separation of concerns

- **Decision**: Add robust type conversion in visualization layer
  - **Rationale**: Defense-in-depth against string-formatted numeric columns
  - **Implementation**: `pd.to_numeric(errors='coerce')` + `dropna()` in `create_value_scatter_plot()`
  - **Trade-off**: Slight performance overhead vs guaranteed type safety

### 2026-02-10 (Session 4) - UI Layer Architecture
- **Decision**: Session state management for performance
  - **Rationale**: Avoid re-fetching data on every UI interaction (slider adjustments, re-runs)
  - **Implementation**: Store results_df, config, counts in `st.session_state`
  - **Trade-off**: Slightly more complex state logic vs significant performance gain

- **Decision**: RdYlGn color scale for scatter plot
  - **Rationale**: Intuitive color coding - green = good value, red = avoid
  - **Implementation**: Plotly Express with `color_continuous_scale='RdYlGn'`
  - **Trade-off**: Standard color scheme vs custom brand colors

- **Decision**: Modular UI separation (sidebar, visualizations, components)
  - **Rationale**: Reusability, testability, separation of concerns
  - **Implementation**: Three separate modules with clear responsibilities
  - **Trade-off**: More files vs monolithic app.py

- **Decision**: Wide page layout with two-column results display
  - **Rationale**: Scatter plot needs horizontal space, Top 5 provides context
  - **Implementation**: `layout="wide"`, `st.columns([2, 1])` for scatter + top picks
  - **Trade-off**: Less suitable for mobile vs standard layout

- **Decision**: Progressive disclosure for Data Quality Report
  - **Rationale**: Don't overwhelm users with technical details unless needed
  - **Implementation**: Expander collapsed by default, auto-expands if issues exist
  - **Trade-off**: Some users may miss important quality issues vs always visible

- **Decision**: CSV export for screening results
  - **Rationale**: Enable offline analysis, portfolio tracking, integration with other tools
  - **Implementation**: Streamlit download button with UTF-8 encoded CSV
  - **Trade-off**: Simple CSV vs more sophisticated export formats (Excel, JSON)

### 2026-02-10 (Session 3) - Quant Layer Architecture
- **Decision**: NOPAT-based ROIC calculation (Approach B - Deep Dive)
  - **Rationale**: Prioritize precision over speed for professional-grade analysis
  - **Implementation**: Fetch full financial statements (income, balance, cashflow)
  - **Trade-off**: More API calls and complexity vs simpler ROA proxy, but ensures accurate ROIC

- **Decision**: Strict 3-year positive FCF requirement
  - **Rationale**: No tolerance for cash-burning companies in value screening
  - **Implementation**: Validate `cashflow_statement.loc['Free Cash Flow']` for all 3 years
  - **Trade-off**: More restrictive filter may exclude turnaround candidates

- **Decision**: Weighted value score formula (60% ROIC, 40% Discount)
  - **Rationale**: Emphasize quality over price - Buffett's "wonderful company at fair price"
  - **Formula**: `(ROIC/0.15 × 0.6) + (abs(distance_from_high)/100 × 0.4)`
  - **Trade-off**: Quality bias vs equal weighting or discount-heavy approach

- **Decision**: STRICT filtering (Screener philosophy, not Ranker)
  - **Rationale**: Only show "Gold Standard" stocks that pass ALL filters
  - **Implementation**: Stocks failing ANY filter (ROIC, D/E, FCF, price) are excluded entirely
  - **Trade-off**: Fewer results vs showing all stocks with warnings/grades

- **Decision**: Hardcoded ticker lists (Nifty 100, S&P 500 top 100)
  - **Rationale**: Stability and reliability for MVP over dynamic fetching
  - **Implementation**: `src/utils/ticker_lists.py` with static lists
  - **Trade-off**: Requires quarterly maintenance vs auto-update from NSE/S&P APIs

- **Decision**: Financial statement row name flexibility
  - **Rationale**: yfinance schema varies by ticker/exchange (e.g., "Stockholders Equity" vs "Total Equity")
  - **Implementation**: `_extract_value()` helper tries multiple possible keys
  - **Trade-off**: More robust but adds complexity to metric calculations

### 2026-02-10 (Session 2) - Data Layer Architecture
- **Decision**: Dual cache TTL strategy (24h fundamentals, 1h price)
  - **Rationale**: Fundamental data changes slowly; price data needs freshness
  - **Trade-off**: Increased complexity vs single TTL, but better data freshness

- **Decision**: In-memory logging instead of file-based
  - **Rationale**: Real-time UI feedback, simpler implementation for MVP
  - **Trade-off**: Logs don't persist between sessions (acceptable for MVP)

- **Decision**: Simple retry logic (3 attempts, 2-second delay)
  - **Rationale**: Handles transient yfinance API failures without external dependencies
  - **Trade-off**: Not as sophisticated as tenacity library, but sufficient for MVP

- **Decision**: Use yfinance .info dict as primary data contract
  - **Rationale**: Well-documented, contains all needed fields for screening
  - **Trade-off**: Schema not fully stable, requires validation layer

- **Decision**: Predefined ticker lists (Nifty 100, S&P 500)
  - **Rationale**: Better UX than manual entry, ensures data quality
  - **Trade-off**: Requires maintenance if index constituents change

### 2026-02-10 (Session 1) - Project Foundation
- **Decision**: Use yfinance as primary data source
  - **Rationale**: Free, reliable, sufficient data for fundamental analysis
  - **Trade-off**: Rate limits require aggressive caching

- **Decision**: Streamlit for UI framework
  - **Rationale**: Rapid prototyping, native Python, built-in caching
  - **Trade-off**: Less customizable than React/Vue

---

## Future Enhancements (Backlog)
- [ ] Add sector-based peer comparison
- [ ] Implement DCF (Discounted Cash Flow) valuation model
- [ ] Export results to CSV/Excel
- [ ] Add historical performance backtesting
- [ ] Multi-threading for parallel ticker fetching
- [ ] Database layer for persistent storage (SQLite/PostgreSQL)

---

**Last Updated**: 2026-02-10 (Session 7 - Professional Analytics & Education Layer - v0.7.0)
**Maintained By**: Claude (Senior Quant Developer)
