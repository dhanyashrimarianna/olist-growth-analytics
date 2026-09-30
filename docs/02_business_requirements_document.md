# 02. Business Requirements Document (BRD)

**Project:** Olist Growth & Retention Analytics
**Version:** 1.0 (draft for stakeholder review)
**Author:** Business Analyst
**Sponsor:** Head of Growth (fictional)
**Status:** Simulated engagement on the public Olist dataset. Company context is fictional; data is real.

---

## 1. Purpose

Define the business need, scope, measures of success and requirements for a project that explains low
repeat-purchase behaviour on the Olist marketplace and recommends product changes to improve it.

## 2. Background

Olist operates a marketplace connecting sellers to customers across Brazil. The dataset covers about
100k orders from 2016 to 2018, with order, payment, delivery, review, product, seller and customer data.

A first-pass query on the loaded data shows:

| Measure | Value | Source |
|---|---|---|
| Unique customers | 96,096 | `dw.dim_customer` |
| Customers with 2+ orders | 2,997 (**3.12%**) | `dw.fact_orders`, grouped by `customer_key` |
| Orders with impossible timestamp order | 189 | `is_timestamp_valid = false` |
| Orders with no review | 768 | `review_score IS NULL` |

> The 3.12% was a **first-pass baseline** (all order statuses, no adjustment for time to return). Phase 2
> refined it: **3.00%** of customers placed 2+ delivered orders, and **1.23%** returned within 90 days
> (see KPI-01 and KPI-02).

## 3. Business problem

Roughly 97 of every 100 customers buy once and never return. Every sale therefore depends on paying
to acquire a new customer, which limits profitable growth.

## 4. Business objectives

| ID | Objective | Measure of success |
|---|---|---|
| BO-1 | Understand what differentiates customers who return from those who do not | Documented, quantified drivers (delivery, review score, category, region, payment method) |
| BO-2 | Quantify the revenue opportunity from better retention | Revenue-at-risk estimate with stated assumptions |
| BO-3 | Recommend and prioritize product changes | Ranked roadmap using RICE, with a PRD for the top item |
| BO-4 | Make the recommendations testable | An A/B test plan with hypothesis, metrics, sample size and decision rule |
| BO-5 | Give stakeholders a standing view of retention health | An executive dashboard on agreed KPIs |

## 5. Scope

### In scope
- Customer, order, delivery, review, payment, product and seller analysis on the Olist dataset
- Funnel analysis: purchase, approval, shipping, delivery, review
- Cohort retention and repeat-purchase analysis
- Drivers of dissatisfaction and non-return
- Product recommendations, RICE prioritization, A/B test design, PRD for the top feature
- Executive dashboard and a small interactive demo

### Out of scope
- Building or deploying the recommended features
- Acquisition and paid marketing analysis (no marketing spend data in the dataset)
- Seller-side profitability
- Causal claims from observational data. Findings show association, and the A/B test is how causality would be established
- Real-time or production data pipelines

## 6. Key performance indicators

All KPIs are computed from the star schema in `sql/02_star_schema.sql`.

| ID | KPI | Definition | Source | Baseline | Target |
|---|---|---|---|---|---|
| KPI-01 | Repeat purchase rate | Customers with 2+ **delivered** orders / customers with 1+ delivered order (orders placed Jan 2017 to Aug 2018) | `dw.fact_orders` | **3.00%** (2,789 of 93,104) | Set in Phase 3 roadmap |
| KPI-02 | 90-day repeat rate | Share of customers placing a second delivered order 1 to 90 days after their first, using only customers observable for a full 90 days; same-day second orders excluded | `dw.v_customer_first_order` | **1.23%** (2.18% counting same-day orders; n = 84,198) | Set in Phase 3 roadmap |
| KPI-03 | On-time delivery rate | Delivered orders delivered on or before the estimated date / delivered orders with valid timestamps | `dw.fact_orders.is_late` | **93.20%** | Guardrail: hold or improve |
| KPI-04 | Average delay (late orders) | Mean of `delay_days` for late orders | `dw.fact_orders.delay_days` | **11.30 days** | Diagnostic |
| KPI-05 | Average review score | Mean `review_score` (latest review per order) | `dw.fact_orders.review_score` | **4.16** | Guardrail: hold or improve |
| KPI-06 | Review score gap | Avg score of on-time orders minus avg score of late orders | `dw.fact_orders` | **2.02 points** (4.29 vs 2.27) | Diagnostic (used to size the delivery problem) |
| KPI-07 | Repeat rate by first-order experience | KPI-02 split by on-time versus late first order | `dw.v_customer_first_order` | **1.25%** on time vs **0.92%** late (p = 0.027) | Diagnostic |
| KPI-08 | Average order value (AOV) | Mean `payment_value` per delivered order | `dw.fact_orders` | **R$ 159.81** | Guardrail (must not fall) |
| KPI-09 | Revenue at risk (illustrative) | Customers with a poor first experience x observed repeat-rate gap x average second-order value | Derived | **about R$ 2.4k** if half the gap were closed (16 customers) | Sizing input for ROI |

Baselines were measured in Phase 2 (see `docs/05_findings.md`). Targets are deliberately not invented: they
are agreed with Finance and Growth, and any figure shown in the roadmap is labelled as an assumption.

## 7. Business requirements

Priority uses MoSCoW: Must, Should, Could.

| ID | Requirement | Objective | Priority |
|---|---|---|---|
| BR-01 | The analysis shall define a customer by `customer_unique_id`, not `customer_id`, because the latter is unique per order | BO-1 | Must |
| BR-02 | The analysis shall report repeat purchase using cohorts observed for the same window, so recent customers are not unfairly counted as non-returning | BO-1 | Must |
| BR-03 | The analysis shall quantify the relationship between delivery performance (late versus on time, delay days) and review score | BO-1 | Must |
| BR-04 | The analysis shall quantify the relationship between the first-order experience and the likelihood of a second order | BO-1 | Must |
| BR-05 | The analysis shall segment retention by product category, customer state and payment type | BO-1 | Should |
| BR-06 | The project shall estimate revenue at risk with all assumptions documented | BO-2 | Must |
| BR-07 | The project shall recommend at least three product changes, each linked to evidence | BO-3 | Must |
| BR-08 | Recommendations shall be prioritized with a RICE score, showing inputs | BO-3 | Must |
| BR-09 | The project shall deliver a PRD for the highest-priority recommendation | BO-3 | Must |
| BR-10 | The project shall provide an A/B test plan: hypothesis, primary and guardrail metrics, sample size, duration, decision rule | BO-4 | Must |
| BR-11 | The project shall provide an executive dashboard showing the KPIs above with filters for time, state and category | BO-5 | Should |
| BR-12 | KPI definitions and SQL shall be documented and reproducible from the repository | BO-5 | Must |
| BR-13 | The project shall provide a lightweight interactive demo of retention insights | BO-5 | Could |

## 8. Data requirements

| ID | Requirement |
|---|---|
| DR-01 | Raw data is loaded unchanged into a `raw` schema; all cleaning is done in the `dw` model |
| DR-02 | Data quality checks run automatically after load, with results reported as PASS, WARN or FAIL |
| DR-03 | Known source issues are documented with their handling (see `docs/data_dictionary.md`) |
| DR-04 | Analysis window is January 2017 to August 2018, because data before and after is sparse |
| DR-05 | Delivery metrics use only delivered orders with valid timestamps |

## 9. Assumptions

1. The dataset is a representative sample of marketplace behaviour for the period.
2. A second order at any time in the window counts as a return, unless a KPI states a specific window.
3. Customers are identified reliably by `customer_unique_id`.
4. Review scores reflect customer satisfaction with the order and delivery, not only the product.
5. Purchases outside Olist (competitors) are invisible, so a customer who does not return may simply have bought elsewhere.

## 10. Constraints

- Public, anonymised data only; no marketing spend, acquisition channel, margin or cost data
- Observational data only; no experiment has been run
- Data ends in 2018, so findings describe the past and need re-validation on current data

## 11. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | Low repeat rate is structural (one-off, high-ticket purchases), so retention features have a low ceiling | High | High | Segment by category, since some categories naturally repurchase more; size the opportunity honestly |
| R-2 | Correlation between late delivery and non-return is mistaken for causation | Medium | High | State limitations in every readout; use the A/B test plan to test causality |
| R-3 | Recent cohorts have had too little time to return, which biases the rate downward | High | Medium | Use fixed-window cohort metrics (BR-02) |
| R-4 | Missing cost and margin data makes ROI shaky | High | Medium | Present ROI as a range with explicit assumptions |
| R-5 | Data quality issues distort delivery metrics | Low | Medium | Exclude invalid timestamps and report counts |

## 12. Dependencies

- Olist dataset available and loaded (done)
- Agreement on KPI definitions with Data/BI and Growth
- Finance input on acceptable incentive cost for the ROI model

## 13. Success criteria

The project succeeds when stakeholders can:
1. State, with numbers, how much retention differs between customers with good and poor first experiences
2. See a ranked list of recommendations with the reasoning behind each
3. Approve or reject an A/B test to validate the top recommendation
4. Track the agreed KPIs in one dashboard

## 14. Traceability matrix

| Business objective | Requirements | Deliverable |
|---|---|---|
| BO-1 | BR-01 to BR-05 | Notebooks (cohorts, delivery and review analysis) |
| BO-2 | BR-06 | Revenue-at-risk model |
| BO-3 | BR-07 to BR-09 | `roadmap/` RICE scoring, PRD |
| BO-4 | BR-10 | `roadmap/` A/B test plan |
| BO-5 | BR-11 to BR-13 | Dashboard, Streamlit demo, documented SQL |

## 15. Approval (simulated)

| Role | Name | Decision | Date |
|---|---|---|---|
| Sponsor, Head of Growth | (fictional) | Pending | |
| Product Manager | (fictional) | Pending | |
| Finance Partner | (fictional) | Pending | |
