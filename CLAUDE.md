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
**v1.1.0** - UI/UX Modernization (Midnight Finance Theme)

### Last Implementation
- **UI/UX Modernization (v1.1.0)**:
  - `src/ui/styles.py`: NEW (~350 lines) — Centralized design system
    - `COLORS` dict: 14-color Midnight Finance palette (dark navy, slate, emerald, rose, indigo, amber, violet)
    - `get_global_css()`: Full CSS stylesheet injected via `st.markdown` — Google Fonts (Inter), sidebar styling, tabs pill design, metric cards, expanders, buttons, scrollbar, progress bar
    - `get_plotly_theme()`: Unified dark Plotly layout dict for all charts (surface bg, border grid, themed hover labels)
    - `metric_card()`: HTML KPI card with accent left-border, delta display, box-shadow
    - `model_card()`: HTML card with top-accent border for forecast model breakdown
    - `top_pick_card()`: HTML card with rank badge, ticker, ROIC, score layout
    - `filter_chip()`: HTML pill badge for sidebar filter summary
    - `section_header()`: HTML header with accent underline bar
  - `app.py`: Global CSS injection via `st.markdown`, HTML section headers, styled info banner, card-based Top 5, spacer divs replacing `st.markdown("---")`
  - `src/ui/sidebar.py`: Custom HTML section headers, collapsed label visibility, filter chips replacing info box, styled sidebar footer with version
  - `src/ui/components.py`: Custom `metric_card()` HTML replacing `st.metric`, new `render_top_5_cards()` function, styled empty state, HTML header/footer
  - `src/ui/visualizations.py`: Dark Plotly theme via `get_plotly_theme()`, custom red-amber-green color scale, themed colorbar, dark marker borders
  - `src/ui/deep_dive.py`: Dark Plotly theme on all 4 chart types, indigo Bollinger band fill, amber ROIC mid-tier color, section headers, spacer divs
  - `src/ui/forecast_tab.py`: Dark Plotly theme on price target chart, `model_card()` HTML for 3-column breakdown, `metric_card()` for risk dashboard with conditional accent colors (green/amber/red), styled valuation summary cards
  - `src/utils/config.py`: Chart colors updated to Midnight Finance palette (emerald `#10B981`, rose `#EF4444`, indigo `#6366F1`, violet `#8B5CF6`)

- **Previous: Forecast & Valuation Tab (v1.0.0)**:
  - `src/quant/forecast.py`: NEW (~480 lines) — Multi-model forecasting engine
    - DCF Model: FCF projection with decaying growth, terminal value, WACC via CAPM
    - Earnings Multiple Model: EPS CAGR projection × target P/E (3-year normalized)
    - ROIC Growth Model: Sustainable growth = reinvestment rate × ROIC
    - Scenario analysis: Bull (no decay) / Base (linear decay to 3%) / Bear (50% growth)
    - Risk metrics: Beta, annualized volatility, max drawdown, Sharpe ratio
    - Composite forecast: Average of available models, market benchmark comparison
  - `src/ui/forecast_tab.py`: NEW (~380 lines) — Forecast tab UI
    - Summary table: All filtered stocks with price targets (6mo/1y/2y/5y), alpha, risk
    - Per-stock detail: Valuation summary cards, 5-year price target chart, model breakdown, risk dashboard, assumptions table
    - Price target chart: Bull/Base/Bear lines + market benchmark (Plotly)
  - `src/utils/config.py`: Added RISK_FREE_RATES, EQUITY_RISK_PREMIUM, MARKET_ANNUAL_RETURNS, TERMINAL_GROWTH_RATE, MAX_PROJECTION_GROWTH, scenario chart colors
  - `app.py`: Third tab "Forecast & Valuation", forecast session state caching, cache invalidation on re-screen

- **Previous: Fix Near 52w Low Filter (v0.9.1)**:
  - `src/quant/screener.py`: `apply_valuation_filter()` now filters on `distance_from_low <= near_low_threshold` instead of pre-baked boolean

- **Previous: SP500 Delisted Tickers & Rate Limit Resilience (v0.9.0)**:
  - `src/utils/ticker_lists.py`: Removed ANSS (acquired by Synopsys Jul 2025), HES (acquired by Chevron Jul 2025), DFS (acquired by Capital One May 2025)
  - `src/data/fetcher.py`: Rate limit detection via `_is_rate_limit_error()` — checks for "rate", "too many requests", "429" in error string
  - `src/data/fetcher.py`: Exponential backoff for rate limits — 5s, 10s, 20s, 40s, 80s (5 retries vs 3 for normal errors)
  - `src/data/fetcher.py`: `DEFAULT_MAX_WORKERS` reduced from 10 → 5 to prevent Yahoo throttling on 500-ticker runs
  - `src/utils/config.py`: Added `RATE_LIMIT_MAX_RETRIES=5`, `RATE_LIMIT_BASE_DELAY=5.0` constants
  - SP500_FULL: 498 → 495 tickers (3 delisted removed)

- **Previous: SP500 Ticker Fix (v0.8.6)**:
  - `src/utils/ticker_lists.py`: Removed `FI` from SP500_FULL — Fiserv changed ticker from FI (NYSE) to FISV (Nasdaq) in Nov 2025; FISV already existed in both SP500_TOP100 and SP500_FULL

- **Previous: NIFTY Ticker Fixes (v0.8.5)**:
  - `src/utils/ticker_lists.py`: TATAMOTORS → TMCV (Tata Motors demerged Oct 2025 into TMCV.NS commercial vehicles + TMPV.NS passenger vehicles; TMCV is larger by mcap)
  - `src/utils/ticker_lists.py`: ZOMATO → ETERNAL (Zomato renamed to Eternal Limited, Mar 2025; ZOMATO.NS is dead on yfinance)

- **Previous: FTSE Ticker Fixes & Error Logging Cleanup (v0.8.4)**:
  - `src/ui/deep_dive.py`: Fixed FTSE100 exchange mapping — was falling through to NYSE, causing dot-to-dash conversion (RMV.L → RMV-L)
  - `src/utils/ticker_lists.py`: BTR.L → BTRW.L (Barratt Redrow renamed), ICP.L → ICG.L (Intermediate Capital Group correct ticker)
  - `src/data/fetcher.py`: Refactored `_retry_fetch()` to log ONCE after all retries exhausted (was logging per-attempt, causing 3x duplicate entries)
  - `src/data/fetcher.py`: Moved all `log_data_issue()` calls out of inner `_fetch()` functions into `_retry_fetch()` via `failure_message` parameter
  - `src/ui/sidebar.py`: Version bumped to 0.8.4

- **Previous: yfinance curl_cffi Compatibility Fix (v0.8.3)**:
  - `src/data/fetcher.py`: Removed custom `requests.Session` (`get_yahoo_session()`) entirely
  - `src/data/fetcher.py`: Removed `import requests`, `import threading`, `_thread_local` storage
  - `src/data/fetcher.py`: All 6 `yf.Ticker()` calls now use default session (no `session=` param)
  - Root cause: yfinance v1.1.0 switched from `requests` to `curl_cffi` for HTTP
  - Fix: Let yfinance manage its own `curl_cffi` session internally

- **Previous: Concurrent Fetching (v0.8.2)**:
  - `src/data/fetcher.py`: `batch_fetch_deep_data()` uses `ThreadPoolExecutor(max_workers=10)`
  - `src/data/fetcher.py`: `batch_fetch_data()` also parallelized with same pattern
  - `src/data/fetcher.py`: Thread-local sessions via `threading.local()` (replaces global singleton)
  - `src/data/fetcher.py`: `progress_callback` parameter for real-time UI updates
  - `app.py`: Per-ticker progress bar ("Fetching... 47/100 tickers") with 0-70% range
  - Expected: ~60-90 seconds for 100 tickers (was 10+ minutes sequential)

- **Previous: FTSE Ticker Hardening & Anti-Throttle (v0.8.1)**:
  - ALL FTSE tickers hardcoded with `.L` suffix; BDEV → BTR.L, ICAG → IAG.L, SMDS removed
  - Anti-throttle browser User-Agent session for all yf.Ticker() calls

- **Previous: Maintenance & FTSE 100 Expansion (v0.8.0)**:
  - `src/utils/ticker_lists.py`: ADANITRANS → ADANIENSOL, MCDOWELL-N → UNITDSPR, IDEA → LTIM
  - `src/data/fetcher.py`: Empty data returns handled silently (no log spam for FI etc.)
  - `src/utils/ticker_lists.py`: NEW `FTSE_100` list, `get_ftse_100()`, `get_all_tickers()` supports "FTSE100"
  - `src/ui/sidebar.py`: "FTSE 100" radio button option added
  - `src/utils/config.py`: GBP currency (£), LSE exchange suffix, FTSE100 due diligence URLs
  - `app.py`: Exchange mapping and display name for FTSE100
  - `src/data/validator.py`: DELETED (dead code)
  - `src/data/fetcher.py`: Removed duplicate `fetch_complete_data`

- **Previous: Deep Dive Analysis (v0.7.0)**:
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
11. ✅ ~~Fix broken tickers (ADANITRANS, MCDOWELL-N, LTI/MINDTREE)~~
12. ✅ ~~Add FTSE 100 (UK Market) support~~
13. ✅ ~~Code cleanup (dead validator.py, duplicate fetch_complete_data)~~
14. Test full screening on FTSE 100 in production
15. ✅ ~~FTSE ticker hardening (hardcode .L suffix, fix BDEV/ICAG/SMDS)~~
16. ✅ ~~Anti-throttle User-Agent session for yfinance~~
17. ✅ ~~Concurrent fetching with ThreadPoolExecutor (performance fix)~~
18. ✅ ~~Forecast & Valuation tab (DCF, Earnings Multiple, ROIC Growth models)~~
19. ✅ ~~UI/UX Modernization (Midnight Finance dark theme)~~

### Known Issues
- FTSE_100 list has 99 tickers (SMDS removed due to acquisition) — add replacement when next constituent is confirmed
- SP500_FULL has 495 tickers (FI, ANSS, HES, DFS removed — acquisitions/delistings)
- CBOE and NDAQ may show "Balance sheet data unavailable" — financial exchanges have non-standard statement formats

---

## Implementation History

### 2026-02-11 (Session 18) - UI/UX Modernization (v1.1.0)
**New Files Created**:
- `src/ui/styles.py` (~350 lines) — Centralized "Midnight Finance" design system

**Design System** (`src/ui/styles.py`):
- **COLORS dict**: 14-color dark palette — bg_primary (#0E1117), surface (#1B2332), surface_elevated (#232F3E), border (#2D3B4E), text_primary (#F0F2F5), text_secondary (#8899A6), text_muted (#5C6B7A), accent_green (#10B981), accent_red (#EF4444), accent_blue (#6366F1), accent_amber (#F59E0B), accent_purple (#8B5CF6)
- **get_global_css()**: Full CSS injection — Google Fonts (Inter 400-700), sidebar surface bg, tab pill design (active = indigo), metric card borders, expander styling, button gradient (indigo→violet), download/link button hover states, progress bar gradient, custom scrollbar, DataFrame rounded borders
- **get_plotly_theme()**: Shared dark layout dict — surface bg, border gridlines, themed hover labels, Inter font, secondary text colors for axes/labels
- **HTML component helpers**: `metric_card()` (accent left-border KPI), `model_card()` (top-accent border), `top_pick_card()` (rank badge + metrics), `filter_chip()` (pill badge), `section_header()` (accent underline bar)

**Files Modified (Style-Only Changes)**:
- `app.py`: CSS injection at top (`get_global_css()`), HTML section headers, styled info banner replacing emoji st.info, card-based Top 5 via `render_top_5_cards()`, HTML "How to Read" card, spacer divs replacing `st.markdown("---")`
- `src/ui/sidebar.py`: Custom HTML section headers (uppercase, text-secondary), collapsed label visibility on radio/sliders, `filter_chip()` pills for current thresholds, HTML styled footer with version 1.1.0
- `src/ui/components.py`: `metric_card()` HTML replacing `st.metric`, new `render_top_5_cards()` function, styled empty state (centered icon + numbered steps), HTML header (no emoji, text gradient), HTML footer (centered, muted, no emoji)
- `src/ui/visualizations.py`: `get_plotly_theme()` applied, custom color_scale (red→amber→green→light emerald), themed colorbar and marker borders
- `src/ui/deep_dive.py`: `get_plotly_theme()` on all 4 chart types, indigo Bollinger band fill (rgba 99,102,241), amber color for ROIC 10-15%, `section_header()` replacing `st.subheader`, spacer divs replacing `st.markdown("---")`
- `src/ui/forecast_tab.py`: `get_plotly_theme()` on price target chart, `model_card()` HTML for 3-column DCF/Earnings/ROIC breakdown, `metric_card()` for all 4 risk metrics with conditional accent (green/amber/red), `metric_card()` for valuation summary, `section_header()` throughout
- `src/utils/config.py`: Chart colors updated — POSITIVE: #10B981, NEGATIVE: #EF4444, NEUTRAL: #6366F1, BULL: #10B981, BASE: #6366F1, BEAR: #EF4444, MARKET: #8B5CF6

**Design Decisions**:
- **Dark-first theme**: Matches Streamlit's default dark mode; financial dashboards look more professional on dark backgrounds. Bloomberg Terminal, TradingView, and Linear.app all use dark themes.
- **Inter font**: Industry standard for data-dense UIs — has tabular numerals, excellent readability at small sizes, widely available via Google Fonts CDN. No new pip dependency.
- **CSS injection over custom components**: Using `st.markdown(unsafe_allow_html=True)` keeps the stack simple — no JavaScript, no external Streamlit component packages. All styling is pure CSS + inline HTML.
- **Plotly theme dict pattern**: Single `get_plotly_theme()` function returns a layout dict that all charts call via `fig.update_layout(**theme)`. Ensures visual consistency across 8+ chart types without code duplication.
- **Conditional accent colors**: Risk dashboard cards use green/amber/red accents based on actual metric values (e.g., beta < 0.8 = green, > 1.3 = red). This is purely cosmetic — no logic changes.
- **No emojis in UI**: Replaced all emoji prefixes (📈📊✅🔍 etc.) with clean typography. Professional fintech products don't use emojis in navigation or headers.
- **Pill-shaped filter chips**: Replaced `st.sidebar.info()` filter summary with styled pill badges. More compact, looks like a modern filter UI (think Figma, Linear).
- **Card-based Top 5**: Replaced plain `st.dataframe` with custom HTML cards featuring rank badges, ROIC, and Value Score. Each card has consistent sizing and hover-ready styling.

**Technical Notes**:
- Google Fonts CSS loaded via `@import url()` in the injected stylesheet — single HTTP request, cached by browser
- All HTML components use inline styles (no external CSS classes) for maximum Streamlit compatibility
- `unsafe_allow_html=True` is required for all `st.markdown()` calls with custom HTML — this is Streamlit's standard pattern for custom styling
- The `page_icon="📈"` is kept in `st.set_page_config` (browser tab only, not visible in app)
- Zero new pip dependencies — only uses existing streamlit, plotly, pandas

### 2026-02-11 (Session 17) - Forecast & Valuation Tab (v1.0.0)
**New Files Created**:
- `src/quant/forecast.py` (~480 lines) — Multi-model forecasting engine
- `src/ui/forecast_tab.py` (~380 lines) — Forecast tab UI rendering

**Forecasting Engine** (`src/quant/forecast.py`):
- **Model 1: Simplified DCF**
  - `calculate_fcf_cagr()`: 3-year FCF compound annual growth rate
  - `calculate_wacc()`: CAPM-based cost of equity + debt-weighted WACC
  - `calculate_dcf_valuation()`: Project FCF 5 years → terminal value → PV → intrinsic value/share
  - Net debt subtracted from enterprise value for equity value
  - Horizon prices: converge from current to intrinsic (10%/20%/40%/100% at 6mo/1y/2y/5y)

- **Model 2: Earnings Multiple**
  - `calculate_eps_cagr()`: 3-year EPS growth rate
  - `calculate_earnings_multiple_valuation()`: Project EPS × target P/E at each horizon
  - Target P/E priority: 3-year normalized > forwardPE > trailingPE

- **Model 3: ROIC Growth**
  - `calculate_roic_growth_valuation()`: Sustainable growth = reinvestment_rate × ROIC
  - Reinvestment rate from payoutRatio, default 60%
  - Project earnings at sustainable growth, apply trailing P/E

- **Scenario Analysis** (`_apply_scenario_growth()`):
  - Bull: Historical growth maintained, capped at 30%
  - Base: Linear decay from historical to 3% terminal growth over 5 years
  - Bear: 50% of historical growth, same decay pattern

- **Risk Metrics** (`calculate_risk_metrics()`):
  - Beta (from yfinance, default 1.0)
  - Annual volatility: std(daily returns) × sqrt(252)
  - Max drawdown: worst peak-to-trough over 1 year
  - Sharpe ratio: (projected return - risk_free) / volatility

- **Composite** (`calculate_composite_forecast()`):
  - Runs all 3 models × 3 scenarios per stock
  - Composite = average of available models (graceful None handling)
  - Alpha = stock projected 1Y return - market expected 1Y return

**Forecast UI** (`src/ui/forecast_tab.py`):
- Summary table: Ticker, Price, DCF Value, Margin of Safety, 6mo/1y/2y/5y targets, Alpha, Beta, Vol
- Per-stock detail (selectbox):
  - Valuation summary: 4 metric cards (price, DCF, earnings, margin of safety)
  - 5-year price target chart: Bull/Base/Bear + Market benchmark lines (Plotly)
  - Model breakdown: 3-column DCF/Earnings/ROIC with key inputs and outputs
  - Risk dashboard: Beta, Volatility, Max Drawdown, Sharpe as metric cards
  - Assumptions table: All model inputs (Rf, ERP, WACC, growth rates, P/E, etc.)

**Config Additions** (`src/utils/config.py`):
- `RISK_FREE_RATES`: India 7.0%, US 4.5%, UK 4.5%
- `EQUITY_RISK_PREMIUM`: 5.5% global
- `MARKET_ANNUAL_RETURNS`: Nifty 12%, S&P 10%, FTSE 8%
- `TERMINAL_GROWTH_RATE`: 3% GDP proxy
- `MAX_PROJECTION_GROWTH`: 30% cap
- `CHART_COLOR_BULL/BASE/BEAR/MARKET`: Scenario chart colors

**App Changes** (`app.py`):
- Third tab: "Forecast & Valuation"
- Session state: `forecast_df`, `forecast_data`, `forecast_index`, `forecast_tickers`
- Forecast cache invalidated on re-screening

**Design Decisions**:
- **No new API calls**: All valuation models use data already in `stocks_data` (session state).
  Historical prices for volatility use `fetch_historical_prices` (cached 24h).
- **Graceful degradation**: Each model returns None independently. Composite averages
  whatever models succeed. Stocks with 0 successful models show "insufficient data".
- **Convergence-based DCF horizons**: Rather than complex intermediate DCF recalculations,
  price converges linearly from current to intrinsic over time (10%→20%→40%→100%).
  Pragmatic approximation that avoids over-engineering.
- **Growth decay**: Base case decays historical growth toward GDP (3%) over 5 years.
  Prevents unrealistic extrapolation of high short-term growth rates.
- **30% growth cap**: Even bull case capped at 30% CAGR. Prevents absurd projections
  from stocks with temporarily explosive growth.
- **Default beta 1.0**: Stocks without yfinance beta (rare for large-caps) default to
  market-average risk. Better than failing the entire model.
- **Forecast caching**: Computed once per screening run, stored in session state.
  Invalidated when new screening runs. Per-stock selectbox doesn't re-compute.

### 2026-02-11 (Session 16) - Fix Near 52w Low Filter Ignoring User Threshold (v0.9.1)
**Bug Fix** (`src/quant/screener.py`):
- **Symptom**: Changing "Price Near 52w Low" slider from 10% to 20% produced identical results
- **Root Cause**: Two-part disconnect between user's slider value and actual filtering:
  1. `calculate_all_metrics()` in `metrics.py:581` hardcoded `is_near_52w_low(data, threshold_pct=10.0)` —
     the `near_52w_low` boolean was always baked at 10% regardless of user input
  2. `apply_valuation_filter()` in `screener.py:158` filtered on `df['near_52w_low'] == True` —
     ignoring its own `near_low_threshold` parameter entirely
- **Fix**: Replaced boolean filter with numeric comparison:
  - Old: `df[df['near_52w_low'] == True]`
  - New: `df[df['distance_from_low'].notna() & (df['distance_from_low'] <= near_low_threshold)]`
- `distance_from_low` (% above 52w low) was already computed correctly in `calculate_all_metrics()`
- No changes needed upstream — `app.py` and `screen_stocks()` already passed the threshold correctly

**Design Decision**:
- Used existing `distance_from_low` numeric column rather than threading threshold through
  `calculate_all_metrics()` — cleaner, avoids modifying the metrics API surface
- `near_52w_low` boolean and `is_near_52w_low()` function left intact as informational fields

### 2026-02-11 (Session 15) - SP500 Delisted Tickers & Rate Limit Resilience (v0.9.0)
**Delisted Tickers Removed (S&P 500)**:
- `ANSS` → removed: Ansys acquired by Synopsys, delisted from Nasdaq Jul 17, 2025
- `HES` → removed: Hess acquired by Chevron, delisted from NYSE Jul 18, 2025
- `DFS` → removed: Discover Financial acquired by Capital One, delisted from NYSE May 19, 2025
- SP500_FULL: 498 → 495 tickers

**Rate Limit Resilience** (`src/data/fetcher.py`):
- Problem: Full SP500 (498 tickers) with 10 concurrent workers triggered Yahoo "Too Many Requests"
  after ~350 tickers. 10 workers × 5 API calls/ticker = ~50 in-flight requests at peak.
- Added `_is_rate_limit_error()`: Detects rate limit exceptions ("rate", "too many requests", "429")
- `_retry_fetch()` now uses exponential backoff for rate limits:
  - Normal errors: 3 retries, 2s fixed delay
  - Rate limit errors: 5 retries, exponential backoff (5s, 10s, 20s, 40s, 80s)
  - On first rate limit hit, retry count automatically upgrades from 3 → 5
- `DEFAULT_MAX_WORKERS` reduced: 10 → 5 (halved in-flight requests)
- New config constants in `src/utils/config.py`:
  - `RATE_LIMIT_MAX_RETRIES = 5`
  - `RATE_LIMIT_BASE_DELAY = 5.0` (seconds, doubles each attempt)

**Design Decisions**:
- **5 workers default**: 5 × 5 = ~25 in-flight requests — well within Yahoo's tolerance
  even for 500-ticker runs. Trade-off: ~2x slower than 10 workers (~120-180s vs 60-90s)
  but dramatically fewer rate limit failures
- **Exponential backoff**: Rate limits are global (per-IP), so waiting longer gives the
  server time to reset. Doubling pattern (5→10→20→40→80) provides up to 155s total wait
- **Auto-upgrade retry count**: When a rate limit is first detected, retry count silently
  increases from 3 to 5 — more chances to recover without changing normal error handling

### 2026-02-11 (Session 14) - SP500 Ticker Fix (v0.8.6)
**Ticker Fix (S&P 500)**:
- `FI` → removed: Fiserv changed ticker from FI (NYSE) to FISV (Nasdaq) effective Nov 11, 2025
- `FISV` already existed in both SP500_TOP100 (line 73) and SP500_FULL (line 112)
- Simply removed the stale `FI` entry from SP500_FULL to eliminate duplicate
- SP500_FULL: 499 → 498 tickers (498 unique)

### 2026-02-11 (Session 13) - NIFTY Ticker Fixes (v0.8.5)
**Ticker Fixes (NIFTY 100)**:
- `TATAMOTORS` → `TMCV`: Tata Motors demerged in October 2025 into two entities:
  - `TMCV.NS` — Tata Motors Limited (Commercial Vehicles), mcap ~₹1.8T
  - `TMPV.NS` — Tata Motors Passenger Vehicles Limited, mcap ~₹1.4T
  - Old `TATAMOTORS.NS` returns 404 from yfinance (dead ticker)
  - Chose TMCV as replacement (larger entity, retains the "Tata Motors" name)
- `ZOMATO` → `ETERNAL`: Zomato renamed to Eternal Limited in March 2025
  - `ZOMATO.NS` returns `quoteType: NONE` with no price/financial data
  - `ETERNAL.NS` is the active ticker, mcap ~₹2.7T

**Technical Notes**:
- Both corporate actions happened in 2025 (before our project started) but yfinance
  retained stale mappings until recently
- TATAMOTORS.NS now redirects to TATAMOTOR.NS which itself says "SEE <TATAMOTORS.NS>" — circular redirect, completely broken
- NSE website still uses ZOMATO as symbol, but Yahoo Finance migrated to ETERNAL

### 2026-02-11 (Session 12) - FTSE Ticker Fixes & Error Logging Cleanup (v0.8.4)
**Bug Fixes**:
- **RMV.L → RMV-L Deep Dive bug** (`src/ui/deep_dive.py`):
  - Root cause: `exchange` mapping only knew NIFTY100→NSE, everything else fell to `None`
  - `None` triggered `exchange or "NYSE"` → NYSE → dot-to-dash conversion on `.L` tickers
  - Fix: Added `exchange_map = {"NIFTY100": "NSE", "FTSE100": "LSE"}` dict lookup
  - Now FTSE tickers like RMV.L are passed correctly to `fetch_historical_prices()`

- **BTR.L → BTRW.L** (`src/utils/ticker_lists.py`):
  - Barratt Redrow completed corporate rename; BTR.L returns no data from yfinance
  - Correct Yahoo Finance ticker is now BTRW.L

- **ICP.L → ICG.L** (`src/utils/ticker_lists.py`):
  - Intermediate Capital Group's correct Yahoo Finance ticker is ICG.L, not ICP.L
  - ICP.L returns no data (empty .info, no financial statements)

**Error Logging Refactor** (`src/data/fetcher.py`):
- Problem: Every data issue logged 3x (once per retry attempt) — `_fetch()` inner functions
  called `log_data_issue()` directly, and `_retry_fetch()` called them 3 times
- Fix: Moved ALL `log_data_issue()` calls out of inner `_fetch()` functions
- `_retry_fetch()` now accepts `failure_message` parameter and logs ONCE after exhausting retries
- Two log paths: `last_error` (exception) → "Max retries exceeded: {error}", or
  `None` return → custom `failure_message` (e.g., "Income statement data unavailable")
- Result: Data Quality Report now shows 1 entry per issue instead of 3

**Version**: Sidebar bumped to 0.8.4

### 2026-02-11 (Session 11) - yfinance curl_cffi Compatibility Fix (v0.8.3)
**Root Cause**:
- yfinance v1.1.0 replaced `requests` with `curl_cffi` for HTTP internals
- Our custom `requests.Session` (added in v0.8.1 for anti-throttle User-Agent) is now rejected
- Error: "Yahoo API requires curl_cffi session not `<class 'requests.sessions.Session'>`"
- ALL tickers on ALL markets affected (100% fetch failure rate)

**Changes to `src/data/fetcher.py`**:
- Removed `import requests` and `import threading`
- Removed `_thread_local = threading.local()` thread-local storage
- Removed `get_yahoo_session()` function entirely (~20 lines)
- Removed `session=get_yahoo_session()` from all 6 `yf.Ticker()` calls:
  - `fetch_fundamental_data()`, `fetch_price_data()`, `fetch_historical_prices()`
  - `fetch_income_statement()`, `fetch_balance_sheet()`, `fetch_cashflow_statement()`
- ThreadPoolExecutor concurrency preserved (unaffected by session removal)

**Design Decisions**:
- **Let yfinance manage sessions**: yfinance v1.1.0 uses `curl_cffi` internally with its own
  session management. Custom sessions are no longer needed or supported.
- **No replacement anti-throttle**: `curl_cffi` mimics browser TLS fingerprints natively,
  which is more effective than a User-Agent header alone. Throttling protection is now built-in.
- **Thread safety**: yfinance's internal session handling works with ThreadPoolExecutor.
  Verified: SHEL.L, RELIANCE.NS, AAPL all fetch correctly without custom session.

**Technical Notes**:
- yfinance v1.1.0 installed in .venv (breaking change from earlier versions)
- `requests` no longer imported (was transitive dependency, still available but unused)
- `threading` no longer imported (`concurrent.futures` handles thread pool independently)
- Tested: FTSE (SHEL.L), NIFTY (RELIANCE.NS), SP500 (AAPL) — all returning data correctly

### 2026-02-11 (Session 10) - Concurrent Fetching & Performance Restoration (v0.8.2)
**Performance Fix**:
- Root cause: `batch_fetch_deep_data` was a sequential loop — 100 tickers × 5 HTTP calls = 500 serial requests
- The custom `requests.Session` removed yfinance internal connection reuse, compounding latency
- Solution: `ThreadPoolExecutor(max_workers=10)` with `as_completed()` pattern

**Changes to `src/data/fetcher.py`**:
- Added imports: `threading`, `concurrent.futures.ThreadPoolExecutor`, `as_completed`
- `get_yahoo_session()`: Now uses `threading.local()` for thread-local sessions (was global singleton)
  - Each worker thread gets its own `requests.Session` with browser User-Agent
  - Thread-safe: no shared session state between concurrent fetches
- `batch_fetch_deep_data()`: Rewrote with ThreadPoolExecutor
  - `max_workers=10`: 10 tickers fetched concurrently
  - `progress_callback`: Optional `Callable[[int, int], None]` for UI updates
  - Per-future exception handling: one failed ticker doesn't crash the batch
- `batch_fetch_data()`: Same parallel pattern applied
- Added `DEFAULT_MAX_WORKERS = 10` module constant

**Changes to `app.py`**:
- `run_screening()`: New `on_ticker_fetched()` callback updates progress bar per-ticker
  - Progress range 0-70% for fetch phase (was static 0→50% jump)
  - Text shows "Fetching... (47/100 tickers)" for user visibility
  - Callback runs in main Streamlit thread via `as_completed()` — safe for UI updates

**Design Decisions**:
- **10 workers**: 10 concurrent tickers × 5 requests each = ~50 in-flight HTTP requests
  Conservative enough to avoid Yahoo Finance rate-limiting
  Aggressive enough for ~8-10x speedup over sequential
- **Thread-local sessions**: `requests.Session` is NOT thread-safe per docs
  `threading.local()` gives each worker its own session + connection pool
  Avoids shared-state corruption while preserving per-thread connection reuse
- **as_completed() for progress**: Yields futures in the calling (main) thread
  Safe to call `st.progress()` and `st.empty().text()` from there
  No need for thread-safe queue or lock for Streamlit UI updates

**Technical Notes**:
- `st.cache_data` is internally thread-safe (uses locks) — cached functions work from worker threads
- `threading`, `concurrent.futures` are stdlib — no new dependencies
- `typing.Callable` used for progress_callback type hint (Python 3.9 compatible)
- Expected performance: ~60-90 seconds for 100 tickers (vs 10+ minutes sequential)

### 2026-02-11 (Session 9) - FTSE Ticker Hardening & Anti-Throttle Session (v0.8.1)
**FTSE 100 Ticker Fixes**:
- Hardcoded `.L` suffix on ALL FTSE_100 tickers (was relying on normalize_ticker)
- `BDEV` → `BTR.L` (Barratt Developments renamed to Barratt Redrow)
- `ICAG` → `IAG.L` (correct Yahoo Finance ticker for International Airlines Group)
- `SMDS` (DS Smith) REMOVED — undergoing acquisition, returning unstable data
- List now has 99 tickers (down from 100)

**Anti-Throttle Session**:
- Added `import requests` to fetcher.py
- Added `get_yahoo_session()` — module-level singleton `requests.Session`
- Browser User-Agent header: Chrome/91.0 on Windows 10
- All 6 `yf.Ticker()` calls now pass `session=get_yahoo_session()`:
  - `fetch_fundamental_data()`, `fetch_price_data()`, `fetch_historical_prices()`
  - `fetch_income_statement()`, `fetch_balance_sheet()`, `fetch_cashflow_statement()`
- Fixes intermittent "Incomplete Data" / "Fetch Failure" for valid NSE stocks

**Design Decisions**:
- **Hardcoded .L suffix**: Prevents ambiguity where bare tickers (BA, AAL, RR) could be
  confused with US tickers. normalize_ticker() detects existing .L and skips appending.
  Trade-off: FTSE list format differs from NIFTY/SP500, but eliminates a class of bugs.

- **Singleton session pattern**: Single `requests.Session` reused across all fetches.
  Avoids creating new sessions per-ticker (connection pooling benefits).
  Module-level `_yahoo_session` initialized lazily on first call.

- **SMDS removal without replacement**: Preferred data integrity over round-number list size.
  Will add replacement when next FTSE 100 constituent is confirmed.

**Technical Notes**:
- `requests` is already a transitive dependency of `yfinance` — no new pip install needed
- User-Agent string uses Chrome 91 (widely recognized, low blocking risk)
- Session singleton is NOT thread-safe, but Streamlit runs single-threaded per user
- Python 3.9.13 compatibility maintained

### 2026-02-11 (Session 8) - Maintenance, Data Quality & FTSE 100 Expansion (v0.8.0)
**Ticker Fixes (NIFTY 100)**:
- `ADANITRANS` → `ADANIENSOL` (Adani Energy Solutions renamed)
- `MCDOWELL-N` → `UNITDSPR` (United Spirits renamed)
- `IDEA` → `LTIM` (Vodafone Idea removed, LTIMindtree added from LTI/MINDTREE merger)
- `TATAMOTORS` and `ZOMATO`: Confirmed correct, .NS suffix auto-applied by normalize_ticker()

**Ticker Fixes (S&P 500)**:
- `FI`: Kept in list. Modified `fetch_fundamental_data()` to return None silently for empty data
  instead of calling `log_data_issue()` — prevents Data Quality Report spam
- Note: `FISV` (actual Fiserv ticker) already present in both SP500_TOP100 and SP500_FULL

**FTSE 100 (New Market)**:
- Added `FTSE_100` list: 100 UK stocks sorted by market cap (SHEL, AZN, HSBA, ... WISE)
  - Tickers stored WITHOUT .L suffix (normalize_ticker adds it when exchange="LSE")
  - 5 tiers: Mega Cap (>£50B), Large Cap, Mid-Large Cap, Mid Cap, Lower Mid Cap
- Added `get_ftse_100()` helper function
- Updated `get_all_tickers()` to accept "FTSE100" index key
- Sidebar: Added "FTSE 100" radio button via index_map dict (replaced if/else)
- Config: `CURRENCY_CONFIG["FTSE100"]` = £/GBP
- Config: `EXCHANGE_SUFFIXES["LSE"]` = ".L"
- Config: `DUE_DILIGENCE_URLS["FTSE100"]` for Yahoo Finance
- App: `exchange_map` dict for NSE/LSE/None routing
- App: `index_display_names` dict for UI display

**Code Cleanup**:
- Deleted `src/data/validator.py` (150 lines) — zero imports across entire codebase
- Removed duplicate `fetch_complete_data()` in fetcher.py (lines 323-354 shadowed lines 187-218)

**Design Decisions**:
- **FTSE tickers without .L suffix**: Consistent with NIFTY pattern (normalize_ticker adds suffix)
  - normalize_ticker("SHEL", "LSE") → "SHEL.L"
  - normalize_ticker("BT-A", "LSE") → "BT-A.L"
  - No dot-to-dash conversion for LSE (only applies to NYSE/NASDAQ/None)

- **IDEA → LTIM replacement**: Vodafone Idea is no longer Nifty 100 constituent (~small cap)
  - Frees slot for LTIMindtree which is a major IT company
  - Maintains NIFTY_100 at exactly 100 entries

- **Silent empty data handling**: Removed log_data_issue() call for empty yfinance returns
  - Tickers like FI consistently return empty — logging every time clutters Data Quality Report
  - Retry logic still logs actual fetch failures (network errors, timeouts)

- **index_map dict in sidebar**: Replaced if/else chain with dict lookup
  - Cleaner, extensible pattern for adding future markets
  - Same pattern used for exchange_map and index_display_names in app.py

**Technical Notes**:
- FTSE_100 list should be updated quarterly as index constituents change
- Some FTSE tickers share symbols with US tickers (BA=BAE Systems vs Boeing, AAL=Anglo American vs American Airlines) — no conflict since different exchange suffixes
- Python 3.9.13 compatibility maintained (typing.Final, typing.List, typing.Optional)
- Version bumped to 0.8.0 in sidebar footer

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
- ~~**validator.py**~~: DELETED in v0.8.0 (unused dead code)

#### `src/utils/` (✅ IMPLEMENTED)
- **config.py**: Application constants (cache TTL, thresholds, exchange suffixes)
- **logger.py**: In-memory data quality issue tracking for UI display
- **ticker_lists.py**: Nifty 100, S&P 500, and FTSE 100 ticker lists

#### `src/quant/` (✅ IMPLEMENTED)
- **metrics.py**: NOPAT-based ROIC, 3-year FCF validation, D/E ratio, value score calculation
- **screener.py**: Strict filtering pipeline, ranking algorithm, display formatting
- **forecast.py**: Multi-model forecasting (DCF, Earnings Multiple, ROIC Growth), scenario analysis, risk metrics, composite forecasts

#### `src/ui/` (✅ IMPLEMENTED)
- **styles.py**: Midnight Finance design system (color palette, global CSS, Plotly dark theme, HTML card helpers)
- **sidebar.py**: Interactive controls (index selector, ROIC/D/E/price sliders, run button, Quant Mentor glossary)
- **components.py**: Reusable Streamlit widgets (metric cards, data table with tooltips, data quality report)
- **visualizations.py**: Plotly scatter plot with custom color scale (ROIC vs Price Discount)
- **deep_dive.py**: Per-stock analysis (Bollinger Bands, ROIC/FCF trends, P/E Mean Reversion, due diligence links)
- **forecast_tab.py**: Forecast & Valuation tab (summary table, price target charts, model breakdown, risk dashboard, assumptions)

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
- [x] ~~Implement DCF (Discounted Cash Flow) valuation model~~ (v1.0.0)
- [x] ~~Export results to CSV/Excel~~ (forecast CSV export in v1.0.0)
- [ ] Add historical performance backtesting
- [x] ~~Multi-threading for parallel ticker fetching~~ (v0.8.2)
- [ ] Database layer for persistent storage (SQLite/PostgreSQL)

---

**Last Updated**: 2026-02-11 (Session 18 - UI/UX Modernization - v1.1.0)
**Maintained By**: Claude (Senior Quant Developer)
