@echo off
REM Script setup virtual environment và cài đặt dependencies (Windows)

echo 🔧 Đang setup môi trường...

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt. Vui lòng cài Python 3.7+ trước.
    pause
    exit /b 1
)

echo ✅ Python version:
python --version

REM Tạo virtual environment nếu chưa có
if not exist "venv" (
    echo 📦 Đang tạo virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Không thể tạo venv.
        pause
        exit /b 1
    )
)

REM Kích hoạt venv
echo 🔌 Đang kích hoạt virtual environment...
call venv\Scripts\activate.bat

REM Nâng cấp pip
echo ⬆️  Đang nâng cấp pip...
python -m pip install --upgrade pip --quiet

REM Cài đặt dependencies
echo 📦 Đang cài đặt dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Có lỗi khi cài đặt. Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo.
echo ✅ Setup thành công!
echo.
echo 📝 Cách sử dụng:
echo 1. Kích hoạt venv: venv\Scripts\activate
echo 2. Cấu hình API key (xem README.md)
echo 3. Chạy: python check_api.py (kiểm tra kết nối)
echo 4. Chạy: python main1.py (chạy bot)
echo.
pause
