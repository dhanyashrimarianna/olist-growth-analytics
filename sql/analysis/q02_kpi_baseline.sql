-- KPI baseline (BRD section 6). One row per metric.
WITH win AS (
    SELECT * FROM dw.fact_orders
    WHERE order_status = 'delivered'
      AND purchase_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
),
per_customer AS (
    SELECT customer_key, COUNT(*) AS n_orders FROM win GROUP BY customer_key
),
valid AS (
    SELECT * FROM win WHERE is_late IS NOT NULL
),
coh AS (
    SELECT * FROM dw.v_customer_first_order
    WHERE is_90d_observable
      AND cohort_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
)
SELECT metric, value
FROM (
    SELECT 1 AS ord, 'KPI-01 customers with a delivered order' AS metric, COUNT(*)::numeric AS value FROM per_customer
    UNION ALL SELECT 2,  'KPI-01 customers with 2+ delivered orders', COUNT(*) FILTER (WHERE n_orders > 1) FROM per_customer
    UNION ALL SELECT 3,  'KPI-01 repeat purchase rate (pct)', ROUND(100.0 * COUNT(*) FILTER (WHERE n_orders > 1) / COUNT(*), 2) FROM per_customer
    UNION ALL SELECT 4,  'KPI-02 cohort customers observable for 90 days', COUNT(*) FROM coh
    UNION ALL SELECT 5,  'KPI-02 90-day repeat rate (pct), excl same-day', ROUND(100.0 * AVG(repeat_90d::int), 2) FROM coh
    UNION ALL SELECT 6,  'KPI-02 90-day repeat rate (pct), incl same-day', ROUND(100.0 * AVG(repeat_90d_incl_same_day::int), 2) FROM coh
    UNION ALL SELECT 7,  'KPI-03 on-time delivery rate (pct)', ROUND(100.0 * AVG((NOT is_late)::int), 2) FROM valid
    UNION ALL SELECT 8,  'KPI-04 avg delay of late orders (days)', ROUND(AVG(delay_days) FILTER (WHERE is_late), 2) FROM valid
    UNION ALL SELECT 9,  'KPI-05 avg review score', ROUND(AVG(review_score), 3) FROM win
    UNION ALL SELECT 10, 'KPI-06 review gap, on-time minus late', ROUND(AVG(review_score) FILTER (WHERE NOT is_late) - AVG(review_score) FILTER (WHERE is_late), 3) FROM valid
    UNION ALL SELECT 11, 'KPI-08 average order value (BRL)', ROUND(AVG(payment_value), 2) FROM win
) t
ORDER BY ord;
