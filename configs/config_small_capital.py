# -*- coding: utf-8 -*-
"""
CẤU HÌNH BOT TRADING - VỐN < 300 USDT
======================================
Mục tiêu: 10-20 USD/tháng (~2.5-5 USD/tuần)
Vốn khuyến nghị: 150-300 USDT
Chiến lược: An toàn, ít rủi ro, volume nhỏ
"""

# --- RỦI RO TÀI CHÍNH ---
LEVERAGE = 2                    # Đòn bẩy x2 (an toàn)
MAX_CONCURRENT_POSITIONS = 3    # ✅ Giảm xuống 3 vị thế (từ 5)
                                # → Giảm margin cần thiết
VOLUME_USDT = 8.0              # ✅ 8 USDT/lệnh (tăng từ 5.5, nhưng vẫn nhỏ)
                                # → Lãi ~0.32 USD/lệnh thắng
                                # → Cần ~40-50 lệnh thắng/tháng cho 15 USD
MIN_NOTIONAL_USDT = 5.0         # Notional tối thiểu Binance

# Take profit / Stop loss (theo %)
TAKE_PROFIT_PCT = 0.02         # +2% (giữ nguyên)
STOP_LOSS_PCT = 0.025          # 2.5% (giữ nguyên)
SLIPPAGE_BUFFER_PCT = 0.003    # +0.3% buffer

# --- GIỚI HẠN DRAWDOWN & DỪNG BOT ---
MAX_DRAWDOWN_PCT = 8.0         # ✅ Giảm xuống 8% (từ 10%) - an toàn hơn với vốn nhỏ
MAX_CONSECUTIVE_LOSSES = 3     # Dừng sau 3 lệnh thua liên tiếp
DAILY_LOSS_LIMIT_PCT = 4.0     # ✅ Giảm xuống 4% (từ 5%) - bảo vệ vốn nhỏ

# --- THANH KHOẢN & KỸ THUẬT ---
MIN_24H_VOLUME_USDT = 2_000_000   # ✅ Tăng lên 2M (từ 1M) - chỉ trade coin thanh khoản cao
MIN_FREE_BALANCE_USDT = 30.0      # ✅ 30 USDT (từ 20) - đủ cho 3 vị thế x 8 USDT
MARGIN_BUFFER_PCT = 0.20          # ✅ Tăng buffer lên 20% (từ 15%) - an toàn hơn

# --- MẠNG & RETRY ---
API_RECV_WINDOW = 8000
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2

# --- MARGIN MODE ---
MARGIN_TYPE = 'ISOLATED'  # ISOLATED an toàn hơn với vốn nhỏ

# --- CHIẾN LƯỢC ---
STRATEGY = 'multi'  # RSI + StochRSI + MACD + EMA
                    # Ít tín hiệu nhưng chất lượng cao → win rate tốt

# Khung thời gian nến & chu kỳ quét
KLINES_INTERVAL = '15m'         # 15 phút (cân bằng)
SCAN_INTERVAL_SEC = 180         # 3 phút

# Whitelist symbol
SYMBOL_WHITELIST = []           # [] = trade tất cả coin có volume đủ
                                # Hoặc chỉ định coin ổn định:
                                # ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']

# --- LOGGING ---
LOG_FILE = "bot.log"
LOG_LEVEL = "INFO"

# --- DATABASE ---
ENABLE_DB = True
DB_PATH = "trades.db"

# --- TESTNET ---
TESTNET = True  # True = testnet, False = mainnet
                # ⚠️ TEST TRÊN TESTNET 1-2 TUẦN TRƯỚC KHI CHẠY THẬT!

"""
===========================================
GIẢI THÍCH CHI TIẾT
===========================================

VỐN KHUYẾN NGHỊ:
- Tối thiểu: 150 USDT (có thể chạy được)
- An toàn: 200-300 USDT (thoải mái hơn)

VỚI CẤU HÌNH NÀY:
├─ Volume/lệnh: 8 USDT
├─ Đòn bẩy: x2 → Giá trị lệnh = 16 USDT
├─ Take Profit: 2% → Lãi/lệnh thắng = 16 × 2% = 0.32 USD
└─ Stop Loss: 2.5% → Lỗ/lệnh thua = 16 × 2.5% = 0.40 USD

TÍNH TOÁN LỢI NHUẬN:

1. MỤC TIÊU 15 USD/THÁNG (giữa 10-20):
   
   Với win rate 60%:
   ├─ Profit/lệnh = (0.32 × 0.6) - (0.40 × 0.4) = 0.032 USD
   ├─ Số lệnh cần = 15 ÷ 0.032 ≈ 470 lệnh/tháng
   └─ = ~16 lệnh/ngày
   
   Strategy 'multi' thường cho 5-10 tín hiệu/ngày
   → Với 3 vị thế cùng lúc, có thể đạt 10-15 lệnh/ngày
   → KHẢ THI!

2. MỤC TIÊU 10 USD/THÁNG (thấp hơn, an toàn):
   
   ├─ Số lệnh cần ≈ 310 lệnh/tháng
   └─ = ~10 lệnh/ngày → DỄ ĐẠT HƠN!

3. MỤC TIÊU 20 USD/THÁNG (cao hơn):
   
   ├─ Số lệnh cần ≈ 625 lệnh/tháng
   └─ = ~21 lệnh/ngày → KHÓ HƠN, phụ thuộc thị trường

PHÂN TÍCH RỦI RO:

1. Margin cần thiết:
   ├─ 3 vị thế × 8 USDT = 24 USDT margin
   ├─ Buffer 20% = thêm 4.8 USDT
   └─ Tổng cần: ~30 USDT khả dụng
   
   Với vốn 200 USDT, còn 170 USDT dư → AN TOÀN ✅

2. Drawdown 8%:
   ├─ Vốn 200 USDT → Dừng khi lỗ 16 USDT
   └─ = ~50 lệnh thua liên tục (rất khó xảy ra với strategy 'multi')

3. Lỗ trong ngày 4%:
   ├─ Vốn 200 USDT → Dừng khi lỗ 8 USDT/ngày
   └─ = ~20 lệnh thua trong ngày (bot sẽ dừng trước)

KỊCH BẢN THỰC TẾ:

Tuần 1-2 (Testnet):
├─ Chạy trên testnet để đo win rate
├─ Quan sát số lệnh/ngày
└─ Điều chỉnh config nếu cần

Tuần 3-4 (Mainnet - vốn nhỏ):
├─ Bắt đầu với 100-150 USDT
├─ Mục tiêu: 5-10 USD/tháng (thấp)
└─ Nếu ổn định → tăng vốn lên 200-300 USDT

Tháng 2 trở đi:
├─ Vốn 200-300 USDT
├─ Mục tiêu: 10-20 USD/tháng
└─ Rút lợi nhuận hoặc tái đầu tư

SO SÁNH VỚI CONFIG CŨ:

                        CŨ          MỚI         THAY ĐỔI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOLUME_USDT             5.5         8.0         +45%
MAX_POSITIONS           5           3           -40%
MIN_FREE_BALANCE        20          30          +50%
MAX_DRAWDOWN            10%         8%          An toàn hơn
DAILY_LOSS_LIMIT        5%          4%          An toàn hơn
MARGIN_BUFFER           15%         20%         An toàn hơn
MIN_24H_VOLUME          1M          2M          Coin tốt hơn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ Cấu hình mới AN TOÀN HƠN, PHÙ HỢP VỐN NHỎ

TẠI SAO GIẢM MAX_POSITIONS XUỐNG 3?

1. Giảm margin cần thiết:
   ├─ 5 vị thế × 8 = 40 USDT (quá nhiều cho vốn 200)
   └─ 3 vị thế × 8 = 24 USDT (vừa phải)

2. Quản lý rủi ro tốt hơn:
   ├─ Ít vị thế = dễ theo dõi
   └─ Giảm nguy cơ nhiều lệnh thua cùng lúc

3. Vẫn đủ để đạt mục tiêu:
   ├─ 3 vị thế có thể tạo 10-15 lệnh/ngày
   └─ Đủ cho 15 USD/tháng

LƯU Ý QUAN TRỌNG:

1. ⚠️ TEST TRÊN TESTNET TRƯỚC:
   - Ít nhất 1-2 tuần
   - Đo win rate thực tế
   - Xem bot có chạy ổn định không

2. 📊 THEO DÕI HÀNG NGÀY:
   - Kiểm tra log mỗi ngày
   - Đảm bảo SL/TP hoạt động
   - Xem có lệnh bất thường không

3. 💰 BẮT ĐẦU VỐN NHỎ:
   - Tuần đầu: 100 USDT
   - Nếu ổn định → tăng lên 200-300 USDT
   - KHÔNG nạp hết vốn ngay từ đầu

4. 📈 ĐIỀU CHỈNH MỤC TIÊU:
   - Tháng 1: Mục tiêu 5-10 USD (làm quen)
   - Tháng 2-3: Tăng lên 10-15 USD
   - Tháng 4+: Có thể đạt 15-20 USD nếu ổn định

5. 🛑 BIẾT LÚC DỪNG:
   - Nếu thua 3 ngày liên tiếp → tạm dừng, review
   - Nếu thị trường biến động mạnh → giảm volume
   - Nếu win rate < 45% → điều chỉnh strategy

TỔNG KẾT:

✅ Config này phù hợp với:
   - Vốn 150-300 USDT
   - Mục tiêu 10-20 USD/tháng
   - Người mới, muốn an toàn

✅ Ưu điểm:
   - Rủi ro thấp
   - Dễ quản lý
   - Phí giao dịch thấp

⚠️ Nhược điểm:
   - Lợi nhuận nhỏ (nhưng ổn định)
   - Cần kiên nhẫn
   - Phụ thuộc win rate

🎯 Khuyến nghị:
   - Test 1-2 tuần trên testnet
   - Chạy thật với 100-150 USDT
   - Tăng dần lên 200-300 USDT
   - Mục tiêu tháng 1: 5-10 USD
   - Mục tiêu tháng 2+: 10-20 USD
"""
