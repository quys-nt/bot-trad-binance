# Hướng dẫn tích hợp Zalo Bot với Bot Trading

Hướng dẫn chi tiết để kết nối Zalo Bot với bot trading, cho phép bạn:
- **Nhận thông báo** qua Zalo khi bot mở/đóng lệnh hoặc dừng
- **Điều khiển bot** qua tin nhắn Zalo (xem balance, vị thế, dừng bot)

---

## Bước 1: Cấu hình .env

Thêm vào file `.env` (đã có `ZALO_BOT_TOKEN`):

```
ZALO_BOT_TOKEN=your_token_here
```

**Lưu ý:** 
- Token format thường là `app_id:secret` (vd: `1636785030370890134:xxx...`)
- Nếu dùng **Zalo OA (Official Account)** và có access_token riêng, dùng biến `ZALO_OA_ACCESS_TOKEN`
- `ZALO_USER_ID` **không cần** thêm thủ công – sẽ được lưu tự động khi bạn nhắn bot lần đầu

---

## Bước 2: Cài đặt dependencies

```bash
pip install flask requests
# hoặc
pip install -r requirements.txt
```

---

## Bước 3: Chạy Zalo Bot Server (webhook)

Server webhook nhận tin nhắn từ Zalo và xử lý lệnh.

```bash
python zalo_bot_server.py
```

Server chạy tại `http://0.0.0.0:5000`. Webhook URL: `http://YOUR_IP:5000/zalo-webhook`

### Expose ra internet (bắt buộc để Zalo gửi webhook)

Zalo cần gửi webhook tới URL **công khai (HTTPS)**. Cách đơn giản:

#### Option A: Ngrok (phát triển / test)

1. Cài [ngrok](https://ngrok.com/)
2. Chạy:
   ```bash
   ngrok http 5000
   ```
3. Copy URL dạng `https://xxxx.ngrok-free.app` → Webhook URL: `https://xxxx.ngrok-free.app/zalo-webhook`

#### Option B: Deploy lên server (production)

- Dùng VPS (DigitalOcean, AWS, v.v.) với domain và HTTPS (Let's Encrypt)
- Reverse proxy (nginx) forward `/zalo-webhook` tới `localhost:5000`

---

## Bước 4: Đăng ký Webhook trên Zalo Developer

1. Vào [Zalo Developers](https://developers.zalo.me/)
2. Chọn ứng dụng / OA của bạn
3. Vào mục **Webhook** hoặc **Chatbot**
4. Nhập **Callback URL**: `https://YOUR_NGROK_OR_DOMAIN/zalo-webhook`
5. Nếu có **Verify Token** hoặc **Secret**, ghi lại (có thể cần cấu hình thêm trong code)
6. Lưu cấu hình

---

## Bước 5: Kết nối với Zalo và lấy ZALO_USER_ID

1. Mở **Zalo** trên điện thoại
2. Tìm và nhắn tin cho **Official Account / Chatbot** của bạn
3. Gửi bất kỳ tin nhắn nào (vd: `hi` hoặc `/help`)
4. Server sẽ:
   - Lưu `user_id` của bạn vào `zalo_state.json`
   - Trả lời danh sách lệnh
5. Từ giờ `notify.send_zalo()` sẽ gửi thông báo tới Zalo của bạn

---

## Các lệnh điều khiển

Gửi tin nhắn tới Zalo Bot:

| Lệnh | Mô tả |
|------|-------|
| `/balance` | Xem số dư USDT |
| `/pos` | Xem vị thế đang mở |
| `/status` | Trạng thái bot |
| `/stop` | Gửi tín hiệu dừng bot |
| `/help` | Xem hướng dẫn |

---

## Chạy Bot Trading kèm Zalo

**Terminal 1 – Zalo Bot Server:**
```bash
python zalo_bot_server.py
```

**Terminal 2 – Bot Trading:**
```bash
python main1.py
```

Bot trading sẽ:
- Gửi thông báo (mở/đóng lệnh, dừng) qua Zalo nếu đã có `ZALO_USER_ID`
- Đọc lệnh `/stop` từ file `bot_commands.json` mỗi vòng lặp và dừng khi nhận lệnh

---

## Lưu ý quan trọng

### Token Zalo OA vs Zalo Chatbot (zapps)

- **Zalo OA (Official Account):** API `openapi.zalo.me` dùng access_token. Access token thường hết hạn sau 1 giờ, cần flow refresh. Nếu bạn dùng OA, có thể cần tích hợp OAuth/refresh token.
- **Zalo Chatbot (zapps):** Token dạng `app_id:secret` thường dùng trực tiếp. Nếu token của bạn không hoạt động với `openapi.zalo.me`, có thể bạn đang dùng nền tảng khác (vd: zapps) – khi đó cần kiểm tra tài liệu API của nền tảng đó.

### Bảo mật

- Không commit `.env`, `zalo_state.json`, `bot_commands.json` vào git (đã có trong .gitignore)
- Webhook nên chạy qua HTTPS
- Chỉ bạn (user_id đã lưu) mới nhận được thông báo và điều khiển bot

### Xử lý lỗi

- Nếu không nhận được tin nhắn: kiểm tra webhook URL, token, và log của `zalo_bot_server.py`
- Nếu gửi thông báo không được: kiểm tra `zalo_state.json` đã có `user_id` chưa (nhắn bot ít nhất 1 lần)
- Nếu API trả lỗi: xem mã lỗi trong tài liệu Zalo OA / nền tảng bạn dùng

---

## Cấu trúc file

```
notify.py           # Thêm send_zalo(), dùng cho thông báo
zalo_bot_server.py  # Webhook server nhận tin Zalo
zalo_state.json     # Lưu user_id (tự tạo khi nhắn bot)
bot_commands.json   # Lệnh từ Zalo (vd: stop) cho main1 đọc
main1.py            # Đọc bot_commands, gửi notify.send()
```

---

## Tóm tắt quy trình

1. Thêm `ZALO_BOT_TOKEN` vào `.env`
2. Cài Flask: `pip install flask`
3. Chạy `python zalo_bot_server.py`
4. Dùng ngrok expose: `ngrok http 5000`
5. Đăng ký webhook URL trên Zalo Developers
6. Nhắn tin cho bot → lấy `user_id` tự động
7. Chạy `python main1.py` → nhận thông báo qua Zalo và có thể điều khiển bằng lệnh
