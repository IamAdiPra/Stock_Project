"""
Hardcoded ticker lists for Nifty 100, S&P 500, and FTSE 100 indices.
These lists are SORTED BY MARKET CAPITALIZATION (descending).
Lists are stable for MVP and should be updated quarterly.
"""

from typing import Final, List, Optional

# ==================== NIFTY 100 ====================
# National Stock Exchange of India - Top 100 companies
# Last Updated: 2026-02-10
# Note: Tickers will be normalized with .NS suffix by fetcher module

NIFTY_100: Final[List[str]] = [
    # Nifty 50 Core
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
    "ICICIBANK", "BHARTIARTL", "ITC", "SBIN", "LT",
    "BAJFINANCE", "KOTAKBANK", "HCLTECH", "ASIANPAINT", "AXISBANK",
    "MARUTI", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NESTLEIND",
    "WIPRO", "NTPC", "ONGC", "POWERGRID", "TMCV",
    "BAJAJFINSV", "TECHM", "ADANIENT", "JSWSTEEL", "DIVISLAB",
    "HINDALCO", "INDUSINDBK", "TATASTEEL", "COALINDIA", "M&M",
    "CIPLA", "DRREDDY", "EICHERMOT", "APOLLOHOSP", "TATACONSUM",
    "GRASIM", "ADANIPORTS", "BRITANNIA", "HEROMOTOCO", "SBILIFE",
    "BAJAJ-AUTO", "SHREECEM", "HDFCLIFE", "UPL", "BPCL",

    # Nifty Next 50
    "ADANIGREEN", "ADANIENSOL", "AMBUJACEM", "BANDHANBNK", "BEL",
    "BERGEPAINT", "BOSCHLTD", "CHOLAFIN", "COLPAL", "DABUR",
    "DLF", "GAIL", "GODREJCP", "HAVELLS", "HINDZINC",
    "ICICIPRULI", "INDIGO", "IOC", "JINDALSTEL", "LUPIN",
    "MARICO", "UNITDSPR", "MUTHOOTFIN", "NMDC", "NYKAA",
    "OFSS", "PAGEIND", "PETRONET", "PIDILITIND", "PNB",
    "RECLTD", "SAIL", "SBICARD", "SIEMENS", "TATAPOWER",
    "TORNTPHARM", "TRENT", "VEDL", "ETERNAL", "ABCAPITAL",
    "BANKBARODA", "CANBK", "LTIM", "PFC", "INDUSTOWER",
    "ICICIGI", "MOTHERSON", "PIIND", "TVSMOTOR", "VOLTAS"
]

# ==================== S&P 500 (Top 100 by Market Cap) ====================
# United States - Major Large-Cap Companies
# Last Updated: 2026-02-10
# Note: These tickers don't need suffix (NYSE/NASDAQ default)

SP500_TOP100: Final[List[str]] = [
    # Mega Cap Tech (FAANG+)
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "V", "UNH",

    # Large Cap Tech
    "JNJ", "WMT", "JPM", "MA", "PG",
    "XOM", "HD", "CVX", "MRK", "ABBV",
    "LLY", "AVGO", "COST", "PEP", "KO",
    "ADBE", "TMO", "MCD", "CSCO", "ACN",
    "NFLX", "ABT", "CRM", "DHR", "ORCL",
    "NKE", "VZ", "WFC", "BAC", "AMD",

    # Financials & Healthcare
    "CMCSA", "DIS", "TXN", "PM", "INTC",
    "NEE", "UNP", "RTX", "COP", "UPS",
    "QCOM", "HON", "T", "INTU", "LOW",
    "AMGN", "BMY", "SPGI", "SBUX", "GE",
    "CAT", "BLK", "MDLZ", "AXP", "DE",
    "IBM", "ISRG", "BA", "ADI", "LMT",

    # Diversified Industrials & Consumer
    "GS", "GILD", "MMM", "PLD", "ADP",
    "TJX", "VRTX", "BKNG", "SCHW", "CVS",
    "MO", "SYK", "CI", "AMT", "ZTS",
    "REGN", "EL", "PYPL", "CB", "NOW",
    "BDX", "TMUS", "SO", "DUK", "PGR",
    "MS", "CL", "BSX", "MMC", "SLB",
    "EOG", "C", "ITW", "FISV", "HUM"
]

# ==================== S&P 500 FULL (~503 tickers) ====================
# Complete S&P 500 constituents sorted by MARKET CAPITALIZATION (descending).
# Last Updated: 2026-02-10
# Note: BRK.B will be converted to BRK-B by normalize_ticker() in fetcher.py
# Note: Update this list quarterly as index constituents change.

SP500_FULL: Final[List[str]] = [
    # --- Mega Cap ($500B+) ---
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "BRK.B", "TSLA", "LLY", "AVGO",
    "V", "JPM", "UNH", "MA", "XOM",

    # --- Large Cap ($200B-$500B) ---
    "COST", "WMT", "HD", "PG", "NFLX",
    "JNJ", "ABBV", "ORCL", "CRM", "BAC",
    "CVX", "MRK", "KO", "PEP", "AMD",
    "TMO", "ADBE", "LIN", "CSCO", "ACN",
    "WFC", "MCD", "ABT", "PM", "GE",
    "ISRG", "QCOM", "TXN", "INTU", "DHR",
    "AMGN", "MS", "AXP", "NOW", "IBM",

    # --- Large Cap ($100B-$200B) ---
    "BX", "CAT", "VZ", "T", "BKNG",
    "PLD", "SPGI", "HON", "GS", "NEE",
    "BLK", "LOW", "CMCSA", "RTX", "UNP",
    "UBER", "SYK", "DE", "MDLZ", "C",
    "SCHW", "AMAT", "PGR", "TJX", "ADP",
    "VRTX", "ADI", "BSX", "CB", "COP",
    "LRCX", "MMC", "BMY", "CI",
    "REGN", "GILD", "KLAC", "PANW", "SO",
    "SBUX", "ZTS", "DUK", "CME", "SNPS",
    "TMUS", "CL", "MCK", "SLB", "CDNS",

    # --- Upper Mid Cap ($60B-$100B) ---
    "ARM", "KKR", "AMT", "MO", "EOG",
    "ITW", "PYPL", "BDX", "CEG", "APH",
    "CVS", "ETN", "FISV", "PH", "NOC",
    "CMG", "USB", "TT", "SHW", "ORLY",
    "MSI", "AJG", "WMB", "CTAS", "TDG",
    "AON", "ROP", "HCA", "CARR", "APD",
    "NSC", "FCX", "WELL", "PSA", "MPC",
    "GD", "APO", "CRWD", "DELL", "ABNB",
    "HLT", "SPG", "TGT", "FDX", "CCI",
    "MCO", "ECL", "O", "EMR", "COF",

    # --- Mid Cap ($40B-$60B) ---
    "AFL", "NXPI", "PSX", "JCI", "KMB",
    "SRE", "AZO", "PCAR", "A", "MRVL",
    "MAR", "CHTR", "PLTR", "MMM", "NEM",
    "OXY", "AIG", "D", "AEP", "MNST",
    "LULU", "DXCM", "WDAY", "DIS", "NKE",
    "BA", "LMT", "UPS", "F", "GM",
    "WM", "ICE", "PNC", "IDXX", "KDP",
    "YUM", "CTSH", "CMI", "CSX", "BK",
    "OTIS", "EW", "KHC", "FAST", "DOW",
    "RSG", "VRSK", "FICO", "GEHC", "ACGL",

    # --- Mid Cap ($25B-$40B) ---
    "ODFL", "CDW", "EA", "DD", "KR",
    "HAL", "OKE", "BKR", "GPN", "FANG",
    "CPRT", "CNC", "WEC", "XEL", "PPG",
    "DHI", "CTVA", "STZ", "TFC", "GWW",
    "VLO", "KMI", "EXC", "FTNT", "PWR",
    "RCL", "MPWR", "HSY", "ROK",
    "AWK", "GLW", "TSCO", "WAB", "FTV",
    "BR", "AVB", "TRGP", "EFX", "URI",
    "VICI", "DLR", "IR", "IRM", "DECK",
    "VLTO", "VMC", "MLM", "CBRE", "DAL",
    "DOV", "ON", "PCG", "LHX", "WTW",
    "HUBB", "ZBH", "LH", "PTC", "TTWO",
    "GPC", "ROST", "DG", "MOH", "SYF",

    # --- Mid Cap ($15B-$25B) ---
    "NTAP", "HBAN", "BIIB", "DVN",
    "LVS", "MTD", "INTC", "KEYS",
    "EL", "LEN", "NVR", "PHM", "HPQ",
    "HPE", "GIS", "SYY", "MSCI",
    "DPZ", "PEG", "ETR", "AMP", "LYB",
    "GDDY", "AXON", "DDOG", "VST", "GEV",
    "HUM", "FIS", "CAH", "BALL", "SNA",
    "TSN", "CF", "DLTR", "EXPE", "LYV",
    "CINF", "DTE", "PPL", "FE", "ES",
    "CMS", "CNP", "ED", "ALGN", "TER",
    "SWKS", "WAT", "IFF", "JBHT", "POOL",
    "TYL", "DGX", "HOLX", "COO", "RMD",
    "GRMN", "RJF", "NDAQ", "CBOE", "HIG",
    "TRV", "MET", "PRU", "BRO", "NTRS",
    "STT", "CCL", "MAA", "FITB", "MTB",
    "STLD", "NUE", "IP", "CAG", "CPB",
    "MKC", "SJM", "HRL", "IQV", "PAYX",

    # --- Lower Mid Cap ($10B-$15B) ---
    "BAX", "AES", "LNT", "EVRG", "ATO",
    "FDS", "LDOS", "PODD", "INCY", "CHD",
    "IT", "GEN", "WDC", "FSLR",
    "NDSN", "CHRW", "TRMB", "STE", "WRB",
    "CLX", "EPAM", "PAYC", "ZBRA", "AKAM",
    "FFIV", "VTRS", "PKG", "KBH",
    "TPR", "MTCH", "MGM", "WYNN", "CZR",
    "LW", "BEN", "IVZ", "HSIC", "FMC",
    "CRL", "TECH", "BIO", "RL", "BWA",
    "APTV", "MHK", "AOS", "HII", "PNR",
    "EMN", "CE", "SEE", "TXT",
    "AIZ", "NWS", "NWSA", "J", "LKQ",

    # --- Small-Mid Cap ($5B-$10B) ---
    "GNRC", "DVA", "ETSY", "FRT", "REG",
    "KIM", "EQR", "ESS", "UDR", "CPT",
    "BXP", "ARE", "HST", "WBA", "MRO",
    "APA", "RVTY", "DAY", "TFX", "HAS",
    "NI", "PNW", "AMCR", "UHS", "CTRA",
    "FOXA", "FOX", "SWK", "IEX", "EXPD",
    "JKHY", "MKTX", "TAP", "KMX", "ALLE",
    "NRG", "VTR", "SBAC", "AAL", "UAL",
    "LUV", "NCLH", "GL", "RF", "CFG",
    "KEY", "CMA", "ZION", "BLDR", "EG",
    "HWM", "SOLV", "KVUE", "MRNA", "VEEV",
    "ZS", "EQT", "ENPH", "WBD", "ILMN",
    "ERIE", "ROL", "WST", "INVH", "CSGP",
    "TROW", "L", "PFG", "OMC",
    "VRSN", "CPAY", "WHR", "XYL", "ALB",
    "MAS", "ITT", "ADM", "BG", "NOV",
    "LNC", "UNM", "TPL", "BBY",
    "MCHP", "QRVO", "WY", "SMCI",
]


# ==================== FTSE 100 (UK Market) ====================
# London Stock Exchange - Top 100 companies
# Last Updated: 2026-02-11
# Note: .L suffix is HARDCODED on each ticker to prevent US-ticker confusion.
#       normalize_ticker() will detect the existing suffix and skip appending.

FTSE_100: Final[List[str]] = [
    # Mega Cap (>£50B market cap)
    "SHEL.L", "AZN.L", "HSBA.L", "ULVR.L", "BP.L",
    "GSK.L", "RIO.L", "LSEG.L", "REL.L", "DGE.L",

    # Large Cap (£20B-£50B)
    "BATS.L", "NG.L", "BA.L", "GLEN.L", "CPG.L",
    "RKT.L", "III.L", "EXPN.L", "NXT.L", "ABF.L",
    "AHT.L", "RR.L", "AAL.L", "IMB.L", "ANTO.L",
    "LLOY.L", "BARC.L", "NWG.L", "STAN.L", "PRU.L",

    # Mid-Large Cap (£10B-£20B)
    "AV.L", "LGEN.L", "TSCO.L", "SSE.L", "SGE.L",
    "SGRO.L", "INF.L", "WPP.L", "BNZL.L", "SN.L",
    "IHG.L", "HLMA.L", "ADM.L", "AUTO.L", "VOD.L",
    "CCH.L", "SDR.L", "JD.L", "BT-A.L", "MNG.L",

    # Mid Cap (£5B-£10B)
    "SBRY.L", "RTO.L", "SVT.L", "UU.L", "PSN.L",
    "TW.L", "BTRW.L", "CRDA.L", "WEIR.L", "SPX.L",
    "ITRK.L", "RMV.L", "ENT.L", "CNA.L", "IAG.L",
    "BME.L", "MNDI.L", "PSON.L", "SMIN.L", "PHNX.L",

    # Lower Mid Cap (£3B-£5B)
    "KGF.L", "WTB.L", "FRAS.L", "HIK.L", "BRBY.L",
    "EZJ.L", "LAND.L", "DCC.L", "EDV.L",
    "ICG.L", "BEZ.L", "STJ.L", "HWDN.L", "DPLM.L",
    "CTEC.L", "UTG.L", "VTY.L", "BKG.L", "FRES.L",
    "HSX.L", "OCDO.L", "HBR.L", "JMAT.L", "TPK.L",
    "MKS.L", "ABDN.L", "RS1.L", "PNN.L", "WISE.L",
]


# ==================== HELPER FUNCTIONS ====================

def get_nifty_100() -> List[str]:
    """Return Nifty 100 ticker list."""
    return NIFTY_100.copy()


def get_sp500_top100() -> List[str]:
    """Return top 100 S&P 500 tickers by market cap."""
    return SP500_TOP100.copy()


def get_sp500_full() -> List[str]:
    """Return full S&P 500 ticker list (~503 tickers, sorted by market cap)."""
    return SP500_FULL.copy()


def get_ftse_100() -> List[str]:
    """Return FTSE 100 ticker list."""
    return FTSE_100.copy()


def get_all_tickers(index: str = "NIFTY100", limit: Optional[int] = None) -> List[str]:
    """
    Get ticker list by index name, optionally limited to top N by market cap.

    Args:
        index: "NIFTY100", "SP500", or "FTSE100"
        limit: Maximum number of tickers to return (default: all available)
               Takes the top N largest companies by market cap

    Returns:
        List of ticker symbols (sorted by market cap, descending)
    """
    index = index.upper()

    if index == "NIFTY100":
        tickers = get_nifty_100()
    elif index == "SP500":
        tickers = get_sp500_full()
    elif index == "FTSE100":
        tickers = get_ftse_100()
    else:
        raise ValueError(f"Unknown index: {index}. Use 'NIFTY100', 'SP500', or 'FTSE100'")

    # Apply limit if specified
    if limit is not None and limit > 0:
        return tickers[:limit]

    return tickers


def get_ticker_count(index: str) -> int:
    """Get the number of tickers in an index."""
    return len(get_all_tickers(index))
