# Data Dictionary

Dataset: `driiiportfolio.merchandising_insights` (BigQuery, US). All data is synthetic.

**Layers:** `raw_` as loaded · `stg_` and `dq_` cleaned and audited · `dim_` descriptive tables · `fct_` order-level facts · `mart_` dashboard aggregates · `analysis_` statistical results.

## Core definitions

| Term | Definition |
| --- | --- |
| Channel | One of four selling channels: Nordstrom Stores, Nordstrom.com, Rack Stores, NordstromRack.com |
| Format (`box_format`) | Full-line (Nordstrom Stores, Nordstrom.com) or Off-price (Rack Stores, NordstromRack.com) |
| Order | One row in `fct_transactions`: one customer, one category, one brand, one date |
| Net revenue | Gross revenue after the discount |
| Gross margin | Net revenue minus cost of goods sold |
| Return-adjusted gross margin | Zero if the order was returned, otherwise gross margin |
| Markdown dollars | Gross revenue minus net revenue |
| Event | A promotion in `dim_promo_event`, active for specific channels and dates |
| DiD | Difference-in-differences: change in a treated channel minus change in an untreated control channel |

## Order-level fact: `fct_transactions`

One row per staged order (49,875), clustered by `sales_channel` and `merchandise_category`.

| Field | Type | Definition |
| --- | --- | --- |
| transaction_id | STRING | Unique order ID |
| transaction_date | DATE | Order date |
| month_start | DATE | First day of the order month |
| customer_id | STRING | Buyer; orders without one are rejected in staging |
| sales_channel | STRING | One of the four standard channel names |
| box_format | STRING | Full-line or Off-price |
| channel_type | STRING | Stores or Digital |
| merchandise_category | STRING | Designer Apparel, Contemporary Shoes, Handbags & Accessories, Beauty & Fragrance, Home & Gifts |
| brand_id | STRING | Brand key (see `dim_brand`) |
| price_tier | STRING | Luxury, Premium or Contemporary |
| units_sold | INT64 | Units in the order |
| unit_price | FLOAT64 | List price per unit |
| is_promotional | INT64 | 1 if discount_percentage is above 0 |
| discount_percentage | FLOAT64 | Share off list price; valid range 0 to 0.8 |
| gross_revenue | FLOAT64 | Units times list price |
| net_revenue | FLOAT64 | Gross revenue after discount |
| markdown_dollars | FLOAT64 | Gross revenue minus net revenue |
| cost_of_goods_sold | FLOAT64 | Cost of the units sold |
| gross_margin | FLOAT64 | Net revenue minus cost of goods sold |
| is_returned | INT64 | 1 if the order was returned |
| returned_net_revenue | FLOAT64 | Net revenue if returned, else 0 |
| return_adjusted_gross_margin | FLOAT64 | 0 if returned, else gross margin |
| event_id, event_name | STRING | Promotion active for that channel and date, if any |
| customer_order_seq | INT64 | The customer's order number, oldest first |
| next_order_date | DATE | Date of the customer's next order; empty for the last order |
| days_to_next_order | INT64 | Days until the next order; empty for the last order |

## Staging and data quality

| Object | Grain | Purpose |
| --- | --- | --- |
| raw_transactions | One as-loaded row (50,150) | Source with injected duplicates, nulls, bad values and inconsistent labels |
| stg_all | One deduplicated row (50,000) | Typed and standardized, with `reject_reason` |
| stg_transactions | One accepted order (49,875) | Rows with no reject reason |
| dq_rejects | One rejected order (125) | `reject_reason`: missing_customer_id (60), negative_net_revenue (40), impossible_discount (25) |
| dq_reconciliation | One row | raw_rows, duplicates_removed, rejected_rows, staged_rows, unexplained_difference (must be 0) |
| dq_channel_day_gaps | One channel-day with no orders | Telemetry completeness check (2 rows) |

## Dimensions

| Table | Fields |
| --- | --- |
| dim_brand | brand_id, brand_name, merchandise_category, price_tier |
| dim_customer | customer_id, signup_date, home_channel, loyalty_tier (Member, Insider, Influencer, Icon) |
| dim_promo_event | event_id, event_name, start_date, end_date, sales_channel, event_days, discount_options |
| dim_date | transaction_date, month_start, calendar_year, calendar_quarter, day_name, is_weekend, is_any_promo_day |
| raw_inventory_monthly | month_start, sales_channel, merchandise_category, avg_inventory_cost |

## Customer tables and views

| Object | Grain | Fields |
| --- | --- | --- |
| customer_rfm | One customer (7,945) | last_order_date, frequency, monetary, observed_gross_margin_ltv, promo_share, avg_discount, recency_days, r_score, f_score, m_score (1 to 5), loyalty_tier, home_channel, rfm_segment (Champions, Loyal cooling, Promising, At risk, Hibernating) |
| metric_repeat_rate_30d | Month x format | orders_observable, orders_repeat_30d, repeat_rate_30d. Orders in the last 30 days of data are excluded |
| customer_first_order | One customer | first_order_date, first_order_channel, first_order_on_promo |

`observed_gross_margin_ltv` covers the 21 months in the data. It is not a forecast.

## Marts (dashboard sources)

**mart_category_performance** (month x channel x category, 420 rows)

| Field | Definition |
| --- | --- |
| month_start, sales_channel, box_format, channel_type, merchandise_category | Grain and descriptors |
| transaction_count, total_units_sold | Orders and units |
| gross_revenue, net_revenue, markdown_dollars, cogs | Revenue, markdown and cost |
| gross_margin, return_adjusted_gross_margin, returned_net_revenue | Margin before and after returns |
| promo_revenue, baseline_revenue, promo_gross_margin, promo_transactions | Promotional versus full-price split |
| returned_transactions | Returned orders |
| avg_inventory_cost | Average inventory at cost for the month |
| gross_margin_pct, promo_revenue_share, return_rate, gmroi_monthly | Stored ratios. Do not average them; recompute from sums |

**Other marts**

| Table | Grain | Fields |
| --- | --- | --- |
| mart_event_performance | Event x channel | Event and pre-period daily orders, revenue and margin; naive_order_lift, naive_revenue_lift, naive_margin_lift (no control group) |
| vw_event_naive_vs_did | Event x effect group (13 rows) | did_revenue_lift, did_margin_lift, did_revenue_total, did_margin_total, did_orders_total, naive_revenue_lift, naive_margin_lift |
| mart_category_health | Format x category (10 rows) | gmroi_annualized, return_adjusted_margin_pct, promo_revenue_share, net_revenue, repeat_rate_30d, category_health_index (0 to 100) |
| mart_rfm_segment_summary | RFM segment (5 rows) | customers, net_revenue, revenue_share, avg_orders, avg_promo_share, gross_margin_after_returns |
| mart_brand_performance | Brand x format (40 rows) | transaction_count, net_revenue, gross_margin, gross_margin_pct, promo_revenue_share, return_rate, return_adjusted_margin_pct |

## Analysis tables (written by Python)

| Table | Grain | Fields |
| --- | --- | --- |
| analysis_elasticity | Category (5) | price_elasticity (log-price coefficient), std_err, ci_low, ci_high, n_orders |
| analysis_discount_bands | Format x discount band (9) | orders, gm_per_order, gm_pct, units_per_order, observed_unit_lift, breakeven_unit_lift, gm_per_order_vs_full_price, ci_low, ci_high, welch_p |
| analysis_did_by_event | Event x effect group x metric (39) | event_days, pre_days_used, treated_pre_mean, did_per_channel_day, lift_pct_vs_pre, total_effect |
| analysis_did_pooled | Event family x effect group x metric (9) | did_coef, ci_low, ci_high, p_value, n_obs. Units are dollars per channel-day, or orders |
| analysis_segments | Customer (7,945) | frequency, monetary, promo_share, avg_discount, recency_days, cluster, segment (Core loyalists, Lapsing, Deal seekers) |
| analysis_anomaly_flags | Flagged day (5) | net_revenue, robust_z, in_event_window, explanation |

## KPI formulas

| KPI | Formula |
| --- | --- |
| Gross margin % | SUM(gross_margin) / SUM(net_revenue) |
| Return-adjusted margin % | SUM(return_adjusted_gross_margin) / SUM(net_revenue) |
| AOV | SUM(net_revenue) / SUM(transaction_count) |
| Return rate | SUM(returned_transactions) / SUM(transaction_count) |
| GMROI (annualized) | SUM(gross_margin) / SUM(avg_inventory_cost) * 12 |
| Inventory turns (annualized) | SUM(cogs) / SUM(avg_inventory_cost) * 12 |
| Repeat rate 30d | SUM(orders_repeat_30d) / SUM(orders_observable) |
| Break-even unit lift | Margin per unit at full price divided by margin per unit at the discount, minus 1 |
| Category Health Index | 100 x (0.35 x GMROI rank + 0.25 x return-adjusted margin rank + 0.20 x repeat-rate rank + 0.20 x (1 - promo-share rank)), ranks as percentile within the 10 rows |
