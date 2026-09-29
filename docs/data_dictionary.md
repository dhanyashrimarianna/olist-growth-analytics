# Data Dictionary

Dataset: Olist Brazilian E-Commerce (9 tables). Raw tables are loaded 1:1 into the `raw` schema,
then modeled into a star schema in the `dw` schema (see `sql/`).

## Entity relationships

```
customers 1───* orders 1───* order_items *───1 products *───1 category_translation
                  │  │                 *───1 sellers
                  │  └───* order_payments
                  └──────* order_reviews
geolocation: joins to customers/sellers on zip code prefix (many rows per prefix)
```

## Tables

### orders (99,441 rows)
| Column | Type | Description |
|---|---|---|
| order_id | text | Unique order identifier (PK) |
| customer_id | text | Key to customers. **Unique per order**, not per person |
| order_status | text | delivered, shipped, canceled, unavailable, invoiced, processing, created, approved |
| order_purchase_timestamp | timestamp | When the customer placed the order |
| order_approved_at | timestamp | When payment was approved |
| order_delivered_carrier_date | timestamp | When handed to the logistics partner |
| order_delivered_customer_date | timestamp | When the customer received it |
| order_estimated_delivery_date | date | Delivery date promised at purchase |

### customers (99,441 rows)
| Column | Type | Description |
|---|---|---|
| customer_id | text | Per-order customer key (PK) |
| customer_unique_id | text | **The real person identifier.** Use this for repeat-purchase and retention analysis |
| customer_zip_code_prefix | text | First 5 digits of zip |
| customer_city | text | City |
| customer_state | text | 2-letter Brazilian state code |

### order_items (112,650 rows)
| Column | Type | Description |
|---|---|---|
| order_id | text | Key to orders (part of PK) |
| order_item_id | int | Item sequence within the order (part of PK) |
| product_id | text | Key to products |
| seller_id | text | Key to sellers |
| shipping_limit_date | timestamp | Seller deadline to hand the item to the carrier |
| price | numeric | Item price (BRL) |
| freight_value | numeric | Freight cost for the item (BRL) |

### order_payments (103,886 rows)
| Column | Type | Description |
|---|---|---|
| order_id | text | Key to orders (part of PK) |
| payment_sequential | int | Sequence when an order uses multiple methods (part of PK) |
| payment_type | text | credit_card, boleto, voucher, debit_card, not_defined |
| payment_installments | int | Number of installments |
| payment_value | numeric | Amount paid (BRL) |

### order_reviews (99,224 rows)
| Column | Type | Description |
|---|---|---|
| review_id | text | Review identifier. **Not unique** (see issues) |
| order_id | text | Key to orders |
| review_score | int | 1 to 5 satisfaction score |
| review_comment_title | text | Optional title (Portuguese) |
| review_comment_message | text | Optional comment (Portuguese) |
| review_creation_date | timestamp | When the survey was sent |
| review_answer_timestamp | timestamp | When the customer answered |

### products (32,951 rows)
| Column | Type | Description |
|---|---|---|
| product_id | text | Product identifier (PK) |
| product_category_name | text | Category in Portuguese |
| product_name_lenght | int | Characters in product name (column name misspelled in source) |
| product_description_lenght | int | Characters in description (misspelled in source) |
| product_photos_qty | int | Number of photos |
| product_weight_g | int | Weight in grams |
| product_length_cm / product_height_cm / product_width_cm | int | Package dimensions |

### sellers (3,095 rows)
| Column | Type | Description |
|---|---|---|
| seller_id | text | Seller identifier (PK) |
| seller_zip_code_prefix | text | First 5 digits of zip |
| seller_city | text | City |
| seller_state | text | State code |

### geolocation (~1M rows)
| Column | Type | Description |
|---|---|---|
| geolocation_zip_code_prefix | text | Zip prefix |
| geolocation_lat / geolocation_lng | numeric | Coordinates |
| geolocation_city / geolocation_state | text | City and state |

### product_category_name_translation (71 rows)
| Column | Type | Description |
|---|---|---|
| product_category_name | text | Portuguese name (PK) |
| product_category_name_english | text | English name |

## Known data quality issues (and how we handle them)

| Issue | Handling |
|---|---|
| `customer_id` is unique per order, so repeat rate computed on it is always 0% | Use `customer_unique_id` for all customer-level metrics |
| `review_id` is duplicated for some rows, and some orders have multiple reviews | Keep the latest review per order (by `review_answer_timestamp`) |
| Geolocation has many rows per zip prefix | Aggregate to one row per prefix (average lat/lng) |
| ~610 products have NULL category | Label as `unknown` |
| A few categories are missing from the translation table | Fall back to the Portuguese name |
| Delivery timestamps are NULL for undelivered orders | Delivery metrics computed on `delivered` orders only |
| A handful of orders (8 in the source) are marked `delivered` but have no delivery date | Reported as WARN in the quality checks; delivery metrics (`delivery_days`, `is_late`) are NULL for them |
| Some approved/delivery timestamps are out of order | Flag with `is_timestamp_valid`, exclude from delay metrics |
| Dataset covers Sep 2016 to Oct 2018, with very thin data in 2016 and late 2018 | Analysis window: Jan 2017 to Aug 2018 |
| Payments can be split across methods, so an order has multiple payment rows | Aggregate to one row per order for order-level revenue |
