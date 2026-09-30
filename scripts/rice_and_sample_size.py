"""Phase 3 calculations: RICE scoring, sensitivity check, upper-bound retention gains, A/B sample sizes.

    python scripts/rice_and_sample_size.py

No database needed. MEASURED inputs come from reports/summary.md (Phase 2).
ASSUMPTION inputs (impact, confidence, effort) are judgement calls and are labelled as such;
change them and re-run to see how the ranking responds.
Writes roadmap/rice_scoring.csv, roadmap/rice_sensitivity.csv, roadmap/sample_size.csv.
"""
import csv
import math
from pathlib import Path

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

OUT = Path(__file__).resolve().parents[1] / "roadmap"

# ---------------------------------------------------------------- MEASURED (reports/summary.md)
WINDOW_MONTHS = 20            # Jan 2017 to Aug 2018
CUSTOMERS = 93_104            # customers with a delivered order in the window
DELIVERED_ORDERS = 96_211
# (orders, pct of those orders with a 1-2 star review) by delivery outcome
REVIEW_BUCKETS = {"On time": (89_001, 9.24), "Late 1-3": (1_358, 25.55),
                  "Late 4-7": (1_772, 61.29), "Late 8+": (3_246, 78.47)}
BASELINE_90D = 0.0123         # KPI-02, 90-day repeat rate excl. same-day
REPEAT_INCL_SAME_DAY = 0.0218
REPEAT_ON_TIME, REPEAT_LATE = 0.0125, 0.0092
REPEAT_4_5_STARS, REPEAT_1_2_STARS = 0.0129, 0.0098
AVG_SECOND_ORDER_BRL = 152.30

# ---------------------------------------------------------------- DERIVED reach per quarter
reviewed = sum(n for n, _ in REVIEW_BUCKETS.values())
late_share = sum(n for k, (n, _) in REVIEW_BUCKETS.items() if k != "On time") / reviewed
low_review_share = sum(n * p / 100 for n, p in REVIEW_BUCKETS.values()) / reviewed
customers_pq = CUSTOMERS / WINDOW_MONTHS * 3
orders_pq = DELIVERED_ORDERS / WINDOW_MONTHS * 3
REACH = {
    "F1": customers_pq,                                   # every first-time customer
    "F2": orders_pq * late_share,                         # late orders
    "F3": orders_pq * low_review_share,                   # orders with 1-2 star review
    "F4": customers_pq * (REPEAT_INCL_SAME_DAY - BASELINE_90D),  # same-day repeaters
}

# ---------------------------------------------------------------- ASSUMPTIONS (judgement)
# impact scale (standard RICE): 3 massive, 2 high, 1 medium, 0.5 low, 0.25 minimal
# confidence: 0-1 | effort: person-months
ITEMS = [
    dict(id="F1", name="Timed, category-aware second-order nudge", story="US-07",
         impact=1.0, confidence=0.5, effort=2.0),
    dict(id="F2", name="Proactive delay notification with revised date", story="US-05",
         impact=0.5, confidence=0.5, effort=3.0),
    dict(id="F3", name="Service recovery for 1-2 star reviews", story="US-08",
         impact=0.5, confidence=0.5, effort=1.5),
    dict(id="F4", name="Investigate same-day split orders (discovery)", story="n/a",
         impact=0.25, confidence=0.8, effort=0.5),
]


def rice(item, reach):
    return reach * item["impact"] * item["confidence"] / item["effort"]


def ranked(items, overrides=None):
    overrides = overrides or {}
    rows = []
    for it in items:
        it2 = {**it, **overrides.get(it["id"], {})}
        rows.append((it2["id"], rice(it2, REACH[it["id"]])))
    rows.sort(key=lambda r: -r[1])
    return rows


# ---------------------------------------------------------------- RICE table
print("== Reach per quarter (derived from measured data) ==")
print(f"first-time customers/quarter : {customers_pq:,.0f}")
print(f"delivered orders/quarter     : {orders_pq:,.0f}")
print(f"late share of reviewed orders: {late_share:.1%} -> {REACH['F2']:,.0f} late orders/quarter")
print(f"1-2 star share               : {low_review_share:.1%} -> {REACH['F3']:,.0f} orders/quarter")
print(f"same-day repeaters/quarter   : {REACH['F4']:,.0f}\n")

OUT.mkdir(exist_ok=True)
with open(OUT / "rice_scoring.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "feature", "user_story", "reach_per_quarter", "impact", "confidence",
                "effort_person_months", "rice_score", "rank"])
    order = [r[0] for r in ranked(ITEMS)]
    print("== RICE (base case) ==")
    for it in sorted(ITEMS, key=lambda i: order.index(i["id"])):
        score = rice(it, REACH[it["id"]])
        w.writerow([it["id"], it["name"], it["story"], round(REACH[it["id"]], -1), it["impact"],
                    it["confidence"], it["effort"], round(score), order.index(it["id"]) + 1])
        print(f"#{order.index(it['id']) + 1} {it['id']} {it['name']:<52} reach {REACH[it['id']]:>8,.0f}  "
              f"RICE {score:>7,.0f}")

# ---------------------------------------------------------------- sensitivity
scenarios = {
    "Base case": {},
    "Pessimistic on F1 (impact 0.5, confidence 0.3)": {"F1": {"impact": 0.5, "confidence": 0.3}},
    "Optimistic on F2 and F3 (impact 1, confidence 0.8)":
        {"F2": {"impact": 1.0, "confidence": 0.8}, "F3": {"impact": 1.0, "confidence": 0.8}},
    "Both together": {"F1": {"impact": 0.5, "confidence": 0.3},
                      "F2": {"impact": 1.0, "confidence": 0.8}, "F3": {"impact": 1.0, "confidence": 0.8}},
}
print("\n== Sensitivity: does the top pick change? ==")
with open(OUT / "rice_sensitivity.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["scenario", "ranking (id:score)"])
    for name, ov in scenarios.items():
        r = ranked(ITEMS, ov)
        txt = ", ".join(f"{i}:{s:,.0f}" for i, s in r)
        w.writerow([name, txt])
        print(f"{name:<52} {txt}")

# ---------------------------------------------------------------- upper bounds on retention gain
print("\n== Upper bound on extra returning customers per quarter ==")
ub_f2 = REACH["F2"] * (REPEAT_ON_TIME - REPEAT_LATE)
ub_f3 = REACH["F3"] * (REPEAT_4_5_STARS - REPEAT_1_2_STARS)
print(f"F2 (late customers reach on-time repeat rate): {ub_f2:.1f} customers, R$ {ub_f2 * AVG_SECOND_ORDER_BRL:,.0f}")
print(f"F3 (1-2 star customers reach 4-5 star rate)  : {ub_f3:.1f} customers, R$ {ub_f3 * AVG_SECOND_ORDER_BRL:,.0f}")
for lift in (0.10, 0.25, 0.50):
    extra = customers_pq * BASELINE_90D * lift
    print(f"F1 at +{int(lift * 100)}% relative lift in 90-day repeat: {extra:.1f} customers, "
          f"R$ {extra * AVG_SECOND_ORDER_BRL:,.0f}")
print(f"(baseline returners per quarter: {customers_pq * BASELINE_90D:,.0f})")

# ---------------------------------------------------------------- sample size
print("\n== A/B sample size (two-sided alpha 0.05, power 0.80, baseline 1.23%) ==")
monthly = CUSTOMERS / WINDOW_MONTHS
rows = []
for lift_pp in (0.2, 0.3, 0.4, 0.5, 0.75):
    p2 = BASELINE_90D + lift_pp / 100
    n = math.ceil(NormalIndPower().solve_power(proportion_effectsize(p2, BASELINE_90D),
                                               alpha=0.05, power=0.8, ratio=1))
    enrol_months = 2 * n / monthly
    rel = lift_pp / 100 / BASELINE_90D * 100
    rows.append([lift_pp, round(rel), n, 2 * n, round(enrol_months, 1), round(enrol_months + 3, 1)])
    print(f"+{lift_pp:.2f} pp (+{rel:.0f}% relative): {n:>6,} per arm, {2 * n:>7,} total, "
          f"enrol {enrol_months:4.1f} months, read-out ~{enrol_months + 3:4.1f} months (incl. 90-day window)")
with open(OUT / "sample_size.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["absolute_lift_pp", "relative_lift_pct", "n_per_arm", "n_total",
                "enrolment_months", "months_to_readout_incl_90d_window"])
    w.writerows(rows)
print(f"(enrolment rate assumed: {monthly:,.0f} new customers/month, the average over the analysis window)")
