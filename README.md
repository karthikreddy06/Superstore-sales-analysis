# Superstore Sales and Profit Analysis

An end-to-end Business Analyst portfolio project analyzing 9,994 order line items (5,009 orders, 793 customers) from the Sample Superstore dataset (`2014-01-03` to `2017-12-30`) using **PostgreSQL**, **SQL**, and **Python**.

---

## Business Problem

The Superstore generated **$2,297,200.86** in sales across 2014–2017, but net profit is only **$286,397.02** (**12.47%** margin). Leadership needs to know:
1. Where profit is leaking across products, states, and discount tiers.
2. Whether heavy discounting drives the losses in unprofitable states and sub-categories.
3. Which customer segments and regions deliver the highest profit per customer.

---

## Dataset

- **Source:** `data/Sample - Superstore.csv` — the public "Sample - Superstore" dataset (a commonly shared public sample dataset of fictional retail data, e.g. available on Kaggle)
- **Size:** 9,994 order line items | 5,009 distinct orders | 793 customers | 49 US states
- **Period:** January 2014 – December 2017 (`2014-01-03` to `2017-12-30`)
- **Documentation:** See [docs/data_dictionary.md](docs/data_dictionary.md) for all 21 columns and cleaning rules.

---

## Approach

1. **Data Ingestion & Cleaning (`Python` + `pandas` + `PostgreSQL`):** Parsed `M/D/YYYY` dates, normalized column names, enforced numeric types, and loaded all 9,994 rows into PostgreSQL (`sql/01_schema.sql`, `python/load_data.py`).
2. **SQL Analysis (`PostgreSQL`):** Wrote 10 business-question queries (`sql/02_analysis.sql`) using CTEs, `CASE` banding, `PERCENTILE_CONT`, and window functions (`LAG` for MoM sales growth, `SUM() OVER` for running profit, `RANK`/`DENSE_RANK` for within-category ranking).
3. **Automated Verification (`Python` + `pandas`):** Built `python/verify.py` to recompute 31 key metrics directly from the raw CSV and fail if any PostgreSQL result differs.
4. **BI-Ready Exports:** Exported all 10 query outputs to `dashboard/data/` as clearly named CSVs, documented in [docs/powerbi_guide.md](docs/powerbi_guide.md).

---

## Project Structure

```text
├── data/
│   └── Sample - Superstore.csv             # Raw dataset (9,994 rows)
├── sql/
│   ├── 01_schema.sql                       # PostgreSQL table schema and indexes
│   └── 02_analysis.sql                     # 10 documented analysis queries
├── python/
│   ├── db_config.py                        # Loads .env credentials for PostgreSQL
│   ├── load_data.py                        # Cleans CSV and loads PostgreSQL
│   ├── run_queries.py                      # Runs SQL queries and exports CSVs
│   └── verify.py                           # Cross-checks PostgreSQL vs pandas
├── dashboard/
│   └── data/                               # 10 exported CSVs for Power BI
├── docs/
│   ├── data_dictionary.md                  # Column definitions and cleaning steps
│   └── powerbi_guide.md                    # Click-by-click Power BI build guide
├── .env.example                            # Template for database credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. Prerequisites
- Python 3.10+ and PostgreSQL 14+
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Configure Database
```bash
createdb -U postgres superstore
cp .env.example .env
# Edit .env with your PostgreSQL host, port, user, and password
```

### 3. Load, Query, and Verify
```bash
python python/load_data.py
python python/run_queries.py
python python/verify.py
```

---

## Key Findings

### 1. Discounts Above 20% Erase $135,376 in Profit
- **Numbers:** Orders with discount `<= 20%` generate **+$421,773.08** in profit, while orders discounted `> 20%` lose **-$135,376.06**. At `0%` discount, margin is **29.51%** ($320,987.60 profit on $1,087,908.47 sales). At `21-30%` discount, margin flips to **-10.05%** (-$10,369.28); at `50%+` discount (856 lines), margin collapses to **-119.20%** (-$76,559.05).
- **Source:** `sql/02_analysis.sql` (Query 3) -> `dashboard/data/discount_band_profit.csv`
- **Recommendation:** Cap standard sales-rep discounts at 20% and require finance/manager approval for any discount above 20%.

### 2. Four States Account for 72.1% of State-Level Losses and Discount Far More Than the Rest
- **Numbers:** Texas (-$25,729.36), Ohio (-$16,971.38), Pennsylvania (-$15,559.96), and Illinois (-$12,607.89) combine for **-$70,868.58** in losses. This equals **72.1%** of the combined losses across all 10 loss-making states (-$98,246.74), and **45.4%** of all loss-making order lines (-$156,131.29). These 4 states average a **35.60%** discount (**41.65%** of lines `> 20%` discount) vs **8.84%** (**4.53%** `> 20%`) in the other 45 states. Every one of the 4 states is profitable on orders `<= 20%` discount (**+$17,891.01** combined) and loses money only above 20% (**-$88,759.59**).
- **Source:** `sql/02_analysis.sql` (Queries 4 & 9) -> `dashboard/data/state_performance.csv`, `dashboard/data/loss_state_root_cause.csv`
- **Recommendation:** Audit regional discounting policies in TX, OH, PA, and IL and shift regional sales incentives from gross revenue to net profit margin.

### 3. Three Sub-Categories Lose $22,387 — But Supplies Is Not a Discount Problem
- **Numbers:** Only 3 of 17 sub-categories lose money: **Tables** (-$17,725.48, `-8.56%` margin), **Bookcases** (-$3,472.56, `-3.02%`), and **Supplies** (-$1,189.10, `-2.55%`), erasing **$22,387.14** combined. Root-cause testing shows **Tables** (26.13% avg discount; 55.17% of lines `> 20%`) and **Bookcases** (21.11% avg discount; 30.70% of lines `> 20%`) are both profitable at `<= 20%` discount (**+$12,972.74** and **+$7,625.21**). By contrast, **Supplies** averages only a **7.68%** discount with **0.00%** of lines above 20% — all -$1,189.10 of its loss occurs at `<= 20%` discount.
- **Source:** `sql/02_analysis.sql` (Queries 2 & 8) -> `dashboard/data/category_subcategory_profit.csv`, `dashboard/data/loss_subcategory_root_cause.csv`
- **Recommendation:** Restrict discounts above 20% on Tables and Bookcases; for Supplies, review supplier unit costs and SKU pricing rather than discount policy.

### 4. Home Office Leads Profit Per Customer (\$407.42), While Central Region Lags at 7.92% Margin
- **By Segment:** **Home Office** (148 customers) generates **$60,298.68** in profit (**$407.42** per customer, `14.03%` margin); **Corporate** (236 customers) generates **$91,979.13** (**$389.74** per customer, `13.03%` margin); and **Consumer** (409 customers) generates **$134,119.21** (**$327.92** per customer, `11.55%` margin).
- **By Region (order-based):** **West** leads with **$108,418.45** profit on **$725,457.82** sales (`14.94%` margin), followed by **East** (**$91,522.78** on **$678,781.24**, `13.48%`) and **South** (**$46,749.43** on **$391,721.91**, `11.93%`). **Central** generates **$501,239.89** in sales (28% more than South) but only **$39,706.36** in profit (`7.92%` margin).
- *Limitations note: Customers span regions (766 of 793 order across multiple regions), so customer-level figures are reported by Segment, not by Region.*
- **Source:** `sql/02_analysis.sql` (Queries 7 & 8) -> `dashboard/data/segment_profit.csv`, `dashboard/data/region_performance.csv`
- **Recommendation:** Prioritize retention and account management for **Home Office** and **Corporate** customers (highest profit per customer and margin), and focus regional margin-recovery efforts on **Central** (`7.92%` margin) by tightening discount guardrails.

---

## Dashboard

Power BI dashboard built from the CSVs in `dashboard/data/`:

![Dashboard Overview](dashboard/screenshots/overview.png)
![Discount Analysis](dashboard/screenshots/discount_analysis.png)

---

## Recommendations

1. **Enforce a 20% Discount Ceiling:** Eliminating or gating `> 20%` discounts protects the profitable core (+$421,773.08) from the -$135,376.06 drag.
2. **Fix Regional Margin Leakage First in TX, OH, PA, IL:** Align regional rep compensation with margin rather than top-line sales.
3. **Separate Pricing Fixes from Discount Fixes:** Apply discount caps to Tables and Bookcases, and run a supplier/SKU cost review on Supplies.
4. **Prioritize Home Office & Corporate Retention and Central Margin Recovery:** Focus account-management and retention efforts on Home Office (\$407.42/customer) and Corporate (\$389.74/customer), while tightening discount guardrails in the Central region (`7.92%` margin).

---

## Limitations

- **Single-retailer historical data:** Covers one fictionalized US retail dataset from 2014–2017; results may not generalize to other industries or current inflation/shipping environments.
- **Observational, not causal:** High discounts strongly correlate with negative profit, but the dataset does not include randomized price experiments or unit-cost breakdowns to prove discount elasticity.
- **No cost-of-goods or shipping-cost columns:** `Profit` is given as a net figure without separate COGS, freight, or overhead fields, limiting deeper margin attribution (especially for Supplies).
- **No forecasting:** Analysis is descriptive and diagnostic; no time-series forecasting model was built.
