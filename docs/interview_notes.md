# Interview Notes: Superstore Sales & Profit Analysis

Plain, first-person answers grounded in the actual SQL queries and verified numbers from this repository.

---

### 1. Can you walk me through this project in 60 seconds?
I analyzed 9,994 order line items (5,009 orders, 793 customers) from the Sample Superstore dataset covering 2014 to 2017 using Python, PostgreSQL, and SQL. While total sales were \$2.30M (\$2,297,200.86), net profit was only \$286,397.02, or a 12.47% margin. My analysis showed that orders discounted up to 20% generated +\$421,773.08 in profit, whereas orders discounted above 20% lost -\$135,376.06. Four states—Texas, Ohio, Pennsylvania, and Illinois—accounted for 72.1% of all state-level losses (-\$70,868.58 out of -\$98,246.74), and three sub-categories—Tables, Bookcases, and Supplies—lost \$22,387.14 combined. I also built an automated pandas-to-PostgreSQL verification script (`verify.py`) so every number in the README is reproducible.

### 2. Why did you choose 20% as the discount cutoff?
I didn't pick 20% arbitrarily—it came directly from the discount band query (`discount_band_profit.csv`). Orders with 0% discount had a 29.51% profit margin (+\$320,987.60), 1–10% had 16.61% (+\$9,029.18), and 11–20% still stayed positive at 11.58% (+\$91,756.30). As soon as discounts crossed 20%, margin flipped negative: the 21–30% band dropped to -10.05% (-\$10,369.28), 31–40% to -19.44% (-\$25,448.19), 41–50% to -35.71% (-\$22,999.54), and 50%+ collapsed to -119.20% (-\$76,559.05). So 20% is the exact empirical breakeven threshold in this dataset.

### 3. What do `LAG` and `RANK` / `DENSE_RANK` do in your SQL queries?
In Query 1 (`monthly_trend.csv`), I used `LAG(total_sales) OVER (ORDER BY month)` inside a CTE to pull the previous month's sales onto the current row so I could calculate month-over-month sales growth percentage without a self-join. I also used `SUM(total_profit) OVER (ORDER BY month)` for a running total of profit. In Query 2 (`category_subcategory_profit.csv`), I used `RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC)` and `DENSE_RANK()` to rank every sub-category by profit within its own category (`Furniture`, `Office Supplies`, `Technology`), which immediately highlights that `Tables` and `Bookcases` sit at the bottom of `Furniture` while `Supplies` sits at the bottom of `Office Supplies`.

### 4. How did you calculate profit per customer, and why didn't you split it by Region?
In Query 7 (`segment_profit.csv`), I calculated `SUM(profit) / COUNT(DISTINCT customer_id)` grouped by `segment` only. Every one of the 793 customers belongs to exactly one segment (`Home Office`: 148 customers, \$407.42/customer, 14.03% margin; `Corporate`: 236 customers, \$389.74/customer, 13.03% margin; `Consumer`: 409 customers, \$327.92/customer, 11.55% margin). I intentionally did not compute profit per customer by Region because 766 of 793 customers (96.60%) ordered across multiple regions—so regional customer counts overlap. Instead, I evaluated regions on an order basis in Query 8 (`region_performance.csv`), which shows `West` leading at 14.94% margin (\$108,418.45 profit) and `Central` lagging at 7.92% margin (\$39,706.36 profit on \$501,239.89 sales).

### 5. Why do Texas, Ohio, Pennsylvania, and Illinois lose so much money?
Those four states combine for -\$70,868.58 in losses, which is 72.1% of the -\$98,246.74 combined losses across all 10 loss-making states. In Query 9 (`loss_state_root_cause.csv`), I compared them against the other 45 states: the four states average a 35.60% discount with 41.65% of order lines above 20% discount, compared to an 8.84% average discount and only 4.53% above 20% in the rest of the country. More importantly, all four states are actually profitable on orders discounted 20% or less (+\$17,891.01 combined) and only lose money on orders above 20% discount (-\$88,759.59).

### 6. Why did you report 72.1% for the four loss-making states instead of 60% or 45.4%?
The original README said 60%, which I could not reproduce. When I recomputed it in PostgreSQL, -\$70,868.58 is 72.13% of the combined losses of the 10 net loss-making states (-\$98,246.74), and 45.39% of all individual loss-making order lines across the entire dataset (-\$156,131.29). I used 72.1% as the headline figure because Finding 3 is a state-level comparison, and I also stated the 45.4% line-item share so the definition is completely transparent.

### 7. Are all three loss-making sub-categories losing money because of discounts?
No, and checking that was one of the best parts of the root-cause analysis (Query 8, `loss_subcategory_root_cause.csv`). `Tables` (-\$17,725.48) and `Bookcases` (-\$3,472.56) both have high discounting—26.13% and 21.11% average discount, with 55.17% and 30.70% of lines above 20%—and both are profitable on orders at or below 20% discount (+\$12,972.74 and +\$7,625.21). However, `Supplies` (-\$1,189.10) has only a 7.68% average discount and 0.00% of its order lines above 20% discount. So `Supplies` loses money even without heavy discounting, which points to unit cost or pricing issues rather than discount policy.

### 8. Why did you replace the "repeat vs. one-time customers" analysis?
In the original queries, 781 customers were repeat buyers and only 12 were one-time buyers (98.5% repeat). Comparing 781 customers to 12 customers doesn't give a stakeholder anything actionable. Replacing it with Segment-level profit per customer (Query 7) and order-based Region performance (Query 8) gives a much clearer view of where margin is strong or weak.

### 9. Why did you use PostgreSQL and Python instead of doing everything in Excel?
PostgreSQL lets me store the cleaned data in a typed relational schema with indexes (`01_schema.sql`), write reproducible SQL using CTEs and window functions (`02_analysis.sql`), and separate data engineering (`load_data.py`) from analysis (`run_queries.py`) and BI consumption (`dashboard/data/*.csv`). Using Python with `python-dotenv` keeps credentials out of code, and `verify.py` automates data-quality checks against the raw CSV.

### 10. How does `verify.py` work and why did you build it?
`verify.py` reads the raw `Sample - Superstore.csv` with `pandas`, recomputes 31 key metrics—row count, distinct orders, distinct customers, total sales, total profit, overall margin, the three loss-making sub-categories, profit above vs. up to 20% discount, the 4 and 10 loss-making states, Segment profit and profit per customer, and Region sales and profit—and compares each to PostgreSQL within a \$0.02 tolerance. If any check fails, it exits with status code 1 so stale or broken numbers never make it into the README.

### 11. What are the main limitations of this analysis?
First, it's a single fictionalized US retail dataset from 2014–2017, so the patterns don't automatically generalize to other businesses or current cost structures. Second, it's observational data, not a controlled experiment—heavy discounting strongly correlates with losses, but we can't prove causal price elasticity without A/B testing. Third, the dataset has no separate COGS, freight, or customer-acquisition cost columns, only net `Profit`. Finally, it's descriptive and diagnostic only—I didn't build a forecasting model.

### 12. What would you do next if you had more data?
With unit cost (COGS) and shipping cost broken out, I'd isolate why `Supplies` loses money at low discounts and check whether `Tables` and `Bookcases` are also hurt by bulky-item freight costs. With marketing and acquisition cost data, I could compute true customer acquisition payback and lifetime value (LTV/CAC) by segment. And with a controlled pricing test, I'd measure how much volume we actually keep if we cap discounts at 20% in Texas, Ohio, Pennsylvania, and Illinois.
