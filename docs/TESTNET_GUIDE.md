# Hướng dẫn Test trên Binance Futures Testnet

## Bước 1: Lấy API Key từ Testnet

1. **Truy cập:** https://testnet.binancefuture.com
2. **Đăng nhập** (hoặc đăng ký nếu chưa có tài khoản testnet)
3. **Vào API Management:**
   - Click vào profile/avatar góc phải
   - Chọn "API Management" hoặc tìm mục API
4. **Tạo API Key mới:**
   - Click "Create API" hoặc "Generate API Key"
   - **Chỉ bật:** ✅ Enable Futures
   - **KHÔNG bật:** ❌ Enable Withdrawals
   - Copy **API Key** và **Secret Key** (chỉ hiện 1 lần, lưu lại ngay!)

## Bước 2: Cấu hình trong project

### Cách 1: Dùng biến môi trường (khuyến nghị)
```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_secret"
```

### Cách 2: Dùng file keys.py
1. Copy `keys.py.example` → `keys.py`
2. Điền API key và secret từ testnet:
```python
api = "your_testnet_api_key"
secret = "your_testnet_secret"
```

## Bước 3: Bật Testnet trong config

Mở `config.py`, đảm bảo:
```python
TESTNET = True  # True = testnet, False = mainnet (tiền thật)
```

## Bước 4: Kiểm tra kết nối

```bash
python check_api.py
```

Kết quả mong đợi:
- Balance: có số USDT testnet (thường ~10,000 USDT testnet)
- get_income: OK
- Open orders: OK

Nếu thấy log `🔧 Đang dùng TESTNET: https://testnet.binancefuture.com` → đúng!

## Bước 5: Chạy bot test

```bash
python main1.py
```

**Lưu ý:**
- Testnet có **10,000 USDT testnet** miễn phí để test
- Dữ liệu testnet **không ảnh hưởng** tài khoản thật
- Có thể test nhiều lần, reset balance nếu cần
- Giá trên testnet có thể khác mainnet (dùng dữ liệu test)

## Chuyển sang Mainnet (tiền thật)

1. **Tắt testnet:** Trong `config.py` đặt `TESTNET = False`
2. **Đổi API key:** Dùng API key từ **mainnet** (https://www.binance.com)
3. **Kiểm tra lại:** `python check_api.py` → phải thấy balance thật
4. **Cảnh báo:** Khi `TESTNET = False`, bot sẽ dùng **tiền thật**!

## Troubleshooting

**Lỗi: "Invalid API-key"**
- Kiểm tra API key đúng từ testnet (không phải mainnet)
- Đảm bảo đã bật "Enable Futures"

**Lỗi: "IP not whitelisted"**
- Testnet có thể không yêu cầu IP whitelist
- Nếu có, thêm IP hiện tại vào whitelist trên testnet

**Balance = 0**
- Testnet có thể reset balance định kỳ
- Đăng nhập lại testnet để kiểm tra balance

**Không thấy log "🔧 Đang dùng TESTNET"**
- Kiểm tra `config.TESTNET = True`
- Restart bot
