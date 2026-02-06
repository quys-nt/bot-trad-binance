# -*- coding: utf-8 -*-
"""
DASHBOARD - Đóng lệnh thủ công, PnL realtime
Chạy: streamlit run dashboard/app.py (từ thư mục gốc)
"""

import os
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

try:
    import config as cf
    DB_PATH = getattr(cf, "DB_PATH", "trades.db")
    TESTNET = getattr(cf, "TESTNET", False)
    VOLUME_USDT = getattr(cf, "VOLUME_USDT", 8.0)
    LEVERAGE = getattr(cf, "LEVERAGE", 2)
    MAX_DRAWDOWN = getattr(cf, "MAX_DRAWDOWN_PCT", 8.0)
    DAILY_LOSS_LIMIT = getattr(cf, "DAILY_LOSS_LIMIT_PCT", 4.0)
    TAKE_PROFIT_PCT = getattr(cf, "TAKE_PROFIT_PCT", 0.02)
    STOP_LOSS_PCT = getattr(cf, "STOP_LOSS_PCT", 0.025)
except Exception:
    class _Cf:
        MAX_CONCURRENT_POSITIONS = 5
        MIN_FREE_BALANCE_USDT = 30.0
    cf = _Cf()
    DB_PATH = str(ROOT / "trades.db")
    TESTNET = True
    VOLUME_USDT = 8.0
    LEVERAGE = 2
    MAX_DRAWDOWN = 8.0
    DAILY_LOSS_LIMIT = 4.0
    TAKE_PROFIT_PCT = 0.02
    STOP_LOSS_PCT = 0.025

import db as _db
_db.init_db()

# Binance API client
try:
    from binance.um_futures import UMFutures
    from keys_loader import get_api_credentials
    
    api_key, api_secret = get_api_credentials()
    base_url = "https://testnet.binancefuture.com" if TESTNET else None
    binance_client = UMFutures(key=api_key, secret=api_secret, base_url=base_url)
except Exception as e:
    binance_client = None
    st.warning(f"⚠️ Không kết nối được Binance API: {e}")


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def get_current_price(symbol):
    """Lấy giá hiện tại từ Binance"""
    if not binance_client:
        return None
    try:
        ticker = binance_client.ticker_price(symbol)
        return float(ticker['price'])
    except Exception as e:
        st.error(f"Lỗi lấy giá {symbol}: {e}")
        return None


def calculate_pnl(entry_price, current_price, qty, side):
    """Tính PnL dựa vào giá hiện tại"""
    if side.lower() == "buy":
        # Long: profit = (current - entry) * qty
        pnl = (current_price - entry_price) * qty
    else:
        # Short: profit = (entry - current) * qty
        pnl = (entry_price - current_price) * qty
    return pnl


def get_binance_open_positions():
    """Lấy danh sách position đang mở từ Binance API."""
    if not binance_client:
        return []
    try:
        positions = binance_client.get_position_risk(recvWindow=8000)
        out = []
        for p in positions:
            amt = float(p.get("positionAmt", 0) or 0)
            if amt == 0:
                continue
            entry = float(p.get("entryPrice", 0) or 0)
            mark = float(p.get("markPrice", 0) or 0)
            upnl = float(p.get("unRealizedProfit", 0) or 0)
            out.append({
                "symbol": p.get("symbol", ""),
                "positionAmt": amt,
                "entryPrice": entry,
                "markPrice": mark,
                "unRealizedProfit": upnl,
                "side": "buy" if amt > 0 else "sell",
                "qty": abs(amt),
            })
        return out
    except Exception as e:
        st.error(f"Lỗi lấy position từ Binance: {e}")
        return []


def close_position_manual(symbol):
    """Đóng lệnh thủ công"""
    if not binance_client:
        st.error("❌ Không kết nối được Binance API!")
        return False
    
    try:
        # 1. Hủy tất cả open orders của symbol (bao gồm SL/TP)
        try:
            binance_client.cancel_open_orders(symbol=symbol, recvWindow=8000)
        except Exception as e:
            # Bỏ qua lỗi nếu không có open orders
            pass
        
        # 2. Lấy thông tin position hiện tại
        positions = binance_client.get_position_risk(recvWindow=8000)
        position = None
        for p in positions:
            if p['symbol'] == symbol and float(p['positionAmt']) != 0:
                position = p
                break
        
        if not position:
            st.warning(f"⚠️ Không tìm thấy position {symbol}")
            return False
        
        # 3. Đóng position bằng market order với reduceOnly=True
        pos_amt = float(position['positionAmt'])
        side = "SELL" if pos_amt > 0 else "BUY"  # Đảo ngược để đóng
        qty = abs(pos_amt)
        
        # ✅ FIX: Thêm reduceOnly=True để tránh lỗi -4164 (notional < 5)
        result = binance_client.new_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
            reduceOnly=True,  # ← Quan trọng! Cho phép đóng position nhỏ
            recvWindow=8000
        )
        
        st.success(f"✅ Đã đóng lệnh {symbol} thành công!")
        return True
        
    except Exception as e:
        st.error(f"❌ Lỗi đóng lệnh: {e}")
        return False


def get_trades(limit=500):
    if not os.path.isfile(DB_PATH):
        return []
    c = _conn()
    r = c.execute(
        """SELECT symbol, side, entry_price, qty, exit_price, pnl, exit_reason, 
           opened_at, closed_at FROM trades ORDER BY opened_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    c.close()
    return r


def get_open_positions():
    trades = get_trades(100)
    return [t for t in trades if t[8] is None]


def get_closed_trades(days=None):
    if not os.path.isfile(DB_PATH):
        return []
    c = _conn()
    
    if days:
        cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        r = c.execute(
            """SELECT symbol, side, entry_price, qty, exit_price, pnl, exit_reason, 
               opened_at, closed_at FROM trades 
               WHERE closed_at IS NOT NULL AND closed_at >= ?
               ORDER BY closed_at DESC""",
            (cutoff,),
        ).fetchall()
    else:
        r = c.execute(
            """SELECT symbol, side, entry_price, qty, exit_price, pnl, exit_reason, 
               opened_at, closed_at FROM trades 
               WHERE closed_at IS NOT NULL
               ORDER BY closed_at DESC""",
        ).fetchall()
    
    c.close()
    return r


def get_latest_status():
    if not os.path.isfile(DB_PATH):
        return None
    c = _conn()
    r = c.execute(
        "SELECT ts, balance, available, positions_json FROM status ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    c.close()
    return r


def get_simple_stats(closed_trades):
    """Tính thống kê đơn giản"""
    if not closed_trades:
        return None
    
    wins = [t for t in closed_trades if (t[5] or 0) > 0]
    losses = [t for t in closed_trades if (t[5] or 0) <= 0]
    
    total_pnl = sum(t[5] or 0 for t in closed_trades)
    win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
    
    avg_win = sum(t[5] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t[5] for t in losses) / len(losses) if losses else 0
    
    return {
        'total_trades': len(closed_trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
    }


def show_health_score(stats, balance):
    """Hiển thị điểm sức khỏe bot (0-100)"""
    if not stats or not balance:
        return
    
    score = 0
    
    # Win rate (40 điểm)
    if stats['win_rate'] >= 60:
        score += 40
    elif stats['win_rate'] >= 55:
        score += 30
    elif stats['win_rate'] >= 50:
        score += 20
    else:
        score += 10
    
    # PnL positive (30 điểm)
    if stats['total_pnl'] > 0:
        score += 30
    elif stats['total_pnl'] > -5:
        score += 15
    
    # Avg win > Avg loss (30 điểm)
    if abs(stats['avg_win']) > abs(stats['avg_loss']):
        ratio = abs(stats['avg_win']) / abs(stats['avg_loss']) if stats['avg_loss'] != 0 else 1
        if ratio >= 1.5:
            score += 30
        elif ratio >= 1.2:
            score += 20
        else:
            score += 10
    
    # Hiển thị
    st.markdown("### 🏥 Sức khỏe Bot")
    
    if score >= 80:
        st.success(f"**{score}/100** - Xuất sắc! Bot đang hoạt động rất tốt.")
    elif score >= 60:
        st.info(f"**{score}/100** - Tốt. Bot đang hoạt động ổn định.")
    elif score >= 40:
        st.warning(f"**{score}/100** - Trung bình. Cần theo dõi và điều chỉnh.")
    else:
        st.error(f"**{score}/100** - Yếu. Cần xem xét lại chiến lược!")
    
    st.progress(score / 100)
    st.markdown("---")


def show_simple_explanation():
    """Hướng dẫn đọc dashboard"""
    with st.expander("📖 Hướng dẫn đọc Dashboard", expanded=False):
        st.markdown("""
        ### Các khái niệm cơ bản:
        
        **1. Balance (Số dư)**
        - Tổng số tiền trong tài khoản
        
        **2. Khả dụng**
        - Số tiền có thể dùng để mở lệnh mới
        
        **3. PnL Ước tính (Realtime)**
        - Lãi/lỗ hiện tại dựa vào giá thị trường
        - **Màu xanh:** Đang lãi
        - **Màu đỏ:** Đang lỗ
        
        **4. Đóng lệnh thủ công**
        - Click "🔴 Đóng lệnh" để đóng trước TP/SL
        - Hệ thống sẽ hiển thị PnL ước tính
        - Xác nhận để thực hiện đóng lệnh
        
        **Lưu ý:**
        - PnL ước tính có thể thay đổi theo giá thị trường
        - Phí giao dịch (~0.04%) chưa bao gồm trong PnL ước tính
        """)


def main():
    st.set_page_config(
        page_title="Bot Trading - Dashboard V4",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🤖 Bot Trading Dashboard V4")
    st.caption("Phiên bản nâng cao - Đóng lệnh thủ công")
    st.markdown("---")
    
    # Hướng dẫn
    show_simple_explanation()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Thông tin Bot")
        
        # Mode
        if TESTNET:
            st.warning("🟡 **TESTNET** (Tiền ảo)")
        else:
            st.error("🔴 **MAINNET** (Tiền thật!)")
        
        st.markdown("---")
        
        # Config
        st.subheader("📋 Cấu hình")
        st.info(f"""
        - Tiền mỗi lệnh: **{VOLUME_USDT} USDT**
        - Đòn bẩy: **x{LEVERAGE}**
        - Chốt lãi: **+{TAKE_PROFIT_PCT*100}%**
        - Cắt lỗ: **-{STOP_LOSS_PCT*100}%**
        """)
        
        st.markdown("---")
        
        # Time filter
        st.subheader("🕐 Xem dữ liệu")
        time_filter = st.selectbox(
            "Chọn khoảng thời gian",
            ["Hôm nay", "7 ngày qua", "30 ngày qua", "Tất cả"]
        )
        
        st.markdown("---")
        
        # Auto refresh
        auto_refresh = st.checkbox("♻️ Tự động làm mới (30s)", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # Manual refresh
        if st.button("🔄 Làm mới ngay"):
            st.rerun()
    
    # Check database
    if not os.path.isfile(DB_PATH):
        st.error("❌ Chưa có dữ liệu. Vui lòng chạy bot trước!")
        return
    
    # Get data
    status = get_latest_status()
    open_positions = get_open_positions()
    binance_positions = get_binance_open_positions()
    db_symbols = {t[0] for t in open_positions}
    binance_only_positions = [p for p in binance_positions if p["symbol"] not in db_symbols]

    # Ẩn các kênh đã đóng thủ công trong phiên (chỉ áp dụng lệnh "chỉ trên Binance")
    if "hidden_after_close" not in st.session_state:
        st.session_state["hidden_after_close"] = set()
    binance_only_display = [p for p in binance_only_positions if p["symbol"] not in st.session_state["hidden_after_close"]]
    open_positions_display = [t for t in open_positions if t[0] not in st.session_state["hidden_after_close"]]

    # Filter trades
    if time_filter == "Hôm nay":
        closed_trades = get_closed_trades(1)
    elif time_filter == "7 ngày qua":
        closed_trades = get_closed_trades(7)
    elif time_filter == "30 ngày qua":
        closed_trades = get_closed_trades(30)
    else:
        closed_trades = get_closed_trades()
    
    # === PHẦN 1: TỔNG QUAN ===
    st.header("💰 Tổng quan tài khoản")
    
    if status:
        ts, balance, available, pos_json = status
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💵 Tổng số dư", f"{balance:.2f} USDT")
        
        with col2:
            st.metric("✅ Tiền có thể dùng", f"{available:.2f} USDT")
        
        with col3:
            positions = json.loads(pos_json or "[]")
            st.metric("📊 Lệnh đang mở", f"{len(positions)}/{cf.MAX_CONCURRENT_POSITIONS}")
        
        # Cảnh báo
        if available < cf.MIN_FREE_BALANCE_USDT:
            st.warning(f"⚠️ Tiền khả dụng thấp ({available:.2f} USDT)")
    
    st.markdown("---")
    
    # === PHẦN 2: SỨC KHỎE BOT ===
    if closed_trades:
        stats = get_simple_stats(closed_trades)
        show_health_score(stats, status[1] if status else None)
    
    # === PHẦN 3: KẾT QUẢ GIAO DỊCH ===
    st.header("📈 Kết quả giao dịch")
    
    if closed_trades:
        stats = get_simple_stats(closed_trades)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Tổng số lệnh", stats['total_trades'])
        
        with col2:
            st.metric("🏆 Tỷ lệ thắng", f"{stats['win_rate']:.1f}%")
        
        with col3:
            st.metric("💵 Tổng lãi/lỗ", f"{stats['total_pnl']:+.2f} USDT")
        
        with col4:
            st.metric("✅ Thắng", stats['wins'])
            st.metric("❌ Thua", stats['losses'])
    
    st.markdown("---")
    
    # === PHẦN 4: LỆNH ĐANG MỞ - VỚI TÍNH NĂNG ĐÓNG THỦ CÔNG ===
    st.header("🔓 Lệnh đang mở (Có thể đóng thủ công)")
    
    if open_positions_display:
        st.info(f"Có **{len(open_positions_display)}** lệnh đang chờ (từ trades.db). Bạn có thể đóng thủ công nếu thấy thị trường không còn biến động.")
        
        for idx, t in enumerate(open_positions_display):
            sym, side, entry, qty, _, _, _, opened_at, _ = t
            opened_str = datetime.fromtimestamp(opened_at / 1000).strftime("%Y-%m-%d %H:%M") if opened_at else "-"
            
            # Lấy giá hiện tại
            current_price = get_current_price(sym)
            
            # Tính PnL ước tính
            if current_price:
                estimated_pnl = calculate_pnl(entry, current_price, qty, side)
                pnl_pct = (estimated_pnl / (entry * qty)) * 100
            else:
                estimated_pnl = None
                pnl_pct = None
            
            # Hiển thị
            with st.expander(f"💼 {sym} - {side.upper()} @ {entry:.6f} (Mở: {opened_str})", expanded=True):
                
                # Thông tin cơ bản
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📍 Giá vào", f"{entry:.6f}")
                
                with col2:
                    st.metric("📊 Số lượng", f"{qty}")
                
                with col3:
                    if current_price:
                        st.metric("💹 Giá hiện tại", f"{current_price:.6f}")
                    else:
                        st.metric("💹 Giá hiện tại", "Đang tải...")
                
                with col4:
                    if estimated_pnl is not None:
                        if estimated_pnl >= 0:
                            st.success(f"**PnL ước tính:**\n+{estimated_pnl:.3f} USDT ({pnl_pct:+.2f}%)")
                        else:
                            st.error(f"**PnL ước tính:**\n{estimated_pnl:.3f} USDT ({pnl_pct:+.2f}%)")
                    else:
                        st.info("**PnL ước tính:**\nĐang tải...")
                
                # Mục tiêu SL/TP
                st.markdown("---")
                col_sl, col_tp = st.columns(2)
                
                if side.lower() == "buy":
                    tp_price = entry * (1 + TAKE_PROFIT_PCT)
                    sl_price = entry * (1 - STOP_LOSS_PCT)
                else:
                    tp_price = entry * (1 - TAKE_PROFIT_PCT)
                    sl_price = entry * (1 + STOP_LOSS_PCT)
                
                with col_sl:
                    st.warning(f"🛑 **Stop Loss:** {sl_price:.6f} (-{STOP_LOSS_PCT*100}%)")
                
                with col_tp:
                    st.success(f"🎯 **Take Profit:** {tp_price:.6f} (+{TAKE_PROFIT_PCT*100}%)")
                
                # Nút đóng lệnh
                st.markdown("---")
                
                # Modal xác nhận
                modal_key = f"modal_{sym}_{idx}"
                close_key = f"close_{sym}_{idx}"
                confirm_key = f"confirm_{sym}_{idx}"
                cancel_key = f"cancel_{sym}_{idx}"
                
                # Hiển thị modal nếu đã click "Đóng lệnh"
                if modal_key not in st.session_state:
                    st.session_state[modal_key] = False
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    if st.button(f"🔴 Đóng lệnh", key=close_key, type="primary"):
                        st.session_state[modal_key] = True
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"📊 Xem chart", key=f"chart_{sym}_{idx}"):
                        chart_url = f"https://{'demo.' if TESTNET else ''}binance.com/en/futures/{sym}"
                        st.info(f"Mở chart: {chart_url}")
                        # JavaScript để mở tab mới (không hoạt động trong Streamlit, chỉ hiển thị link)
                        st.markdown(f"[👉 Mở chart trong tab mới]({chart_url})")
                
                # Modal xác nhận
                if st.session_state.get(modal_key, False):
                    st.warning("### ⚠️ XÁC NHẬN ĐÓNG LỆNH")
                    
                    if estimated_pnl is not None:
                        st.markdown(f"""
                        **Symbol:** {sym}
                        
                        **Thông tin lệnh:**
                        - Hướng: **{side.upper()}**
                        - Giá vào: **{entry:.6f}**
                        - Giá hiện tại: **{current_price:.6f}**
                        - Số lượng: **{qty}**
                        
                        **Nếu đóng ngay:**
                        """)
                        
                        if estimated_pnl >= 0:
                            st.success(f"""
                            ✅ **LÃI:** +{estimated_pnl:.3f} USDT ({pnl_pct:+.2f}%)
                            
                            (Chưa bao gồm phí giao dịch ~{estimated_pnl * 0.0004:.4f} USDT)
                            """)
                        else:
                            st.error(f"""
                            ❌ **LỖ:** {estimated_pnl:.3f} USDT ({pnl_pct:+.2f}%)
                            
                            (Chưa bao gồm phí giao dịch ~{abs(estimated_pnl) * 0.0004:.4f} USDT)
                            """)
                        
                        st.info(f"""
                        **So sánh với mục tiêu:**
                        - 🎯 TP ({tp_price:.6f}): Lãi {(qty * (tp_price - entry if side.lower() == 'buy' else entry - tp_price)):.3f} USDT
                        - 🛑 SL ({sl_price:.6f}): Lỗ {(qty * (sl_price - entry if side.lower() == 'buy' else entry - sl_price)):.3f} USDT
                        """)
                    else:
                        st.warning("⚠️ Không lấy được giá hiện tại. Vui lòng thử lại.")
                    
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ XÁC NHẬN ĐÓNG", key=confirm_key, type="primary"):
                            with st.spinner("Đang đóng lệnh..."):
                                success = close_position_manual(sym)
                                if success:
                                    _db.record_trade_close(sym, estimated_pnl or 0, int(time.time() * 1000), "manual")
                                    st.session_state["hidden_after_close"].add(sym)
                                    st.session_state[modal_key] = False
                                    time.sleep(1)
                                    st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ HỦY", key=cancel_key):
                            st.session_state[modal_key] = False
                            st.rerun()
    else:
        st.success("✅ Không có lệnh đang mở (từ trades.db). Bot sẽ tìm cơ hội mới.")

    # === LỆNH CHỈ TRÊN BINANCE (KHÔNG TRONG TRADES.DB) ===
    st.subheader("📌 Lệnh mở trên Binance (không trong trades.db)")
    if binance_only_display:
        st.warning(f"Có **{len(binance_only_display)}** lệnh đang mở trên Binance nhưng không có trong trades.db (ví dụ mở tay hoặc từ bot khác). Bạn có thể đóng thủ công và lệnh sẽ được ẩn sau khi đóng.")
        for idx, p in enumerate(binance_only_display):
            sym = p["symbol"]
            side = p["side"]
            entry = p["entryPrice"]
            qty = p["qty"]
            mark_price = p["markPrice"]
            upnl = p["unRealizedProfit"]
            pnl_pct = (upnl / (entry * qty)) * 100 if entry and qty else 0

            bo_modal_key = f"bo_modal_{sym}_{idx}"
            bo_close_key = f"bo_close_{sym}_{idx}"
            bo_confirm_key = f"bo_confirm_{sym}_{idx}"
            bo_cancel_key = f"bo_cancel_{sym}_{idx}"

            if bo_modal_key not in st.session_state:
                st.session_state[bo_modal_key] = False

            with st.expander(f"📌 {sym} - {side.upper()} @ {entry:.6f} (chỉ trên Binance)", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📍 Giá vào", f"{entry:.6f}")
                with col2:
                    st.metric("📊 Số lượng", f"{qty}")
                with col3:
                    st.metric("💹 Mark price", f"{mark_price:.6f}")
                with col4:
                    if upnl >= 0:
                        st.success(f"**PnL ước tính:** +{upnl:.3f} USDT ({pnl_pct:+.2f}%)")
                    else:
                        st.error(f"**PnL ước tính:** {upnl:.3f} USDT ({pnl_pct:+.2f}%)")

                st.markdown("---")
                if st.button(f"🔴 Đóng lệnh", key=bo_close_key, type="primary"):
                    st.session_state[bo_modal_key] = True
                    st.rerun()

                if st.session_state.get(bo_modal_key, False):
                    st.warning("### ⚠️ XÁC NHẬN ĐÓNG LỆNH (chỉ trên Binance)")
                    st.markdown(f"**Symbol:** {sym} | **PnL ước tính:** {upnl:+.3f} USDT")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ XÁC NHẬN ĐÓNG", key=bo_confirm_key, type="primary"):
                            with st.spinner("Đang đóng lệnh..."):
                                if close_position_manual(sym):
                                    st.session_state["hidden_after_close"].add(sym)
                                    st.session_state[bo_modal_key] = False
                                    time.sleep(1)
                                    st.rerun()
                    with col_b:
                        if st.button("❌ HỦY", key=bo_cancel_key):
                            st.session_state[bo_modal_key] = False
                            st.rerun()
    else:
        st.success("✅ Không có lệnh nào chỉ mở trên Binance (ngoài trades.db).")

    if st.session_state.get("hidden_after_close"):
        if st.button("🔄 Hiện lại các lệnh đã ẩn trong phiên"):
            st.session_state["hidden_after_close"] = set()
            st.rerun()

    st.markdown("---")
    
    # === PHẦN 5: LỊCH SỬ ===
    st.header("📜 Lịch sử 10 lệnh gần nhất")
    
    if closed_trades:
        recent = closed_trades[:10]
        
        for t in recent:
            sym, side, entry, qty, exit_p, pnl, reason, opened, closed = t
            
            opened_str = datetime.fromtimestamp(opened / 1000).strftime("%Y-%m-%d %H:%M") if opened else "-"
            closed_str = datetime.fromtimestamp(closed / 1000).strftime("%Y-%m-%d %H:%M") if closed else "-"
            
            icon = "✅" if pnl and pnl > 0 else "❌"
            
            with st.expander(f"{icon} {sym} - {side.upper()} - PnL: {pnl:.3f} USDT", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Vào:** {opened_str}")
                    st.write(f"**Giá vào:** {entry:.6f}")
                
                with col2:
                    st.write(f"**Ra:** {closed_str}")
                    st.write(f"**Giá ra:** {exit_p:.6f}" if exit_p else "-")
                
                with col3:
                    if pnl and pnl > 0:
                        st.success(f"**Lãi:** +{pnl:.3f} USDT")
                    else:
                        st.error(f"**Lỗ:** {pnl:.3f} USDT")
                    st.write(f"**Lý do:** {reason or '-'}")
    else:
        st.info("ℹ️ Chưa có lịch sử lệnh.")
    
    st.markdown("---")
    
    # Footer
    st.caption(f"""
    Dashboard V4 - Đóng lệnh thủ công | 
    Database: {DB_PATH} | 
    Chế độ: {'TESTNET' if TESTNET else 'MAINNET'} |
    Cập nhật: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)


if __name__ == "__main__":
    main()