-- Superstore Sales and Profit Analysis Queries
-- Each query answers a specific business question and exports to dashboard/data/.

-- ============================================================
-- 1. MONTHLY SALES, PROFIT TREND & RUNNING TOTAL
-- Output: monthly_trend.csv
-- Business Question: How have sales, profit, MoM sales growth, and cumulative profit trended over time?
-- Why this query: Tracks seasonality, month-over-month sales momentum (LAG), and cumulative profit growth across all 48 months.
-- ============================================================
WITH monthly_summary AS (
    SELECT
        DATE_TRUNC('month', order_date)::date AS month,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit,
        COUNT(DISTINCT order_id) AS order_count
    FROM superstore
    GROUP BY DATE_TRUNC('month', order_date)::date
)
SELECT
    month,
    total_sales,
    total_profit,
    order_count,
    LAG(total_sales) OVER (ORDER BY month) AS prev_month_sales,
    ROUND(
        ((total_sales - LAG(total_sales) OVER (ORDER BY month))
        / NULLIF(LAG(total_sales) OVER (ORDER BY month), 0) * 100)::numeric,
        2
    ) AS mom_sales_growth_pct,
    SUM(total_profit) OVER (ORDER BY month) AS running_total_profit
FROM monthly_summary
ORDER BY month;

-- ============================================================
-- 2. PROFIT BY CATEGORY AND SUB-CATEGORY (WITH WITHIN-CATEGORY RANK)
-- Output: category_subcategory_profit.csv
-- Business Question: Which categories and sub-categories are most/least profitable, and how does each rank within its category?
-- Why this query: Pinpoints exact loss-making sub-categories and ranks all 17 sub-categories within their parent category using RANK and DENSE_RANK.
-- ============================================================
SELECT
    category,
    sub_category,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS profit_margin_pct,
    COUNT(*) AS order_lines,
    RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS profit_rank_in_category,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS profit_dense_rank_in_category
FROM superstore
GROUP BY category, sub_category
ORDER BY total_profit ASC;

-- ============================================================
-- 3. EFFECT OF DISCOUNT BANDS ON PROFIT
-- Output: discount_band_profit.csv
-- Business Question: How do different discount levels affect profitability and margin?
-- Why this query: Identifies the exact discount threshold where average order-line profit turns negative.
-- ============================================================
WITH discount_bands AS (
    SELECT
        CASE
            WHEN discount = 0 THEN '0% (No Discount)'
            WHEN discount > 0 AND discount <= 0.1 THEN '1-10%'
            WHEN discount > 0.1 AND discount <= 0.2 THEN '11-20%'
            WHEN discount > 0.2 AND discount <= 0.3 THEN '21-30%'
            WHEN discount > 0.3 AND discount <= 0.4 THEN '31-40%'
            WHEN discount > 0.4 AND discount <= 0.5 THEN '41-50%'
            ELSE '50%+'
        END AS discount_band,
        sales,
        profit
    FROM superstore
)
SELECT
    discount_band,
    COUNT(*) AS order_lines,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    AVG(profit) AS avg_profit_per_line,
    SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS profit_margin_pct
FROM discount_bands
GROUP BY discount_band
ORDER BY
    CASE discount_band
        WHEN '0% (No Discount)' THEN 1
        WHEN '1-10%' THEN 2
        WHEN '11-20%' THEN 3
        WHEN '21-30%' THEN 4
        WHEN '31-40%' THEN 5
        WHEN '41-50%' THEN 6
        ELSE 7
    END;

-- ============================================================
-- 4. REGION AND STATE PERFORMANCE
-- Output: state_performance.csv
-- Business Question: How do regions and states compare in sales, profit, and margin?
-- Why this query: Surfaces geographic profit concentration and highlights loss-making states despite high sales volume.
-- ============================================================
SELECT
    region,
    state,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count
FROM superstore
GROUP BY region, state
ORDER BY total_profit DESC;

-- ============================================================
-- 5. TOP 10 CUSTOMERS BY PROFIT
-- Output: top_customers.csv
-- Business Question: Who are our most valuable customers by lifetime profit contribution?
-- Why this query: Profiles high-margin customers to inform retention and account-based targeting.
-- ============================================================
SELECT
    customer_id,
    customer_name,
    segment,
    region,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS order_count
FROM superstore
GROUP BY customer_id, customer_name, segment, region
ORDER BY total_profit DESC
LIMIT 10;

-- ============================================================
-- 6. SHIPPING MODE VS DELIVERY TIME
-- Output: shipping_mode_delivery.csv
-- Business Question: How does shipping mode affect delivery time (days to ship)?
-- Why this query: Benchmarks operational fulfillment speed across all four shipping tiers using mean and median lead times.
-- ============================================================
SELECT
    ship_mode,
    COUNT(*) AS order_lines,
    AVG((ship_date - order_date)) AS avg_days_to_ship,
    MIN((ship_date - order_date)) AS min_days_to_ship,
    MAX((ship_date - order_date)) AS max_days_to_ship,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (ship_date - order_date)) AS median_days_to_ship
FROM superstore
GROUP BY ship_mode
ORDER BY avg_days_to_ship;

-- ============================================================
-- 7. PROFIT PER CUSTOMER BY SEGMENT AND REGION
-- Output: segment_region_profit.csv
-- Business Question: How does profit per customer and profit margin vary across customer segments and regions?
-- Why this query: Replaces the uninformative repeat-vs-one-time split (781 vs 12) with an actionable view of customer value by Segment and Region.
-- ============================================================
SELECT
    segment,
    region,
    COUNT(DISTINCT customer_id) AS customer_count,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    SUM(profit) / NULLIF(COUNT(DISTINCT customer_id), 0) AS profit_per_customer,
    SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS profit_margin_pct
FROM superstore
GROUP BY segment, region
ORDER BY profit_per_customer DESC;

-- ============================================================
-- 8. ROOT-CAUSE ANALYSIS: LOSS-MAKING SUB-CATEGORIES VS DISCOUNTING
-- Output: loss_subcategory_root_cause.csv
-- Business Question: Do loss-making sub-categories (Tables, Bookcases, Supplies) have higher discounts, and are they profitable at <= 20% discount?
-- Why this query: Tests whether heavy discounting (>20%) drives losses in Tables, Bookcases, and Supplies or whether other cost factors are at play.
-- ============================================================
WITH subcat_groups AS (
    SELECT
        CASE
            WHEN sub_category IN ('Tables', 'Bookcases', 'Supplies') THEN sub_category
            ELSE 'Other 14 Sub-Categories'
        END AS sub_category_group,
        sales,
        profit,
        discount
    FROM superstore
)
SELECT
    sub_category_group,
    COUNT(*) AS order_lines,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    AVG(discount) * 100 AS avg_discount_pct,
    SUM(CASE WHEN discount > 0.20 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100 AS pct_lines_over_20_discount,
    SUM(CASE WHEN discount > 0.20 THEN profit ELSE 0 END) AS profit_over_20_discount,
    SUM(CASE WHEN discount <= 0.20 THEN profit ELSE 0 END) AS profit_up_to_20_discount
FROM subcat_groups
GROUP BY sub_category_group
ORDER BY total_profit ASC;

-- ============================================================
-- 9. ROOT-CAUSE ANALYSIS: TOP 4 LOSS STATES VS DISCOUNTING
-- Output: loss_state_root_cause.csv
-- Business Question: Do the top 4 loss-making states (TX, OH, PA, IL) suffer from heavier discounting than the remaining 45 states?
-- Why this query: Quantifies average discount, share of >20% discounted lines, and profit above vs up to 20% discount for TX, OH, PA, and IL.
-- ============================================================
WITH state_groups AS (
    SELECT
        CASE
            WHEN state IN ('Texas', 'Ohio', 'Pennsylvania', 'Illinois') THEN state
            ELSE 'Other 45 States'
        END AS state_group,
        sales,
        profit,
        discount
    FROM superstore
)
SELECT
    state_group,
    COUNT(*) AS order_lines,
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit,
    AVG(discount) * 100 AS avg_discount_pct,
    SUM(CASE WHEN discount > 0.20 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100 AS pct_lines_over_20_discount,
    SUM(CASE WHEN discount > 0.20 THEN profit ELSE 0 END) AS profit_over_20_discount,
    SUM(CASE WHEN discount <= 0.20 THEN profit ELSE 0 END) AS profit_up_to_20_discount
FROM state_groups
GROUP BY state_group
ORDER BY total_profit ASC;
