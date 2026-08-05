def init_db():
    """Ensure all required tables exist in Turso before querying."""
    conn = get_conn()
    tables = [
        """
        CREATE TABLE IF NOT EXISTS SKU (
            sku_id TEXT PRIMARY KEY,
            sku_name TEXT NOT NULL,
            category TEXT,
            unit_cost REAL,
            unit_price REAL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Node (
            node_id TEXT PRIMARY KEY,
            node_name TEXT NOT NULL,
            node_type TEXT CHECK(node_type IN ('DC', 'Store')),
            location TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS InventorySnapshot (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            on_hand INTEGER DEFAULT 0,
            allocated INTEGER DEFAULT 0,
            on_order INTEGER DEFAULT 0,
            snapshot_date TEXT,
            FOREIGN KEY (node_id) REFERENCES Node(node_id),
            FOREIGN KEY (sku_id) REFERENCES SKU(sku_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS LeadTimeProfile (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            lead_time_days INTEGER DEFAULT 1,
            FOREIGN KEY (source_node_id) REFERENCES Node(node_id),
            FOREIGN KEY (target_node_id) REFERENCES Node(node_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS DemandHistory (
            demand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (node_id) REFERENCES Node(node_id),
            FOREIGN KEY (sku_id) REFERENCES SKU(sku_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ReplenishmentRecommendation (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            recommended_qty INTEGER NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_node_id) REFERENCES Node(node_id),
            FOREIGN KEY (target_node_id) REFERENCES Node(node_id),
            FOREIGN KEY (sku_id) REFERENCES SKU(sku_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS TransferOrder (
            transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'APPROVED',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_node_id) REFERENCES Node(node_id),
            FOREIGN KEY (target_node_id) REFERENCES Node(node_id),
            FOREIGN KEY (sku_id) REFERENCES SKU(sku_id)
        );
        """
    ]
    for statement in tables:
        try:
            conn.execute(statement)
        except Exception:
            pass
