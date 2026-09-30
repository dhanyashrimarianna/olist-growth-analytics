# 02. A/B Test Plan: Second-Order Nudge

Supports US-11 and BR-10. Numbers below come from `sample_size.csv`
(`python scripts/rice_and_sample_size.py`). Anything marked **proposal** is a starting value for
stakeholders to confirm.

## Decision this test supports

Should the marketplace roll out a timed, category-aware message to first-time customers to increase the
chance of a second order?

## Hypothesis

- **H0:** The 90-day repeat rate is the same for customers who receive the nudge and those who do not.
- **H1:** The 90-day repeat rate is higher for customers who receive the nudge.

Rationale (Phase 2): return activity peaks in month 1 and then flattens (0.45% falling to about 0.2%), and
repeat rate differs by category (0.80% to 1.75%). A well-timed, relevant reminder may convert some customers
who would otherwise drift away. The data shows the pattern, not that a message causes the lift, which is why
this test exists.

## Population

| Rule | Detail |
|---|---|
| Included | First-time customers (by `customer_unique_id`) whose first order has been delivered |
| Excluded | Customers who left a 1 to 2 star review (they go to service recovery, not promotion) |
| Excluded | Customers who opted out of marketing or have no valid contact consent |
| Excluded | Customers who already placed a second order before their assignment date |

## Design

| Item | Choice |
|---|---|
| Unit of randomization | Customer (`customer_unique_id`), so one person always sees one experience |
| Assignment | Hash of the customer id, 50/50, at the moment the first delivery is confirmed (**proposal**) |
| Control | No message |
| Treatment | Two messages, on day 14 and day 45 after delivery, with recommendations chosen by the first order's category (**proposal**: timing follows the month-1 peak, and day 14 leaves room for the review window) |
| Incentive | **None in this test.** A discount arm is a later test, so the first result shows whether a reminder alone helps |

## Metrics

| Type | Metric | Definition |
|---|---|---|
| **Primary** | 90-day repeat rate | Share of customers with a second delivered order 1 to 90 days after assignment |
| Secondary | 30-day repeat rate | Earlier read on the effect |
| Secondary | Revenue per customer at 90 days | Total `payment_value` of orders in the window, divided by customers |
| Secondary | Value of the second order | Average order value among returners |
| Diagnostic | Sent, delivered, opened, clicked | Explains the result; never used to define groups |
| **Guardrail** | Unsubscribe and complaint rate | Stop if above the agreed limit (**proposal**: 0.5% of messaged customers) |
| **Guardrail** | Review score of second orders | Must not fall |
| **Guardrail** | Contact-centre volume per customer | Must not rise materially |

Same-day second orders are excluded from the primary metric, matching KPI-02 (the window starts after
assignment, so this is rare in practice).

## Sample size and duration

Baseline 90-day repeat rate **1.23%**, two-sided significance 5%, power 80%, equal split.
Enrolment assumes **4,655 new customers per month**, the window average; later months were probably busier.

| Lift to detect | Relative lift | Per group | Total | Enrolment | Read-out (incl. 90-day window) |
|---|---|---|---|---|---|
| +0.20 points | +16% | 51,429 | 102,858 | 22.1 months | about 25 months |
| +0.30 points | +24% | 23,668 | 47,336 | 10.2 months | about 13 months |
| +0.40 points | +33% | 13,762 | 27,524 | 5.9 months | about 9 months |
| **+0.50 points** | **+41%** | **9,091** | **18,182** | **3.9 months** | **about 7 months** |
| +0.75 points | +61% | 4,347 | 8,694 | 1.9 months | about 5 months |

**Planning choice (proposal): design for +0.5 points.** Because the baseline is low, small lifts need very
large samples. A real effect smaller than 0.5 points has less than an 80% chance of being detected. The
trade-off is explicit: a test sized for +0.3 points would take more than a year at this volume. Options to
speed it up are higher traffic, a longer run, or accepting an inconclusive result. The decision rule below
covers that case.

## Analysis plan

1. **Sample ratio check** before anything else: the observed split should match 50/50 (chi-square test).
   A mismatch means assignment or logging is broken and the result is not trusted.
2. **Balance check** on first-order category, customer state and whether the first delivery was late.
3. **Intention to treat:** analyse customers by assigned group, whether or not they opened the message.
4. **Primary test:** two-proportion z-test with 95% Wilson intervals for each group and a 95% confidence
   interval for the difference.
5. **One look at the end.** No stopping early on a promising interim result, since repeated looks inflate
   false positives. If interim monitoring is needed, use a pre-agreed alpha-spending rule.
6. **Segments:** only those named in advance (category family, first delivery on time or late), reported with
   correction for multiple comparisons. Anything else is exploratory and labelled so.
7. Run for whole weeks, and note the holiday-season months (November and December), which may shift behaviour.

## Decision rule (agreed before launch)

| Result | Decision |
|---|---|
| Lift is positive, the 95% interval excludes zero, and all guardrails pass | **Ship**, then test an incentive |
| Lift is positive but the interval includes zero, and the upper bound is at or above 0.5 points | **Iterate**: change timing or content, or extend the test |
| Interval rules out lifts of 0.5 points or more, or a guardrail is breached | **Stop** |

Shipping also requires Finance to confirm that the revenue from the lift exceeds the cost of running the
messages.

## Risks to validity

| Risk | Mitigation |
|---|---|
| Consent and contact data missing for many customers | Count eligible customers first; restrict to consented contacts |
| One person with several accounts | `customer_unique_id` is the best identifier available; note the limit |
| Email deliverability differs across groups | Monitor delivery rate as a diagnostic |
| Novelty effect or seasonality | Whole-week runs; repeat in another period if the result is borderline |
| Purchases outside the marketplace are invisible | Acknowledge; affects both groups equally |

## Instrumentation required

Assignment event (customer id, group, timestamp), message sent, delivered, opened and clicked, order
placed with customer id, and an experiment flag in the reporting layer so results can be reproduced.

## Follow-up tests

1. Incentive arm versus reminder-only arm, once Finance sets an acceptable cost per returning customer.
2. Timing: day 14 versus day 30 for the first message.
3. Delay notification (F2), if it moves forward on the roadmap.
