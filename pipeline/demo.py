"""Offline demo: replaces every network fetcher with simulated data, then runs the real
pipeline. Use it to preview the site without internet:  python -m pipeline.demo
Never commit demo output as real data (the site shows a DEMO banner when meta.demo is true)."""
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config as C
from . import prices as P
from . import run as R
from . import sources as S
from .util import load_json, save_json

rng = np.random.default_rng(7)
END = pd.Timestamp(date.today()) - pd.Timedelta(days=1)


def _walk(n, mu, vol, start=100.0):
    r = rng.normal(mu / 252, vol / np.sqrt(252), n)
    return start * np.exp(np.cumsum(r))


_FAC = {}


def _factor(t, idx):
    if t not in _FAC:
        _FAC[t] = pd.Series(rng.normal(0, 0.012 if t != "BZ=F" else 0.022, len(idx)), index=idx)
    return _FAC[t].reindex(idx).fillna(0)


def fake_download(tickers, years=11):
    from . import kb
    idx = pd.bdate_range(END - pd.Timedelta(days=365 * 11), END)
    out = {}
    for t in tickers:
        if t.endswith(".NS") and t not in ("LTGILTBEES.NS",) and t[:-3] not in [a["ticker"] for a in C.ASSETS]:
            sym = t[:-3]
            tm = kb.TEMPLATES.get(kb.STOCKS.get(sym, "default"), kb.TEMPLATES["default"])
            r = 1.0 * _factor("^NSEI", idx) * rng.uniform(0.6, 1.4)
            for node, sign, strength, _ in tm["drivers"]:
                tick = {"brent": "BZ=F", "usdinr": "INR=X", "gold": "GC=F", "copper": "HG=F", "natgas": "NG=F"}.get(node)
                if tick and sign in "+-":
                    r = r + (1 if sign == "+" else -1) * 0.12 * strength * _factor(tick, idx)
            r = r + rng.normal(0, 0.014, len(idx))
            out[t] = pd.Series(100 * np.exp(np.cumsum(r)), index=idx)
            continue
        if t in ("^NSEI", "BZ=F", "INR=X", "GC=F", "HG=F", "NG=F"):
            out[t] = pd.Series(100 * np.exp(np.cumsum(_factor(t, idx) + 0.0002)), index=idx)
            continue
        vol = 0.6 if "BTC" in t or "ETH" in t else 0.3 if t.endswith("=F") else 0.08 if t.endswith("=X") else 0.18
        mu = 0.12 if "GC" in t or "GOLD" in t else -0.02 if t.endswith("=X") else 0.07
        out[t] = pd.Series(_walk(len(idx), mu, vol), index=idx)
    return out


def fake_fred(sid, start="2010-01-01"):
    idx = pd.date_range("2016-01-01", END, freq="W-WED")
    base = {"DTB3": 4.2, "INTGSTINM193N": 6.4, "DGS2": 3.9, "DGS10": 4.3, "BAMLH0A0HYM2": 3.4, "BAMLC0A0CM": 1.0, "INDIRLTLT01STM": 6.6}.get(sid)
    if base:
        s = pd.Series(base + np.cumsum(rng.normal(0, 0.03, len(idx))), index=idx)
    else:
        s = pd.Series(_walk(len(idx), 0.05, 0.05, 1000), index=idx)
    return s, s.index[-1].strftime("%Y-%m-%d")


def weeks(n):
    return [(END - pd.Timedelta(days=7 * i)).strftime("%Y-%m-%d") for i in range(n)][::-1]


def main():
    P.download = fake_download
    S.fred = fake_fred
    wk = weeks(30)
    tot = 7000.0
    mmf = []
    for d in wk:
        ch = float(rng.normal(15, 20)); tot += ch
        mmf.append({"date": d, "total_bn": tot, "change_bn": ch})
    ici = [{"date": d, "Domestic equity": float(rng.normal(-6, 5)), "World equity": float(rng.normal(-1, 2)), "Hybrid": float(rng.normal(-1, 1)),
            "Taxable bond": float(rng.normal(4, 3)), "Municipal bond": float(rng.normal(0.5, 0.5)), "Commodity": float(rng.normal(0.8, 0.6))} for d in wk]
    days = [(END - pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(120)][::-1]
    btc = [{"date": d, "value_mn": float(rng.normal(-60, 200))} for d in days]
    eth = [{"date": d, "value_mn": float(rng.normal(-10, 50))} for d in days]
    nse = [{"date": d, "fii": float(rng.normal(-2500, 1500)), "dii": float(rng.normal(3200, 1500))} for d in days[-40:]]
    months = [(END.to_period("M") - i).strftime("%Y-%m") for i in range(1, 14)][::-1]
    amfi = []
    for m in months:
        row = {"date": m}
        for _, n, cls in C.AMFI_CATEGORIES:
            mu = {"Cash & money market": 20000, "Equities": 3000, "Gold": 2000, "Bonds": -800, "Global equities": 200}[cls]
            row[n] = float(rng.normal(mu, abs(mu) * 0.8))
        amfi.append(row)
    nsdlm = [{"date": m, "equity": float(rng.normal(-12000, 9000)), "debt": float(rng.normal(3000, 4000))} for m in months]
    mof = [{"date": d, "jp_buy_foreign_equity": float(rng.normal(1000, 2000)), "jp_buy_foreign_bonds": float(rng.normal(3000, 5000)),
            "foreign_buy_jp_equity": float(rng.normal(-2000, 4000)), "foreign_buy_jp_bonds": float(rng.normal(2000, 6000))} for d in wk]

    def cftc(markets):
        res = []
        for c, n in markets.items():
            h = np.clip(np.cumsum(rng.normal(0, 0.02, 60)) + rng.uniform(-0.3, 0.4), -0.9, 0.9)
            ds = weeks(60)
            res.append({"code": c, "name": n, "date": ds[-1], "net": float(h[-1] * 300000), "net_pct_oi": float(h[-1]),
                        "chg4w_pct_oi": float(h[-1] - h[-5]), "pctile_1y": float((h[-1] - h[-52:].min()) / (np.ptp(h[-52:]) or 1)),
                        "history": [[d, round(float(v), 4)] for d, v in zip(ds, h)]})
        return res, ds[-1]

    S.ici_mmf = lambda: (mmf[-1], mmf[-1]["date"])
    S.ici_flows = lambda: (ici[-1], ici[-1]["date"])
    S.cftc = cftc
    S.farside = lambda kind="btc": ((btc if kind == "btc" else eth), days[-1])
    S.nse_fii_dii = lambda: (nse[-1], nse[-1]["date"])
    S.nsdl_daily = lambda: ([{"date": r["date"], "equity": r["fii"] * 0.9, "debt": float(rng.normal(300, 400))} for r in nse], nse[-1]["date"])
    S.nsdl_monthly = lambda: (nsdlm, nsdlm[-1]["date"])
    S.amfi = lambda cats, months_back=13, existing=None: (amfi, amfi[-1]["date"])
    S.japan_mof = lambda: (mof, mof[-1]["date"])

    def nifty_pe(index_name="NIFTY 50", years=8):
        idx = pd.bdate_range(END - pd.Timedelta(days=365 * years), END)
        pe = pd.Series(22 + np.cumsum(rng.normal(0, 0.08, len(idx))), index=idx).clip(16, 28)
        return pd.DataFrame({"pe": pe, "dy": 1.3}), idx[-1].strftime("%Y-%m-%d")

    def spx():
        idx = pd.date_range("2013-01-31", END, freq="ME")
        eps = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.006, 0.01, len(idx)))), index=idx)
        return pd.DataFrame({"eps": eps, "dy": 1.5}), idx[-1].strftime("%Y-%m-%d")

    S.nifty_pe = nifty_pe
    from . import kb, stocks as STK
    syms = sorted(kb.STOCKS)
    broad = list(kb.BROAD)
    STK.universe = lambda: ([{"s": x, "n": x.title() + " Ltd", "i": broad[i % len(broad)]} for i, x in enumerate(syms)], date.today().isoformat())
    STK.memberships = lambda: ({"nifty50": syms[:50], "nifty100": syms[:100], "nifty500": syms, "niftybank": [x for x in syms if kb.STOCKS[x] in ("private_bank", "psu_bank")][:12],
                                "niftyit": [x for x in syms if kb.STOCKS[x] == "it_services"][:10]}, date.today().isoformat())
    STK.market_caps = lambda symbols, px, cache: {x: float(rng.lognormal(10, 1.2)) for x in symbols}
    def own(symbols, cache, limit=150):
        for x in symbols:
            pr = float(rng.uniform(30, 75))
            cache[x] = {"checked": date.today().isoformat(), "src": "NSE shareholding pattern", "hist": [{"date": d, "promoter": pr - i * 0.3, "public": 100 - pr + i * 0.3} for i, d in enumerate(["30-Sep-2026", "30-Jun-2026", "31-Mar-2026"])]}
        return cache, len(symbols)
    STK.ownership = own
    S.multpl_sp500 = spx
    # pre-seed history so the merge path is exercised
    save_json("flows.json", {"mmf": mmf[:-1], "ici": ici[:-1], "nse": nse[:-1]})
    R.main()
    meta = load_json("meta.json")
    meta["demo"] = True
    save_json("meta.json", meta)


if __name__ == "__main__":
    main()
