import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "magic_formula.db"


def init_db():
    """Initializes the SQLite tables if they do not exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_cache (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                market_cap REAL,
                ebit REAL,
                enterprise_value REAL,
                net_working_capital REAL,
                net_fixed_assets REAL,
                updated_at TIMESTAMP
            )
        """)
        conn.commit()


def get_cached_metrics(tickers, max_age_hours=24):
    """Retrieves cached metrics if they were updated recently."""
    init_db()
    cutoff = datetime.now() - timedelta(hours=max_age_hours)

    with sqlite3.connect(DB_NAME) as conn:
        placeholders = ",".join(["?"] * len(tickers))
        query = f"""
            SELECT ticker, company_name, sector, market_cap, ebit, 
                   enterprise_value, net_working_capital, net_fixed_assets
            FROM metrics_cache 
            WHERE ticker IN ({placeholders}) AND updated_at >= ?
        """
        params = list(tickers) + [cutoff]
        df = pd.read_sql_query(query, conn, params=params)
    return df


def save_metrics_to_cache(df_metrics):
    """Saves or updates fetched stock metrics in the SQLite cache."""
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for _, row in df_metrics.iterrows():
            cursor.execute(
                """
                INSERT OR REPLACE INTO metrics_cache 
                (ticker, company_name, sector, market_cap, ebit, enterprise_value, net_working_capital, net_fixed_assets, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    row["ticker"],
                    row["company_name"],
                    row["sector"],
                    row["market_cap"],
                    row["ebit"],
                    row["enterprise_value"],
                    row["net_working_capital"],
                    row["net_fixed_assets"],
                    datetime.now(),
                ),
            )
        conn.commit()
