#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CÔNG CỤ PHÂN TÍCH PERFORMANCE
Chạy: python scripts/performance_analyzer.py (từ thư mục gốc)
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


def get_all_closed_trades():
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


def analyze_by_time():
    trades = get_all_closed_trades()
    if not trades:
        return None
    by_hour = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0})
    by_weekday = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0})
    for trade in trades:
        _, _, _, _, _, pnl, _, _, closed_at = trade
        dt = datetime.fromtimestamp(closed_at / 1000)
        hour = dt.hour
        weekday = dt.strftime('%A')
        if pnl > 0:
            by_hour[hour]['wins'] += 1
            by_weekday[weekday]['wins'] += 1
        else:
            by_hour[hour]['losses'] += 1
            by_weekday[weekday]['losses'] += 1
        by_hour[hour]['total_pnl'] += pnl
        by_weekday[weekday]['total_pnl'] += pnl
    return by_hour, by_weekday


def analyze_by_symbol():
    trades = get_all_closed_trades()
    if not trades:
        return None
    by_symbol = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0, 'avg_pnl': 0, 'win_rate': 0})
    for trade in trades:
        symbol, _, _, _, _, pnl, _, _, _ = trade
        by_symbol[symbol]['trades'] += 1
        if pnl > 0:
            by_symbol[symbol]['wins'] += 1
        else:
            by_symbol[symbol]['losses'] += 1
        by_symbol[symbol]['total_pnl'] += pnl
    for symbol in by_symbol:
        stats = by_symbol[symbol]
        stats['avg_pnl'] = stats['total_pnl'] / stats['trades']
        stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
    return by_symbol


def calculate_risk_metrics(trades):
    if not trades:
        return None
    pnls = [t[5] for t in trades]
    avg_pnl = sum(pnls) / len(pnls)
    std_pnl = (sum((p - avg_pnl) ** 2 for p in pnls) / len(pnls)) ** 0.5
    sharpe = avg_pnl / std_pnl if std_pnl > 0 else 0
    max_wins = max_losses = current_wins = current_losses = 0
    for pnl in pnls:
        if pnl > 0:
            current_wins += 1
            current_losses = 0
            max_wins = max(max_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    pl_ratio = abs(avg_win / avg_loss) if avg_loss < 0 else 0
    return {'sharpe_ratio': sharpe, 'max_consecutive_wins': max_wins, 'max_consecutive_losses': max_losses,
            'profit_loss_ratio': pl_ratio, 'avg_win': avg_win, 'avg_loss': avg_loss}


def generate_suggestions(trades):
    suggestions = []
    if not trades:
        return ["Chưa có đủ dữ liệu. Hãy chạy bot thêm."]
    wins = [t for t in trades if t[5] > 0]
    losses = [t for t in trades if t[5] <= 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    if win_rate < 50:
        suggestions.append(f"⚠️ Win rate thấp ({win_rate:.1f}%). Tăng MIN_24H_VOLUME_USDT, dùng SYMBOL_WHITELIST.")
    if wins and losses:
        avg_win = sum(t[5] for t in wins) / len(wins)
        avg_loss = sum(t[5] for t in losses) / len(losses)
        if avg_win / abs(avg_loss) < 1.0:
            suggestions.append("⚠️ P/L ratio thấp. Tăng TAKE_PROFIT_PCT hoặc giảm STOP_LOSS_PCT.")
    if not suggestions:
        suggestions.append("✅ Performance ổn định. Tiếp tục theo dõi.")
    return suggestions


def print_report():
    print("=" * 80)
    print("📊 BÁO CÁO PHÂN TÍCH PERFORMANCE")
    print("=" * 80)
    trades = get_all_closed_trades()
    if not trades:
        print("❌ Chưa có dữ liệu. Hãy chạy bot trước.")
        return
    wins = [t for t in trades if t[5] > 0]
    losses = [t for t in trades if t[5] <= 0]
    total_pnl = sum(t[5] for t in trades)
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    print("\n📈 THỐNG KÊ: Tổng lệnh", len(trades), "| Thắng", len(wins), "| Thua", len(losses))
    print(f"   Win Rate: {win_rate:.2f}% | Tổng PnL: {total_pnl:.3f} USDT")
    metrics = calculate_risk_metrics(trades)
    if metrics:
        print("\n⚠️ RỦI RO: Sharpe", metrics['sharpe_ratio']:.3f, "| P/L ratio", metrics['profit_loss_ratio']:.2f)
    by_symbol = analyze_by_symbol()
    if by_symbol:
        sorted_symbols = sorted(by_symbol.items(), key=lambda x: x[1]['total_pnl'], reverse=True)[:10]
        print("\n🎯 TOP SYMBOL:")
        for symbol, stats in sorted_symbols:
            print(f"   {symbol}: PnL {stats['total_pnl']:+.3f} | WR {stats['win_rate']:.1f}%")
    print("\n💡 GỢI Ý:")
    for s in generate_suggestions(trades):
        print("  ", s)
    print("\n" + "=" * 80)
    print(f"Báo cáo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | DB: {DB_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    print_report()
