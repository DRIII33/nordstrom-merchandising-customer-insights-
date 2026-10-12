WITH checks AS (
  SELECT 'reconciliation_unexplained_difference' AS test_name, '0' AS expected,
         CAST(unexplained_difference AS STRING) AS actual, unexplained_difference = 0 AS passed
  FROM `driiiportfolio.merchandising_insights.dq_reconciliation`
  UNION ALL
  SELECT 'staged_rows', '49875', CAST(COUNT(*) AS STRING), COUNT(*) = 49875
  FROM `driiiportfolio.merchandising_insights.stg_transactions`
  UNION ALL
  SELECT 'no_duplicate_transaction_ids', '0', CAST(COUNT(*) - COUNT(DISTINCT transaction_id) AS STRING),
         COUNT(*) = COUNT(DISTINCT transaction_id)
  FROM `driiiportfolio.merchandising_insights.stg_transactions`
  UNION ALL
  SELECT 'fact_rows_equal_staged_rows (no join fan-out)', '49875', CAST(COUNT(*) AS STRING), COUNT(*) = 49875
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  UNION ALL
  SELECT 'mart_net_revenue_equals_staged', '0.00',
         CAST(ROUND(ABS((SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.mart_category_performance`)
                      - (SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.stg_transactions`)), 2) AS STRING),
         ABS((SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.mart_category_performance`)
           - (SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.stg_transactions`)) < 0.01
  UNION ALL
  SELECT 'margin_identity_within_rounding (tolerance 25 USD)', '< 25',
         CAST(ROUND(ABS(SUM(net_revenue - cost_of_goods_sold - gross_margin)), 2) AS STRING),
         ABS(SUM(net_revenue - cost_of_goods_sold - gross_margin)) < 25
  FROM `driiiportfolio.merchandising_insights.stg_transactions`
  UNION ALL
  SELECT 'mart_rows (21 months x 4 channels x 5 categories)', '420', CAST(COUNT(*) AS STRING), COUNT(*) = 420
  FROM `driiiportfolio.merchandising_insights.mart_category_performance`
  UNION ALL
  SELECT 'mart_rows_missing_inventory', '0', CAST(COUNTIF(avg_inventory_cost IS NULL) AS STRING),
         COUNTIF(avg_inventory_cost IS NULL) = 0
  FROM `driiiportfolio.merchandising_insights.mart_category_performance`
  UNION ALL
  SELECT 'discount_within_0_to_0.8', '0', CAST(COUNTIF(discount_percentage NOT BETWEEN 0 AND 0.8) AS STRING),
         COUNTIF(discount_percentage NOT BETWEEN 0 AND 0.8) = 0
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  UNION ALL
  SELECT 'four_standard_channels', '4', CAST(COUNT(DISTINCT sales_channel) AS STRING), COUNT(DISTINCT sales_channel) = 4
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  UNION ALL
  SELECT 'events_do_not_overlap_within_channel', '0', CAST(COUNT(*) AS STRING), COUNT(*) = 0
  FROM `driiiportfolio.merchandising_insights.dim_promo_event` a
  JOIN `driiiportfolio.merchandising_insights.dim_promo_event` b
    ON a.sales_channel = b.sales_channel AND a.event_id < b.event_id
   AND a.start_date <= b.end_date AND b.start_date <= a.end_date
  UNION ALL
  SELECT 'telemetry_gap_days_detected', '2', CAST(COUNT(*) AS STRING), COUNT(*) = 2
  FROM `driiiportfolio.merchandising_insights.dq_channel_day_gaps`
)
SELECT * FROM checks ORDER BY passed, test_name; 
