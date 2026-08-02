"""
StockBridge - One-Time Migration to Turso
==========================================
Run this ONCE, locally, after you've created your Turso database, to copy
your existing local stockbridge.db data (schema + all rows) into Turso.

Before running, set these two environment variables (or edit them directly
below temporarily):
    TURSO_DATABASE_URL   e.g. libsql://stockbridge-yourname.turso.io
    TURSO_AUTH_TOKEN     the token you generated in the Turso dashboard

Usage (Windows cmd):
    set TURSO_DATABASE_URL=libsql://your-db.turso.io
    set TURSO_AUTH_TOKEN=your-token-here
    python 06_migrate_to_turso.py

Usage (Mac/Linux):
    export TURSO_DATABASE_URL=libsql://your-db.turso.io
    export TURSO_AUTH_TOKEN=your-token-here
    python3 06_migrate_to_turso.py
"""
import os
import sqlite3
import sys

try:
    import libsql_client
except ImportError:
    print("ERROR: libsql_client is not installed. Run: pip install libsql-client")
    sys.exit(1)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

if not TURSO_URL or not TURSO_TOKEN:
    print("ERROR: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set as environment variables.")
    print("See the instructions at the top of this file.")
    sys.exit(1)

print(f"Connecting to Turso at {TURSO_URL} ...")
client = libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN)

print("Connecting to local stockbridge.db ...")
local = sqlite3.connect("stockbridge.db")
local.row_factory = sqlite3.Row

SCHEMA = """
DROP TABLE IF EXISTS SKU;
DROP TABLE IF EXISTS Node;
DROP TABLE IF EXISTS InventorySnapshot;
DROP TABLE IF EXISTS LeadTimeProfile;
DROP TABLE IF EXISTS DemandHistory;
DROP TABLE IF EXISTS TransferOrder;
DROP TABLE IF EXISTS ReplenishmentRecommendation;

CREATE TABLE SKU (
    sku_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    unit_cost REAL
);

CREATE TABLE Node (
    node_id TEXT PRIMARY KEY,
    node_name TEXT NOT NULL,
    node_type TEXT,
    capacity INTEGER
);

CREATE TABLE InventorySnapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL
);

CREATE TABLE LeadTimeProfile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id TEXT NOT NULL,
    dest_node_id TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL
);

CREATE TABLE DemandHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    demand_date TEXT NOT NULL,
    units_sold INTEGER NOT NULL
);

CREATE TABLE TransferOrder (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    dest_node_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT DEFAULT 'Requested',
    requested_date TEXT NOT NULL,
    planned_delivery_date TEXT,
    actual_delivery_date TEXT
);

CREATE TABLE ReplenishmentRecommendation (
    sku_id TEXT, store TEXT, avg_daily_demand REAL, lead_time_days INTEGER,
    safety_stock REAL, reorder_point REAL, current_stock INTEGER,
    days_of_stock_left REAL, needs_replenishment INTEGER,
    suggested_transfer_qty INTEGER, business_value_score REAL, risk_rank_score REAL
);
"""

print("Creating schema on Turso ...")
for stmt in [s.strip() for s in SCHEMA.split(";") if s.strip()]:
    client.execute(stmt)

TABLES = ["SKU", "Node", "InventorySnapshot", "LeadTimeProfile", "DemandHistory",
          "TransferOrder", "ReplenishmentRecommendation"]

for table in TABLES:
    rows = local.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print(f"  {table}: no rows to copy, skipping.")
        continue
    cols = rows[0].keys()
    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    for row in rows:
        client.execute(insert_sql, [row[c] for c in cols])
    print(f"  {table}: copied {len(rows)} rows.")

client.close()
local.close()
print("\nMigration complete! Your Turso database now has all your local data.")
print("Next: add TURSO_DATABASE_URL and TURSO_AUTH_TOKEN to your Streamlit Cloud app's Secrets.")
