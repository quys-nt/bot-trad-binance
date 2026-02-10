#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST SYMBOL FILTER - Kiểm tra BTCDOMUSDT có bị loại bỏ không
Chạy: python test_symbol_filter.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config as cf
from binance.um_futures import UMFutures
from keys_loader import get_api_credentials

def test_filter():
    print("="*80)
    print("🧪 KIỂM TRA SYMBOL FILTER")
    print("="*80)
    
    # 1. Kiểm tra config
    print("\n1️⃣ CONFIG:")
    print(f"   SYMBOL_WHITELIST: {cf.SYMBOL_WHITELIST}")
    print(f"   MIN_24H_VOLUME: {cf.MIN_24H_VOLUME_USDT:,.0f} USDT")
    
    # 2. Lấy API
    api, secret = get_api_credentials()
    base_url = "https://testnet.binancefuture.com" if getattr(cf, "TESTNET", False) else None
    client = UMFutures(key=api, secret=secret, base_url=base_url)
    
    # 3. Lấy tất cả symbols
    all_symbols = [e["symbol"] for e in client.ticker_price() if "USDT" in e.get("symbol", "")]
    print(f"\n2️⃣ TẤT CẢ SYMBOLS USDT: {len(all_symbols)}")
    
    # 4. Test whitelist
    if cf.SYMBOL_WHITELIST:
        after_whitelist = [s for s in all_symbols if s in cf.SYMBOL_WHITELIST]
        print(f"\n3️⃣ SAU WHITELIST: {len(after_whitelist)}")
        print(f"   {after_whitelist}")
    else:
        after_whitelist = all_symbols
        print(f"\n3️⃣ KHÔNG CÓ WHITELIST - Dùng tất cả")
    
    # 5. Test blacklist
    BLACKLIST = ("USDCUSDT", "BTCDOMUSDT", "BTCSTUSDT", "ETHBTCUSDT", "DEFIUSDT")
    after_blacklist = [s for s in after_whitelist if s not in BLACKLIST]
    removed = set(after_whitelist) - set(after_blacklist)
    
    print(f"\n4️⃣ SAU BLACKLIST: {len(after_blacklist)}")
    if removed:
        print(f"   ❌ Loại bỏ: {removed}")
    else:
        print(f"   ✅ Không có coin nào trong blacklist")
    
    # 6. Test volume filter
    print(f"\n5️⃣ KIỂM TRA VOLUME (MIN: {cf.MIN_24H_VOLUME_USDT:,.0f}):")
    ticker_24h = client.ticker_24hr_price_change()
    vol_map = {e["symbol"]: float(e.get("quoteVolume", 0)) for e in ticker_24h}
    
    final = []
    for s in after_blacklist:
        vol = vol_map.get(s, 0)
        if vol >= cf.MIN_24H_VOLUME_USDT:
            final.append(s)
            print(f"   ✅ {s:15} volume: {vol:>15,.0f} USDT")
        else:
            print(f"   ❌ {s:15} volume: {vol:>15,.0f} USDT (< MIN)")
    
    # 7. Kiểm tra BTCDOMUSDT
    print(f"\n6️⃣ KIỂM TRA BTCDOMUSDT:")
    if "BTCDOMUSDT" in all_symbols:
        vol_btcdom = vol_map.get("BTCDOMUSDT", 0)
        print(f"   - Có trong all_symbols: ✅")
        print(f"   - Volume 24h: {vol_btcdom:,.0f} USDT")
        
        if cf.SYMBOL_WHITELIST and "BTCDOMUSDT" not in cf.SYMBOL_WHITELIST:
            print(f"   - Trong whitelist: ❌ (đã loại)")
        
        if "BTCDOMUSDT" in BLACKLIST:
            print(f"   - Trong blacklist: ✅ (đã loại)")
        
        if "BTCDOMUSDT" in final:
            print(f"   ❌❌❌ BUG: BTCDOMUSDT VẪN Ở TRONG FINAL LIST!")
        else:
            print(f"   ✅✅✅ OK: BTCDOMUSDT ĐÃ BỊ LOẠI BỎ")
    else:
        print(f"   - Không tồn tại trên testnet/mainnet này")
    
    # 8. Kết quả cuối
    print(f"\n7️⃣ KẾT QUẢ CUỐI CÙNG:")
    print(f"   Tổng symbols: {len(all_symbols)}")
    print(f"   Sau whitelist: {len(after_whitelist)}")
    print(f"   Sau blacklist: {len(after_blacklist)}")
    print(f"   Sau volume filter: {len(final)}")
    print(f"   Final list: {final}")
    
    print("\n" + "="*80)
    
    # 9. Đánh giá
    print("\n📊 ĐÁNH GIÁ:")
    
    success = True
    
    # Check 1: BTCDOMUSDT không trong final
    if "BTCDOMUSDT" not in final:
        print("✅ BTCDOMUSDT đã bị loại bỏ")
    else:
        print("❌ BUG: BTCDOMUSDT vẫn trong final list!")
        success = False
    
    # Check 2: Chỉ có coin trong whitelist
    if cf.SYMBOL_WHITELIST:
        unexpected = [s for s in final if s not in cf.SYMBOL_WHITELIST]
        if not unexpected:
            print("✅ Tất cả coin trong final đều nằm trong whitelist")
        else:
            print(f"❌ BUG: Có coin không trong whitelist: {unexpected}")
            success = False
    
    # Check 3: Có ít nhất 1 symbol
    if final:
        print(f"✅ Có {len(final)} symbol để trade")
    else:
        print("⚠️ CẢNH BÁO: Không có symbol nào sau filter!")
        print("   Kiểm tra lại MIN_24H_VOLUME hoặc whitelist")
    
    print("\n" + "="*80)
    if success and final:
        print("🎉 PASS: Filter hoạt động đúng!")
    elif success and not final:
        print("⚠️ WARNING: Filter OK nhưng không có coin nào")
    else:
        print("❌ FAIL: Có lỗi trong filter logic!")
    print("="*80)

if __name__ == "__main__":
    test_filter()
