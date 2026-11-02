"""Curated knowledge base for the driver map.

NODES: id -> (name, kind, series, description)
    series: "a:<asset id in config.ASSETS>", "y:<Yahoo ticker>", "f:<FRED id>" or None (qualitative)
EDGES: (driver, driven, sign, strength, why)
    sign: "+" driver up -> driven up; "-" driver up -> driven down; "~" mixed / depends
    strength: 1 low, 2 medium, 3 high (judgement, shown as "stated importance")
TEMPLATES: industry -> dict(name, sector_index, drivers=[(node, sign, strength, why)], drives=[(node, sign, strength, why)])
    Every stock inherits its industry template. Measured sensitivities are added by the pipeline.
These are mechanisms drawn from public company filings, industry reports and standard economics.
They describe typical relationships, not forecasts.
"""

NODES = {
    # ---------------- Global policy & macro ----------------
    "fed": ("US Federal Reserve policy rate", "Policy", "f:DFF", "The overnight rate set by the US Fed. It anchors global borrowing costs and the dollar."),
    "us10y": ("US 10-year Treasury yield", "Rates", "y:^TNX", "The world's benchmark long-term interest rate."),
    "realyield": ("US real yields (10Y TIPS)", "Rates", "f:DFII10", "Interest rates after inflation. The opportunity cost of holding gold and long-duration assets."),
    "dxy": ("US dollar", "Currency", "a:dxy", "The dollar against major currencies. A strong dollar tightens global financial conditions."),
    "us_inflation": ("US inflation", "Macro", "f:CPIAUCSL", "Consumer price inflation in the US; drives Fed policy."),
    "us_growth": ("US economic growth", "Macro", None, "Activity in the world's largest economy: jobs, spending, earnings."),
    "china_growth": ("China growth & stimulus", "Macro", "a:csi300", "The largest buyer of most commodities; stimulus lifts metals demand."),
    "global_liquidity": ("Global liquidity (Fed balance sheet)", "Policy", "f:WALCL", "Money created by central banks. More liquidity tends to lift risk assets."),
    "risk_appetite": ("Global risk appetite (VIX)", "Market", "a:vix", "Investor fear gauge. A higher VIX means less appetite for risky assets, and is shown inverted in links."),
    "geopolitics": ("Geopolitics & conflicts", "Qualitative", None, "Wars, sanctions and shipping disruptions. They raise risk premiums on oil and gold."),
    "opec": ("OPEC+ supply decisions", "Policy", None, "Production quotas from oil exporters; the biggest swing factor for crude supply."),
    "central_bank_gold": ("Central-bank gold buying", "Flows", None, "Reserve diversification by central banks (China, India, Poland, Turkey) away from the dollar."),
    "ai_capex": ("AI & data-centre investment", "Theme", "a:semis", "Spending on chips, servers and power by large tech firms."),
    "us_tech": ("US tech stocks", "Market", "a:nasdaq100", "Nasdaq 100: sets global tech valuations and sentiment for Indian IT."),
    "us_equities": ("US equities", "Market", "a:sp500", "S&P 500, the anchor for global equity sentiment."),
    "em_equities": ("Emerging-market equities", "Market", "a:em", "Where India competes for foreign portfolio money."),
    "bitcoin": ("Bitcoin", "Market", "a:btc", "The largest crypto asset; trades as a liquidity-sensitive risk asset."),

    # ---------------- India macro & policy ----------------
    "rbi": ("RBI repo rate & liquidity", "Policy", "f:INTGSTINM193N", "The Reserve Bank of India's policy rate and system liquidity (T-bill rate shown)."),
    "india_10y": ("India 10-year G-sec yield", "Rates", "f:INDIRLTLT01STM", "India's benchmark borrowing cost; drives home-loan and corporate rates."),
    "india_bonds": ("India government bond prices", "Rates", "a:indgilt", "Long gilt prices move opposite to yields."),
    "india_cpi": ("India inflation (CPI)", "Macro", "f:INDCPIALLMINMEI", "Consumer inflation; RBI targets 4%. Food and fuel are the swing items."),
    "india_growth": ("India GDP & corporate earnings growth", "Macro", None, "The base for Indian equity returns over time."),
    "govt_capex": ("Government capital spending", "Policy", None, "Union & state spending on roads, rail, defence and power. Drives order books."),
    "fiscal": ("Fiscal deficit & subsidies", "Policy", None, "Government borrowing; higher deficits push bond yields up."),
    "monsoon": ("Monsoon rainfall", "Macro", None, "Sets farm output, rural incomes and food prices for the year."),
    "rural_demand": ("Rural demand", "Macro", None, "Spending by ~65% of India's population; tied to crops, wages and MSP."),
    "urban_demand": ("Urban consumption", "Macro", None, "Spending on discretionary goods, travel, eating out; tied to jobs and wages."),
    "housing": ("Housing & real-estate activity", "Macro", "a:niftyrealty", "New launches, sales and registrations; feeds cement, steel, paints, pipes, furnishings."),
    "credit_growth": ("Bank credit growth", "Macro", None, "Loan growth across retail, MSME and corporates."),
    "auto_demand": ("Vehicle demand", "Macro", "a:niftyauto", "Car, two-wheeler and truck sales."),
    "festive": ("Festive & wedding season", "Qualitative", None, "Oct–Dec spending peak for autos, jewellery, durables and apparel."),
    "power_demand": ("Electricity demand", "Macro", None, "Peak power demand; driven by heat waves, industry and data centres."),
    "usdinr": ("US dollar / Indian rupee", "Currency", "a:usdinr", "Rupees per dollar. Up = weaker rupee: helps exporters, hurts importers."),
    "fpi": ("Foreign portfolio flows into India", "Flows", None, "Net buying by foreign investors (NSDL). Big swing driver for large caps and the rupee."),
    "dii": ("Domestic institutional & SIP flows", "Flows", None, "Monthly SIPs and insurance money: a steady domestic buyer."),
    "nifty": ("Nifty 50", "Market", "a:nifty50", "India's benchmark index; captures overall market moves (beta)."),
    "india_vix": ("India VIX", "Market", "a:indiavix", "Expected Nifty volatility; spikes during sell-offs."),
    "regulation": ("Regulation & policy changes", "Qualitative", None, "SEBI, RBI, tariff and tax decisions that change sector economics."),
    "gst": ("GST & indirect taxes", "Policy", None, "Rate changes alter final prices and demand."),
    "pli": ("Production-linked incentives (PLI)", "Policy", None, "Subsidies for domestic manufacturing (electronics, solar, pharma inputs, autos)."),
    "tariffs": ("Global trade tariffs", "Policy", None, "Import duties by the US and others on Indian goods (textiles, gems, chemicals, auto parts)."),

    # ---------------- Commodities ----------------
    "brent": ("Crude oil (Brent)", "Commodity", "a:brent", "The global oil benchmark; India imports ~85% of its crude."),
    "natgas": ("Natural gas / LNG", "Commodity", "a:natgas", "Fuel for power, fertiliser and city gas; India imports ~half its gas as LNG."),
    "coal": ("Coal prices", "Commodity", None, "Thermal coal for power and coking coal for steel."),
    "gold": ("Gold", "Commodity", "a:gold", "The global safe-haven and reserve asset."),
    "silver": ("Silver", "Commodity", "a:silver", "Half precious metal, half industrial (solar, electronics)."),
    "copper": ("Copper", "Commodity", "a:copper", "Industrial bellwether: wiring, power grids, EVs, data centres."),
    "aluminium": ("Aluminium", "Commodity", "y:ALI=F", "Packaging, autos, power lines; energy-intensive to produce."),
    "steel": ("Steel (HRC)", "Commodity", "y:HRC=F", "Hot-rolled coil prices; India's steelmakers price off global and import parity."),
    "iron_ore": ("Iron ore", "Commodity", None, "The main steel input."),
    "zinc": ("Zinc & lead", "Commodity", None, "Galvanising steel; batteries."),
    "tio2": ("Titanium dioxide", "Commodity", None, "White pigment used in paints and plastics."),
    "palm_oil": ("Edible oils (palm, soy)", "Commodity", None, "Key input for soaps, foods and snacks; India imports most of it."),
    "wheat": ("Wheat & grains", "Commodity", "y:ZW=F", "Input for flour, biscuits and food prices."),
    "sugar": ("Sugar", "Commodity", "y:SB=F", "Global sugar price; drives Indian mill realisations and ethanol economics."),
    "cotton": ("Cotton", "Commodity", "y:CT=F", "Main textile raw material."),
    "rubber": ("Natural rubber", "Commodity", None, "Tyre input with synthetic rubber (crude-linked)."),
    "lithium": ("Lithium & battery materials", "Commodity", None, "EV and storage battery costs."),
    "fertiliser_inputs": ("Fertiliser inputs (ammonia, phosphate)", "Commodity", None, "Imported raw materials for urea/DAP makers."),
    "chemicals_china": ("China chemical prices & dumping", "Commodity", None, "Chinese oversupply sets global prices for many specialty chemicals."),

    # ---------------- Sector indices (also used as dependants) ----------------
    "sec_bank": ("Nifty Bank", "Sector", "a:niftybank", "Bank stocks index."),
    "sec_it": ("Nifty IT", "Sector", "a:niftyit", "IT services index."),
    "sec_pharma": ("Nifty Pharma", "Sector", "a:niftypharma", "Pharmaceuticals index."),
    "sec_fmcg": ("Nifty FMCG", "Sector", "a:niftyfmcg", "Consumer staples index."),
    "sec_auto": ("Nifty Auto", "Sector", "a:niftyauto", "Autos & auto components index."),
    "sec_metal": ("Nifty Metal", "Sector", "a:niftymetal", "Metals & mining index."),
    "sec_energy": ("Nifty Energy", "Sector", "a:niftyenergy", "Oil, gas and power index."),
    "sec_realty": ("Nifty Realty", "Sector", "a:niftyrealty", "Real-estate developers index."),

    # ---------------- Qualitative downstream effects ----------------
    "construction_cost": ("Construction & finishing costs", "Qualitative", None, "Cost of building and finishing homes, offices and infrastructure."),
    "home_affordability": ("Home affordability", "Qualitative", None, "Price and EMI burden for home buyers."),
    "food_inflation": ("Food inflation", "Qualitative", None, "Prices of cereals, vegetables, edible oils, milk; ~45% of India's CPI."),
    "fuel_prices": ("Petrol, diesel & LPG prices", "Qualitative", None, "Retail fuel prices; partly set by government and oil marketers."),
    "transport_cost": ("Freight & logistics costs", "Qualitative", None, "Trucking, shipping and air-freight costs across the economy."),
    "electricity_tariff": ("Electricity tariffs", "Qualitative", None, "Power prices for homes and industry."),
    "trade_deficit": ("India trade & current-account deficit", "Macro", None, "Import bill minus exports; oil and gold are the largest imports."),
    "jobs_wages": ("Jobs & wages", "Macro", None, "Hiring and salary growth (IT, banking and manufacturing are big employers)."),
    "consumer_wallet": ("Household spending power", "Qualitative", None, "What households have left after essentials and EMIs."),
    "vehicle_cost": ("Vehicle prices & running costs", "Qualitative", None, "Sticker prices and fuel/tyre costs of owning vehicles."),
    "farm_income": ("Farm incomes", "Qualitative", None, "Crop output × prices; drives rural demand."),
    "bank_asset_quality": ("Bank loan quality (NPAs)", "Qualitative", None, "Share of loans at risk of default."),
    "savings_shift": ("Household savings shift to markets", "Qualitative", None, "Money moving from deposits/gold into mutual funds and stocks."),
    "jewellery_demand": ("Jewellery demand", "Qualitative", None, "Consumer gold jewellery buying."),
    "gold_loans": ("Gold-loan collateral value", "Qualitative", None, "Value of gold pledged against loans."),
    "infra_buildout": ("Infrastructure build-out", "Qualitative", None, "Roads, rail, ports, power and urban projects."),
    "telecom_tariffs": ("Mobile tariffs & data costs", "Qualitative", None, "Prices paid for mobile and broadband."),
    "healthcare_cost": ("Healthcare costs", "Qualitative", None, "Prices of medicines and hospital care."),
    "digital_adoption": ("Digital & AI adoption by companies", "Qualitative", None, "Corporate spending on software, cloud and AI."),
    "travel_demand": ("Travel & tourism demand", "Qualitative", None, "Flights, hotels and leisure spending."),
    "power_supply": ("Power supply & capacity", "Qualitative", None, "Generation capacity and grid reliability."),
    "packaging_cost": ("Packaging costs", "Qualitative", None, "Cost of plastic, paper, glass and aluminium packaging for consumer goods."),
}

E = [
    # global rates, dollar, liquidity
    ("fed", "us10y", "+", 3, "Policy-rate expectations anchor Treasury yields."),
    ("us_inflation", "fed", "+", 3, "Higher inflation pushes the Fed to keep rates high."),
    ("us_growth", "us10y", "+", 2, "Stronger growth lifts yields."),
    ("us10y", "realyield", "+", 3, "Real yield = nominal yield minus inflation expectations."),
    ("fed", "dxy", "+", 3, "Higher US rates attract capital to the dollar."),
    ("us_growth", "dxy", "+", 1, "US outperformance supports the dollar."),
    ("global_liquidity", "risk_appetite", "+", 2, "Abundant liquidity lifts appetite for risk (lower VIX)."),
    ("fed", "global_liquidity", "-", 2, "Rate hikes and balance-sheet shrinkage drain liquidity."),
    ("dxy", "em_equities", "-", 2, "A strong dollar tightens conditions for emerging markets."),
    ("dxy", "usdinr", "+", 3, "When the dollar strengthens globally, the rupee usually weakens."),
    ("us10y", "us_tech", "-", 2, "Higher discount rates hit long-duration growth stocks."),
    ("ai_capex", "us_tech", "+", 3, "AI spending drives earnings of chipmakers and cloud firms."),
    ("us_growth", "us_equities", "+", 3, "Earnings follow the economy."),
    ("risk_appetite", "us_equities", "+", 2, "Calm markets support valuations."),
    ("global_liquidity", "bitcoin", "+", 3, "Bitcoin trades as a liquidity-sensitive asset."),
    ("risk_appetite", "bitcoin", "+", 2, "Risk-on periods lift crypto."),
    ("dxy", "bitcoin", "-", 1, "A weaker dollar has tended to support crypto."),
    # gold
    ("realyield", "gold", "-", 3, "Gold pays no interest; higher real yields raise the cost of holding it."),
    ("dxy", "gold", "-", 2, "Gold is priced in dollars; a strong dollar makes it costlier elsewhere."),
    ("central_bank_gold", "gold", "+", 3, "Central banks have bought ~1,000 t a year since 2022."),
    ("geopolitics", "gold", "+", 2, "Safe-haven demand rises in conflicts."),
    ("risk_appetite", "gold", "-", 1, "Fear (high VIX) can lift gold as a hedge."),
    ("gold", "silver", "+", 3, "Silver tracks gold with higher volatility."),
    ("gold", "jewellery_demand", "-", 2, "Higher prices cut volumes but lift value per gram."),
    ("gold", "gold_loans", "+", 3, "Higher gold prices raise collateral values and loan sizes."),
    ("gold", "trade_deficit", "+", 2, "Gold is India's second-largest import."),
    # oil
    ("opec", "brent", "-", 3, "More supply lowers prices; cuts raise them."),
    ("china_growth", "brent", "+", 2, "China is the largest crude importer."),
    ("us_growth", "brent", "+", 2, "Global demand sets the trend."),
    ("geopolitics", "brent", "+", 3, "Middle East and Russia risks add a supply premium."),
    ("dxy", "brent", "-", 1, "Dollar-priced commodities fall when the dollar rises."),
    ("brent", "fuel_prices", "+", 2, "Retail fuel follows crude with policy lags."),
    ("brent", "trade_deficit", "+", 3, "Oil is India's largest import (~25% of the bill)."),
    ("brent", "usdinr", "+", 2, "A higher oil bill weakens the rupee."),
    ("brent", "india_cpi", "+", 2, "Fuel, transport and petrochemical costs feed inflation."),
    ("brent", "transport_cost", "+", 2, "Diesel is the main trucking cost."),
    ("brent", "fiscal", "+", 1, "LPG and fertiliser subsidies rise with energy prices."),
    ("natgas", "electricity_tariff", "+", 1, "Gas-fired power and LNG costs."),
    ("natgas", "fertiliser_inputs", "+", 3, "Gas is the feedstock for urea and ammonia."),
    ("brent", "natgas", "+", 1, "Many LNG contracts are oil-indexed."),
    # metals
    ("china_growth", "copper", "+", 3, "China uses ~55% of the world's copper."),
    ("china_growth", "steel", "+", 3, "China makes over half the world's steel; its exports set prices."),
    ("china_growth", "iron_ore", "+", 3, "Chinese steel output sets iron ore demand."),
    ("china_growth", "aluminium", "+", 2, "China dominates aluminium supply and demand."),
    ("china_growth", "zinc", "+", 2, "Galvanising demand from Chinese construction."),
    ("ai_capex", "copper", "+", 2, "Data centres and grid upgrades are copper-intensive."),
    ("ai_capex", "power_demand", "+", 2, "Data centres add electricity load."),
    ("iron_ore", "steel", "+", 2, "Raw-material costs pass through to steel."),
    ("coal", "steel", "+", 2, "Coking coal is the second main input."),
    ("coal", "electricity_tariff", "+", 2, "~70% of India's power is coal-fired."),
    ("steel", "construction_cost", "+", 2, "Rebar and structural steel."),
    ("steel", "vehicle_cost", "+", 1, "Body and chassis steel."),
    ("copper", "construction_cost", "+", 1, "Wiring and plumbing."),
    ("aluminium", "packaging_cost", "+", 1, "Cans and foil packaging."),
    ("brent", "packaging_cost", "+", 2, "Plastic packaging is crude-derived."),
    # India macro
    ("fed", "rbi", "+", 1, "RBI weighs global rates and the rupee."),
    ("india_cpi", "rbi", "+", 3, "RBI targets 4% inflation."),
    ("rbi", "india_10y", "+", 3, "Policy rate anchors the yield curve."),
    ("fiscal", "india_10y", "+", 2, "More government borrowing pushes yields up."),
    ("us10y", "india_10y", "+", 1, "Global yields influence foreign demand for Indian bonds."),
    ("india_10y", "india_bonds", "-", 3, "Bond prices fall when yields rise."),
    ("rbi", "credit_growth", "-", 2, "Higher rates slow borrowing."),
    ("india_10y", "housing", "-", 2, "Home-loan rates follow benchmark yields."),
    ("monsoon", "farm_income", "+", 3, "Rain-fed farming covers about half of cropland."),
    ("monsoon", "food_inflation", "-", 2, "Good rains lower food prices."),
    ("food_inflation", "india_cpi", "+", 3, "Food is ~45% of CPI."),
    ("farm_income", "rural_demand", "+", 3, "Crop incomes fund rural spending."),
    ("jobs_wages", "urban_demand", "+", 3, "Salaries fund urban spending."),
    ("india_cpi", "consumer_wallet", "-", 2, "Inflation erodes real incomes."),
    ("consumer_wallet", "urban_demand", "+", 2, "Spare cash goes to discretionary goods."),
    ("india_10y", "consumer_wallet", "-", 1, "Higher EMIs squeeze budgets."),
    ("govt_capex", "infra_buildout", "+", 3, "Budget spending funds projects."),
    ("infra_buildout", "india_growth", "+", 2, "Investment-led growth."),
    ("credit_growth", "india_growth", "+", 2, "Credit funds investment and consumption."),
    ("rural_demand", "india_growth", "+", 2, "Consumption is ~60% of GDP."),
    ("urban_demand", "india_growth", "+", 2, "Consumption is ~60% of GDP."),
    ("india_growth", "nifty", "+", 3, "Earnings growth drives the index over time."),
    ("fpi", "nifty", "+", 2, "Foreign buying lifts large caps."),
    ("dii", "nifty", "+", 2, "Domestic SIP money cushions sell-offs."),
    ("fpi", "usdinr", "-", 2, "Foreign inflows strengthen the rupee."),
    ("dxy", "fpi", "-", 2, "A strong dollar pulls money out of emerging markets."),
    ("us10y", "fpi", "-", 2, "Higher US yields make India relatively less attractive."),
    ("risk_appetite", "fpi", "+", 2, "Foreign money flows to EMs when risk appetite is high."),
    ("em_equities", "fpi", "+", 1, "Global EM fund flows include India."),
    ("savings_shift", "dii", "+", 3, "Household money into SIPs and insurance."),
    ("nifty", "india_vix", "-", 3, "Volatility rises when the market falls."),
    ("india_vix", "nifty", "-", 1, "Fear spikes coincide with sell-offs."),
    ("trade_deficit", "usdinr", "+", 2, "A wider deficit weakens the rupee."),
    ("usdinr", "india_cpi", "+", 1, "Imports cost more in rupees."),
    ("housing", "construction_cost", "+", 1, "Busy construction tightens material markets."),
    ("construction_cost", "home_affordability", "-", 2, "Higher building costs raise home prices."),
    ("india_10y", "home_affordability", "-", 2, "Higher rates raise EMIs."),
    ("home_affordability", "housing", "+", 2, "Affordability drives sales."),
    ("power_demand", "electricity_tariff", "+", 1, "Peak demand raises exchange power prices."),
    ("tariffs", "india_growth", "-", 1, "Export-oriented sectors lose orders."),
    ("credit_growth", "bank_asset_quality", "~", 1, "Fast growth can store up future bad loans."),
    ("india_growth", "bank_asset_quality", "+", 2, "A healthy economy keeps borrowers paying."),
    ("india_growth", "jobs_wages", "+", 2, "Growth creates jobs."),
    ("auto_demand", "india_growth", "+", 1, "Autos are ~7% of GDP."),
    ("festive", "auto_demand", "+", 2, "Festive months bring peak sales."),
    ("festive", "jewellery_demand", "+", 2, "Weddings and Dhanteras lift gold buying."),
    ("rural_demand", "auto_demand", "+", 2, "Two-wheelers and tractors depend on rural incomes."),
    ("credit_growth", "auto_demand", "+", 2, "Most vehicles are bought on loans."),
    ("fuel_prices", "vehicle_cost", "+", 2, "Running costs."),
    ("vehicle_cost", "auto_demand", "-", 2, "Higher prices deter buyers."),
    ("digital_adoption", "jobs_wages", "+", 1, "Tech hiring."),
    ("us_growth", "digital_adoption", "+", 2, "US clients drive global IT budgets."),
]

# ----------------- Industry templates -----------------
def T(name, sector, drivers, drives):
    return dict(name=name, sector_index=sector, drivers=drivers, drives=drives)

TEMPLATES = {
    "paints": T("Paints", "sec_fmcg", [
        ("brent", "-", 3, "Crude derivatives (solvents, monomers, binders) are the largest raw-material bucket; margins move with a 1–2 quarter lag."),
        ("tio2", "-", 2, "Titanium dioxide is the main pigment cost."),
        ("usdinr", "-", 2, "Many inputs are imported or import-priced."),
        ("housing", "+", 3, "New homes and repainting drive decorative volumes."),
        ("monsoon", "+", 1, "Rural repainting follows farm incomes; heavy rains delay painting."),
        ("regulation", "-", 1, "New competition (Birla Opus, JSW Paints) is pressuring share and pricing."),
        ("india_10y", "-", 1, "Higher rates cool housing and lower valuations of long-duration consumer stocks."),
    ], [
        ("construction_cost", "+", 1, "Paint price hikes add to finishing costs for developers and households."),
        ("india_cpi", "+", 1, "Household goods component of CPI."),
    ]),
    "cement": T("Cement", "sec_realty", [
        ("housing", "+", 3, "Housing is ~60% of cement demand."),
        ("govt_capex", "+", 3, "Roads, rail and urban infrastructure."),
        ("coal", "-", 2, "Coal and pet coke fuel the kilns."),
        ("brent", "-", 2, "Diesel freight is a major cost."),
        ("monsoon", "-", 1, "Heavy rains halt construction in Jul–Sep."),
    ], [
        ("construction_cost", "+", 2, "Cement price hikes raise building costs."),
        ("infra_buildout", "+", 1, "Capacity enables projects."),
    ]),
    "steel": T("Steel", "sec_metal", [
        ("steel", "+", 3, "Realisations follow global HRC prices."),
        ("iron_ore", "-", 2, "Main raw material (partly captive)."),
        ("coal", "-", 3, "Imported coking coal is the biggest cost."),
        ("china_growth", "+", 2, "Chinese exports set the global price floor."),
        ("govt_capex", "+", 2, "Infrastructure demand."),
        ("auto_demand", "+", 1, "Flat steel for vehicles."),
        ("regulation", "+", 1, "Safeguard duties on imports protect prices."),
    ], [
        ("construction_cost", "+", 2, "Rebar and structural steel prices."),
        ("vehicle_cost", "+", 1, "Body steel for autos and white goods."),
    ]),
    "aluminium": T("Aluminium", "sec_metal", [
        ("aluminium", "+", 3, "Realisations track LME aluminium."),
        ("coal", "-", 2, "Captive power for smelting."),
        ("usdinr", "+", 1, "Dollar-linked pricing; weaker rupee helps."),
        ("china_growth", "+", 2, "China sets global supply-demand."),
    ], [("packaging_cost", "+", 1, "Cans and foil."), ("power_supply", "~", 1, "Grid conductors.")]),
    "zinc_silver": T("Zinc, lead & silver", "sec_metal", [
        ("zinc", "+", 3, "Realisations track LME zinc."),
        ("silver", "+", 2, "Silver is a large profit contributor."),
        ("usdinr", "+", 1, "Dollar-priced output."),
    ], []),
    "copper": T("Copper", "sec_metal", [("copper", "+", 3, "Refining margins and inventory gains."), ("power_demand", "+", 1, "Wire and cable demand.")], [("construction_cost", "+", 1, "Wiring costs.")]),
    "mining": T("Mining (coal, iron ore)", "sec_metal", [
        ("coal", "+", 3, "Price of e-auction coal and iron ore."), ("power_demand", "+", 2, "Thermal plants buy most coal."),
        ("iron_ore", "+", 2, "Iron ore realisations."),
    ], [("electricity_tariff", "+", 1, "Coal costs feed tariffs."), ("steel", "+", 1, "Ore costs feed steel.")]),
    "oil_upstream": T("Oil & gas producers", "sec_energy", [
        ("brent", "+", 3, "Realisations rise with crude."), ("natgas", "+", 2, "Gas price formula (APM) is crude-linked."),
        ("regulation", "-", 2, "Windfall taxes and pricing caps."), ("usdinr", "+", 1, "Dollar-priced output."),
    ], [("fiscal", "+", 1, "Large dividend payer to the government.")]),
    "oil_marketing": T("Oil refining & marketing", "sec_energy", [
        ("brent", "-", 3, "If pump prices are held, cheaper crude means bigger marketing margins."),
        ("fuel_prices", "+", 2, "Retail price changes."), ("regulation", "-", 2, "Government asks them to absorb LPG losses."),
        ("usdinr", "-", 1, "Crude is bought in dollars."),
    ], [("fuel_prices", "+", 2, "They set pump prices."), ("fiscal", "~", 1, "LPG under-recoveries.")]),
    "refining_petchem": T("Refining & petrochemicals (diversified)", "sec_energy", [
        ("brent", "~", 2, "Refining margins (cracks) matter more than crude level."), ("china_growth", "+", 1, "Petchem demand."),
        ("telecom_tariffs", "+", 1, "Jio earnings for conglomerates."), ("urban_demand", "+", 1, "Retail business."),
    ], [("fuel_prices", "+", 1, "Major fuel supplier."), ("packaging_cost", "+", 1, "Polymers for packaging.")]),
    "gas_distribution": T("Gas transmission & city gas", "sec_energy", [
        ("natgas", "-", 3, "Input cost for city gas; volume risk for transmission."), ("regulation", "-", 2, "APM gas allocation and tariff orders."),
        ("brent", "+", 1, "CNG competitiveness versus petrol/diesel."),
    ], [("transport_cost", "-", 1, "CNG fleets.")]),
    "power_utility": T("Power generation & utilities", "sec_energy", [
        ("power_demand", "+", 3, "Plant load factors and merchant prices."), ("coal", "-", 2, "Fuel cost (mostly passed through)."),
        ("india_10y", "-", 2, "Capital-heavy; regulated returns."), ("regulation", "~", 2, "Tariff orders."),
    ], [("electricity_tariff", "+", 2, "They supply the grid."), ("power_supply", "+", 2, "Capacity additions.")]),
    "renewables": T("Renewables & green energy", "sec_energy", [
        ("india_10y", "-", 3, "Long-duration projects financed with debt."), ("pli", "+", 2, "Solar module incentives."),
        ("power_demand", "+", 2, "Demand growth absorbs new capacity."), ("chemicals_china", "~", 2, "Module prices from China."),
    ], [("power_supply", "+", 2, "New capacity."), ("electricity_tariff", "-", 1, "Low-cost solar tariffs.")]),
    "power_equipment": T("Power & electrical equipment", "sec_energy", [
        ("govt_capex", "+", 3, "Grid, transmission and generation orders."), ("power_demand", "+", 3, "Utilities add capacity."),
        ("copper", "-", 2, "Copper and steel are key inputs."), ("ai_capex", "+", 1, "Data-centre power gear."),
    ], [("power_supply", "+", 2, "Transformers, switchgear, turbines.")]),
    "cables_wires": T("Cables & wires", None, [
        ("copper", "-", 3, "Copper is ~70% of cost (passed on with a lag)."), ("aluminium", "-", 1, "Power cables."),
        ("housing", "+", 2, "Building wires."), ("govt_capex", "+", 2, "Power and telecom cables."),
    ], [("construction_cost", "+", 1, "Wiring costs.")]),
    "pipes": T("Plastic pipes & building products", None, [
        ("brent", "-", 2, "PVC resin is crude/ethylene-linked."), ("housing", "+", 3, "Plumbing demand."), ("rural_demand", "+", 1, "Agri pipes."),
    ], [("construction_cost", "+", 1, "Plumbing costs.")]),
    "private_bank": T("Private banks", "sec_bank", [
        ("credit_growth", "+", 3, "Loan growth drives profits."), ("rbi", "~", 2, "Rate cuts compress margins short-term but lift growth."),
        ("bank_asset_quality", "+", 3, "Lower bad loans mean lower provisions."), ("fpi", "+", 2, "Banks are FPIs' largest holding."),
        ("india_growth", "+", 2, "Economic health."),
    ], [("credit_growth", "+", 2, "They supply credit."), ("nifty", "+", 3, "Financials are ~35% of the Nifty."), ("home_affordability", "~", 1, "Home-loan pricing.")]),
    "psu_bank": T("Public-sector banks", "sec_bank", [
        ("credit_growth", "+", 2, "Loan growth."), ("india_10y", "-", 2, "Large bond portfolios lose value when yields rise."),
        ("bank_asset_quality", "+", 3, "Bad-loan cycles hit PSU banks hardest."), ("regulation", "~", 1, "Government ownership and directives."),
    ], [("credit_growth", "+", 2, "Biggest lenders to infrastructure and agriculture."), ("govt_capex", "+", 1, "Fund infrastructure projects.")]),
    "nbfc": T("NBFCs & consumer finance", "sec_bank", [
        ("india_10y", "-", 3, "They borrow from markets; costs follow yields."), ("rbi", "-", 2, "Funding costs and risk-weight rules."),
        ("urban_demand", "+", 2, "Consumer loans."), ("bank_asset_quality", "+", 2, "Credit costs."),
    ], [("consumer_wallet", "+", 1, "Consumer credit availability."), ("auto_demand", "+", 1, "Vehicle loans.")]),
    "housing_finance": T("Housing finance", "sec_bank", [
        ("india_10y", "-", 3, "Funding cost and loan demand both depend on rates."), ("housing", "+", 3, "Mortgage demand."),
    ], [("home_affordability", "~", 2, "Mortgage rates.")]),
    "gold_finance": T("Gold-loan companies", "sec_bank", [
        ("gold", "+", 3, "Higher gold prices raise loan sizes and collateral."), ("regulation", "-", 2, "RBI loan-to-value rules."),
        ("rural_demand", "+", 1, "Borrowers are mostly rural and MSME."),
    ], [("rural_demand", "+", 1, "Quick credit for households.")]),
    "insurance": T("Insurance", "sec_bank", [
        ("india_10y", "~", 2, "Investment income vs. guarantee costs."), ("nifty", "+", 2, "Market-linked products and float."),
        ("regulation", "~", 2, "IRDAI rules on commissions and products."), ("savings_shift", "+", 2, "Household financial savings."),
    ], [("dii", "+", 2, "Large domestic institutional investors.")]),
    "capital_markets": T("AMCs, brokers & exchanges", None, [
        ("nifty", "+", 3, "Fees rise with market levels and activity."), ("savings_shift", "+", 3, "SIP and demat growth."),
        ("regulation", "-", 2, "SEBI curbs on F&O and fees."), ("india_vix", "+", 1, "Volatility lifts trading volumes."),
    ], [("dii", "+", 2, "They channel SIP money.")]),
    "it_services": T("IT services", "sec_it", [
        ("us_growth", "+", 3, "~60% of revenue comes from US clients."), ("usdinr", "+", 3, "A weaker rupee lifts rupee revenue and margins."),
        ("digital_adoption", "+", 2, "Client tech budgets."), ("ai_capex", "~", 2, "AI creates new work but can shrink some services."),
        ("us_tech", "+", 1, "Sentiment link with US tech."), ("tariffs", "-", 1, "Visa and services-tax risks."),
    ], [("jobs_wages", "+", 2, "Among India's largest private employers."), ("urban_demand", "+", 1, "Salaries fund urban spending (Bengaluru, Pune, Hyderabad)."), ("usdinr", "-", 1, "Services exports bring dollars in.")]),
    "pharma": T("Pharmaceuticals", "sec_pharma", [
        ("usdinr", "+", 2, "US generics exports earn dollars."), ("regulation", "~", 3, "USFDA inspections and US drug pricing."),
        ("chemicals_china", "-", 2, "Many raw materials (APIs, KSMs) come from China."), ("tariffs", "-", 1, "Possible US tariffs on pharma."),
    ], [("healthcare_cost", "+", 1, "Medicine prices.")]),
    "hospitals": T("Hospitals & diagnostics", "sec_pharma", [
        ("urban_demand", "+", 2, "Insured, paying patients."), ("regulation", "-", 1, "Price caps."), ("jobs_wages", "-", 1, "Doctor and nurse costs."),
    ], [("healthcare_cost", "+", 2, "Treatment costs.")]),
    "fmcg_staples": T("FMCG staples (food, home & personal care)", "sec_fmcg", [
        ("palm_oil", "-", 3, "Soaps and foods; India imports most edible oil."), ("brent", "-", 2, "Packaging, detergents and freight."),
        ("rural_demand", "+", 3, "Rural is ~35–40% of FMCG sales."), ("india_cpi", "~", 2, "Pricing power vs. volume squeeze."),
        ("wheat", "-", 1, "Biscuits and foods."), ("gst", "-", 1, "Rate changes."),
    ], [("india_cpi", "+", 1, "Consumer price inflation."), ("packaging_cost", "~", 1, "Large packaging buyers.")]),
    "tobacco": T("Cigarettes & diversified FMCG", "sec_fmcg", [
        ("gst", "-", 3, "Excise and GST hikes on cigarettes."), ("urban_demand", "+", 1, "Hotels and FMCG arms."), ("farm_income", "~", 1, "Leaf tobacco and agri exports."),
    ], [("fiscal", "+", 1, "Large tax payer.")]),
    "beverages_alcohol": T("Beverages & alcohol", "sec_fmcg", [
        ("urban_demand", "+", 2, "Premium spending."), ("regulation", "-", 2, "State excise policies."), ("sugar", "-", 1, "Input cost."), ("packaging_cost", "-", 1, "Glass bottles and cans."),
    ], []),
    "sugar_ethanol": T("Sugar & ethanol", None, [
        ("sugar", "+", 3, "Mill realisations."), ("monsoon", "+", 2, "Cane output."), ("regulation", "~", 3, "Export quotas, ethanol pricing, cane prices."), ("brent", "+", 1, "Ethanol blending economics."),
    ], [("food_inflation", "+", 1, "Sugar prices in CPI."), ("fuel_prices", "-", 1, "Ethanol blending.")]),
    "agrochem": T("Agrochemicals", None, [
        ("monsoon", "+", 3, "Sowing drives demand for crop protection."), ("chemicals_china", "-", 2, "Chinese technical prices and dumping."), ("farm_income", "+", 2, "Farmer spending."),
    ], [("farm_income", "+", 1, "Crop yields.")]),
    "fertiliser": T("Fertilisers", None, [
        ("natgas", "-", 2, "Urea feedstock (subsidy-protected)."), ("fertiliser_inputs", "-", 2, "Phosphate and ammonia imports."),
        ("regulation", "~", 3, "Government subsidy formula sets margins."), ("monsoon", "+", 2, "Application volumes."),
    ], [("fiscal", "+", 2, "Fertiliser subsidies are a large budget item."), ("farm_income", "+", 1, "Farm input availability.")]),
    "specialty_chem": T("Specialty chemicals", None, [
        ("chemicals_china", "-", 3, "Chinese pricing and capacity."), ("brent", "-", 2, "Petrochemical feedstocks."), ("usdinr", "+", 1, "Export-heavy."), ("tariffs", "~", 1, "US tariffs on China can shift orders to India."),
    ], [("packaging_cost", "+", 1, "Polymer and additive costs downstream.")]),
    "auto_pv": T("Passenger vehicles", "sec_auto", [
        ("urban_demand", "+", 3, "Car buyers are mostly urban."), ("credit_growth", "+", 2, "~80% bought on loans."), ("steel", "-", 2, "Steel, aluminium and plastics."),
        ("fuel_prices", "-", 1, "Running costs shift demand to CNG/EVs."), ("festive", "+", 2, "Seasonal peak."), ("gst", "-", 2, "GST/cess changes."),
    ], [("steel", "+", 1, "Large steel buyer."), ("jobs_wages", "+", 1, "Dealers and component makers."), ("vehicle_cost", "+", 2, "Vehicle prices.")]),
    "auto_2w": T("Two-wheelers & tractors", "sec_auto", [
        ("rural_demand", "+", 3, "Rural buyers dominate."), ("monsoon", "+", 2, "Farm incomes; tractors especially."), ("brent", "-", 1, "Fuel costs."),
        ("steel", "-", 1, "Input costs."), ("festive", "+", 2, "Seasonal peak."), ("regulation", "~", 1, "EV subsidies and emission norms."),
    ], [("vehicle_cost", "+", 1, "Vehicle prices.")]),
    "auto_cv": T("Commercial vehicles", "sec_auto", [
        ("govt_capex", "+", 3, "Infrastructure and mining trucks."), ("india_growth", "+", 2, "Freight demand."), ("brent", "-", 2, "Fleet operator profitability."), ("india_10y", "-", 1, "Truck financing."),
    ], [("transport_cost", "~", 1, "Fleet capacity.")]),
    "auto_ancillary": T("Auto components", "sec_auto", [
        ("auto_demand", "+", 3, "OEM production volumes."), ("steel", "-", 2, "Steel and aluminium costs."), ("usdinr", "+", 1, "Exporters gain."), ("tariffs", "-", 1, "US/EU tariffs on parts."),
    ], [("vehicle_cost", "+", 1, "Component prices.")]),
    "tyres": T("Tyres", "sec_auto", [
        ("rubber", "-", 3, "Natural rubber is the largest input."), ("brent", "-", 2, "Synthetic rubber, carbon black and nylon are crude-derived."),
        ("auto_demand", "+", 2, "Original-equipment demand."), ("transport_cost", "~", 1, "Replacement demand tracks freight activity."),
    ], [("vehicle_cost", "+", 1, "Tyre prices.")]),
    "airlines": T("Airlines", None, [
        ("brent", "-", 3, "Jet fuel is ~35–40% of costs."), ("usdinr", "-", 2, "Leases and fuel are dollar-linked."), ("travel_demand", "+", 3, "Passenger traffic and fares."),
    ], [("travel_demand", "+", 1, "Capacity and fares.")]),
    "hotels_travel": T("Hotels & travel", None, [
        ("travel_demand", "+", 3, "Occupancy and room rates."), ("urban_demand", "+", 2, "Leisure and business travel."), ("festive", "+", 1, "Wedding season."),
    ], [("travel_demand", "+", 1, "Room supply.")]),
    "retail_qsr": T("Retail, fashion & restaurants", None, [
        ("urban_demand", "+", 3, "Discretionary spending."), ("consumer_wallet", "+", 2, "Spare income."), ("cotton", "-", 1, "Apparel costs."), ("palm_oil", "-", 1, "Food costs for restaurants."),
    ], [("jobs_wages", "+", 1, "Large retail employers.")]),
    "jewellery": T("Jewellery & watches", None, [
        ("gold", "~", 3, "Higher prices lift inventory gains and ticket sizes but cut grams sold."), ("festive", "+", 3, "Wedding and festive demand."),
        ("urban_demand", "+", 2, "Discretionary spending."), ("regulation", "~", 1, "Import duty on gold."),
    ], [("jewellery_demand", "+", 2, "Main organised retailers.")]),
    "consumer_durables": T("Consumer durables & electronics", None, [
        ("urban_demand", "+", 3, "ACs, TVs, appliances."), ("copper", "-", 2, "Copper, aluminium, steel inputs."), ("usdinr", "-", 2, "Imported components."),
        ("power_demand", "+", 1, "Hot summers lift AC/fan sales."), ("pli", "+", 1, "Electronics incentives."),
    ], [("consumer_wallet", "-", 1, "Big-ticket purchases.")]),
    "realty": T("Real-estate developers", "sec_realty", [
        ("india_10y", "-", 3, "Home-loan rates and developer funding."), ("home_affordability", "+", 3, "Sales velocity."), ("construction_cost", "-", 2, "Margins."),
        ("jobs_wages", "+", 2, "Office leasing and housing demand."),
    ], [("housing", "+", 3, "They drive launches."), ("construction_cost", "+", 1, "Material demand.")]),
    "construction_epc": T("Construction & engineering (EPC)", None, [
        ("govt_capex", "+", 3, "Order inflows."), ("steel", "-", 2, "Steel and cement costs (often with escalation clauses)."), ("india_10y", "-", 1, "Working-capital costs."),
    ], [("infra_buildout", "+", 3, "They build it."), ("jobs_wages", "+", 1, "Large employers.")]),
    "capital_goods": T("Capital goods & industrials", None, [
        ("govt_capex", "+", 3, "Public investment orders."), ("india_growth", "+", 2, "Private capex cycle."), ("steel", "-", 1, "Inputs."), ("ai_capex", "+", 1, "Data-centre equipment."),
    ], [("infra_buildout", "+", 2, "Equipment for projects.")]),
    "defence": T("Defence & aerospace", None, [
        ("govt_capex", "+", 3, "Defence budget and indigenisation orders."), ("geopolitics", "+", 2, "Conflicts raise defence spending and export interest."),
    ], [("infra_buildout", "+", 1, "Strategic capability.")]),
    "railways": T("Railways & rail equipment", None, [("govt_capex", "+", 3, "Railway budget is the main driver."), ("steel", "-", 1, "Wagon and coach inputs.")], [("transport_cost", "-", 1, "Cheaper freight capacity."), ("infra_buildout", "+", 2, "Rail network.")]),
    "logistics_ports": T("Logistics, ports & shipping", None, [
        ("india_growth", "+", 2, "Freight volumes."), ("brent", "-", 1, "Fuel costs."), ("tariffs", "-", 1, "Trade volumes."), ("geopolitics", "~", 2, "Red Sea disruptions raise freight rates."),
    ], [("transport_cost", "~", 2, "Freight pricing.")]),
    "telecom": T("Telecom", None, [
        ("telecom_tariffs", "+", 3, "Tariff hikes lift revenue per user."), ("regulation", "~", 2, "Spectrum costs and dues."), ("india_10y", "-", 1, "Heavy debt."),
    ], [("telecom_tariffs", "+", 3, "They set prices."), ("digital_adoption", "+", 1, "Network access.")]),
    "media": T("Media & entertainment", None, [("urban_demand", "+", 2, "Ad spending and subscriptions."), ("india_growth", "+", 1, "Ad budgets follow the economy.")], []),
    "textiles": T("Textiles & apparel", None, [
        ("cotton", "-", 3, "Main raw material."), ("tariffs", "-", 2, "US is the largest export market."), ("usdinr", "+", 1, "Exporters gain from a weaker rupee."),
    ], [("india_cpi", "+", 1, "Clothing prices.")]),
    "diversified": T("Diversified conglomerates", None, [("india_growth", "+", 2, "Spread across the economy."), ("govt_capex", "+", 1, "Infrastructure arms.")], []),
    "default": T("Other", None, [("nifty", "+", 2, "Overall market direction."), ("india_growth", "+", 1, "Economic growth.")], []),
}

# Broad NSE 'Industry' (Nifty constituent files) -> default template when a stock is not mapped below
BROAD = {
    "Financial Services": "private_bank", "Information Technology": "it_services", "Healthcare": "pharma",
    "Fast Moving Consumer Goods": "fmcg_staples", "Automobile and Auto Components": "auto_ancillary",
    "Capital Goods": "capital_goods", "Chemicals": "specialty_chem", "Consumer Durables": "consumer_durables",
    "Consumer Services": "retail_qsr", "Construction": "construction_epc", "Construction Materials": "cement",
    "Diversified": "diversified", "Forest Materials": "default", "Media Entertainment & Publication": "media",
    "Media, Entertainment & Publication": "media", "Metals & Mining": "steel", "Oil Gas & Consumable Fuels": "refining_petchem",
    "Oil, Gas & Consumable Fuels": "refining_petchem", "Power": "power_utility", "Realty": "realty", "Services": "logistics_ports",
    "Telecommunication": "telecom", "Textiles": "textiles", "Utilities": "power_utility",
}

# Curated stock -> template (NSE symbol). Anything not here uses BROAD by its NSE industry.
STOCKS = {}
def _m(t, syms):
    for s in syms.split():
        STOCKS[s] = t

_m("paints", "ASIANPAINT BERGEPAINT KANSAINER INDIGOPNTS AKZOINDIA")
_m("cement", "ULTRACEMCO SHREECEM AMBUJACEM ACC DALBHARAT JKCEMENT RAMCOCEM INDIACEM NUVOCO BIRLACORPN JKLAKSHMI HEIDELBERG STARCEMENT ORIENTCEM")
_m("steel", "TATASTEEL JSWSTEEL JINDALSTEL SAIL JSL APLAPOLLO RATNAMANI SHYAMMETL GPIL WELCORP")
_m("aluminium", "HINDALCO NATIONALUM")
_m("zinc_silver", "HINDZINC VEDL")
_m("copper", "HINDCOPPER")
_m("mining", "COALINDIA NMDC MOIL GMDCLTD")
_m("oil_upstream", "ONGC OIL")
_m("oil_marketing", "IOC BPCL HINDPETRO MRPL CHENNPETRO")
_m("refining_petchem", "RELIANCE")
_m("gas_distribution", "GAIL IGL MGL GUJGASLTD GSPL PETRONET ATGL")
_m("power_utility", "NTPC POWERGRID TATAPOWER NHPC SJVN TORNTPOWER CESC JSWENERGY ADANIPOWER NLCINDIA RPOWER IEX")
_m("renewables", "ADANIGREEN SUZLON INOXWIND WAAREEENER PREMIERENE NTPCGREEN BORORENEW IREDA")
_m("power_equipment", "SIEMENS ABB BHEL CGPOWER HITACHIENERGY GEVERNOVA TRIL APARINDS")
_m("cables_wires", "POLYCAB KEI FINCABLES HAVELLS RRKABEL")
_m("pipes", "ASTRAL SUPREMEIND PRINCEPIPE FINPIPE CERA KAJARIACER CENTURYPLY GREENPANEL PIDILITIND")
_m("private_bank", "HDFCBANK ICICIBANK KOTAKBANK AXISBANK INDUSINDBK IDFCFIRSTB FEDERALBNK BANDHANBNK RBLBANK AUBANK YESBANK CUB KARURVYSYA DCBBANK EQUITASBNK UJJIVANSFB")
_m("psu_bank", "SBIN BANKBARODA PNB CANBK UNIONBANK INDIANB BANKINDIA CENTRALBK IOB MAHABANK UCOBANK")
_m("nbfc", "BAJFINANCE BAJAJFINSV SHRIRAMFIN CHOLAFIN MUTHOOTCAP SUNDARMFIN POONAWALLA M&MFIN LTF ABCAPITAL PFC RECLTD IRFC HUDCO JIOFIN TATAINVEST CREDITACC")
_m("housing_finance", "LICHSGFIN PNBHOUSING CANFINHOME AAVAS HOMEFIRST APTUS BAJAJHFL")
_m("gold_finance", "MUTHOOTFIN MANAPPURAM")
_m("insurance", "LICI SBILIFE HDFCLIFE ICICIPRULI ICICIGI NIACL GICRE STARHEALTH MAXFIN")
_m("capital_markets", "BSE MCX CDSL CAMS KFINTECH HDFCAMC NAM-INDIA UTIAMC ANGELONE MOTILALOFS 360ONE NUVAMA IIFL")
_m("it_services", "TCS INFY HCLTECH WIPRO TECHM LTIM MPHASIS PERSISTENT COFORGE OFSS LTTS KPITTECH TATAELXSI CYIENT SONACOMS ZENSARTECH BSOFT SASKEN TATATECH NEWGEN INTELLECT")
_m("pharma", "SUNPHARMA DRREDDY CIPLA DIVISLAB LUPIN AUROPHARMA ZYDUSLIFE TORNTPHARM ALKEM GLENMARK BIOCON IPCALAB ABBOTINDIA GLAXO NATCOPHARM LAURUSLABS GRANULES AJANTPHARM MANKIND JBCHEPHARM PFIZER")
_m("hospitals", "APOLLOHOSP MAXHEALTH FORTIS NH LALPATHLAB METROPOLIS GLOBAL MEDANTA KIMS ASTERDM")
_m("fmcg_staples", "HINDUNILVR NESTLEIND BRITANNIA DABUR MARICO GODREJCP COLPAL TATACONSUM EMAMILTD JYOTHYLAB BAJAJCON PATANJALI AWL GILLETTE PGHH HONASA")
_m("tobacco", "ITC GODFRYPHLP VSTIND")
_m("beverages_alcohol", "VBL UNITDSPR RADICO UBL")
_m("sugar_ethanol", "BALRAMCHIN TRIVENI EIDPARRY RENUKA")
_m("agrochem", "UPL PIIND BAYERCROP DHANUKA RALLIS SUMICHEM")
_m("fertiliser", "CHAMBLFERT COROMANDEL RCF FACT GSFC DEEPAKFERT GNFC")
_m("specialty_chem", "SRF DEEPAKNTR AARTIIND NAVINFLUOR ATUL VINATIORGA CLEAN FINEORG GUJFLUORO TATACHEM ALKYLAMINE BALAMINES SOLARINDS LINDEINDIA")
_m("auto_pv", "MARUTI M&M TATAMOTORS HYUNDAI")
_m("auto_2w", "BAJAJ-AUTO HEROMOTOCO EICHERMOT TVSMOTOR ESCORTS OLAELEC")
_m("auto_cv", "ASHOKLEY FORCEMOT")
_m("auto_ancillary", "BOSCHLTD MOTHERSON BHARATFORG UNOMINDA SONACOMS EXIDEIND ARE&M SCHAEFFLER TIINDIA SUNDRMFAST ENDURANCE MINDACORP ZFCVINDIA")
_m("tyres", "MRF APOLLOTYRE BALKRISIND CEATLTD JKTYRE")
_m("airlines", "INDIGO SPICEJET")
_m("hotels_travel", "INDHOTEL EIHOTEL LEMONTREE CHALET IRCTC THOMASCOOK EASEMYTRIP")
_m("retail_qsr", "DMART TRENT ABFRL PAGEIND JUBLFOOD DEVYANI WESTLIFE SAPPHIRE VMART NYKAA ZOMATO ETERNAL SWIGGY BATAINDIA RELAXO METROBRAND")
_m("jewellery", "TITAN KALYANKJIL SENCO RAJESHEXPO PCJEWELLER")
_m("consumer_durables", "VOLTAS BLUESTARCO WHIRLPOOL CROMPTON DIXON AMBER KAYNES ORIENTELEC BAJAJELEC VGUARD SYRMA TTKPRESTIG")
_m("realty", "DLF GODREJPROP OBEROIRLTY PRESTIGE PHOENIXLTD LODHA BRIGADE SOBHA MAHLIFE SUNTECK")
_m("construction_epc", "LT NCC KEC KPIL IRCON RVNL NBCC PNCINFRA HGINFRA ENGINERSIN")
_m("capital_goods", "CUMMINSIND THERMAX ELGIEQUIP GRINDWELL AIAENG KIRLOSENG TIMKEN SKFINDIA HONAUT CARBORUNIV")
_m("defence", "HAL BEL BDL MAZDOCK COCHINSHIP GRSE DATAPATTNS ASTRAMICRO SOLARINDS")
_m("railways", "TITAGARH TEXRAIL JWL RAILTEL CONCOR")
_m("logistics_ports", "ADANIPORTS GMRAIRPORT BLUEDART DELHIVERY SCI GESHIP ALLCARGO TCIEXP")
_m("telecom", "BHARTIARTL IDEA INDUSTOWER TATACOMM HFCL ROUTE")
_m("media", "ZEEL SUNTV PVRINOX NAZARA SAREGAMA NETWORK18")
_m("textiles", "KPRMILL TRIDENT WELSPUNLIV RAYMOND VTL ARVIND GOKEX")
_m("diversified", "ADANIENT GRASIM 3MINDIA DCMSHRIRAM GODREJIND")

# Index-tracking ETFs listed in India (for "who must hold it")
INDEX_ETFS = {
    "nifty50": "Nifty 50 ETFs & index funds (e.g. NIFTYBEES)", "niftynext50": "Nifty Next 50 ETFs (e.g. JUNIORBEES)",
    "niftybank": "Bank ETFs (e.g. BANKBEES)", "niftyit": "IT ETFs (e.g. ITBEES)", "niftypsubank": "PSU bank ETFs (e.g. PSUBNKBEES)",
    "niftymidcap150": "Midcap 150 ETFs (e.g. MID150BEES)", "nifty100": "Nifty 100 ETFs", "niftypharma": "Pharma ETFs (e.g. PHARMABEES)",
    "niftyfmcg": "FMCG ETFs", "niftyauto": "Auto ETFs", "niftymetal": "Metal ETFs", "niftyenergy": "Energy ETFs",
}

# Index constituent files on niftyindices.com: key -> (display name, csv file)
INDICES = {
    "nifty50": ("Nifty 50", "ind_nifty50list.csv"), "niftynext50": ("Nifty Next 50", "ind_niftynext50list.csv"),
    "nifty100": ("Nifty 100", "ind_nifty100list.csv"), "nifty500": ("Nifty 500", "ind_nifty500list.csv"),
    "niftymidcap150": ("Nifty Midcap 150", "ind_niftymidcap150list.csv"), "niftysmallcap250": ("Nifty Smallcap 250", "ind_niftysmallcap250list.csv"),
    "niftybank": ("Nifty Bank", "ind_niftybanklist.csv"), "niftyit": ("Nifty IT", "ind_niftyitlist.csv"),
    "niftypharma": ("Nifty Pharma", "ind_niftypharmalist.csv"), "niftyfmcg": ("Nifty FMCG", "ind_niftyfmcglist.csv"),
    "niftyauto": ("Nifty Auto", "ind_niftyautolist.csv"), "niftymetal": ("Nifty Metal", "ind_niftymetallist.csv"),
    "niftyenergy": ("Nifty Energy", "ind_niftyenergylist.csv"), "niftyrealty": ("Nifty Realty", "ind_niftyrealtylist.csv"),
    "niftypsubank": ("Nifty PSU Bank", "ind_niftypsubanklist.csv"), "niftyprivatebank": ("Nifty Private Bank", "ind_nifty_privatebanklist.csv"),
    "niftyfinance": ("Nifty Financial Services", "ind_niftyfinancelist.csv"), "niftyconsumerdurables": ("Nifty Consumer Durables", "ind_niftyconsumerdurableslist.csv"),
    "niftyoilgas": ("Nifty Oil & Gas", "ind_niftyoilgaslist.csv"), "niftyhealthcare": ("Nifty Healthcare", "ind_niftyhealthcarelist.csv"),
    "niftymedia": ("Nifty Media", "ind_niftymedialist.csv"),
}
UNIVERSE_FILE = "ind_niftytotalmarket_list.csv"

# Factors used for measured sensitivities and the shock simulator.
# key: (label, yahoo ticker, kind) kind 'ret' = % change, 'yld' = change in yield (percentage points)
FACTORS = {
    "nifty": ("Nifty 50", "^NSEI", "ret"),
    "brent": ("Crude oil (Brent)", "BZ=F", "ret"),
    "usdinr": ("USD / INR", "INR=X", "ret"),
    "gold": ("Gold", "GC=F", "ret"),
    "copper": ("Copper", "HG=F", "ret"),
    "natgas": ("Natural gas", "NG=F", "ret"),
    "aluminium": ("Aluminium", "ALI=F", "ret"),
    "us10y": ("US 10Y yield", "^TNX", "yld"),
    "us_tech": ("Nasdaq 100", "^NDX", "ret"),
    "dxy": ("US dollar index", "DX-Y.NYB", "ret"),
    "india_bonds": ("India gilt prices", "LTGILTBEES.NS", "ret"),
    "sugar": ("Sugar", "SB=F", "ret"),
    "cotton": ("Cotton", "CT=F", "ret"),
}
