# 03. User Stories & Acceptance Criteria

Stories are grouped into epics and traced back to business requirements in the BRD.
Format: *As a [role], I want [capability], so that [benefit].* Acceptance criteria use Given / When / Then.

Priority is MoSCoW. Estimates are story points (Fibonacci) and are relative sizing guesses for a
simulated backlog.

| Epic | Theme |
|---|---|
| E1 | Trustworthy retention metrics |
| E2 | Delivery experience |
| E3 | Post-purchase engagement |
| E4 | Executive visibility |
| E5 | Experimentation |

---

## E1. Trustworthy retention metrics

### US-01: Customer identity
**As a** data analyst, **I want** customers identified by `customer_unique_id`, **so that** repeat purchase is not reported as 0%.
**BR:** BR-01 · **Priority:** Must · **Points:** 2

- **Given** the raw orders table, **when** I count orders per `customer_id`, **then** every customer has exactly one order (documented as a known source issue).
- **Given** the star schema, **when** I count orders per `customer_key`, **then** some customers have 2 or more orders.
- **Given** `dw.dim_customer`, **when** I check for duplicate `customer_key`, **then** there are none.

### US-02: Fair cohort retention
**As a** head of growth, **I want** retention measured over the same window for every cohort, **so that** recent customers are not counted as lost simply because they had less time to return.
**BR:** BR-02 · **Priority:** Must · **Points:** 5

- **Given** the first-order cohort of each customer, **when** I compute the 90-day repeat rate, **then** only cohorts with at least 90 days of observable history are included.
- **Given** the cohort table, **when** I view it, **then** it shows cohort size and the share returning in each month after the first order.
- **Given** the KPI definition, **when** a stakeholder asks how it is calculated, **then** the SQL is in the repository and referenced from the BRD.

---

## E2. Delivery experience

### US-03: Delivery versus satisfaction
**As a** logistics head, **I want** to see how delays relate to review scores, **so that** I can judge how much delivery performance affects customer satisfaction.
**BR:** BR-03 · **Priority:** Must · **Points:** 3

- **Given** delivered orders with valid timestamps, **when** I compare late and on-time orders, **then** I see average review score and the score distribution for each group.
- **Given** delay in days, **when** I bucket orders (on time, 1 to 3 days late, 4 to 7, 8+), **then** I see review score by bucket.
- **Given** invalid or missing timestamps, **when** the analysis runs, **then** these orders are excluded and their count is reported.

### US-04: First-order experience and return
**As a** product manager, **I want** to know whether a bad first delivery reduces the chance of a second order, **so that** I can decide whether delivery-related features deserve priority.
**BR:** BR-04 · **Priority:** Must · **Points:** 5

- **Given** customers grouped by first-order outcome (on time, late, low review), **when** I compute the 90-day repeat rate for each group, **then** I can compare them side by side.
- **Given** the comparison, **when** the difference is shown, **then** it includes a confidence interval or significance test.
- **Given** the results, **when** they are presented, **then** they are labelled as association and not proven cause.

### US-05: Proactive delay communication *(recommended feature)*
**As a** customer whose order will arrive late, **I want** to be told early and given a revised date, **so that** I am not left wondering and can trust the marketplace.
**BR:** BR-07 · **Priority:** Should · **Points:** 8

- **Given** an order with an estimated delivery date, **when** the carrier scan indicates it will miss that date, **then** the customer receives a notification with the new expected date.
- **Given** a notification is sent, **when** the customer opens it, **then** they can see order status and contact support in one step.
- **Given** an order is delivered on time, **when** the process runs, **then** no delay notification is sent.

---

## E3. Post-purchase engagement

### US-06: Segmenting for retention
**As a** CRM lead, **I want** retention broken down by product category, state and payment type, **so that** I can target the segments most likely to respond.
**BR:** BR-05 · **Priority:** Should · **Points:** 5

- **Given** the cohort model, **when** I filter by category, state or payment type, **then** repeat rate and customer count are shown for each segment.
- **Given** a segment with fewer than 100 customers, **when** it is displayed, **then** it is flagged as low-sample.
- **Given** the segment view, **when** I export it, **then** columns and definitions match the KPI table in the BRD.

### US-07: Second-order incentive *(recommended feature)*
**As a** first-time customer, **I want** a relevant offer after my order is delivered, **so that** I have a reason to come back.
**BR:** BR-07 · **Priority:** Should · **Points:** 8

- **Given** a first order marked delivered, **when** a set number of days has passed, **then** the customer receives an offer.
- **Given** a customer left a review of 2 stars or less, **when** the offer logic runs, **then** they are routed to a service-recovery message instead of a discount.
- **Given** an offer is redeemed, **when** the order completes, **then** it is attributed to the campaign for reporting.

### US-08: Review follow-up *(recommended feature)*
**As a** customer who left a poor review, **I want** the marketplace to respond, **so that** I feel heard and my problem is fixed.
**BR:** BR-07 · **Priority:** Could · **Points:** 5

- **Given** a review with a score of 1 or 2, **when** it is submitted, **then** a support ticket is created automatically.
- **Given** a ticket is created, **when** it is resolved, **then** the customer is told the outcome.

---

## E4. Executive visibility

### US-09: Retention dashboard
**As a** head of growth, **I want** one dashboard with the agreed KPIs, **so that** I can track retention health without asking the analytics team.
**BR:** BR-11, BR-12 · **Priority:** Should · **Points:** 8

- **Given** the dashboard, **when** it loads, **then** it shows KPI-01 to KPI-08 with the definitions available on hover or in a notes page.
- **Given** filters for time period, state and category, **when** I change them, **then** every visual updates consistently.
- **Given** the data refresh, **when** it runs, **then** the last refresh date is displayed.

### US-10: Documented KPI definitions
**As a** BI analyst, **I want** every KPI defined once and documented, **so that** teams stop reporting different numbers for the same metric.
**BR:** BR-12 · **Priority:** Must · **Points:** 2

- **Given** the KPI table in the BRD, **when** I search for a KPI, **then** its definition, formula and source table are listed.
- **Given** the SQL scripts, **when** I run them from a clean database, **then** they reproduce the KPI values.

---

## E5. Experimentation

### US-11: A/B test plan
**As a** product manager, **I want** a test plan for the top recommendation, **so that** we can measure its real effect before a full rollout.
**BR:** BR-10 · **Priority:** Must · **Points:** 5

- **Given** the top-ranked feature, **when** I open the test plan, **then** it states the hypothesis, primary metric, guardrail metrics and randomization unit.
- **Given** a baseline rate and a minimum detectable effect, **when** the sample size is calculated, **then** the inputs and method are shown.
- **Given** the plan, **when** the test ends, **then** the decision rule (ship, iterate or stop) is defined in advance.

### US-12: Prioritized roadmap
**As a** head of growth, **I want** recommendations ranked with a transparent score, **so that** I can see why one feature comes before another.
**BR:** BR-08, BR-09 · **Priority:** Must · **Points:** 3

- **Given** each recommendation, **when** I view the roadmap, **then** Reach, Impact, Confidence and Effort are shown with the reasoning for each value.
- **Given** the RICE formula, **when** inputs change, **then** the ranking updates.
- **Given** the top-ranked item, **when** I follow the link, **then** it opens its PRD.

---

## Backlog summary

| ID | Story | Epic | BR | Priority | Points |
|---|---|---|---|---|---|
| US-01 | Customer identity | E1 | BR-01 | Must | 2 |
| US-02 | Fair cohort retention | E1 | BR-02 | Must | 5 |
| US-03 | Delivery versus satisfaction | E2 | BR-03 | Must | 3 |
| US-04 | First-order experience and return | E2 | BR-04 | Must | 5 |
| US-05 | Proactive delay communication | E2 | BR-07 | Should | 8 |
| US-06 | Segmenting for retention | E3 | BR-05 | Should | 5 |
| US-07 | Second-order incentive | E3 | BR-07 | Should | 8 |
| US-08 | Review follow-up | E3 | BR-07 | Could | 5 |
| US-09 | Retention dashboard | E4 | BR-11, BR-12 | Should | 8 |
| US-10 | Documented KPI definitions | E4 | BR-12 | Must | 2 |
| US-11 | A/B test plan | E5 | BR-10 | Must | 5 |
| US-12 | Prioritized roadmap | E5 | BR-08, BR-09 | Must | 3 |

The three recommended features (US-05, US-07, US-08) are hypotheses at this stage. Phase 2 analysis
decides which of them the evidence supports, and the RICE scoring in Phase 3 ranks them.
