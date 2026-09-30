-- Monthly cohort retention. Cohort = month of a customer's first delivered order.
-- retention_pct = share of the cohort that placed a delivered order in month N after the first.
-- Only COMPLETE calendar months are reported, so the partial last month never looks like churn.
WITH delivered AS (
    SELECT
        customer_key,
        purchase_month,
        ROW_NUMBER() OVER (PARTITION BY customer_key ORDER BY purchase_ts, order_id) AS d_seq
    FROM dw.fact_orders
    WHERE order_status = 'delivered'
),
first_order AS (
    SELECT customer_key, purchase_month AS cohort_month
    FROM delivered
    WHERE d_seq = 1
      AND purchase_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size FROM first_order GROUP BY cohort_month
),
active AS (
    SELECT DISTINCT customer_key, purchase_month FROM delivered
),
activity AS (
    SELECT
        f.cohort_month,
        ((EXTRACT(YEAR FROM a.purchase_month) * 12 + EXTRACT(MONTH FROM a.purchase_month))
       - (EXTRACT(YEAR FROM f.cohort_month)   * 12 + EXTRACT(MONTH FROM f.cohort_month)))::int AS months_since,
        COUNT(DISTINCT a.customer_key) AS active_customers
    FROM first_order f
    JOIN active a ON a.customer_key = f.customer_key
    GROUP BY 1, 2
),
last_full AS (
    SELECT DATE_TRUNC('month', MAX(purchase_date))::date AS last_month FROM dw.fact_orders
),
grid AS (
    SELECT s.cohort_month, s.cohort_size, g AS months_since
    FROM sizes s CROSS JOIN generate_series(0, 12) AS g
)
SELECT
    gr.cohort_month,
    gr.cohort_size,
    gr.months_since,
    COALESCE(ac.active_customers, 0)                                     AS active_customers,
    ROUND(100.0 * COALESCE(ac.active_customers, 0) / gr.cohort_size, 2) AS retention_pct
FROM grid gr
LEFT JOIN activity ac
       ON ac.cohort_month = gr.cohort_month AND ac.months_since = gr.months_since
CROSS JOIN last_full lf
WHERE (gr.cohort_month + gr.months_since * INTERVAL '1 month')::date < lf.last_month
ORDER BY gr.cohort_month, gr.months_since;
