"""
Verification script: recomputes key metrics directly from the raw CSV using pandas
and compares them against PostgreSQL query results. Exits with code 1 on mismatch.
"""

import math
import sys
import pandas as pd

from db_config import PROJECT_ROOT, get_connection

CSV_PATH = PROJECT_ROOT / "data" / "Sample - Superstore.csv"
TOLERANCE = 0.02  # $0.02 or 0.02 percentage points for floating-point rounding


def assert_close(label, pandas_val, pg_val, tol=TOLERANCE):
    """Compare two numeric values and return True if within tolerance."""
    if not math.isclose(float(pandas_val), float(pg_val), abs_tol=tol):
        print(f"FAIL [{label}]: pandas={pandas_val:.4f} vs postgres={pg_val:.4f}")
        return False
    print(f"PASS [{label}]: pandas={pandas_val:.2f}, postgres={pg_val:.2f}")
    return True


def main():
    print("=" * 50)
    print("Verifying PostgreSQL Results Against Raw CSV")
    print("=" * 50)

    df = pd.read_csv(CSV_PATH, encoding="latin1")
    conn = get_connection(autocommit=True)
    failures = 0

    try:
        with conn.cursor() as cur:
            # 1. Overall totals
            cur.execute(
                "SELECT COUNT(*), COUNT(DISTINCT order_id), COUNT(DISTINCT customer_id), "
                "SUM(sales), SUM(profit) FROM superstore;"
            )
            pg_rows, pg_orders, pg_custs, pg_sales, pg_profit = cur.fetchone()

            checks = [
                ("Row count", len(df), pg_rows, 0),
                ("Distinct orders", df["Order ID"].nunique(), pg_orders, 0),
                ("Distinct customers", df["Customer ID"].nunique(), pg_custs, 0),
                ("Total sales", df["Sales"].sum(), pg_sales, TOLERANCE),
                ("Total profit", df["Profit"].sum(), pg_profit, TOLERANCE),
                (
                    "Overall profit margin %",
                    df["Profit"].sum() / df["Sales"].sum() * 100,
                    float(pg_profit) / float(pg_sales) * 100,
                    TOLERANCE,
                ),
            ]

            # 2. Loss-making sub-categories
            for sub in ["Tables", "Bookcases", "Supplies"]:
                cur.execute(
                    "SELECT SUM(sales), SUM(profit) FROM superstore WHERE sub_category = %s;",
                    (sub,),
                )
                s_pg, p_pg = cur.fetchone()
                sub_df = df[df["Sub-Category"] == sub]
                checks.append((f"{sub} sales", sub_df["Sales"].sum(), s_pg, TOLERANCE))
                checks.append((f"{sub} profit", sub_df["Profit"].sum(), p_pg, TOLERANCE))

            # 3. Discount > 20% vs <= 20%
            cur.execute(
                "SELECT "
                "SUM(CASE WHEN discount > 0.20 THEN profit ELSE 0 END), "
                "SUM(CASE WHEN discount <= 0.20 THEN profit ELSE 0 END) "
                "FROM superstore;"
            )
            pg_over20, pg_le20 = cur.fetchone()
            checks.append(("Profit (discount > 20%)", df.loc[df["Discount"] > 0.20, "Profit"].sum(), pg_over20, TOLERANCE))
            checks.append(("Profit (discount <= 20%)", df.loc[df["Discount"] <= 0.20, "Profit"].sum(), pg_le20, TOLERANCE))

            # 4. Top 4 loss states combined & all 10 loss states combined
            state_profit_pd = df.groupby("State")["Profit"].sum()
            top4_pd = state_profit_pd.loc[["Texas", "Ohio", "Pennsylvania", "Illinois"]].sum()
            all10_pd = state_profit_pd[state_profit_pd < 0].sum()

            cur.execute(
                "SELECT SUM(profit) FROM ("
                "  SELECT state, SUM(profit) AS profit FROM superstore GROUP BY state"
                ") s WHERE state IN ('Texas', 'Ohio', 'Pennsylvania', 'Illinois');"
            )
            top4_pg = cur.fetchone()[0]
            cur.execute(
                "SELECT SUM(profit) FROM ("
                "  SELECT state, SUM(profit) AS profit FROM superstore GROUP BY state HAVING SUM(profit) < 0"
                ") s;"
            )
            all10_pg = cur.fetchone()[0]
            checks.append(("Top 4 loss states profit", top4_pd, top4_pg, TOLERANCE))
            checks.append(("All 10 loss states profit", all10_pd, all10_pg, TOLERANCE))

            # 5. Segment-Region highest & lowest profit per customer
            sr_pd = df.groupby(["Segment", "Region"]).agg(
                profit=("Profit", "sum"),
                customers=("Customer ID", "nunique"),
            )
            sr_pd["ppc"] = sr_pd["profit"] / sr_pd["customers"]
            cur.execute(
                "SELECT segment, region, SUM(profit) / COUNT(DISTINCT customer_id) AS ppc "
                "FROM superstore GROUP BY segment, region ORDER BY ppc DESC;"
            )
            sr_pg = cur.fetchall()
            top_seg, top_reg, top_ppc_pg = sr_pg[0]
            bot_seg, bot_reg, bot_ppc_pg = sr_pg[-1]
            checks.append((f"Top PPC ({top_seg}-{top_reg})", sr_pd.loc[(top_seg, top_reg), "ppc"], top_ppc_pg, TOLERANCE))
            checks.append((f"Bottom PPC ({bot_seg}-{bot_reg})", sr_pd.loc[(bot_seg, bot_reg), "ppc"], bot_ppc_pg, TOLERANCE))

        for label, pd_v, pg_v, tol in checks:
            if not assert_close(label, pd_v, pg_v, tol):
                failures += 1

    finally:
        conn.close()

    print("-" * 50)
    if failures > 0:
        print(f"VERIFICATION FAILED: {failures} check(s) mismatched.")
        sys.exit(1)
    print(f"VERIFICATION PASSED: All {len(checks)} checks matched.")


if __name__ == "__main__":
    main()
