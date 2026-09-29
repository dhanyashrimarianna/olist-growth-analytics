# Olist Growth & Retention Analytics: From Requirements to Recommendations

An end-to-end business analysis project on the public Olist Brazilian e-commerce dataset
(~100k orders, 2016 to 2018). I play a Business Analyst embedded in a product team, and the
stakeholder asks:

> **"Why are repeat purchases so low, and what should we build to fix it?"**

The project covers the full loop: requirements, data modeling, analysis, product recommendations,
and experiment design.

| Phase | What I did | Where |
|---|---|---|
| 1. Business analysis | Stakeholder map, BRD, KPIs, user stories, journey/process flow | `docs/` |
| 2. Data & analytics | PostgreSQL star schema, funnel, cohort retention, churn drivers, dashboard | `sql/`, `notebooks/`, `dashboard/` |
| 3. Product management | RICE-scored roadmap, A/B test plan, PRD for the top feature | `roadmap/`, `docs/` |

## Key findings

_To be filled in after the analysis is run on the real dataset (Phase 2). No numbers are
claimed until they are computed and reproducible from this repo._

## Tech stack

PostgreSQL 16 (star schema, CTEs, window functions) · Python (pandas, SciPy, statsmodels) ·
Power BI / Tableau · Streamlit · Git

## Repository structure

```
olist-growth-analytics/
├── README.md
├── docs/                  data dictionary, BRD, user stories, PRD, process flows
├── data/
│   ├── raw/               (git-ignored) Olist CSVs from Kaggle
│   └── sample/            tiny synthetic data for smoke-testing the pipeline
├── sql/
│   ├── 01_raw_schema.sql          raw layer, 1:1 with the CSVs
│   ├── 02_star_schema.sql         dw layer: dimensions + facts, cleaning rules applied
│   └── 03_data_quality_checks.sql PASS/FAIL checks + known-issue profile
├── scripts/
│   ├── setup_db.sh                create DB, load, model, validate
│   └── make_sample_data.py        synthetic Olist-shaped data
├── notebooks/             EDA, cohorts, churn drivers
├── dashboard/             Power BI/Tableau file + screenshots
├── app/                   Streamlit demo
└── roadmap/               RICE scoring, A/B test plan
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

`setup_db.sh` ends by running `sql/03_data_quality_checks.sql`, which should print PASS on every check.

## Progress

- [x] Repo skeleton, data dictionary, PostgreSQL schema, star schema, data quality checks
- [ ] Phase 1: BRD, stakeholder map, user stories, process flow
- [ ] Phase 2: funnel, cohort retention, churn drivers, dashboard, Streamlit app
- [ ] Phase 3: RICE roadmap, A/B test plan, PRD
- [ ] Fill in key findings above

## Data source and licence

Olist Brazilian E-Commerce Public Dataset, Kaggle, CC BY-NC-SA 4.0. Raw data is not redistributed here.
