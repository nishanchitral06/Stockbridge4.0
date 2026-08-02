# 📦 StockBridge — Multi-Echelon Inventory Replenishment Planner

> **Minor Project Submission** — Logistics & Supply Chain Internship (Persevex)

StockBridge is an end-to-end **multi-echelon inventory replenishment planning system** built with Python. It models a realistic supply chain network consisting of a central warehouse and multiple retail stores, then forecasts demand, computes safety stock, generates replenishment transfer orders, and visualizes everything through a modern interactive dashboard.

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| **Demand Forecasting** | 14-day moving average with Poisson-distributed demand and weekly seasonality (weekend boost) |
| **Safety Stock Calculation** | Statistical safety stock using z-score (95% service level) and lead-time variability |
| **Reorder Point Engine** | Automatic detection of SKUs below reorder threshold with prioritized replenishment |
| **Transfer Order Workflow** | End-to-end order lifecycle: Requested → Approved → In-Transit → Delivered / Delayed |
| **Warehouse Capacity Validation** | Transfers capped at available warehouse stock to prevent over-allocation |
| **Risk-Based Prioritization** | Combined business value & stockout risk scoring to rank replenishment urgency |
| **Interactive Dashboard** | Futuristic light-theme Streamlit dashboard with KPI cards, charts, and data management |
| **Cloud Database (Turso)** | Persistent data storage via Turso (LibSQL) — survives app restarts and redeploys |
| **Local SQLite Fallback** | Automatic fallback to local `stockbridge.db` when no cloud credentials are set |

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     StockBridge System                         │
├───────────────┬───────────────┬───────────────┬───────────────┤
│  Phase 1      │  Phase 2      │  Phase 3      │  Phase 4      │
│  Schema &     │  Replenishment│  Transfer     │  Interactive  │
│  Sample Data  │  Engine       │  Workflow     │  Dashboard    │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ 01_create_    │ 03_replenish- │ 04_transfer_  │ 05_dashboard  │
│ schema.py     │ ment_engine.py│ workflow.py   │ .py           │
│ 02_generate_  │               │               │               │
│ sample_data.py│               │               │               │
├───────────────┴───────────────┴───────────────┴───────────────┤
│                        db.py                                   │
│          (Connection helper: Turso cloud ↔ Local SQLite)       │
├───────────────────────────────────────────────────────────────┤
│              stockbridge.db  /  Turso Cloud DB                 │
└───────────────────────────────────────────────────────────────┘
```

### Supply Chain Network

```
                ┌─────────────────────┐
                │   WH1 — Central     │
                │   Warehouse         │
                │   (Capacity: 100K)  │
                └──┬───┬───┬───┬─────┘
                   │   │   │   │
         ┌─────────┘   │   │   └─────────┐
         ▼             ▼   ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ ST1      │  │ ST2      │  │ ST3      │  │ ST4      │
   │ Bangalore│  │ Mumbai   │  │ Delhi    │  │ Chennai  │
   │ Store    │  │ Store    │  │ Store    │  │ Store    │
   │ (Cap:2K) │  │ (Cap:2K) │  │ (Cap:2K) │  │ (Cap:1.5K)│
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.x** | Core programming language |
| **Streamlit** | Interactive web dashboard framework |
| **Pandas** | Data manipulation and analysis |
| **NumPy** | Statistical computations (Poisson distribution, safety stock) |
| **Plotly** | Interactive charts and visualizations |
| **Matplotlib** | Additional plotting support |
| **SQLite** | Local relational database (fallback) |
| **Turso (LibSQL)** | Cloud-hosted persistent database |

---

## 📁 Project Structure

```
StockBridge_Minor_Project_Submission4.0/
│
├── README.md                          ← You are here
├── StockBridge_Presentation.pptx      ← Project presentation (PPT)
├── StockBridge_Project_Report.pdf     ← Full project report (PDF)
├── LIVE_LINK.txt                      ← Deployment instructions
├── TURSO_SETUP.txt                    ← Cloud database setup guide
├── STOCKBRIDGE TOKEN4.0.txt           ← Turso credentials (keep private)
│
└── Source_Code/
    ├── 01_create_schema.py            ← Database schema (6 tables)
    ├── 02_generate_sample_data.py     ← Synthetic data generator (18 SKUs, 5 nodes, 90 days)
    ├── 03_replenishment_engine.py     ← Demand forecasting & reorder engine
    ├── 04_transfer_workflow.py        ← Transfer order lifecycle simulator
    ├── 05_dashboard.py                ← Streamlit interactive dashboard (main app)
    ├── 06_migrate_to_turso.py         ← One-time migration to Turso cloud DB
    ├── db.py                          ← Database connection helper (Turso ↔ SQLite)
    ├── requirements.txt               ← Python dependencies
    └── stockbridge.db                 ← Pre-built SQLite database with sample data
```

---

## 🗄️ Database Schema

The system uses **6 core tables** plus 1 derived table:

| Table | Description | Key Columns |
|---|---|---|
| `SKU` | Product catalog | `sku_id` (PK), `product_name`, `category`, `unit_cost` |
| `Node` | Warehouses & stores | `node_id` (PK), `node_name`, `node_type`, `capacity` |
| `InventorySnapshot` | Stock levels at a point in time | `sku_id`, `node_id`, `snapshot_date`, `quantity_on_hand` |
| `LeadTimeProfile` | Shipping times between nodes | `source_node_id`, `dest_node_id`, `lead_time_days` |
| `DemandHistory` | Historical sales data | `sku_id`, `node_id`, `demand_date`, `units_sold` |
| `TransferOrder` | Replenishment orders | `sku_id`, `source_node_id`, `dest_node_id`, `quantity`, `status` |
| `ReplenishmentRecommendation` | Engine output (derived) | `sku_id`, `store`, `reorder_point`, `safety_stock`, `risk_rank_score` |

### Sample Data Summary

- **18 SKUs** across 3 categories (Apparel, Footwear, Accessories)
- **5 Nodes** — 1 Central Warehouse + 4 Retail Stores (Bangalore, Mumbai, Delhi, Chennai)
- **90 days** of demand history with weekly seasonality
- **Lead times** of 2–6 days from warehouse to each store

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation & Local Run

```bash
# 1. Clone or navigate to the project directory
cd Source_Code

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Regenerate the database from scratch
python 01_create_schema.py
python 02_generate_sample_data.py
python 03_replenishment_engine.py
python 04_transfer_workflow.py

# 4. Launch the dashboard
streamlit run 05_dashboard.py
```

> **Note:** Step 3 is optional — the repository includes a pre-built `stockbridge.db` with all sample data already loaded.

The dashboard will open in your browser at `http://localhost:8501`.

---

## ⚙️ How the Engine Works

### 1. Demand Forecasting
```
Avg Daily Demand = Mean of last 14 days of sales (moving average)
```

### 2. Safety Stock Calculation
```
Safety Stock = Z × σ_demand × √(Lead Time)
where Z = 1.65 (95% service level)
```

### 3. Reorder Point
```
Reorder Point = (Avg Daily Demand × Lead Time) + Safety Stock
```

### 4. Replenishment Decision
```
IF current_stock < reorder_point:
    suggested_qty = (Avg Daily Demand × 21 days) − current_stock
```

### 5. Risk Prioritization
```
Risk Rank Score = Business Value Score / (Days of Stock Left + 1)
where Business Value Score = Unit Cost × Avg Daily Demand
```

Higher risk rank score → Higher priority for replenishment.

---

## ☁️ Cloud Deployment

### Deploy to Streamlit Community Cloud (Free)

1. Upload the `Source_Code/` files to a **GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New App** → select your repo → set main file to `05_dashboard.py`
4. Click **Deploy** — your live URL will look like: `https://your-app-name.streamlit.app`

### Set Up Persistent Storage with Turso (Optional)

To make data persist across app restarts:

1. Create a free [Turso](https://turso.tech) account and database
2. Run the migration script locally:
   ```bash
   set TURSO_DATABASE_URL=libsql://your-db.turso.io
   set TURSO_AUTH_TOKEN=your-token-here
   python 06_migrate_to_turso.py
   ```
3. Add `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` to Streamlit Cloud's **Secrets** settings

See [`TURSO_SETUP.txt`](TURSO_SETUP.txt) for detailed step-by-step instructions.

---

## 📊 Dashboard Highlights

The Streamlit dashboard (`05_dashboard.py`) provides:

- **🏠 KPI Overview** — Total SKUs, nodes, transfer orders, and replenishment alerts at a glance
- **📈 Demand Trend Charts** — Interactive Plotly time-series visualizations with filtering
- **🔔 Replenishment Alerts** — SKUs below reorder point, ranked by stockout risk
- **🚚 Transfer Order Tracker** — Full lifecycle view with status badges (Requested / Approved / In-Transit / Delivered / Delayed)
- **📝 Data Management** — Add/edit SKUs, nodes, inventory, and demand records directly from the sidebar
- **📋 Browse All Data** — Explore raw data across all tables with search and filtering
- **🎨 Futuristic Light Theme** — Custom CSS with glassmorphism, gradient accents, and micro-animations

---

## 📄 Submission Contents

| Item | File | Status |
|---|---|---|
| Project Presentation | `StockBridge_Presentation.pptx` | ✅ Complete |
| Project Report | `StockBridge_Project_Report.pdf` | ✅ Complete |
| Source Code | `Source_Code/` | ✅ Complete |
| Live Link | See `LIVE_LINK.txt` | 🔗 Deploy & add link |

---

## 👤 Author

**Nishan Chitral**
Logistics & Supply Chain Intern — Persevex

---

## 📜 License

This project was developed as part of a minor project submission for the Logistics & Supply Chain Internship at Persevex. All rights reserved.
