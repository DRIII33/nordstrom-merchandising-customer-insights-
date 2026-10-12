import os
os.environ["AURA_MODE"] = "bigquery"

# 1. We write the complete file first so that it exists in the filesystem
with open("sa_run.py", "w") as f:
    f.write('''
import json
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrices
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

MODE = "bigquery"
PROJECT, DATASET = "driiiportfolio", "merchandising_insights"
RACK = ["Rack Stores", "NordstromRack.com"]
FULL_LINE = ["Nordstrom Stores", "Nordstrom.com"]
ALL_CH = FULL_LINE + RACK
RESULTS = {}

def load_bigquery():
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT)
    cfg = bigquery.QueryJobConfig(maximum_bytes_billed=2 * 1024**3)
    q = lambda sql: client.query(sql, job_config=cfg).to_dataframe()
    fct = q(f"SELECT * FROM `{PROJECT}.{DATASET}.fct_transactions`")
    cal = q(f"SELECT * FROM `{PROJECT}.{DATASET}.dim_promo_event`")
    inv = q(f"SELECT * FROM `{PROJECT}.{DATASET}.raw_inventory_monthly`")
    return client, fct, cal, inv

def elasticity(fct):
    d = fct.copy()
    d["ln_p"] = np.log(1 - d.discount_percentage)
    d["ln_list"] = np.log(d.unit_price)
    d["month"] = pd.to_datetime(d.transaction_date).dt.to_period("M").astype(str)
    rows = []
    for cat, g in d.groupby("merchandise_category"):
        fit = smf.glm("units_sold ~ ln_p + ln_list + C(sales_channel) + C(month)", data=g,
                      family=sm.families.Poisson()).fit(cov_type="HC3")
        lo, hi = fit.conf_int().loc["ln_p"]
        rows.append((cat, fit.params["ln_p"], fit.bse["ln_p"], lo, hi, len(g)))
    out = pd.DataFrame(rows, columns=["merchandise_category", "price_elasticity", "std_err",
                                      "ci_low", "ci_high", "n_orders"])
    out["price_elasticity"] = out.price_elasticity.round(3)
    _, X = dmatrices("units_sold ~ ln_p + ln_list + C(sales_channel)", d, return_type="dataframe")
    vif = pd.Series([variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])],
                    index=X.columns[1:]).round(2)
    return out.sort_values("price_elasticity"), vif

def discount_band_economics(fct):
    d = fct.copy()
    d["format"] = np.where(d.sales_channel.isin(RACK), "Off-price (Rack)", "Full-line")
    d["band"] = pd.cut(d.discount_percentage, [-0.01, 0, 0.2, 0.3, 0.4, 0.5],
                       labels=["0%", "1-20%", "21-30%", "31-40%", "41-50%"])
    rows = []
    for fmt, g in d.groupby("format"):
        base = g[g.band == "0%"]
        for band, b in g.groupby("band", observed=True):
            if len(b) < 100:
                continue
            t = stats.ttest_ind(b.gross_margin, base.gross_margin, equal_var=False)
            ci = t.confidence_interval()
            gm_unit_b, gm_unit_0 = b.gross_margin.sum() / b.units_sold.sum(), base.gross_margin.sum() / base.units_sold.sum()
            rows.append({
                "format": fmt, "discount_band": str(band), "orders": len(b),
                "gm_per_order": b.gross_margin.mean(), "gm_pct": b.gross_margin.sum() / b.net_revenue.sum(),
                "units_per_order": b.units_sold.mean(),
                "observed_unit_lift": b.units_sold.mean() / base.units_sold.mean() - 1,
                "breakeven_unit_lift": (gm_unit_0 / gm_unit_b - 1) if gm_unit_b > 0 else np.inf,
                "gm_per_order_vs_full_price": b.gross_margin.mean() - base.gross_margin.mean(),
                "ci_low": ci.low, "ci_high": ci.high, "welch_p": t.pvalue})
    return pd.DataFrame(rows).round(4)

def daily_panel(fct, cal):
    fct["transaction_date"] = pd.to_datetime(fct.transaction_date)
    dc = (fct.groupby(["transaction_date", "sales_channel"])
             .agg(net_revenue=("net_revenue", "sum"), gross_margin=("gross_margin", "sum"),
                  orders=("transaction_id", "count")).reset_index())
    full = pd.MultiIndex.from_product( 
        [pd.date_range(fct.transaction_date.min(), fct.transaction_date.max()), ALL_CH],
        names=["transaction_date", "sales_channel"])
    dc = dc.set_index(["transaction_date", "sales_channel"]).reindex(full, fill_value=0).reset_index()
    return dc

def outage_dates(dc):
    med = dc.groupby("sales_channel").orders.transform("median")
    return set(dc.loc[(dc.orders == 0) & (med > 0), "transaction_date"])

def did_events(dc, cal, bad_dates, pre_days=28):
    cal = cal.copy()
    cal["start_date"] = pd.to_datetime(cal.start_date)
    cal["end_date"] = pd.to_datetime(cal.end_date)
    any_event_days = set()
    for _, r in cal.iterrows():
        any_event_days |= set(pd.date_range(r.start_date, r.end_date))
    excluded = any_event_days | set(bad_dates)
    out = []
    for eid, g in cal.groupby("event_id"):
        name, s, e = g.event_name.iloc[0], g.start_date.iloc[0], g.end_date.iloc[0]
        treated = set(g.sales_channel)
        if len(treated) == 4:
            continue
        if name == "Clear the Rack":
            specs = {"Rack channels": (RACK, ["Nordstrom Stores"]),
                     "Nordstrom.com (cannibalization)": (["Nordstrom.com"], ["Nordstrom Stores"])}
        else:
            specs = {"Full-line channels": (FULL_LINE, RACK)}
        post_days = pd.date_range(s, e)
        pre = [d for d in pd.date_range(s - pd.Timedelta(days=pre_days), s - pd.Timedelta(days=1))
               if d not in excluded]
        for label, (tr, ct) in specs.items():
            for metric in ["orders", "net_revenue", "gross_margin"]:
                f = lambda chs, days: dc[dc.sales_channel.isin(chs) & dc.transaction_date.isin(days)] \
                    .groupby("sales_channel")[metric].mean().mean()
                tr_pre, tr_post, ct_pre, ct_post = f(tr, pre), f(tr, post_days), f(ct, pre), f(ct, post_days)
                did = (tr_post - tr_pre) - (ct_post - ct_pre)
                out.append({"event_id": eid, "event_name": name, "effect_on": label, "metric": metric,
                            "event_days": len(post_days), "pre_days_used": len(pre),
                            "treated_pre_mean": tr_pre, "did_per_channel_day": did,
                            "lift_pct_vs_pre": did / tr_pre if tr_pre else np.nan,
                            "total_effect": did * len(post_days) * len(tr)})
    return pd.DataFrame(out).round(4)

def did_pooled(dc, cal, bad_dates, family, treated, control, metric, pre_days=28):
    cal = cal.copy()
    cal["start_date"] = pd.to_datetime(cal.start_date)
    cal["end_date"] = pd.to_datetime(cal.end_date)
    excluded = set(bad_dates)
    for _, r in cal.iterrows():
        excluded |= set(pd.date_range(r.start_date, r.end_date))
    frames = []
    for eid, g in cal[cal.event_name == family].groupby("event_id"):
        s, e = g.start_date.iloc[0], g.end_date.iloc[0]
        days = [d for d in pd.date_range(s - pd.Timedelta(days=pre_days), e)
               if (d >= s) or (d not in excluded)]
        sub = dc[dc.sales_channel.isin(treated + control) & dc.transaction_date.isin(days)].copy()
        sub["post"] = (sub.transaction_date >= s).astype(int)
        sub["treat"] = sub.sales_channel.isin(treated).astype(int)
        sub["event_id"] = eid
        frames.append(sub)
    P = pd.concat(frames)
    fit = smf.ols(f"{metric} ~ treat:post + post + C(event_id) + C(sales_channel)", data=P).fit(cov_type="HC3")
    lo, hi = fit.conf_int().loc["treat:post"]
    return {"family": family, "metric": metric, "did_coef": fit.params["treat:post"],
            "ci_low": lo, "ci_high": hi, "p_value": fit.pvalues["treat:post"], "n_obs": int(fit.nobs)}

def pretrend_check(dc, cal, bad_dates, treated, control, window=28):
    placebo = cal.copy()
    placebo["start_date"] = pd.to_datetime(placebo.start_date) - pd.Timedelta(days=14)
    placebo["end_date"] = pd.to_datetime(placebo.end_date) - pd.Timedelta(days=14)
    return did_pooled(dc, placebo, bad_dates, "Clear the Rack", treated, control, "gross_margin", window)

def segment_customers(fct, asof):
    c = (fct.groupby("customer_id")
            .agg(last_order=("transaction_date", "max"), frequency=("transaction_id", "count"),
                 monetary=("net_revenue", "sum"), promo_share=("is_promotional", "mean"),
                 avg_discount=("discount_percentage", "mean")).reset_index())
    c["recency_days"] = (pd.Timestamp(asof) - pd.to_datetime(c.last_order)).dt.days
    X = np.column_stack([np.log1p(c.recency_days), np.log1p(c.frequency), np.log1p(c.monetary), c.promo_share])
    Z = StandardScaler().fit_transform(X)
    sil = {k: silhouette_score(Z, KMeans(k, n_init=10, random_state=42).fit_predict(Z), sample_size=5000, random_state=42)
           for k in range(3, 7)}
    k = max(sil, key=sil.get)
    c["cluster"] = KMeans(k, n_init=10, random_state=42).fit_predict(Z)
    prof = c.groupby("cluster").agg(customers=("customer_id", "count"), recency_days=("recency_days", "mean"),
                                    orders=("frequency", "mean"), net_revenue=("monetary", "mean"),
                                    promo_share=("promo_share", "mean")).round(3)
    return c, prof, sil

def label_clusters(prof):
    labels = {}
    for cl, r in prof.iterrows():
        if r.promo_share >= prof.promo_share.quantile(0.67) and r.promo_share > 0.35:
            labels[cl] = "Deal seekers"
        elif r.orders >= prof.orders.quantile(0.67):
            labels[cl] = "Core loyalists"
        elif r.recency_days >= prof.recency_days.quantile(0.67):
            labels[cl] = "Lapsing"
        else:
            labels[cl] = "Occasional full-price"
    return labels

def anomalies(dc, cal):
    tot = dc.groupby("transaction_date").net_revenue.sum().rename("net_revenue").reset_index()
    med = tot.net_revenue.rolling(35, center=True, min_periods=14).median()
    mad = (tot.net_revenue - med).abs().rolling(35, center=True, min_periods=14).median()
    tot["robust_z"] = 0.6745 * (tot.net_revenue - med) / mad.replace(0, np.nan)
    ev_days = set()
    for _, r in cal.iterrows():
        ev_days |= set(pd.date_range(r.start_date, r.end_date))
    tot["in_event_window"] = tot.transaction_date.isin(ev_days)
    flagged = tot[tot.robust_z.abs() > 3.5].copy()
    flagged["explanation"] = np.where(flagged.in_event_window, "promo event", "UNEXPLAINED - investigate")
    return flagged

def run():
    client, fct, cal, inv = load_bigquery()
    fct["transaction_date"] = pd.to_datetime(fct.transaction_date)
    cal["start_date"], cal["end_date"] = pd.to_datetime(cal.start_date), pd.to_datetime(cal.end_date)
    os.makedirs("results", exist_ok=True)

    el, vif = elasticity(fct)
    bands = discount_band_economics(fct)
    dc = daily_panel(fct, cal)
    gaps = outage_dates(dc)
    ev = did_events(dc, cal, gaps)
    pooled = pd.DataFrame(
        [did_pooled(dc, cal, gaps, "Clear the Rack", RACK, ["Nordstrom Stores"], m) for m in ["orders", "net_revenue", "gross_margin"]]
        + [did_pooled(dc, cal, gaps, "Clear the Rack", ["Nordstrom.com"], ["Nordstrom Stores"], m) for m in ["orders", "net_revenue", "gross_margin"]]
        + [did_pooled(dc, cal, gaps, "Anniversary Sale", FULL_LINE, RACK, m) for m in ["orders", "net_revenue", "gross_margin"]])
    pooled["effect_on"] = ["Rack channels"] * 3 + ["Nordstrom.com (cannibalization)"] * 3 + ["Full-line channels"] * 3
    placebo = pretrend_check(dc, cal, gaps, RACK, ["Nordstrom Stores"])
    seg, prof, sil = segment_customers(fct, asof=fct.transaction_date.max() + pd.Timedelta(days=1))
    prof["segment"] = pd.Series(label_clusters(prof))
    flagged = anomalies(dc, cal)
    gap_df = pd.DataFrame({"transaction_date": sorted(gaps)})
    gap_df["issue"] = "zero-order day for a channel that normally trades (telemetry gap suspect)"

    for name, df in [("elasticity", el), ("discount_band_economics", bands), ("did_by_event", ev),
                     ("did_pooled", pooled), ("segment_profiles", prof.reset_index()),
                     ("anomaly_flags", flagged), ("telemetry_gaps", gap_df)]:
        df.to_csv(f"results/{name}.csv", index=False)
        RESULTS[name] = df
    seg["segment"] = seg.cluster.map(prof.segment)
    seg.drop(columns=["last_order"]).to_csv("results/customer_segments.csv", index=False)
    
    from google.cloud import bigquery
    for name, df in [("analysis_elasticity", el), ("analysis_discount_bands", bands),
                     ("analysis_did_by_event", ev), ("analysis_did_pooled", pooled),
                     ("analysis_segments", seg.drop(columns=["last_order"])),
                     ("analysis_anomaly_flags", flagged)]:
        client.load_table_from_dataframe(
            df, f"{PROJECT}.{DATASET}.{name}",
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")).result()
    return RESULTS, vif, sil, placebo, gaps
''')

# 2. Now import and execute the newly written module
import sa_run
import importlib
importlib.reload(sa_run)
RESULTS, vif, sil, placebo, gaps = sa_run.run()
print("Successfully computed and exported statistical analysis outputs to results/ and BigQuery!")
