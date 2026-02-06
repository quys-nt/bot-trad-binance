#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test gửi tin Zalo - chạy để debug API
Usage: python test_zalo_send.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.exists():
    for line in open(_env, "r", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import requests

TOKEN = (os.environ.get("ZALO_BOT_TOKEN") or "").strip()
CHAT_ID = "4857e9a6a4f24dac14e3"
TEXT = "Test từ script - bạn nhận được tin này chứ?"

if not TOKEN:
    print("Chưa có ZALO_BOT_TOKEN trong .env")
    sys.exit(1)

print("Token (10 ký tự đầu):", TOKEN[:10] + "...")
print("Chat ID:", CHAT_ID)
print()

# Test 1: zapps JSON
print("1) Thử bot-api.zapps.me (JSON body)...")
try:
    url = f"https://bot-api.zapps.me/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": TEXT}, timeout=10)
    print("   Status:", r.status_code)
    print("   Response:", r.text[:300] if r.text else "(empty)")
    if r.status_code == 200:
        print("   OK! Kiểm tra Zalo xem có tin không.")
except Exception as e:
    print("   Lỗi:", e)

print()

# Test 2: zapps form-urlencoded
print("2) Thử bot-api.zapps.me (form data)...")
try:
    url = f"https://bot-api.zapps.me/bot{TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": TEXT}, timeout=10)
    print("   Status:", r.status_code)
    print("   Response:", r.text[:300] if r.text else "(empty)")
    if r.status_code == 200:
        print("   OK!")
except Exception as e:
    print("   Lỗi:", e)

print()

# Test 3: Zalo OA
print("3) Thử openapi.zalo.me OA...")
try:
    url = "https://openapi.zalo.me/v2.0/oa/message"
    r = requests.post(
        url,
        params={"access_token": TOKEN},
        json={"recipient": {"user_id": CHAT_ID}, "message": {"text": TEXT}},
        timeout=10,
    )
    print("   Status:", r.status_code)
    print("   Response:", r.text[:300] if r.text else "(empty)")
except Exception as e:
    print("   Lỗi:", e)
