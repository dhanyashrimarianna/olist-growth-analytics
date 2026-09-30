# 01. Prioritized Roadmap (RICE)

Recommendations come from the Phase 2 findings (`docs/05_findings.md`). Scores are reproducible with
`python scripts/rice_and_sample_size.py`, which writes `rice_scoring.csv`, `rice_sensitivity.csv` and
`sample_size.csv` in this folder.

## What the evidence supports

| Evidence (Phase 2) | Used for |
|---|---|
| Repeat purchase is rare (3.0% ever, 1.23% within 90 days) | The problem worth solving |
| Return activity is front-loaded: 0.45% in month 1, about 0.2% from month 4 | Timing of a nudge |
| Repeat rate by category ranges from 0.80% to 1.75% | Category-aware content |
| Late delivery cuts reviews (2.27 vs 4.29) but only slightly lowers return (0.92% vs 1.25%) | Delivery is a satisfaction lever more than a retention lever |
| About 4 in 10 "quick repeats" are same-day orders | A measurement and possible cart-design question |

## Candidate features

| ID | Feature | Story | Why it is on the list |
|---|---|---|---|
| F1 | Timed, category-aware second-order nudge | US-07 | Targets the repeat gap directly, at the moment returns are most likely |
| F2 | Proactive delay notification with a revised date | US-05 | Late orders drive the worst reviews |
| F3 | Service recovery for 1 to 2 star reviews | US-08 | About 1 in 8 orders gets a 1 to 2 star review, and those customers return less (0.98% vs 1.29%) |
| F4 | Investigate same-day split orders (discovery, not a build) | none | Could change how repeat is measured and whether the cart needs a fix |

## RICE scoring

RICE = Reach × Impact × Confidence ÷ Effort. **Reach** is per quarter and derived from measured data
(about 13,970 first-time customers, 14,430 delivered orders per quarter). **Impact, Confidence and Effort
are judgement calls**, labelled as assumptions, and meant to be challenged.

| Rank | ID | Feature | Reach / quarter | Impact | Confidence | Effort (person-months) | RICE |
|---|---|---|---|---|---|---|---|
| 1 | F1 | Second-order nudge | 13,970 (all first-time customers) | 1 (medium) | 50% | 2.0 | **3,491** |
| 2 | F3 | Service recovery | 1,850 (orders with 1 to 2 stars) | 0.5 (low) | 50% | 1.5 | **308** |
| 3 | F2 | Delay notification | 960 (late orders, 6.7%) | 0.5 (low) | 50% | 3.0 | **80** |
| 4 | F4 | Same-day investigation | 130 (same-day repeaters) | 0.25 (minimal) | 80% | 0.5 | **53** |

**Why the inputs are what they are**
- **Impact for F2 and F3 is low** because the measured retention gap is small: 0.33 points for late
  deliveries and 0.31 points for poor reviews.
- **Impact for F1 is medium**, not high. Nothing in the data proves a nudge works. The case rests on timing
  and on category differences, which are associations.
- **Confidence is 50% for all three builds** because every result so far is observational.
- **F2 costs the most** (3 person-months) because it needs carrier-scan data and a way to predict delays,
  and it reaches the fewest orders.

## Sensitivity: is the ranking just my assumptions?

| Scenario | Ranking (RICE score) |
|---|---|
| Base case | F1 3,491 · F3 308 · F2 80 · F4 53 |
| Pessimistic on F1 (impact 0.5, confidence 30%) | F1 1,047 · F3 308 · F2 80 · F4 53 |
| Optimistic on F2 and F3 (impact 1, confidence 80%) | F1 3,491 · F3 985 · F2 257 · F4 53 |
| Both together | F1 1,047 · F3 985 · F2 257 · F4 53 |

F1 stays first in every scenario, but in the combined worst case it leads F3 only narrowly (1,047 versus
985). The order of F3, F2 and F4 is steadier than the size of the gaps between them.

## How much could each one realistically add?

Upper bounds on extra returning customers per quarter, using measured rates and an average second order
of R$ 152.30. These are revenue, not profit.

| Feature | Assumption | Extra returning customers / quarter | Revenue / quarter |
|---|---|---|---|
| F2 | Late customers return as often as on-time ones (best case) | about 3 | R$ 485 |
| F3 | 1 to 2 star customers return as often as 4 to 5 star ones (best case) | about 6 | R$ 872 |
| F1 | 90-day repeat rate rises 10% relative | about 17 | R$ 2,616 |
| F1 | rises 25% relative | about 43 | R$ 6,540 |
| F1 | rises 50% relative | about 86 | R$ 13,081 |

Today about 172 customers per quarter return within 90 days. Even the larger F1 scenarios add tens of
customers, not thousands. **Retention work at this scale is worth doing only if it is cheap to build and
run**, which is why F1 is scoped as a no-discount message in its first test.

F2 and F3 may still be worth doing for customer experience, seller quality and brand reasons. This analysis
does not measure those, so they are not in the score.

## Now / Next / Later

| Horizon | Work | Notes |
|---|---|---|
| **Now** (months 0 to 2) | F1: build the nudge and start the A/B test | Spec in `docs/06_prd_second_order_nudge.md`, test in `02_ab_test_plan.md` |
| **Now** | F4: investigate same-day split orders | Half a person-month. Check whether same-day pairs share a cart or carrier |
| **Next** (months 2 to 6) | F3: service recovery for 1 to 2 star reviews | Cheap, and it is also the exclusion rule for F1 |
| **Later** (after the first test reads out) | Test an incentive arm on F1 | Needs Finance input on acceptable cost per returning customer |
| **Later** | F2: delay notifications | Revisit once F1's result is known and carrier data access is confirmed |

## Not doing, and why

- **A large delivery-speed programme aimed at retention.** The measured retention gap is too small to
  justify it on retention grounds.
- **Discounts in the first test.** They cost money and would hide whether a simple reminder works.
- **Large claims about revenue.** The numbers above are illustrative.

## Assumptions to validate before committing

1. Recent volume matches the window average (about 4,655 new customers per month). The marketplace grew during
   the window, so later months are probably busier. Check `cohort_size` in
   `reports/tables/cohort_retention_long.csv`.
2. The team can send messages to these customers (consent and contact data). See the PRD.
3. Effort estimates come from engineering, not from this analysis.
