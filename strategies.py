# -*- coding: utf-8 -*-
"""
CHIẾN LƯỢC CẢI TIẾN - TĂNG WIN RATE
====================================
Thay thế file strategies.py hiện tại để cải thiện win rate

Vấn đề hiện tại:
- Win rate 28.1% (quá thấp)
- P/L ratio 1.57 (tốt) 
→ Chiến lược tạo quá nhiều tín hiệu sai

Giải pháp:
1. strict_multi: Chặt chẽ hơn, yêu cầu TẤT CẢ điều kiện
2. volume_profile: Dựa vào vùng hỗ trợ/kháng cự volume cao
3. Tăng bộ lọc thanh khoản
"""

import ta
import pandas as pd


# ============= CHIẾN LƯỢC GỐC (GIỮ LẠI ĐỂ TƯƠNG THÍCH) =============

def str_signal(kl: pd.DataFrame) -> str:
    """Đa chỉ báo: RSI + StochRSI + EMA 200. Tín hiệu mạnh, ít nhiễu."""
    if kl is None or len(kl) < 210:
        return "none"
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    rsi_k = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_k()
    rsi_d = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_d()
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if (rsi.iloc[-1] < 40 and ema.iloc[-1] < kl.Close.iloc[-1] and
        rsi_k.iloc[-1] < 20 and rsi_k.iloc[-3] < rsi_d.iloc[-3] and
        rsi_k.iloc[-2] < rsi_d.iloc[-2] and rsi_k.iloc[-1] > rsi_d.iloc[-1]):
        return "up"
    if (rsi.iloc[-1] > 60 and ema.iloc[-1] > kl.Close.iloc[-1] and
        rsi_k.iloc[-1] > 80 and rsi_k.iloc[-3] > rsi_d.iloc[-3] and
        rsi_k.iloc[-2] > rsi_d.iloc[-2] and rsi_k.iloc[-1] < rsi_d.iloc[-1]):
        return "down"
    return "none"


def rsi_signal(kl: pd.DataFrame) -> str:
    if kl is None or len(kl) < 50:
        return "none"
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    if rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30:
        return "up"
    if rsi.iloc[-2] > 70 and rsi.iloc[-1] < 70:
        return "down"
    return "none"


def macd_ema(kl: pd.DataFrame) -> str:
    if kl is None or len(kl) < 50:
        return "none"
    macd = ta.trend.macd_diff(kl.Close)
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if macd.iloc[-3] < 0 and macd.iloc[-2] < 0 and macd.iloc[-1] > 0 and ema.iloc[-1] < kl.Close.iloc[-1]:
        return "up"
    if macd.iloc[-3] > 0 and macd.iloc[-2] > 0 and macd.iloc[-1] < 0 and ema.iloc[-1] > kl.Close.iloc[-1]:
        return "down"
    return "none"


def ema200_50(kl: pd.DataFrame) -> str:
    if kl is None or len(kl) < 110:
        return "none"
    ema200 = ta.trend.ema_indicator(kl.Close, window=100)
    ema50 = ta.trend.ema_indicator(kl.Close, window=50)
    if ema50.iloc[-3] < ema200.iloc[-3] and ema50.iloc[-2] < ema200.iloc[-2] and ema50.iloc[-1] > ema200.iloc[-1]:
        return "up"
    if ema50.iloc[-3] > ema200.iloc[-3] and ema50.iloc[-2] > ema200.iloc[-2] and ema50.iloc[-1] < ema200.iloc[-1]:
        return "down"
    return "none"


# ============= CHIẾN LƯỢC CẢI TIẾN - TĂNG WIN RATE =============

def strict_multi_signal(kl: pd.DataFrame) -> str:
    """
    🎯 CHIẾN LƯỢC CHẶT CHẼ - TĂNG WIN RATE
    
    Yêu cầu TẤT CẢ điều kiện sau:
    1. RSI oversold/overbought rõ ràng (< 35 hoặc > 65)
    2. StochRSI xác nhận (đang quay đầu)
    3. MACD đổi chiều (cross 0)
    4. Giá theo trend chính (trên/dưới EMA200)
    5. EMA50 và EMA200 cùng chiều (xác nhận trend)
    6. Volume tăng đột biến (> 1.5x trung bình)
    
    → Ít tín hiệu nhưng chất lượng cao
    """
    if kl is None or len(kl) < 210:
        return "none"
    
    # 1. RSI - phải rõ ràng oversold/overbought
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    prev_rsi = rsi.iloc[-2]
    
    # 2. StochRSI - xác nhận momentum
    rsi_k = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_k()
    rsi_d = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_d()
    
    # 3. MACD - xác nhận trend
    macd = ta.trend.macd_diff(kl.Close)
    
    # 4. EMA 200 & 50 - chỉ trade theo trend chính
    ema200 = ta.trend.ema_indicator(kl.Close, window=200)
    ema50 = ta.trend.ema_indicator(kl.Close, window=50)
    
    # 5. Volume - phải có volume tăng đột biến
    volume_sma = kl.Volume.rolling(window=20).mean()
    current_volume = kl.Volume.iloc[-1]
    avg_volume = volume_sma.iloc[-1]
    volume_spike = current_volume > avg_volume * 1.5
    
    # === LONG (MUA) - Cực kỳ chặt chẽ ===
    long_conditions = [
        # RSI oversold rõ ràng (2 nến liên tiếp)
        current_rsi < 35 and prev_rsi < 35,
        # StochRSI đang ở dưới 25 và BẮT ĐẦU quay đầu lên
        rsi_k.iloc[-1] < 25,
        rsi_k.iloc[-1] > rsi_d.iloc[-1],
        rsi_k.iloc[-2] < rsi_d.iloc[-2],
        # MACD chuyển từ âm sang dương
        macd.iloc[-2] < 0,
        macd.iloc[-1] > 0,
        # Giá PHẢI trên EMA200 (trend tăng)
        kl.Close.iloc[-1] > ema200.iloc[-1],
        # EMA50 PHẢI trên EMA200 (xác nhận uptrend)
        ema50.iloc[-1] > ema200.iloc[-1],
        # Volume tăng ít nhất 50%
        volume_spike
    ]
    
    if all(long_conditions):
        return "up"
    
    # === SHORT (BÁN) - Cực kỳ chặt chẽ ===
    short_conditions = [
        # RSI overbought rõ ràng (2 nến liên tiếp)
        current_rsi > 65 and prev_rsi > 65,
        # StochRSI đang ở trên 75 và BẮT ĐẦU quay đầu xuống
        rsi_k.iloc[-1] > 75,
        rsi_k.iloc[-1] < rsi_d.iloc[-1],
        rsi_k.iloc[-2] > rsi_d.iloc[-2],
        # MACD chuyển từ dương sang âm
        macd.iloc[-2] > 0,
        macd.iloc[-1] < 0,
        # Giá PHẢI dưới EMA200 (trend giảm)
        kl.Close.iloc[-1] < ema200.iloc[-1],
        # EMA50 PHẢI dưới EMA200 (xác nhận downtrend)
        ema50.iloc[-1] < ema200.iloc[-1],
        # Volume tăng ít nhất 50%
        volume_spike
    ]
    
    if all(short_conditions):
        return "down"
    
    return "none"


def volume_profile_signal(kl: pd.DataFrame) -> str:
    """
    📊 CHIẾN LƯỢC VOLUME PROFILE
    
    Nguyên lý:
    - POC (Point of Control) = Giá có volume giao dịch cao nhất
    - POC thường là vùng hỗ trợ/kháng cự mạnh
    - Mua khi giá bounce từ POC + RSI oversold
    - Bán khi giá reject tại POC + RSI overbought
    
    → Tìm entry point tốt hơn
    """
    if kl is None or len(kl) < 100:
        return "none"
    
    # Phân tích 20 nến gần nhất
    lookback = 20
    recent_kl = kl.iloc[-lookback:]
    
    # Tìm giá có volume cao nhất (POC)
    price_bins = 20  # Chia giá thành 20 khoảng
    price_range = recent_kl.High.max() - recent_kl.Low.min()
    
    if price_range == 0:
        return "none"
    
    bin_size = price_range / price_bins
    
    # Tạo histogram volume theo giá
    volume_at_price = {}
    for idx, row in recent_kl.iterrows():
        # Tính bin cho giá đóng cửa
        price_bin = int((row.Close - recent_kl.Low.min()) / bin_size)
        price_bin = min(price_bin, price_bins - 1)  # Đảm bảo không vượt quá
        
        volume_at_price[price_bin] = volume_at_price.get(price_bin, 0) + row.Volume
    
    if not volume_at_price:
        return "none"
    
    # POC = bin có volume cao nhất
    poc_bin = max(volume_at_price, key=volume_at_price.get)
    poc_price = recent_kl.Low.min() + (poc_bin * bin_size) + (bin_size / 2)
    
    # Tính RSI
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    
    # Tính EMA200 để xác định trend
    ema200 = ta.trend.ema_indicator(kl.Close, window=200)
    
    current_price = kl.Close.iloc[-1]
    price_to_poc_pct = abs(current_price - poc_price) / current_price
    
    # LONG: Giá gần POC (trong vòng 1%) + RSI < 40 + Trên EMA200
    if (price_to_poc_pct < 0.01 and 
        current_rsi < 40 and 
        current_price > ema200.iloc[-1]):
        return "up"
    
    # SHORT: Giá gần POC (trong vòng 1%) + RSI > 60 + Dưới EMA200
    if (price_to_poc_pct < 0.01 and 
        current_rsi > 60 and 
        current_price < ema200.iloc[-1]):
        return "down"
    
    return "none"


def conservative_rsi_signal(kl: pd.DataFrame) -> str:
    """
    📉 RSI BẢO THỦ - CHỈ TRADE KHI CỰC RÕ RÀNG
    
    Khác với RSI thường:
    - Chỉ trade khi RSI < 25 (thay vì < 30)
    - Chỉ trade khi RSI > 75 (thay vì > 70)
    - Phải có xác nhận EMA200
    
    → Ít tín hiệu hơn nhưng chất lượng cao hơn
    """
    if kl is None or len(kl) < 210:
        return "none"
    
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    ema200 = ta.trend.ema_indicator(kl.Close, window=200)
    
    current_rsi = rsi.iloc[-1]
    prev_rsi = rsi.iloc[-2]
    
    # LONG: RSI cực oversold + trend tăng
    if (prev_rsi < 25 and 
        current_rsi > 25 and 
        current_rsi < 35 and
        kl.Close.iloc[-1] > ema200.iloc[-1]):
        return "up"
    
    # SHORT: RSI cực overbought + trend giảm
    if (prev_rsi > 75 and 
        current_rsi < 75 and 
        current_rsi > 65 and
        kl.Close.iloc[-1] < ema200.iloc[-1]):
        return "down"
    
    return "none"


# ============= BOOKMAP STRATEGIES (GIỮ NGUYÊN) =============

def get_order_book_signal(client, symbol):
    """Phân tích Order Book để tìm tín hiệu"""
    try:
        depth = client.depth(symbol=symbol, limit=20)
        
        bids = [(float(p), float(q)) for p, q in depth['bids']]
        asks = [(float(p), float(q)) for p, q in depth['asks']]
        
        top5_bid_vol = sum([q for _, q in bids[:5]])
        top5_ask_vol = sum([q for _, q in asks[:5]])
        
        total_bid_vol = sum([q for _, q in bids])
        total_ask_vol = sum([q for _, q in asks])
        
        avg_bid_vol = total_bid_vol / len(bids) if bids else 0
        avg_ask_vol = total_ask_vol / len(asks) if asks else 0
        
        has_support_wall = any(q > avg_bid_vol * 3 for _, q in bids[:5]) if avg_bid_vol > 0 else False
        has_resistance_wall = any(q > avg_ask_vol * 3 for _, q in asks[:5]) if avg_ask_vol > 0 else False
        
        imbalance_ratio = top5_bid_vol / top5_ask_vol if top5_ask_vol > 0 else 1.0
        
        if has_support_wall and imbalance_ratio > 1.5:
            return 'strong_support'
        if has_resistance_wall and imbalance_ratio < 0.7:
            return 'strong_resistance'
        if imbalance_ratio > 2.0:
            return 'imbalance_buy'
        if imbalance_ratio < 0.5:
            return 'imbalance_sell'
        
        return 'neutral'
        
    except Exception:
        return 'neutral'


def get_volume_delta(client, symbol, limit=50):
    """Tính Volume Delta từ recent trades"""
    try:
        trades = client.trades(symbol=symbol, limit=limit)
        
        buy_volume = 0
        sell_volume = 0
        
        for trade in trades:
            qty = float(trade['qty'])
            if trade['isBuyerMaker']:
                sell_volume += qty
            else:
                buy_volume += qty
        
        delta = buy_volume - sell_volume
        total = buy_volume + sell_volume
        
        if total == 0:
            return 'neutral'
        
        delta_pct = (delta / total) * 100
        
        if delta_pct > 20:
            return 'strong_buy'
        elif delta_pct < -20:
            return 'strong_sell'
        else:
            return 'neutral'
        
    except Exception:
        return 'neutral'


def bookmap_rsi_signal(kl: pd.DataFrame, client=None, symbol: str = None) -> str:
    """Kết hợp RSI + Order Book + Volume Delta"""
    if kl is None or len(kl) < 50:
        return "none"
    
    if client is None or symbol is None:
        return rsi_signal(kl)
    
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    
    ob_signal = get_order_book_signal(client, symbol)
    delta_signal = get_volume_delta(client, symbol)
    
    if current_rsi < 40:
        if ob_signal in ['strong_support', 'imbalance_buy']:
            if delta_signal in ['strong_buy', 'neutral']:
                return "up"
    
    if current_rsi > 60:
        if ob_signal in ['strong_resistance', 'imbalance_sell']:
            if delta_signal in ['strong_sell', 'neutral']:
                return "down"
    
    return "none"


def bookmap_advanced_signal(kl: pd.DataFrame, client=None, symbol: str = None) -> str:
    """Phiên bản nâng cao: RSI + EMA200 + Order Book + Volume Delta"""
    if kl is None or len(kl) < 210:
        return "none"
    
    if client is None or symbol is None:
        return str_signal(kl)
    
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    
    ema200 = ta.trend.ema_indicator(kl.Close, window=200)
    current_price = kl.Close.iloc[-1]
    above_ema = current_price > ema200.iloc[-1]
    
    ob_signal = get_order_book_signal(client, symbol)
    delta_signal = get_volume_delta(client, symbol)
    
    if above_ema and current_rsi < 40:
        if ob_signal in ['strong_support', 'imbalance_buy'] and \
           delta_signal in ['strong_buy', 'neutral']:
            return "up"
    
    if not above_ema and current_rsi > 60:
        if ob_signal in ['strong_resistance', 'imbalance_sell'] and \
           delta_signal in ['strong_sell', 'neutral']:
            return "down"
    
    return "none"


# ============= STRATEGY SELECTOR =============

def get_strategy(name: str, client=None):
    """
    Lấy strategy function
    
    Args:
        name: tên strategy
            - 'strict_multi': 🎯 KHUYẾN NGHỊ - Chặt chẽ nhất, win rate cao
            - 'volume_profile': Volume Profile
            - 'conservative_rsi': RSI bảo thủ
            - 'multi': Chiến lược gốc (không khuyến nghị)
            - 'rsi', 'macd', 'ema200_50': Các chiến lược cũ
            - 'bookmap', 'bookmap_advanced': Bookmap
        client: Binance client (cần cho bookmap strategies)
    
    Returns:
        Strategy function
    """
    strategies = {
        # === CHIẾN LƯỢC MỚI - TĂNG WIN RATE ===
        "strict_multi": strict_multi_signal,          # 🎯 KHUYẾN NGHỊ NHẤT
        "volume_profile": volume_profile_signal,       # Volume Profile
        "conservative_rsi": conservative_rsi_signal,   # RSI bảo thủ
        
        # === CHIẾN LƯỢC CŨ ===
        "multi": str_signal,
        "rsi": rsi_signal,
        "macd": macd_ema,
        "ema200_50": ema200_50,
        "bookmap": bookmap_rsi_signal,
        "bookmap_advanced": bookmap_advanced_signal,
    }
    
    strategy_fn = strategies.get(name, strict_multi_signal)  # Default: strict_multi
    
    # Nếu là bookmap strategy, wrap để tự động truyền client
    if name in ["bookmap", "bookmap_advanced"] and client is not None:
        def wrapped_strategy(kl, symbol=None):
            return strategy_fn(kl, client=client, symbol=symbol)
        return wrapped_strategy
    
    return strategy_fn


"""
===========================================
HƯỚNG DẪN SỬ DỤNG
===========================================

1. Thay thế file strategies.py cũ bằng file này
   cp strategies_improved.py strategies.py

2. Cập nhật config.py:
   STRATEGY = 'strict_multi'  # 🎯 Khuyến nghị nhất

3. Các tùy chọn khác:
   - 'volume_profile': Nếu muốn trade theo volume
   - 'conservative_rsi': Nếu muốn simple nhưng chặt

4. Tăng bộ lọc thanh khoản trong config.py:
   MIN_24H_VOLUME_USDT = 5_000_000  # Chỉ trade coin lớn
   SYMBOL_WHITELIST = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

5. Test lại trên testnet 1-2 tuần

KỲ VỌNG:
- Win rate: 45-55% (tăng từ 28%)
- Số lệnh/ngày: Giảm (5-8 lệnh thay vì 10-15)
- Chất lượng lệnh: Tăng đáng kể

LƯU Ý:
- strict_multi yêu cầu TẤT CẢ điều kiện → Ít tín hiệu
- Nếu quá ít tín hiệu, thử volume_profile hoặc conservative_rsi
- Luôn backtest trước khi chạy thật!
"""
