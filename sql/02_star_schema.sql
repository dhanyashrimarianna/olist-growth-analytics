-- =====================================================================
-- 02_star_schema.sql
-- Builds the analytics layer (schema "dw") from the raw layer.
--
-- Grain
--   fact_orders       one row per order
--   fact_order_items  one row per order line item
-- Dimensions
--   dim_customer (one row per REAL person = customer_unique_id),
--   dim_product, dim_seller, dim_geo, dim_date
--
-- Cleaning rules are documented in docs/data_dictionary.md.
-- Run after loading raw data: psql -d olist -f sql/02_star_schema.sql
-- =====================================================================

DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- ---------------------------------------------------------------------
-- dim_date
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_date AS
SELECT
    d::date                                   AS date_key,
    EXTRACT(YEAR    FROM d)::int              AS year,
    EXTRACT(QUARTER FROM d)::int              AS quarter,
    EXTRACT(MONTH   FROM d)::int              AS month,
    TO_CHAR(d, 'Mon')                         AS month_name,
    DATE_TRUNC('month', d)::date              AS month_start,
    EXTRACT(ISODOW  FROM d)::int              AS iso_weekday,
    (EXTRACT(ISODOW FROM d) IN (6, 7))        AS is_weekend
FROM generate_series('2016-01-01'::date, '2018-12-31'::date, INTERVAL '1 day') AS d;

ALTER TABLE dw.dim_date ADD PRIMARY KEY (date_key);

-- ---------------------------------------------------------------------
-- dim_customer: one row per person. customer_id is per-order in the source,
-- so we key on customer_unique_id and keep the location from the latest order.
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_customer AS
SELECT DISTINCT ON (c.customer_unique_id)
    c.customer_unique_id        AS customer_key,
    c.customer_zip_code_prefix  AS zip_prefix,
    c.customer_city             AS city,
    c.customer_state            AS state
FROM raw.customers c
JOIN raw.orders    o ON o.customer_id = c.customer_id
ORDER BY c.customer_unique_id, o.order_purchase_timestamp DESC;

ALTER TABLE dw.dim_customer ADD PRIMARY KEY (customer_key);

-- ---------------------------------------------------------------------
-- dim_product: English category, NULL category labelled 'unknown'
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_product AS
SELECT
    p.product_id                                                  AS product_key,
    COALESCE(t.product_category_name_english,
             p.product_category_name,
             'unknown')                                           AS category,
    p.product_photos_qty                                          AS photos_qty,
    p.product_weight_g                                            AS weight_g,
    (p.product_length_cm * p.product_height_cm * p.product_width_cm) AS volume_cm3
FROM raw.products p
LEFT JOIN raw.product_category_translation t
       ON t.product_category_name = p.product_category_name;

ALTER TABLE dw.dim_product ADD PRIMARY KEY (product_key);

-- ---------------------------------------------------------------------
-- dim_seller
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_seller AS
SELECT
    seller_id               AS seller_key,
    seller_zip_code_prefix  AS zip_prefix,
    seller_city             AS city,
    seller_state            AS state
FROM raw.sellers;

ALTER TABLE dw.dim_seller ADD PRIMARY KEY (seller_key);

-- ---------------------------------------------------------------------
-- dim_geo: one row per zip prefix (source has many rows per prefix)
-- ---------------------------------------------------------------------
CREATE TABLE dw.dim_geo AS
SELECT
    geolocation_zip_code_prefix        AS zip_prefix,
    AVG(geolocation_lat)::numeric(12,8) AS lat,
    AVG(geolocation_lng)::numeric(12,8) AS lng
FROM raw.geolocation
GROUP BY geolocation_zip_code_prefix;

ALTER TABLE dw.dim_geo ADD PRIMARY KEY (zip_prefix);

-- ---------------------------------------------------------------------
-- fact_orders
-- ---------------------------------------------------------------------
CREATE TABLE dw.fact_orders AS
WITH items AS (
    SELECT
        order_id,
        COUNT(*)                    AS items_count,
        COUNT(DISTINCT seller_id)   AS sellers_count,
        SUM(price)                  AS items_value,
        SUM(freight_value)          AS freight_value
    FROM raw.order_items
    GROUP BY order_id
),
pay AS (
    SELECT
        order_id,
        SUM(payment_value)                                             AS payment_value,
        MAX(payment_installments)                                      AS max_installments,
        (ARRAY_AGG(payment_type ORDER BY payment_sequential))[1]       AS primary_payment_type
    FROM raw.order_payments
    GROUP BY order_id
),
-- keep only the latest review per order (duplicates exist in the source)
rev AS (
    SELECT DISTINCT ON (order_id)
        order_id, review_score, review_answer_timestamp
    FROM raw.order_reviews
    ORDER BY order_id, review_answer_timestamp DESC NULLS LAST, review_id
),
base AS (
    SELECT
        o.order_id,
        c.customer_unique_id                                AS customer_key,
        o.order_status,
        o.order_purchase_timestamp                          AS purchase_ts,
        o.order_purchase_timestamp::date                    AS purchase_date,
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS purchase_month,
        o.order_approved_at                                 AS approved_ts,
        o.order_delivered_carrier_date                      AS carrier_ts,
        o.order_delivered_customer_date                     AS delivered_ts,
        o.order_estimated_delivery_date::date               AS estimated_delivery_date,
        i.items_count, i.sellers_count, i.items_value, i.freight_value,
        p.payment_value, p.max_installments, p.primary_payment_type,
        r.review_score,
        -- timestamps must be in a sensible order to be trusted for delay metrics
        (
            (o.order_approved_at IS NULL OR o.order_approved_at >= o.order_purchase_timestamp)
        AND (o.order_delivered_carrier_date IS NULL
             OR o.order_delivered_carrier_date >= o.order_purchase_timestamp)
        AND (o.order_delivered_customer_date IS NULL
             OR o.order_delivered_customer_date >= COALESCE(o.order_delivered_carrier_date,
                                                             o.order_purchase_timestamp))
        )                                                   AS is_timestamp_valid
    FROM raw.orders o
    JOIN raw.customers c ON c.customer_id = o.customer_id
    LEFT JOIN items i ON i.order_id = o.order_id
    LEFT JOIN pay   p ON p.order_id = o.order_id
    LEFT JOIN rev   r ON r.order_id = o.order_id
)
SELECT
    b.*,
    -- delivery metrics only for delivered orders with trustworthy timestamps
    CASE WHEN b.order_status = 'delivered' AND b.delivered_ts IS NOT NULL AND b.is_timestamp_valid
         THEN ROUND((EXTRACT(EPOCH FROM (b.delivered_ts - b.purchase_ts)) / 86400.0)::numeric, 2)
    END AS delivery_days,
    CASE WHEN b.order_status = 'delivered' AND b.delivered_ts IS NOT NULL AND b.is_timestamp_valid
         THEN ROUND((EXTRACT(EPOCH FROM (b.delivered_ts - b.estimated_delivery_date::timestamp)) / 86400.0)::numeric, 2)
    END AS delay_days,
    CASE WHEN b.order_status = 'delivered' AND b.delivered_ts IS NOT NULL AND b.is_timestamp_valid
         THEN (b.delivered_ts::date > b.estimated_delivery_date)
    END AS is_late,
    -- customer journey: nth order of this person, and first-order cohort
    ROW_NUMBER() OVER (PARTITION BY b.customer_key ORDER BY b.purchase_ts, b.order_id) AS customer_order_seq,
    MIN(b.purchase_month) OVER (PARTITION BY b.customer_key)                            AS cohort_month
FROM base b;

ALTER TABLE dw.fact_orders ADD PRIMARY KEY (order_id);
ALTER TABLE dw.fact_orders ADD FOREIGN KEY (customer_key) REFERENCES dw.dim_customer (customer_key);
CREATE INDEX idx_fo_customer ON dw.fact_orders (customer_key);
CREATE INDEX idx_fo_month    ON dw.fact_orders (purchase_month);
CREATE INDEX idx_fo_status   ON dw.fact_orders (order_status);

-- ---------------------------------------------------------------------
-- fact_order_items
-- ---------------------------------------------------------------------
CREATE TABLE dw.fact_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id   AS product_key,
    oi.seller_id    AS seller_key,
    fo.purchase_date,
    oi.price,
    oi.freight_value
FROM raw.order_items oi
JOIN dw.fact_orders fo ON fo.order_id = oi.order_id;

ALTER TABLE dw.fact_order_items ADD PRIMARY KEY (order_id, order_item_id);
ALTER TABLE dw.fact_order_items ADD FOREIGN KEY (order_id)    REFERENCES dw.fact_orders (order_id);
ALTER TABLE dw.fact_order_items ADD FOREIGN KEY (product_key) REFERENCES dw.dim_product (product_key);
ALTER TABLE dw.fact_order_items ADD FOREIGN KEY (seller_key)  REFERENCES dw.dim_seller (seller_key);
CREATE INDEX idx_foi_product ON dw.fact_order_items (product_key);
CREATE INDEX idx_foi_seller  ON dw.fact_order_items (seller_key);

ANALYZE;
