# -*- coding: utf-8 -*-
"""
Chiến lược giao dịch – nhận DataFrame klines (O,H,L,C,V).
Dùng chung cho main1 (live) và backtest.

PHIÊN BẢN MỚI: Thêm Bookmap strategies
"""

import ta
import pandas as pd


# ============= STRATEGIES GỐC =============

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


# ============= BOOKMAP STRATEGIES =============

def get_order_book_signal(client, symbol):
    """
    Phân tích Order Book để tìm tín hiệu
    """
    try:
        depth = client.depth(symbol=symbol, limit=20)
        
        bids = [(float(p), float(q)) for p, q in depth['bids']]
        asks = [(float(p), float(q)) for p, q in depth['asks']]
        
        # Tính tổng volume 5 mức giá đầu
        top5_bid_vol = sum([q for _, q in bids[:5]])
        top5_ask_vol = sum([q for _, q in asks[:5]])
        
        # Tính tổng volume tất cả
        total_bid_vol = sum([q for _, q in bids])
        total_ask_vol = sum([q for _, q in asks])
        
        # Tìm "tường thanh khoản"
        avg_bid_vol = total_bid_vol / len(bids) if bids else 0
        avg_ask_vol = total_ask_vol / len(asks) if asks else 0
        
        has_support_wall = any(q > avg_bid_vol * 3 for _, q in bids[:5]) if avg_bid_vol > 0 else False
        has_resistance_wall = any(q > avg_ask_vol * 3 for _, q in asks[:5]) if avg_ask_vol > 0 else False
        
        # Tỷ lệ imbalance
        imbalance_ratio = top5_bid_vol / top5_ask_vol if top5_ask_vol > 0 else 1.0
        
        # Phân tích
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
    """
    Tính Volume Delta từ recent trades
    """
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
    """
    Kết hợp RSI + Order Book + Volume Delta
    
    QUAN TRỌNG: Cần truyền client và symbol từ main1.py
    """
    if kl is None or len(kl) < 50:
        return "none"
    
    if client is None or symbol is None:
        # Fallback về RSI thuần nếu không có client
        return rsi_signal(kl)
    
    # 1. RSI
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    
    # 2. Order Book
    ob_signal = get_order_book_signal(client, symbol)
    
    # 3. Volume Delta
    delta_signal = get_volume_delta(client, symbol)
    
    # LOGIC MUA
    if current_rsi < 40:
        if ob_signal in ['strong_support', 'imbalance_buy']:
            if delta_signal in ['strong_buy', 'neutral']:
                return "up"
    
    # LOGIC BÁN
    if current_rsi > 60:
        if ob_signal in ['strong_resistance', 'imbalance_sell']:
            if delta_signal in ['strong_sell', 'neutral']:
                return "down"
    
    return "none"


def bookmap_advanced_signal(kl: pd.DataFrame, client=None, symbol: str = None) -> str:
    """
    Phiên bản nâng cao: RSI + EMA200 + Order Book + Volume Delta
    """
    if kl is None or len(kl) < 210:
        return "none"
    
    if client is None or symbol is None:
        return str_signal(kl)
    
    # 1. RSI
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    current_rsi = rsi.iloc[-1]
    
    # 2. EMA 200
    ema200 = ta.trend.ema_indicator(kl.Close, window=200)
    current_price = kl.Close.iloc[-1]
    above_ema = current_price > ema200.iloc[-1]
    
    # 3. Order Book
    ob_signal = get_order_book_signal(client, symbol)
    
    # 4. Volume Delta
    delta_signal = get_volume_delta(client, symbol)
    
    # LOGIC MUA (chỉ khi trên EMA200)
    if above_ema and current_rsi < 40:
        if ob_signal in ['strong_support', 'imbalance_buy'] and \
           delta_signal in ['strong_buy', 'neutral']:
            return "up"
    
    # LOGIC BÁN (chỉ khi dưới EMA200)
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
        name: tên strategy ('multi', 'rsi', 'macd', 'bookmap', 'bookmap_advanced')
        client: Binance client (cần cho bookmap strategies)
    
    Returns:
        Strategy function
    """
    strategies = {
        "multi": str_signal,
        "rsi": rsi_signal,
        "macd": macd_ema,
        "ema200_50": ema200_50,
        "bookmap": bookmap_rsi_signal,
        "bookmap_advanced": bookmap_advanced_signal,
    }
    
    strategy_fn = strategies.get(name, str_signal)
    
    # Nếu là bookmap strategy, wrap để tự động truyền client
    if name in ["bookmap", "bookmap_advanced"] and client is not None:
        def wrapped_strategy(kl, symbol=None):
            return strategy_fn(kl, client=client, symbol=symbol)
        return wrapped_strategy
    
    return strategy_fn
