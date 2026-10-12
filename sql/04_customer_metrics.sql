-- RFM scores and rule-based segments
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.customer_rfm` AS
WITH asof AS (
  SELECT DATE_ADD(MAX(transaction_date), INTERVAL 1 DAY) AS asof_date
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
),
c AS (
  SELECT
    customer_id,
    MAX(transaction_date)                 AS last_order_date,
    COUNT(*)                              AS frequency,
    SUM(net_revenue)                      AS monetary,
    SUM(return_adjusted_gross_margin)     AS observed_gross_margin_ltv,
    AVG(is_promotional)                   AS promo_share,
    AVG(discount_percentage)              AS avg_discount
  FROM `driiiportfolio.merchandising_insights.fct_transactions`
  GROUP BY customer_id
),
scored AS (
  SELECT
    c.*,
    DATE_DIFF(asof.asof_date, c.last_order_date, DAY)                                    AS recency_days,
    NTILE(5) OVER (ORDER BY DATE_DIFF(asof.asof_date, c.last_order_date, DAY) DESC)      AS r_score,
    NTILE(5) OVER (ORDER BY c.frequency)                                                 AS f_score,
    NTILE(5) OVER (ORDER BY c.monetary)                                                  AS m_score
  FROM c CROSS JOIN asof
)
SELECT
  s.*,
  d.loyalty_tier,
  d.home_channel,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
    WHEN f_score >= 4                  THEN 'Loyal, cooling'
    WHEN r_score >= 4                  THEN 'Promising'
    WHEN r_score <= 2 AND f_score >= 3 THEN 'At risk'
    ELSE 'Hibernating'
  END AS rfm_segment
FROM scored s
LEFT JOIN `driiiportfolio.merchandising_insights.dim_customer` d USING (customer_id);

-- 30-day repeat purchase rate
CREATE OR REPLACE VIEW `driiiportfolio.merchandising_insights.metric_repeat_rate_30d` AS
SELECT
  month_start,
  box_format,
  COUNT(*)                                                    AS orders_observable,
  COUNTIF(days_to_next_order <= 30)                           AS orders_repeat_30d,
  SAFE_DIVIDE(COUNTIF(days_to_next_order <= 30), COUNT(*))    AS repeat_rate_30d
FROM `driiiportfolio.merchandising_insights.fct_transactions`
WHERE transaction_date <= DATE_SUB(
  (SELECT MAX(transaction_date) FROM `driiiportfolio.merchandising_insights.fct_transactions`), INTERVAL 30 DAY)
GROUP BY 1, 2;

-- First observed order per customer
CREATE OR REPLACE VIEW `driiiportfolio.merchandising_insights.customer_first_order` AS
SELECT customer_id, transaction_date AS first_order_date,
       sales_channel AS first_order_channel, is_promotional AS first_order_on_promo
FROM `driiiportfolio.merchandising_insights.fct_transactions` 
WHERE TRUE
QUALIFY customer_order_seq = 1;
