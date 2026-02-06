#!/bin/bash
# Script setup virtual environment và cài đặt dependencies

echo "🔧 Đang setup môi trường..."

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt. Vui lòng cài Python 3.7+ trước."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Tạo virtual environment nếu chưa có
if [ ! -d "venv" ]; then
    echo "📦 Đang tạo virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Không thể tạo venv. Kiểm tra: python3 -m venv --help"
        exit 1
    fi
fi

# Kích hoạt venv
echo "🔌 Đang kích hoạt virtual environment..."
source venv/bin/activate

# Nâng cấp pip
echo "⬆️  Đang nâng cấp pip..."
pip install --upgrade pip --quiet

# Cài đặt dependencies
echo "📦 Đang cài đặt dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup thành công!"
    echo ""
    echo "📝 Cách sử dụng:"
    echo "1. Kích hoạt venv: source venv/bin/activate"
    echo "2. Cấu hình API key (xem README.md)"
    echo "3. Chạy: python check_api.py (kiểm tra kết nối)"
    echo "4. Chạy: python main1.py (chạy bot)"
    echo ""
    echo "💡 Lưu ý: Mỗi lần mở terminal mới, cần chạy: source venv/bin/activate"
else
    echo ""
    echo "❌ Có lỗi khi cài đặt. Vui lòng kiểm tra lại."
    exit 1
fi
