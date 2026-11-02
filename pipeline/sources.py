"""Fetchers for each public source. Every function returns (data, as_of_date_string)
and raises on any problem, so the caller can fall back to the last good data."""
import io
import json
import re
from datetime import date, datetime, timedelta

import pandas as pd

from .util import get, session

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]


def _num(x):
    """Parse '1,234.5', '(12.3)', '-', '$1.2' into float or None."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return None if x != x else float(x)
    t = str(x).strip().replace(",", "").replace("$", "").replace("₹", "").replace("%", "")
    if t in ("", "-", "–", "—", "nan", "NaN"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _infer_year(month_day):
    """'October 29' -> date in the most recent past occurrence."""
    d = datetime.strptime(month_day.strip(), "%B %d").date()
    today = date.today()
    d = d.replace(year=today.year)
    if d > today + timedelta(days=3):
        d = d.replace(year=today.year - 1)
    return d


# ---------------------------------------------------------------- FRED
def fred(series_id, start="2010-01-01"):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}"
    r = get(url)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna()
    s = pd.Series(df["value"].values, index=pd.to_datetime(df["date"]))
    if s.empty:
        raise ValueError("empty series")
    return s, s.index[-1].strftime("%Y-%m-%d")


# ---------------------------------------------------------------- ICI
def _ici_text(url):
    from bs4 import BeautifulSoup
    html = get(url).text
    return " ".join(BeautifulSoup(html, "lxml").get_text(" ").split())


def ici_mmf():
    text = _ici_text("https://www.ici.org/research/stats/mmf")
    m = re.search(r"Total money market fund assets (increased|decreased) by \$([\d.,]+) (billion|million) "
                  r"to \$([\d.,]+) (trillion|billion) for the [\w-]*\s?week ended (?:\w+day, )?([A-Z][a-z]+ \d{1,2})",
                  text)
    if not m:
        raise ValueError("MMF sentence not found on ICI page")
    chg = _num(m.group(2)) * (0.001 if m.group(3) == "million" else 1) * (-1 if m.group(1) == "decreased" else 1)
    tot = _num(m.group(4)) * (1000 if m.group(5) == "trillion" else 1)
    d = _infer_year(m.group(6)).isoformat()
    return {"date": d, "total_bn": tot, "change_bn": chg}, d


ICI_CATS = [("Domestic equity", "US equity funds", "Equities"),
            ("World equity", "World equity funds", "Equities"),
            ("Hybrid", "Hybrid funds", "Multi-asset"),
            ("Taxable bond", "Taxable bond funds", "Bonds"),
            ("Municipal bond", "Municipal bond funds", "Bonds"),
            ("Commodity", "Commodity funds", "Commodities")]


def ici_flows():
    text = _ici_text("https://www.ici.org/research/stats/combined_flows")
    wk = re.search(r"for the [\w-]*\s?week ended (?:\w+day, )?([A-Z][a-z]+ \d{1,2})", text)
    if not wk:
        raise ValueError("week-ended date not found on ICI flows page")
    d = _infer_year(wk.group(1)).isoformat()
    row = {"date": d}
    for key, _, _ in ICI_CATS:
        m = re.search(key + r" funds (?:had|saw|posted|recorded|experienced) (?:net )?estimated (?:net )?"
                      r"(inflows|outflows) of \$([\d.,]+) (billion|million)", text, re.I)
        if m:
            v = _num(m.group(2)) * (0.001 if m.group(3).lower() == "million" else 1)
            row[key] = v if m.group(1).lower() == "inflows" else -v
    if len(row) < 3:
        raise ValueError("could not read fund categories from ICI page")
    return row, d


# ---------------------------------------------------------------- CFTC
def cftc(markets):
    codes = ",".join(f"'{c}'" for c in markets)
    params = {"$where": f"cftc_contract_market_code in({codes})",
              "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": "1500"}
    r = get("https://publicreporting.cftc.gov/resource/6dca-aqww.json", params=params)
    rows = r.json()
    out = {}
    for x in rows:
        c = x.get("cftc_contract_market_code")
        if c not in markets:
            continue
        lng, sht, oi = _num(x.get("noncomm_positions_long_all")), _num(x.get("noncomm_positions_short_all")), _num(x.get("open_interest_all"))
        if None in (lng, sht) or not oi:
            continue
        out.setdefault(c, []).append({"date": x["report_date_as_yyyy_mm_dd"][:10], "net": lng - sht, "net_pct_oi": (lng - sht) / oi})
    if not out:
        raise ValueError("no CFTC rows")
    res = []
    for c, hist in out.items():
        hist = sorted(hist, key=lambda r: r["date"])[-60:]
        last = hist[-1]
        prev4 = hist[-5] if len(hist) >= 5 else hist[0]
        pcts = [h["net_pct_oi"] for h in hist[-52:]]
        lo, hi = min(pcts), max(pcts)
        res.append({"code": c, "name": markets[c], "date": last["date"], "net": last["net"],
                    "net_pct_oi": last["net_pct_oi"], "chg4w_pct_oi": last["net_pct_oi"] - prev4["net_pct_oi"],
                    "pctile_1y": (last["net_pct_oi"] - lo) / (hi - lo) if hi > lo else None,
                    "history": [[h["date"], round(h["net_pct_oi"], 4)] for h in hist]})
    as_of = max(r["date"] for r in res)
    return res, as_of


# ---------------------------------------------------------------- Farside (spot crypto ETF flows)
def farside(kind="btc"):
    r = get(f"https://farside.co.uk/{kind}/")
    tables = pd.read_html(io.StringIO(r.text))
    best = None
    for t in tables:
        cols = [str(c[-1] if isinstance(c, tuple) else c).strip().lower() for c in t.columns]
        if "total" in cols and len(t) > 10:
            best, tcol = t, cols.index("total")
            break
    if best is None:
        raise ValueError("flow table not found")
    rows = []
    for _, rr in best.iterrows():
        try:
            d = pd.to_datetime(str(rr.iloc[0]), format="%d %b %Y", errors="raise")
        except Exception:
            continue
        v = _num(rr.iloc[tcol])
        if v is not None:
            rows.append({"date": d.strftime("%Y-%m-%d"), "value_mn": v})
    if not rows:
        raise ValueError("no dated rows")
    rows.sort(key=lambda r: r["date"])
    return rows, rows[-1]["date"]


# ---------------------------------------------------------------- India: NSE FII/DII (latest day)
def nse_fii_dii():
    s = session()
    s.headers.update({"Referer": "https://www.nseindia.com/reports/fii-dii", "Accept": "application/json"})
    get("https://www.nseindia.com/", sess=s)
    data = get("https://www.nseindia.com/api/fiidiiTradeReact", sess=s).json()
    row = {}
    for x in data:
        cat = str(x.get("category", "")).upper()
        key = "dii" if cat.startswith("DII") else "fii" if cat.startswith("FII") else None
        if key:
            row[key] = _num(x.get("netValue"))
            row["date"] = pd.to_datetime(x.get("date")).strftime("%Y-%m-%d")
    if "date" not in row:
        raise ValueError("unexpected NSE response")
    return row, row["date"]


# ---------------------------------------------------------------- India: NSDL FPI
def _flat_tables(html):
    tables = pd.read_html(io.StringIO(html))
    out = []
    for t in tables:
        t = t.copy()
        t.columns = [" ".join(str(x) for x in (c if isinstance(c, tuple) else (c,))).strip() for c in t.columns]
        out.append(t)
    return out


def nsdl_daily():
    """Latest daily FPI net investment (Rs crore) by Equity / Debt from NSDL 'Latest' report."""
    html = get("https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx").text
    rows = []
    for t in _flat_tables(html):
        net_col = next((c for c in t.columns if "net" in c.lower() and ("crore" in c.lower() or "inr" in c.lower() or "rs" in c.lower())), None)
        if net_col is None:
            continue
        cur_date = None
        for _, r in t.iterrows():
            cells = [str(v) for v in r.values]
            for c in cells:
                try:
                    cur_date = pd.to_datetime(c, dayfirst=True, errors="raise").strftime("%Y-%m-%d")
                    break
                except Exception:
                    pass
            label = " ".join(cells).lower()
            typ = "equity" if "equity" in label else "debt" if "debt" in label else None
            v = _num(r[net_col])
            if cur_date and typ and v is not None and "total" not in label:
                rows.append({"date": cur_date, "type": typ, "value_cr": v})
    if not rows:
        raise ValueError("NSDL daily table not recognised")
    by = {}
    for r in rows:
        by.setdefault(r["date"], {"date": r["date"]}).setdefault(r["type"], 0)
        by[r["date"]][r["type"]] += r["value_cr"]
    res = sorted(by.values(), key=lambda r: r["date"])
    return res, res[-1]["date"]


def nsdl_monthly():
    """Month-wise FPI net investment (Rs crore), equity and debt, current + previous calendar year."""
    res = {}
    yr = date.today().year
    for y in (yr - 1, yr):
        html = None
        for url in (f"https://www.fpi.nsdl.co.in/web/Reports/Yearwise.aspx?RptType=6&year={y}",
                    "https://www.fpi.nsdl.co.in/web/Reports/Monthly.aspx"):
            try:
                html = get(url).text
                break
            except Exception:
                continue
        if not html:
            continue
        for t in _flat_tables(html):
            cols = [c.lower() for c in t.columns]
            eq = next((t.columns[i] for i, c in enumerate(cols) if "equity" in c), None)
            debt = next((t.columns[i] for i, c in enumerate(cols) if c.startswith("debt") or " debt" in c), None)
            if eq is None:
                continue
            for _, r in t.iterrows():
                first = str(r.iloc[0]).strip().lower()
                mi = next((i for i, m in enumerate(MONTHS) if first.startswith(m[:3])), None)
                if mi is None:
                    continue
                ym = re.search(r"(20\d\d)", first)
                yy = int(ym.group(1)) if ym else y
                key = f"{yy}-{mi + 1:02d}"
                res[key] = {"date": key, "equity": _num(r[eq]), "debt": _num(r[debt]) if debt else None}
    if not res:
        raise ValueError("NSDL monthly table not recognised")
    rows = [res[k] for k in sorted(res)]
    return rows, rows[-1]["date"]


# ---------------------------------------------------------------- India: AMFI monthly flows
def _amfi_month(y, m, categories):
    mon = MONTHS[m - 1][:3]
    url = f"https://portal.amfiindia.com/spages/am{mon}{y}repo.xls"
    r = get(url, tries=2)
    raw = pd.read_excel(io.BytesIO(r.content), header=None)
    hdr_row, net_col = None, None
    for i in range(min(20, len(raw))):
        for j, v in enumerate(raw.iloc[i].values):
            if isinstance(v, str) and "net inflow" in v.lower():
                hdr_row, net_col = i, j
                break
        if hdr_row is not None:
            break
    if hdr_row is None:
        raise ValueError("AMFI header not found")
    out = {}
    for i in range(hdr_row + 1, len(raw)):
        label = " ".join(str(v) for v in raw.iloc[i].values[:3] if isinstance(v, str)).lower()
        val = _num(raw.iloc[i, net_col])
        if val is None or not label:
            continue
        for key, name, cls in categories:
            if key.lower() in label and name not in out:
                out[name] = val
        if "grand total" in label:
            out["Total"] = val
    if len(out) < 3:
        raise ValueError("AMFI categories not found")
    return out


def amfi(categories, months_back=13, existing=None):
    have = {r["date"] for r in (existing or [])}
    today = date.today()
    rows = []
    misses = 0
    y, m = today.year, today.month
    for _ in range(months_back + 1):
        if misses >= 3 and not rows:
            break
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        key = f"{y}-{m:02d}"
        if key in have and len(rows) > 0:
            continue
        try:
            vals = _amfi_month(y, m, categories)
            rows.append({"date": key, **vals})
            misses = 0
        except Exception as e:
            misses += 1
            print(f"  AMFI {key}: {e}", flush=True)
    if not rows:
        raise ValueError("no AMFI months downloaded")
    rows.sort(key=lambda r: r["date"])
    return rows, rows[-1]["date"]


# ---------------------------------------------------------------- Japan MOF weekly portfolio flows
def japan_mof():
    """Weekly net purchases (100 million yen). Experimental parser for MOF week.csv."""
    r = get("https://www.mof.go.jp/english/policy/international_policy/reference/itn_transactions_in_securities/week.csv")
    text = r.content.decode("utf-8", errors="ignore") or r.content.decode("shift_jis", errors="ignore")
    rows = []
    for line in text.splitlines():
        cells = [c.strip().strip('"') for c in line.split(",")]
        if len(cells) < 10:
            continue
        m = re.search(r"(20\d\d)\.?\s*(\d{1,2})\.?\s*(\d{1,2})", cells[0] + " " + cells[1])
        nums = [_num(c) for c in cells[1:]]
        nums = [n for n in nums if n is not None]
        if not m or len(nums) < 12:
            continue
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        # Layout: outward (equity, long-term debt, short-term) then inward (same); each acquisition, disposition, net
        net = nums[2::3]
        if len(net) < 6:
            continue
        rows.append({"date": d, "jp_buy_foreign_equity": net[0], "jp_buy_foreign_bonds": net[1],
                     "foreign_buy_jp_equity": net[3], "foreign_buy_jp_bonds": net[4]})
    if not rows:
        raise ValueError("MOF table not recognised")
    rows.sort(key=lambda r: r["date"])
    return rows[-60:], rows[-1]["date"]


# ---------------------------------------------------------------- Valuations for return decomposition
def nifty_pe(index_name="NIFTY 50", years=8):
    s = session()
    s.headers.update({"Content-Type": "application/json; charset=utf-8", "Referer": "https://www.niftyindices.com/reports/historical-data",
                      "X-Requested-With": "XMLHttpRequest"})
    end = date.today()
    start = end.replace(year=end.year - years)
    payload = {"cinfo": json.dumps({"name": index_name, "startDate": start.strftime("%d-%b-%Y"),
                                    "endDate": end.strftime("%d-%b-%Y"), "indexName": index_name}).replace('"', "'")}
    r = s.post("https://www.niftyindices.com/Backpage.aspx/getpepbHistoricaldataDBtoString", data=json.dumps(payload), timeout=40)
    r.raise_for_status()
    data = json.loads(r.json()["d"])
    rows = []
    for x in data:
        k = {kk.lower(): v for kk, v in x.items()}
        dt = pd.to_datetime(k.get("date") or k.get("historicaldate"), dayfirst=True, errors="coerce")
        pe = _num(k.get("pe")); dy = _num(k.get("divyield"))
        if dt is not pd.NaT and pe:
            rows.append((dt, pe, dy))
    if not rows:
        raise ValueError("no P/E rows")
    df = pd.DataFrame(rows, columns=["date", "pe", "dy"]).set_index("date").sort_index()
    return df, df.index[-1].strftime("%Y-%m-%d")


def multpl_sp500():
    def table(slug):
        r = get(f"https://www.multpl.com/{slug}/table/by-month")
        t = pd.read_html(io.StringIO(r.text))[0]
        t.columns = ["date", "value"]
        t["date"] = pd.to_datetime(t["date"], errors="coerce")
        t["value"] = t["value"].map(lambda v: _num(re.sub(r"[^\d.\-()]", "", str(v).split()[0] if str(v).split() else "")))
        return t.dropna().set_index("date")["value"].sort_index()
    eps = table("s-p-500-earnings")
    dy = table("s-p-500-dividend-yield")
    df = pd.concat([eps.rename("eps"), dy.rename("dy")], axis=1).sort_index()
    return df, eps.index[-1].strftime("%Y-%m-%d")
