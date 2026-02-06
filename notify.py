# -*- coding: utf-8 -*-
"""
Thông báo Telegram / Discord / Zalo khi mở lệnh, đóng lệnh (SL/TP), hoặc bot dừng do rủi ro.
Cần: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (env). Discord: DISCORD_WEBHOOK_URL (env).
Zalo: ZALO_BOT_TOKEN, ZALO_USER_ID (env). ZALO_USER_ID được lưu tự động khi bạn nhắn bot lần đầu.
"""

import os

try:
    import requests
except ImportError:
    requests = None


def _get_zalo_user_id() -> str:
    """Lấy ZALO_USER_ID từ env hoặc zalo_state.json (lưu khi nhắn bot lần đầu)."""
    uid = (os.environ.get("ZALO_USER_ID") or "").strip()
    if uid:
        return uid
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zalo_state.json")
        if os.path.isfile(path):
            import json
            with open(path, "r", encoding="utf-8") as f:
                return (json.load(f).get("user_id") or "").strip()
    except Exception:
        pass
    return ""


def send_zalo(msg: str) -> bool:
    """
    Gửi tin nhắn qua Zalo Bot (Zalo OA hoặc Zalo zapps).
    Cần: ZALO_BOT_TOKEN (hoặc ZALO_OA_ACCESS_TOKEN), ZALO_USER_ID trong .env hoặc zalo_state.json
    ZALO_USER_ID được lưu tự động khi bạn nhắn tin cho bot lần đầu (chạy zalo_bot_server.py).
    """
    token = (os.environ.get("ZALO_BOT_TOKEN") or os.environ.get("ZALO_OA_ACCESS_TOKEN") or "").strip()
    user_id = _get_zalo_user_id()
    if not token or not user_id:
        return False
    if not requests:
        return False
    try:
        # Zalo OA API: https://openapi.zalo.me/v2.0/oa/message
        url = "https://openapi.zalo.me/v2.0/oa/message"
        params = {"access_token": token}
        payload = {
            "recipient": {"user_id": user_id},
            "message": {"text": msg},
        }
        r = requests.post(url, params=params, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def send_telegram(msg: str) -> bool:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        return False
    if not requests:
        return False
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        r = requests.post(url, json={"chat_id": chat, "text": msg}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def send_discord(msg: str) -> bool:
    url = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
    if not url or not requests:
        return False
    try:
        r = requests.post(url, json={"content": msg}, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False


def send(msg: str):
    """Gửi cả Telegram, Discord và Zalo nếu đã cấu hình."""
    send_telegram(msg)
    send_discord(msg)
    send_zalo(msg)
