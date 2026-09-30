# Olist Growth & Retention Analytics: From Requirements to Recommendations

An end-to-end business analysis project on the public Olist Brazilian e-commerce dataset
(~100k orders, 2016 to 2018). I play a Business Analyst embedded in a product team, and the
stakeholder asks:

> **"Why are repeat purchases so low, and what should we build to fix it?"**

The project covers the full loop: requirements, data modeling, analysis, product recommendations,
and experiment design.

| Phase | What I did | Where |
|---|---|---|
| 1. Business analysis | Stakeholder map, BRD, KPIs, user stories, journey/process flow | [`docs/`](docs/) |
| 2. Data & analytics | PostgreSQL star schema, funnel, cohort retention, churn drivers, dashboard | `sql/`, `notebooks/`, `dashboard/` |
| 3. Product management | RICE-scored roadmap, A/B test plan, PRD for the top feature | `roadmap/`, `docs/` |

## Key findings

Measured on the full dataset (99,441 orders), orders placed Jan 2017 to Aug 2018. Details and caveats in
[`docs/05_findings.md`](docs/05_findings.md); raw output in [`reports/summary.md`](reports/summary.md).

- **Repeat purchase is rare.** 3.0% of customers (2,789 of 93,104) ever placed a second delivered order;
  1.23% did so within 90 days.
- **The funnel is healthy up to delivery** (97.1% of orders delivered). The leak is after the first order.
- **Late delivery sharply lowers satisfaction.** Average review 2.27 for late orders versus 4.29 on time;
  62.4% of late orders get a 1 to 2 star review versus 9.2%. It gets worse with delay: 1.73 average when 8+
  days late.
- **A bad first delivery is linked to a lower return rate, but the gap is small:** 0.92% versus 1.25%
  (about a quarter lower, p = 0.027).
- **Category matters more than delivery.** Repeat rate ranges from 0.80% (computers_accessories) to 1.75%
  (bed_bath_table) among the largest categories.
- **Sizing:** closing half of the delivery-related gap would add roughly 16 returning customers
  (about R$ 2.4k) across the observed cohorts. Delivery is more a satisfaction lever than a growth lever.
- **Initial hypothesis only partly supported:** delivery problems do not explain most of the low repeat
  rate. The roadmap therefore weights timed, category-aware second-order nudges alongside delay handling.

All results are associations from observational data, not proven causes; the A/B test plan is how causality
would be tested.

## Recommendations

Scored with RICE (reproducible: `python scripts/rice_and_sample_size.py`). Full reasoning in
[`roadmap/01_roadmap.md`](roadmap/01_roadmap.md).

| Rank | Feature | RICE | Notes |
|---|---|---|---|
| 1 | Timed, category-aware second-order nudge | 3,491 | Stays first in all sensitivity scenarios; specified in [`docs/06_prd_second_order_nudge.md`](docs/06_prd_second_order_nudge.md) |
| 2 | Service recovery for 1 to 2 star reviews | 308 | Cheap; also the exclusion rule for the nudge |
| 3 | Proactive delay notification | 80 | Large effect on reviews, small on retention |
| 4 | Investigate same-day split orders | 53 | Discovery; may change how repeat is measured |

The test for the top item ([`roadmap/02_ab_test_plan.md`](roadmap/02_ab_test_plan.md)) is sized for a +0.5
point lift in 90-day repeat rate: about 9,100 customers per group and roughly 7 months to read out at the
marketplace's average volume. Retention gains at this scale are modest, so the first version has no discount.

## Tech stack

PostgreSQL 16 (star schema, CTEs, window functions) · Python (pandas, SciPy, statsmodels) ·
Power BI / Tableau · Streamlit · Git

## Repository structure

```
olist-growth-analytics/
├── README.md
├── docs/
│   ├── data_dictionary.md
│   ├── 01_stakeholder_map.md          problem statement, stakeholders, RACI
│   ├── 02_business_requirements_document.md   objectives, KPIs, requirements, risks
│   ├── 03_user_stories.md             12 stories with acceptance criteria
│   └── 04_process_flows.md            customer journey and future-state flows
├── data/
│   ├── raw/               (git-ignored) Olist CSVs from Kaggle
│   └── sample/            tiny synthetic data for smoke-testing the pipeline
├── sql/
│   ├── 01_raw_schema.sql          raw layer, 1:1 with the CSVs
│   ├── 02_star_schema.sql         dw layer: dimensions + facts, cleaning rules applied
│   ├── 03_data_quality_checks.sql PASS/FAIL/WARN checks + known-issue profile
│   ├── 04_analysis_views.sql      one row per customer: first order + did they return
│   └── analysis/                  q01 funnel, q02 KPI baseline, q03 cohort retention,
│                                  q04 delivery vs review, q05 first-order experience,
│                                  q06 segments, q07 second-order value
├── scripts/
│   ├── setup_db.sh                create DB, load, model, validate
│   ├── make_sample_data.py        synthetic Olist-shaped data
│   ├── run_analysis.py            runs the analysis: tables, charts, summary.md
│   └── rice_and_sample_size.py    RICE scoring, sensitivity, A/B sample sizes
├── reports/               analysis output: tables/, figures/, summary.md
├── notebooks/             EDA, cohorts, churn drivers
├── dashboard/             Power BI/Tableau file + screenshots
├── app/                   Streamlit demo
└── roadmap/               01_roadmap.md (RICE), 02_ab_test_plan.md, rice/sample-size CSVs
```

## Data model

```
                    dim_date
                       │
dim_customer ──── fact_orders ────< fact_order_items >──── dim_product
 (per person)      (1 row/order)                     └──── dim_seller
                                                          dim_geo (zip prefix)
```

Design decisions worth noting:

- **Customer grain:** `customer_id` in the source is unique per order, so repeat rate computed on it is
  always 0%. The model keys customers on `customer_unique_id` instead.
- **Reviews:** duplicated in the source, so the latest review per order is kept.
- **Delivery metrics:** computed only for delivered orders whose timestamps are in a sensible order
  (`is_timestamp_valid`).
- `fact_orders` carries `customer_order_seq` and `cohort_month`, so cohort and repeat-purchase queries
  are simple window-free aggregations.

Full column-level documentation and data quality handling: [`docs/data_dictionary.md`](docs/data_dictionary.md).

## Quickstart

```bash
# 1. Get the data (see data/README.md), put the 9 CSVs in data/raw/
# 2. Python deps
pip install -r requirements.txt

# 3. Build the database (needs a local PostgreSQL 14+)
bash scripts/setup_db.sh

# No data yet? Smoke-test the pipeline on synthetic sample data:
python scripts/make_sample_data.py
DATA_DIR=data/sample bash scripts/setup_db.sh
```

`setup_db.sh` ends by running `sql/03_data_quality_checks.sql`. Every check should print PASS, except one
WARN for a known source issue (a few orders marked delivered with no delivery date).

```bash
# 4. Run the analysis (writes tables, charts and summary.md to reports/)
python scripts/run_analysis.py
```

Set `PGPASSWORD` (and `PGUSER`, `PGHOST`, `PGDATABASE` if they differ from the defaults `postgres`,
`localhost`, `olist`) before running.

### Method notes

- **First order / repeat:** a customer's first *delivered* order is their first order. A repeat is a second
  delivered order placed 1 to 90 days later. Same-day second orders are excluded, since they are usually a
  split basket; the alternative is reported alongside.
- **Fair windows:** only customers whose first order is at least 90 days older than the latest order in the
  data are counted, so recent customers are not scored as "lost".
- **Statistics:** rates carry 95% Wilson confidence intervals; group differences use a two-proportion z-test.
- **Causality:** all results are associations from observational data. The A/B test plan in Phase 3 is how a
  causal effect would be measured.

## Progress

- [x] Repo skeleton, data dictionary, PostgreSQL schema, star schema, data quality checks
- [x] Phase 1: stakeholder map, BRD, user stories, process flows
- [x] Phase 2a: analysis SQL and runner (funnel, KPIs, cohorts, delivery vs review, segments)
- [x] Phase 2b: run on real data, interpret results
- [ ] Phase 2c: dashboard, Streamlit app
- [x] Phase 3: RICE roadmap, A/B test plan, PRD
- [x] Key findings above

## Data source and licence

Olist Brazilian E-Commerce Public Dataset, Kaggle, CC BY-NC-SA 4.0. Raw data is not redistributed here.
