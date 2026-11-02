# Flowscope

A self-updating website that tracks **where money is moving** across regions and asset classes, and how each asset has performed:

- **Flows**: net flows by asset class (US: ICI, money-market funds, crypto ETFs · India: AMFI, NSDL, NSE · Japan: MOF), plus futures positioning (CFTC)
- **Assets**: about 70 assets with returns from 1 day to 10 years, plus volatility, max drawdown, Sharpe, Sortino, Calmar, beta, correlation and trend, in local currency or USD
- **Asset pages**: price and drawdown chart, risk metrics in plain English, the earnings split for Nifty 50 and S&P 500 (EPS growth vs P/E change vs dividends), and who is buying or selling
- **Cash & liquidity**: money-market funds, Fed reverse repo, bank deposits, Treasury account, yields and spreads, and India's cash-like fund flows
- **Driver map**: a mind map for every factor, industry, index and stock, covering about 750 Indian stocks (Nifty Total Market). It shows what drives an item and what that item drives, with:
  - direction and strength of each link
  - a plain-English mechanism
  - the measured sensitivity from 3 years of price data, with the market move removed
  - this week's move, flagged as a tailwind or headwind

  Click any node, then **Open**, to re-centre on it. A trail lets you step back. **List** view shows two levels deep, including drivers of drivers and knock-on effects.
- **Shock simulator**: move crude, the rupee, gold, copper, yields, the Nasdaq and more. The page ranks the most helped and hurt stocks and industries, and shows your watchlist's combined exposure.
- **Sources**: every source with its frequency, the date of its latest data, and whether it's current

GitHub refreshes everything **every day at 07:00 IST**, for free. If a source fails, the site keeps its last good data and flags it on the Sources page.

---

## Setup (about 10 minutes, one time)

### 1. Create the repository
1. Go to **github.com → + (top right) → New repository**.
2. Name it `flowscope`. Choose **Public**, because GitHub Pages is free for public repos. Don't add a README.
3. Click **Create repository**.

### 2. Upload the files
1. On the new repo page, click **uploading an existing file**.
2. Unzip `flowscope.zip` on your computer. Open the `flowscope` folder, select **everything inside it** (`.github`, `pipeline`, `site`, `README.md`, `requirements.txt`, `.gitignore`) and drag it into the browser.
   - **Windows**: `.github` is visible as normal.
   - **Mac**: press **Cmd + Shift + .** in Finder to show the hidden `.github` folder before selecting.
3. Click **Commit changes**.
4. Check that the repo now shows a `.github/workflows/update.yml` file. If it's missing, the daily refresh won't run. Re-upload just that folder.

### 3. Turn on GitHub Pages
**Settings → Pages → Build and deployment → Source: GitHub Actions.**

### 4. Allow the refresh job to save data
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

### 5. Run the first refresh
1. Open the **Actions** tab. If prompted, click **I understand my workflows, go ahead and enable them**.
2. Click **Daily data refresh → Run workflow → Run workflow**.
3. Wait about 5–10 minutes until both jobs show a green tick.

### 6. Open your site
`https://<your-github-username>.github.io/flowscope/`

The URL also appears under **Settings → Pages**. Bookmark it on your phone and PC.

From now on it refreshes itself every morning. You can also click **Run workflow** any time for an extra refresh.

---

## After the first run: check the Sources page
Some publishers block automated downloads, or change their page layout without notice. Indian exchange sites are the most likely to block GitHub's US-based servers. Any source that failed shows as **Unavailable** with the error message.

To get help fixing one: open **Actions → the latest run → refresh → "Fetch sources and compute metrics"**, copy the lines containing `FAILED`, and share them.

Some sources only publish the latest period: ICI weekly, NSE daily FII/DII and Farside. For these, history **builds up from your first refresh**, so the 3M/6M/12M windows and daily India chart fill in over time. Until there are enough NSE sessions, the India chart uses monthly AMFI + NSDL data.

## How the driver map is built
| Layer | What it gives | Source |
|---|---|---|
| Factor web | ~90 macro, commodity, currency, rate and flow factors, ~110 cause-and-effect links | Curated in `pipeline/kb.py` |
| Industry templates | 54 industries, each with its drivers and knock-on effects (e.g. paints → construction costs) | Curated; ~420 large stocks mapped by hand, the rest by their NSE industry |
| Measured sensitivity | Each stock's response to Nifty, crude, USD/INR, gold, copper, gas, aluminium, US 10Y, Nasdaq, dollar, India gilts, sugar, cotton | Daily prices, 3-year weekly regressions with the market move removed |
| Dependants | Index membership with approximate weights (by market cap, not free-float), index ETFs, peers ranked by correlation, ownership (promoter vs public) | niftyindices.com, Yahoo Finance, NSE shareholding filings |

Limits:
- **Company-specific supply chains** (exact suppliers and customers) aren't in any free dataset. Stocks inherit their industry's mechanisms.
- **Mutual-fund holdings** need each fund house's monthly file, so the map shows index/ETF ownership instead.
- **Ownership** comes from NSE, which may block GitHub's servers. If so, it shows as unavailable on the Sources page.

To improve a stock's map, edit `pipeline/kb.py`:
- add its symbol to a better-fitting template in the `_m(...)` lines, or
- add new factors to `NODES` and links to `E`.

## Customising
- **Add or remove assets**: edit `pipeline/config.py` (the `ASSETS` list). Each entry needs a Yahoo Finance ticker. Commit, and the site rebuilds automatically.
- **Change the refresh time**: edit the `cron` line in `.github/workflows/update.yml`. It's in UTC; IST = UTC + 5:30.
- **Preview locally with simulated data**: `pip install -r requirements.txt`, `python -m pipeline.demo`, then `cd site && python -m http.server` and open http://localhost:8000. A yellow DEMO banner shows the numbers are fake. **Don't commit demo data.** Delete `site/data` first, or let the next real refresh overwrite it.

## Notes
- GitHub may start scheduled runs 5–30 minutes late at busy times.
- GitHub pauses scheduled workflows in repos with no activity for 60 days. The daily data commits normally keep it active. If the site ever stops updating, re-enable the workflow from the Actions tab.
- Free global fund-flow databases don't exist; EPFR and Lipper are paid. This site uses official and issuer-published data, and says so where coverage is partial.
- Information only, not investment advice.

## How it works
```
.github/workflows/update.yml   daily schedule → runs the pipeline → saves data → publishes the site
pipeline/sources.py            one fetcher per public source
pipeline/prices.py, metrics.py prices and return/risk maths
pipeline/run.py                orchestrates everything, writes site/data/*.json
site/                          the website (plain HTML/CSS/JS, no build step)
```
