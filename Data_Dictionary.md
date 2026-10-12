| **Field** | **Table** | **Definition** |
|---|---|---|
| `transaction_id` | `raw`, `stg`, `fct` | One order. Unique after deduplication |
| `customer_id` | `raw`, `stg`, `fct` | Buyer; rows without one are rejected |
| `sales_channel` | `stg`, `fct` | One of four standard box names |
| `box_format` | `fct` | Full-line or Off-price |
| `discount_percentage` | `raw`, `fct` | Share off list price, valid range 0 to 0.8 |
| `markdown_dollars` | `fct` | Gross revenue minus net revenue |
| `gross_margin` | `raw`, `fct` | Net revenue minus cost of goods sold |
| `return_adjusted_gross_margin` | `fct` | Zero if the order was returned, else gross margin |
| `event_id`, `event_name` | `fct` | Promotion active for that channel and date, if any |
| `days_to_next_order` | `fct` | Days until the same customer's next order; empty for the last order |
| `avg_inventory_cost` | `raw_inventory_monthly`, `mart` | Average inventory at cost for the month, channel and category |
| `gmroi_monthly` | `mart` | Gross margin divided by average inventory at cost for that month |
