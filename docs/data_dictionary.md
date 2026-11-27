# Data Dictionary

## Source Dataset
- **File:** `data/Sample - Superstore.csv`
- **Rows:** 9,994 order line items (5,009 distinct orders; 793 distinct customers)
- **Date Range:** `2014-01-03` to `2017-12-30`
- **Encoding:** `latin1` (preserves special characters in product names)

## Cleaning & Transformation (`python/load_data.py`)
1. **Encoding:** Read raw CSV with `encoding="latin1"`.
2. **Date Parsing:** Converted `Order Date` and `Ship Date` from `M/D/YYYY` strings to `DATE` using `pd.to_datetime(..., format="%m/%d/%Y")`.
3. **Column Normalization:** Renamed all 21 columns to `snake_case` to match `sql/01_schema.sql`.
4. **Type Enforcement:** Cast `row_id` and `quantity` to integer (`Int64`), and `sales`, `discount`, and `profit` to numeric (`NUMERIC(12,4)` / `NUMERIC(4,2)`).
5. **Null Handling:** Replaced missing `postal_code` values with an empty string (`""`). Checked critical keys (`order_id`, `order_date`, `ship_date`, `customer_id`) for nulls — 0 rows were dropped (9,994 of 9,994 rows retained).

## Table Schema: `superstore`

| Column | SQL Type | Raw CSV Name | Description |
| :--- | :--- | :--- | :--- |
| `row_id` | `INTEGER PRIMARY KEY` | `Row ID` | Unique identifier for each order line item (1–9,994). |
| `order_id` | `VARCHAR(20) NOT NULL` | `Order ID` | Order identifier (multiple line items can share one `order_id`). |
| `order_date` | `DATE NOT NULL` | `Order Date` | Date the order was placed (`2014-01-03` to `2017-12-30`). |
| `ship_date` | `DATE NOT NULL` | `Ship Date` | Date the order was shipped. |
| `ship_mode` | `VARCHAR(20) NOT NULL` | `Ship Mode` | Shipping tier (`Same Day`, `First Class`, `Second Class`, `Standard Class`). |
| `customer_id` | `VARCHAR(20) NOT NULL` | `Customer ID` | Unique customer identifier (793 distinct customers). |
| `customer_name` | `VARCHAR(100) NOT NULL` | `Customer Name` | Full name of the customer. |
| `segment` | `VARCHAR(20) NOT NULL` | `Segment` | Customer segment (`Consumer`, `Corporate`, `Home Office`). |
| `country` | `VARCHAR(50) NOT NULL` | `Country` | Country of delivery (`United States` for all rows). |
| `city` | `VARCHAR(50) NOT NULL` | `City` | Delivery city. |
| `state` | `VARCHAR(50) NOT NULL` | `State` | Delivery state (49 US states including District of Columbia). |
| `postal_code` | `VARCHAR(20)` | `Postal Code` | Delivery ZIP/postal code (stored as string to preserve leading zeros). |
| `region` | `VARCHAR(20) NOT NULL` | `Region` | US sales region (`West`, `East`, `Central`, `South`). |
| `product_id` | `VARCHAR(20) NOT NULL` | `Product ID` | Unique product SKU identifier. |
| `category` | `VARCHAR(20) NOT NULL` | `Category` | Top-level product category (`Furniture`, `Office Supplies`, `Technology`). |
| `sub_category` | `VARCHAR(30) NOT NULL` | `Sub-Category` | Product sub-category (17 distinct sub-categories). |
| `product_name` | `VARCHAR(200) NOT NULL` | `Product Name` | Descriptive name of the product. |
| `sales` | `NUMERIC(12,4) NOT NULL` | `Sales` | Line-item revenue in USD. |
| `quantity` | `INTEGER NOT NULL` | `Quantity` | Number of units sold on the line item. |
| `discount` | `NUMERIC(4,2) NOT NULL` | `Discount` | Fractional discount applied (e.g., `0.20` = 20% discount). |
| `profit` | `NUMERIC(12,4) NOT NULL` | `Profit` | Line-item net profit (or loss, if negative) in USD. |
