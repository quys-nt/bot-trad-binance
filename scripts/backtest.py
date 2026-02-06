# -*- coding: utf-8 -*-
"""
Backtest chiến lược trên dữ liệu lịch sử.
Chạy: python scripts/backtest.py --symbol BTCUSDT [--days 60] [--strategy multi]
      python scripts/backtest.py --csv klines.csv [--strategy multi]

Dữ liệu: lấy từ API (cần keys) hoặc file CSV có cột: Time,Open,High,Low,Close,Volume.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import config as cf
from strategies import get_strategy


def load_klines_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    for c in ("Time", "Open", "High", "Low", "Close", "Volume"):
        if c not in df.columns and c.lower() in [x.lower() for x in df.columns]:
            df = df.rename(columns={k: c for k in df.columns if k.lower() == c.lower()})
    if "Time" in df.columns and not pd.api.types.is_numeric_dtype(df["Time"]):
        df["Time"] = pd.to_datetime(df["Time"]).astype("int64") // 10**6
    if "Time" in df.columns:
        df = df.set_index("Time")
    for c in ("Open", "High", "Low", "Close", "Volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(how="all").astype(float)


def fetch_klines_api(symbol: str, days: int = 60) -> pd.DataFrame:
    import time
    from keys_loader import get_api_credentials
    from binance.um_futures import UMFutures

    api, secret = get_api_credentials()
    _base_url = "https://testnet.binancefuture.com" if getattr(cf, "TESTNET", False) else None
    client = UMFutures(key=api, secret=secret, base_url=_base_url)
    interval = getattr(cf, "KLINES_INTERVAL", "15m")
    limit = min(1500, max(500, int(days * 96 * 1.2)))
    out = []
    start = None
    while len(out) < limit:
        kw = {"symbol": symbol, "interval": interval, "limit": 1000}
        if start:
            kw["startTime"] = start
        resp = client.klines(**kw)
        if not resp:
            break
        out.extend(resp)
        start = resp[-1][0] + 1
        if len(resp) < 1000:
            break
        time.sleep(0.2)
    df = pd.DataFrame(out).iloc[:, :6]
    df.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
    df = df.set_index("Time").astype(float)
    df.index = pd.to_datetime(df.index, unit="ms")
    return df


def run_backtest(kl: pd.DataFrame, strategy_name: str = None, sl: float = None, tp: float = None):
    strategy_name = strategy_name or getattr(cf, "STRATEGY", "multi")
    sl = sl if sl is not None else getattr(cf, "STOP_LOSS_PCT", 0.025)
    tp = tp if tp is not None else getattr(cf, "TAKE_PROFIT_PCT", 0.02)
    sig_fn = get_strategy(strategy_name)

    trades = []
    position = None
    min_bars = 210 if strategy_name == "multi" else 50

    for i in range(min_bars, len(kl) - 1):
        kl_slice = kl.iloc[: i + 1]
        if position is None:
            sig = sig_fn(kl_slice)
            if sig in ("up", "down"):
                entry_price = float(kl.iloc[i + 1]["Open"])
                position = ("long" if sig == "up" else "short", i + 1, entry_price)
            continue

        side, entry_idx, entry_price = position
        row = kl.iloc[i]
        o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]

        if side == "long":
            sl_price = entry_price * (1 - sl)
            tp_price = entry_price * (1 + tp)
            if l <= sl_price:
                pnl_pct = (sl_price - entry_price) / entry_price
                trades.append((entry_idx, i, "long", entry_price, sl_price, pnl_pct, "SL"))
                position = None
            elif h >= tp_price:
                pnl_pct = (tp_price - entry_price) / entry_price
                trades.append((entry_idx, i, "long", entry_price, tp_price, pnl_pct, "TP"))
                position = None
        else:
            sl_price = entry_price * (1 + sl)
            tp_price = entry_price * (1 - tp)
            if h >= sl_price:
                pnl_pct = (entry_price - sl_price) / entry_price
                trades.append((entry_idx, i, "short", entry_price, sl_price, pnl_pct, "SL"))
                position = None
            elif l <= tp_price:
                pnl_pct = (entry_price - tp_price) / entry_price
                trades.append((entry_idx, i, "short", entry_price, tp_price, pnl_pct, "TP"))
                position = None

    if not trades:
        return {"trades": 0, "win": 0, "loss": 0, "win_rate": 0, "total_return_pct": 0, "max_dd_pct": 0}

    wins = sum(1 for t in trades if t[5] > 0)
    total = len(trades)
    total_ret = sum(t[5] for t in trades) * 100

    eq = 10000.0
    peak = eq
    max_dd = 0
    for t in trades:
        eq += t[5] * 10000 * 0.1
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return {
        "trades": total,
        "win": wins,
        "loss": total - wins,
        "win_rate": wins / total * 100 if total else 0,
        "total_return_pct": total_ret,
        "max_dd_pct": max_dd,
        "list": trades,
    }


def main():
    ap = argparse.ArgumentParser(description="Backtest chiến lược")
    ap.add_argument("--symbol", default=None, help="Symbol (vd: BTCUSDT) khi lấy từ API")
    ap.add_argument("--csv", default=None, help="Đường dẫn file CSV klines")
    ap.add_argument("--days", type=int, default=60, help="Số ngày khi lấy từ API (mặc định 60)")
    ap.add_argument("--strategy", default=None, help="multi, rsi, macd (mặc định từ config)")
    args = ap.parse_args()

    if args.csv:
        kl = load_klines_csv(args.csv)
        print("Đã load {} nến từ {}".format(len(kl), args.csv))
    elif args.symbol:
        try:
            kl = fetch_klines_api(args.symbol, args.days)
            print("Đã lấy {} nến {} từ API".format(len(kl), args.symbol))
        except Exception as e:
            print("Lỗi lấy dữ liệu API:", e)
            sys.exit(1)
    else:
        print("Cần --symbol HOẶC --csv. VD: --symbol BTCUSDT --days 60")
        sys.exit(1)

    if len(kl) < 250:
        print("Cần ít nhất 250 nến. Hiện có {}.".format(len(kl)))
        sys.exit(1)

    res = run_backtest(kl, strategy_name=args.strategy)
    print("\n--- KẾT QUẢ BACKTEST ---")
    print("Số lệnh:     ", res["trades"])
    print("Thắng / Thua:", res["win"], "/", res["loss"])
    print("Win rate:    {:.1f}%".format(res["win_rate"]))
    print("Tổng lợi nhuận (giả định mỗi lệnh 10% vốn): {:.2f}%".format(res["total_return_pct"]))
    print("Max drawdown: {:.1f}%".format(res["max_dd_pct"]))


if __name__ == "__main__":
    main()
