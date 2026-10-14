# Decision Memo: Clear the Rack Targeting Test

**To:** VP, Omnichannel Merchandising (illustrative recipient)
**From:** Daniel Rodriguez III, Merchandising Customer Insights
**Date:** October 13, 2026
**Decision requested:** Approve a controlled test of Rack-only targeting for the next Clear the Rack event.

*This memo uses synthetic data. It shows how the analysis would support a real decision; it makes no claim about any actual company.*

---

## Recommendation

Run the next Clear the Rack event with promotions aimed at Rack shoppers only, and hold out a random 10% of Nordstrom.com visitors from any Clear the Rack exposure. Measure orders and gross margin against the holdout and against Nordstrom Stores. Decide whether to keep, change or stop the event format from the result.

## Why

Across five past events, Clear the Rack moved revenue but lost margin once its effect on Nordstrom.com is counted.

| Where | Net revenue | Gross margin | Orders |
| --- | --- | --- | --- |
| Rack Stores and NordstromRack.com | +$119.3k | -$15.2k | +613 |
| Nordstrom.com (full price) | -$101.8k | -$48.4k | -212 |
| **Total** | **+$17.5k** | **-$63.6k** | **+401** |

- Nordstrom.com lost about 3.8 orders per day during events (95% interval 1.3 to 6.4), roughly 17% of its normal volume. This effect is statistically clear.
- Cannibalization accounts for about 76% of the margin loss. Deep Rack markdowns account for the rest, but that part is not statistically clear on its own (-$135 per channel-day, interval -$612 to +$341).
- At 41-50% off in Rack, margin is 9.6% of revenue, so extra units cannot repay the markdown (+55% units observed against +1,176% needed).
- Comparing before and after without a control would have hidden this: for two of the five events the naive view shows margin gains where the controlled view shows losses.

## Options

| Option | Net revenue | Gross margin | Main risk |
| --- | --- | --- | --- |
| A. Keep current events | +$17k | -$64k | Cannibalization continues |
| B. Rack-only targeting with Nordstrom.com holdout (recommended) | Up to +$119k | Up to -$15k if cannibalization is removed | Exposure may still leak to other audiences |
| C. Pause Clear the Rack | $0 | $0 | Loses Rack traffic; effect on aged stock cannot be measured here |

Option B's figures are upper bounds that assume cannibalization can be fully removed. The test exists to find out how much of it can.

## Test design

1. **Audience:** send Clear the Rack promotions only to customers who have bought in Rack channels.
2. **Holdout:** randomly assign 10% of Nordstrom.com visitors to a group that sees no Clear the Rack promotion.
3. **Comparison:** exposed vs holdout Nordstrom.com visitors, with Nordstrom Stores as a second comparison group.
4. **Sizing:** confirm the holdout is large enough to detect a 5% change in Nordstrom.com orders before launch.
5. **Duration:** the full event window, plus a 28-day baseline that excludes other events and any data outage.

## Success criteria

| Measure | Today | Target |
| --- | --- | --- |
| Nordstrom.com orders during the event | About 17% below baseline | Within 5% of baseline |
| Event gross margin, per event | About -$12.7k | -$3.0k or better |
| Rack revenue lift | +$119k over five events | Not materially lower |

Stop and revisit if Rack revenue lift falls by more than half while Nordstrom.com does not recover.

## Risks and open questions

- **Spillover:** shoppers can see promotions outside targeted channels. The holdout measures this directly.
- **Inventory:** the data has no inventory age, so this analysis cannot say whether the event clears aged stock. Add that measure before judging Option C.
- **Black Friday:** it ran in all four channels, so it has no control and is not covered here.
- **Generalization:** the numbers come from simulated data with built-in effects. A real test must replace them.

## Next steps

| Step | Owner | Timing |
| --- | --- | --- |
| Confirm holdout size and audience rules | Insights and Marketing | Before the next event is planned |
| Build the test readout in the dashboard (Page 2 pattern) | Insights | Before launch |
| Report results against the success criteria | Insights | Within two weeks of the event ending |
