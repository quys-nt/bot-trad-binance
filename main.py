# -*- coding: utf-8 -*-
"""
BOT TRADING FUTURES - BẢN AN TOÀN CAO, QUẢN LÝ RỦI RO
======================================================
- Giới hạn drawdown, thua lỗ liên tiếp, lỗ trong ngày
- Kiểm tra thanh khoản, margin, retry khi mất mạng
- Chiến lược đa chỉ báo (RSI + StochRSI + MACD + EMA) để tăng tỷ lệ thắng
- Hỗ trợ API key qua biến môi trường hoặc keys.py
- Logging, DB, Telegram/Discord, backtest, dashboard
"""

import math
import os
import json
import logging
from datetime import datetime, timezone
from time import sleep

import pandas as pd
from binance.um_futures import UMFutures
from binance.error import ClientError

from keys_loader import get_api_credentials
from strategies import get_strategy
import config as cf
import db
import notify

# --- Logging (UTF-8) ---
_handlers = [logging.StreamHandler()]
if getattr(cf, "LOG_FILE", None):
    _handlers.append(logging.FileHandler(cf.LOG_FILE, encoding="utf-8"))
logging.basicConfig(
    level=getattr(logging, (getattr(cf, "LOG_LEVEL", "INFO") or "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
)
log = logging.getLogger(__name__)

# --- Khởi tạo client (dùng keys từ env hoặc keys.py) ---
_api, _secret = get_api_credentials()
# Dùng testnet nếu config.TESTNET = True
_base_url = "https://testnet.binancefuture.com" if getattr(cf, "TESTNET", False) else None
if _base_url:
    log.info("🔧 Đang dùng TESTNET: %s", _base_url)
client = UMFutures(key=_api, secret=_secret, base_url=_base_url)

# --- File lưu trạng thái rủi ro (drawdown, ngày, consecutive losses) ---
RISK_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_state.json")
# --- File lệnh từ Zalo bot (stop, etc.) ---
BOT_COMMANDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_commands.json")


def _api_retry(fn, *args, **kwargs):
    """Gọi API với retry khi lỗi mạng / 5xx."""
    for i in range(cf.MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err = str(e).lower()
            if i == cf.MAX_RETRIES - 1:
                raise
            if "connection" in err or "timeout" in err or "5" in str(getattr(e, "status_code", "")):
                sleep(cf.RETRY_DELAY_SEC)
                continue
            raise


def _load_risk_state():
    try:
        if os.path.isfile(RISK_STATE_PATH):
            with open(RISK_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _save_risk_state(data):
    try:
        # Giữ tối đa 200 tran_id
        ids = data.get("income_tran_ids_seen") or []
        data["income_tran_ids_seen"] = ids[-200:]
        with open(RISK_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log.warning("[Risk] Không ghi risk_state.json: %s", e)


def _get_balance(use_available=True):
    """Lấy balance USDT. use_available=True dùng availableBalance nếu có."""
    try:
        resp = _api_retry(lambda: client.balance(recvWindow=cf.API_RECV_WINDOW))
        for e in resp:
            if e.get("asset") == "USDT":
                bal = float(e.get("balance") or 0)
                av = e.get("availableBalance")
                if use_available and av is not None:
                    return float(av), bal
                return bal, bal
    except ClientError as err:
        log.warning("Balance error: %s - %s - %s",
            getattr(err, "status_code", ""), getattr(err, "error_code", ""), getattr(err, "error_message", ""))
    return None, None


def get_balance_usdt():
    """Balance tổng (để hiển thị)."""
    _, b = _get_balance(use_available=False)
    return b


def get_available_balance_usdt():
    """Balance khả dụng (để kiểm tra margin trước khi mở lệnh)."""
    a, _ = _get_balance(use_available=True)
    return a


def get_tickers_usdt():
    """Tất cả cặp USDT."""
    try:
        resp = _api_retry(client.ticker_price)
        return [e["symbol"] for e in resp if "USDT" in e.get("symbol", "")]
    except Exception as e:
        log.warning("get_tickers_usdt error: %s", e)
        return []


def get_tickers_filtered():
    """Lọc theo volume 24h và whitelist."""
    base = get_tickers_usdt()
    out = []
    # Whitelist
    if cf.SYMBOL_WHITELIST:
        base = [s for s in base if s in cf.SYMBOL_WHITELIST]
    # Loại trừ
    base = [s for s in base if s not in ("USDCUSDT",)]
    # Lọc volume 24h (nếu API có)
    try:
        resp = _api_retry(client.ticker_24hr_price_change)
        vol_map = {e["symbol"]: float(e.get("quoteVolume") or 0) for e in resp if "symbol" in e}
        for s in base:
            if vol_map.get(s, 0) >= cf.MIN_24H_VOLUME_USDT:
                out.append(s)
    except Exception:
        out = base  # Không có 24h thì bỏ qua lọc volume
    return out if out else base


def klines(symbol):
    try:
        resp = pd.DataFrame(_api_retry(client.klines, symbol, cf.KLINES_INTERVAL))
        resp = resp.iloc[:, :6]
        resp.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
        resp = resp.set_index("Time")
        resp.index = pd.to_datetime(resp.index, unit="ms")
        return resp.astype(float)
    except ClientError as err:
        log.warning("klines error: %s - %s", getattr(err, "error_code", ""), getattr(err, "error_message", ""))
        return None


def set_leverage(symbol, level):
    try:
        _api_retry(client.change_leverage, symbol=symbol, leverage=level, recvWindow=cf.API_RECV_WINDOW)
        log.info("Leverage %s set to %s for %s", level, symbol, symbol)
    except ClientError as err:
        log.warning("set_leverage error: %s - %s", getattr(err, "error_code", ""), getattr(err, "error_message", ""))


def set_mode(symbol, margin_type):
    try:
        _api_retry(client.change_margin_type, symbol=symbol, marginType=margin_type, recvWindow=cf.API_RECV_WINDOW)
        log.info("Margin %s set to %s for %s", margin_type, symbol, symbol)
    except ClientError as err:
        if getattr(err, "error_code", None) != -4046:
            log.warning("set_mode error: %s - %s", getattr(err, "error_code", ""), getattr(err, "error_message", ""))


def get_price_precision(symbol):
    resp = _api_retry(client.exchange_info)
    for e in resp.get("symbols", []):
        if e.get("symbol") == symbol:
            return e.get("pricePrecision", 2)
    return 2


def get_qty_precision(symbol):
    resp = _api_retry(client.exchange_info)
    for e in resp.get("symbols", []):
        if e.get("symbol") == symbol:
            return e.get("quantityPrecision", 3)
    return 3


def open_order(symbol, side):
    """Đặt lệnh vào + SL + TP. Có buffer slippage. Trả về (ok, entry_price, qty)."""
    try:
        price = float(_api_retry(client.ticker_price, symbol)["price"])
    except Exception as e:
        log.warning("open_order: không lấy được giá %s: %s", symbol, e)
        return False, None, None

    qty_prec = get_qty_precision(symbol)
    price_prec = get_price_precision(symbol)
    vol = cf.VOLUME_USDT
    min_notional = getattr(cf, "MIN_NOTIONAL_USDT", 5.0)
    qty = round(vol / price, qty_prec)
    # Binance: notional (qty * price) phải >= 5 USDT (-4164). Làm tròn qty có thể làm notional < 5 → làm tròn lên.
    if qty <= 0:
        log.warning("open_order: qty=0 %s (vol=%s, price=%s)", symbol, vol, price)
        return False, None, None
    notional = qty * price
    if notional < min_notional:
        qty_min = min_notional / price
        qty = math.ceil(qty_min * (10 ** qty_prec)) / (10 ** qty_prec)
        if qty <= 0:
            log.warning("open_order: qty=0 sau khi đảm bảo min notional %s", symbol)
            return False, None, None

    # SL/TP có buffer chống trượt giá
    sl = cf.STOP_LOSS_PCT
    tp = cf.TAKE_PROFIT_PCT
    buf = cf.SLIPPAGE_BUFFER_PCT

    def _place_algo_order(sym, side_val, order_type, qty_val, trigger_price):
        """Đặt lệnh SL/TP qua Algo Order API (Binance yêu cầu -4120). Trả về algoId hoặc None."""
        try:
            params = {
                "algoType": "CONDITIONAL",
                "symbol": sym,
                "side": side_val,
                "type": order_type,
                "quantity": qty_val,
                "triggerPrice": trigger_price,
                "timeInForce": "GTC",
                "recvWindow": cf.API_RECV_WINDOW,
            }
            r = client.sign_request("POST", "/fapi/v1/algoOrder", params)
            return r.get("algoId") if isinstance(r, dict) else None
        except Exception as e:
            log.warning("_place_algo_order: %s", e)
            return None

    def _cancel_algo_order(algo_id):
        try:
            if algo_id is None:
                return
            client.sign_request("DELETE", "/fapi/v1/algoOrder", {"algoId": algo_id, "recvWindow": cf.API_RECV_WINDOW})
        except Exception:
            pass

    def _cancel_order(s, oid):
        try:
            client.cancel_order(symbol=s, orderId=oid, recvWindow=cf.API_RECV_WINDOW)
        except Exception:
            pass

    if side == "buy":
        oid1 = None
        algo_sl = algo_tp = None
        sl_p = round(price * (1 - sl + buf), price_prec)
        tp_p = round(price * (1 + tp + buf), price_prec)
        try:
            r1 = client.new_order(symbol=symbol, side="BUY", type="LIMIT", quantity=qty, timeInForce="GTC", price=round(price, price_prec), recvWindow=cf.API_RECV_WINDOW)
            oid1 = r1.get("orderId")
            sleep(1)
            algo_sl = _place_algo_order(symbol, "SELL", "STOP_MARKET", qty, sl_p)
            if algo_sl is None:
                raise ClientError(None, None, "Failed to place SL algo order")
            sleep(1)
            algo_tp = _place_algo_order(symbol, "SELL", "TAKE_PROFIT_MARKET", qty, tp_p)
            if algo_tp is None:
                _cancel_algo_order(algo_sl)
                raise ClientError(None, None, "Failed to place TP algo order")
        except ClientError as err:
            if oid1 is not None:
                _cancel_order(symbol, oid1)
            _cancel_algo_order(algo_sl)
            _cancel_algo_order(algo_tp)
            code = getattr(err, "error_code", None)
            msg = getattr(err, "error_message", "")
            if code in (-2019, -1111, -4164) or "margin" in msg.lower() or "insufficient" in msg.lower():
                log.warning("open_order: margin/insufficient – bỏ qua: %s %s", code, msg)
                return False, None, None
            log.warning("open_order BUY error: %s %s", code, msg)
            return False, None, None

        sleep(12)
        _query = getattr(client, "get_order", None) or getattr(client, "query_order", None)
        if _query:
            try:
                o = _query(symbol=symbol, orderId=oid1, recvWindow=cf.API_RECV_WINDOW)
                if (o.get("status") or "").upper() != "FILLED":
                    log.warning("Lệnh vào chưa khớp – hủy entry + SL + TP để tránh lệnh mồ côi")
                    _cancel_order(symbol, oid1)
                    _cancel_algo_order(algo_sl)
                    _cancel_algo_order(algo_tp)
                    return False, None, None
            except Exception as e:
                log.warning("get_order check error: %s", e)

        log.info("%s BUY OK, SL=%s TP=%s", symbol, sl_p, tp_p)
        return True, price, qty

    if side == "sell":
        oid1 = None
        algo_sl = algo_tp = None
        sl_p = round(price * (1 + sl - buf), price_prec)
        tp_p = round(price * (1 - tp - buf), price_prec)
        try:
            r1 = client.new_order(symbol=symbol, side="SELL", type="LIMIT", quantity=qty, timeInForce="GTC", price=round(price, price_prec), recvWindow=cf.API_RECV_WINDOW)
            oid1 = r1.get("orderId")
            sleep(1)
            algo_sl = _place_algo_order(symbol, "BUY", "STOP_MARKET", qty, sl_p)
            if algo_sl is None:
                raise ClientError(None, None, "Failed to place SL algo order")
            sleep(1)
            algo_tp = _place_algo_order(symbol, "BUY", "TAKE_PROFIT_MARKET", qty, tp_p)
            if algo_tp is None:
                _cancel_algo_order(algo_sl)
                raise ClientError(None, None, "Failed to place TP algo order")
        except ClientError as err:
            if oid1 is not None:
                _cancel_order(symbol, oid1)
            _cancel_algo_order(algo_sl)
            _cancel_algo_order(algo_tp)
            code = getattr(err, "error_code", None)
            msg = getattr(err, "error_message", "")
            if code in (-2019, -1111, -4164) or "margin" in msg.lower() or "insufficient" in msg.lower():
                log.warning("open_order: margin/insufficient – bỏ qua: %s %s", code, msg)
                return False, None, None
            log.warning("open_order SELL error: %s %s", code, msg)
            return False, None, None

        sleep(12)
        _query = getattr(client, "get_order", None) or getattr(client, "query_order", None)
        if _query:
            try:
                o = _query(symbol=symbol, orderId=oid1, recvWindow=cf.API_RECV_WINDOW)
                if (o.get("status") or "").upper() != "FILLED":
                    log.warning("Lệnh vào chưa khớp – hủy entry + SL + TP")
                    _cancel_order(symbol, oid1)
                    _cancel_algo_order(algo_sl)
                    _cancel_algo_order(algo_tp)
                    return False, None, None
            except Exception as e:
                log.warning("get_order check error: %s", e)

        log.info("%s SELL OK, SL=%s TP=%s", symbol, sl_p, tp_p)
        return True, price, qty

    return False, None, None


def get_pos():
    try:
        resp = _api_retry(client.get_position_risk, recvWindow=cf.API_RECV_WINDOW)
        # Dedupe symbol để tránh đếm sai trong một số mode (hedge/BOTH)
        return list({e["symbol"] for e in resp if float(e.get("positionAmt") or 0) != 0})
    except ClientError as err:
        log.warning("get_pos error: %s %s", getattr(err, "error_code", ""), getattr(err, "error_message", ""))
        return []


def _get_positions_detail():
    """Trả về list position dict với positionAmt != 0."""
    try:
        resp = _api_retry(client.get_position_risk, recvWindow=cf.API_RECV_WINDOW)
        out = []
        for e in resp or []:
            try:
                amt = float(e.get("positionAmt") or 0)
            except Exception:
                amt = 0.0
            if amt != 0:
                out.append(e)
        return out
    except Exception:
        return []


def _trim_positions_to_max(max_positions: int):
    """
    Nếu đang có nhiều hơn max_positions, tự đóng bớt (reduceOnly MARKET).
    Mặc định chỉ chạy khi config.AUTO_TRIM_POSITIONS = True.
    """
    if not getattr(cf, "AUTO_TRIM_POSITIONS", False):
        return
    if max_positions <= 0:
        return

    pos = _get_positions_detail()
    if len(pos) <= max_positions:
        return

    # Chọn các vị thế nhỏ nhất để đóng trước (an toàn hơn).
    def _abs_amt(e):
        try:
            return abs(float(e.get("positionAmt") or 0))
        except Exception:
            return 0.0

    to_close = sorted(pos, key=_abs_amt)[: max(0, len(pos) - max_positions)]
    if not to_close:
        return

    for e in to_close:
        sym = e.get("symbol")
        try:
            amt = float(e.get("positionAmt") or 0)
        except Exception:
            continue
        if not sym or amt == 0:
            continue

        # Hủy open orders trước (tránh SL/TP còn treo)
        try:
            close_open_orders(sym)
        except Exception:
            pass

        side = "SELL" if amt > 0 else "BUY"  # đóng long -> SELL, đóng short -> BUY
        qty_prec = get_qty_precision(sym)
        qty = round(abs(amt), qty_prec)
        if qty <= 0:
            continue

        try:
            client.new_order(
                symbol=sym,
                side=side,
                type="MARKET",
                quantity=qty,
                reduceOnly=True,
                recvWindow=cf.API_RECV_WINDOW,
            )
            log.warning("AUTO_TRIM: Đã đóng bớt vị thế %s (%s %s) để về max=%s", sym, side, qty, max_positions)
        except Exception as ex:
            log.warning("AUTO_TRIM: Không đóng được %s: %s", sym, ex)


def check_orders():
    """Lấy danh sách symbol có open orders."""
    for method in ("get_open_orders", "get_orders"):
        fn = getattr(client, method, None)
        if not fn:
            continue
        try:
            # Thử không có symbol (lấy tất cả)
            resp = _api_retry(fn, recvWindow=cf.API_RECV_WINDOW)
            if resp:
                return list({e["symbol"] for e in (resp or [])})
        except TypeError:
            # Nếu cần symbol, lấy từ positions hiện có
            try:
                pos = get_pos()
                all_syms = set()
                for sym in pos:
                    try:
                        resp = _api_retry(fn, symbol=sym, recvWindow=cf.API_RECV_WINDOW)
                        if resp:
                            all_syms.add(sym)
                    except Exception:
                        pass
                return list(all_syms)
            except Exception:
                pass
        except Exception:
            continue
    log.warning("check_orders: không gọi được get_open_orders/get_orders")
    return []


def close_open_orders(symbol):
    try:
        client.cancel_open_orders(symbol=symbol, recvWindow=cf.API_RECV_WINDOW)
        log.info("Đã hủy open orders: %s", symbol)
    except ClientError as err:
        log.warning("close_open_orders error: %s %s", getattr(err, "error_code", ""), getattr(err, "error_message", ""))


# --- Chiến lược (dùng strategies.py) ---

def _strategy_signal(symbol):
    kl = klines(symbol)
    if kl is None or len(kl) < 50:
        return "none"
    
    # Lấy strategy name từ config
    strategy_name = getattr(cf, "STRATEGY", "multi")
    
    # Lấy strategy function - truyền client để hỗ trợ Bookmap
    sig_fn = get_strategy(strategy_name, client=client)
    
    # Gọi strategy - nếu là Bookmap thì truyền symbol
    if strategy_name in ['bookmap', 'bookmap_advanced']:
        return sig_fn(kl, symbol=symbol)
    else:
        return sig_fn(kl)



# --- Cập nhật và kiểm tra rủi ro ---

def _on_trade_closed(symbol: str, pnl: float, closed_at):
    """Gọi khi phát hiện lệnh đóng (SL/TP): ghi DB và gửi Telegram/Discord."""
    try:
        if getattr(cf, "ENABLE_DB", True):
            # closed_at nên là timestamp ms từ income API; nếu không có thì fallback "bây giờ"
            ts = int(closed_at or 0) or int(datetime.now(timezone.utc).timestamp() * 1000)
            db.record_trade_close(symbol, pnl, ts)
    except Exception as ex:
        log.warning("db.record_trade_close: %s", ex)
    try:
        notify.send("[BOT] Đóng lệnh {} PnL: {:.2f} USDT ({})".format(symbol, pnl, "TP" if pnl > 0 else "SL"))
    except Exception:
        pass


def _update_consecutive_losses_from_income(risk, on_trade_close=None):
    """
    Cập nhật consecutive_losses từ income REALIZED_PNL.
    - Ghi lại income events vào DB (bảng income) để debug/dashboard fallback.
    - Gọi on_trade_close(symbol, pnl, closed_at) cho các income mới.
    """

    def _safe_int(x, default=0):
        try:
            return int(x)
        except Exception:
            return default

    def _safe_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default

    fn = (
        getattr(client, "get_income", None)
        or getattr(client, "income", None)
        or getattr(client, "get_income_history", None)
    )
    if not fn:
        return

    # Lấy income, thử nhiều signature khác nhau để tránh lỗi silent.
    resp = None
    try:
        resp = _api_retry(fn, incomeType="REALIZED_PNL", limit=50, recvWindow=cf.API_RECV_WINDOW)
    except TypeError:
        try:
            resp = _api_retry(fn, incomeType="REALIZED_PNL", limit=50)
        except TypeError:
            try:
                resp = _api_retry(fn, limit=50)
            except Exception as ex:
                log.debug("get_income fallback failed: %s", ex)
                return
        except Exception as ex:
            log.debug("get_income failed: %s", ex)
            return
    except Exception as ex:
        log.debug("get_income failed: %s", ex)
        return

    if not isinstance(resp, list):
        return

    seen_list = risk.get("income_tran_ids_seen") or []
    if not isinstance(seen_list, list):
        seen_list = list(seen_list) if seen_list else []
    seen = set(str(x) for x in seen_list if x is not None)

    # Chuẩn hoá events
    events = []
    for e in resp:
        if not isinstance(e, dict):
            continue
        it = (e.get("incomeType") or "").upper()
        if it and it != "REALIZED_PNL":
            continue
        tid = e.get("tranId") or e.get("id")
        tid = str(tid) if tid is not None else None
        ts = _safe_int(e.get("time"), 0)
        sym = e.get("symbol")
        amt = _safe_float(e.get("income"), 0.0)
        if not tid:
            continue
        events.append({"tran_id": tid, "ts": ts, "symbol": sym, "income": amt, "income_type": it or "REALIZED_PNL"})

    # Ghi tất cả event mới theo thứ tự thời gian (cũ → mới)
    for ev in sorted(events, key=lambda x: (x["ts"], x["tran_id"])):
        if ev["tran_id"] in seen:
            continue
        seen.add(ev["tran_id"])
        seen_list.append(ev["tran_id"])
        try:
            if getattr(cf, "ENABLE_DB", True):
                db.record_income_event(ev["tran_id"], ev["symbol"], ev["income"], ev["ts"], ev["income_type"])
        except Exception as ex:
            log.debug("db.record_income_event: %s", ex)
        if on_trade_close and ev["symbol"]:
            try:
                on_trade_close(ev["symbol"], ev["income"], ev["ts"])
            except Exception as ex:
                log.warning("on_trade_close: %s", ex)

    # Tính consecutive losses từ chuỗi event mới nhất (mới → cũ)
    con = 0
    for ev in sorted(events, key=lambda x: (x["ts"], x["tran_id"]), reverse=True):
        if ev["income"] < 0:
            con += 1
        else:
            break

    risk["consecutive_losses"] = con
    risk["income_tran_ids_seen"] = seen_list


def _sync_closed_trades_from_account_trades(current_positions: list[str]):
    """
    Fallback (đặc biệt hữu ích trên TESTNET): đồng bộ lệnh đã đóng dựa trên userTrades.
    - Nếu 1 symbol có trade đang mở trong DB nhưng không còn trong positions → coi là đã đóng.
    - Tính pnl bằng cách cộng realizedPnl của userTrades từ thời điểm opened_at.
    """

    def _safe_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    pos_set = set(current_positions or [])

    try:
        open_rows = db.get_open_trades(limit=500)
    except Exception as ex:
        log.debug("db.get_open_trades: %s", ex)
        return

    fn_trades = getattr(client, "get_account_trades", None)
    if not fn_trades:
        return

    for _id, sym, opened_at in open_rows:
        if not sym:
            continue
        if sym in pos_set:
            continue

        opened_at = int(opened_at or 0)
        start_cutoff = max(0, opened_at - 60_000)  # buffer 60s
        try:
            trades = _api_retry(fn_trades, symbol=sym, limit=100, recvWindow=cf.API_RECV_WINDOW)
        except TypeError:
            try:
                trades = _api_retry(fn_trades, symbol=sym, limit=100)
            except Exception:
                continue
        except Exception:
            continue

        if not isinstance(trades, list):
            continue

        pnl = 0.0
        last_ts = 0
        for t in trades:
            if not isinstance(t, dict):
                continue
            ts = int(t.get("time") or 0)
            if ts < start_cutoff or ts > now_ms:
                continue
            rp = _safe_float(t.get("realizedPnl"), 0.0)
            pnl += rp
            if ts > last_ts:
                last_ts = ts

        # Nếu không lấy được timestamp thì vẫn đóng theo "bây giờ"
        closed_at = last_ts or now_ms
        try:
            if getattr(cf, "ENABLE_DB", True):
                db.record_trade_close(sym, pnl, closed_at, exit_reason="AUTO")
        except Exception as ex:
            log.debug("record_trade_close(%s): %s", sym, ex)


def update_and_check_risk(balance, on_trade_close=None):
    """
    Cập nhật peak, day_start, consecutive_losses.
    on_trade_close(symbol, pnl, closed_at) được gọi khi phát hiện lệnh đóng mới (SL/TP).
    Trả về (True, "lý do") nếu cần DỪNG BOT; (False, None) nếu tiếp tục.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = _load_risk_state()
    risk = raw if isinstance(raw, dict) else {}

    peak = float(risk.get("peak_balance") or 0)
    if balance > peak:
        peak = balance
    risk["peak_balance"] = peak

    day = risk.get("day")
    day_start = float(risk.get("day_start_balance") or balance)
    if day != today:
        risk["day"] = today
        risk["day_start_balance"] = balance
        day_start = balance
    risk["day_start_balance"] = day_start

    _update_consecutive_losses_from_income(risk, on_trade_close=on_trade_close)
    con = int(risk.get("consecutive_losses") or 0)

    _save_risk_state(risk)

    # 1) Drawdown
    if peak > 0:
        dd = (peak - balance) / peak * 100
        if dd >= cf.MAX_DRAWDOWN_PCT:
            return True, "DRAWDOWN {:.1f}% >= {}% – DỪNG BOT (chỉ mở lệnh mới khi khởi động lại)".format(dd, cf.MAX_DRAWDOWN_PCT)

    # 2) Lỗ trong ngày
    if day_start > 0:
        daily = (day_start - balance) / day_start * 100
        if daily >= cf.DAILY_LOSS_LIMIT_PCT:
            return True, "LỖ TRONG NGÀY {:.1f}% >= {}% – DỪNG BOT".format(daily, cf.DAILY_LOSS_LIMIT_PCT)

    # 3) Thua liên tiếp
    if con >= cf.MAX_CONSECUTIVE_LOSSES:
        return True, "THUA LIÊN TIẾP {} lệnh >= {} – DỪNG BOT".format(con, cf.MAX_CONSECUTIVE_LOSSES)

    return False, None


# --- Main loop ---

def main():
    if getattr(cf, "ENABLE_DB", True):
        try:
            db.init_db()
        except Exception as ex:
            log.warning("db.init_db: %s", ex)

    symbols = get_tickers_filtered()
    last_symbol = ""

    while True:
        # Kiểm tra lệnh dừng từ Zalo bot
        try:
            if os.path.isfile(BOT_COMMANDS_PATH):
                with open(BOT_COMMANDS_PATH, "r", encoding="utf-8") as f:
                    cmds = json.load(f)
                if cmds.get("stop"):
                    reason = cmds.get("stop_reason", "Lệnh từ Zalo")
                    log.error("DỪNG BOT (từ Zalo): %s", reason)
                    try:
                        notify.send("[BOT] DỪNG: {}".format(reason))
                    except Exception:
                        pass
                    # Xóa flag stop để lần sau có thể chạy lại
                    cmds["stop"] = False
                    with open(BOT_COMMANDS_PATH, "w", encoding="utf-8") as f:
                        json.dump(cmds, f, indent=2)
                    break
        except Exception as ex:
            log.debug("Đọc bot_commands: %s", ex)

        current_hour = datetime.now().hour
        if current_hour in (23, 0, 1):
            log.info("⏸️ Tạm dừng - khung giờ rủi ro cao")
            sleep(3600)  # Ngủ 1 tiếng
            continue

        avail, balance = _get_balance(use_available=True)
        if balance is None:
            log.warning("Không kết nối được API. Kiểm tra IP, giới hạn API hoặc chờ vài phút.")
            sleep(cf.RETRY_DELAY_SEC * 2)
            continue

        stop, reason = update_and_check_risk(balance, on_trade_close=_on_trade_closed)
        if stop:
            log.error("DỪNG BOT: %s", reason)
            try:
                notify.send("[BOT] DỪNG: {}".format(reason))
            except Exception:
                pass
            break

        log.info("Balance: %.2f USDT (khả dụng: %.2f)", balance, avail or 0)
        # Nếu tài khoản đã có sẵn quá nhiều vị thế, có thể auto-trim (tuỳ config)
        _trim_positions_to_max(cf.MAX_CONCURRENT_POSITIONS)
        pos = get_pos()
        # Đồng bộ lệnh đã đóng để dashboard có lịch sử (nhất là khi income API trống trên testnet)
        try:
            _sync_closed_trades_from_account_trades(pos)
        except Exception:
            pass

        if len(pos) > cf.MAX_CONCURRENT_POSITIONS:
            log.error(
                "VƯỢT MAX_CONCURRENT_POSITIONS: %s/%s. Bot sẽ KHÔNG mở thêm lệnh mới. "
                "Hãy đóng bớt vị thế hoặc bật config.AUTO_TRIM_POSITIONS=True.",
                len(pos),
                cf.MAX_CONCURRENT_POSITIONS,
            )
        if getattr(cf, "ENABLE_DB", True):
            try:
                db.record_status(balance, avail or 0, pos)
            except Exception:
                pass
        log.info("Số vị thế: %s/%s – %s", len(pos), cf.MAX_CONCURRENT_POSITIONS, pos)
        ord_syms = check_orders()
        for s in ord_syms:
            if s not in pos:
                close_open_orders(s)

        use_ok = (avail or 0) >= cf.MIN_FREE_BALANCE_USDT
        use_ok = use_ok and (avail or 0) * (1 - cf.MARGIN_BUFFER_PCT) >= cf.VOLUME_USDT
        if not use_ok:
            log.info("Bỏ qua mở lệnh mới: balance/đệm không đủ (khả dụng >= %s, dư >= %s%% sau %s USDT).",
                cf.MIN_FREE_BALANCE_USDT, cf.MARGIN_BUFFER_PCT * 100, cf.VOLUME_USDT)

        if len(pos) < cf.MAX_CONCURRENT_POSITIONS and use_ok:
            for elem in symbols:
                if elem in pos or elem in ord_syms or elem == last_symbol:
                    continue
                if elem == "USDCUSDT":
                    continue

                signal = _strategy_signal(elem)
                if signal not in ("up", "down"):
                    continue

                side = "buy" if signal == "up" else "sell"
                log.info("Tín hiệu %s: %s", "BUY" if signal == "up" else "SELL", elem)
                set_mode(elem, cf.MARGIN_TYPE)
                sleep(1)
                set_leverage(elem, cf.LEVERAGE)
                sleep(1)
                log.info("Đặt lệnh: %s %s", elem, signal)
                ok, entry_price, qty = open_order(elem, side)
                if ok and entry_price is not None and qty is not None:
                    try:
                        if getattr(cf, "ENABLE_DB", True):
                            db.record_trade_open(elem, side, entry_price, qty)
                    except Exception as ex:
                        log.warning("db.record_trade_open: %s", ex)
                    try:
                        notify.send("[BOT] Mở lệnh {} {} @ {:.4f} qty={}".format(side.upper(), elem, entry_price, qty))
                    except Exception:
                        pass
                    last_symbol = elem
                    pos = get_pos()
                    ord_syms = check_orders()
                    sleep(10)
                break

        log.info("Chờ %s giây (%s phút) rồi quét lại...", cf.SCAN_INTERVAL_SEC, cf.SCAN_INTERVAL_SEC // 60)
        sleep(cf.SCAN_INTERVAL_SEC)


if __name__ == "__main__":
    main()
