# HƯỚNG DẪN SỬ DỤNG DASHBOARD V2

## 🚀 Cài đặt

### Yêu cầu:
```bash
pip install streamlit pandas --break-system-packages
```

## 📊 Chạy Dashboard

### Cách 1: Dashboard cũ (cơ bản)
```bash
streamlit run dashboard.py
```

### Cách 2: Dashboard V2 (nâng cấp - khuyến nghị)
```bash
streamlit run dashboard_v2.py
```

Dashboard sẽ mở tại: `http://localhost:8501`

---

## ✨ Tính năng Dashboard V2

### 1. Trạng thái hiện tại
- **Balance & Available**: Số dư tổng và khả dụng
- **Số vị thế đang mở**: Hiển thị realtime
- **Thời gian cập nhật**: Lần cuối bot ghi status
- **⚠️ Cảnh báo rủi ro**: Tự động phát hiện:
  - Drawdown cao (>= 80% giới hạn)
  - Lỗ trong ngày cao
  - Thua liên tiếp

### 2. Vị thế đang mở
- Danh sách chi tiết từng vị thế
- Entry price, quantity, notional value
- Thời gian mở lệnh
- Click để xem chi tiết

### 3. Thống kê tổng quan
**Cột 1:**
- Tổng lệnh đã đóng
- Số lệnh thắng/thua

**Cột 2:**
- Win Rate (màu xanh nếu >= 55%)
- Average Win/Loss

**Cột 3:**
- Tổng PnL (màu xanh/đỏ)
- Profit Factor (>1 = tốt)
- Thời gian hold trung bình

**Cột 4:**
- Largest Win/Loss
- Expected Value (EV mỗi lệnh)

### 4. Equity Curve & Drawdown
**Tab Equity:**
- Biểu đồ đường equity theo thời gian
- Max Drawdown (USDT & %)

**Tab Drawdown:**
- Biểu đồ % drawdown theo thời gian
- Nhìn thấy các đợt rủi ro

### 5. Thống kê theo Symbol
- Xem coin nào lãi/lỗ nhiều nhất
- Win rate từng coin
- Tổng PnL từng coin
- Sắp xếp theo PnL

### 6. Lịch sử lệnh
- Bảng 100 lệnh gần nhất
- Thông tin đầy đủ: entry, exit, PnL, thời gian
- **Export CSV**: Tải về để phân tích ngoài

---

## 📁 Sidebar - Bộ lọc & Cài đặt

### Chế độ Bot
- 🟢 **MAINNET**: Tiền thật
- 🟡 **TESTNET**: Tiền test

### Cấu hình hiện tại
- Volume/lệnh
- Đòn bẩy
- Max Drawdown
- Daily Loss Limit

### Auto Refresh
- Tích để dashboard tự động refresh 30 giây/lần
- Hữu ích khi theo dõi realtime

### Bộ lọc thời gian
- **Tất cả**: Xem toàn bộ dữ liệu
- **7 ngày qua**: Chỉ lệnh 1 tuần
- **30 ngày qua**: Chỉ lệnh 1 tháng
- **Hôm nay**: Chỉ lệnh hôm nay

---

## 📖 Cách đọc thống kê

### Win Rate
```
>= 60%: Tuyệt vời 🟢
55-59%: Tốt 🟢
50-54%: Trung bình 🟡
< 50%: Cần cải thiện 🔴
```

### Profit Factor
```
>= 2.0: Xuất sắc
1.5-2.0: Tốt
1.0-1.5: OK
< 1.0: Lỗ (thua nhiều hơn thắng)
```

### Expected Value (EV)
```
EV > 0: Chiến lược có lãi dài hạn
EV = 0: Hòa vốn
EV < 0: Chiến lược thua lỗ (cần điều chỉnh)
```

Công thức:
```
EV = (Avg Win × Win Rate) + (Avg Loss × Loss Rate)
```

### Max Drawdown
```
< 5%: An toàn
5-8%: Cảnh báo
>= 8%: Nguy hiểm (bot có thể dừng)
```

---

## 🎯 Ví dụ phân tích

### Kịch bản 1: Win rate thấp nhưng vẫn lãi
```
Win Rate: 45%
Avg Win: 1.0 USDT
Avg Loss: -0.5 USDT
Profit Factor: 1.5
Total PnL: +15 USDT

→ Phân tích:
  - Thua nhiều nhưng khi thắng thì lãi gấp đôi
  - Risk/Reward tốt (1:2)
  - Nên giữ chiến lược, có thể tăng volume
```

### Kịch bản 2: Win rate cao nhưng lỗ
```
Win Rate: 70%
Avg Win: 0.2 USDT
Avg Loss: -0.8 USDT
Profit Factor: 0.8
Total PnL: -10 USDT

→ Phân tích:
  - Thắng nhiều nhưng lãi ít, thua ít nhưng lỗ nặng
  - Stop Loss quá xa hoặc Take Profit quá gần
  - Cần điều chỉnh SL/TP trong config
```

### Kịch bản 3: Symbol BTCUSDT lãi, DOGEUSDT lỗ
```
BTCUSDT: 15 lệnh, Win 60%, PnL +5 USDT
DOGEUSDT: 10 lệnh, Win 30%, PnL -3 USDT

→ Hành động:
  - Thêm BTCUSDT vào whitelist
  - Loại DOGEUSDT (hoặc review chiến lược cho coin này)
  
Trong config.py:
SYMBOL_WHITELIST = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
```

---

## 🔧 Troubleshooting

### Dashboard không mở
```bash
# Kiểm tra streamlit đã cài
pip list | grep streamlit

# Cài lại nếu cần
pip install streamlit --break-system-packages
```

### Lỗi "No such table: trades"
```bash
# Chạy bot 1 lần để tạo database
python main1.py

# Hoặc khởi tạo DB thủ công
python -c "import db; db.init_db()"
```

### Dashboard không hiển thị dữ liệu
- Kiểm tra file `trades.db` có tồn tại không
- Chạy bot ít nhất 1 vòng để ghi status
- Xem log: `tail -50 bot.log`

### Equity curve trống
- Cần có ít nhất 1 lệnh đã đóng (TP hoặc SL)
- Nếu chỉ có vị thế mở → chưa có equity

---

## 📱 Tips sử dụng

### 1. Theo dõi hàng ngày
```bash
# Sáng: Mở dashboard xem qua
streamlit run dashboard_v2.py

# Xem:
- Có cảnh báo rủi ro không?
- Win rate hôm qua như thế nào?
- Vị thế nào đang mở?
```

### 2. Review hàng tuần
```bash
# Chủ nhật: Phân tích tuần qua
- Chọn filter "7 ngày qua"
- Xem win rate tuần
- Xem symbol nào tốt/xấu
- Export CSV để phân tích sâu
```

### 3. Export & phân tích ngoài
```python
# Sau khi export CSV, có thể dùng Excel/Python
import pandas as pd

df = pd.read_csv('trades_export_20260128_120000.csv')

# Win rate theo ngày
df['Ngày'] = pd.to_datetime(df['Đóng']).dt.date
daily_wr = df.groupby('Ngày').apply(
    lambda x: (x['PnL'].astype(float) > 0).sum() / len(x) * 100
)
print(daily_wr)
```

### 4. So sánh với mục tiêu
```
Mục tiêu tháng: 15 USD
Đã chạy: 10 ngày
Hiện tại: +4 USD

→ Pace: 4 / 10 * 30 = 12 USD/tháng
→ Hơi chậm, cần tăng tốc hoặc điều chỉnh
```

---

## 🆕 Tính năng sắp tới

**Dashboard V3 (dự kiến):**
- [ ] Biểu đồ win rate theo giờ trong ngày
- [ ] Heat map PnL theo ngày trong tuần
- [ ] Phân tích correlation giữa các symbol
- [ ] Alert qua Telegram khi có cảnh báo
- [ ] Backtest simulator ngay trong dashboard
- [ ] Dark mode

---

## 📞 Hỗ trợ

**Nếu gặp vấn đề:**
1. Kiểm tra log: `tail -100 bot.log`
2. Kiểm tra database: `ls -lh trades.db`
3. Xem version: `streamlit --version`

**Tối ưu hiệu suất:**
- Nếu database > 10MB → chỉ load 500 lệnh gần nhất
- Tắt auto-refresh nếu không cần
- Dùng filter thời gian để giảm data load

---

## 📊 Screenshots mẫu

**Section 1: Trạng thái**
```
💰 Balance        ✅ Khả dụng      📊 Vị thế mở    🕐 Cập nhật
5000.35 USDT      4987.17 USDT     5              17:06:51
```

**Section 3: Thống kê**
```
Tổng lệnh: 45    Win Rate: 62.2%     Tổng PnL: +12.50 USDT
Thắng: 28        Avg Win: +0.65 USDT  Profit Factor: 2.1
Thua: 17         Avg Loss: -0.42      Expected Value: +0.22
```

Chúc bạn sử dụng dashboard hiệu quả! 🚀
