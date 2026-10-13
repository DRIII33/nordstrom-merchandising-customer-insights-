WITH checks AS (
  SELECT 'customer_rfm_covers_all_customers' AS test_name,
         CAST((SELECT COUNT(DISTINCT customer_id) FROM `driiiportfolio.merchandising_insights.fct_transactions`) AS STRING) AS expected,
         CAST(COUNT(*) AS STRING) AS actual,
         COUNT(*) = (SELECT COUNT(DISTINCT customer_id) FROM `driiiportfolio.merchandising_insights.fct_transactions`) AS passed
  FROM `driiiportfolio.merchandising_insights.customer_rfm`
  UNION ALL
  SELECT 'rfm_summary_net_equals_fact',
         CAST(ROUND((SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`), 2) AS STRING),
         CAST(ROUND(SUM(net_revenue), 2) AS STRING),
         ABS(SUM(net_revenue) - (SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`)) < 0.01
  FROM `driiiportfolio.merchandising_insights.mart_rfm_segment_summary`
  UNION ALL
  SELECT 'brand_mart_net_equals_fact',
         CAST(ROUND((SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`), 2) AS STRING),
         CAST(ROUND(SUM(net_revenue), 2) AS STRING),
         ABS(SUM(net_revenue) - (SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`)) < 0.01
  FROM `driiiportfolio.merchandising_insights.mart_brand_performance`
  UNION ALL
  SELECT 'health_mart_net_equals_fact',
         CAST(ROUND((SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`), 2) AS STRING),
         CAST(ROUND(SUM(net_revenue), 2) AS STRING),
         ABS(SUM(net_revenue) - (SELECT SUM(net_revenue) FROM `driiiportfolio.merchandising_insights.fct_transactions`)) < 0.01
  FROM `driiiportfolio.merchandising_insights.mart_category_health`
  UNION ALL
  SELECT 'event_mart_null_naive_lifts', '0', CAST(COUNTIF(naive_revenue_lift IS NULL) AS STRING),
         COUNTIF(naive_revenue_lift IS NULL) = 0
  FROM `driiiportfolio.merchandising_insights.mart_event_performance`
  UNION ALL
  SELECT 'segments_cover_all_customers',
         CAST((SELECT COUNT(DISTINCT customer_id) FROM `driiiportfolio.merchandising_insights.fct_transactions`) AS STRING),
         CAST(COUNT(*) AS STRING),
         COUNT(*) = (SELECT COUNT(DISTINCT customer_id) FROM `driiiportfolio.merchandising_insights.fct_transactions`)
  FROM `driiiportfolio.merchandising_insights.analysis_segments`
  UNION ALL
  SELECT 'event_comparison_view_rows', '13', CAST(COUNT(*) AS STRING), COUNT(*) = 13
  FROM `driiiportfolio.merchandising_insights.vw_event_naive_vs_did`
)
SELECT * FROM checks ORDER BY passed, test_name;
