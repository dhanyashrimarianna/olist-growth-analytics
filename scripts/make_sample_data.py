"""Generate a small synthetic dataset with the SAME schema (and known quirks) as the Olist CSVs.

Purpose: smoke-test the SQL pipeline without the real data. NOT for analysis or resume claims.
Quirks reproduced on purpose: customer_id unique per order, duplicate review_ids,
NULL product categories, split payments, out-of-order timestamps, undelivered orders,
many geolocation rows per zip prefix.

Usage: python scripts/make_sample_data.py  ->  writes CSVs to data/sample/
"""
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_PEOPLE, N_SELLERS, N_PRODUCTS = 1500, 60, 300
OUT = Path(__file__).resolve().parents[1] / "data" / "sample"

random.seed(SEED)
uid = lambda: uuid.UUID(int=random.getrandbits(128)).hex  # deterministic ids

STATES = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE"]
CITIES = {"SP": "sao paulo", "RJ": "rio de janeiro", "MG": "belo horizonte", "RS": "porto alegre",
          "PR": "curitiba", "BA": "salvador", "SC": "florianopolis", "PE": "recife"}
CATS = ["cama_mesa_banho", "beleza_saude", "esporte_lazer", "informatica_acessorios",
        "moveis_decoracao", "brinquedos", "relogios_presentes", "telefonia"]
CATS_EN = ["bed_bath_table", "health_beauty", "sports_leisure", "computers_accessories",
           "furniture_decor", "toys", "watches_gifts", "telephony"]

# --- geolocation: several rows per zip prefix ---
zips = [f"{random.randint(1000, 99999):05d}" for _ in range(200)]
geo = []
for z in zips:
    s = random.choice(STATES)
    for _ in range(random.randint(1, 4)):
        geo.append([z, -23 + random.uniform(-3, 3), -46 + random.uniform(-3, 3), CITIES[s], s])
geo = pd.DataFrame(geo, columns=["geolocation_zip_code_prefix", "geolocation_lat",
                                 "geolocation_lng", "geolocation_city", "geolocation_state"])

# --- sellers / products ---
sellers = pd.DataFrame({"seller_id": [uid() for _ in range(N_SELLERS)]})
sellers["seller_zip_code_prefix"] = [random.choice(zips) for _ in range(N_SELLERS)]
sellers["seller_state"] = [random.choice(STATES) for _ in range(N_SELLERS)]
sellers["seller_city"] = sellers["seller_state"].map(CITIES)
sellers = sellers[["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]]

products = pd.DataFrame({"product_id": [uid() for _ in range(N_PRODUCTS)]})
products["product_category_name"] = [random.choice(CATS) if random.random() > 0.02 else None
                                     for _ in range(N_PRODUCTS)]
products["product_name_lenght"] = [random.randint(20, 60) for _ in range(N_PRODUCTS)]
products["product_description_lenght"] = [random.randint(100, 2000) for _ in range(N_PRODUCTS)]
products["product_photos_qty"] = [random.randint(1, 6) for _ in range(N_PRODUCTS)]
products["product_weight_g"] = [random.randint(100, 8000) for _ in range(N_PRODUCTS)]
products["product_length_cm"] = [random.randint(10, 60) for _ in range(N_PRODUCTS)]
products["product_height_cm"] = [random.randint(5, 40) for _ in range(N_PRODUCTS)]
products["product_width_cm"] = [random.randint(10, 50) for _ in range(N_PRODUCTS)]
translation = pd.DataFrame({"product_category_name": CATS, "product_category_name_english": CATS_EN})

# --- customers / orders / items / payments / reviews ---
people = [uid() for _ in range(N_PEOPLE)]
start = datetime(2017, 1, 1)
customers, orders, items, pays, reviews = [], [], [], [], []

for person in people:
    n_orders = 1 if random.random() < 0.94 else random.randint(2, 4)  # sample only; real Olist has a much lower repeat rate
    zip_ = random.choice(zips)
    st = random.choice(STATES)
    t = start + timedelta(days=random.randint(0, 600), hours=random.randint(0, 23))
    for _ in range(n_orders):
        cid, oid = uid(), uid()  # customer_id is unique PER ORDER
        customers.append([cid, person, zip_, CITIES[st], st])
        status = random.choices(["delivered", "shipped", "canceled", "processing"],
                                [0.93, 0.03, 0.03, 0.01])[0]
        approved = t + timedelta(hours=random.randint(0, 24))
        carrier = approved + timedelta(days=random.randint(1, 5))
        transit = random.randint(3, 25)
        delivered = carrier + timedelta(days=transit) if status == "delivered" else None
        estimated = t + timedelta(days=random.randint(12, 30))
        if status != "delivered":
            carrier = carrier if status == "shipped" else None
        if random.random() < 0.01:  # out-of-order timestamp quirk
            carrier = t - timedelta(days=2)
        orders.append([oid, cid, status, t, approved, carrier, delivered, estimated])

        total = 0.0
        for k in range(1, random.choices([1, 2, 3], [0.88, 0.09, 0.03])[0] + 1):
            price = round(random.lognormvariate(4.3, 0.8), 2)
            freight = round(random.uniform(8, 45), 2)
            total += price + freight
            items.append([oid, k, random.choice(products.product_id), random.choice(sellers.seller_id),
                          carrier or approved, price, freight])
        if random.random() < 0.03:  # split payment across two methods
            pays.append([oid, 1, "voucher", 1, round(total * 0.3, 2)])
            pays.append([oid, 2, "credit_card", random.randint(1, 6), round(total * 0.7, 2)])
        else:
            pays.append([oid, 1, random.choices(["credit_card", "boleto", "debit_card"], [0.75, 0.2, 0.05])[0],
                         random.choice([1, 1, 2, 3, 6, 10]), round(total, 2)])

        if random.random() < 0.98:  # review; late deliveries score lower
            late = delivered is not None and delivered > estimated
            score = random.choices([1, 2, 3, 4, 5], [0.45, 0.15, 0.15, 0.15, 0.10] if late
                                   else [0.04, 0.03, 0.08, 0.2, 0.65])[0]
            created = (delivered or t) + timedelta(days=1)
            answered = created + timedelta(days=random.randint(0, 3))
            rid = uid()
            reviews.append([rid, oid, score, None, None, created, answered])
            if random.random() < 0.01:  # duplicate review_id quirk (two answers for one order)
                reviews.append([rid, oid, min(5, score + 1), None, None, created, answered + timedelta(days=1)])
        t = t + timedelta(days=random.randint(30, 200))

fmt = lambda d: d.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(d) else None
cust = pd.DataFrame(customers, columns=["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                                        "customer_city", "customer_state"])
ords = pd.DataFrame(orders, columns=["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                                     "order_approved_at", "order_delivered_carrier_date",
                                     "order_delivered_customer_date", "order_estimated_delivery_date"])
for c in ords.columns[3:]:
    ords[c] = ords[c].map(fmt)
itm = pd.DataFrame(items, columns=["order_id", "order_item_id", "product_id", "seller_id",
                                   "shipping_limit_date", "price", "freight_value"])
itm["shipping_limit_date"] = itm["shipping_limit_date"].map(fmt)
pay = pd.DataFrame(pays, columns=["order_id", "payment_sequential", "payment_type",
                                  "payment_installments", "payment_value"])
rev = pd.DataFrame(reviews, columns=["review_id", "order_id", "review_score", "review_comment_title",
                                     "review_comment_message", "review_creation_date",
                                     "review_answer_timestamp"])
rev["review_creation_date"] = rev["review_creation_date"].map(fmt)
rev["review_answer_timestamp"] = rev["review_answer_timestamp"].map(fmt)

OUT.mkdir(parents=True, exist_ok=True)
files = {
    "olist_customers_dataset.csv": cust, "olist_geolocation_dataset.csv": geo,
    "olist_order_items_dataset.csv": itm, "olist_order_payments_dataset.csv": pay,
    "olist_order_reviews_dataset.csv": rev, "olist_orders_dataset.csv": ords,
    "olist_products_dataset.csv": products, "olist_sellers_dataset.csv": sellers,
    "product_category_name_translation.csv": translation,
}
for name, df in files.items():
    df.to_csv(OUT / name, index=False)
    print(f"{name:45s} {len(df):>6,} rows")
