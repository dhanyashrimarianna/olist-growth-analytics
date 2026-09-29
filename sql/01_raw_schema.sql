-- =====================================================================
-- 01_raw_schema.sql
-- Raw layer: 1:1 copy of the Olist CSVs. No cleaning happens here.
-- Keys are declared only where the source data actually guarantees them
-- (order_reviews and geolocation contain duplicates, so no PK there).
-- Run: psql -d olist -f sql/01_raw_schema.sql
-- =====================================================================

DROP SCHEMA IF EXISTS raw CASCADE;
CREATE SCHEMA raw;

CREATE TABLE raw.customers (
    customer_id               TEXT PRIMARY KEY,
    customer_unique_id        TEXT NOT NULL,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            CHAR(2)
);

CREATE TABLE raw.orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL,
    order_status                   TEXT NOT NULL,
    order_purchase_timestamp       TIMESTAMP,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP
);

CREATE TABLE raw.order_items (
    order_id             TEXT NOT NULL,
    order_item_id        INTEGER NOT NULL,
    product_id           TEXT NOT NULL,
    seller_id            TEXT NOT NULL,
    shipping_limit_date  TIMESTAMP,
    price                NUMERIC(10,2),
    freight_value        NUMERIC(10,2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE raw.order_payments (
    order_id              TEXT NOT NULL,
    payment_sequential    INTEGER NOT NULL,
    payment_type          TEXT,
    payment_installments  INTEGER,
    payment_value         NUMERIC(10,2),
    PRIMARY KEY (order_id, payment_sequential)
);

-- review_id is NOT unique in the source, so no primary key
CREATE TABLE raw.order_reviews (
    review_id                TEXT,
    order_id                 TEXT NOT NULL,
    review_score             INTEGER,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP,
    review_answer_timestamp  TIMESTAMP
);

-- Source column names are misspelled ("lenght"); kept as-is for raw fidelity
CREATE TABLE raw.products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT,
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);

CREATE TABLE raw.sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            CHAR(2)
);

-- Many rows per zip prefix, so no primary key
CREATE TABLE raw.geolocation (
    geolocation_zip_code_prefix  TEXT,
    geolocation_lat              NUMERIC(12,8),
    geolocation_lng              NUMERIC(12,8),
    geolocation_city             TEXT,
    geolocation_state            CHAR(2)
);

CREATE TABLE raw.product_category_translation (
    product_category_name          TEXT PRIMARY KEY,
    product_category_name_english  TEXT
);

-- Indexes used by the modeling step
CREATE INDEX idx_raw_orders_customer  ON raw.orders (customer_id);
CREATE INDEX idx_raw_items_product    ON raw.order_items (product_id);
CREATE INDEX idx_raw_items_seller     ON raw.order_items (seller_id);
CREATE INDEX idx_raw_reviews_order    ON raw.order_reviews (order_id);
CREATE INDEX idx_raw_geo_zip          ON raw.geolocation (geolocation_zip_code_prefix);
