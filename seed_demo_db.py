"""Create a reproducible, entirely synthetic retail dataset for the demo."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "retail_demo.sqlite3"
RNG = random.Random(417)


def build_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(
            """
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                age_band TEXT NOT NULL,
                city TEXT NOT NULL,
                loyalty_tier TEXT NOT NULL
            );
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL
            );
            CREATE TABLE stores (
                store_id INTEGER PRIMARY KEY,
                store_name TEXT NOT NULL,
                region TEXT NOT NULL,
                city TEXT NOT NULL
            );
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                store_id INTEGER NOT NULL REFERENCES stores(store_id),
                order_date TEXT NOT NULL,
                channel TEXT NOT NULL CHECK(channel IN ('Online', 'In-store'))
            );
            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(order_id),
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL,
                discount_pct REAL NOT NULL CHECK(discount_pct BETWEEN 0 AND 0.4)
            );
            CREATE INDEX idx_orders_date ON orders(order_date);
            CREATE INDEX idx_orders_customer ON orders(customer_id);
            CREATE INDEX idx_order_items_order ON order_items(order_id);
            CREATE INDEX idx_order_items_product ON order_items(product_id);
            """
        )

        cities = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]
        regions = ["South", "West", "North", "Central"]
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            [
                (
                    customer_id,
                    RNG.choice(["18-24", "25-34", "35-44", "45+"]),
                    RNG.choice(cities),
                    RNG.choices(["Bronze", "Silver", "Gold"], [0.5, 0.32, 0.18])[0],
                )
                for customer_id in range(1, 301)
            ],
        )

        category_prices = {
            "Electronics": ("Audio", 800, 12000),
            "Home": ("Kitchen", 250, 4500),
            "Apparel": ("Casualwear", 300, 3500),
            "Grocery": ("Packaged Foods", 40, 800),
            "Sports": ("Fitness", 250, 5000),
        }
        products = []
        for product_id in range(1, 51):
            category = list(category_prices)[(product_id - 1) // 10]
            subcategory, low, high = category_prices[category]
            products.append(
                (
                    product_id,
                    f"{subcategory} item {product_id:02d}",
                    category,
                    round(RNG.uniform(low, high), 2),
                )
            )
        connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

        stores = [
            (1, "Bengaluru Central", "South", "Bengaluru"),
            (2, "Chennai Marina", "South", "Chennai"),
            (3, "Mumbai West", "West", "Mumbai"),
            (4, "Pune Market", "West", "Pune"),
            (5, "Delhi North", "North", "Delhi"),
            (6, "Hyderabad Square", "South", "Hyderabad"),
        ]
        connection.executemany("INSERT INTO stores VALUES (?, ?, ?, ?)", stores)

        start = date(2024, 1, 1)
        order_rows = []
        item_rows = []
        item_id = 1
        for order_id in range(1, 1_201):
            order_day = start + timedelta(days=RNG.randrange(730))
            order_rows.append(
                (
                    order_id,
                    RNG.randint(1, 300),
                    RNG.randint(1, len(stores)),
                    order_day.isoformat(),
                    RNG.choices(["Online", "In-store"], [0.42, 0.58])[0],
                )
            )
            for product_id in RNG.sample(range(1, 51), RNG.randint(1, 4)):
                unit_price = products[product_id - 1][3]
                item_rows.append(
                    (
                        item_id,
                        order_id,
                        product_id,
                        RNG.randint(1, 5),
                        unit_price,
                        RNG.choice([0.0, 0.0, 0.05, 0.10, 0.15, 0.20]),
                    )
                )
                item_id += 1

        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", order_rows)
        connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", item_rows)
        connection.commit()

    print(f"Created {DB_PATH} with 300 customers, 50 products, 6 stores, "
          f"1,200 orders, and {len(item_rows):,} synthetic order items.")


if __name__ == "__main__":
    build_database()
