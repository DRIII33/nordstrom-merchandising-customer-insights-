-- Grain: month x channel x category. Ratios are stored for convenience but the dashboard
-- recomputes them from summed numerators and denominators
-- Mart Category Performance
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.mart_category_performance` AS
WITH sales AS (
  SELECT
    month_start, sales_channel, box_format, channel_type, merchandise_category,
    COUNT(*)                                            AS transaction_count,
    SUM(units_sold)                                     AS total_units_sold,
    SUM(gross_revenue)                                  AS gross_revenue,
    SUM(net_revenue)                                    AS net_revenue,
    SUM(markdown_dollars)                               AS markdown_dollars,
    SUM(cost_of_goods_sold)                             AS cogs,
    SUM(gross_margin)                                   AS gross_margin,
    SUM(return_adjusted_gross_margin)                   AS return_adjusted_gross_margin,
    SUM(returned_net_revenue)                           AS returned_net_revenue,
    SUM(IF(is_promotional = 1, net_revenue, 0))         AS promo_revenue,
    SUM(IF(is_promotional = 0, net_revenue, 0))         AS baseline_revenue,
    SUM(IF(is_promotional = 1, gross_margin, 0))        AS promo_gross_margin,
    COUNTIF(is_promotional = 1)                         AS promo_transactions,
    SUM(is_returned)                                    AS returned_transactions
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  GROUP BY 1, 2, 3, 4, 5
)
SELECT
  s.*,
  SAFE_DIVIDE(s.gross_margin, s.net_revenue)            AS gross_margin_pct,
  SAFE_DIVIDE(s.promo_revenue, s.net_revenue)           AS promo_revenue_share,
  SAFE_DIVIDE(s.returned_transactions, s.transaction_count) AS return_rate,
  i.avg_inventory_cost,
  SAFE_DIVIDE(s.gross_margin, i.avg_inventory_cost)     AS gmroi_monthly
FROM sales s
LEFT JOIN `driiiportfolio.merchandising_insights.raw_inventory_monthly` i
  ON s.month_start = i.month_start
 AND s.sales_channel = i.sales_channel
 AND s.merchandise_category = i.merchandise_category;

-- Naive pre/post event performance
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.mart_event_performance` AS
WITH daily AS (
  SELECT transaction_date, sales_channel, COUNT(*) AS orders,
         SUM(net_revenue) AS net_revenue, SUM(gross_margin) AS gross_margin
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  GROUP BY 1, 2
),
grid AS (
  SELECT d AS transaction_date, ch AS sales_channel
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2026-09-30')) AS d
  CROSS JOIN UNNEST(['Nordstrom Stores', 'Nordstrom.com', 'Rack Stores', 'NordstromRack.com']) AS ch
),
event_days AS (
  SELECT DISTINCT day AS transaction_date
  FROM `driiiportfolio.merchandising_insights.dim_promo_event`,
       UNNEST(GENERATE_DATE_ARRAY(start_date, end_date)) AS day
),
gap_days AS (
  SELECT DISTINCT transaction_date FROM `driiiportfolio.merchandising_insights.dq_channel_day_gaps` 
),
dense AS (
  SELECT
    g.transaction_date, g.sales_channel,
    IFNULL(d.orders, 0) AS orders,
    IFNULL(d.net_revenue, 0) AS net_revenue,
    IFNULL(d.gross_margin, 0) AS gross_margin,
    (ed.transaction_date IS NOT NULL OR gd.transaction_date IS NOT NULL) AS excluded_from_baseline
  FROM grid g
  LEFT JOIN daily d ON g.transaction_date = d.transaction_date AND g.sales_channel = d.sales_channel
  LEFT JOIN event_days ed ON g.transaction_date = ed.transaction_date
  LEFT JOIN gap_days gd ON g.transaction_date = gd.transaction_date
),
agg AS (
  SELECT
    e.event_id, e.event_name, e.sales_channel, e.start_date, e.end_date, e.event_days,
    AVG(IF(n.transaction_date BETWEEN e.start_date AND e.end_date, n.orders, NULL))        AS event_orders_per_day,
    AVG(IF(n.transaction_date < e.start_date AND NOT n.excluded_from_baseline, n.orders, NULL)) AS pre_orders_per_day,
    AVG(IF(n.transaction_date BETWEEN e.start_date AND e.end_date, n.net_revenue, NULL))   AS event_net_revenue_per_day,
    AVG(IF(n.transaction_date < e.start_date AND NOT n.excluded_from_baseline, n.net_revenue, NULL)) AS pre_net_revenue_per_day,
    AVG(IF(n.transaction_date BETWEEN e.start_date AND e.end_date, n.gross_margin, NULL))  AS event_gross_margin_per_day,
    AVG(IF(n.transaction_date < e.start_date AND NOT n.excluded_from_baseline, n.gross_margin, NULL)) AS pre_gross_margin_per_day
  FROM `driiiportfolio.merchandising_insights.dim_promo_event` e
  JOIN dense n
    ON n.sales_channel = e.sales_channel
   AND n.transaction_date BETWEEN DATE_SUB(e.start_date, INTERVAL 28 DAY) AND e.end_date
  GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
  agg.*,
  SAFE_DIVIDE(event_orders_per_day, pre_orders_per_day) - 1               AS naive_order_lift,
  SAFE_DIVIDE(event_net_revenue_per_day, pre_net_revenue_per_day) - 1     AS naive_revenue_lift,
  SAFE_DIVIDE(event_gross_margin_per_day, pre_gross_margin_per_day) - 1   AS naive_margin_lift
FROM agg;

-- Composite Category Health Index
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.mart_category_health` AS
WITH perf AS (
  SELECT
    box_format, merchandise_category,
    SAFE_DIVIDE(SUM(gross_margin), SUM(avg_inventory_cost)) * 12            AS gmroi_annualized,
    SAFE_DIVIDE(SUM(return_adjusted_gross_margin), SUM(net_revenue))        AS return_adjusted_margin_pct,
    SAFE_DIVIDE(SUM(promo_revenue), SUM(net_revenue))                       AS promo_revenue_share,
    SUM(net_revenue)                                                        AS net_revenue
  FROM `driiiportfolio.merchandising_insights.mart_category_performance`
  GROUP BY 1, 2
),
rep AS (
  SELECT box_format, merchandise_category,
         SAFE_DIVIDE(COUNTIF(days_to_next_order <= 30), COUNT(*)) AS repeat_rate_30d
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  WHERE transaction_date <= DATE_SUB(
    (SELECT MAX(transaction_date) FROM `driiiportfolio.merchandising_insights.fct_transactions`), INTERVAL 30 DAY)
  GROUP BY 1, 2
)
SELECT
  p.*,
  r.repeat_rate_30d,
  ROUND(100 * (
      0.35 * PERCENT_RANK() OVER (ORDER BY p.gmroi_annualized)
    + 0.25 * PERCENT_RANK() OVER (ORDER BY p.return_adjusted_margin_pct)
    + 0.20 * PERCENT_RANK() OVER (ORDER BY r.repeat_rate_30d)
    + 0.20 * (1 - PERCENT_RANK() OVER (ORDER BY p.promo_revenue_share))), 1) AS category_health_index
FROM perf p
JOIN rep r ON p.box_format = r.box_format AND p.merchandise_category = r.merchandise_category;

-- RFM Segment Summary
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.mart_rfm_segment_summary` AS
SELECT
  rfm_segment,
  COUNT(*)                                          AS customers,
  SUM(monetary)                                     AS net_revenue,
  SAFE_DIVIDE(SUM(monetary), SUM(SUM(monetary)) OVER ()) AS revenue_share,
  AVG(frequency)                                    AS avg_orders,
  AVG(promo_share)                                  AS avg_promo_share,
  SUM(observed_gross_margin_ltv)                    AS gross_margin_after_returns
FROM `driiiportfolio.merchandising_insights.customer_rfm`
GROUP BY rfm_segment;

-- Brand Performance Scorecard
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.mart_brand_performance` AS
SELECT
  b.brand_id, b.brand_name, b.price_tier, b.merchandise_category, f.box_format,
  COUNT(*)                                                       AS transaction_count,
  SUM(f.net_revenue)                                             AS net_revenue,
  SUM(f.gross_margin)                                            AS gross_margin,
  SAFE_DIVIDE(SUM(f.gross_margin), SUM(f.net_revenue))           AS gross_margin_pct,
  SAFE_DIVIDE(SUM(IF(f.is_promotional = 1, f.net_revenue, 0)), SUM(f.net_revenue)) AS promo_revenue_share,
  SAFE_DIVIDE(SUM(f.is_returned), COUNT(*))                      AS return_rate,
  SAFE_DIVIDE(SUM(f.return_adjusted_gross_margin), SUM(f.net_revenue)) AS return_adjusted_margin_pct
FROM `driiiportfolio.merchandising_insights.fct_transactions` f
JOIN `driiiportfolio.merchandising_insights.dim_brand` b ON f.brand_id = b.brand_id
GROUP BY 1, 2, 3, 4, 5;
