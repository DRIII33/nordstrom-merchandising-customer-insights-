# Dashboard Summary: Looker Studio

**Purpose:** give merchandising leaders one view of promotions, margin, customers and data quality across four channels, with every number reconciled to the source data.
**Pages:** five, each answering one question.
**Live report:** [Looker Studio](ADD-PUBLISHED-LINK-HERE) (view only) · [PDF export](docs/AURA_dashboard.pdf)

Figures below are from the synthetic dataset, January 2025 to September 2026.

---

## Page 1: Executive overview
**Question:** Where do we stand?
**Headline:** Net revenue is $16.68M at a 45.4% gross margin, which falls to 38.6% once returns are reversed.
**Shows:** revenue, margin, GMROI, order value and return rate; performance by channel; monthly revenue and margin by format; the promotion calendar.
**Read it for:** Off-price channels earn about 5.7 points less margin (41.6% vs 47.3%) on 33% of revenue. Margin dips in the months of the Anniversary Sale and Clear the Rack events.

![Page 1](docs/dashboard_page1.png)

## Page 2: Promotion effectiveness
**Question:** Which promotions pay?
**Headline:** Clear the Rack events added $17k of revenue but lost $64k of gross margin once Nordstrom.com cannibalization is counted.
**Shows:** margin and revenue effect by event family; naive versus controlled lift by event; pooled estimates with confidence intervals; margin per order and break-even volume by discount band.
**Read it for:** the controlled (difference-in-differences) numbers carry the causal evidence. The discount-band table is descriptive.

![Page 2](docs/dashboard_page2.png)

## Page 3: Customer insights
**Question:** Who responds to promotions, and who carries revenue?
**Headline:** Core loyalists are 47% of buyers and 81.5% of revenue; deal seekers are 20% of buyers and 6.6% of revenue.
**Shows:** two segmentations kept separate (statistical clusters and rule-based RFM); 30-day repeat purchase rate; loyalty tier mix.
**Read it for:** about 38% of orders are followed by another within 30 days in both formats. The 300 Icon members are 3.8% of buyers and 15.6% of revenue.

![Page 3](docs/dashboard_page3.png)

## Page 4: Category and inventory health
**Question:** What should we buy and mark down?
**Headline:** Beauty earns the most per inventory dollar (GMROI 4.20); Handbags turn slowest (2.76 turns, GMROI 2.33) despite the highest margin.
**Shows:** a Category Health Index across ten channel-format and category rows; GMROI by category and format; category productivity; price response by category; margin by brand tier.
**Read it for:** the index is a percentile rank across those ten rows, so it orders them but is not an absolute score. Price-response estimates are attenuated; read the ranking, not the size.

![Page 4](docs/dashboard_page4.png)

## Page 5: Data trust
**Question:** Can I rely on these numbers?
**Headline:** Every raw row is accounted for: 50,150 = 150 duplicates + 125 rejects + 49,875 staged, with zero unexplained.
**Shows:** reconciliation; rejected rows by reason; channel-days with no orders; revenue anomaly flags.
**Read it for:** two NordstromRack.com days (March 14 and 15, 2026) have no orders and are treated as telemetry gaps. Four of five anomaly flags fall inside promotion windows; one (April 6, 2025) needs analyst review.

![Page 5](docs/dashboard_page5.png)

---

## Metric definitions

| Metric | Definition |
| --- | --- |
| Net revenue | Revenue after discounts |
| Gross margin | Net revenue minus cost of goods sold; shown in dollars and as a percent of net revenue |
| Return-adjusted margin | Gross margin after setting margin to zero on returned orders, as a percent of net revenue |
| GMROI (annualized) | Gross margin divided by average inventory at cost, times 12 |
| Inventory turns (annualized) | Cost of goods sold divided by average inventory at cost, times 12 |
| AOV | Net revenue divided by orders |
| Return rate | Returned orders divided by orders |
| Promo revenue share | Net revenue from discounted orders divided by net revenue |
| 30-day repeat rate | Share of orders followed by another order from the same customer within 30 days |
| Category Health Index (0 to 100) | Percentile-rank blend: 35% GMROI, 25% return-adjusted margin, 20% repeat rate, 20% low promo dependence |

All ratios are calculated from summed numerators and denominators, never from averages of stored ratios.

## How to read the dashboard

- The date control filters the tiles built on monthly performance data: all of Page 1, plus the GMROI and category productivity tiles on Page 4. Analysis tiles (Pages 2, 3 and 5, and the other Page 4 tiles) show the whole period.
- Percentages are shown to one decimal place; dollar values in compact form where noted.
- Event effects are per channel-day unless a total is stated.

## Data and refresh

- Source: BigQuery dataset `merchandising_insights`; the report reads marts and analysis tables only.
- Refresh: after any rebuild, run `sql/06` and `sql/07`, then refresh the report data.
- Access: view only; viewers need no database permissions.

## Validation

Each tile was checked against values recomputed from the order-level fact table and the analysis tables, with 202 expected values across the five pages. See [docs/Methodology_and_Validation.md](docs/Methodology_and_Validation.md).

