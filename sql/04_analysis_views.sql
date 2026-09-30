-- =====================================================================
-- 04_analysis_views.sql
-- One row per customer, describing their FIRST DELIVERED order and whether
-- they came back. Every retention query in sql/analysis/ builds on this view
-- so that "first order", "repeat" and "observable" mean the same thing everywhere.
--
-- Definitions (documented in docs/02_business_requirements_document.md):
--   first order        the customer's earliest delivered order
--   repeat_90d         a second delivered order placed 1 to 90 days after the first
--                      (same-day second orders are excluded: they are usually a split basket,
--                      not a genuine return; see repeat_90d_incl_same_day for the alternative)
--   is_90d_observable  the first order is at least 90 days older than the latest order in the data,
--                      so the customer has had a full window to return
-- Run: psql -d olist -f sql/04_analysis_views.sql   (run_analysis.py also does this)
-- =====================================================================

CREATE OR REPLACE VIEW dw.v_customer_first_order AS
WITH delivered AS (
    SELECT
        fo.*,
        ROW_NUMBER() OVER (PARTITION BY fo.customer_key ORDER BY fo.purchase_ts, fo.order_id) AS d_seq
    FROM dw.fact_orders fo
    WHERE fo.order_status = 'delivered'
),
latest AS (
    SELECT MAX(purchase_date) AS max_date FROM dw.fact_orders
),
first_order AS (
    SELECT * FROM delivered WHERE d_seq = 1
),
second_order AS (
    SELECT customer_key, purchase_date AS second_date, payment_value AS second_value
    FROM delivered WHERE d_seq = 2
),
first_category AS (
    -- category of the first line item of the first order
    SELECT DISTINCT ON (foi.order_id) foi.order_id, dp.category
    FROM dw.fact_order_items foi
    JOIN dw.dim_product dp ON dp.product_key = foi.product_key
    ORDER BY foi.order_id, foi.order_item_id
)
SELECT
    f.customer_key,
    f.order_id                                   AS first_order_id,
    f.purchase_date                              AS first_date,
    f.purchase_month                             AS cohort_month,
    f.is_late,
    f.delay_days,
    f.review_score,
    f.payment_value                              AS first_value,
    f.primary_payment_type                       AS payment_type,
    c.state                                      AS state,
    fc.category                                  AS category,
    s.second_date,
    s.second_value,
    (s.second_date - f.purchase_date)            AS days_to_second,
    (f.purchase_date + 90 <= l.max_date)         AS is_90d_observable,
    COALESCE(s.second_date - f.purchase_date BETWEEN 1 AND 90, FALSE) AS repeat_90d,
    COALESCE(s.second_date - f.purchase_date BETWEEN 0 AND 90, FALSE) AS repeat_90d_incl_same_day
FROM first_order f
JOIN dw.dim_customer c        ON c.customer_key = f.customer_key
CROSS JOIN latest l
LEFT JOIN second_order s      ON s.customer_key = f.customer_key
LEFT JOIN first_category fc   ON fc.order_id    = f.order_id;
