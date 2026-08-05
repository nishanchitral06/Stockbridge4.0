"""
StockBridge - Database Schema Setup
Creates all core tables in SQLite.
"""
import sqlite3

conn = sqlite3.connect("stockbridge.db")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS SKU;
DROP TABLE IF EXISTS Node;
DROP TABLE IF EXISTS InventorySnapshot;
DROP TABLE IF EXISTS LeadTimeProfile;
DROP TABLE IF EXISTS DemandHistory;
DROP TABLE IF EXISTS TransferOrder;

CREATE TABLE SKU (
    sku_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    unit_cost REAL
);

CREATE TABLE Node (
    node_id TEXT PRIMARY KEY,
    node_name TEXT NOT NULL,
    node_type TEXT CHECK(node_type IN ('warehouse','store')),
    capacity INTEGER
);

CREATE TABLE InventorySnapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES SKU(sku_id),
    FOREIGN KEY (node_id) REFERENCES Node(node_id)
);

CREATE TABLE LeadTimeProfile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id TEXT NOT NULL,
    dest_node_id TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL,
    FOREIGN KEY (source_node_id) REFERENCES Node(node_id),
    FOREIGN KEY (dest_node_id) REFERENCES Node(node_id)
);

CREATE TABLE DemandHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    demand_date TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES SKU(sku_id),
    FOREIGN KEY (node_id) REFERENCES Node(node_id)
);

CREATE TABLE TransferOrder (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    dest_node_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT CHECK(status IN ('Requested','Approved','In-Transit','Delivered','Delayed')) DEFAULT 'Requested',
    requested_date TEXT NOT NULL,
    planned_delivery_date TEXT,
    actual_delivery_date TEXT,
    FOREIGN KEY (sku_id) REFERENCES SKU(sku_id),
    FOREIGN KEY (source_node_id) REFERENCES Node(node_id),
    FOREIGN KEY (dest_node_id) REFERENCES Node(node_id)
);
""")

conn.commit()
conn.close()
print("Schema created: stockbridge.db")
