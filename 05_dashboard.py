import streamlit as st
import pandas as pd
import importlib
from db import get_conn, DBIntegrityError, move_inventory


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


def load_all():
    init_db()
    conn = get_conn()
    return {
        "sku": conn.read_df("SELECT * FROM SKU"),
        "node": conn.read_df("SELECT * FROM Node"),
        "inventory": conn.read_df("SELECT * FROM InventorySnapshot"),
        "lead_time": conn.read_df("SELECT * FROM LeadTimeProfile"),
        "demand": conn.read_df("SELECT * FROM DemandHistory"),
        "rec": conn.read_df("SELECT * FROM ReplenishmentRecommendation"),
        "transfer": conn.read_df("SELECT * FROM TransferOrder"),
    }


def main():
    st.set_page_config(page_title="Stockbridge Inventory Dashboard", layout="wide")
    st.title("📦 Stockbridge Inventory Dashboard")

    data = load_all()

    # Check for empty database state
    if data["sku"].empty or data["inventory"].empty:
        st.warning("⚠️ Database connected and tables created, but no sample data exists yet.")
        if st.button("Generate & Populate Sample Data"):
            with st.spinner("Populating database..."):
                try:
                    gen_module = importlib.import_module("02_generate_sample_data")
                    if hasattr(gen_module, "generate_all_data"):
                        gen_module.generate_all_data()
                    elif hasattr(gen_module, "main"):
                        gen_module.main()
                    st.success("Sample data populated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate data automatically: {e}")
                    st.info("Run `python 02_generate_sample_data.py` manually from your environment.")
        return

    # Render main dashboard components
    st.header("Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total SKUs", len(data["sku"]))
    col2.metric("Total Nodes", len(data["node"]))
    col3.metric("Pending Recommendations", len(data["rec"]))

    st.subheader("Inventory Snapshots")
    st.dataframe(data["inventory"], use_container_width=True)

    st.subheader("Replenishment Recommendations")
    st.dataframe(data["rec"], use_container_width=True)


if __name__ == "__main__":
    main()
