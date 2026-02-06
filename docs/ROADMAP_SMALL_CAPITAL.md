# ROADMAP CHI TIẾT - VỐN < 300 USDT

## 🎯 Mục tiêu: 10-20 USD/tháng

---

## GIAI ĐOẠN 1: CHUẨN BỊ (3-7 ngày)

### Bước 1: Test trên Testnet
```bash
# 1. Sao chép config mới
cp config_small_capital.py config.py

# 2. Đảm bảo TESTNET = True
# Mở config.py, kiểm tra dòng:
TESTNET = True

# 3. Chạy bot
python main1.py
```

**Mục tiêu giai đoạn này:**
- [ ] Bot chạy không lỗi
- [ ] Có ít nhất 20-30 lệnh để đo win rate
- [ ] Win rate >= 55% (tốt)
- [ ] Không có lệnh bị lỗi margin/insufficient
- [ ] SL và TP hoạt động đúng

**Thời gian:** 3-7 ngày (tùy số tín hiệu)

---

## GIAI ĐOẠN 2: TESTNET THỰC CHIẾN (1-2 tuần)

### Theo dõi hàng ngày:

**Sáng (8-9h):**
```bash
# Xem log
tail -50 bot.log

# Kiểm tra:
# - Có lệnh nào lỗi không?
# - Win rate hiện tại bao nhiêu?
# - Balance testnet thay đổi thế nào?
```

**Tối (20-21h):**
```bash
# Xem dashboard (nếu có)
streamlit run dashboard.py

# Ghi chép:
# - Số lệnh hôm nay: ___
# - Thắng: ___ | Thua: ___
# - PnL hôm nay: ___
```

### Điều chỉnh nếu cần:

**Nếu win rate < 50%:**
```python
# Trong config.py, thử:
MIN_24H_VOLUME_USDT = 5_000_000  # Tăng lên 5M (chỉ trade coin lớn)
SYMBOL_WHITELIST = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # Chỉ trade top coin
```

**Nếu quá ít tín hiệu (<5 lệnh/ngày):**
```python
SCAN_INTERVAL_SEC = 120  # Giảm xuống 2 phút
KLINES_INTERVAL = '5m'   # Hoặc thử 5 phút
```

**Nếu quá nhiều tín hiệu (>20 lệnh/ngày):**
```python
STRATEGY = 'multi'  # Đảm bảo dùng multi (lọc chặt hơn)
MIN_24H_VOLUME_USDT = 3_000_000  # Tăng lên
```

**Kết quả mong đợi sau 1-2 tuần:**
- Tổng lệnh: 100-200 lệnh
- Win rate: 55-65%
- PnL testnet: +10-30 USD (với vốn testnet 10,000)

---

## GIAI ĐOẠN 3: CHUYỂN SANG MAINNET (Tuần 1-2)

### Chuẩn bị:

1. **Lấy API Key Mainnet:**
   - Truy cập: https://www.binance.com
   - API Management → Create API
   - ✅ Chỉ bật: Enable Futures
   - ❌ KHÔNG bật: Enable Withdrawals
   - Lưu API key và Secret

2. **Cấu hình:**
   ```python
   # Trong config.py
   TESTNET = False  # ⚠️ QUAN TRỌNG!
   ```

3. **Nạp vốn ban đầu:**
   - **Khuyến nghị: 100 USDT** (thấp để test)
   - Chuyển từ Spot sang Futures
   - Kiểm tra: Balance >= 100 USDT

### Chạy tuần đầu:

```bash
# Trước khi chạy, kiểm tra:
python check_api.py

# Phải thấy:
# - Balance: 100 USDT (hoặc số bạn nạp)
# - KHÔNG thấy "🔧 Đang dùng TESTNET"

# Chạy bot
python main1.py
```

**Theo dõi sát sao:**
- Kiểm tra log **MỖI 2-3 GIỜ**
- Đảm bảo SL/TP hoạt động
- Ghi chép mọi lệnh

**Mục tiêu tuần 1-2:**
- Balance: 100 → 102-105 USDT (+2-5%)
- Không có lỗi bất thường
- Win rate giống testnet (±5%)

**Nếu tuần 1-2 ổn định → Tăng vốn lên 200 USDT**

---

## GIAI ĐOẠN 4: VẬN HÀNH ỔN ĐỊNH (Tháng 1+)

### Vốn khuyến nghị: 200-300 USDT

### Mục tiêu từng tháng:

**Tháng 1 (làm quen):**
- Vốn: 200 USDT
- Mục tiêu: **+5-10 USD** (+2.5-5%)
- Focus: Ổn định, không lỗi

**Tháng 2 (tăng trưởng):**
- Vốn: 210-220 USDT (gốc + lời tháng 1)
- Mục tiêu: **+10-15 USD** (+4.5-7%)
- Focus: Tăng win rate

**Tháng 3+ (ổn định):**
- Vốn: 220-250 USDT
- Mục tiêu: **+15-20 USD** (+6-8%)
- Focus: Duy trì, rút lời

### Lịch theo dõi:

**Hàng ngày:**
- [ ] Sáng: Xem log, kiểm tra balance
- [ ] Tối: Ghi chép PnL, số lệnh

**Hàng tuần:**
- [ ] Thứ 7: Review tuần (win rate, PnL, vấn đề)
- [ ] Chủ nhật: Backup database `trades.db`

**Hàng tháng:**
- [ ] Ngày 1: Tổng kết tháng trước
- [ ] Rút lợi nhuận hoặc tái đầu tư
- [ ] Điều chỉnh config nếu cần

---

## KẾ HOẠCH TÀI CHÍNH

### Chiến lược quản lý vốn:

**Option 1: Rút lời định kỳ (An toàn)**
```
Tháng 1: 200 USDT → 210 USDT (+10)
         Rút: 5 USDT
         Giữ lại: 205 USDT

Tháng 2: 205 USDT → 217 USDT (+12)
         Rút: 7 USDT
         Giữ lại: 210 USDT

Tháng 3: 210 USDT → 225 USDT (+15)
         Rút: 10 USDT
         Giữ lại: 215 USDT
```
→ Sau 3 tháng: Rút được 22 USD, vốn tăng lên 215

**Option 2: Tái đầu tư toàn bộ (Tích cực)**
```
Tháng 1: 200 USDT → 210 USDT (+10)
Tháng 2: 210 USDT → 223 USDT (+13)
Tháng 3: 223 USDT → 239 USDT (+16)
Tháng 4: 239 USDT → 256 USDT (+17)
```
→ Sau 4 tháng: Vốn 256 USDT (+28%)

**Option 3: Hybrid (Cân bằng)**
```
Mỗi tháng:
- Rút 50% lợi nhuận
- Tái đầu tư 50%

Tháng 1: 200 → 210 (+10) → Rút 5, giữ 205
Tháng 2: 205 → 217 (+12) → Rút 6, giữ 211
Tháng 3: 211 → 227 (+16) → Rút 8, giữ 219
```
→ Sau 3 tháng: Rút 19 USD, vốn tăng lên 219

**Khuyến nghị:** Dùng **Option 3** (Hybrid)
- Có tiền rút ra dùng (động lực)
- Vốn vẫn tăng đều (hiệu quả)

---

## BẢNG THEO DÕI HÀNG NGÀY (Template)

```
NGÀY: __/__/____

BUỔI SÁNG:
├─ Balance hiện tại: _____ USDT
├─ Vị thế đang mở: ___ (_____, _____, _____)
├─ Lệnh chờ (pending): ___
└─ Ghi chú: _____________________

BUỔI TỐI:
├─ Số lệnh hôm nay: ___
│  ├─ Thắng: ___
│  └─ Thua: ___
├─ PnL hôm nay: _____ USD
├─ Balance cuối ngày: _____ USDT
└─ Win rate tích lũy: ____%

VẤN ĐỀ (nếu có):
└─ _____________________

HÀNH ĐỘNG NGÀY MAI:
└─ _____________________
```

---

## CHECKLIST HÀNG TUẦN

### Thứ 7 - Review tuần:

- [ ] Tổng lệnh tuần này: ___
- [ ] Win rate tuần: ___% (so với mục tiêu 55-65%)
- [ ] PnL tuần: _____ USD (mục tiêu ~2.5-5 USD)
- [ ] Balance đầu tuần: _____ → Cuối tuần: _____
- [ ] Có lệnh bất thường không? _____
- [ ] Cần điều chỉnh config không? _____

### Chủ nhật - Chuẩn bị tuần mới:

- [ ] Backup `trades.db` → `trades_backup_YYYYMMDD.db`
- [ ] Xóa log cũ nếu quá lớn (giữ lại 1 tuần)
- [ ] Kiểm tra kết nối API: `python check_api.py`
- [ ] Review market outlook tuần tới (tin tức, sự kiện lớn)
- [ ] Điều chỉnh SYMBOL_WHITELIST nếu cần

---

## KHI NÀO DỪNG BOT?

### 🛑 Dừng ngay lập tức nếu:

1. **Lỗi kỹ thuật nghiêm trọng:**
   - Bot đặt lệnh sai giá
   - SL/TP không hoạt động
   - Margin bị thanh lý

2. **Lỗ nặng bất thường:**
   - Lỗ > 10% trong 1 ngày
   - 5 lệnh thua liên tiếp trong 1 ngày
   - Win rate tuần < 40%

3. **Thị trường bất thường:**
   - Biến động mạnh (BTC +/-10% trong ngày)
   - Có tin tức lớn (Fed tăng lãi suất, hack sàn, ...)
   - Volume thị trường giảm mạnh (< 50% bình thường)

### ⏸️ Tạm dừng để review nếu:

1. **Win rate giảm:**
   - Win rate 2 tuần liên tục < 50%
   - Cần review strategy hoặc market condition

2. **Lợi nhuận không đạt:**
   - 2 tuần liên tục PnL < 2 USD
   - Có thể thị trường sideway, ít cơ hội

3. **Vốn gần mức rủi ro:**
   - Balance còn < 150 USDT (từ 200)
   - Drawdown gần 8% (mức cảnh báo)

---

## CÔNG THỨC TÍNH TOÁN NHANH

### 1. Lợi nhuận mỗi lệnh:
```
Lãi/thắng = VOLUME × LEVERAGE × TP%
         = 8 × 2 × 0.02
         = 0.32 USD

Lỗ/thua = VOLUME × LEVERAGE × SL%
        = 8 × 2 × 0.025
        = 0.40 USD
```

### 2. Số lệnh cần cho mục tiêu X USD (win rate W):
```
Profit/lệnh = (0.32 × W) - (0.40 × (1-W))

Với W = 60%:
Profit/lệnh = (0.32 × 0.6) - (0.40 × 0.4)
            = 0.192 - 0.160
            = 0.032 USD

Số lệnh = Mục tiêu ÷ Profit/lệnh
        = 15 ÷ 0.032
        = 469 lệnh/tháng
        ≈ 16 lệnh/ngày
```

### 3. Win rate cần thiết cho mục tiêu X USD/tháng:
```
Gọi W là win rate cần tìm
Mục tiêu = Số lệnh × [(0.32 × W) - (0.40 × (1-W))]

Ví dụ mục tiêu 15 USD, 450 lệnh/tháng:
15 = 450 × [(0.32 × W) - (0.40 × (1-W))]
15 = 450 × [0.72W - 0.40]
W = (15/450 + 0.40) / 0.72
W = 0.602
W ≈ 60%
```

---

## FAQ - NHỮNG CÂU HỎI THƯỜNG GẶP

### Q1: Win rate của tôi chỉ 50%, có đạt mục tiêu không?

**A:** Với win rate 50%:
```
Profit/lệnh = (0.32 × 0.5) - (0.40 × 0.5) = -0.04 USD
→ LỖ! Không đạt mục tiêu.
```
→ Cần điều chỉnh: tăng MIN_24H_VOLUME, dùng SYMBOL_WHITELIST, hoặc thử strategy khác.

### Q2: Tôi có 150 USDT, có nên chạy không?

**A:** Được, nhưng:
- Giảm VOLUME_USDT xuống 6-7 USDT
- Giảm MAX_CONCURRENT_POSITIONS xuống 2
- Mục tiêu thấp hơn: 5-10 USD/tháng

### Q3: Khi nào nên tăng vốn lên 300 USDT?

**A:** Khi:
- Chạy ổn định 1 tháng với 200 USDT
- Win rate >= 55%
- Lợi nhuận đều đặn (ít nhất 10 USD/tháng)
- Không có lỗi kỹ thuật

### Q4: Có nên tăng LEVERAGE lên x3 hoặc x5 không?

**A:** KHÔNG khuyến nghị vì:
- Leverage cao = rủi ro thanh lý cao
- Với vốn nhỏ, an toàn quan trọng hơn lợi nhuận
- x2 đã đủ để đạt mục tiêu 10-20 USD/tháng

### Q5: Bot có thể chạy 24/7 không giám sát được không?

**A:** KHÔNG:
- Cần kiểm tra ít nhất 2 lần/ngày
- Thị trường crypto biến động, có thể có sự cố
- Nên có cảnh báo Telegram/Discord

---

## TỔNG KẾT

### ✅ Làm gì:
1. Test 1-2 tuần trên testnet
2. Bắt đầu với 100-150 USDT
3. Tăng dần lên 200-300 USDT
4. Theo dõi hàng ngày, review hàng tuần
5. Rút lời hoặc tái đầu tư theo kế hoạch

### ❌ Không làm gì:
1. KHÔNG nạp hết vốn ngay từ đầu
2. KHÔNG tắt SL/TP
3. KHÔNG tăng leverage quá 2-3x
4. KHÔNG để bot chạy mà không giám sát
5. KHÔNG mong đợi lợi nhuận quá cao

### 🎯 Kỳ vọng thực tế:
- Tháng 1: 5-10 USD (làm quen)
- Tháng 2: 10-15 USD (tăng trưởng)
- Tháng 3+: 15-20 USD (ổn định)

**Chúc bạn trading thành công! 🚀**
