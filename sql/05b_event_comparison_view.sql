-- Naive vs difference-in-differences lift, one row per event and effect group.
-- The Nordstrom.com (cannibalization) rows have no naive value: no promotion is defined for Nordstrom.com in those events.
CREATE OR REPLACE VIEW `driiiportfolio.merchandising_insights.vw_event_naive_vs_did` AS
WITH naive AS (
  SELECT
    event_id, event_name,
    CASE
      WHEN event_name = 'Clear the Rack' AND sales_channel IN ('Rack Stores', 'NordstromRack.com') THEN 'Rack channels'
      WHEN event_name IN ('Anniversary Sale', 'Half-Yearly Sale') THEN 'Full-line channels'
    END AS effect_on,
    SAFE_DIVIDE(SUM(event_net_revenue_per_day), SUM(pre_net_revenue_per_day)) - 1   AS naive_revenue_lift,
    SAFE_DIVIDE(SUM(event_gross_margin_per_day), SUM(pre_gross_margin_per_day)) - 1 AS naive_margin_lift
  FROM `driiiportfolio.merchandising_insights.mart_event_performance`
  GROUP BY 1, 2, 3
),
did AS (
  SELECT
    event_id, event_name, effect_on,
    MAX(IF(metric = 'net_revenue',  lift_pct_vs_pre, NULL)) AS did_revenue_lift,
    MAX(IF(metric = 'gross_margin', lift_pct_vs_pre, NULL)) AS did_margin_lift,
    MAX(IF(metric = 'net_revenue',  total_effect,    NULL)) AS did_revenue_total,
    MAX(IF(metric = 'gross_margin', total_effect,    NULL)) AS did_margin_total,
    MAX(IF(metric = 'orders',       total_effect,    NULL)) AS did_orders_total
  FROM `driiiportfolio.merchandising_insights.analysis_did_by_event`
  GROUP BY 1, 2, 3
)
SELECT d.*, n.naive_revenue_lift, n.naive_margin_lift
FROM did d
LEFT JOIN naive n ON d.event_id = n.event_id AND d.effect_on = n.effect_on;
