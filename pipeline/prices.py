"""Daily prices from Yahoo Finance (via yfinance) for every asset and FX pair."""
import pandas as pd


def download(tickers, years=11):
    import yfinance as yf
    out = {}
    tickers = sorted(set(tickers))
    empty = 0
    for i in range(0, len(tickers), 20):
        if empty >= 2 and not out:
            raise RuntimeError("Yahoo Finance returned no data for the first chunks; aborting")
        chunk = tickers[i:i + 20]
        before = len(out)
        df = yf.download(chunk, period=f"{years}y", interval="1d", auto_adjust=True,
                         group_by="ticker", threads=True, progress=False, timeout=30)
        for t in chunk:
            try:
                col = df[t]["Close"] if isinstance(df.columns, pd.MultiIndex) else df["Close"]
                s = col.dropna()
                s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
                s = s[~s.index.duplicated(keep="last")]
                if len(s) > 5:
                    out[t] = s.astype(float)
            except Exception as e:
                print(f"  price {t}: {e}")
        empty = empty + 1 if len(out) == before else 0
    return out


def to_usd(s, ccy, fx_series, rule):
    if ccy == "USD" or rule is None:
        return s
    fx_t, op = rule
    fx = fx_series.get(fx_t)
    if fx is None:
        return None
    fx = fx.reindex(s.index, method="ffill")
    return (s / fx if op == "div" else s * fx).dropna()
