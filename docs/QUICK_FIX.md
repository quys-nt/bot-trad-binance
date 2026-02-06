# Fix lỗi "No module named 'binance.um_futures'"

## Vấn đề
```
Lỗi import: No module named 'binance.um_futures'
```

## Nguyên nhân
Package name sai trong `requirements.txt`. Cần dùng `binance-futures-connector` chứ không phải `binance-connector`.

## Giải pháp

### Bước 1: Gỡ package cũ (nếu đã cài)
```bash
# Kích hoạt venv trước
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Gỡ package sai
pip uninstall binance-connector -y
```

### Bước 2: Cài đúng package
```bash
# Đảm bảo đang trong venv (thấy (venv) ở đầu dòng)
pip install binance-futures-connector
```

### Bước 3: Hoặc cài lại tất cả
```bash
pip install -r requirements.txt
```

### Bước 4: Kiểm tra
```bash
python -c "from binance.um_futures import UMFutures; print('✅ OK')"
```

Nếu thấy `✅ OK` → đã fix!

## Lưu ý
- Đảm bảo đã kích hoạt venv: `source venv/bin/activate`
- Package đúng: `binance-futures-connector` (có chữ "futures")
- Package sai: `binance-connector` (không có "futures")
