from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from .config import SETTINGS
_engine: Engine | None = None
def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(SETTINGS.pg_dsn, pool_pre_ping=True)
    return _engine
@contextmanager
def tx():
    engine = get_engine()
    with engine.begin() as conn:
        yield conn
def upsert(conn, table: str, conflict_cols: list[str], insert_cols: list[str], rows: list[dict]):
    if not rows: return 0
    col_list = ", ".join(insert_cols)
    placeholders = ", ".join([f":{c}" for c in insert_cols])
    conflict = ", ".join(conflict_cols)
    updates = ", ".join([f"{c}=EXCLUDED.{c}" for c in insert_cols if c not in conflict_cols])
    sql = text(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT ({conflict}) DO UPDATE SET {updates}")
    conn.execute(sql, rows)
    return len(rows)
