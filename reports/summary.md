# Analysis results (auto-generated)

_Generated 2026-09-29 by `scripts/run_analysis.py` from a database with **99,441 orders**, latest purchase date **2018-10-17**._

_All results are associations from observational data. They show how groups differ, not what caused the difference. Confidence intervals are 95% Wilson intervals._

## KPI baseline

| metric | value |
|---|---|
| KPI-01 customers with a delivered order | 93,104 |
| KPI-01 customers with 2+ delivered orders | 2,789 |
| KPI-01 repeat purchase rate (pct) | 3 |
| KPI-02 cohort customers observable for 90 days | 84,198 |
| KPI-02 90-day repeat rate (pct), excl same-day | 1.23 |
| KPI-02 90-day repeat rate (pct), incl same-day | 2.18 |
| KPI-03 on-time delivery rate (pct) | 93.20 |
| KPI-04 avg delay of late orders (days) | 11.30 |
| KPI-05 avg review score | 4.16 |
| KPI-06 review gap, on-time minus late | 2.02 |
| KPI-08 average order value (BRL) | 159.81 |

## Order funnel (Jan 2017 to Aug 2018)

| stage | orders | pct_of_placed | pct_of_previous |
|---|---|---|---|
| Orders placed | 99,092 | 100 | n/a |
| Payment approved | 98,957 | 99.86 | 99.86 |
| Handed to carrier | 97,376 | 98.27 | 98.40 |
| Delivered | 96,211 | 97.09 | 98.80 |
| Reviewed | 95,568 | 96.44 | 99.33 |

## Monthly retention curve (all eligible cohorts pooled)

Share of a cohort placing a delivered order in month N after its first order.

| months_since | cohorts | customers | active | retention_pct |
|---|---|---|---|---|
| 1 | 20 | 93,094 | 420 | 0.45 |
| 2 | 19 | 86,950 | 273 | 0.31 |
| 3 | 18 | 81,001 | 192 | 0.24 |
| 4 | 17 | 75,123 | 176 | 0.23 |
| 5 | 16 | 68,617 | 140 | 0.20 |
| 6 | 15 | 62,035 | 128 | 0.21 |
| 7 | 14 | 55,261 | 102 | 0.18 |
| 8 | 13 | 48,973 | 86 | 0.18 |
| 9 | 12 | 42,131 | 59 | 0.14 |
| 10 | 11 | 36,793 | 75 | 0.20 |
| 11 | 10 | 29,733 | 56 | 0.19 |
| 12 | 9 | 25,405 | 36 | 0.14 |

## Delivery outcome vs review score

| bucket | orders | avg_review | pct_1_2_star | pct_5_star |
|---|---|---|---|---|
| On time | 89,001 | 4.29 | 9.24 | 62.29 |
| Late 1-3 days | 1,358 | 3.51 | 25.55 | 36.30 |
| Late 4-7 days | 1,772 | 2.32 | 61.29 | 18.06 |
| Late 8+ days | 3,246 | 1.73 | 78.47 | 7.46 |

On-time orders average **4.29**; late orders average **2.27**. Late orders get a 1 or 2 star review **62.4%** of the time versus **9.2%** for on-time orders.

## 90-day repeat rate by first-order experience

**By delivery**

| delivery_group | customers | repeaters | repeat_rate_pct | ci_low | ci_high |
|---|---|---|---|---|---|
| Late | 5,864 | 54 | 0.92 | 0.71 | 1.20 |
| On time | 78,206 | 979 | 1.25 | 1.18 | 1.33 |
| Unknown | 128 | 1 | 0.78 | 0.14 | 4.29 |

**By review**

| review_group | customers | repeaters | repeat_rate_pct | ci_low | ci_high |
|---|---|---|---|---|---|
| 1-2 stars | 11,016 | 108 | 0.98 | 0.81 | 1.18 |
| 3 stars | 7,052 | 76 | 1.08 | 0.86 | 1.35 |
| 4-5 stars | 65,555 | 844 | 1.29 | 1.20 | 1.38 |
| No review | 575 | 6 | 1.04 | 0.48 | 2.26 |

On-time vs late first orders: difference **0.33 percentage points** (two-proportion z-test: z = 2.22, p = 0.0265).

## 90-day repeat rate by segment

Segments under 100 customers are flagged `low_sample` and excluded from charts.

**Customer state**

| segment | customers | repeaters | repeat_rate_pct | low_sample |
|---|---|---|---|---|
| SP | 34,716 | 472 | 1.36 |  |
| RJ | 10,875 | 139 | 1.28 |  |
| MG | 10,003 | 115 | 1.15 |  |
| RS | 4,737 | 51 | 1.08 |  |
| PR | 4,307 | 35 | 0.81 |  |
| SC | 3,174 | 32 | 1.01 |  |
| BA | 2,886 | 38 | 1.32 |  |
| DF | 1,786 | 21 | 1.18 |  |
| ES | 1,777 | 32 | 1.80 |  |
| GO | 1,735 | 20 | 1.15 |  |
| PE | 1,405 | 13 | 0.93 |  |
| CE | 1,169 | 10 | 0.86 |  |

**Payment type**

| segment | customers | repeaters | repeat_rate_pct | low_sample |
|---|---|---|---|---|
| credit_card | 64,886 | 793 | 1.22 |  |
| boleto | 16,946 | 203 | 1.20 |  |
| voucher | 1,289 | 23 | 1.78 |  |
| debit_card | 1,077 | 15 | 1.39 |  |

**Product category**

| segment | customers | repeaters | repeat_rate_pct | low_sample |
|---|---|---|---|---|
| bed_bath_table | 7,992 | 140 | 1.75 |  |
| health_beauty | 7,339 | 84 | 1.14 |  |
| sports_leisure | 6,592 | 106 | 1.61 |  |
| computers_accessories | 5,736 | 46 | 0.80 |  |
| furniture_decor | 5,404 | 80 | 1.48 |  |
| housewares | 4,744 | 53 | 1.12 |  |
| watches_gifts | 4,730 | 58 | 1.23 |  |
| telephony | 3,641 | 42 | 1.15 |  |
| toys | 3,449 | 39 | 1.13 |  |
| cool_stuff | 3,302 | 19 | 0.58 |  |
| auto | 3,216 | 39 | 1.21 |  |
| garden_tools | 3,145 | 35 | 1.11 |  |

## Illustrative revenue opportunity

- Customers with a poor first experience (late delivery or 1-2 star review): **13,204**, 90-day repeat rate **1.03%**
- Customers with a good first experience (on time and 3+ stars): **70,444**, repeat rate **1.27%**
- Gap: **0.24 percentage points**
- Average value of a returning customer's second order: **R$ 152.30**

Scenario: what if a share of that gap could be closed? (covers the observed eligible cohorts, not a full year)

| share_of_gap_closed | extra_repeat_customers | extra_revenue_BRL |
|---|---|---|
| 10% | 3 | 457 |
| 25% | 8 | 1,218 |
| 50% | 16 | 2,437 |

**Assumptions:** the gap is treated as if poor experience caused the lower return rate; it may not (for example, late deliveries cluster in remote regions and categories that repurchase less). The A/B test in Phase 3 is how the true effect would be measured.
