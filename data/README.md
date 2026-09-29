# Data

**Source:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle, CC BY-NC-SA 4.0).
About 100k orders placed at multiple marketplaces in Brazil, 2016 to 2018.

## Get the data

1. Download the dataset zip from Kaggle (free account required).
2. Unzip all 9 CSVs into `data/raw/`:

```
data/raw/
├── olist_customers_dataset.csv
├── olist_geolocation_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

Raw CSVs are git-ignored on purpose (licence and repo size). `data/sample/` holds a tiny
synthetic dataset with the same schema, used only to smoke-test the pipeline
(`python scripts/make_sample_data.py`).

See `docs/data_dictionary.md` for every column and known data quality issues.
