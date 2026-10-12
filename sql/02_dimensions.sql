CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.dim_brand` AS
SELECT brand_id, brand_name, merchandise_category, price_tier
FROM `driiiportfolio.merchandising_insights.raw_brands`;

CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.dim_customer` AS
SELECT customer_id, signup_date, home_channel, loyalty_tier
FROM `driiiportfolio.merchandising_insights.raw_customers`;

-- One row per event x channel. Events never overlap within a channel (tested in 06).
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.dim_promo_event` AS
SELECT event_id, event_name, start_date, end_date, sales_channel,
       DATE_DIFF(end_date, start_date, DAY) + 1 AS event_days,
       discount_options
FROM `driiiportfolio.merchandising_insights.raw_promo_calendar`;

CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.dim_date` AS
SELECT
  d AS transaction_date,
  DATE_TRUNC(d, MONTH)              AS month_start,
  EXTRACT(YEAR FROM d)              AS calendar_year,
  EXTRACT(QUARTER FROM d)           AS calendar_quarter,
  FORMAT_DATE('%A', d)              AS day_name,
  EXTRACT(DAYOFWEEK FROM d) IN (1, 7) AS is_weekend,
  EXISTS (
    SELECT 1 FROM `driiiportfolio.merchandising_insights.dim_promo_event` e
    WHERE d BETWEEN e.start_date AND e.end_date
  )                                 AS is_any_promo_day
FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2026-09-30')) AS d;
