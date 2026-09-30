-- Customers whose first order is observable for 90 days, split by first-order experience.
-- Long format so Python can aggregate marginals, confidence intervals and tests.
SELECT
    CASE WHEN is_late IS NULL THEN 'Unknown' WHEN is_late THEN 'Late' ELSE 'On time' END AS delivery_group,
    CASE WHEN review_score IS NULL THEN 'No review'
         WHEN review_score <= 2 THEN '1-2 stars'
         WHEN review_score = 3 THEN '3 stars'
         ELSE '4-5 stars' END AS review_group,
    COUNT(*)                     AS customers,
    SUM(repeat_90d::int)::bigint AS repeaters
FROM dw.v_customer_first_order
WHERE is_90d_observable
  AND cohort_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
GROUP BY 1, 2
ORDER BY 1, 2;
