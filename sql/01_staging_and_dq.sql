-- Typed, standardized, deduplicated staging with an explicit reject reason on every row.
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.stg_all` AS
WITH typed AS (
  SELECT
    NULLIF(TRIM(transaction_id), '')                  AS transaction_id,
    SAFE_CAST(transaction_date AS DATE)               AS transaction_date,
    NULLIF(TRIM(customer_id), '')                     AS customer_id,
    CASE LOWER(TRIM(sales_channel))
      WHEN 'nordstrom stores'    THEN 'Nordstrom Stores'
      WHEN 'nordstrom.com'       THEN 'Nordstrom.com'
      WHEN 'rack stores'         THEN 'Rack Stores'
      WHEN 'nordstromrack.com'   THEN 'NordstromRack.com'
    END                                               AS sales_channel,
    TRIM(merchandise_category)                        AS merchandise_category,
    TRIM(brand_id)                                    AS brand_id,
    SAFE_CAST(units_sold AS INT64)                    AS units_sold,
    SAFE_CAST(unit_price AS FLOAT64)                  AS unit_price,
    SAFE_CAST(discount_percentage AS FLOAT64)         AS discount_percentage,
    SAFE_CAST(gross_revenue AS FLOAT64)               AS gross_revenue,
    SAFE_CAST(net_revenue AS FLOAT64)                 AS net_revenue,
    SAFE_CAST(cost_of_goods_sold AS FLOAT64)          AS cost_of_goods_sold,
    SAFE_CAST(gross_margin AS FLOAT64)                AS gross_margin,
    SAFE_CAST(is_returned AS INT64)                   AS is_returned,
    SAFE_CAST(returned_net_revenue AS FLOAT64)        AS returned_net_revenue
  FROM `driiiportfolio.merchandising_insights.raw_transactions`
)
SELECT
  *,
  CASE
    WHEN transaction_id IS NULL                                   THEN 'missing_transaction_id'
    WHEN customer_id IS NULL                                      THEN 'missing_customer_id'
    WHEN transaction_date IS NULL                                 THEN 'bad_date'
    WHEN sales_channel IS NULL                                    THEN 'unknown_channel'
    WHEN net_revenue IS NULL                                      THEN 'missing_revenue'
    WHEN net_revenue < 0                                          THEN 'negative_net_revenue'
    WHEN discount_percentage IS NULL
         OR discount_percentage < 0 OR discount_percentage > 0.8  THEN 'impossible_discount'
  END AS reject_reason
FROM typed
WHERE TRUE
QUALIFY ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_date) = 1;

CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.stg_transactions` AS
SELECT * EXCEPT (reject_reason)
FROM `driiiportfolio.merchandising_insights.stg_all`
WHERE reject_reason IS NULL;

CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.dq_rejects` AS
SELECT *
FROM `driiiportfolio.merchandising_insights.stg_all`
WHERE reject_reason IS NOT NULL;

-- Reconciliation: every raw row must be accounted for. unexplained_difference must be 0.
CREATE OR REPLACE VIEW `driiiportfolio.merchandising_insights.dq_reconciliation` AS
WITH c AS (
  SELECT
    (SELECT COUNT(*) FROM `driiiportfolio.merchandising_insights.raw_transactions`) AS raw_rows,
    (SELECT COUNT(*) FROM `driiiportfolio.merchandising_insights.stg_all`)           AS deduped_rows,
    (SELECT COUNT(*) FROM `driiiportfolio.merchandising_insights.dq_rejects`)        AS rejected_rows,
    (SELECT COUNT(*) FROM `driiiportfolio.merchandising_insights.stg_transactions`)  AS staged_rows
)
SELECT raw_rows, raw_rows - deduped_rows AS duplicates_removed, rejected_rows, staged_rows,
       raw_rows - (raw_rows - deduped_rows) - rejected_rows - staged_rows AS unexplained_difference
FROM c;

-- Telemetry completeness: channel-days with no orders at all.
CREATE OR REPLACE VIEW `driiiportfolio.merchandising_insights.dq_channel_day_gaps` AS
WITH grid AS (
  SELECT d AS transaction_date, ch AS sales_channel
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2026-09-30')) AS d
  CROSS JOIN UNNEST(['Nordstrom Stores', 'Nordstrom.com', 'Rack Stores', 'NordstromRack.com']) AS ch
),
actual AS (
  SELECT transaction_date, sales_channel, COUNT(*) AS orders
  FROM `driiiportfolio.merchandising_insights.stg_transactions`
  GROUP BY 1, 2
)
SELECT g.transaction_date, g.sales_channel
FROM grid g
LEFT JOIN actual a ON g.transaction_date = a.transaction_date AND g.sales_channel = a.sales_channel
WHERE a.orders IS NULL;
