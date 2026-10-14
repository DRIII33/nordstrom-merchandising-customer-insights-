# Project AURA: Omnichannel Merchandising Customer Insights

**Which promotions create margin, which only move sales between channels, and which customers respond to them?**

Project AURA is an end-to-end analytics build for a four-channel fashion retailer: Nordstrom Stores, Nordstrom.com, Rack Stores and NordstromRack.com. It runs from raw data through audited SQL models and statistical testing to a 13-page executive dashboard. All data is synthetic (see [Project_Disclaimer.md](Project_Disclaimer.md)).

**Author:** Daniel Rodriguez III
**Built for:** Data Analyst 3, Merchandising Customer Insights
**Stack:** Google BigQuery, Python (pandas, statsmodels, scikit-learn), Looker Studio, GitHub

---

## Results at a glance

Sample: 49,875 orders from 7,945 customers, January 2025 to September 2026, $16.68M net revenue, 45.4% gross margin.

| Question | Answer | Evidence |
| --- | --- | --- |
| Do discounts pay for themselves? | No. A 1-20% markdown in full-line earns $53 less margin per order than full price, and units rise 10% against the 58% needed to break even | Discount-band analysis |
| Do big events add margin? | They add traffic, not margin. The Anniversary Sale lifted orders by about 12 per channel-day, but its margin effect is statistically indistinguishable from zero. Incremental revenue earned 8.6 cents of margin per dollar against 45 cents on average | Difference-in-differences, 2 events |
| Do Clear the Rack events cannibalize full-price sales? | Yes. Across five events Rack channels added $119k of revenue but lost $15k of margin; Nordstrom.com lost $102k of revenue and $48k of margin. Net: +$17k revenue, -$64k margin | Difference-in-differences, 5 events |
| Which channel is healthiest after returns? | Nordstrom Stores (43.4%). Nordstrom.com drops from 47.4% to 37.1% once returns are reversed | Return-adjusted margin |
| Who carries the revenue? | 47% of buyers (core loyalists) generate 81.5% of revenue. Deal seekers are 20% of buyers and 6.6% of revenue | K-means segmentation |
| Where does inventory work hardest? | Beauty earns a 4.20 annualized GMROI; Handbags earn 2.33 despite the highest gross margin | GMROI by category |

**Recommendation:** run a controlled test of Rack-only promotion targeting with a Nordstrom.com holdout, and judge every event on margin dollars against a control group. Details are in [Executive_Memo.md](Executive_Memo.md).

> Results describe simulated data with known built-in effects. They demonstrate the method and its ability to recover those effects, not the performance of any real company.

---

## Start here

| If you are | Read | Time |
| --- | --- | --- |
| An executive or hiring manager | [Executive_Summary.md](Executive_Summary.md), then [Executive_Memo.md](Executive_Memo.md) | 5 minutes |
| Reviewing the dashboard | [Dashboard_Executive_Summary.md](Dashboard_Executive_Summary.md) and the PDF in `docs/` | 5 minutes |
| Checking the analytics | [docs/Methodology_and_Validation.md](docs/Methodology_and_Validation.md) | 10 minutes |
| Looking up a field | [Data_Dictionary.md](Data_Dictionary.md) | As needed |
| Running the code | Quick start below | 30 minutes |

**Live dashboard:** [Looker Studio report]([ADD-PUBLISHED-LINK-HERE](https://datastudio.google.com/s/uEzg37Iw_ZI)) (view only). A PDF export (`docs/`) and page images (`dashboard_pages_images/`) keep the work visible after the cloud tables expire.

---

## How the pipeline works

```
Generate data (Python)  ->  Load to BigQuery  ->  Model with SQL  ->  QA gate  ->  Analyze (Python)  ->  Publish
 5 raw CSVs, seed 42        5 raw tables          stg, dq, dim,        19 tests     elasticity, DiD,      Looker Studio
 ground truth kept out                            fct, mart            must pass    segments, anomalies   GitHub
```

- **Staging** standardizes channel labels, removes duplicates and rejects unusable rows with a stated reason. Every raw row is accounted for: 50,150 raw = 150 duplicates + 125 rejects + 49,875 staged, with zero unexplained.
- **Modeling** builds one fact table at order grain, plus dimensions and dashboard-ready marts.
- **Analysis** estimates price response, promotion incrementality, cannibalization, customer segments and anomalies.
- **Dashboard** tells the story in 13 pages and five sections: where we stand, whether promotions pay, who responds, category and inventory health, and data trust.

## Repository structure

```
nordstrom-merchandising-customer-insights/
├── README.md                         Start here
├── Executive_Summary.md              One-page findings and recommendations
├── Executive_Memo.md                 Decision memo on Clear the Rack targeting
├── Dashboard_Executive_Summary.md    What each dashboard page answers
├── Data_Dictionary.md                Tables, fields and KPI definitions
├── Project_Disclaimer.md             Synthetic data and non-affiliation notice
├── LICENSE
├── requirements.txt
├── .gitignore
├── python/
│   ├── generate_project_data.py      Phase 1: synthetic data with built-in effects
│   ├── load_to_bigquery.py           Phase 2: dataset and raw tables
│   ├── statistical_analysis.py       Phase 3: all statistical analyses
│   └── optional_r_parity.R           Cross-check of the elasticity model in R
├── sql/
│   ├── 01_staging_and_dq.sql         Cleaning, rejects, reconciliation, gap check
│   ├── 02_dimensions.sql             Brand, customer, promotion calendar, date
│   ├── 03_facts.sql                  Order-grain fact table
│   ├── 04_customer_metrics.sql       RFM, repeat rate, first order
│   ├── 05_marts.sql                  Dashboard marts
│   ├── 05b_event_comparison_view.sql Naive vs DiD event view
│   ├── 06_qa_tests.sql               12 pipeline tests
│   └── 07_qa_mart_freshness.sql      7 mart freshness tests
├── notebooks/
│   └── AURA_statistical_analysis.ipynb   Colab notebook (report layer)
├── dashboard_pages_images/           Page1_Executive_Scorecard.png ... Page13_Data_Trust.png
└── docs/
    ├── Methodology_and_Validation.md
    └── AURA_dashboard.pdf
```

## Quick start

**With BigQuery and Looker Studio**

1. Create a Google Cloud project (the code uses `driiiportfolio`) and enable BigQuery.
2. In Colab: `pip install -r requirements.txt`, then run `python/generate_project_data.py`.
3. Run `python/load_to_bigquery.py` to create the dataset `merchandising_insights` and the raw tables.
4. In the BigQuery console run `sql/01` to `sql/05`, then `sql/05b`, in order.
5. Run `sql/06_qa_tests.sql` and `sql/07_qa_mart_freshness.sql`. Every row must show `passed = TRUE`.
6. In Colab set `AURA_MODE=bigquery` and run `python/statistical_analysis.py`. It writes the `analysis_` tables.
7. Connect Looker Studio to the marts and analysis tables as described in [Dashboard_Executive_Summary.md](Dashboard_Executive_Summary.md).

**With no cloud account**

1. `pip install -r requirements.txt`
2. `python python/generate_project_data.py`
3. `python python/statistical_analysis.py` (writes `results/*.csv`)

Re-running the SQL rebuilds every table. If you rebuild only part of the pipeline, run the freshness tests in `sql/07`: they catch marts built from an older fact table.

## Quality controls

- **Reconciliation:** raw rows equal duplicates plus rejects plus staged rows, with zero difference.
- **Rejects are explained:** 60 missing customers, 40 negative revenues, 25 impossible discounts.
- **Telemetry gaps:** two zero-order channel-days (NordstromRack.com, March 14 and 15, 2026) are detected, flagged and excluded from event baselines.
- **Tests:** 12 pipeline tests and 7 freshness tests, all passing.
- **Placebo check:** shifting events 14 days earlier produces no spurious effect.

## Limitations

- Every effect is simulated. The project shows that the method recovers known truth, not how any real retailer behaves.
- Elasticity estimates are attenuated because each simulated order has at least one unit. Compare their ranking, not their size.
- Discount-band comparisons mix different shoppers and items, so they are descriptive. The difference-in-differences results carry the causal evidence.
- Black Friday ran in all four channels, so there is no untreated comparison and it is excluded from incrementality.
- Rule-based RFM segments have ties at score cut points, so segment counts can shift slightly between rebuilds. See [docs/Methodology_and_Validation.md](docs/Methodology_and_Validation.md).
- BigQuery sandbox tables expire after 60 days. Re-run the SQL or enable billing to keep them.

## Skills demonstrated

| Role requirement | Where it shows up |
| --- | --- |
| Expert BigQuery SQL | Window functions, `QUALIFY`, clustered fact table, idempotent pipeline |
| Statistical modeling in Python | Poisson elasticity, Welch tests, pooled difference-in-differences, K-means |
| Experiment design | Control channels, placebo test, holdout test proposal |
| Retail economics | GMROI, markdown break-even, return-adjusted margin, cannibalization |
| Data quality | Reconciliation, rejects table, anomaly and completeness checks |
| Executive communication | Decision memo, answer-first dashboard pages, quantified recommendation |

## License

MIT. See [LICENSE](LICENSE).
