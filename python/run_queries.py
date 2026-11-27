"""
Run SQL analysis queries and export results to clearly named CSVs for Power BI.
"""

import warnings
import pandas as pd

from db_config import PROJECT_ROOT, get_connection

OUTPUT_DIR = PROJECT_ROOT / "dashboard" / "data"
QUERY_FILE = PROJECT_ROOT / "sql" / "02_analysis.sql"


def parse_queries(sql_content):
    """Parse SQL file into individual queries with output filenames and metadata."""
    queries = []
    current_comment = []
    current_query = []

    for line in sql_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            current_comment.append(stripped)
            continue

        current_query.append(line)
        if ";" in stripped:
            query_text = "\n".join(current_query).strip()
            if query_text:
                business_question = ""
                output_file = ""
                for cline in current_comment:
                    if "Business Question:" in cline:
                        business_question = cline.split("Business Question:", 1)[1].strip()
                    elif "Output:" in cline:
                        output_file = cline.split("Output:", 1)[1].strip()

                queries.append({
                    "business_question": business_question,
                    "output_file": output_file,
                    "query": query_text,
                })
            current_comment = []
            current_query = []

    return queries


def run_query(conn, query):
    """Execute a query using a standard cursor and return results as DataFrame."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.read_sql_query(query, conn)


def main():
    print("=" * 50)
    print("Running Analysis Queries")
    print("=" * 50)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sql_content = QUERY_FILE.read_text(encoding="utf-8")
    queries = parse_queries(sql_content)
    print(f"Found {len(queries)} queries to execute.\n")

    conn = get_connection(autocommit=True)
    try:
        for i, q in enumerate(queries, 1):
            filename = q["output_file"] or f"query_{i:02d}.csv"
            output_path = OUTPUT_DIR / filename
            print(f"Query {i} ({filename}): {q['business_question']}")

            df = run_query(conn, q["query"])
            df.to_csv(output_path, index=False)
            print(f"  -> Saved {len(df)} rows to {output_path.relative_to(PROJECT_ROOT)}")
            print(f"  -> Columns: {list(df.columns)}\n")
    finally:
        conn.close()

    print("All queries completed!")


if __name__ == "__main__":
    main()
