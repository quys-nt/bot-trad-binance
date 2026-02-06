@echo off
REM Script cài đặt dependencies cho bot trading (Windows)

echo 🔧 Đang cài đặt dependencies...

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt. Vui lòng cài Python 3.7+ trước.
    pause
    exit /b 1
)

echo ✅ Python version:
python --version

REM Cài đặt dependencies
echo 📦 Đang cài đặt từ requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Có lỗi khi cài đặt. Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo.
echo ✅ Cài đặt thành công!
echo.
echo 📝 Các bước tiếp theo:
echo 1. Cấu hình API key (xem README.md hoặc TESTNET_GUIDE.md)
echo 2. Chạy: python check_api.py (kiểm tra kết nối)
echo 3. Chạy: python main1.py (chạy bot)
pause
