-- Table recreated as a clean standard table to completely bypass BigQuery Sandbox partition constraints.
CREATE OR REPLACE TABLE `driiiportfolio.merchandising_insights.fct_transactions` 
CLUSTER BY sales_channel, merchandise_category AS
WITH base AS (
  SELECT
    t.transaction_id,
    t.transaction_date,
    DATE_TRUNC(t.transaction_date, MONTH)                                                 AS month_start,
    t.customer_id,
    t.sales_channel,
    IF(t.sales_channel IN ('Rack Stores', 'NordstromRack.com'), 'Off-price', 'Full-line') AS box_format,
    IF(t.sales_channel IN ('Nordstrom.com', 'NordstromRack.com'), 'Digital', 'Stores')    AS channel_type,
    t.merchandise_category,
    t.brand_id,
    b.price_tier,
    t.units_sold,
    t.unit_price,
    IF(t.discount_percentage > 0, 1, 0)                                                  AS is_promotional,
    t.discount_percentage,
    t.gross_revenue,
    t.net_revenue,
    t.gross_revenue - t.net_revenue                                                      AS markdown_dollars,
    t.cost_of_goods_sold,
    t.gross_margin,
    t.is_returned,
    t.returned_net_revenue,
    IF(t.is_returned = 1, 0, t.gross_margin)                                             AS return_adjusted_gross_margin,
    e.event_id,
    e.event_name
  FROM `driiiportfolio.merchandising_insights.stg_transactions` t
  LEFT JOIN `driiiportfolio.merchandising_insights.dim_brand` b ON t.brand_id = b.brand_id
  LEFT JOIN `driiiportfolio.merchandising_insights.dim_promo_event` e
    ON t.sales_channel = e.sales_channel
   AND t.transaction_date BETWEEN e.start_date AND e.end_date
)
SELECT
  base.*,
  ROW_NUMBER() OVER w                                              AS customer_order_seq,
  LEAD(transaction_date) OVER w                                    AS next_order_date,
  DATE_DIFF(LEAD(transaction_date) OVER w, transaction_date, DAY)  AS days_to_next_order
FROM base
WINDOW w AS (PARTITION BY customer_id ORDER BY transaction_date, transaction_id);
