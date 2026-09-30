"""Run the Phase 2 analysis end to end.

    python scripts/run_analysis.py            # writes to reports/
    python scripts/run_analysis.py --out /tmp/test_reports

Steps: build analysis view -> run sql/analysis/q*.sql -> confidence intervals and significance
test -> charts (reports/figures) -> tables (reports/tables) -> reports/summary.md

Connection uses the standard PG* environment variables (PGHOST, PGPORT, PGDATABASE, PGUSER,
PGPASSWORD); defaults are localhost / 5432 / olist / postgres.

All findings are ASSOCIATIONS from observational data. They are not proof of cause.
"""
import argparse
import os
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
MIN_SEGMENT = 100  # segments smaller than this are flagged low-sample
SCENARIOS = (0.10, 0.25, 0.50)  # share of the experience gap assumed recoverable


# ---------------------------------------------------------------- helpers
def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.getenv("PGDATABASE", "olist"),
    )
    return create_engine(url, connect_args={"options": "-c client_encoding=UTF8"})


def run_sql(engine, path):
    sql = Path(path).read_text(encoding="utf-8")
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    for c in df.columns:  # Postgres NUMERIC arrives as Decimal objects
        if df[c].dtype == object:
            try:
                df[c] = pd.to_numeric(df[c])
            except (ValueError, TypeError):
                pass
    return df


def rate_with_ci(k, n):
    """Rate in percent with a 95% Wilson confidence interval."""
    if n == 0:
        return np.nan, np.nan, np.nan
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return 100 * k / n, 100 * lo, 100 * hi


def summarise_groups(df, by):
    g = df.groupby(by)[["customers", "repeaters"]].sum().reset_index()
    out = g.apply(lambda r: pd.Series(rate_with_ci(r.repeaters, r.customers),
                                      index=["repeat_rate_pct", "ci_low", "ci_high"]), axis=1)
    return pd.concat([g, out], axis=1)


def fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else ""
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return "n/a"
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    if isinstance(v, (int, np.integer)):
        return f"{v:,}"
    return str(v)


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(fmt(v) for v in r) + " |")
    return "\n".join(lines)


def save_fig(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports", help="output folder (default: reports)")
    args = ap.parse_args()
    out = Path(args.out)
    out = out if out.is_absolute() else ROOT / out
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text((SQL_DIR / "04_analysis_views.sql").read_text(encoding="utf-8")))

    q = lambda name: run_sql(engine, SQL_DIR / "analysis" / name)
    meta = run_sql(engine, SQL_DIR / "analysis" / "q02_kpi_baseline.sql")  # also proves the view works
    with engine.connect() as conn:
        n_orders = conn.execute(text("SELECT COUNT(*) FROM dw.fact_orders")).scalar()
        last_day = conn.execute(text("SELECT MAX(purchase_date) FROM dw.fact_orders")).scalar()
    print(f"Database has {n_orders:,} orders, latest purchase date {last_day}")

    # 1. funnel ---------------------------------------------------------
    funnel = q("q01_funnel.sql")
    funnel.to_csv(out / "tables" / "funnel.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(funnel["stage"][::-1], funnel["orders"][::-1], color="#3b7dd8")
    for i, (o, p) in enumerate(zip(funnel["orders"][::-1], funnel["pct_of_placed"][::-1])):
        ax.text(o, i, f"  {o:,} ({p:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, funnel["orders"].max() * 1.25)
    ax.set_title("Order funnel, Jan 2017 to Aug 2018")
    ax.set_xlabel("Orders")
    save_fig(fig, out / "figures" / "01_funnel.png")

    # 2. KPI baseline ---------------------------------------------------
    kpi = meta
    kpi.to_csv(out / "tables" / "kpi_baseline.csv", index=False)

    # 3. cohort retention -----------------------------------------------
    coh = q("q03_cohort_retention.sql")
    coh["cohort_month"] = pd.to_datetime(coh["cohort_month"])
    coh.to_csv(out / "tables" / "cohort_retention_long.csv", index=False)
    curve = (coh[coh.months_since >= 1]
             .groupby("months_since")
             .agg(cohorts=("cohort_month", "count"), customers=("cohort_size", "sum"),
                  active=("active_customers", "sum"))
             .reset_index())
    curve["retention_pct"] = 100 * curve["active"] / curve["customers"]
    curve.to_csv(out / "tables" / "retention_curve.csv", index=False)

    pivot = coh.pivot(index="cohort_month", columns="months_since", values="retention_pct")
    heat = pivot.drop(columns=[0], errors="ignore")
    if heat.notna().any().any():
        fig, ax = plt.subplots(figsize=(11, 0.42 * len(heat) + 2))
        vmax = max(1.0, float(np.nanmax(heat.values)))
        im = ax.imshow(heat.values.astype(float), aspect="auto", cmap="Blues", vmin=0, vmax=vmax)
        ax.set_xticks(range(heat.shape[1]))
        ax.set_xticklabels(heat.columns)
        ax.set_yticks(range(heat.shape[0]))
        ax.set_yticklabels([d.strftime("%Y-%m") for d in heat.index])
        for i in range(heat.shape[0]):
            for j in range(heat.shape[1]):
                v = heat.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7,
                            color="white" if v > vmax * 0.6 else "black")
        ax.set_xlabel("Months since first delivered order")
        ax.set_ylabel("Cohort (month of first order)")
        ax.set_title("Monthly retention: % of cohort ordering again in month N")
        fig.colorbar(im, ax=ax, label="% of cohort")
        save_fig(fig, out / "figures" / "02_cohort_retention_heatmap.png")

    # 4. delivery vs review ---------------------------------------------
    dv = q("q04_delivery_vs_review.sql")
    dv.to_csv(out / "tables" / "delivery_vs_review.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#2e9d5b"] + ["#e8a33d", "#e0742f", "#c9382c"][: len(dv) - 1]
    ax.bar(dv["bucket"], dv["avg_review"], color=colors)
    for i, v in enumerate(dv["avg_review"]):
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylim(0, 5.2)
    ax.set_ylabel("Average review score (1-5)")
    ax.set_title("Review score by delivery outcome")
    save_fig(fig, out / "figures" / "03_review_by_delay.png")
    on_time = dv[dv.bucket == "On time"]
    late = dv[dv.bucket != "On time"]
    late_avg = np.average(late.avg_review, weights=late.orders) if len(late) else np.nan
    late_low = np.average(late.pct_1_2_star, weights=late.orders) if len(late) else np.nan

    # 5. first-order experience -> repeat -----------------------------
    exp = q("q05_first_order_experience.sql")
    exp.to_csv(out / "tables" / "first_order_experience_long.csv", index=False)
    by_delivery = summarise_groups(exp, "delivery_group")
    by_review = summarise_groups(exp, "review_group")
    by_delivery.to_csv(out / "tables" / "repeat_by_delivery.csv", index=False)
    by_review.to_csv(out / "tables" / "repeat_by_review.csv", index=False)

    ztest = None
    d = by_delivery.set_index("delivery_group")
    if {"On time", "Late"} <= set(d.index) and d.loc[["On time", "Late"], "customers"].min() > 0:
        counts = [int(d.loc["On time", "repeaters"]), int(d.loc["Late", "repeaters"])]
        nobs = [int(d.loc["On time", "customers"]), int(d.loc["Late", "customers"])]
        stat, p = proportions_ztest(counts, nobs)
        ztest = {"z": stat, "p": p,
                 "diff_pp": d.loc["On time", "repeat_rate_pct"] - d.loc["Late", "repeat_rate_pct"]}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    panels = ((axes[0], by_delivery, "delivery_group", ["On time", "Late"], "By first-order delivery"),
              (axes[1], by_review, "review_group", ["4-5 stars", "3 stars", "1-2 stars"],
               "By first-order review"))
    for ax, df_, col, order, title in panels:
        # 'Unknown' / 'No review' stay in the tables but are left off the chart: tiny groups with huge intervals
        df_ = df_.set_index(col).reindex([o for o in order if o in set(df_[col])]).reset_index()
        err = [df_.repeat_rate_pct - df_.ci_low, df_.ci_high - df_.repeat_rate_pct]
        ax.bar(range(len(df_)), df_.repeat_rate_pct, yerr=err, capsize=4, color="#3b7dd8")
        ax.set_xticks(range(len(df_)))
        ax.set_xticklabels([f"{g}\n(n={n:,})" for g, n in zip(df_[col], df_.customers)])
        for i, (v, hi) in enumerate(zip(df_.repeat_rate_pct, df_.ci_high)):
            ax.text(i, hi * 1.03, f"{v:.2f}%", ha="center", va="bottom", fontsize=9)
        ax.set_title(title)
        ax.set_ylabel("90-day repeat rate (%)")
        ax.set_ylim(0, float(df_.ci_high.max()) * 1.18)
    fig.suptitle("Does the first-order experience relate to coming back? (95% CI)")
    save_fig(fig, out / "figures" / "04_repeat_by_experience.png")

    # 6. segments -------------------------------------------------------
    seg = q("q06_segments.sql")
    seg["repeat_rate_pct"] = 100 * seg.repeaters / seg.customers
    seg["low_sample"] = seg.customers < MIN_SEGMENT
    seg.to_csv(out / "tables" / "segments.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, dim, topn in zip(axes, ["Product category", "Customer state", "Payment type"], [12, 10, 6]):
        s = seg[(seg.dimension == dim) & (~seg.low_sample)].nlargest(topn, "customers")
        s = s.sort_values("repeat_rate_pct")
        ax.barh(s.segment, s.repeat_rate_pct, color="#3b7dd8")
        ax.set_title(f"{dim} (top {topn} by size, n>={MIN_SEGMENT})")
        ax.set_xlabel("90-day repeat rate (%)")
    save_fig(fig, out / "figures" / "05_segments.png")

    # 7. revenue opportunity scenarios ---------------------------------
    val = q("q07_second_order_value.sql").iloc[0]
    ex = exp.copy()
    poor = ex[(ex.delivery_group == "Late") | (ex.review_group == "1-2 stars")]
    good = ex[(ex.delivery_group == "On time") & (ex.review_group.isin(["3 stars", "4-5 stars"]))]
    n_poor, k_poor = int(poor.customers.sum()), int(poor.repeaters.sum())
    n_good, k_good = int(good.customers.sum()), int(good.repeaters.sum())
    rev = None
    if n_poor and n_good:
        r_poor, r_good = k_poor / n_poor, k_good / n_good
        gap = r_good - r_poor
        avg_val = float(val.avg_second_order_value) if pd.notna(val.avg_second_order_value) else np.nan
        rows = []
        for share in SCENARIOS:
            extra = round(n_poor * gap * share)  # whole customers; revenue uses the same rounded figure
            rows.append({"share_of_gap_closed": f"{int(share * 100)}%",
                         "extra_repeat_customers": extra,
                         "extra_revenue_BRL": round(extra * avg_val) if not np.isnan(avg_val) else np.nan})
        rev = {"n_poor": n_poor, "n_good": n_good, "rate_poor": 100 * r_poor,
               "rate_good": 100 * r_good, "gap_pp": 100 * gap, "avg_second_order_value": avg_val,
               "table": pd.DataFrame(rows) if gap > 0 else None}
        if rev["table"] is not None:
            rev["table"].to_csv(out / "tables" / "revenue_opportunity_scenarios.csv", index=False)

    # ---------------------------------------------------------- summary
    L = []
    L.append("# Analysis results (auto-generated)\n")
    L.append(f"_Generated {date.today()} by `scripts/run_analysis.py` from a database with "
             f"**{n_orders:,} orders**, latest purchase date **{last_day}**._\n")
    L.append("_All results are associations from observational data. They show how groups differ, "
             "not what caused the difference. Confidence intervals are 95% Wilson intervals._\n")
    L.append("## KPI baseline\n\n" + md_table(kpi) + "\n")
    L.append("## Order funnel (Jan 2017 to Aug 2018)\n\n" + md_table(funnel.drop(columns="stage_no")) + "\n")
    L.append("## Monthly retention curve (all eligible cohorts pooled)\n\n"
             "Share of a cohort placing a delivered order in month N after its first order.\n\n"
             + md_table(curve.assign(retention_pct=curve.retention_pct.round(2))) + "\n")
    L.append("## Delivery outcome vs review score\n\n" + md_table(dv.drop(columns="bucket_no")) + "\n")
    if len(on_time) and len(late):
        L.append(f"On-time orders average **{on_time.avg_review.iloc[0]:.2f}**; late orders average "
                 f"**{late_avg:.2f}**. Late orders get a 1 or 2 star review "
                 f"**{late_low:.1f}%** of the time versus **{on_time.pct_1_2_star.iloc[0]:.1f}%** "
                 "for on-time orders.\n")
    L.append("## 90-day repeat rate by first-order experience\n\n**By delivery**\n\n"
             + md_table(by_delivery.round(2)) + "\n\n**By review**\n\n"
             + md_table(by_review.round(2)) + "\n")
    if ztest:
        L.append(f"On-time vs late first orders: difference **{ztest['diff_pp']:.2f} percentage points** "
                 f"(two-proportion z-test: z = {ztest['z']:.2f}, p = {ztest['p']:.4g}).\n")
    L.append("## 90-day repeat rate by segment\n\n"
             f"Segments under {MIN_SEGMENT} customers are flagged `low_sample` and excluded from charts.\n\n"
             + "\n\n".join(f"**{dim}**\n\n" + md_table(
                 seg[seg.dimension == dim].drop(columns="dimension").head(12).round(2))
                 for dim in seg.dimension.unique()) + "\n")
    if rev:
        if rev["table"] is not None:
            scenario_text = ("Scenario: what if a share of that gap could be closed? "
                             "(covers the observed eligible cohorts, not a full year)\n\n"
                             + md_table(rev["table"]) + "\n\n")
        else:
            scenario_text = ("The gap is not positive, so no revenue scenario is shown: in this data a "
                             "poor first experience does not go with a lower repeat rate.\n\n")
        L.append("## Illustrative revenue opportunity\n\n"
                 f"- Customers with a poor first experience (late delivery or 1-2 star review): "
                 f"**{rev['n_poor']:,}**, 90-day repeat rate **{rev['rate_poor']:.2f}%**\n"
                 f"- Customers with a good first experience (on time and 3+ stars): "
                 f"**{rev['n_good']:,}**, repeat rate **{rev['rate_good']:.2f}%**\n"
                 f"- Gap: **{rev['gap_pp']:.2f} percentage points**\n"
                 f"- Average value of a returning customer's second order: "
                 f"**R$ {rev['avg_second_order_value']:,.2f}**\n\n"
                 + scenario_text
                 + "**Assumptions:** the gap is treated as if poor experience caused the lower return "
                   "rate; it may not (for example, late deliveries cluster in remote regions and "
                   "categories that repurchase less). The A/B test in Phase 3 is how the true effect "
                   "would be measured.\n")
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nDone. Wrote tables, figures and summary.md to {out}")


if __name__ == "__main__":
    main()
