from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

DB_PATH = Path("data/psp_flow_crm.db")
PROCESSED = Path("data/processed")

TABLES = [
    "owners", "products_plans", "companies", "contacts", "leads", "deals", "activities",
    "subscriptions", "onboarding", "tasks", "usage_events", "support_tickets", "cs_activities",
]

def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    sql = Path("sql_schema.sql").read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def _load_csv(conn: sqlite3.Connection, table: str, folder: Path = PROCESSED) -> int:
    f = folder / f"{table}.csv"
    df = pd.read_csv(f)
    df.to_sql(table, conn, if_exists="append", index=False)
    return len(df)


def rebuild_database(db_path: Path = DB_PATH, folder: Path = PROCESSED) -> dict:
    if db_path.exists():
        db_path.unlink()
    conn = connect(db_path)
    create_schema(conn)
    counts = {table: _load_csv(conn, table, folder) for table in TABLES}
    conn.commit()
    conn.close()
    return counts


def read_table(table: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    with connect(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
