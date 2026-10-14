# Methodology and Validation

This note explains how each result was produced, how the data was checked, and where the results stop being reliable. It is written for analysts and reviewers; the executive documents summarize the conclusions.

## 1. Why synthetic data with known effects

Real retail data cannot show whether an analysis method works, because the true effect is unknown. The generator (`python/generate_project_data.py`, seed 42) builds the effects in, so each estimate can be compared with the truth.

| Built-in mechanism | Value in the generator | Recovered by |
| --- | --- | --- |
| Price response by category | Beauty 1.9, Shoes 1.5, Home 1.3, Apparel 1.1, Handbags 0.7 (scaled by brand tier) | Poisson elasticity model |
| Event traffic lift | Anniversary 1.5x, Clear the Rack 1.5x, Half-Yearly 1.35x, Black Friday 1.8x | Difference-in-differences |
| Cannibalization | Nordstrom.com order volume x0.85 on every Clear the Rack day | Difference-in-differences |
| Price-sensitive customers | 25% high, 45% mid, 30% low sensitivity | Promo-affinity clusters |
| Cost structure | Rack cost ratio 0.45 vs 0.50 full-line; Rack inventory turns 1.7x faster | Margin and GMROI by channel |
| Returns | 8% Stores, 22% Nordstrom.com, 10% Rack Stores, 24% NordstromRack.com; +6 points above 40% discount | Return-adjusted margin |
| Telemetry outage | Zero NordstromRack.com orders on March 14 and 15, 2026 | Channel-day completeness check |
| Dirty rows | 150 duplicates, 60 missing customers, 40 negative revenues, 25 impossible discounts, 80 inconsistent labels | Staging rules and reject table |

The 45% digital share of revenue is an input to the simulation (channel weights 30% and 15%), not a finding.

## 2. Analyses

| Question | Method | Why it is appropriate |
| --- | --- | --- |
| How responsive is demand to price? | Poisson regression of units on log(1 - discount), log list price, channel and month effects, by category; robust (HC3) standard errors | Units are counts; month effects absorb seasonality; list price is controlled so the discount term is the price response |
| Does a discount repay its margin in volume? | Margin per order by discount band with a Welch t-test against the full-price band, plus the unit lift each band needs to break even | Shows the trade-off in dollars |
| Do events add margin? | Difference-in-differences per event on daily orders, revenue and margin | Untreated channels set the seasonal baseline |
| Do Rack events cannibalize Nordstrom.com? | Nordstrom.com versus Nordstrom Stores around each Clear the Rack event; pooled regression with robust errors | Nordstrom Stores is untouched by Rack events, so it is a clean control |
| Who responds to promotions? | K-means on log recency, log frequency, log spend and promo share; cluster count chosen by silhouette (3) | Separates value from price sensitivity |
| What is unusual? | Rolling median and MAD z-scores on daily revenue, plus a channel-day completeness check | Separates promo spikes from unexplained moves and missing data |

**Baseline rule.** The baseline window is the 28 days before an event, excluding any day inside another event and any telemetry-gap day. Without this rule, the Half-Yearly Sale baseline would include Black Friday, and the March outage would distort the April baseline.

**Control choice.** Anniversary and Half-Yearly sales use the Rack channels as controls. Clear the Rack uses Nordstrom Stores as the control, because Rack channels cannot control for an event that Nordstrom.com is exposed to. Black Friday ran in all four channels, so no untreated channel exists and it is excluded.

**Placebo test.** Shifting every Clear the Rack event 14 days earlier gives a margin effect of +$113 per channel-day (interval -$356 to +$582), so the design shows no spurious effect.

## 3. Results versus built-in truth

| Result | Estimate | Truth | Verdict |
| --- | --- | --- | --- |
| Elasticity ranking | Beauty -0.95, Shoes -0.65, Home -0.60, Apparel -0.46, Handbags -0.32 | 1.9, 1.5, 1.3, 1.1, 0.7 | Rank recovered exactly; size attenuated (see limits) |
| Multicollinearity | VIF 1.0 to 1.5 | n/a | No concern |
| Anniversary Sale | +12.1 orders per channel-day (10.1 to 14.2); margin +$233 (-$203 to +$669) | Lift 1.5x | Traffic confirmed; margin not distinguishable from zero |
| Cannibalization | -3.85 orders per day (-6.39 to -1.31), about -17% | -15% | Recovered |
| Customer segments | Deal seekers: 44% truly high-sensitivity vs 25% overall | 25% base rate | Partly recovered |
| 30-day repeat rate | 38.3% full-line, 38.1% off-price | No format effect | Correctly shows no difference |

## 4. Data quality controls

| Control | Result |
| --- | --- |
| Row reconciliation | 50,150 raw = 150 duplicates + 125 rejects + 49,875 staged; unexplained difference 0 |
| Rejects are explained | missing_customer_id 60, negative_net_revenue 40, impossible_discount 25 |
| Duplicate IDs in staged data | 0 |
| Fact rows equal staged rows (no join fan-out) | 49,875 = 49,875 |
| Mart net revenue equals staged net revenue | Within $0.01 |
| Margin identity (net revenue - cost - margin) | Within rounding ($1.32 on $7.6M) |
| Telemetry gaps | 2 channel-days detected |
| Freshness tests | Customers, mart revenue totals, event lifts and view rows all reconcile after any rebuild |

`sql/06_qa_tests.sql` holds 12 tests; `sql/07_qa_mart_freshness.sql` holds 7. Both must show `passed = TRUE` before analysis or publishing. The freshness tests exist because marts built before the fact table was last rebuilt otherwise pass silently.

## 5. Dashboard validation

Each of the five dashboard pages was checked tile by tile against values recomputed from the order-level fact table and the analysis tables: 202 expected values covering every number named in the build instructions. Percentages match within 0.06 points, dollar amounts within 1.5% (compact formats), counts exactly.

## 6. Limitations

- **Simulated effects.** Results show that the method recovers known truth, not how any real retailer behaves.
- **Elasticity size.** Every simulated order has at least one unit, which biases the estimates toward zero. Use the ranking; do not call any category inelastic.
- **Discount bands are descriptive.** They compare different shoppers and items. The difference-in-differences results carry the causal evidence.
- **Small bands.** The Off-price 1-20% band has 170 orders.
- **Black Friday** has no control group and is excluded.
- **Rack-channel margin.** The margin effect on Rack channels (-$135 per channel-day) has an interval spanning zero. The case against Clear the Rack rests mainly on the statistically clear cannibalization of Nordstrom.com.
- **Rule-based RFM ties.** Frequency scores split customers who have the same order count (for example 3 orders or 6 orders) arbitrarily, so a rebuild can move about 10 customers between segments. Adding a `customer_id` tie-breaker to the `NTILE` ordering in `sql/04_customer_metrics.sql` makes the result repeatable.
- **Observed value only.** Customer value covers 21 months and is not a forecast.
- **Table expiry.** BigQuery sandbox tables expire after 60 days by default. The PDF export and screenshots in `docs/` preserve the dashboard.

## 7. Reproducibility

Seed 42 and `numpy.random.default_rng` make the data and analysis repeatable. `AURA_MODE=local` reruns the full analysis from the CSVs with no cloud account. Tested with numpy 2.4.4, pandas 3.0.2, statsmodels 0.15.0 and scikit-learn 1.8.0.
