"""
StockBridge - Phase 2: Replenishment Recommendation Engine
- Forecasts short-term demand using a moving average
- Computes safety stock + reorder point per SKU-Node
- Generates transfer recommendations from Warehouse -> Stores
- Prioritizes by stockout risk
"""
import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect("stockbridge.db")

demand = pd.read_sql("SELECT * FROM DemandHistory", conn)
inv = pd.read_sql("SELECT * FROM InventorySnapshot", conn)
lead = pd.read_sql("SELECT * FROM LeadTimeProfile", conn)
skus = pd.read_sql("SELECT * FROM SKU", conn)

Z_SCORE = 1.65          # ~95% service level
MOVING_AVG_WINDOW = 14  # days
TARGET_DAYS_COVER = 21  # target stock = enough for 21 days

results = []

stores = ["ST1", "ST2", "ST3", "ST4"]

for sku_id in skus["sku_id"]:
    for store in stores:
        d = demand[(demand.sku_id == sku_id) & (demand.node_id == store)].sort_values("demand_date")
        if d.empty:
            continue

        recent = d.tail(MOVING_AVG_WINDOW)["units_sold"]
        avg_daily_demand = recent.mean()
        std_daily_demand = recent.std(ddof=0)

        lt_row = lead[(lead.source_node_id == "WH1") & (lead.dest_node_id == store)]
        lead_time_days = int(lt_row["lead_time_days"].iloc[0]) if not lt_row.empty else 4

        safety_stock = Z_SCORE * std_daily_demand * np.sqrt(lead_time_days)
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        target_stock = avg_daily_demand * TARGET_DAYS_COVER

        current_stock_row = inv[(inv.sku_id == sku_id) & (inv.node_id == store)]
        current_stock = int(current_stock_row["quantity_on_hand"].iloc[0]) if not current_stock_row.empty else 0

        days_of_stock_left = current_stock / avg_daily_demand if avg_daily_demand > 0 else np.inf
        needs_replenishment = current_stock < reorder_point
        suggested_qty = max(0, round(target_stock - current_stock)) if needs_replenishment else 0

        # simple business value = unit_cost * avg_daily_demand
        unit_cost = skus.loc[skus.sku_id == sku_id, "unit_cost"].values[0]
        business_value = unit_cost * avg_daily_demand

        results.append({
            "sku_id": sku_id,
            "store": store,
            "avg_daily_demand": round(avg_daily_demand, 2),
            "lead_time_days": lead_time_days,
            "safety_stock": round(safety_stock, 1),
            "reorder_point": round(reorder_point, 1),
            "current_stock": current_stock,
            "days_of_stock_left": round(days_of_stock_left, 1),
            "needs_replenishment": needs_replenishment,
            "suggested_transfer_qty": suggested_qty,
            "business_value_score": round(business_value, 1),
        })

df = pd.DataFrame(results)

# Stockout risk rank: lower days_of_stock_left = higher risk. Combine with business value.
df["risk_rank_score"] = df["business_value_score"] / (df["days_of_stock_left"] + 1)
df = df.sort_values("risk_rank_score", ascending=False)

df.to_sql("ReplenishmentRecommendation", conn, if_exists="replace", index=False)
conn.commit()

print(f"Generated {len(df)} SKU-Store recommendations.")
print(f"{df['needs_replenishment'].sum()} need replenishment right now.\n")
print("Top 10 priority items (highest risk):")
print(df[df.needs_replenishment][
    ["sku_id","store","current_stock","reorder_point","days_of_stock_left","suggested_transfer_qty"]
].head(10).to_string(index=False))

conn.close()
