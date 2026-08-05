"""
StockBridge - Database Connection Helper
==========================================
This module makes the rest of the app work with EITHER:
  1. Turso (cloud database) - used automatically when TURSO_DATABASE_URL and
     TURSO_AUTH_TOKEN are set (e.g. in Streamlit Cloud's "Secrets"). Data
     persists forever, across app restarts and redeploys.
  2. Local SQLite file (stockbridge.db) - used automatically as a fallback
     when no Turso credentials are found (e.g. running on your own laptop).

You don't need to change any code elsewhere - just set the two secrets and
this module switches automatically.
"""
import os
import pandas as pd


class DBIntegrityError(Exception):
    """Raised when a unique/primary key constraint is violated, regardless
    of whether we're talking to Turso or local SQLite."""
    pass


def _get_turso_credentials():
    # Try Streamlit secrets first (this is how Streamlit Cloud provides them)
    try:
        import streamlit as st
        if "TURSO_DATABASE_URL" in st.secrets and "TURSO_AUTH_TOKEN" in st.secrets:
            return st.secrets["TURSO_DATABASE_URL"], st.secrets["TURSO_AUTH_TOKEN"]
    except Exception:
        pass
    # Fall back to plain environment variables (useful for scripts / local testing)
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    if url and token:
        return url, token
    return None, None


class DBConnection:
    """
    A small wrapper so the rest of the app can call the same methods
    (execute, read_df, commit, close) no matter which backend is active.
    """

    def __init__(self):
        url, token = _get_turso_credentials()
        self.mode = "turso" if (url and token) else "sqlite"

        if self.mode == "turso":
            import libsql_client
            self.client = libsql_client.create_client_sync(url=url, auth_token=token)
        else:
            import sqlite3
            self.conn = sqlite3.connect("stockbridge.db")

    def execute(self, sql, params=None):
        params = params or []
        try:
            if self.mode == "turso":
                self.client.execute(sql, params)
            else:
                self.conn.execute(sql, params)
        except Exception as e:
            msg = str(e).upper()
            if "UNIQUE" in msg or "PRIMARY KEY" in msg or "CONSTRAINT" in msg:
                raise DBIntegrityError(str(e))
            raise

    def executescript(self, script):
        """Only used for schema setup (multiple CREATE TABLE statements)."""
        if self.mode == "turso":
            for stmt in [s.strip() for s in script.split(";") if s.strip()]:
                self.client.execute(stmt)
        else:
            self.conn.executescript(script)

    def executemany(self, sql, rows):
        if self.mode == "turso":
            for row in rows:
                self.client.execute(sql, list(row))
        else:
            self.conn.executemany(sql, rows)

    def read_df(self, sql, params=None):
        """
        params must be supported here - without it, any query that needs to
        look up a specific SKU/location (like get_latest_qty below) silently
        breaks, which is what was blocking stock transfers.
        """
        params = params or []
        if self.mode == "turso":
            rs = self.client.execute(sql, params)
            return pd.DataFrame([list(r) for r in rs.rows], columns=rs.columns)
        else:
            return pd.read_sql(sql, self.conn, params=params)

    def commit(self):
        if self.mode == "sqlite":
            self.conn.commit()
        # Turso's client commits each statement over HTTP automatically -
        # nothing extra needed here.

    def close(self):
        if self.mode == "turso":
            self.client.close()
        else:
            self.conn.close()


def get_conn():
    return DBConnection()


def get_latest_qty(conn, sku_id, node_id):
    """Returns the most recent quantity_on_hand for a SKU at a location (0 if none exists yet)."""
    df = conn.read_df(
        "SELECT quantity_on_hand FROM InventorySnapshot "
        "WHERE sku_id=? AND node_id=? ORDER BY snapshot_date DESC LIMIT 1",
        [sku_id, node_id]
    )
    return int(df["quantity_on_hand"].iloc[0]) if not df.empty else 0


def move_inventory(conn, sku_id, source_node_id, dest_node_id, qty, move_date):
    """
    Moves `qty` units of `sku_id` from source_node_id to dest_node_id by
    writing two new InventorySnapshot rows dated `move_date` (a string like
    '2026-08-05'): source reduced, destination increased.
    """
    src_qty = get_latest_qty(conn, sku_id, source_node_id)
    dest_qty = get_latest_qty(conn, sku_id, dest_node_id)

    conn.execute(
        "INSERT INTO InventorySnapshot (sku_id, node_id, snapshot_date, quantity_on_hand) VALUES (?,?,?,?)",
        (sku_id, source_node_id, move_date, max(src_qty - qty, 0))
    )
    conn.execute(
        "INSERT INTO InventorySnapshot (sku_id, node_id, snapshot_date, quantity_on_hand) VALUES (?,?,?,?)",
        (sku_id, dest_node_id, move_date, dest_qty + qty)
    )
