#!/bin/bash
# Script cài đặt dependencies cho bot trading

echo "🔧 Đang cài đặt dependencies..."

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt. Vui lòng cài Python 3.7+ trước."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Cài đặt pip nếu chưa có
if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3 chưa có. Đang cài đặt..."
    python3 -m ensurepip --upgrade
fi

# Cài đặt dependencies
echo "📦 Đang cài đặt từ requirements.txt..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cài đặt thành công!"
    echo ""
    echo "📝 Các bước tiếp theo:"
    echo "1. Cấu hình API key (xem README.md hoặc TESTNET_GUIDE.md)"
    echo "2. Chạy: python3 check_api.py (kiểm tra kết nối)"
    echo "3. Chạy: python3 main1.py (chạy bot)"
else
    echo ""
    echo "❌ Có lỗi khi cài đặt. Vui lòng kiểm tra lại."
    exit 1
fi
