-- =====================================================================
-- 03_data_quality_checks.sql
-- Returns one row per check with a PASS/FAIL status.
-- Run: psql -d olist -f sql/03_data_quality_checks.sql
-- =====================================================================

WITH checks AS (
    -- Row-count reconciliation between raw and model
    SELECT 'orders: raw = fact_orders' AS check_name,
           ((SELECT COUNT(*) FROM raw.orders) - (SELECT COUNT(*) FROM dw.fact_orders))::bigint AS violations

    UNION ALL SELECT 'order items: raw = fact_order_items',
           (SELECT COUNT(*) FROM raw.order_items) - (SELECT COUNT(*) FROM dw.fact_order_items)

    -- Grain: exactly one row per order / per person
    UNION ALL SELECT 'fact_orders grain: duplicate order_id',
           (SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM dw.fact_orders)

    UNION ALL SELECT 'dim_customer grain: duplicate customer_key',
           (SELECT COUNT(*) - COUNT(DISTINCT customer_key) FROM dw.dim_customer)

    -- Referential integrity
    UNION ALL SELECT 'orphan order items (no product)',
           (SELECT COUNT(*) FROM dw.fact_order_items f
            LEFT JOIN dw.dim_product p ON p.product_key = f.product_key
            WHERE p.product_key IS NULL)

    UNION ALL SELECT 'orphan order items (no seller)',
           (SELECT COUNT(*) FROM dw.fact_order_items f
            LEFT JOIN dw.dim_seller s ON s.seller_key = f.seller_key
            WHERE s.seller_key IS NULL)

    -- Value sanity
    UNION ALL SELECT 'negative prices or freight',
           (SELECT COUNT(*) FROM raw.order_items WHERE price < 0 OR freight_value < 0)

    UNION ALL SELECT 'review scores outside 1-5',
           (SELECT COUNT(*) FROM dw.fact_orders WHERE review_score NOT BETWEEN 1 AND 5)

    UNION ALL SELECT 'delivered orders with no delivery timestamp',
           (SELECT COUNT(*) FROM dw.fact_orders
            WHERE order_status = 'delivered' AND delivered_ts IS NULL)

    -- Metric integrity
    UNION ALL SELECT 'delivery_days negative',
           (SELECT COUNT(*) FROM dw.fact_orders WHERE delivery_days < 0)

    UNION ALL SELECT 'customer_order_seq starts at 1 for every customer',
           (SELECT COUNT(*) FROM (
               SELECT customer_key FROM dw.fact_orders
               GROUP BY customer_key HAVING MIN(customer_order_seq) <> 1) x)
)
SELECT check_name,
       violations,
       CASE WHEN violations = 0 THEN 'PASS' WHEN check_name LIKE 'delivered orders with no delivery%' THEN 'WARN' ELSE 'FAIL' END AS status
FROM checks;

-- ---------------------------------------------------------------------
-- Informational profile (not pass/fail): known issues from the data dictionary
-- ---------------------------------------------------------------------
SELECT 'orders with invalid timestamp order'          AS metric, COUNT(*) AS n FROM dw.fact_orders WHERE NOT is_timestamp_valid
UNION ALL SELECT 'orders with no review',                         COUNT(*) FROM dw.fact_orders WHERE review_score IS NULL
UNION ALL SELECT 'products with unknown category',                COUNT(*) FROM dw.dim_product WHERE category = 'unknown'
UNION ALL SELECT 'people with 2+ orders',                         COUNT(*) FROM (SELECT customer_key FROM dw.fact_orders GROUP BY 1 HAVING COUNT(*) > 1) x
UNION ALL SELECT 'total people (customer_unique_id)',             COUNT(*) FROM dw.dim_customer;
