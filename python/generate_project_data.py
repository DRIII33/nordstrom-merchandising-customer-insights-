"""
Project AURA - Phase 1: synthetic omnichannel retail data with embedded ground truth.
Outputs (data/): raw_transactions.csv, raw_customers.csv, raw_brands.csv,
raw_promo_calendar.csv, raw_inventory_monthly.csv, ground_truth_customers.csv,
ground_truth_parameters.json  (ground truth is NEVER loaded to BigQuery).
"""
import json
import os
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
OUT = "data"
os.makedirs(OUT, exist_ok=True)

N_ORDERS, N_CUSTOMERS = 50_000, 10_000
START, END = "2025-01-01", "2026-09-30"
CHANNELS = ["Nordstrom Stores", "Nordstrom.com", "Rack Stores", "NordstromRack.com"]
FULL_LINE, RACK = CHANNELS[:2], CHANNELS[2:]
CHANNEL_SHARE = np.array([0.35, 0.30, 0.20, 0.15])
CATEGORIES = ["Designer Apparel", "Contemporary Shoes", "Handbags & Accessories",
              "Beauty & Fragrance", "Home & Gifts"]
CAT_SHARE = [0.25, 0.25, 0.20, 0.20, 0.10]

# ---- ground-truth parameters (what the analysis should recover) ----------
TRUE_ELASTICITY = {"Designer Apparel": 1.1, "Contemporary Shoes": 1.5,
                   "Handbags & Accessories": 0.7, "Beauty & Fragrance": 1.9,
                   "Home & Gifts": 1.3}
TIER_ELASTICITY_MULT = {"Luxury": 0.7, "Premium": 1.0, "Contemporary": 1.2}
BASE_UNITS_LAMBDA = 0.55
TRAFFIC_LIFT = {"Anniversary Sale": 1.50, "Clear the Rack": 1.50,
                "Half-Yearly Sale": 1.35, "Black Friday": 1.80}
RACK_EVENT_CANNIBALIZATION = 0.85      # Nordstrom.com order volume x0.85 during Rack events
PROMO_UPTAKE_IN_EVENT = {"low": 0.55, "mid": 0.80, "high": 0.95}
COGS_RATIO = {"full": 0.50, "rack": 0.45}
ANNUAL_TURNS = {"Designer Apparel": 3.0, "Contemporary Shoes": 3.6, "Handbags & Accessories": 2.4,
                "Beauty & Fragrance": 4.5, "Home & Gifts": 3.4}
RACK_TURN_MULT = 1.7
BASELINE_PROMO_PROB = {  # outside events, by latent price sensitivity: (full-line, rack)
    "low": (0.02, 0.20), "mid": (0.06, 0.45), "high": (0.20, 0.80)}
RETURN_RATE = dict(zip(CHANNELS, [0.08, 0.22, 0.10, 0.24]))
OUTAGE = {"channel": "NordstromRack.com", "dates": ["2026-03-14", "2026-03-15"]}

# ---- promo calendar --------------------------------------------------------
events = [
    ("EVT-01", "Clear the Rack", "2025-04-10", "2025-04-20", RACK, [0.30, 0.40, 0.50]),
    ("EVT-02", "Clear the Rack", "2025-06-12", "2025-06-22", RACK, [0.30, 0.40, 0.50]),
    ("EVT-03", "Anniversary Sale", "2025-07-11", "2025-08-03", FULL_LINE, [0.15, 0.20, 0.30]),
    ("EVT-04", "Clear the Rack", "2025-10-09", "2025-10-19", RACK, [0.30, 0.40, 0.50]),
    ("EVT-05", "Black Friday", "2025-11-24", "2025-12-01", CHANNELS, [0.15, 0.20, 0.30, 0.40]),
    ("EVT-06", "Half-Yearly Sale", "2025-12-26", "2026-01-08", FULL_LINE, [0.15, 0.20, 0.30]),
    ("EVT-07", "Clear the Rack", "2026-04-09", "2026-04-19", RACK, [0.30, 0.40, 0.50]),
    ("EVT-08", "Clear the Rack", "2026-06-11", "2026-06-21", RACK, [0.30, 0.40, 0.50]),
    ("EVT-09", "Anniversary Sale", "2026-07-10", "2026-08-02", FULL_LINE, [0.15, 0.20, 0.30]),
]
cal_rows = []
for eid, name, s, e, chs, depths in events:
    for ch in chs:
        cal_rows.append((eid, name, s, e, ch, ",".join(str(d) for d in depths)))
raw_promo_calendar = pd.DataFrame(cal_rows, columns=[
    "event_id", "event_name", "start_date", "end_date", "sales_channel", "discount_options"])

# ---- day x channel demand matrix ------------------------------------------
days = pd.date_range(START, END, freq="D")
month_factor = {1: .90, 2: .85, 3: .95, 4: 1.0, 5: 1.05, 6: 1.0, 7: 1.05,
                8: 1.0, 9: 1.0, 10: 1.05, 11: 1.20, 12: 1.35}
season = np.array([month_factor[d.month] * (1.15 if d.dayofweek >= 5 else 1.0) for d in days])
W = np.outer(season, CHANNEL_SHARE)
event_lookup = {}                       # (date, channel) -> (event_id, name, depths)
for eid, name, s, e, chs, depths in events:
    for d in pd.date_range(s, e):
        for ch in chs:
            event_lookup[(d, ch)] = (eid, name, depths)
rack_event_days = {d for (d, ch), (eid, name, _) in event_lookup.items() if name == "Clear the Rack"}
for i, d in enumerate(days):
    for j, ch in enumerate(CHANNELS):
        if (d, ch) in event_lookup:
            W[i, j] *= TRAFFIC_LIFT[event_lookup[(d, ch)][1]]
        if ch == "Nordstrom.com" and d in rack_event_days:
            W[i, j] *= RACK_EVENT_CANNIBALIZATION
        if ch == OUTAGE["channel"] and d.strftime("%Y-%m-%d") in OUTAGE["dates"]:
            W[i, j] = 0.0
p = (W / W.sum()).ravel()
cell = rng.choice(W.size, size=N_ORDERS, p=p)
day_idx, ch_idx = np.divmod(cell, len(CHANNELS))
order_date = days[day_idx]
channel = np.array(CHANNELS)[ch_idx]

# ---- customers ---------------------------------------------------------------
sens = rng.choice(["low", "mid", "high"], size=N_CUSTOMERS, p=[0.30, 0.45, 0.25])
activity = rng.gamma(shape=0.8, scale=1.0, size=N_CUSTOMERS)
rank = (-activity).argsort().argsort() / N_CUSTOMERS        # 0 = most active
tier = np.select([rank < 0.03, rank < 0.15, rank < 0.45],
                 ["Icon", "Influencer", "Insider"], default="Member")
customers = pd.DataFrame({
    "customer_id": [f"CUST-{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
    "signup_date": (pd.Timestamp("2021-01-01") + pd.to_timedelta(
        rng.integers(0, 1460, N_CUSTOMERS), unit="D")).strftime("%Y-%m-%d"),
    "home_channel": rng.choice(CHANNELS, N_CUSTOMERS, p=CHANNEL_SHARE),
    "loyalty_tier": tier,
})
cust_idx = rng.choice(N_CUSTOMERS, size=N_ORDERS, p=activity / activity.sum())

# ---- brands ----------------------------------------------------------------
brand_rows, prefixes = [], ["DA", "SH", "HB", "BF", "HG"]
for c, pre in zip(CATEGORIES, prefixes):
    for k, t in enumerate(["Luxury", "Premium", "Premium", "Contemporary"], start=1):
        brand_rows.append((f"{pre}-{k:02d}", f"Brand {pre}{k}", c, t))
brands = pd.DataFrame(brand_rows, columns=["brand_id", "brand_name", "merchandise_category", "price_tier"])
TIER_PRICE = {"Luxury": 2.2, "Premium": 1.3, "Contemporary": 0.7}
CAT_BASE_PRICE = dict(zip(CATEGORIES, [220, 140, 310, 45, 70]))

category = rng.choice(CATEGORIES, size=N_ORDERS, p=CAT_SHARE)
brand_id, tier_of = np.empty(N_ORDERS, dtype=object), np.empty(N_ORDERS, dtype=object)
for c in CATEGORIES:
    m = category == c
    sub = brands[brands.merchandise_category == c].reset_index(drop=True)
    pick = rng.choice(len(sub), size=m.sum(), p=[0.15, 0.30, 0.30, 0.25])
    brand_id[m], tier_of[m] = sub.brand_id.values[pick], sub.price_tier.values[pick]

unit_price = np.array([CAT_BASE_PRICE[c] * TIER_PRICE[t] for c, t in zip(category, tier_of)])
unit_price = np.clip(unit_price * rng.lognormal(0, 0.35, N_ORDERS), 8, 2500)

# ---- promotions --------------------------------------------------------------
event_id = np.full(N_ORDERS, None, dtype=object)
discount = np.zeros(N_ORDERS)
cust_sens = sens[cust_idx]
u = rng.random(N_ORDERS)
for i in range(N_ORDERS):
    key = (order_date[i], channel[i])
    if key in event_lookup:
        eid, name, depths = event_lookup[key]
        if u[i] < PROMO_UPTAKE_IN_EVENT[cust_sens[i]]:
            event_id[i] = eid
            discount[i] = rng.choice(depths)
    elif channel[i] in RACK:                       # always-on off-price markdown
        if u[i] < BASELINE_PROMO_PROB[cust_sens[i]][1]:
            discount[i] = rng.choice([0.30, 0.40, 0.50])
    elif u[i] < BASELINE_PROMO_PROB[cust_sens[i]][0]:   # sparse full-line markdowns
        discount[i] = rng.choice([0.15, 0.20])
is_promo = (discount > 0).astype(int)

# ---- units, revenue, cost, returns ------------------------------------------
elast = np.array([TRUE_ELASTICITY[c] * TIER_ELASTICITY_MULT[t] for c, t in zip(category, tier_of)])
lam = BASE_UNITS_LAMBDA * (1 - discount) ** (-elast)
units = 1 + rng.poisson(lam)
gross = units * unit_price
net = gross * (1 - discount)
ratio = np.where(np.isin(channel, RACK), COGS_RATIO["rack"], COGS_RATIO["full"])
ratio = np.clip(ratio + np.select([tier_of == "Luxury", tier_of == "Contemporary"], [0.03, -0.03], 0)
                + rng.normal(0, 0.04, N_ORDERS), 0.2, 0.8)
cogs = gross * ratio
p_ret = np.array([RETURN_RATE[c] for c in channel]) + 0.06 * (discount >= 0.40)
is_returned = (rng.random(N_ORDERS) < p_ret).astype(int)

order = np.lexsort((np.arange(N_ORDERS), order_date.values))    # chronological IDs
tx = pd.DataFrame({
    "transaction_id": [f"TXN-{i:07d}" for i in range(1, N_ORDERS + 1)],
    "transaction_date": order_date[order].strftime("%Y-%m-%d"),
    "customer_id": customers.customer_id.values[cust_idx][order],
    "sales_channel": channel[order],
    "merchandise_category": category[order],
    "brand_id": brand_id[order],
    "units_sold": units[order],
    "unit_price": np.round(unit_price[order], 2),
    "is_promotional": is_promo[order],
    "discount_percentage": discount[order],
    "gross_revenue": np.round(gross[order], 2),
    "net_revenue": np.round(net[order], 2),
    "cost_of_goods_sold": np.round(cogs[order], 2),
    "gross_margin": np.round(net[order] - cogs[order], 2),
    "is_returned": is_returned[order],
})
tx["returned_net_revenue"] = np.where(tx.is_returned == 1, tx.net_revenue, 0.0)

# ---- inventory (built from clean COGS; annual turns by category and format) --
tx["month_start"] = tx.transaction_date.str[:7] + "-01"
inv = (tx.groupby(["month_start", "sales_channel", "merchandise_category"], as_index=False)
         .cost_of_goods_sold.sum())
annual_turn = inv.merchandise_category.map(ANNUAL_TURNS).values * np.where(
    inv.sales_channel.isin(RACK), RACK_TURN_MULT, 1.0)
inv["avg_inventory_cost"] = np.round(
    inv.cost_of_goods_sold / (annual_turn / 12) * rng.lognormal(0, 0.10, len(inv)), 2)
raw_inventory = inv.drop(columns="cost_of_goods_sold")
tx = tx.drop(columns="month_start")

# ---- controlled dirty data (so Phase 2 cleaning is real) -------------------
raw = tx.copy()
idx = rng.permutation(len(raw))
dup_i, null_i, neg_i, disc_i, lab_i = idx[:150], idx[150:210], idx[210:250], idx[250:275], idx[275:355]
raw.loc[null_i, "customer_id"] = None
raw.loc[neg_i, "net_revenue"] = -raw.loc[neg_i, "net_revenue"]
raw.loc[disc_i, "discount_percentage"] = (raw.loc[disc_i, "discount_percentage"] * 100).replace(0, 15)
variants = {"Nordstrom Stores": " Nordstrom Stores", "Nordstrom.com": "nordstrom.COM ",
            "Rack Stores": "RACK STORES", "NordstromRack.com": "nordstromrack.com"}
raw.loc[lab_i, "sales_channel"] = raw.loc[lab_i, "sales_channel"].map(variants)
raw = pd.concat([raw, raw.iloc[dup_i]], ignore_index=True)       # exact duplicates

# ---- write -------------------------------------------------------------------
raw.to_csv(f"{OUT}/raw_transactions.csv", index=False)
customers.to_csv(f"{OUT}/raw_customers.csv", index=False)
brands.to_csv(f"{OUT}/raw_brands.csv", index=False)
raw_promo_calendar.to_csv(f"{OUT}/raw_promo_calendar.csv", index=False)
raw_inventory.to_csv(f"{OUT}/raw_inventory_monthly.csv", index=False)
pd.DataFrame({"customer_id": customers.customer_id, "latent_price_sensitivity": sens}) \
  .to_csv(f"{OUT}/ground_truth_customers.csv", index=False)
with open(f"{OUT}/ground_truth_parameters.json", "w") as f:
    json.dump({"true_elasticity": TRUE_ELASTICITY, "tier_elasticity_multiplier": TIER_ELASTICITY_MULT,
               "traffic_lift": TRAFFIC_LIFT, "rack_event_cannibalization_multiplier": RACK_EVENT_CANNIBALIZATION,
               "outage": OUTAGE, "baseline_promo_prob": BASELINE_PROMO_PROB, "cogs_ratio": COGS_RATIO, "seed": SEED}, f, indent=2)
print(f"raw_transactions rows: {len(raw):,} (50,000 clean + 150 duplicates; "
      f"125 rows are unusable by design)")
