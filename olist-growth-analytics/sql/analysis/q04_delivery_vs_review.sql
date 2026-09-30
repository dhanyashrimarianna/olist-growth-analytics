-- Review score by delivery outcome (delivered orders, valid timestamps, with a review).
WITH v AS (
    SELECT * FROM dw.fact_orders
    WHERE order_status = 'delivered'
      AND is_late IS NOT NULL
      AND review_score IS NOT NULL
      AND purchase_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
),
bucketed AS (
    SELECT
        review_score,
        CASE WHEN NOT is_late THEN 1
             WHEN delay_days <= 3 THEN 2
             WHEN delay_days <= 7 THEN 3
             ELSE 4 END AS bucket_no,
        CASE WHEN NOT is_late THEN 'On time'
             WHEN delay_days <= 3 THEN 'Late 1-3 days'
             WHEN delay_days <= 7 THEN 'Late 4-7 days'
             ELSE 'Late 8+ days' END AS bucket
    FROM v
)
SELECT
    bucket_no,
    bucket,
    COUNT(*)                                          AS orders,
    ROUND(AVG(review_score), 3)                       AS avg_review,
    ROUND(100.0 * AVG((review_score <= 2)::int), 2)   AS pct_1_2_star,
    ROUND(100.0 * AVG((review_score = 5)::int), 2)    AS pct_5_star
FROM bucketed
GROUP BY bucket_no, bucket
ORDER BY bucket_no;
