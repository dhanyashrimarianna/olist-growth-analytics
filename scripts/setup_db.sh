#!/usr/bin/env bash
# Create the schema, load CSVs, build the star schema, run data quality checks.
#
# Usage:
#   bash scripts/setup_db.sh              # loads real data from data/raw
#   DATA_DIR=data/sample bash scripts/setup_db.sh   # smoke test on synthetic sample
#
# Connection settings come from the standard PG* env vars (see .env.example).
set -euo pipefail

cd "$(dirname "$0")/.."
DATA_DIR="${DATA_DIR:-data/raw}"
DB="${PGDATABASE:-olist}"

if [ ! -f "$DATA_DIR/olist_orders_dataset.csv" ]; then
  echo "No CSVs found in $DATA_DIR. See data/README.md to download the dataset." >&2
  exit 1
fi

# Create the database if it does not exist
psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1 \
  || psql -d postgres -c "CREATE DATABASE $DB"

echo ">> Creating raw schema"
psql -d "$DB" -v ON_ERROR_STOP=1 -q -f sql/01_raw_schema.sql

load() {  # load <table> <csv>
  echo ">> Loading $2 -> raw.$1"
  psql -d "$DB" -v ON_ERROR_STOP=1 -q \
    -c "\copy raw.$1 FROM '$DATA_DIR/$2' WITH (FORMAT csv, HEADER true)"
}

load customers                     olist_customers_dataset.csv
load geolocation                   olist_geolocation_dataset.csv
load sellers                       olist_sellers_dataset.csv
load products                      olist_products_dataset.csv
load product_category_translation  product_category_name_translation.csv
load orders                        olist_orders_dataset.csv
load order_items                   olist_order_items_dataset.csv
load order_payments                olist_order_payments_dataset.csv
load order_reviews                 olist_order_reviews_dataset.csv

echo ">> Building star schema"
psql -d "$DB" -v ON_ERROR_STOP=1 -q -f sql/02_star_schema.sql

echo ">> Running data quality checks"
psql -d "$DB" -f sql/03_data_quality_checks.sql
