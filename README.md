# ⭐ Morning Star / Evening Star — NIFTY Options Strategy
**Balfund Trading Pvt. Ltd.**

> Automated candlestick pattern detection + options trade execution on NIFTY via Dhan API v2

---

## 📦 What's included

| File | Purpose |
|------|---------|
| `gui_app.py` | **Main entry point** — CustomTkinter GUI |
| `main.py` | Strategy orchestrator (WebSocket + threads) |
| `config.py` | All configurable parameters |
| `pattern_detector.py` | Morning Star / Evening Star detection logic |
| `strike_selector.py` | Delta-0.6 strike selection via Dhan scrip master |
| `order_manager.py` | Order placement via dhanhq SDK |
| `trade_tracker.py` | Active trade / signal / P&L tracking |
| `session_guard.py` | IST time gates (09:29 → 15:15) |
| `dhan_token_manager.py` | TOTP-based Dhan access token auto-generation |

---

## 🖥️ Quick Start (Windows EXE)

1. **Download** `MorningStarStrategy.exe` from the [Releases](../../releases) page
2. Run the EXE — no Python required
3. On first launch, go to **🔑 Token Manager** tab:
   - Enter **Client ID** (10-digit from web.dhan.co)
   - Enter **Trading PIN** (4-digit)
   - Enter **TOTP Secret** (from web.dhan.co → Profile → API Access → Enable TOTP)
   - Click **⚡ Generate Token** → then **💾 Save to .env**
4. Go to **📊 Dashboard** tab
5. Ensure **Paper Mode** is ON (yellow toggle)
6. Click **▶ Start Strategy**

---

## 🔑 Dhan TOTP Setup

```
1. Log in to web.dhan.co
2. Go to: Profile → API Access → Enable TOTP
3. You'll see a QR code AND a text secret (e.g. LETTKFDCQGROS...)
4. Copy the text secret → paste into "TOTP Secret" field in GUI
```

The token manager will auto-generate fresh tokens daily at 08:00 AM IST.

---

## ⚙️ Strategy Parameters

All parameters live in `config.py` and can be edited from the **⚙️ Settings** tab in the GUI.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PAPER_TRADE` | `True` | Paper mode (no real orders) |
| `TARGET_DELTA` | `0.60` | Approximate delta for strike selection |
| `SESSION_START_TIME` | `09:29` | No trades before this |
| `LAST_ENTRY_TIME` | `14:45` | No new entries after this |
| `FORCE_EXIT_TIME` | `15:15` | Close all positions |
| `LARGE_BODY_RATIO` | `0.60` | C1/C3 body must be ≥ 60% of range |
| `SMALL_BODY_RATIO` | `0.35` | C2 body must be ≤ 35% of range |
| `ENTRY_BUFFER_OPTIONS` | `1.0` | Points above/below C3 high/low for entry |
| `RISK_REWARD_RATIO` | `1.5` | TP = entry ± (1.5 × risk) |
| `MAX_TRADES_PER_DAY` | `5` | Daily trade cap |
| `LOT_SIZE` | `75` | NIFTY lot size |

---

## 🌅 Pattern Logic

### Morning Star (Bullish Reversal → Buy CE)
```
C1: Strong bearish candle  (body ≥ 60% of range)
C2: Small body / doji      (body ≤ 35% of range, low < C1 & C3 lows)
C3: Strong bullish candle  (body ≥ 60%, close > midpoint of C1 body)
Entry: break above C3 high + 1pt buffer
SL:   lowest low of all 3 candles
TP:   entry + 1.5 × risk
```

### Evening Star (Bearish Reversal → Buy PE)
```
C1: Strong bullish candle  (body ≥ 60% of range)
C2: Small body / doji      (body ≤ 35% of range, high > C1 & C3 highs)
C3: Strong bearish candle  (body ≥ 60%, close < midpoint of C1 body)
Entry: break below C3 low − 1pt buffer
SL:   highest high of all 3 candles
TP:   entry − 1.5 × risk
```

---

## 🏗️ Building from Source

### Prerequisites
```bash
python -m pip install -r requirements.txt
```

### Run GUI directly
```bash
python gui_app.py
```

### Build Windows EXE locally
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "MorningStarStrategy" \
  --add-data ".env;." \
  --add-data "config.py;." \
  --add-data "pattern_detector.py;." \
  --add-data "session_guard.py;." \
  --add-data "strike_selector.py;." \
  --add-data "order_manager.py;." \
  --add-data "trade_tracker.py;." \
  --add-data "dhan_token_manager.py;." \
  --add-data "main.py;." \
  --collect-all customtkinter \
  --collect-all dhanhq \
  gui_app.py
```

### Build via GitHub Actions
Push a version tag to trigger an automatic release build:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 📂 Repository Structure

```
├── gui_app.py               ← GUI entry point (this is the exe)
├── main.py                  ← Strategy engine
├── config.py                ← Parameters
├── pattern_detector.py      ← Candlestick pattern logic
├── strike_selector.py       ← Options strike selection
├── order_manager.py         ← Dhan order placement
├── trade_tracker.py         ← Trade state management
├── session_guard.py         ← Time gate logic
├── dhan_token_manager.py    ← TOTP token auto-generation
├── requirements.txt
├── .env                     ← Credentials (not committed)
├── assets/
│   └── icon.ico             ← App icon (optional)
└── .github/
    └── workflows/
        └── build_exe.yml    ← CI/CD build pipeline
```

---

## ⚠️ Disclaimer

This software is for educational and informational purposes only. Trading in options involves substantial risk. Always start in **Paper Mode** and verify signal behaviour before enabling live trading. Balfund Trading Pvt. Ltd. is not responsible for financial losses.

---

*Built with ❤️ using Python · CustomTkinter · Dhan API v2*
