"""Driver map data: Indian stock universe, index membership, measured sensitivities, peers,
approximate index weights, ownership, and the factor graph with live moves."""
import io
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import kb
from .util import get, load_json, now_iso, save_json, session

NI = "https://www.niftyindices.com/IndexConstituent/"


def fname(sym):
    return sym.replace("&", "_and_").replace("/", "_")


# ---------------------------------------------------------------- universe & indices
def _nifty_csv(file):
    r = get(NI + file, tries=2)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]
    if "Symbol" not in df.columns:
        raise ValueError(f"{file}: no Symbol column")
    return df


def universe():
    df = _nifty_csv(kb.UNIVERSE_FILE)
    rows = [{"s": str(r["Symbol"]).strip(), "n": str(r.get("Company Name", r["Symbol"])).strip(), "i": str(r.get("Industry", "")).strip()}
            for _, r in df.iterrows()]
    return rows, date.today().isoformat()


def memberships():
    out, ok = {}, 0
    for i, (key, (_, file)) in enumerate(kb.INDICES.items()):
        if i >= 3 and ok == 0:
            break
        try:
            out[key] = set(_nifty_csv(file)["Symbol"].astype(str).str.strip())
            ok += 1
        except Exception as e:
            print(f"  index {key}: {e}")
    if not ok:
        raise RuntimeError("no index constituent files downloaded")
    return {k: sorted(v) for k, v in out.items()}, date.today().isoformat()


def template_for(sym, industry):
    return kb.STOCKS.get(sym) or kb.BROAD.get(industry) or "default"


# ---------------------------------------------------------------- measured sensitivities
def weekly(series):
    return series.resample("W-FRI").last().dropna()


def factor_returns(px):
    out = {}
    for k, (_, t, kind) in kb.FACTORS.items():
        s = px.get(t)
        if s is None or len(s) < 100:
            continue
        w = weekly(s)
        out[k] = (w.diff() if kind == "yld" else w.pct_change()).dropna()
    return pd.DataFrame(out)


def sensitivities(stock_w, F, years=3):
    """Two-factor betas (market + factor) for each factor, plus multi-factor R²."""
    r = stock_w.pct_change().dropna()
    r = r[r.index >= r.index[-1] - pd.Timedelta(days=int(365.25 * years))] if len(r) else r
    j = pd.concat([r.rename("y"), F], axis=1, join="inner").dropna(how="any", subset=["y"])
    res = {}
    if len(j) < 52 or "nifty" not in j:
        return res, None, None
    y = j["y"]
    m = j["nifty"].fillna(0)
    vm = m.var()
    beta_mkt = y.cov(m) / vm if vm else None
    for k in F.columns:
        x = j[k]
        ok = x.notna()
        if ok.sum() < 52 or x[ok].std() == 0:
            continue
        if k == "nifty":
            res[k] = {"beta": beta_mkt, "corr": y.corr(m)}
            continue
        X = np.column_stack([np.ones(ok.sum()), m[ok].values, x[ok].values])
        coef, *_ = np.linalg.lstsq(X, y[ok].values, rcond=None)
        res[k] = {"beta": float(coef[2]), "corr": float(y[ok].corr(x[ok]))}
    full = j.dropna()
    r2 = None
    if len(full) >= 52:
        X = np.column_stack([np.ones(len(full))] + [full[c].values for c in F.columns if c in full])
        coef, *_ = np.linalg.lstsq(X, full["y"].values, rcond=None)
        resid = full["y"].values - X @ coef
        tot = ((full["y"] - full["y"].mean()) ** 2).sum()
        r2 = float(1 - (resid ** 2).sum() / tot) if tot else None
    return res, beta_mkt, r2


def _ret(s, days):
    s = s.dropna()
    if len(s) < 2:
        return None
    base = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return float(s.iloc[-1] / base.iloc[-1] - 1) if len(base) else None


# ---------------------------------------------------------------- market cap (cached weekly)
def market_caps(symbols, px, cache, max_seconds=420):
    import time
    import yfinance as yf
    t0 = time.time()
    today = date.today()
    n = fails = 0
    for s in symbols:
        if time.time() - t0 > max_seconds:
            print("  market caps: time cap reached, the rest refresh next run", flush=True)
            break
        if fails >= 15:
            print("  market caps: 15 consecutive failures, stopping for this run")
            break
        c = cache.get(s)
        if c and (today - date.fromisoformat(c["d"])).days < 7:
            continue
        if n >= 900:
            break
        try:
            sh = yf.Ticker(s + ".NS").fast_info.get("shares")
            if sh:
                cache[s] = {"shares": float(sh), "d": today.isoformat()}
                fails = 0
            else:
                fails += 1
            n += 1
        except Exception:
            n += 1
            fails += 1
    caps = {}
    for s in symbols:
        p = px.get(s + ".NS")
        c = cache.get(s)
        if p is not None and len(p) and c:
            caps[s] = float(p.iloc[-1]) * c["shares"] / 1e7  # ₹ crore
    return caps


# ---------------------------------------------------------------- ownership (cached ~monthly)
def ownership(symbols, cache, limit=150):
    """Promoter / public split from NSE shareholding master. Returns (cache, n_ok)."""
    s = session()
    s.headers.update({"Referer": "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern", "Accept": "application/json"})
    try:
        get("https://www.nseindia.com/", sess=s, tries=1, timeout=20)
    except Exception as e:
        raise RuntimeError(f"NSE not reachable: {e}")
    today = date.today()
    todo = [x for x in symbols if not cache.get(x) or (today - date.fromisoformat(cache[x]["checked"])).days > 30][:limit]
    ok = fails = 0
    for sym in todo:
        try:
            r = s.get("https://www.nseindia.com/api/corporate-share-holdings-master", params={"index": "equities", "symbol": sym}, timeout=20)
            data = r.json()
            hist = []
            for q in data if isinstance(data, list) else data.get("data", []):
                k = {kk.lower(): v for kk, v in q.items()}
                pr = next((k[x] for x in k if x.startswith("pr_and_prgrp") or x == "promoter"), None)
                pub = next((k[x] for x in k if x.startswith("public_val") or x == "public"), None)
                dt = k.get("date") or k.get("asondate")
                try:
                    pr, pub = float(pr), float(pub)
                except (TypeError, ValueError):
                    continue
                hist.append({"date": str(dt), "promoter": pr, "public": pub})
            if hist:
                cache[sym] = {"checked": today.isoformat(), "hist": hist[:6], "src": "NSE shareholding pattern"}
                ok += 1
            else:
                fails += 1
        except Exception:
            fails += 1
        if fails > 10 and ok == 0:
            raise RuntimeError("NSE shareholding endpoint not responding")
    return cache, ok


# ---------------------------------------------------------------- factor graph with live moves
def node_moves(px, fred, assets_by_id):
    moves = {}
    for nid, (name, kind, ser, desc) in kb.NODES.items():
        if not ser:
            continue
        typ, ref = ser.split(":", 1)
        s = None
        if typ == "a" and ref in assets_by_id:
            s = px.get(assets_by_id[ref]["ticker"])
        elif typ == "y":
            s = px.get(ref)
        elif typ == "f":
            s = fred.get(ref)
        if s is None or len(s.dropna()) < 3:
            continue
        s = s.dropna()
        diff = kind in ("Rates", "Policy") or (typ == "f" and ref in ("DFF", "DFII10"))
        level_series = typ == "f" and ref in ("CPIAUCSL", "INDCPIALLMINMEI", "WALCL")

        def chg(days):
            base = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
            if not len(base):
                return None
            return float(s.iloc[-1] - base.iloc[-1]) if diff else float(s.iloc[-1] / base.iloc[-1] - 1)
        m = {"last": float(s.iloc[-1]), "date": s.index[-1].strftime("%Y-%m-%d"), "unit": "pp" if diff else "%"}
        if level_series:  # monthly/weekly levels: show YoY
            m["w1"] = chg(7) if ref == "WALCL" else None
            m["m1"] = chg(31)
            m["y1"] = chg(365)
        else:
            m["w1"], m["m1"] = chg(7), chg(31)
        moves[nid] = m
    return moves


def build(px_download, px_existing, fred, assets_by_id, log, SRC):
    """Called from run.main after market data is loaded."""
    old_index = load_json("stocks/index.json", {}) or {}
    uni = log.run("nifty_universe", SRC["nifty_universe"], universe, budget=60,
                  fallback=[{"s": x["s"], "n": x["n"], "i": x["i"]} for x in old_index.get("stocks", [])] or None)
    if not uni:
        uni = [{"s": s, "n": s, "i": ""} for s in sorted(kb.STOCKS)]
    mem = log.run("nifty_indices", SRC["nifty_indices"], memberships, fallback=old_index.get("memberships"), budget=180) or {}

    syms = [u["s"] for u in uni]
    tick = [s + ".NS" for s in syms] + [t for _, t, _ in kb.FACTORS.values()] + \
           [ser[2:] for (_, _, ser, _) in kb.NODES.values() if ser and ser.startswith("y:")]
    px = dict(px_existing)

    def _px():
        got = px_download([t for t in tick if t not in px], years=4)
        px.update(got)
        n = sum(1 for s in syms if s + ".NS" in px)
        if n < len(syms) * 0.5:
            raise RuntimeError(f"only {n} of {len(syms)} stocks downloaded")
        return True, max(px[s + ".NS"].index[-1] for s in syms if s + ".NS" in px).strftime("%Y-%m-%d")
    log.run("stock_prices", SRC["stock_prices"], _px, fallback=None, budget=900)

    F = factor_returns(px)
    cache = load_json("stocks/_cache.json", {}) or {}
    mc_cache = cache.get("shares", {})
    own_cache = cache.get("own", {})
    caps = {}
    try:
        caps = market_caps(syms, px, mc_cache, max_seconds=max(30, min(420, log.remaining() - 600)))
    except Exception as e:
        print("  market caps:", e)
    try:
        own_cache, n_own = log.run("nse_ownership", SRC["nse_ownership"], lambda: (lambda r: (r, date.today().isoformat()))(ownership(syms, own_cache)), fallback=(own_cache, 0) if own_cache else None, budget=240) or (own_cache, 0)
    except Exception:
        pass
    save_json("stocks/_cache.json", {"shares": mc_cache, "own": own_cache})

    # index weights (approximate: full market cap, not free-float)
    weights = {}
    for key, members in mem.items():
        tot = sum(caps.get(s, 0) for s in members)
        if tot:
            for s in members:
                if s in caps:
                    weights.setdefault(s, {})[key] = caps[s] / tot

    # per-stock analytics
    info, wk = {}, {}
    old_by = {x["s"]: x for x in old_index.get("stocks", [])}
    for u in uni:
        s = u["s"]
        p = px.get(s + ".NS")
        t = template_for(s, u["i"])
        rec = {"s": s, "n": u["n"], "i": u["i"], "t": t, "mc": round(caps[s]) if s in caps else old_by.get(s, {}).get("mc"),
               "idx": [k for k, v in mem.items() if s in v]}
        if p is not None and len(p) > 60:
            w = weekly(p)
            wk[s] = w.pct_change()
            sens, bm, r2 = sensitivities(w, F)
            lr = np.log(p).diff().dropna()
            last_year = lr[lr.index >= lr.index[-1] - pd.Timedelta(days=365)]
            rec.update(last=float(p.iloc[-1]), date=p.index[-1].strftime("%Y-%m-%d"), r1d=float(p.iloc[-1] / p.iloc[-2] - 1),
                       r1w=_ret(p, 7), r1m=_ret(p, 30), r3m=_ret(p, 91), r1y=_ret(p, 365), r3y=_ret(p, 1095),
                       vol=float(last_year.std() * np.sqrt(252)) if len(last_year) > 20 else None,
                       bm=bm, r2=r2, sens=sens, spark=[float(v) for v in w.values[-52:]])
        elif s in old_by:
            rec.update({k: v for k, v in old_by[s].items() if k not in rec}, stale=True)
        info[s] = rec

    # peers: same template (fallback same NSE industry), ranked by weekly-return correlation (2y)
    W = pd.DataFrame(wk)
    W = W[W.index >= W.index.max() - pd.Timedelta(days=730)] if len(W) else W
    groups = {}
    for s, r in info.items():
        groups.setdefault(r["t"] if r["t"] != "default" else "i:" + r["i"], []).append(s)
    for g, members in groups.items():
        if len(members) < 3:
            members = [x for x in info if info[x]["i"] == info[members[0]]["i"]]
        cols = [m for m in members if m in W]
        C = W[cols].corr(min_periods=40) if len(cols) > 1 else None
        for s in members:
            if C is None or s not in C:
                info[s]["peers"] = [{"s": m, "c": None} for m in members if m != s][:6]
                continue
            c = C[s].drop(s).dropna().sort_values(ascending=False)
            info[s]["peers"] = [{"s": m, "c": float(v)} for m, v in c.head(6).items()]

    # exposure matrix for the shock simulator
    fkeys = [k for k in kb.FACTORS if k in F.columns]
    exp_syms = [s for s in info if info[s].get("sens")]
    beta = [[(info[s]["sens"].get(k) or {}).get("beta") for k in fkeys] for s in exp_syms]
    save_json("exposure.json", {"generated": now_iso(), "factors": fkeys,
                                "labels": {k: kb.FACTORS[k][0] for k in fkeys}, "kinds": {k: kb.FACTORS[k][2] for k in fkeys},
                                "stocks": exp_syms, "names": [info[s]["n"] for s in exp_syms], "tmpl": [info[s]["t"] for s in exp_syms],
                                "mc": [info[s].get("mc") for s in exp_syms], "beta": beta})

    # top exposed stocks per factor (shown as dependants of that factor)
    top = {}
    for j, k in enumerate(fkeys):
        pairs = [(exp_syms[i], b[j]) for i, b in enumerate(beta) if b[j] is not None and (info[exp_syms[i]].get("mc") or 0) > 5000]
        pairs.sort(key=lambda x: x[1])
        top[k] = {"pos": [{"s": s, "b": b} for s, b in pairs[::-1][:6] if b > 0], "neg": [{"s": s, "b": b} for s, b in pairs[:6] if b < 0]}

    # write per-stock files + index
    for s, r in info.items():
        r2 = dict(r)
        r2["weights"] = weights.get(s, {})
        o = own_cache.get(s)
        if o:
            r2["own"] = o
        save_json(f"stocks/{fname(s)}.json", r2)
    slim = [{k: r.get(k) for k in ("s", "n", "i", "t", "mc", "r1d", "r1w", "r1m", "r1y", "idx", "stale")} for r in info.values()]
    save_json("stocks/index.json", {"generated": now_iso(), "count": len(slim), "memberships": mem, "stocks": slim})

    # graph
    moves = node_moves(px, fred, assets_by_id)
    nodes = {nid: {"name": n[0], "kind": n[1], "series": n[2], "desc": n[3], "move": moves.get(nid)} for nid, n in kb.NODES.items()}
    tmpl = {k: {"name": v["name"], "sector": v["sector_index"], "drivers": v["drivers"], "drives": v["drives"],
                "n": sum(1 for r in info.values() if r["t"] == k)} for k, v in kb.TEMPLATES.items()}
    save_json("graph.json", {"generated": now_iso(), "nodes": nodes, "edges": kb.E, "templates": tmpl,
                             "indices": {k: v[0] for k, v in kb.INDICES.items()}, "etfs": kb.INDEX_ETFS,
                             "factors": {k: v[0] for k, v in kb.FACTORS.items()}, "top": top})
    return len(info)
