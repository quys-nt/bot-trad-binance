# -*- coding: utf-8 -*-
"""
TẢI API KEY – ƯU TIÊN BIẾN MÔI TRƯỜNG (AN TOÀN HƠN FILE)
========================================================
1. Ưu tiên: BINANCE_API_KEY, BINANCE_API_SECRET (env)
2. Fallback: keys.py (api, secret)

Bảo mật:
- Không commit keys.py vào git (thêm keys.py vào .gitignore)
- API key: quyền tối thiểu (chỉ Enable Futures, không Enable Withdrawals)
- Bật IP whitelist trên Binance nếu có thể
"""

import os

def load_keys():
    api = os.environ.get('BINANCE_API_KEY', '').strip()
    secret = os.environ.get('BINANCE_API_SECRET', '').strip()

    if api and secret:
        return api, secret

    try:
        from keys import api as k_api, secret as k_secret
        if k_api and k_secret:
            return str(k_api).strip(), str(k_secret).strip()
    except ImportError:
        pass

    return None, None


def get_api_credentials():
    api, secret = load_keys()
    if not api or not secret:
        raise RuntimeError(
            "Không tìm thấy API key. Cách 1: Đặt biến môi trường BINANCE_API_KEY, BINANCE_API_SECRET. "
            "Cách 2: Tạo file keys.py với api=..., secret=... (xem keys.py.example). "
            "QUAN TRỌNG: Không commit keys.py; dùng API với quyền tối thiểu (chỉ Trading, không Withdraw)."
        )
    return api, secret
