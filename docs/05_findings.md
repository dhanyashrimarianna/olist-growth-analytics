# 05. Findings: Why Is Repeat Purchasing So Low?

All figures come from `reports/summary.md`, produced by `scripts/run_analysis.py` on the full Olist dataset
(99,441 orders, latest purchase 2018-10-17). Analysis window: orders placed January 2017 to August 2018.
Every result is an **association** in observational data, not a proven cause.

## Answer in one paragraph

Almost nobody comes back, and this is mostly not a delivery problem. Only **3.0%** of customers ever
placed a second delivered order, and only **1.23%** did so within 90 days. Late delivery clearly damages
satisfaction (average review 2.27 for late orders versus 4.29 on time) and is linked to a smaller but
real drop in return rate (0.92% versus 1.25%). But delivery is late for only about 7% of orders, and the
size of that gap is small, so fixing delivery alone would protect ratings and reputation far more than it
would grow repeat revenue. Product category shows a wider spread in repeat rate than delivery does,
which points to where a retention effort is more likely to pay off.

## Findings

### F1. Repeat purchase is rare
| Measure | Value |
|---|---|
| Customers with a delivered order | 93,104 |
| Customers with 2+ delivered orders | 2,789 (**3.0%**) |
| 90-day repeat rate (customers observable for a full 90 days, n = 84,198) | **1.23%** |

The first-pass figure in the BRD (3.12%) counted all order statuses; the delivered-only figure is 3.0%.

### F2. About four in ten "quick repeats" are same-day orders
Counting same-day second orders lifts the 90-day repeat rate from 1.23% to 2.18%. Those look more like a
split basket than a genuine return, so the headline KPI excludes them. Worth investigating: whether
same-day pairs come from multi-seller carts that were split into separate orders.

### F3. The funnel is healthy up to delivery; the leak is afterwards
| Stage | Orders | % of placed |
|---|---|---|
| Placed | 99,092 | 100% |
| Payment approved | 98,957 | 99.86% |
| Handed to carrier | 97,376 | 98.27% |
| Delivered | 96,211 | 97.09% |
| Reviewed | 95,568 | 96.44% |

Ninety-seven of every 100 orders are delivered, so operations are not what limits growth. The drop-off is
between the first delivered order and any second one.

### F4. Return activity is small, front-loaded, then flat
Pooled across cohorts, the share of customers ordering again is **0.45%** in month 1, falls to about
**0.23%** by month 4, and then stays near 0.2% (0.14% in month 12). If a nudge is going to work, the first
one to three months are the window.

### F5. Late delivery sharply lowers review scores, and worse delays hurt more
| Delivery outcome | Orders | Avg review | 1 to 2 star | 5 star |
|---|---|---|---|---|
| On time | 89,001 | 4.29 | 9.2% | 62.3% |
| Late 1 to 3 days | 1,358 | 3.51 | 25.6% | 36.3% |
| Late 4 to 7 days | 1,772 | 2.32 | 61.3% | 18.1% |
| Late 8+ days | 3,246 | 1.73 | 78.5% | 7.5% |

On-time delivery is 93.2%, and late orders average 11.3 days late. The relationship is graded: each step
of extra delay pushes scores lower. This is the strongest effect in the analysis.

### F6. A bad first delivery goes with a lower chance of returning, but the gap is small
| First order | Customers | 90-day repeat rate | 95% CI |
|---|---|---|---|
| Delivered on time | 78,206 | 1.25% | 1.18 to 1.33 |
| Delivered late | 5,864 | 0.92% | 0.71 to 1.20 |

The difference is 0.33 percentage points, about a quarter lower in relative terms
(two-proportion z-test, z = 2.22, p = 0.027). It is statistically significant at the 5% level but only
modestly so, and no correction was made for looking at several comparisons. Customers whose first review was
1 to 2 stars returned at 0.98% versus 1.29% for 4 to 5 stars, the same direction and similar size.

### F7. Category differs more than delivery does
Among the largest categories, 90-day repeat rate ranges from **0.80%** (computers_accessories) to
**1.75%** (bed_bath_table), more than double. Sports_leisure (1.61%) and furniture_decor (1.48%) are also
above average. This spread (about 0.95 points) is nearly three times the on-time versus late gap (0.33
points). Caveats: categories were not formally tested against each other, and category is confounded with
price, seller mix and region.

### F8. Sizing: delivery alone is not a large revenue lever
Customers with a poor first experience (late delivery or a 1 to 2 star review) number 13,204 and repeat at
1.03%. Customers with a good first experience number 70,444 and repeat at 1.27%. That is a 0.24 point gap.
With an average second order of R$ 152.30, closing **half** of the gap would add about **16 returning
customers and R$ 2,437** across the observed cohorts, against roughly R$ 15 million in delivered order
value over the window (96,211 orders at an average of R$ 159.81). Even closing all of the gap does not change
the picture. This estimate assumes the gap is caused by the experience, which is the most generous reading.

## What this means for the hypotheses in the BRD

| Hypothesis going in | What the data says |
|---|---|
| Delivery problems drive low repeat purchase | **Partly supported.** Real but small association (F6, F8). Not the main story |
| Poor experience shows up in reviews | **Strongly supported** (F5) |
| Some segments retain better than others | **Supported.** Category spread is the largest difference found (F7) |

## Implications for the Phase 3 roadmap

These are hypotheses to score and test, not conclusions.

1. **Proactive delay communication and service recovery** (US-05, US-08). The evidence for protecting
   satisfaction is strong (F5), but the retention upside is modest (F6, F8). Position it as protecting ratings
   and trust, and do not promise large retention gains.
2. **Timed second-order nudges aimed at higher-repurchase categories** (US-07). Timing (F4) and category
   (F7) both point here. This is the option with the most room to move repeat rate.
3. **Investigate same-day split orders** (F2). If they are multi-seller carts split into separate orders, a
   cart or shipping change could matter more than any retention campaign.

A back-of-envelope check for the A/B test: with a 1.25% baseline, detecting an increase of 0.3 points at 80%
power and 5% significance needs about 24,000 customers per group. That is feasible at this marketplace's scale
but is a real constraint on how quickly a test can conclude.

## Limitations

- Observational data: association only. Late deliveries may cluster in remote regions or categories that
  repurchase less, which would explain part of F6 without delivery being the cause.
- Customers may have bought from competitors or under a different account, which the data cannot show.
- No marketing spend, margin or cost data, so any ROI is illustrative.
- Data ends in 2018; behaviour today may differ.
- The 90-day KPI depends on the same-day rule (F2); both versions are reported.
- Multiple comparisons were not corrected for, and segment differences (F7) were not formally tested.

## Reproduce

```bash
bash scripts/setup_db.sh          # build the database
python scripts/run_analysis.py    # regenerate reports/
```
