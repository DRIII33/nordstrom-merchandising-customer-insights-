# Executive Summary: Project AURA

**Bottom line:** Promotions in this retailer's four channels create traffic and revenue, but most do not create margin. The largest leak is Clear the Rack, which adds $17k of revenue and loses $64k of gross margin once it pulls sales away from Nordstrom.com. A controlled targeting test is the next step.

*All figures come from a synthetic dataset with known built-in effects. See the note at the end.*

## The business at a glance

| Measure | Value |
| --- | --- |
| Orders / buying customers | 49,875 / 7,945 |
| Net revenue | $16.68M |
| Gross margin | 45.4% (38.6% after reversing returns) |
| Average order value | $334.49 |
| Share of orders returned | 15.5% |
| Annualized GMROI | 2.79 |
| Markdown dollars | $2.13M (26.2% of revenue is sold on promotion) |

## What we found

**1. Markdowns cost more margin than they earn back in volume.**
In full-line channels, margin per order falls from $177 at full price to $124 at 1-20% off and $79 at 21-30% off. Units rise 10% and 18% in those bands, against 58% and 164% needed to break even. In Rack at 41-50% off, margin is 9.6% of revenue.
*So what:* discount depth is a margin decision, not just a volume lever.

**2. Big sales add traffic, not margin.**
The Anniversary Sale added about 12 orders and $2.7k of revenue per channel-day (95% interval for orders: 10 to 14), but its margin effect (+$233 per channel-day, interval -$203 to +$669) cannot be told apart from zero. Each incremental revenue dollar earned 8.6 cents of margin, against 45 cents on average.
*So what:* judge events on margin dollars against a control group, not on sales growth.

**3. Clear the Rack cannibalizes full-price digital sales.**
Over five events, Rack channels gained $119k of revenue and lost $15k of margin. Nordstrom.com lost about 3.8 orders a day (interval 1.3 to 6.4, roughly 17% of its volume): 212 orders, $102k of revenue and $48k of margin. Net result: +$17k revenue and -$64k margin. Cannibalization is about 76% of the margin loss.
*So what:* the event pays for itself in neither revenue nor margin unless exposure to Nordstrom.com shoppers is controlled.

**4. Returns reverse the channel ranking.**
Nordstrom.com earns 47.4% gross margin, but 21.7% of its orders are returned, leaving 37.1% after returns. Nordstrom Stores keeps 43.4%.
*So what:* scorecards should show return-adjusted margin next to gross margin.

**5. A small group carries the revenue.**
Core loyalists are 47% of buyers and 81.5% of revenue. Deal seekers are 20% of buyers, place about 75% of their orders on promotion, and generate 6.6% of revenue.
*So what:* blanket category markdowns subsidize a segment that adds little revenue.

**6. Inventory productivity depends on the category.**
Annualized GMROI is 4.20 in Beauty and 2.33 in Handbags, yet gross margin is similar (44.4% to 45.8%). The gap comes from inventory turns (5.26 versus 2.76).
*So what:* buying and markdown plans should be set by turns as well as margin rate.

## Recommendations

| # | Action | Measure of success |
| --- | --- | --- |
| 1 | Test Rack-only targeting for Clear the Rack, with a randomized Nordstrom.com holdout | Nordstrom.com orders stay within 5% of baseline; event margin no worse than -$3.0k per event (today about -$12.7k) |
| 2 | Hold full-line markdowns at 20% or less until the test reports | Margin per order and event margin tracked against a control |
| 3 | Add return-adjusted margin to the standard merchandising scorecard | Scorecard shows both margins for every channel |
| 4 | Aim promotions at deal-seeker customers rather than whole categories | Promotion revenue share and margin per promoted order |
| 5 | Reconcile data on every release and alert on empty channel-days | Reconciliation difference stays at zero |

Full reasoning, options and test design are in [Executive_Memo.md](Executive_Memo.md).

## How much to trust this

- **What is solid:** the estimates recover effects that were built into the data (cannibalization, event traffic lift, price-response ranking), and a placebo test shows no false effects.
- **What is limited:** Anniversary margin and Rack-channel margin effects are not statistically clear on their own. Black Friday could not be analyzed because it ran in every channel. Customer segments recover price sensitivity only partly.
- **What it is not:** evidence about any real company. It shows the method and the decisions it would support.

Method and validation: [docs/Methodology_and_Validation.md](docs/Methodology_and_Validation.md). Dashboard: [Dashboard_Executive_Summary.md](Dashboard_Executive_Summary.md).
