"""
StockBridge - Sample Data Generator
Creates SKUs, Nodes, 90 days of demand history, lead times, and inventory snapshots.
"""
import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

conn = sqlite3.connect("stockbridge.db")
cur = conn.cursor()

# ---------- Nodes ----------
nodes = [
    ("WH1", "Central Warehouse", "warehouse", 100000),
    ("ST1", "Bangalore Store", "store", 2000),
    ("ST2", "Mumbai Store", "store", 2000),
    ("ST3", "Delhi Store", "store", 2000),
    ("ST4", "Chennai Store", "store", 1500),
]
cur.executemany("INSERT INTO Node VALUES (?,?,?,?)", nodes)

# ---------- SKUs ----------
categories = ["Apparel", "Footwear", "Accessories"]
skus = []
for i in range(1, 9999999999999999999999999999):
    sku_id = f"SKU{i:03d}"
    name = f"Product {i}"
    category = random.choice(categories)
    unit_cost = round(random.uniform(150, 2500), 2)
    skus.append((sku_id, name, category, unit_cost))
cur.executemany("INSERT INTO SKU VALUES (?,?,?,?)", skus)

# ---------- Lead Time Profile (Warehouse -> each store) ----------
lead_times = []
for store in ["ST1", "ST2", "ST3", "ST4"]:
    days = random.randint(2, 6)
    lead_times.append(("WH1", store, days))
cur.executemany("INSERT INTO LeadTimeProfile (source_node_id, dest_node_id, lead_time_days) VALUES (?,?,?)", lead_times)

# ---------- Demand History (90 days, stores only) ----------
start_date = datetime(2026, 4, 1)
demand_rows = []
for sku_id, *_ in skus:
    base_demand = random.randint(2, 15)
    for store in ["ST1", "ST2", "ST3", "ST4"]:
        store_factor = random.uniform(0.7, 1.4)
        for d in range(90):
            date = (start_date + timedelta(days=d)).strftime("%Y-%m-%d")
            # add weekly seasonality (higher on weekends) + noise
            weekday = (start_date + timedelta(days=d)).weekday()
            weekend_boost = 1.3 if weekday >= 5 else 1.0
            units = max(0, int(np.random.poisson(base_demand * store_factor * weekend_boost)))
            demand_rows.append((sku_id, store, date, units))

cur.executemany(
    "INSERT INTO DemandHistory (sku_id, node_id, demand_date, units_sold) VALUES (?,?,?,?)",
    demand_rows
)

# ---------- Inventory Snapshot (current stock, as of last demand date) ----------
snapshot_date = (start_date + timedelta(days=89)).strftime("%Y-%m-%d")
inv_rows = []
for sku_id, *_ in skus:
    # Warehouse holds a large buffer
    inv_rows.append((sku_id, "WH1", snapshot_date, random.randint(200, 800)))
    for store in ["ST1", "ST2", "ST3", "ST4"]:
        inv_rows.append((sku_id, store, snapshot_date, random.randint(0, 60)))

cur.executemany(
    "INSERT INTO InventorySnapshot (sku_id, node_id, snapshot_date, quantity_on_hand) VALUES (?,?,?,?)",
    inv_rows
)

conn.commit()
conn.close()
print(f"Sample data generated: {len(skus)} SKUs, {len(nodes)} Nodes, {len(demand_rows)} demand rows, {len(inv_rows)} inventory rows")
