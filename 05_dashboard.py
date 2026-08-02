"""
StockBridge - Phase 4: Inventory Performance Dashboard (Futuristic Dark Theme + Editable + Trackable)
Run with: streamlit run 05_dashboard.py

Data now persists permanently via Turso (cloud database) when TURSO_DATABASE_URL
and TURSO_AUTH_TOKEN are configured in Streamlit Cloud secrets. Falls back to
a local stockbridge.db file automatically when running on your own laptop.

Theme is locked to dark mode via .streamlit/config.toml so text stays readable
regardless of the viewer's system/browser theme setting.
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from db import get_conn, DBIntegrityError

st.set_page_config(page_title="StockBridge Dashboard", page_icon="📦", layout="wide")

# ---------------- Custom CSS: Futuristic Dark Theme ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg-deep: #05070d;
        --bg-mid: #0a0f1e;
        --panel: rgba(18, 25, 45, 0.55);
        --panel-border: rgba(0, 229, 255, 0.18);
        --cyan: #22e5ff;
        --violet: #9d7bff;
        --pink: #ff5cb3;
        --text-primary: #e9edf7;
        --text-muted: #8b95ab;
        --good: #33e6a0;
        --warn: #ffb545;
        --bad: #ff5c7a;
    }

    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    code, .stCodeBlock, .stCode { font-family: 'JetBrains Mono', monospace !important; }

    /* ---------- Global app background: deep space gradient + glow grid ---------- */
    .stApp {
        background:
            radial-gradient(circle at 15% 0%, rgba(34,229,255,0.10) 0%, transparent 45%),
            radial-gradient(circle at 85% 15%, rgba(157,123,255,0.12) 0%, transparent 45%),
            radial-gradient(circle at 50% 100%, rgba(255,92,179,0.08) 0%, transparent 50%),
            linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-mid) 100%);
        background-attachment: fixed;
        color: var(--text-primary);
    }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    /* ---------- Force readable text everywhere, regardless of viewer's theme toggle ---------- */
    h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown, .stCaption, .stText {
        color: var(--text-primary);
    }
    .stCaption, small, [data-testid="stCaptionContainer"] { color: var(--text-muted) !important; }

    /* Inputs, selects, dropdowns */
    .stTextInput input, .stNumberInput input, .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.04) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
    }
    .stTextInput label, .stNumberInput label, .stDateInput label,
    .stSelectbox label, .stMultiSelect label { color: var(--text-muted) !important; font-size: 13px !important; }
    ul[data-testid="stSelectboxVirtualDropdown"] li, div[data-baseweb="popover"] li { color: #0b0f1a !important; }

    /* Alerts (info / success / warning / error) */
    div[data-testid="stAlert"] { border-radius: 10px !important; backdrop-filter: blur(6px); }
    div[data-testid="stAlert"] p { color: var(--text-primary) !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted); font-weight: 600; font-size: 14px;
        background: transparent; border-radius: 8px 8px 0 0; padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--cyan) !important;
        background: rgba(34,229,255,0.08) !important;
        border-bottom: 2px solid var(--cyan) !important;
    }

    /* Dataframes / tables */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); }

    /* Expanders (main area, if any) */
    div[data-testid="stExpander"] {
        background: var(--panel); border: 1px solid var(--panel-border); border-radius: 12px;
    }

    /* ---------- Hero banner ---------- */
    .hero {
        position: relative;
        background: linear-gradient(120deg, rgba(34,229,255,0.15) 0%, rgba(157,123,255,0.18) 50%, rgba(255,92,179,0.12) 100%);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 28px 32px;
        border-radius: 18px;
        margin-bottom: 24px;
        backdrop-filter: blur(14px);
        box-shadow: 0 0 40px rgba(34,229,255,0.08), inset 0 1px 0 rgba(255,255,255,0.06);
        overflow: hidden;
    }
    .hero::before {
        content: ""; position: absolute; inset: 0;
        background: linear-gradient(90deg, var(--cyan), var(--violet), var(--pink));
        opacity: 0.9; height: 3px; top: 0; left: 0; right: 0;
    }
    .hero h1 {
        margin: 0; font-size: 30px; font-weight: 700; letter-spacing: 0.5px;
        background: linear-gradient(90deg, #ffffff, var(--cyan));
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p { color: var(--text-muted); margin: 6px 0 0 0; font-size: 14px; }

    /* ---------- KPI cards ---------- */
    .kpi-card {
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 18px 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.35);
        transition: all 0.2s ease;
    }
    .kpi-card:hover { border-color: rgba(34,229,255,0.45); box-shadow: 0 4px 28px rgba(34,229,255,0.15); transform: translateY(-2px); }
    .kpi-label { color: var(--text-muted); font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value {
        font-size: 30px; font-weight: 700; margin-top: 6px;
        background: linear-gradient(90deg, var(--cyan), var(--violet));
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    }
    .kpi-sub { font-size: 12px; margin-top: 6px; font-weight: 500; }
    .kpi-good { color: var(--good); }
    .kpi-warn { color: var(--warn); }
    .kpi-bad { color: var(--bad); }

    .section-title {
        color: var(--text-primary); font-size: 18px; font-weight: 700;
        margin-top: 8px; margin-bottom: 14px;
        border-left: 3px solid var(--cyan); padding-left: 12px;
        text-shadow: 0 0 18px rgba(34,229,255,0.25);
    }

    .status-badge {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 11.5px; font-weight: 700; color: #06121a;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070b16 0%, #0c1226 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
    .sidebar-hero {
        background: linear-gradient(135deg, rgba(34,229,255,0.18) 0%, rgba(157,123,255,0.22) 100%);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
        padding: 16px 16px;
        margin-bottom: 18px;
        box-shadow: 0 0 24px rgba(34,229,255,0.10);
    }
    .sidebar-hero h2 { color: #ffffff; margin: 0; font-size: 17px; }
    .sidebar-hero p { color: rgba(233,237,247,0.8); margin: 4px 0 0 0; font-size: 12px; line-height: 1.4; }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        margin-bottom: 10px;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
        font-weight: 600; font-size: 13.5px; color: var(--text-primary) !important;
        padding: 4px 2px;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary span { color: var(--text-primary) !important; }
    section[data-testid="stSidebar"] div[data-testid="stExpander"]:hover { border-color: rgba(34,229,255,0.4); }

    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stFormSubmitButton button {
        background: linear-gradient(135deg, var(--cyan) 0%, var(--violet) 100%);
        color: #06121a; border: none; border-radius: 8px;
        font-weight: 700; font-size: 13px; padding: 7px 14px;
        width: 100%; transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton button:hover,
    section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
        box-shadow: 0 0 18px rgba(34,229,255,0.5);
        transform: translateY(-1px);
    }

    .sidebar-note {
        background: rgba(255,181,69,0.08);
        border-left: 3px solid var(--warn);
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 11.5px;
        color: rgba(233,237,247,0.85);
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

STATUS_COLORS = {
    "Delivered": "#33e6a0", "Approved": "#22e5ff", "In-Transit": "#ffb545",
    "Delayed": "#ff5c7a", "Requested": "#9d7bff"
}


def load_all():
    conn = get_conn()
    data = {
        "rec": conn.read_df("SELECT * FROM ReplenishmentRecommendation"),
        "orders": conn.read_df("SELECT * FROM TransferOrder"),
        "skus": conn.read_df("SELECT * FROM SKU"),
        "nodes": conn.read_df("SELECT * FROM Node"),
        "inv": conn.read_df("SELECT * FROM InventorySnapshot"),
        "demand": conn.read_df("SELECT * FROM DemandHistory"),
    }
    conn.close()
    return data


data = load_all()
rec, orders, skus, nodes, inv, demand = (
    data["rec"], data["orders"], data["skus"], data["nodes"], data["inv"], data["demand"]
)

# ================= SIDEBAR: Add / Edit Data =================
st.sidebar.markdown("""
<div class="sidebar-hero">
    <h2>⚙️ Manage StockBridge</h2>
    <p>Add or update records — changes save instantly. Find everything you add under <b>Browse All Data</b> and <b>Order Tracking</b>.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("🆕  Add New SKU", expanded=False):
    with st.form("add_sku_form", clear_on_submit=True):
        new_sku_id = st.text_input("SKU ID (e.g. SKU019)")
        new_sku_name = st.text_input("Product Name")
        new_sku_cat = st.selectbox("Category", ["Apparel", "Footwear", "Accessories", "Other"])
        new_sku_cost = st.number_input("Unit Cost", min_value=0.0, value=100.0, step=10.0)
        submitted = st.form_submit_button("Add SKU")
        if submitted:
            if new_sku_id and new_sku_name:
                conn = get_conn()
                try:
                    conn.execute(
                        "INSERT INTO SKU (sku_id, product_name, category, unit_cost) VALUES (?,?,?,?)",
                        (new_sku_id, new_sku_name, new_sku_cat, new_sku_cost)
                    )
                    conn.commit()
                    st.success(f"Added {new_sku_id}. Find it under 'Browse All Data > SKUs'.")
                    st.rerun()
                except DBIntegrityError:
                    st.error("That SKU ID already exists.")
                finally:
                    conn.close()
            else:
                st.warning("SKU ID and Product Name are required.")

with st.sidebar.expander("📍  Add New Node (Warehouse/Store)", expanded=False):
    with st.form("add_node_form", clear_on_submit=True):
        new_node_id = st.text_input("Node ID (e.g. ST5)")
        new_node_name = st.text_input("Node Name")
        new_node_type = st.selectbox("Type", ["store", "warehouse"])
        new_node_cap = st.number_input("Capacity", min_value=0, value=2000, step=100)
        submitted = st.form_submit_button("Add Node")
        if submitted:
            if new_node_id and new_node_name:
                conn = get_conn()
                try:
                    conn.execute(
                        "INSERT INTO Node (node_id, node_name, node_type, capacity) VALUES (?,?,?,?)",
                        (new_node_id, new_node_name, new_node_type, new_node_cap)
                    )
                    conn.commit()
                    st.success(f"Added {new_node_id}. Find it under 'Browse All Data > Locations'.")
                    st.rerun()
                except DBIntegrityError:
                    st.error("That Node ID already exists.")
                finally:
                    conn.close()
            else:
                st.warning("Node ID and Name are required.")

with st.sidebar.expander("📊  Update Inventory Snapshot", expanded=False):
    with st.form("add_inv_form", clear_on_submit=True):
        inv_sku = st.selectbox("SKU", skus["sku_id"].tolist() if not skus.empty else [])
        inv_node = st.selectbox("Node", nodes["node_id"].tolist() if not nodes.empty else [])
        inv_qty = st.number_input("Quantity on Hand", min_value=0, value=0, step=1)
        inv_date = st.date_input("Snapshot Date", value=date.today())
        submitted = st.form_submit_button("Save Snapshot")
        if submitted:
            conn = get_conn()
            conn.execute(
                "INSERT INTO InventorySnapshot (sku_id, node_id, snapshot_date, quantity_on_hand) VALUES (?,?,?,?)",
                (inv_sku, inv_node, inv_date.strftime("%Y-%m-%d"), inv_qty)
            )
            conn.commit()
            conn.close()
            st.success("Saved. Find it under 'Browse All Data > Inventory Snapshots'.")
            st.rerun()

with st.sidebar.expander("🚚  Create Transfer Order", expanded=False):
    with st.form("add_transfer_form", clear_on_submit=True):
        t_sku = st.selectbox("SKU", skus["sku_id"].tolist() if not skus.empty else [], key="t_sku")
        t_source = st.selectbox("Source Node", nodes["node_id"].tolist() if not nodes.empty else [], key="t_source")
        t_dest = st.selectbox("Destination Node", nodes["node_id"].tolist() if not nodes.empty else [], key="t_dest")
        t_qty = st.number_input("Quantity", min_value=1, value=10, step=1)
        t_status = st.selectbox("Status", ["Requested", "Approved", "In-Transit", "Delivered", "Delayed"])
        t_req_date = st.date_input("Requested Date", value=date.today())
        t_planned_date = st.date_input("Planned Delivery Date", value=date.today())
        submitted = st.form_submit_button("Create Transfer Order")
        if submitted:
            conn = get_conn()
            conn.execute("""
                INSERT INTO TransferOrder
                (sku_id, source_node_id, dest_node_id, quantity, status, requested_date, planned_delivery_date)
                VALUES (?,?,?,?,?,?,?)
            """, (t_sku, t_source, t_dest, t_qty, t_status,
                  t_req_date.strftime("%Y-%m-%d"), t_planned_date.strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Order created. Find it under the 'Order Tracking' tab.")
            st.rerun()

with st.sidebar.expander("🔄  Update Transfer Order Status", expanded=False):
    if not orders.empty:
        with st.form("update_status_form"):
            order_id = st.selectbox("Transfer ID", orders["transfer_id"].tolist())
            new_status = st.selectbox("New Status", ["Requested", "Approved", "In-Transit", "Delivered", "Delayed"])
            actual_date = st.date_input("Actual Delivery Date (if Delivered/Delayed)", value=date.today())
            submitted = st.form_submit_button("Update Status")
            if submitted:
                conn = get_conn()
                if new_status in ("Delivered", "Delayed"):
                    conn.execute(
                        "UPDATE TransferOrder SET status=?, actual_delivery_date=? WHERE transfer_id=?",
                        (new_status, actual_date.strftime("%Y-%m-%d"), int(order_id))
                    )
                else:
                    conn.execute(
                        "UPDATE TransferOrder SET status=? WHERE transfer_id=?",
                        (new_status, int(order_id))
                    )
                conn.commit()
                conn.close()
                st.success(f"Transfer #{order_id} updated to {new_status}. Check 'Order Tracking' to confirm.")
                st.rerun()
    else:
        st.caption("No transfer orders yet.")

st.sidebar.divider()
st.sidebar.markdown("""
<div class="sidebar-note">
    ⚠️ <b>Note:</b> KPI numbers (Fill Rate, Reorder Points) refresh only after you re-run <code>03_replenishment_engine.py</code> — they're computed, not live-editable.
</div>
""", unsafe_allow_html=True)


def kpi_card(label, value, sub_text, sub_class):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub {sub_class}">{sub_text}</div>
    </div>
    """


def status_badge(status):
    color = STATUS_COLORS.get(status, "#888")
    return f'<span class="status-badge" style="background:{color}">{status}</span>'


# ================= MAIN DASHBOARD =================
st.markdown("""
<div class="hero">
    <h1>📦 StockBridge</h1>
    <p>Multi-Echelon Inventory Replenishment Planner &nbsp;•&nbsp; Logistics & Supply Chain Intern Project</p>
</div>
""", unsafe_allow_html=True)

tab_overview, tab_browse, tab_tracking = st.tabs(["📊 Overview", "🔍 Browse All Data", "🚚 Order Tracking"])

# ---------------- TAB 1: OVERVIEW ----------------
with tab_overview:
    total_skus_stores = len(rec)
    need_replenishment = rec["needs_replenishment"].sum() if total_skus_stores else 0
    fill_rate = 100 * (1 - need_replenishment / total_skus_stores) if total_skus_stores else 0

    delivered = orders[orders.status == "Delivered"]
    delayed = orders[orders.status == "Delayed"]
    on_time_rate = 100 * len(delivered) / max(1, len(delivered) + len(delayed))

    store_demand_total = demand.groupby("sku_id")["units_sold"].sum().sum() if not demand.empty else 0
    store_inv_total = inv[inv.node_id != "WH1"]["quantity_on_hand"].sum() if not inv.empty else 0
    turnover = round(store_demand_total / max(1, store_inv_total), 2)

    dead_stock = rec[(rec.avg_daily_demand < 1) & (rec.current_stock > 20)] if total_skus_stores else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cls = "kpi-good" if fill_rate >= 70 else ("kpi-warn" if fill_rate >= 40 else "kpi-bad")
        st.markdown(kpi_card("Fill Rate", f"{fill_rate:.1f}%", f"{int(need_replenishment)} of {total_skus_stores} need action", cls), unsafe_allow_html=True)
    with c2:
        cls = "kpi-good" if on_time_rate >= 85 else ("kpi-warn" if on_time_rate >= 70 else "kpi-bad")
        st.markdown(kpi_card("On-Time Delivery", f"{on_time_rate:.1f}%", f"{len(delayed)} delayed orders", cls), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Inventory Turnover", f"{turnover}x", "90-day rolling window", "kpi-good"), unsafe_allow_html=True)
    with c4:
        cls = "kpi-good" if len(dead_stock) == 0 else "kpi-warn"
        st.markdown(kpi_card("Dead Stock Items", f"{len(dead_stock)}", "low demand, high stock", cls), unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="section-title">🚨 Stockout Prevention Scorecard — Top Priority Items</div>', unsafe_allow_html=True)
    if total_skus_stores:
        priority = rec[rec.needs_replenishment == 1].sort_values("risk_rank_score", ascending=False).head(15).copy()
        priority_display = priority[["sku_id","store","current_stock","reorder_point","days_of_stock_left","suggested_transfer_qty"]].rename(columns={
            "sku_id": "SKU", "store": "Store", "current_stock": "Current Stock",
            "reorder_point": "Reorder Point", "days_of_stock_left": "Days Left", "suggested_transfer_qty": "Suggested Qty"
        })
        st.dataframe(
            priority_display.style.background_gradient(subset=["Days Left"], cmap="RdYlGn"),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No recommendation data yet. Run 03_replenishment_engine.py first.")

    st.write("")

    col5, col6 = st.columns(2)
    with col5:
        st.markdown('<div class="section-title">Transfer Order Status</div>', unsafe_allow_html=True)
        if not orders.empty:
            status_counts = orders["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig1 = go.Figure(data=[go.Pie(
                labels=status_counts["status"], values=status_counts["count"], hole=0.6,
                marker=dict(colors=[STATUS_COLORS.get(s, "#888") for s in status_counts["status"]],
                            line=dict(color="#05070d", width=2)),
                textinfo="label+percent", textfont=dict(size=13, color="#e9edf7")
            )])
            fig1.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=340,
                annotations=[dict(text=f"{len(orders)}<br>Orders", x=0.5, y=0.5, font_size=18, font_color="#22e5ff", showarrow=False)]
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No transfer orders yet.")

    with col6:
        st.markdown('<div class="section-title">Delivery Delay Distribution</div>', unsafe_allow_html=True)
        comp = orders.dropna(subset=["actual_delivery_date"]).copy()
        if not comp.empty:
            comp["planned_delivery_date"] = pd.to_datetime(comp["planned_delivery_date"])
            comp["actual_delivery_date"] = pd.to_datetime(comp["actual_delivery_date"])
            comp["delay_days"] = (comp["actual_delivery_date"] - comp["planned_delivery_date"]).dt.days
            fig2 = px.histogram(comp, x="delay_days", nbins=8, color_discrete_sequence=["#22e5ff"])
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e9edf7", margin=dict(t=10, b=10, l=10, r=10), height=340,
                xaxis_title="Delay (days)", yaxis_title="Orders",
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)")
            )
            fig2.update_traces(marker_line_color="#05070d", marker_line_width=1)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No completed deliveries yet.")

    st.write("")

    st.markdown('<div class="section-title">Top 10 Highest-Risk SKU-Store Combinations</div>', unsafe_allow_html=True)
    if total_skus_stores:
        top_risk = priority.head(10).copy()
        if not top_risk.empty:
            top_risk["label"] = top_risk["sku_id"] + " @ " + top_risk["store"]
            fig3 = px.bar(
                top_risk.sort_values("days_of_stock_left"), x="days_of_stock_left", y="label", orientation="h",
                color="days_of_stock_left", color_continuous_scale=["#ff5c7a", "#ffb545", "#33e6a0"],
                labels={"days_of_stock_left": "Days of Stock Left", "label": ""}
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e9edf7", margin=dict(t=10, b=10, l=10, r=10), height=380, coloraxis_showscale=False,
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.03)")
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.success("Nothing currently at risk.")
    else:
        st.info("No recommendation data yet.")

    st.write("")

    st.markdown('<div class="section-title">💀 Dead Stock — Low Demand, High Inventory</div>', unsafe_allow_html=True)
    if len(dead_stock) > 0:
        dead_display = dead_stock[["sku_id","store","current_stock","avg_daily_demand"]].sort_values("current_stock", ascending=False).rename(columns={
            "sku_id": "SKU", "store": "Store", "current_stock": "Current Stock", "avg_daily_demand": "Avg Daily Demand"
        })
        st.dataframe(dead_display, use_container_width=True, hide_index=True)
    else:
        st.success("No dead stock detected in the current dataset.")

    st.caption("Data is simulated for demonstration purposes as part of the StockBridge internship project. Use the sidebar to add or update records.")

# ---------------- TAB 2: BROWSE ALL DATA ----------------
with tab_browse:
    st.markdown('<div class="section-title">🔍 Browse Everything in the System</div>', unsafe_allow_html=True)
    st.caption("Every SKU, location, and inventory record you've ever added lives here — searchable, always visible.")

    sub_sku, sub_node, sub_inv = st.tabs(["📦 SKUs", "📍 Locations (Nodes)", "📊 Stock Quantity by Location"])

    with sub_sku:
        st.write(f"**{len(skus)} SKUs in the system**")
        search_sku = st.text_input("Search by SKU ID or Product Name", key="search_sku")
        filtered_skus = skus.copy()
        if search_sku:
            mask = (
                filtered_skus["sku_id"].str.contains(search_sku, case=False, na=False) |
                filtered_skus["product_name"].str.contains(search_sku, case=False, na=False)
            )
            filtered_skus = filtered_skus[mask]
        st.dataframe(
            filtered_skus.rename(columns={
                "sku_id": "SKU ID", "product_name": "Product Name",
                "category": "Category", "unit_cost": "Unit Cost"
            }).sort_values("SKU ID"),
            use_container_width=True, hide_index=True
        )

    with sub_node:
        st.write(f"**{len(nodes)} Locations in the system**")
        search_node = st.text_input("Search by Node ID or Name", key="search_node")
        filtered_nodes = nodes.copy()
        if search_node:
            mask = (
                filtered_nodes["node_id"].str.contains(search_node, case=False, na=False) |
                filtered_nodes["node_name"].str.contains(search_node, case=False, na=False)
            )
            filtered_nodes = filtered_nodes[mask]
        st.dataframe(
            filtered_nodes.rename(columns={
                "node_id": "Node ID", "node_name": "Node Name",
                "node_type": "Type", "capacity": "Capacity"
            }).sort_values("Node ID"),
            use_container_width=True, hide_index=True
        )

    with sub_inv:
        st.write(f"**Current Stock Levels — every SKU x Location combination**")
        st.caption("This shows the most recent quantity on hand for each SKU at each location. Use the filters below to narrow it down.")

        col_a, col_b = st.columns(2)
        with col_a:
            filter_sku_inv = st.selectbox("Filter by SKU (optional)", ["All"] + sorted(skus["sku_id"].tolist()), key="filter_sku_inv")
        with col_b:
            filter_node_inv = st.selectbox("Filter by Location (optional)", ["All"] + sorted(nodes["node_id"].tolist()), key="filter_node_inv")

        if not inv.empty:
            # Keep only the LATEST snapshot per SKU-Node pair (in case multiple dates exist)
            latest_inv = (
                inv.sort_values("snapshot_date")
                   .groupby(["sku_id", "node_id"], as_index=False)
                   .last()
            )

            # Merge in readable names
            latest_inv = latest_inv.merge(skus[["sku_id", "product_name"]], on="sku_id", how="left")
            latest_inv = latest_inv.merge(nodes[["node_id", "node_name"]], on="node_id", how="left")

            display_stock = latest_inv[["sku_id","product_name","node_id","node_name","quantity_on_hand","snapshot_date"]].rename(columns={
                "sku_id": "SKU", "product_name": "Product Name", "node_id": "Location ID",
                "node_name": "Location Name", "quantity_on_hand": "Quantity", "snapshot_date": "As Of Date"
            })

            if filter_sku_inv != "All":
                display_stock = display_stock[display_stock["SKU"] == filter_sku_inv]
            if filter_node_inv != "All":
                display_stock = display_stock[display_stock["Location ID"] == filter_node_inv]

            st.dataframe(
                display_stock.sort_values(["SKU", "Location ID"]).style.background_gradient(subset=["Quantity"], cmap="Blues"),
                use_container_width=True, hide_index=True, height=420
            )

            st.write("")
            st.markdown("**Pivot view — SKU rows x Location columns (quantity on hand)**")
            pivot = latest_inv.pivot_table(
                index="sku_id", columns="node_id", values="quantity_on_hand", fill_value=0, aggfunc="sum"
            )
            st.dataframe(pivot.style.background_gradient(cmap="Blues", axis=None), use_container_width=True)

            st.write("")
            with st.expander("View full raw snapshot history (every entry ever added, including old dates)"):
                st.dataframe(
                    inv[["sku_id","node_id","snapshot_date","quantity_on_hand"]]
                        .rename(columns={"sku_id": "SKU", "node_id": "Location", "snapshot_date": "Date", "quantity_on_hand": "Quantity"})
                        .sort_values("Date", ascending=False),
                    use_container_width=True, hide_index=True
                )
        else:
            st.info("No inventory data yet. Add a snapshot from the sidebar.")

# ---------------- TAB 3: ORDER TRACKING ----------------
with tab_tracking:
    st.markdown('<div class="section-title">🚚 Track Every Transfer Order</div>', unsafe_allow_html=True)
    st.caption("Every order you create shows up here immediately — filter by status to see what's In-Transit, Delayed, or Delivered.")

    if orders.empty:
        st.info("No transfer orders yet. Create one from the sidebar.")
    else:
        # Quick status counts as clickable-style summary
        status_order = ["Requested", "Approved", "In-Transit", "Delayed", "Delivered"]
        cols = st.columns(len(status_order))
        for i, stat in enumerate(status_order):
            count = (orders.status == stat).sum()
            with cols[i]:
                st.markdown(
                    f'<div class="kpi-card" style="text-align:center;">'
                    f'<div class="kpi-label">{stat}</div>'
                    f'<div class="kpi-value" style="font-size:24px;color:{STATUS_COLORS.get(stat)}">{count}</div>'
                    f'</div>', unsafe_allow_html=True
                )

        st.write("")

        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            status_filter = st.multiselect("Filter by Status", status_order, default=status_order)
        with colf2:
            sku_filter = st.selectbox("Filter by SKU", ["All"] + sorted(orders["sku_id"].unique().tolist()))
        with colf3:
            search_order_id = st.text_input("Search by Transfer ID")

        filtered_orders = orders[orders.status.isin(status_filter)].copy()
        if sku_filter != "All":
            filtered_orders = filtered_orders[filtered_orders.sku_id == sku_filter]
        if search_order_id:
            try:
                filtered_orders = filtered_orders[filtered_orders.transfer_id == int(search_order_id)]
            except ValueError:
                st.warning("Transfer ID should be a number.")

        # newest first so freshly added/updated orders are easy to find
        filtered_orders = filtered_orders.sort_values("transfer_id", ascending=False)

        display_orders = filtered_orders[[
            "transfer_id","sku_id","source_node_id","dest_node_id","quantity",
            "status","requested_date","planned_delivery_date","actual_delivery_date"
        ]].rename(columns={
            "transfer_id": "ID", "sku_id": "SKU", "source_node_id": "From", "dest_node_id": "To",
            "quantity": "Qty", "status": "Status", "requested_date": "Requested",
            "planned_delivery_date": "Planned Delivery", "actual_delivery_date": "Actual Delivery"
        })

        def highlight_status(row):
            color = STATUS_COLORS.get(row["Status"], "#ffffff")
            return [f"background-color: {color}22" if col == "Status" else "" for col in row.index]

        st.dataframe(
            display_orders.style.apply(highlight_status, axis=1),
            use_container_width=True, hide_index=True, height=420
        )

        st.caption(f"Showing {len(filtered_orders)} of {len(orders)} total transfer orders.")
