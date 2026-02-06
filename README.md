# Bot Futures – Bản an toàn, quản lý rủi ro

## Cấu trúc thư mục

```
binance-futures-bot/
├── main.py              # Entry point - chạy bot
├── config.py            # Cấu hình chính
├── keys_loader.py       # Load API key (env hoặc keys.py)
├── db.py, notify.py     # Database, thông báo
├── strategies.py        # Chiến lược giao dịch
├── scripts/             # Tiện ích
│   ├── check_api.py     # Kiểm tra API
│   ├── backtest.py      # Backtest
│   ├── sync_db.py       # Đồng bộ trades mồ côi
│   ├── analyze_simple.py
│   └── performance_analyzer.py
├── bot/                 # Zalo Bot
│   └── server.py        # Webhook nhận tin Zalo
├── dashboard/           # Dashboard Streamlit
│   └── app.py           # Đóng lệnh thủ công, PnL realtime
├── configs/             # Config presets
│   └── small_capital.py
├── docs/                # Tài liệu
└── tests/               # Test
```

---

## Cài đặt

> ⚠️ **Nếu gặp lỗi `ModuleNotFoundError: No module named 'pandas'`**, xem [docs/QUICK_START.md](docs/QUICK_START.md)

### Bước 1: Setup môi trường

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

**Hoặc setup thủ công:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## Cấu hình nhanh

### Test trên Testnet (KHUYẾN NGHỊ)

1. **Lấy API Key:** https://testnet.binancefuture.com → API Management → Create API
2. **Cấu hình:** `export BINANCE_API_KEY=...` và `export BINANCE_API_SECRET=...`
3. **Bật Testnet:** Trong `config.py` đặt `TESTNET = True`
4. **Kiểm tra:** `python scripts/check_api.py`
5. **Chạy:** `python main.py`

👉 **Chi tiết:** [docs/TESTNET_GUIDE.md](docs/TESTNET_GUIDE.md)

### Chạy Mainnet (tiền thật)

1. API Key từ https://www.binance.com → API Management
2. `config.py` → `TESTNET = False`
3. ⚠️ **Bot sẽ dùng tiền thật!**

---

## Lệnh thường dùng

| Lệnh | Mô tả |
|------|-------|
| `python main.py` | Chạy bot trading |
| `python scripts/check_api.py` | Kiểm tra API |
| `python scripts/backtest.py --symbol BTCUSDT --days 60` | Backtest |
| `python scripts/sync_db.py` | Đồng bộ trades mồ côi |
| `python scripts/analyze_simple.py` | Phân tích đơn giản |
| `python scripts/performance_analyzer.py` | Phân tích chi tiết |
| `streamlit run dashboard/app.py` | Dashboard (đóng lệnh thủ công) |
| `python -m bot.server` | Zalo Bot webhook |

---

## Backtesting

```bash
python scripts/backtest.py --symbol BTCUSDT --days 60 [--strategy multi]
python scripts/backtest.py --csv klines.csv [--strategy multi]
```

- `--strategy`: `multi` (mặc định), `rsi`, `macd`

---

## Dashboard

```bash
streamlit run dashboard/app.py
```

- Balance, win rate, PnL
- Đóng lệnh thủ công trước TP/SL
- PnL ước tính realtime

---

## Zalo Bot

```bash
python -m bot.server
```

Lệnh: `/balance`, `/pos`, `/status`, `/stop`, `/help`

👉 [docs/ZALO_BOT_GUIDE.md](docs/ZALO_BOT_GUIDE.md)

---

## Tài liệu

| File | Nội dung |
|------|----------|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Hướng dẫn nhanh |
| [docs/QUICK_FIX.md](docs/QUICK_FIX.md) | Fix lỗi thường gặp |
| [docs/FIX_API_KEY.md](docs/FIX_API_KEY.md) | Fix lỗi API key |
| [docs/TESTNET_GUIDE.md](docs/TESTNET_GUIDE.md) | Hướng dẫn Testnet |
| [docs/DASHBOARD_GUIDE.md](docs/DASHBOARD_GUIDE.md) | Hướng dẫn Dashboard |
| [docs/ZALO_BOT_GUIDE.md](docs/ZALO_BOT_GUIDE.md) | Hướng dẫn Zalo Bot |
| [docs/ROADMAP_SMALL_CAPITAL.md](docs/ROADMAP_SMALL_CAPITAL.md) | Config vốn nhỏ |

---

## Quản lý rủi ro

- **Drawdown:** Dừng khi lỗ từ đỉnh ≥ `MAX_DRAWDOWN_PCT`
- **Lỗ trong ngày:** Dừng khi ≥ `DAILY_LOSS_LIMIT_PCT`
- **Thua liên tiếp:** Dừng sau `MAX_CONSECUTIVE_LOSSES` lệnh

## Chiến lược

- `STRATEGY = 'multi'` (mặc định): RSI + StochRSI + EMA 200
- `'rsi'`, `'macd'`, `'bookmap'`

## Phụ thuộc

- `binance-futures-connector`, `pandas`, `ta`
- `streamlit` (dashboard), `requests` (Telegram/Discord/Zalo)
