-- Value of a returning customer's second order (used for the revenue-opportunity scenarios).
SELECT
    COUNT(*) FILTER (WHERE repeat_90d)                       AS repeat_customers,
    ROUND(AVG(second_value) FILTER (WHERE repeat_90d), 2)    AS avg_second_order_value,
    ROUND(AVG(first_value), 2)                               AS avg_first_order_value
FROM dw.v_customer_first_order
WHERE is_90d_observable
  AND cohort_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01';
