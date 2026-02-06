# Fix lỗi -2015 Invalid API-key

## Lỗi
```
Lỗi: -2015 Invalid API-key, IP, or permissions for action
```

## Nguyên nhân
1. API key không đúng (sai key/secret)
2. API key từ mainnet nhưng đang dùng testnet (hoặc ngược lại)
3. API key chưa bật quyền "Enable Futures"
4. IP bị chặn (có IP whitelist)

## Giải pháp

### Bước 1: Kiểm tra config TESTNET

Mở `config.py`, xem:
```python
TESTNET = True  # Nếu True → cần API key từ TESTNET
```

### Bước 2: Lấy API key đúng

**Nếu `TESTNET = True`:**
1. Truy cập: https://testnet.binancefuture.com
2. Đăng nhập → API Management
3. Tạo API key mới (hoặc dùng key cũ)
4. **Chỉ bật:** ✅ Enable Futures
5. Copy API key và Secret

**Nếu `TESTNET = False`:**
1. Truy cập: https://www.binance.com
2. Đăng nhập → API Management
3. Tạo API key mới
4. **Chỉ bật:** ✅ Enable Futures
5. Copy API key và Secret

### Bước 3: Cấu hình API key

**Cách 1: Biến môi trường (khuyến nghị)**
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_secret_here"
```

**Cách 2: File keys.py**
Mở `keys.py`, điền:
```python
api = "your_api_key_here"
secret = "your_secret_here"
```

### Bước 4: Kiểm tra IP whitelist

- Nếu API key có IP whitelist, thêm IP hiện tại của bạn
- Testnet thường không yêu cầu IP whitelist

### Bước 5: Test lại

```bash
python check_api.py
```

Kết quả mong đợi:
```
1) Balance USDT:
   ✅ balance: 10000.0 | available: 10000.0
```

## Checklist

- [ ] API key từ đúng nguồn (testnet nếu TESTNET=True, mainnet nếu TESTNET=False)
- [ ] Đã bật "Enable Futures"
- [ ] Không bật "Enable Withdrawals" (bảo mật)
- [ ] API key và secret đúng (không có khoảng trắng thừa)
- [ ] IP whitelist (nếu có) đã thêm IP hiện tại
- [ ] Đã chạy `python check_api.py` và thấy ✅ balance

## Lưu ý

- **Testnet và Mainnet dùng API key khác nhau!**
- API key testnet chỉ dùng được trên testnet
- API key mainnet chỉ dùng được trên mainnet
- Không thể dùng API key testnet trên mainnet và ngược lại
