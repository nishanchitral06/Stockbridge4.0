import os
import streamlit as st
import libsql_client
import pandas as pd


# Define DBIntegrityError so dashboard imports don't fail
class DBIntegrityError(Exception):
    """Custom exception for database integrity errors."""

    pass


def get_turso_credentials():
    """Retrieve database URL and token from Streamlit secrets or environment variables."""
    db_url = None
    auth_token = None

    # 1. Try Streamlit Secrets
    try:
        if "TURSO_DATABASE_URL" in st.secrets:
            db_url = st.secrets["TURSO_DATABASE_URL"]
        if "TURSO_AUTH_TOKEN" in st.secrets:
            auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    except Exception:
        pass

    # 2. Fall back to Environment Variables
    if not db_url:
        db_url = os.environ.get("TURSO_DATABASE_URL")
    if not auth_token:
        auth_token = os.environ.get("TURSO_AUTH_TOKEN")

    if not db_url or not auth_token:
        raise ValueError(
            "Missing Turso credentials! Please configure TURSO_DATABASE_URL "
            "and TURSO_AUTH_TOKEN in Streamlit Secrets or environment variables."
        )

    # 3. Force HTTP/HTTPS protocol to prevent WebSocket (WSServerHandshakeError) errors
    if db_url.startswith("libsql://"):
        db_url = db_url.replace("libsql://", "https://")
    elif db_url.startswith("wss://"):
        db_url = db_url.replace("wss://", "https://")
    elif not db_url.startswith("http://") and not db_url.startswith("https://"):
        db_url = f"https://{db_url}"

    return db_url, auth_token


class TursoDB:

    def __init__(self):
        url, auth_token = get_turso_credentials()
        self.client = libsql_client.create_client_sync(
            url=url, auth_token=auth_token
        )

    def execute(self, sql: str, params: list | tuple = None):
        """Execute a single SQL statement (INSERT, UPDATE, DELETE, CREATE)."""
        if params is None:
            params = []
        try:
            return self.client.execute(sql, params)
        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "FOREIGN KEY" in str(e):
                raise DBIntegrityError(str(e)) from e
            raise e

    def read_df(self, sql: str, params: list | tuple = None) -> pd.DataFrame:
        """Execute a SELECT query and return results as a Pandas DataFrame."""
        if params is None:
            params = []
        rs = self.client.execute(sql, params)
        columns = rs.columns
        rows = [list(row) for row in rs.rows]
        return pd.DataFrame(rows, columns=columns)

    def move_inventory(
        self,
        source_node_id: str,
        target_node_id: str,
        sku_id: str,
        quantity: int,
    ):
        """Deduct stock from source node and add it to target node."""
        # Deduct from source
        self.execute(
            """
            UPDATE InventorySnapshot
            SET on_hand = on_hand - ?
            WHERE node_id = ? AND sku_id = ?
            """,
            [quantity, source_node_id, sku_id],
        )

        # Add to target
        self.execute(
            """
            UPDATE InventorySnapshot
            SET on_hand = on_hand + ?
            WHERE node_id = ? AND sku_id = ?
            """,
            [quantity, target_node_id, sku_id],
        )


def get_conn() -> TursoDB:
    """Connection function expected by 05_dashboard.py."""
    return TursoDB()


def get_db() -> TursoDB:
    """Alias for get_conn."""
    return get_conn()


def move_inventory(
    source_node_id: str, target_node_id: str, sku_id: str, quantity: int
):
    """Standalone helper function expected by 05_dashboard.py."""
    conn = get_conn()
    conn.move_inventory(source_node_id, target_node_id, sku_id, quantity)
