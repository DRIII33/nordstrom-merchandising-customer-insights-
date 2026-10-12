# Project AURA: Omnichannel Merchandising Customer Insights and Promotional Incrementality Engine

**Author:** Daniel Rodriguez III
**Target role:** Data Analyst 3, Merchandising Customer Insights (Seattle, hybrid)
**Data:** 100% synthetic. No proprietary or confidential information. See Project_Disclaimer.md.

## What this answers
Which promotions create gross margin, which only move revenue between boxes, and which customers respond to them, across four boxes: Nordstrom Stores, Nordstrom.com, Rack Stores and NordstromRack.com.

## Headline results (synthetic data, seed 42)
- Discounts do not pay for themselves per order. Full-line orders at 1-20% off earn $53 less gross margin than full-price orders, and units rise 10% against 58% needed to break even.
- The Anniversary Sale adds about 12 orders per channel-day but its margin effect is not distinguishable from zero. Incremental revenue earned about 8.6 cents of margin per dollar, against 45 cents on average.
- Five Clear the Rack events added $17k of revenue and lost $64k of gross margin. Cannibalization of Nordstrom.com explains $48k (76%) of the loss.
- Digital returns remove about 10 points of margin on Nordstrom.com (47.4% to 37.1%).
- Details: Executive_Summary.md, Executive_Memo.md and the dashboard in docs/.

## Architecture
Google Colab (Python) generates data and runs statistics -> BigQuery (raw, staging, dimensions, facts, marts) -> Looker Studio dashboard -> GitHub.

## Quick start with BigQuery
1. Create a GCP project (the code uses driiiportfolio) and enable BigQuery.
2. In Colab: pip install -r requirements.txt, then run python/generate_project_data.py.
3. Run python/load_to_bigquery.py to create the dataset and raw tables.
4. Run sql/01 to sql/05 in order in the BigQuery console, then sql/06_qa_tests.sql. Every row must show passed = TRUE.
5. In Colab set AURA_MODE=bigquery and run python/statistical_analysis.py.
6. Connect Looker Studio to the mart_ and analysis_ tables (see Dashboard_Executive_Summary.md).

## Quick start with no cloud account
1. pip install -r requirements.txt
2. python python/generate_project_data.py
3. python python/statistical_analysis.py  (writes results/*.csv)

## Method notes and limitations
- Ground truth is built into the simulator, so recovered effects can be checked. Elasticity estimates are attenuated because every order has at least one unit; compare rank order, not size.
- The digital revenue share (45%) is an input to the simulator, not a finding.
- DiD uses untreated channels as controls. Black Friday has none and is excluded.
- Customer segments recover price sensitivity only partly: the deal-seeker cluster holds 44% truly high-sensitivity customers, against 25% overall.
- BigQuery sandbox tables expire after 60 days; rerun the SQL or enable billing. Screenshots in docs/ preserve the dashboard.

## Repository map
python/ analysis code | sql/ pipeline and QA tests | notebooks/ Colab notebook | docs/ dashboard exports
