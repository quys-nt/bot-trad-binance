#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYNC DB - đóng các trade "mồ côi" trong trades.db
Chạy: python scripts/sync_db.py (từ thư mục gốc)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from binance.um_futures import UMFutures
import config as cf
import db
from keys_loader import get_api_credentials


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_pos_symbols(client: UMFutures) -> list:
    resp = client.get_position_risk(recvWindow=getattr(cf, "API_RECV_WINDOW", 8000))
    return [e["symbol"] for e in resp if float(e.get("positionAmt") or 0) != 0]


def main():
    db.init_db()
    api, secret = get_api_credentials()
    base_url = "https://testnet.binancefuture.com" if getattr(cf, "TESTNET", False) else None
    client = UMFutures(key=api, secret=secret, base_url=base_url)

    pos = set(get_pos_symbols(client))
    open_rows = db.get_open_trades(limit=2000)

    closed = 0
    skipped_still_open = 0
    for _id, sym, opened_at in open_rows:
        if not sym:
            continue
        if sym in pos:
            skipped_still_open += 1
            continue

        opened_at = int(opened_at or 0)
        cutoff = max(0, opened_at - 60_000)
        try:
            trades = client.get_account_trades(symbol=sym, limit=200)
        except Exception:
            continue

        pnl = 0.0
        last_ts = 0
        for t in trades or []:
            ts = int(t.get("time") or 0)
            if ts < cutoff:
                continue
            try:
                pnl += float(t.get("realizedPnl") or 0)
            except Exception:
                pass
            last_ts = max(last_ts, ts)

        db.record_trade_close(sym, pnl, last_ts or _now_ms(), exit_reason="SYNC")
        closed += 1

    conn = sqlite3.connect(getattr(cf, "DB_PATH", "trades.db"))
    total, closed_cnt, open_cnt = conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN closed_at IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END) FROM trades"
    ).fetchone()
    conn.close()

    print("Done.")
    print(f"- positions hiện tại: {len(pos)}")
    print(f"- closed mới: {closed}")
    print(f"- vẫn đang mở: {skipped_still_open}")
    print(f"- DB trades: total={total}, closed={closed_cnt}, open={open_cnt}")


if __name__ == "__main__":
    main()
