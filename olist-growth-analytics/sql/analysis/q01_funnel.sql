-- Order funnel, Jan 2017 to Aug 2018 (analysis window, see BRD DR-04).
-- Order-level: how many placed orders reach each stage.
WITH o AS (
    SELECT * FROM dw.fact_orders
    WHERE purchase_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
),
stages AS (
    SELECT 1 AS stage_no, 'Orders placed' AS stage, COUNT(*) AS orders FROM o
    UNION ALL SELECT 2, 'Payment approved',  COUNT(*) FILTER (WHERE approved_ts IS NOT NULL) FROM o
    UNION ALL SELECT 3, 'Handed to carrier', COUNT(*) FILTER (WHERE carrier_ts IS NOT NULL)  FROM o
    UNION ALL SELECT 4, 'Delivered',         COUNT(*) FILTER (WHERE order_status = 'delivered') FROM o
    UNION ALL SELECT 5, 'Reviewed',          COUNT(*) FILTER (WHERE order_status = 'delivered' AND review_score IS NOT NULL) FROM o
)
SELECT
    stage_no,
    stage,
    orders,
    ROUND(100.0 * orders / FIRST_VALUE(orders) OVER (ORDER BY stage_no), 2) AS pct_of_placed,
    ROUND(100.0 * orders / LAG(orders) OVER (ORDER BY stage_no), 2)         AS pct_of_previous
FROM stages
ORDER BY stage_no;
