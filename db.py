# -*- coding: utf-8 -*-
"""
SQLite: lưu lịch sử lệnh và snapshot balance/position.
Dùng cho dashboard và phân tích, không phụ thuộc API income.
"""

import os
import sqlite3
import json
import time

# Import config khi chạy (tránh circular)
def _config():
    import config as c
    return c

def _conn():
    cfg = _config()
    path = getattr(cfg, "DB_PATH", "trades.db")
    return sqlite3.connect(path, check_same_thread=False)


def init_db():
    try:
        cfg = _config()
        if not getattr(cfg, "ENABLE_DB", True):
            return
    except Exception:
        pass
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            qty REAL NOT NULL,
            exit_price REAL,
            pnl REAL,
            exit_reason TEXT,
            opened_at INTEGER NOT NULL,
            closed_at INTEGER,
            created_at INTEGER NOT NULL
        );
        -- Lưu income events (REALIZED_PNL) để debug / fallback hiển thị dashboard
        CREATE TABLE IF NOT EXISTS income (
            tran_id TEXT PRIMARY KEY,
            symbol TEXT,
            income REAL,
            income_type TEXT,
            ts INTEGER,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            balance REAL NOT NULL,
            available REAL NOT NULL,
            positions_json TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
        CREATE INDEX IF NOT EXISTS idx_trades_opened ON trades(opened_at);
        CREATE INDEX IF NOT EXISTS idx_income_ts ON income(ts);
        CREATE INDEX IF NOT EXISTS idx_status_ts ON status(ts);
    """)
    c.commit()
    c.close()


def record_trade_open(symbol: str, side: str, entry_price: float, qty: float):
    try:
        if not getattr(_config(), "ENABLE_DB", True):
            return
    except Exception:
        return
    ts = int(time.time() * 1000)
    c = _conn()
    c.execute(
        "INSERT INTO trades (symbol, side, entry_price, qty, exit_price, pnl, exit_reason, opened_at, closed_at, created_at) VALUES (?,?,?,?, NULL, NULL, NULL, ?, NULL, ?)",
        (symbol, side.upper(), entry_price, qty, ts, ts)
    )
    c.commit()
    c.close()


def record_trade_close(symbol: str, pnl: float, closed_at: int, exit_reason: str = None):
    try:
        if not getattr(_config(), "ENABLE_DB", True):
            return
    except Exception:
        return
    if exit_reason is None:
        exit_reason = "SL" if pnl < 0 else "TP"
    c = _conn()
    row = c.execute(
        "SELECT id, entry_price, qty FROM trades WHERE symbol=? AND closed_at IS NULL ORDER BY opened_at DESC LIMIT 1",
        (symbol,)
    ).fetchone()
    if row:
        tid, entry, qty = row
        exit_price = entry + (pnl / qty) if qty and qty != 0 else None
        c.execute(
            "UPDATE trades SET exit_price=?, pnl=?, exit_reason=?, closed_at=? WHERE id=?",
            (exit_price, pnl, exit_reason, closed_at, tid)
        )
    c.commit()
    c.close()


def record_status(balance: float, available: float, positions: list):
    try:
        if not getattr(_config(), "ENABLE_DB", True):
            return
    except Exception:
        return
    ts = int(time.time() * 1000)
    c = _conn()
    c.execute(
        "INSERT INTO status (ts, balance, available, positions_json) VALUES (?,?,?,?)",
        (ts, balance, available, json.dumps(positions or []))
    )
    c.commit()
    c.close()

def record_income_event(tran_id, symbol: str, income: float, ts: int, income_type: str = "REALIZED_PNL"):
    """Ghi 1 income event (INSERT OR IGNORE theo tran_id)."""
    try:
        if not getattr(_config(), "ENABLE_DB", True):
            return
    except Exception:
        return
    if not tran_id:
        return
    now = int(time.time() * 1000)
    c = _conn()
    c.execute(
        "INSERT OR IGNORE INTO income (tran_id, symbol, income, income_type, ts, created_at) VALUES (?,?,?,?,?,?)",
        (str(tran_id), symbol, float(income or 0), income_type, int(ts or 0), now),
    )
    c.commit()
    c.close()


def get_recent_income(limit: int = 10):
    """Lấy các income events mới nhất."""
    c = _conn()
    r = c.execute(
        "SELECT symbol, income, income_type, ts, tran_id FROM income ORDER BY ts DESC LIMIT ?",
        (limit,),
    ).fetchall()
    c.close()
    return r


def get_trades(limit: int = 500):
    c = _conn()
    r = c.execute(
        "SELECT symbol, side, entry_price, qty, exit_price, pnl, exit_reason, opened_at, closed_at FROM trades ORDER BY opened_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    c.close()
    return r


def get_open_trades(limit: int = 500):
    """Lấy các trade đang mở (closed_at IS NULL)."""
    c = _conn()
    r = c.execute(
        "SELECT id, symbol, opened_at FROM trades WHERE closed_at IS NULL ORDER BY opened_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    c.close()
    return r


def get_latest_status():
    c = _conn()
    r = c.execute(
        "SELECT ts, balance, available, positions_json FROM status ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    c.close()
    return r


def get_equity_series():
    """Trả về list (ts, equity) từ trades để vẽ drawdown. equity = cumsum(pnl) + start."""
    c = _conn()
    rows = c.execute(
        "SELECT closed_at, pnl FROM trades WHERE closed_at IS NOT NULL AND pnl IS NOT NULL ORDER BY closed_at ASC"
    ).fetchall()
    c.close()
    if not rows:
        return [], []
    start = 10000.0
    eq = start
    ts_list, eq_list = [], []
    for closed_at, pnl in rows:
        eq += pnl
        ts_list.append(closed_at)
        eq_list.append(eq)
    return ts_list, eq_list
