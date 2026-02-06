#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHÂN TÍCH ĐƠN GIẢN - DỄ HIỂU
Chạy: python scripts/analyze_simple.py (từ thư mục gốc)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import config as cf
    DB_PATH = getattr(cf, "DB_PATH", "trades.db")
    VOLUME_USDT = getattr(cf, "VOLUME_USDT", 8.0)
    LEVERAGE = getattr(cf, "LEVERAGE", 2)
except Exception:
    DB_PATH = str(ROOT / "trades.db")
    VOLUME_USDT = 8.0
    LEVERAGE = 2


def get_conn():
    return sqlite3.connect(DB_PATH)


def get_closed_trades():
    conn = get_conn()
    cursor = conn.execute("""
        SELECT symbol, side, entry_price, qty, exit_price, pnl, exit_reason,
               opened_at, closed_at
        FROM trades
        WHERE closed_at IS NOT NULL AND pnl IS NOT NULL
        ORDER BY closed_at ASC
    """)
    trades = cursor.fetchall()
    conn.close()
    return trades


def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text):
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80 + "\n")


def analyze_simple():
    trades = get_closed_trades()

    if not trades:
        print_header("❌ CHƯA CÓ DỮ LIỆU")
        print("Bot chưa có lệnh nào đóng. Vui lòng:")
        print("1. Chạy bot: python main.py")
        print("2. Đợi ít nhất 1-2 lệnh đóng (SL hoặc TP)")
        print("3. Chạy lại phân tích này")
        return

    print_header("📊 BÁO CÁO PHÂN TÍCH ĐƠN GIẢN")

    wins = [t for t in trades if t[5] > 0]
    losses = [t for t in trades if t[5] <= 0]
    total_pnl = sum(t[5] for t in trades)
    win_rate = len(wins) / len(trades) * 100 if trades else 0

    print_section("1️⃣ TỔNG QUAN")
    print(f"📈 Tổng số lệnh đã đóng: {len(trades)}")
    print(f"   ├─ ✅ Thắng: {len(wins)} lệnh")
    print(f"   └─ ❌ Thua: {len(losses)} lệnh")
    print(f"\n🎯 Tỷ lệ thắng: {win_rate:.1f}%")
    print(f"💰 Tổng lãi/lỗ: {total_pnl:+.2f} USDT")

    print_section("2️⃣ PHÂN TÍCH CHI TIẾT")
    avg_win = sum(t[5] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t[5] for t in losses) / len(losses) if losses else 0
    print(f"💵 Trung bình lệnh THẮNG: +{avg_win:.3f} USDT")
    print(f"💵 Trung bình lệnh THUA: {avg_loss:.3f} USDT")

    print_section("3️⃣ DỰ ĐOÁN LỢI NHUẬN")
    profit_per_trade = (avg_win * win_rate / 100) + (avg_loss * (100 - win_rate) / 100)
    trades_per_day = len(trades) / max(1, (trades[-1][8] - trades[0][8]) / 86400000)
    trades_per_month = trades_per_day * 30
    monthly_profit = profit_per_trade * trades_per_month
    print(f"📈 Lợi nhuận trung bình/lệnh: {profit_per_trade:+.4f} USDT")
    print(f"📊 Dự kiến lệnh/tháng: {trades_per_month:.0f}")
    print(f"💰 Dự kiến lợi nhuận/tháng: {monthly_profit:+.2f} USDT")

    print_section("4️⃣ PHÂN TÍCH THEO COIN")
    by_symbol = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0})
    for t in trades:
        sym = t[0]
        pnl = t[5]
        by_symbol[sym]['trades'] += 1
        by_symbol[sym]['pnl'] += pnl
        if pnl > 0:
            by_symbol[sym]['wins'] += 1
    for sym in by_symbol:
        s = by_symbol[sym]
        s['win_rate'] = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    sorted_symbols = sorted(by_symbol.items(), key=lambda x: x[1]['pnl'], reverse=True)
    print("🏆 TOP 5 COIN TỐT NHẤT:")
    for i, (sym, stats) in enumerate(sorted_symbols[:5], 1):
        print(f"{i}. {sym:12} - Lãi: {stats['pnl']:+.3f} USDT | WR: {stats['win_rate']:.0f}% | Lệnh: {stats['trades']}")

    print("\n" + "=" * 80)
    print(f"Báo cáo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | DB: {DB_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    analyze_simple()
