-- 90-day repeat rate by segment of the FIRST order (observable customers only).
WITH coh AS (
    SELECT * FROM dw.v_customer_first_order
    WHERE is_90d_observable
      AND cohort_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
)
SELECT 'Product category' AS dimension, COALESCE(category, 'unknown') AS segment,
       COUNT(*) AS customers, SUM(repeat_90d::int)::bigint AS repeaters
FROM coh GROUP BY 2
UNION ALL
SELECT 'Customer state', state, COUNT(*), SUM(repeat_90d::int)::bigint
FROM coh GROUP BY 2
UNION ALL
SELECT 'Payment type', COALESCE(payment_type, 'unknown'), COUNT(*), SUM(repeat_90d::int)::bigint
FROM coh GROUP BY 2
ORDER BY 1, 3 DESC;
