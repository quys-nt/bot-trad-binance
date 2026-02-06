# -*- coding: utf-8 -*-
"""
Kiểm tra API: balance, get_income (REALIZED_PNL), get_open_orders.
Chạy: python scripts/check_api.py (từ thư mục gốc)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    print("--- Kiểm tra API Binance Futures ---\n")
    try:
        from keys_loader import get_api_credentials
        from binance.um_futures import UMFutures
        from binance.error import ClientError
    except ImportError as e:
        print("Lỗi import:", e)
        sys.exit(1)

    api, secret = get_api_credentials()
    try:
        import config as c
        _base_url = "https://testnet.binancefuture.com" if getattr(c, "TESTNET", False) else None
        if _base_url:
            print("🔧 Đang dùng TESTNET: {}\n".format(_base_url))
    except Exception:
        _base_url = None
    client = UMFutures(key=api, secret=secret, base_url=_base_url)

    # 1) Balance
    print("1) Balance USDT:")
    try:
        r = client.balance(recvWindow=8000)
        for e in r:
            if e.get("asset") == "USDT":
                print("   ✅ balance:", e.get("balance"), "| available:", e.get("availableBalance"))
                break
        else:
            print("   ⚠️  Không thấy USDT trong balance")
    except ClientError as err:
        code = getattr(err, "error_code", "")
        msg = getattr(err, "error_message", "")
        print("   ❌ Lỗi:", code, msg)
        if code == -2015:
            print("\n   💡 Hướng dẫn fix lỗi -2015:")
            print("      - Kiểm tra API key và secret trong keys.py hoặc env")
            print("      - Đảm bảo API key từ TESTNET (nếu config.TESTNET = True)")
            print("      - Kiểm tra API key đã bật 'Enable Futures'")
            print("      - Nếu có IP whitelist, thêm IP hiện tại")
            print("      - Testnet: https://testnet.binancefuture.com → API Management")
    except Exception as e:
        print("   ❌ Lỗi:", e)

    # 2) get_income (REALIZED_PNL)
    print("\n2) get_income(incomeType='REALIZED_PNL', limit=5):")
    found = False
    for name in ("get_income", "income", "get_account_trades"):
        fn = getattr(client, name, None)
        if not fn:
            continue
        try:
            if name == "get_account_trades":
                continue
            r = fn(incomeType="REALIZED_PNL", limit=5)
            if isinstance(r, list):
                print("   ✅ Method '{}' OK. Số bản ghi: {}.".format(name, len(r)))
                if r:
                    e = r[0]
                    print("   Mẫu: symbol={}, income={}, time={}".format(e.get("symbol"), e.get("income"), e.get("time")))
                found = True
                break
            else:
                print("   ⚠️  Method '{}' trả về: {} (không phải list)".format(name, type(r)))
        except TypeError:
            try:
                r = fn(limit=5)
                if isinstance(r, list):
                    print("   ✅ Method '{}' OK (không dùng incomeType). Số bản ghi: {}.".format(name, len(r)))
                    found = True
                    break
            except Exception:
                pass
        except Exception:
            pass
    if not found:
        print("   ⚠️  Không tìm thấy method get_income / income.")

    # 3) get_open_orders / get_orders
    print("\n3) Open orders:")
    found = False
    for name in ("get_open_orders", "get_orders", "get_all_orders"):
        fn = getattr(client, name, None)
        if not fn:
            continue
        try:
            r = fn(recvWindow=8000)
            if isinstance(r, list):
                print("   ✅ Method '{}' OK. Số lệnh mở: {}.".format(name, len(r)))
                found = True
                break
        except TypeError:
            try:
                r = fn(symbol="BTCUSDT", recvWindow=8000)
                if isinstance(r, list):
                    print("   ✅ Method '{}' OK (cần symbol). Số lệnh mở BTCUSDT: {}.".format(name, len(r)))
                    found = True
                    break
            except Exception:
                pass
        except Exception:
            pass
    if not found:
        print("   ⚠️  Không tìm thấy method get_open_orders phù hợp.")

    print("\n--- Kết thúc ---")


if __name__ == "__main__":
    main()
