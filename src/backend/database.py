"""
SQLite database layer -- zero-install, single-file, works on Jetson and anywhere.
"""
from __future__ import annotations
import os, sqlite3, threading
from backend.config import DB_PATH

_local = threading.local()


def get_db() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


def close_db():
    conn = getattr(_local, "conn", None)
    if conn:
        conn.close()
        _local.conn = None


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            pw_hash     TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id       TEXT    NOT NULL,
            feed_name     TEXT    NOT NULL,
            anomaly_type  TEXT    NOT NULL,
            severity      TEXT    NOT NULL,
            class_name    TEXT    NOT NULL,
            confidence    REAL    NOT NULL,
            bbox          TEXT,
            snapshot      TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_type  TEXT    NOT NULL,
            severity      TEXT    NOT NULL,
            feed_name     TEXT    NOT NULL,
            class_name    TEXT    NOT NULL,
            confidence    REAL    NOT NULL,
            message       TEXT,
            snapshot      TEXT,
            sms_sent      INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS feed_configs (
            feed_id    TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            source     TEXT NOT NULL,
            zone_type  TEXT DEFAULT 'general',
            active     INTEGER DEFAULT 1
        );
    """)
    db.commit()


def query(sql: str, params: tuple = (), one: bool = False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(sql: str, params: tuple = ()) -> int:
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid
