"""Read-only access to the generated demo database."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "retail_demo.sqlite3"
ALLOWED_TABLES = {"customers", "products", "stores", "orders", "order_items"}
ALLOWED_FUNCTIONS = {
    "abs", "avg", "coalesce", "count", "date", "ifnull", "lower", "max",
    "min", "nullif", "printf", "round", "strftime", "substr", "sum", "total",
    "trim", "upper",
}
MAX_ROWS = 200


SCHEMA_DESCRIPTION = """
Demo data is synthetic. Tables and relationships:
- customers(customer_id INTEGER PRIMARY KEY, age_band TEXT, city TEXT, loyalty_tier TEXT)
- products(product_id INTEGER PRIMARY KEY, product_name TEXT, category TEXT, unit_price REAL)
- stores(store_id INTEGER PRIMARY KEY, store_name TEXT, region TEXT, city TEXT)
- orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER, store_id INTEGER,
  order_date TEXT in YYYY-MM-DD format, channel TEXT [Online or In-store])
- order_items(order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
  quantity INTEGER, unit_price REAL, discount_pct REAL stored from 0.00 to 0.40)
Join orders to order_items on order_id; order_items to products on product_id;
orders to customers on customer_id and stores on store_id.
Net sales = quantity * unit_price * (1 - discount_pct).
""".strip()


def _connect_read_only() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Demo database not found at {DB_PATH}. Run `python seed_demo_db.py` first."
        )

    uri = f"file:{quote(DB_PATH.as_posix(), safe='/')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=2)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.enable_load_extension(False)

    def authorize(action: int, arg1: str | None, arg2: str | None,
                  database_name: str | None, trigger_name: str | None) -> int:
        del arg2, database_name, trigger_name
        if action in {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE}:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 in ALLOWED_TABLES else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION:
            return sqlite3.SQLITE_OK if (arg1 or "").lower() in ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)
    # Abort unexpectedly expensive generated queries after a bounded amount of work.
    connection.set_progress_handler(lambda: 1, 250_000)
    return connection


def run_read_only_query(sql: str) -> tuple[list[str], list[dict[str, object]], bool]:
    """Run one model-generated read query and return columns, rows, and truncation."""
    statement = sql.strip()
    if not statement:
        raise ValueError("The model returned an empty SQL query.")
    if len(statement) > 8_000:
        raise ValueError("The generated SQL is longer than the allowed limit.")
    if not statement.upper().startswith(("SELECT", "WITH")):
        raise ValueError("Only SELECT queries are allowed.")
    if ";" in statement.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed.")

    # A wrapper caps the result even when the generated query omitted LIMIT.
    statement = statement.rstrip().removesuffix(";")
    bounded_sql = f"SELECT * FROM ({statement}) AS generated_result LIMIT {MAX_ROWS + 1}"

    with closing(_connect_read_only()) as connection:
        cursor = connection.execute(bounded_sql)
        rows = cursor.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        columns = [description[0] for description in (cursor.description or [])]
        return columns, [dict(row) for row in rows], truncated
