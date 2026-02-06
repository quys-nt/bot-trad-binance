# Hướng dẫn nhanh - Fix lỗi "ModuleNotFoundError"

## Vấn đề
```
ModuleNotFoundError: No module named 'pandas'
```

## Giải pháp: Dùng Virtual Environment

### Cách 1: Chạy script tự động (khuyến nghị)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Cách 2: Setup thủ công

**Bước 1: Tạo virtual environment**
```bash
python3 -m venv venv
```

**Bước 2: Kích hoạt venv**

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

Sau khi kích hoạt, bạn sẽ thấy `(venv)` ở đầu dòng terminal.

**Bước 3: Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

**Bước 4: Chạy bot**
```bash
python check_api.py    # Kiểm tra kết nối
python main1.py        # Chạy bot
```

## Lưu ý quan trọng

⚠️ **Mỗi lần mở terminal mới**, bạn cần kích hoạt lại venv:
```bash
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

Nếu không kích hoạt, sẽ gặp lại lỗi `ModuleNotFoundError`.

## Kiểm tra đã cài đúng chưa

```bash
# Kích hoạt venv
source venv/bin/activate

# Kiểm tra
python -c "import pandas; print('✅ pandas OK')"
python -c "import ta; print('✅ ta OK')"
python -c "from binance.um_futures import UMFutures; print('✅ binance OK')"
```

Nếu thấy 3 dòng ✅ → đã cài đúng!

## Troubleshooting

**Lỗi: "python3: command not found"**
- Cài Python 3.7+ từ https://www.python.org

**Lỗi: "No module named 'venv'"**
- Cài: `python3 -m pip install --user virtualenv`
- Hoặc dùng: `python3 -m virtualenv venv`

**Lỗi: "pip: command not found"**
- Cài pip: `python3 -m ensurepip --upgrade`

**Lỗi kết nối khi cài (network error)**
- Kiểm tra internet
- Thử lại: `pip install -r requirements.txt --timeout 60`
