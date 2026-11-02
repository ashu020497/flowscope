"""Daily build: fetch every source, compute metrics, write site/data/*.json.

Run:  python -m pipeline.run
A source that fails keeps its last good data and is marked 'stale' on the Sources page.
"""
from datetime import date

import pandas as pd

from . import config as C
from . import metrics as M
from . import prices as P
from . import sources as S
from . import stocks as STK
from .util import SourceLog, load_json, merge_history, now_iso, save_json

SRC = {
    "yahoo": dict(name="Market prices", publisher="Yahoo Finance (exchange data)", url="https://finance.yahoo.com", freq="Daily"),
    "fred": dict(name="US liquidity, yields, spreads; India rates", publisher="Federal Reserve Bank of St. Louis (FRED)", url="https://fred.stlouisfed.org", freq="Daily / weekly / monthly"),
    "ici_mmf": dict(name="US money-market fund assets", publisher="Investment Company Institute", url="https://www.ici.org/research/stats/mmf", freq="Weekly (Thu)"),
    "ici_flows": dict(name="US fund & ETF flows by category", publisher="Investment Company Institute", url="https://www.ici.org/research/stats/combined_flows", freq="Weekly (Wed)"),
    "cftc": dict(name="Futures positioning (Commitments of Traders)", publisher="US CFTC", url="https://publicreporting.cftc.gov", freq="Weekly (Fri)"),
    "farside_btc": dict(name="US spot Bitcoin ETF flows", publisher="Farside Investors (from issuer data)", url="https://farside.co.uk/btc/", freq="Daily"),
    "farside_eth": dict(name="US spot Ether ETF flows", publisher="Farside Investors (from issuer data)", url="https://farside.co.uk/eth/", freq="Daily"),
    "nse": dict(name="India FII / DII cash-market activity", publisher="National Stock Exchange of India", url="https://www.nseindia.com/reports/fii-dii", freq="Daily"),
    "nsdl_daily": dict(name="India FPI daily investment", publisher="NSDL", url="https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx", freq="Daily"),
    "nsdl_monthly": dict(name="India FPI monthly investment", publisher="NSDL", url="https://www.fpi.nsdl.co.in", freq="Monthly"),
    "amfi": dict(name="India mutual-fund flows by category", publisher="AMFI", url="https://www.amfiindia.com", freq="Monthly"),
    "mof": dict(name="Japan cross-border portfolio flows", publisher="Ministry of Finance, Japan", url="https://www.mof.go.jp/english/policy/international_policy/reference/itn_transactions_in_securities/", freq="Weekly"),
    "nifty_pe": dict(name="Nifty 50 P/E and dividend yield", publisher="NSE Indices (niftyindices.com)", url="https://www.niftyindices.com", freq="Daily"),
    "nifty_universe": dict(name="Stock universe (Nifty Total Market) with industries", publisher="NSE Indices (niftyindices.com)", url="https://www.niftyindices.com", freq="Monthly rebalance"),
    "nifty_indices": dict(name="Index constituents (Nifty 50, sectors, caps)", publisher="NSE Indices (niftyindices.com)", url="https://www.niftyindices.com", freq="Semi-annual rebalance"),
    "stock_prices": dict(name="Indian stock prices (750 stocks)", publisher="Yahoo Finance (NSE data)", url="https://finance.yahoo.com", freq="Daily"),
    "nse_ownership": dict(name="Shareholding pattern (promoter / public)", publisher="National Stock Exchange of India", url="https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern", freq="Quarterly"),
    "sp500_eps": dict(name="S&P 500 earnings and dividend yield", publisher="multpl.com (from S&P Dow Jones Indices data)", url="https://www.multpl.com", freq="Monthly"),
}


def pts(s, scale=1.0, last_n=None):
    s = s.dropna()
    if last_n:
        s = s.iloc[-last_n:]
    return [[d.strftime("%Y-%m-%d"), round(float(v) * scale, 4)] for d, v in s.items()]


def main():
    log = SourceLog()
    print("Flowscope refresh started", now_iso(), flush=True)
    old_cash = load_json("cash.json", {}) or {}
    old_flows = load_json("flows.json", {}) or {}
    old_assets = load_json("assets.json", {}) or {}

    # ---------- FRED ----------
    fred = {}
    fred_ok = []

    def _fred():
        asof, misses = [], 0
        for sid in C.FRED_SERIES:
            if misses >= 3 and not fred:
                raise RuntimeError("FRED not responding (first 3 series failed)")
            try:
                s, d = S.fred(sid)
                fred[sid] = s
                asof.append(d)
                fred_ok.append(sid)
                misses = 0
            except Exception as e:
                misses += 1
                print(f"  FRED {sid}: {e}", flush=True)
        if not fred:
            raise RuntimeError("no FRED series downloaded")
        return True, max(asof)

    log.run("fred", SRC["fred"], _fred, fallback=old_cash.get("series"), budget=240)
    cash_series = {}
    for sid, meta in C.FRED_SERIES.items():
        if sid in fred:
            cash_series[sid] = dict(meta, id=sid, source="fred", points=pts(fred[sid][fred[sid].index >= "2016-01-01"], meta["scale"]))
        elif sid in (old_cash.get("series") or {}):
            cash_series[sid] = old_cash["series"][sid]

    def last_rate(sid, default):
        if sid in fred and len(fred[sid]):
            return float(fred[sid].iloc[-1]) / 100
        p = (cash_series.get(sid) or {}).get("points")
        return p[-1][1] / 100 if p else default

    rf = {"USD": last_rate("DTB3", 0.04), "INR": last_rate("INTGSTINM193N", 0.065)}

    # ---------- Prices & metrics ----------
    tickers = [a["ticker"] for a in C.ASSETS] + [v[0] for v in C.FX_TO_USD.values()]
    px = {}

    def _prices():
        px.update(P.download(tickers))
        if len(px) < len(C.ASSETS) * 0.5:
            raise RuntimeError(f"only {len(px)} of {len(tickers)} tickers downloaded")
        return True, max(s.index[-1] for s in px.values()).strftime("%Y-%m-%d")

    ok = log.run("yahoo", SRC["yahoo"], _prices, fallback=old_assets.get("assets"), budget=420)
    by_id = {a["id"]: a for a in C.ASSETS}
    bench_t = by_id[C.BENCHMARK]["ticker"]
    bench = px.get(bench_t)
    assets_out = []
    old_by_id = {a["id"]: a for a in (old_assets.get("assets") or [])}
    for a in C.ASSETS:
        s = px.get(a["ticker"])
        if s is None or len(s) < 30:
            if a["id"] in old_by_id:
                o = dict(old_by_id[a["id"]], stale=True)
                assets_out.append(o)
            continue
        usd = P.to_usd(s, a["ccy"], px, C.FX_TO_USD.get(a["ccy"])) if a["cls"] not in ("FX", "Volatility") else s
        rec = {k: a.get(k) for k in ("id", "name", "ticker", "region", "cls", "ccy", "theme", "decomp")}
        rec.update(last=float(s.iloc[-1]), prev=float(s.iloc[-2]), last_date=s.index[-1].strftime("%Y-%m-%d"),
                   start_date=s.index[0].strftime("%Y-%m-%d"),
                   ret=M.returns(s), spark=M.spark(s))
        if not a.get("no_risk"):
            rec["risk"] = M.risk(s, rf.get(a["ccy"], 0.0), bench if a["id"] != C.BENCHMARK else None)
            rec["rf_note"] = "local T-bill" if a["ccy"] in rf else "0% (no free local T-bill series)"
        if usd is not None and a["ccy"] != "USD":
            rec["ret_usd"] = M.returns(usd)
            if not a.get("no_risk"):
                rec["risk_usd"] = M.risk(usd, rf["USD"], bench)
        assets_out.append(rec)
        save_json(f"series/{a['id']}.json", {"id": a["id"], "local": M.compact(s),
                                              "usd": M.compact(usd) if usd is not None and a["ccy"] != "USD" else None})
    save_json("assets.json", {"generated": now_iso(), "benchmark": C.BENCHMARK, "rf": rf, "assets": assets_out})

    # ---------- Flows ----------
    flows = {}

    def keep(key, sid, fn, merge=True, budget=120):
        old = old_flows.get(key)
        res = log.run(sid, SRC[sid], fn, fallback=old, budget=budget)
        if res is None:
            return
        if merge and isinstance(res, list) and isinstance(old, list) and res is not old:
            res = merge_history(old, res)
        flows[key] = res

    keep("mmf", "ici_mmf", lambda: (lambda r: ([r[0]], r[1]))(S.ici_mmf()))
    keep("ici", "ici_flows", lambda: (lambda r: ([r[0]], r[1]))(S.ici_flows()))
    keep("cftc", "cftc", lambda: S.cftc(C.CFTC_MARKETS), merge=False)
    keep("btc_etf", "farside_btc", lambda: S.farside("btc"))
    keep("eth_etf", "farside_eth", lambda: S.farside("eth"))
    keep("nse", "nse", lambda: (lambda r: ([r[0]], r[1]))(S.nse_fii_dii()))
    keep("nsdl_daily", "nsdl_daily", S.nsdl_daily)
    keep("nsdl_monthly", "nsdl_monthly", S.nsdl_monthly)
    keep("amfi", "amfi", lambda: S.amfi(C.AMFI_CATEGORIES, existing=old_flows.get("amfi")), budget=240)
    keep("mof", "mof", S.japan_mof)
    for k in ("mmf", "ici", "nse", "btc_etf", "eth_etf", "nsdl_daily"):
        if isinstance(flows.get(k), list):
            flows[k] = flows[k][-800:]

    board = build_board(flows)
    save_json("flows.json", dict(flows, board=board, generated=now_iso()))

    # ---------- Cash & liquidity page ----------
    cash = {"generated": now_iso(), "series": cash_series}
    if flows.get("mmf"):
        cash["ici_mmf"] = [[r["date"], r["total_bn"]] for r in flows["mmf"]]
    save_json("cash.json", cash)

    # ---------- Return decomposition ----------
    old_dec = load_json("decomp.json", {}) or {}
    dec = {}
    nifty_px = px.get(by_id["nifty50"]["ticker"])
    spx_px = px.get(by_id["sp500"]["ticker"])

    def _nifty():
        df, d = S.nifty_pe()
        return decompose_from_pe(nifty_px, df["pe"], df["dy"]), d

    def _spx():
        df, d = S.multpl_sp500()
        return decompose_from_eps(spx_px, df["eps"], df["dy"]), d

    r = log.run("nifty_pe", SRC["nifty_pe"], _nifty, fallback=old_dec.get("nifty50"))
    if r:
        dec["nifty50"] = r
    r = log.run("sp500_eps", SRC["sp500_eps"], _spx, fallback=old_dec.get("sp500"))
    if r:
        dec["sp500"] = r
    save_json("decomp.json", dec)

    # ---------- Driver map: 750 stocks + factor graph ----------
    try:
        print(f"driver map: {log.remaining() / 60:.0f} min left in the time budget", flush=True)
        n_st = STK.build(P.download, px, fred, by_id, log, SRC)
        print("stocks:", n_st)
    except Exception as e:
        import traceback
        print("driver map build failed:", e)
        traceback.print_exc()

    log.save()
    save_json("meta.json", {"generated": now_iso(), "assets": len(assets_out),
                            "sources_ok": sum(1 for s in log.items.values() if s["status"] == "ok"),
                            "sources_total": len(log.items)})
    print("done:", {k: v["status"] for k, v in log.items.items()})


def _cat(name, cls, unit, freq, source, hist):
    hist = [h for h in hist if h[1] is not None]
    return {"name": name, "cls": cls, "unit": unit, "freq": freq, "source": source, "history": hist}


def build_board(f):
    """Flow categories per scope; the site sums history over the chosen window."""
    us = []
    if f.get("mmf"):
        us.append(_cat("Money-market funds", "Cash", "US$ bn", "Weekly", "ICI", [[r["date"], r.get("change_bn")] for r in f["mmf"]]))
    for key, name, cls in S.ICI_CATS:
        h = [[r["date"], r.get(key)] for r in f.get("ici") or [] if r.get(key) is not None]
        if h:
            us.append(_cat(name, cls, "US$ bn", "Weekly", "ICI", h))
    for k, nm in (("btc_etf", "Bitcoin ETFs"), ("eth_etf", "Ether ETFs")):
        if f.get(k):
            us.append(_cat(nm, "Crypto", "US$ bn", "Daily", "Farside", [[r["date"], r["value_mn"] / 1000] for r in f[k]]))
    india = []
    names = {n: c for _, n, c in C.AMFI_CATEGORIES}
    for n, cls in names.items():
        h = [[r["date"], r.get(n)] for r in f.get("amfi") or [] if r.get(n) is not None]
        if h:
            india.append(_cat(n, cls, "₹ cr", "Monthly", "AMFI", h))
    if f.get("nsdl_monthly"):
        india.append(_cat("Foreign investors: equity", "Equities", "₹ cr", "Monthly", "NSDL", [[r["date"], r.get("equity")] for r in f["nsdl_monthly"]]))
        india.append(_cat("Foreign investors: debt", "Bonds", "₹ cr", "Monthly", "NSDL", [[r["date"], r.get("debt")] for r in f["nsdl_monthly"]]))
    japan = []
    lab = {"foreign_buy_jp_equity": ("Foreigners buying Japanese stocks", "Equities"),
           "foreign_buy_jp_bonds": ("Foreigners buying Japanese bonds", "Bonds"),
           "jp_buy_foreign_equity": ("Japanese buying foreign stocks", "Equities"),
           "jp_buy_foreign_bonds": ("Japanese buying foreign bonds", "Bonds")}
    for k, (n, cls) in lab.items():
        h = [[r["date"], r[k] / 10] for r in f.get("mof") or [] if r.get(k) is not None]
        if h:
            japan.append(_cat(n, cls, "¥ bn", "Weekly", "Japan MOF", h))
    return {"Global": us, "United States": us, "India": india, "Japan": japan}


def _annual(s):
    s = s.dropna()
    return s.groupby(s.index.year).last()


def _row(year, g, pe, dy, partial):
    price = (1 + g) * (1 + pe) - 1
    return {"year": f"{year} YTD" if partial else str(year), "eps_growth": g, "pe_change": pe,
            "dividend": dy, "price_return": price, "total": price + dy}


def decompose_from_pe(price, pe, dy):
    if price is None:
        raise RuntimeError("no Nifty price series")
    pe = pe[~pe.index.duplicated()].sort_index()
    eps = (price.reindex(pe.index, method="ffill") / pe).dropna()
    pe_a, eps_a, dy_a = _annual(pe), _annual(eps), (dy.dropna().groupby(dy.dropna().index.year).mean() / 100)
    rows = []
    yrs = list(pe_a.index)
    for i in range(1, len(yrs)):
        y = yrs[i]
        rows.append(_row(y, eps_a[y] / eps_a[yrs[i - 1]] - 1, pe_a[y] / pe_a[yrs[i - 1]] - 1, float(dy_a.get(y, 0) or 0), y == date.today().year))
    p5 = pe[pe.index >= pe.index[-1] - pd.Timedelta(days=365 * 5)]
    return {"rows": rows[-6:], "pe": float(pe.iloc[-1]), "pe_5y_min": float(p5.min()), "pe_5y_max": float(p5.max()),
            "pe_5y_median": float(p5.median()), "as_of": pe.index[-1].strftime("%Y-%m-%d"), "method": "EPS = index level ÷ trailing P/E (NSE)"}


def decompose_from_eps(price, eps, dy):
    if price is None:
        raise RuntimeError("no S&P price series")
    eps = eps[eps.index >= "2014-01-01"]
    px_m = price.resample("ME").last()
    eps_m = eps.resample("ME").last().reindex(px_m.index, method="ffill")
    pe = (px_m / eps_m).dropna()
    eps_a, pe_a = _annual(eps_m.dropna()), _annual(pe)
    dy_a = dy.dropna().groupby(dy.dropna().index.year).mean() / 100
    rows = []
    yrs = list(pe_a.index)
    for i in range(1, len(yrs)):
        y = yrs[i]
        rows.append(_row(y, eps_a[y] / eps_a[yrs[i - 1]] - 1, pe_a[y] / pe_a[yrs[i - 1]] - 1, float(dy_a.get(y, 0) or 0), y == date.today().year))
    p5 = pe[pe.index >= pe.index[-1] - pd.Timedelta(days=365 * 5)]
    return {"rows": rows[-6:], "pe": float(pe.iloc[-1]), "pe_5y_min": float(p5.min()), "pe_5y_max": float(p5.max()),
            "pe_5y_median": float(p5.median()), "as_of": pe.index[-1].strftime("%Y-%m-%d"),
            "method": "Trailing 12-month reported EPS (S&P via multpl); P/E = index ÷ EPS"}


if __name__ == "__main__":
    main()
