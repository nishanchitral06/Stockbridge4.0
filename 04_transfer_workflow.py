"""
StockBridge - Phase 3: Transfer Order Workflow
- Creates TransferOrder rows from recommendations that need replenishment
- Validates warehouse capacity before approving
- Simulates transit and marks some as Delivered / Delayed
- Tracks planned vs actual delivery
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(7)

conn = sqlite3.connect("stockbridge.db")
cur = conn.cursor()

rec = pd.read_sql("SELECT * FROM ReplenishmentRecommendation WHERE needs_replenishment = 1", conn)
lead = pd.read_sql("SELECT * FROM LeadTimeProfile", conn)
inv_wh = pd.read_sql("SELECT * FROM InventorySnapshot WHERE node_id = 'WH1'", conn)

requested_date = datetime(2026, 6, 30)

orders = []
wh_stock = dict(zip(inv_wh.sku_id, inv_wh.quantity_on_hand))

for _, row in rec.iterrows():
    sku = row["sku_id"]
    store = row["store"]
    qty = int(row["suggested_transfer_qty"])
    if qty <= 0:
        continue

    available = wh_stock.get(sku, 0)
    # Capacity validation: cap transfer at available warehouse stock
    approved_qty = min(qty, available)
    if approved_qty <= 0:
        status = "Requested"  # can't approve, nothing available
        approved_qty = 0
    else:
        wh_stock[sku] = available - approved_qty
        status = "Approved"

    lt_row = lead[(lead.source_node_id == "WH1") & (lead.dest_node_id == store)]
    lead_time_days = int(lt_row["lead_time_days"].iloc[0]) if not lt_row.empty else 4
    planned_delivery = requested_date + timedelta(days=lead_time_days)

    actual_delivery = None
    if status == "Approved":
        # simulate: 70% on time, 20% delayed by 1-3 days, 10% still in transit (no actual date yet)
        roll = np.random.rand()
        if roll < 0.7:
            actual_delivery = planned_delivery
            status = "Delivered"
        elif roll < 0.9:
            actual_delivery = planned_delivery + timedelta(days=int(np.random.randint(1, 4)))
            status = "Delayed"
        else:
            status = "In-Transit"

    orders.append((
        sku, "WH1", store, approved_qty, status,
        requested_date.strftime("%Y-%m-%d"),
        planned_delivery.strftime("%Y-%m-%d"),
        actual_delivery.strftime("%Y-%m-%d") if actual_delivery else None
    ))

cur.executemany("""
    INSERT INTO TransferOrder
    (sku_id, source_node_id, dest_node_id, quantity, status, requested_date, planned_delivery_date, actual_delivery_date)
    VALUES (?,?,?,?,?,?,?,?)
""", orders)
conn.commit()

df = pd.read_sql("SELECT * FROM TransferOrder", conn)
print(f"Created {len(df)} transfer orders.\n")
print("Status breakdown:")
print(df["status"].value_counts().to_string())

conn.close()
