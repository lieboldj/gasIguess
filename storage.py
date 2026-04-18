import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

_lock = Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts TEXT NOT NULL,
    analog INTEGER,
    digital INTEGER
);
CREATE INDEX IF NOT EXISTS idx_samples_ts ON samples(ts);
"""

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)

def insert_sample(db_path: str, ts: datetime, analog, digital) -> None:
    with _lock, _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO samples (ts, analog, digital) VALUES (?, ?, ?)",
            (ts.isoformat(timespec="seconds"),
             int(analog) if analog is not None else None,
             int(digital) if digital is not None else None),
        )
        conn.commit()

def recent(db_path: str, minutes: int):
    since = (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT ts, analog, digital FROM samples WHERE ts >= ? ORDER BY ts ASC",
            (since,),
        ).fetchall()
    return [dict(r) for r in rows]

def latest(db_path: str):
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT ts, analog, digital FROM samples ORDER BY ts DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None
