# -*- coding: utf-8 -*-
"""
CẤU HÌNH BOT TRADING - TỐI ƯU WIN RATE
==========================================
Mục tiêu: Win Rate ≥55% (hiện tại: 28%)
Vốn khuyến nghị: 150-300 USDT
Chiến lược: Chỉ trade coin TOP, filter chặt

THAY ĐỔI CHÍNH:
✅ Tăng MIN_24H_VOLUME: 3M → 10M (chỉ trade coin lớn)
✅ Dùng SYMBOL_WHITELIST: Chỉ BTC, ETH, BNB, SOL, XRP (proven coins)
✅ Đổi STRATEGY: rsi → multi (filter chặt hơn)
✅ Giảm MAX_POSITIONS: 5 → 3 (tập trung quality hơn quantity)
✅ Tăng SL/TP ratio: Cải thiện risk/reward
"""

# --- RỦI RO TÀI CHÍNH ---
LEVERAGE = 2                    # Đòn bẩy x2 (an toàn)
MAX_CONCURRENT_POSITIONS = 3    # ✅✅ Giảm xuống 3 (từ 5) - Tập trung chất lượng
AUTO_TRIM_POSITIONS = True      # Tự động đóng bớt nếu quá nhiều vị thế

VOLUME_USDT = 8.0              # 8 USDT/lệnh
MIN_NOTIONAL_USDT = 5.0        # Notional tối thiểu Binance

# Take profit / Stop loss (theo %)
TAKE_PROFIT_PCT = 0.025        # ✅✅ Tăng TP lên 2.5% (từ 2%) - Lãi nhiều hơn khi thắng
STOP_LOSS_PCT = 0.025          # ✅✅ Giữ SL 2.5% - Risk/Reward = 1:1
SLIPPAGE_BUFFER_PCT = 0.015    # +1.5% buffer

# --- GIỚI HẠN DRAWDOWN & DỪNG BOT ---
MAX_DRAWDOWN_PCT = 8.0         # Dừng khi lỗ 8% từ đỉnh
MAX_CONSECUTIVE_LOSSES = 3     # Dừng sau 3 lệnh thua liên tiếp
DAILY_LOSS_LIMIT_PCT = 4.0     # Dừng khi lỗ 4% trong ngày

# --- THANH KHOẢN & KỸ THUẬT ---
MIN_24H_VOLUME_USDT = 10_000_000  # ✅✅ Tăng lên 10M (từ 3M) - CHỈ trade coin TOP
MIN_FREE_BALANCE_USDT = 30.0      # 30 USDT - đủ cho 3 vị thế
MARGIN_BUFFER_PCT = 0.20          # Buffer 20%

# --- MẠNG & RETRY ---
API_RECV_WINDOW = 8000
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2

# --- MARGIN MODE ---
MARGIN_TYPE = 'ISOLATED'  # ISOLATED an toàn hơn

# --- CHIẾN LƯỢC ---
STRATEGY = 'multi'  # ✅✅ Đổi từ 'rsi' → 'multi'
                    # multi = RSI + StochRSI + MACD + EMA
                    # Filter chặt hơn → ít tín hiệu nhưng win rate cao

# Khung thời gian nến & chu kỳ quét
KLINES_INTERVAL = '15m'         # 15 phút
SCAN_INTERVAL_SEC = 300         # ✅✅ Tăng lên 5 phút (từ 3 phút) - Giảm false signals

# Whitelist symbol
SYMBOL_WHITELIST = [
    'BTCUSDT',   # Bitcoin - coin #1
    'ETHUSDT',   # Ethereum - coin #2
    'BNBUSDT',   # Binance Coin - coin #3
    'SOLUSDT',   # Solana - coin #4
    'XRPUSDT',   # Ripple - coin #5
]
# ✅✅ CHỈ trade 5 coin TOP này - Đã proven trong phân tích

# --- LOGGING ---
LOG_FILE = "bot.log"
LOG_LEVEL = "INFO"

# --- DATABASE ---
ENABLE_DB = True
DB_PATH = "trades.db"

# --- TESTNET ---
TESTNET = True  # True = testnet, False = mainnet
                # ⚠️ TEST CONFIG MỚI TRÊN TESTNET 1 TUẦN TRƯỚC KHI CHẠY THẬT!

"""
===========================================
GIẢI THÍCH THAY ĐỔI
===========================================

1. MIN_24H_VOLUME: 3M → 10M
   ├─ Lý do: Coin volume thấp dễ bị pump/dump
   ├─ Kết quả mong đợi: Loại bỏ BIRBUSDT, LIGHTUSDT... (win nhưng rủi ro cao)
   └─ Chỉ giữ BTC, ETH, BNB, SOL, XRP (thanh khoản cao, stable hơn)

2. STRATEGY: rsi → multi
   ├─ rsi: Chỉ dùng RSI (đơn giản, nhiều false signals)
   ├─ multi: RSI + StochRSI + MACD + EMA (filter 4 lớp)
   └─ Kết quả: Ít tín hiệu (5-10/ngày) nhưng chất lượng cao

3. MAX_POSITIONS: 5 → 3
   ├─ Lý do: Ít vị thế = quản lý tốt hơn
   └─ Focus vào quality thay vì quantity

4. TAKE_PROFIT: 2% → 2.5%
   ├─ Win khi thắng: 0.32 → 0.40 USD
   ├─ P/L ratio: 0.80 → 1.00 (break-even)
   └─ Cần win rate 50% để hòa vốn (thay vì 55%)

5. SCAN_INTERVAL: 3 phút → 5 phút
   ├─ Lý do: Giảm overtrading
   └─ Chờ tín hiệu rõ ràng hơn

DỰ ĐOÁN KẾT QUẢ:

Với config mới:
├─ Win rate dự kiến: 50-60% (tăng từ 28%)
├─ Số lệnh/ngày: 3-6 (giảm từ 10-15)
├─ Lợi nhuận/lệnh (win rate 55%):
│  └─ (0.40 × 0.55) - (0.40 × 0.45) = 0.04 USD
├─ Số lệnh cần cho 15 USD/tháng:
│  └─ 15 ÷ 0.04 = 375 lệnh/tháng = 12.5 lệnh/ngày
└─ KẾT LUẬN: KHẢ THI!

SO SÁNH:

                        CŨ          MỚI         THAY ĐỔI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRATEGY                rsi         multi       Chặt hơn
MIN_24H_VOLUME          3M          10M         +233%
MAX_POSITIONS           5           3           -40%
TAKE_PROFIT             2.0%        2.5%        +25%
SCAN_INTERVAL           3min        5min        +67%
WHITELIST               None        Top 5       CHỈ proven
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KẾ HOẠCH THỰC HIỆN:

TUẦN 1 (TESTNET):
├─ Backup config cũ: cp config.py config_old.py
├─ Áp dụng config mới: cp config_optimized.py config.py
├─ Chạy testnet: python main.py
├─ Theo dõi: python scripts/analyze_simple.py (mỗi ngày)
└─ Mục tiêu: Đạt win rate ≥50% sau 20-30 lệnh

TUẦN 2 (TESTNET):
├─ Tiếp tục test
├─ Điều chỉnh nếu cần (SL/TP, SCAN_INTERVAL)
└─ Mục tiêu: Xác nhận win rate ổn định 50-60%

TUẦN 3+ (MAINNET nếu OK):
├─ Chuyển sang mainnet (TESTNET = False)
├─ Bắt đầu với vốn nhỏ (100-150 USDT)
└─ Tăng dần lên 200-300 USDT

LƯU Ý QUAN TRỌNG:

1. ⚠️ BACKUP CONFIG CŨ TRƯỚC KHI THAY ĐỔI
2. 📊 Test ít nhất 1 tuần trên testnet
3. 💰 Không chạy mainnet cho đến khi win rate ≥50% trên testnet
4. 📈 Theo dõi hàng ngày: python scripts/analyze_simple.py
5. 🛑 Dừng nếu win rate < 45% sau 30 lệnh

DẤU HIỆU THÀNH CÔNG:

✅ Win rate ≥50% sau 20 lệnh
✅ Lợi nhuận/lệnh > 0
✅ Không có lỗ >3 lệnh liên tiếp
✅ Tổng PnL dương sau 30 lệnh

DẤU HIỆU CẦN ĐIỀU CHỈNH:

⚠️ Win rate < 45% sau 30 lệnh → Review lại STRATEGY
⚠️ Quá ít tín hiệu (< 3 lệnh/ngày) → Giảm MIN_24H_VOLUME xuống 8M
⚠️ Quá nhiều tín hiệu (> 10 lệnh/ngày) → Tăng SCAN_INTERVAL lên 10 phút

KHI NÀO QUAY LẠI CONFIG CŨ?

Nếu sau 2 tuần testnet:
- Win rate vẫn < 40%
- Lỗ liên tục
- Không có cải thiện

→ Có thể thị trường không phù hợp với strategy này
→ Cần review lại chiến lược hoặc tạm dừng bot
"""
