"""Universe of tracked assets and data-source settings.

Edit ASSETS to add or remove anything. Each entry:
  id      short unique id used in URLs
  name    display name
  ticker  Yahoo Finance symbol (daily closes, adjusted for dividends where Yahoo provides it)
  region  India | United States | Europe | UK | Japan | China | EM | Global
  cls     asset class shown in filters
  ccy     quote currency (used for the USD toggle)
  bench   benchmark id for beta / correlation (defaults to "acwi")
"""

BENCHMARK = "acwi"

ASSETS = [
    # ---------- India: equities ----------
    dict(id="nifty50", name="Nifty 50", ticker="^NSEI", region="India", cls="Equities", ccy="INR", decomp="nifty50"),
    dict(id="niftybank", name="Nifty Bank", ticker="^NSEBANK", region="India", cls="Equities", ccy="INR"),
    dict(id="niftyit", name="Nifty IT", ticker="^CNXIT", region="India", cls="Equities", ccy="INR"),
    dict(id="niftypharma", name="Nifty Pharma", ticker="^CNXPHARMA", region="India", cls="Equities", ccy="INR"),
    dict(id="niftyfmcg", name="Nifty FMCG", ticker="^CNXFMCG", region="India", cls="Equities", ccy="INR"),
    dict(id="niftyauto", name="Nifty Auto", ticker="^CNXAUTO", region="India", cls="Equities", ccy="INR"),
    dict(id="niftymetal", name="Nifty Metal", ticker="^CNXMETAL", region="India", cls="Equities", ccy="INR"),
    dict(id="niftyenergy", name="Nifty Energy", ticker="^CNXENERGY", region="India", cls="Equities", ccy="INR"),
    dict(id="niftyrealty", name="Nifty Realty", ticker="^CNXREALTY", region="India", cls="Equities", ccy="INR"),
    dict(id="niftymid", name="Nifty Midcap 150 ETF", ticker="MID150BEES.NS", region="India", cls="Equities", ccy="INR"),
    # ---------- India: other ----------
    dict(id="goldinr", name="Gold ETF (India)", ticker="GOLDBEES.NS", region="India", cls="Commodities", ccy="INR"),
    dict(id="silverinr", name="Silver ETF (India)", ticker="SILVERBEES.NS", region="India", cls="Commodities", ccy="INR"),
    dict(id="indgilt", name="India long G-sec ETF", ticker="LTGILTBEES.NS", region="India", cls="Bonds & cash", ccy="INR"),
    dict(id="embassy", name="Embassy Office REIT", ticker="EMBASSY.NS", region="India", cls="Real estate", ccy="INR"),
    dict(id="indigrid", name="IndiGrid InvIT", ticker="INDIGRID.NS", region="India", cls="Alternatives", ccy="INR"),
    dict(id="indiavix", name="India VIX", ticker="^INDIAVIX", region="India", cls="Volatility", ccy="INR", no_risk=True),
    dict(id="usdinr", name="USD / INR", ticker="INR=X", region="India", cls="FX", ccy="INR"),

    # ---------- United States ----------
    dict(id="sp500", name="S&P 500", ticker="^GSPC", region="United States", cls="Equities", ccy="USD", decomp="sp500"),
    dict(id="nasdaq100", name="Nasdaq 100", ticker="^NDX", region="United States", cls="Equities", ccy="USD"),
    dict(id="russell2000", name="Russell 2000", ticker="^RUT", region="United States", cls="Equities", ccy="USD"),
    dict(id="semis", name="Semiconductors (SOXX)", ticker="SOXX", region="United States", cls="Equities", ccy="USD", theme="AI"),
    dict(id="aibots", name="AI & robotics (BOTZ)", ticker="BOTZ", region="Global", cls="Equities", ccy="USD", theme="AI"),
    dict(id="usvalue", name="US value (VTV)", ticker="VTV", region="United States", cls="Equities", ccy="USD"),
    dict(id="usgrowth", name="US growth (VUG)", ticker="VUG", region="United States", cls="Equities", ccy="USD"),
    dict(id="usquality", name="US quality (QUAL)", ticker="QUAL", region="United States", cls="Equities", ccy="USD"),
    dict(id="tbills", name="US T-bills 1–3M (BIL)", ticker="BIL", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="ust2", name="US Treasuries 1–3Y (SHY)", ticker="SHY", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="ust20", name="US Treasuries 20Y+ (TLT)", ticker="TLT", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="tips", name="US TIPS (TIP)", ticker="TIP", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="usig", name="US IG credit (LQD)", ticker="LQD", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="ushy", name="US high yield (HYG)", ticker="HYG", region="United States", cls="Bonds & cash", ccy="USD"),
    dict(id="usreit", name="US REITs (VNQ)", ticker="VNQ", region="United States", cls="Real estate", ccy="USD"),
    dict(id="vix", name="VIX", ticker="^VIX", region="United States", cls="Volatility", ccy="USD", no_risk=True),

    # ---------- Europe / UK / Japan / China / EM ----------
    dict(id="stoxx50", name="Euro Stoxx 50", ticker="^STOXX50E", region="Europe", cls="Equities", ccy="EUR"),
    dict(id="dax", name="DAX", ticker="^GDAXI", region="Europe", cls="Equities", ccy="EUR"),
    dict(id="ftse100", name="FTSE 100", ticker="^FTSE", region="UK", cls="Equities", ccy="GBP"),
    dict(id="nikkei", name="Nikkei 225", ticker="^N225", region="Japan", cls="Equities", ccy="JPY"),
    dict(id="csi300", name="CSI 300", ticker="000300.SS", region="China", cls="Equities", ccy="CNY"),
    dict(id="hangseng", name="Hang Seng", ticker="^HSI", region="China", cls="Equities", ccy="HKD"),
    dict(id="kospi", name="KOSPI", ticker="^KS11", region="EM", cls="Equities", ccy="KRW"),
    dict(id="taiex", name="Taiwan TAIEX", ticker="^TWII", region="EM", cls="Equities", ccy="TWD"),
    dict(id="brazil", name="Brazil (EWZ)", ticker="EWZ", region="EM", cls="Equities", ccy="USD"),
    dict(id="em", name="Emerging markets (EEM)", ticker="EEM", region="EM", cls="Equities", ccy="USD"),
    dict(id="emdebt", name="EM USD bonds (EMB)", ticker="EMB", region="EM", cls="Bonds & cash", ccy="USD"),
    dict(id="vietnam", name="Vietnam (VNM, frontier proxy)", ticker="VNM", region="EM", cls="Alternatives", ccy="USD"),

    # ---------- Global ----------
    dict(id="acwi", name="MSCI All-Country World (ACWI)", ticker="ACWI", region="Global", cls="Equities", ccy="USD"),
    dict(id="globalbonds", name="Global bonds ex-US (BNDX)", ticker="BNDX", region="Global", cls="Bonds & cash", ccy="USD"),

    # ---------- Commodities ----------
    dict(id="gold", name="Gold", ticker="GC=F", region="Global", cls="Commodities", ccy="USD"),
    dict(id="silver", name="Silver", ticker="SI=F", region="Global", cls="Commodities", ccy="USD"),
    dict(id="brent", name="Brent crude", ticker="BZ=F", region="Global", cls="Commodities", ccy="USD"),
    dict(id="natgas", name="Natural gas", ticker="NG=F", region="Global", cls="Commodities", ccy="USD"),
    dict(id="copper", name="Copper", ticker="HG=F", region="Global", cls="Commodities", ccy="USD"),
    dict(id="agri", name="Agriculture (DBA)", ticker="DBA", region="Global", cls="Commodities", ccy="USD"),
    dict(id="commod", name="Broad commodities (DBC)", ticker="DBC", region="Global", cls="Commodities", ccy="USD"),
    dict(id="goldminers", name="Gold miners (GDX)", ticker="GDX", region="Global", cls="Commodities", ccy="USD"),

    # ---------- FX ----------
    dict(id="dxy", name="US dollar index", ticker="DX-Y.NYB", region="Global", cls="FX", ccy="USD"),
    dict(id="eurusd", name="EUR / USD", ticker="EURUSD=X", region="Europe", cls="FX", ccy="USD"),
    dict(id="usdjpy", name="USD / JPY", ticker="JPY=X", region="Japan", cls="FX", ccy="JPY"),
    dict(id="usdcny", name="USD / CNY", ticker="CNY=X", region="China", cls="FX", ccy="CNY"),

    # ---------- Crypto ----------
    dict(id="btc", name="Bitcoin", ticker="BTC-USD", region="Global", cls="Crypto", ccy="USD"),
    dict(id="eth", name="Ether", ticker="ETH-USD", region="Global", cls="Crypto", ccy="USD"),
    dict(id="btcminers", name="Bitcoin miners (WGMI)", ticker="WGMI", region="Global", cls="Crypto", ccy="USD"),

    # ---------- Non-mainstream / alternatives ----------
    dict(id="bdc", name="Private credit / BDCs (BIZD)", ticker="BIZD", region="United States", cls="Alternatives", ccy="USD"),
    dict(id="infra", name="Global infrastructure (IGF)", ticker="IGF", region="Global", cls="Alternatives", ccy="USD"),
    dict(id="uranium", name="Uranium & nuclear (URA)", ticker="URA", region="Global", cls="Alternatives", ccy="USD"),
    dict(id="carbon", name="Carbon credits (KRBN)", ticker="KRBN", region="Global", cls="Alternatives", ccy="USD"),
    dict(id="timber", name="Timber & forestry (WOOD)", ticker="WOOD", region="Global", cls="Alternatives", ccy="USD"),
    dict(id="pe", name="Listed private equity (PSP)", ticker="PSP", region="Global", cls="Alternatives", ccy="USD"),
    dict(id="mlp", name="Energy infrastructure MLPs (AMLP)", ticker="AMLP", region="United States", cls="Alternatives", ccy="USD"),
    dict(id="globalreit", name="Global REITs ex-US (VNQI)", ticker="VNQI", region="Global", cls="Real estate", ccy="USD"),
]

# How to convert a local-currency price to USD: (fx ticker, "div" or "mul")
FX_TO_USD = {
    "INR": ("INR=X", "div"),
    "EUR": ("EURUSD=X", "mul"),
    "GBP": ("GBPUSD=X", "mul"),
    "JPY": ("JPY=X", "div"),
    "CNY": ("CNY=X", "div"),
    "HKD": ("HKD=X", "div"),
    "KRW": ("KRW=X", "div"),
    "TWD": ("TWD=X", "div"),
}

# Risk-free rate per currency for Sharpe/Sortino (FRED series, % per year)
RISK_FREE = {"USD": "DTB3", "INR": "INTGSTINM193N"}

# FRED series used on the Cash & liquidity page
FRED_SERIES = {
    "RRPONTSYD": dict(name="Fed overnight reverse repo", unit="US$ bn", freq="Daily", scale=1),
    "WTREGEN": dict(name="US Treasury General Account", unit="US$ bn", freq="Weekly", scale=0.001),
    "WALCL": dict(name="Fed total assets", unit="US$ bn", freq="Weekly", scale=0.001),
    "DPSACBW027SBOG": dict(name="US commercial bank deposits", unit="US$ bn", freq="Weekly", scale=1),
    "WRMFNS": dict(name="US retail money-market funds", unit="US$ bn", freq="Weekly", scale=1),
    "WMTSECL1": dict(name="Treasuries held at Fed for foreign official accounts", unit="US$ bn", freq="Weekly", scale=0.001),
    "DTB3": dict(name="US 3-month T-bill yield", unit="%", freq="Daily", scale=1),
    "DGS2": dict(name="US 2-year Treasury yield", unit="%", freq="Daily", scale=1),
    "DGS10": dict(name="US 10-year Treasury yield", unit="%", freq="Daily", scale=1),
    "BAMLH0A0HYM2": dict(name="US high-yield spread", unit="%", freq="Daily", scale=1),
    "BAMLC0A0CM": dict(name="US investment-grade spread", unit="%", freq="Daily", scale=1),
    "DTWEXBGS": dict(name="Broad US dollar index", unit="index", freq="Daily", scale=1),
    "DFF": dict(name="US Fed funds rate", unit="%", freq="Daily", scale=1),
    "DFII10": dict(name="US 10-year real yield (TIPS)", unit="%", freq="Daily", scale=1),
    "CPIAUCSL": dict(name="US consumer price index", unit="index", freq="Monthly", scale=1),
    "INDCPIALLMINMEI": dict(name="India consumer price index", unit="index", freq="Monthly", scale=1),
    "INTGSTINM193N": dict(name="India T-bill rate", unit="%", freq="Monthly", scale=1),
    "INDIRLTLT01STM": dict(name="India 10-year G-sec yield", unit="%", freq="Monthly", scale=1),
}

# CFTC Commitments of Traders (legacy, futures only): speculative positioning
CFTC_MARKETS = {
    "088691": "Gold",
    "084691": "Silver",
    "067651": "Crude oil (WTI)",
    "085692": "Copper",
    "13874A": "S&P 500 e-mini",
    "209742": "Nasdaq 100 e-mini",
    "043602": "US 10-year note",
    "098662": "US dollar index",
    "133741": "Bitcoin (CME)",
    "002602": "Corn",
}

# AMFI categories we surface (matched case-insensitively as substrings of the row label)
AMFI_CATEGORIES = [
    ("Overnight Fund", "Overnight funds", "Cash & money market"),
    ("Liquid Fund", "Liquid funds", "Cash & money market"),
    ("Money Market Fund", "Money-market funds", "Cash & money market"),
    ("Arbitrage Fund", "Arbitrage funds", "Cash & money market"),
    ("Gilt Fund", "Gilt funds", "Bonds"),
    ("Corporate Bond Fund", "Corporate bond funds", "Bonds"),
    ("Large Cap Fund", "Large-cap equity", "Equities"),
    ("Mid Cap Fund", "Mid-cap equity", "Equities"),
    ("Small Cap Fund", "Small-cap equity", "Equities"),
    ("Flexi Cap Fund", "Flexi-cap equity", "Equities"),
    ("Sectoral/Thematic", "Sectoral & thematic", "Equities"),
    ("Index Funds", "Index funds", "Equities"),
    ("GOLD ETF", "Gold ETFs", "Gold"),
    ("Other ETFs", "Other ETFs", "Equities"),
    ("Fund of funds investing overseas", "Overseas fund-of-funds", "Global equities"),
]
