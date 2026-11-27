# Power BI One-Page Dashboard Guide

Follow these steps to build a one-page executive dashboard in Power BI Desktop using the exported CSVs in `dashboard/data/`.

## 1. Load the Data
1. Open **Power BI Desktop** -> **Home** -> **Get Data** -> **Text/CSV**.
2. Import the following files from `dashboard/data/`:
   - `monthly_trend.csv`
   - `category_subcategory_profit.csv`
   - `discount_band_profit.csv`
   - `state_performance.csv`
   - `segment_region_profit.csv`
3. In **Transform Data** (Power Query Editor):
   - In `monthly_trend`, confirm `month` is typed as **Date**.
   - Add a `Year` column from `month`: **Add Column** -> **Date** -> **Year** -> **Year**.
   - In `discount_band_profit`, add a sort-order column (`band_order`: `0%` = 1, `1-10%` = 2, ..., `50%+` = 7) so the chart sorts chronologically by discount level instead of alphabetically.
   - Click **Home** -> **Close & Apply**.

## 2. Configure Relationships & Measures
1. Go to **Model view**:
   - Link `state_performance[region]` to `segment_region_profit[region]` (Many-to-Many or via a small `Region` bridge table) so the Region slicer filters both state and segment visuals.
   - *Tip:* Because each exported CSV is pre-aggregated at its own grain, the **Year** slicer filters `monthly_trend`, while **Region** and **Segment** slicers filter `state_performance` and `segment_region_profit`. If you want all three slicers to cross-filter every visual simultaneously, also import `data/Sample - Superstore.csv` as a detail table.
2. Create a Profit Margin measure in **Report view** (**Modeling** -> **New Measure**):
   ```dax
   Profit Margin % = DIVIDE(SUM(monthly_trend[total_profit]), SUM(monthly_trend[total_sales]), 0)
   ```

## 3. Build the One-Page Layout
Set the canvas to **16:9** (**Format page** -> **Canvas settings**).

### Row 1: KPI Cards (Top Strip)
1. **Total Sales Card:** Add **Card** visual -> drag `monthly_trend[total_sales]` -> format as Currency (`$2.30M`).
2. **Total Profit Card:** Add **Card** visual -> drag `monthly_trend[total_profit]` -> format as Currency (`$286.40K`).
3. **Profit Margin % Card:** Add **Card** visual -> drag `[Profit Margin %]` -> format as Percentage (`12.47%`).

### Row 1 (Right): Slicers
1. **Year Slicer:** Add **Slicer** -> drag `monthly_trend[Year]` -> **Slicer settings** -> **Dropdown** or **Tile**.
2. **Region Slicer:** Add **Slicer** -> drag `segment_region_profit[region]`.
3. **Segment Slicer:** Add **Slicer** -> drag `segment_region_profit[segment]`.

### Row 2: Trends & Sub-Categories
1. **Monthly Sales & Profit Trend (Line Chart):**
   - **X-axis:** `monthly_trend[month]`
   - **Y-axis:** `monthly_trend[total_sales]`
   - **Secondary Y-axis:** `monthly_trend[total_profit]`
   - Title: *Monthly Sales & Profit Trend (2014–2017)*.
2. **Profit by Sub-Category (Clustered Bar Chart):**
   - **Y-axis:** `category_subcategory_profit[sub_category]`
   - **X-axis:** `category_subcategory_profit[total_profit]`
   - **Conditional formatting:** Set bars `< 0` to red (`#D64550`) and `>= 0` to teal/blue (`#118DFF`) to highlight Tables, Bookcases, and Supplies.

### Row 3: Discount Impact & Geographic Losses
1. **Discount Band vs. Profit (Clustered Column Chart):**
   - **X-axis:** `discount_band_profit[discount_band]` (sorted by `band_order`)
   - **Y-axis:** `discount_band_profit[total_profit]`
   - Add a horizontal constant line at `0` (**Analytics** pane -> **Constant line**) to show the profitability cliff above 20% discount.
2. **State Profit Performance (Filled Map or Bar Chart):**
   - **Location / Y-axis:** `state_performance[state]`
   - **Color saturation / X-axis:** `state_performance[total_profit]`
   - **Tooltips:** `total_sales`, `profit_margin_pct`, `region`.
   - Use a diverging color scale (red for negative profit such as TX, OH, PA, IL; blue/green for positive profit such as CA, NY, WA).
