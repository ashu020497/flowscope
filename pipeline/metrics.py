"""Return and risk metrics from a daily close series (pandas Series, DatetimeIndex)."""
import numpy as np
import pandas as pd

PERIODS = [("1D", None), ("1W", 7), ("1M", 30), ("3M", 91), ("6M", 182), ("YTD", "ytd"),
           ("1Y", 365), ("3Y", 365 * 3), ("5Y", 365 * 5), ("10Y", 365 * 10)]


def _asof(s, when):
    sub = s[s.index <= when]
    return (sub.iloc[-1], sub.index[-1]) if len(sub) else (None, None)


def returns(s):
    s = s.dropna()
    out = {}
    if len(s) < 2:
        return out
    last, last_d = s.iloc[-1], s.index[-1]
    for label, days in PERIODS:
        if days is None:
            out[label] = last / s.iloc[-2] - 1
            continue
        if days == "ytd":
            base, bd = _asof(s, pd.Timestamp(year=last_d.year, month=1, day=1) - pd.Timedelta(days=1))
        else:
            target = last_d - pd.Timedelta(days=days)
            if s.index[0] > target + pd.Timedelta(days=7):
                out[label] = None  # not enough history
                continue
            base, bd = _asof(s, target)
        if base is None or base <= 0:
            out[label] = None
            continue
        r = last / base - 1
        if isinstance(days, int) and days > 365:  # annualise multi-year
            yrs = (last_d - bd).days / 365.25
            r = (last / base) ** (1 / yrs) - 1 if yrs > 0 else None
        out[label] = r
    return out


def risk(s, rf_annual=0.0, bench=None, years=3):
    """Volatility, drawdown, Sharpe, Sortino, Calmar, beta/corr vs bench, % up months."""
    s = s.dropna()
    s = s[s > 0]
    if len(s) < 60:
        return {}
    start = s.index[-1] - pd.Timedelta(days=int(365.25 * years))
    w = s[s.index >= start]
    if len(w) < 60:
        return {}
    yrs = max((w.index[-1] - w.index[0]).days / 365.25, 0.25)
    ppy = (len(w) - 1) / yrs  # observations per year (252 for stocks, ~365 for crypto)
    lr = np.log(w).diff().dropna()
    vol = lr.std() * np.sqrt(ppy)
    ann = (w.iloc[-1] / w.iloc[0]) ** (1 / yrs) - 1
    rf = rf_annual or 0.0
    rf_p = np.log(1 + rf) / ppy
    downside = lr[lr < rf_p] - rf_p
    dd_dev = np.sqrt((downside ** 2).sum() / len(lr)) * np.sqrt(ppy) if len(lr) else np.nan
    peak = w.cummax()
    dd = w / peak - 1
    mdd = dd.min()
    m = w.resample("ME").last().pct_change().dropna()
    out = dict(
        vol=vol, ann_return=ann, max_dd=mdd, current_dd=dd.iloc[-1],
        sharpe=(ann - rf) / vol if vol else None,
        sortino=(ann - rf) / dd_dev if dd_dev else None,
        calmar=ann / abs(mdd) if mdd else None,
        up_months=(m > 0).mean() if len(m) else None,
        best_month=m.max() if len(m) else None, worst_month=m.min() if len(m) else None,
        years=yrs,
    )
    ma200 = s.rolling(200).mean().iloc[-1] if len(s) >= 200 else np.nan
    out["vs_200dma"] = s.iloc[-1] / ma200 - 1 if ma200 == ma200 else None
    if bench is not None and len(bench.dropna()) > 60:
        a = w.resample("W-FRI").last().pct_change()
        b = bench.dropna().resample("W-FRI").last().pct_change()
        j = pd.concat([a, b], axis=1, join="inner").dropna()
        if len(j) > 26:
            cov = np.cov(j.iloc[:, 0], j.iloc[:, 1])
            out["beta"] = cov[0, 1] / cov[1, 1] if cov[1, 1] else None
            out["corr"] = j.iloc[:, 0].corr(j.iloc[:, 1])
    return out


def spark(s, points=52):
    s = s.dropna()
    if not len(s):
        return []
    y = s[s.index >= s.index[-1] - pd.Timedelta(days=365)].resample("W-FRI").last().dropna()
    return [float(v) for v in y.values[-points:]]


def compact(s, max_points=1600):
    """Daily up to ~6 years, weekly before that, as [[YYYY-MM-DD, close], ...]."""
    s = s.dropna()
    cut = s.index[-1] - pd.Timedelta(days=365 * 6)
    old = s[s.index < cut].resample("W-FRI").last().dropna()
    new = s[s.index >= cut]
    both = pd.concat([old, new])
    if len(both) > max_points:
        both = both.iloc[:: int(np.ceil(len(both) / max_points))]
    return [[d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in both.items()]
