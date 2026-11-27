"""
Shared database configuration and connection helper.
Reads PostgreSQL credentials from the project-level .env file.
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_db_config():
    """Return PostgreSQL connection parameters from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "superstore"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def get_connection(autocommit=False):
    """Create and return a PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**get_db_config())
        conn.autocommit = autocommit
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)
