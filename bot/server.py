# -*- coding: utf-8 -*-
"""
ZALO BOT SERVER - Webhook nhận tin nhắn từ Zalo và điều khiển Bot Trading
Chạy: python -m bot.server (từ thư mục gốc)

Lệnh: /balance, /pos, /status, /stop, /help
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_env_path = ROOT / ".env"
if _env_path.exists():
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Cần cài Flask: pip install flask")
    sys.exit(1)

import requests

app = Flask(__name__)
ZALO_STATE_PATH = ROOT / "zalo_state.json"
BOT_COMMANDS_PATH = ROOT / "bot_commands.json"


def _get_token():
    return (os.environ.get("ZALO_BOT_TOKEN") or os.environ.get("ZALO_OA_ACCESS_TOKEN") or "").strip()


def _save_zalo_user_id(user_id: str):
    try:
        data = {}
        if ZALO_STATE_PATH.exists():
            with open(ZALO_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["user_id"] = user_id
        with open(ZALO_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.environ["ZALO_USER_ID"] = user_id
    except Exception as e:
        print("[Zalo] Lỗi lưu user_id:", e)


def _get_zalo_user_id():
    if ZALO_STATE_PATH.exists():
        try:
            with open(ZALO_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("user_id", "")
        except Exception:
            pass
    return os.environ.get("ZALO_USER_ID", "")


def _send_zalo_reply(user_id: str, text: str, chat_id: str = None) -> bool:
    token = _get_token()
    if not token:
        return False
    target = chat_id or user_id
    try:
        url = "https://bot-api.zapps.me/bot{}/sendMessage".format(token)
        r = requests.post(url, json={"chat_id": target, "text": text}, timeout=10)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    try:
        url = "https://openapi.zalo.me/v2.0/oa/message"
        r = requests.post(url, params={"access_token": token},
            json={"recipient": {"user_id": user_id}, "message": {"text": text}}, timeout=10)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    return False


def _run_bot_command(cmd: str) -> str:
    try:
        import main
    except Exception as e:
        return f"Không kết nối được bot: {e}"
    cmd = (cmd or "").strip().lower()
    if cmd in ("balance", "số dư", "sodu"):
        bal = main.get_balance_usdt()
        avail, _ = main._get_balance(use_available=True)
        if bal is not None:
            return f"💰 Balance: {bal:.2f} USDT\nKhả dụng: {(avail or bal):.2f} USDT"
        return "Không lấy được balance."
    if cmd in ("pos", "positions", "vị thế", "vithe"):
        pos = getattr(main, "_get_positions_detail", lambda: main.get_pos())()
        if not pos:
            return "Không có vị thế đang mở."
        lines = ["📊 Vị thế đang mở:"]
        for p in pos:
            if isinstance(p, dict):
                lines.append(f"  • {p.get('symbol', '?')} | amt={p.get('positionAmt')} | entry={p.get('entryPrice')} | PnL={p.get('unRealizedProfit')}")
            else:
                lines.append(f"  • {p}")
        return "\n".join(lines)
    if cmd in ("status", "trạng thái"):
        bal = main.get_balance_usdt()
        pos_list = getattr(main, "_get_positions_detail", lambda: main.get_pos())()
        n = len(pos_list) if pos_list else 0
        cfg = __import__("config", fromlist=["MAX_CONCURRENT_POSITIONS"])
        mx = getattr(cfg, "MAX_CONCURRENT_POSITIONS", 5)
        return f"📈 Trạng thái:\nBalance: {bal:.2f} USDT\nVị thế: {n}/{mx}"
    if cmd in ("stop", "dừng"):
        try:
            data = {}
            if BOT_COMMANDS_PATH.exists():
                with open(BOT_COMMANDS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["stop"] = True
            data["stop_reason"] = "Lệnh từ Zalo"
            with open(BOT_COMMANDS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return "✅ Đã gửi tín hiệu DỪNG bot."
        except Exception as e:
            return f"Lỗi: {e}"
    return ""


def _parse_zalo_webhook(data: dict) -> tuple:
    if not isinstance(data, dict):
        return "", "", ""
    msg = data.get("message") or data.get("event", {})
    chat_id = ""
    if isinstance(msg, dict):
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id", "")) if isinstance(chat, dict) and chat.get("id") else ""
        sender = msg.get("from") or msg.get("sender") or {}
        uid = sender.get("id") or sender.get("user_id") or sender.get("userId") if isinstance(sender, dict) else None
        if not uid and chat_id:
            uid = chat_id
        text = msg.get("text") or msg.get("content") or ""
        if uid:
            return str(uid), (text or "").strip(), chat_id
        text = msg.get("text") or msg.get("content") or ""
    else:
        text = ""
    sender = data.get("sender") or data.get("user") or {}
    if isinstance(sender, dict):
        uid = sender.get("id") or sender.get("user_id") or sender.get("userId")
        if uid:
            if not text and isinstance(msg, dict):
                text = msg.get("text") or msg.get("content") or ""
            return str(uid), (text or "").strip(), ""
    res = data.get("result") or data.get("data")
    if isinstance(res, dict):
        return _parse_zalo_webhook(res)
    if isinstance(res, list) and res:
        return _parse_zalo_webhook(res[0])
    return "", "", ""


@app.route("/zalo-webhook", methods=["GET"])
def zalo_verify():
    challenge = request.args.get("challenge") or request.args.get("verify_token")
    return challenge if challenge else "ok"


@app.route("/zalo-webhook", methods=["POST"])
def zalo_webhook():
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data.get("message") and (data.get("data") or data.get("event")):
            data = data.get("data") or data.get("event") or data
    except Exception:
        return jsonify({"ok": False}), 400

    user_id, text, chat_id = _parse_zalo_webhook(data)
    if not user_id:
        for key in ("sender", "user", "from", "recipient"):
            obj = data.get(key)
            if isinstance(obj, dict):
                uid = obj.get("id") or obj.get("user_id")
                if uid:
                    user_id = str(uid)
                    break
        if not user_id:
            return jsonify({"ok": True})

    _save_zalo_user_id(user_id)
    if not text:
        _send_zalo_reply(user_id, "👋 Xin chào! Gửi /help để xem lệnh.", chat_id)
        return jsonify({"ok": True})

    txt = text.lower().strip()
    if txt in ("help", "/help", "hướng dẫn"):
        reply = "🤖 Lệnh: /balance - Số dư | /pos - Vị thế | /status - Trạng thái | /stop - Dừng bot | /help"
    else:
        cmd = txt.lstrip("/").split()[0] if txt else ""
        reply = _run_bot_command(cmd)
        if not reply:
            reply = "Lệnh không rõ. Gửi /help để xem danh sách."
    _send_zalo_reply(user_id, reply, chat_id)
    return jsonify({"ok": True})


@app.route("/")
def index():
    return "Zalo Bot Webhook đang chạy. Endpoint: POST /zalo-webhook"


if __name__ == "__main__":
    port = int(os.environ.get("ZALO_BOT_PORT", "5001"))
    print("Chạy tại http://0.0.0.0:{}".format(port))
    app.run(host="0.0.0.0", port=port, debug=False)
