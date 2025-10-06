# MarketsAI - AI-Driven Stock Analysis App

En mobil trading-app baserad på **Marketmate-strategin** med AI-drivna köpsignaler och automatisk position management enligt 1/3-exit regeln.

## 🎯 Funktioner

### För Användare
- **Watchlist** - Bevaka upp till 30 aktier (svenska och amerikanska)
- **AI-Signaler** - Få köpsignaler baserade på RSI, MACD, Stochastic
- **Positionshantering** - Tracka positioner och få automatiska exit-notiser
- **1/3-Exit Regel** - Automatiska notiser för att sälja 1/3 vid targets
- **Realtidsdata** - Live priser från Yahoo Finance
- **Prenumeration** - 50 kr/månad

### För Utvecklare
- **Backend**: Python Flask REST API
- **Frontend**: React Native (Expo)
- **AI**: Marketmate-strategi implementation
- **Data**: Yahoo Finance API

## 🚀 Snabbstart

### 1. Backend (Python)

```bash
cd backend

# Installera dependencies
python -m pip install -r requirements.txt

# Starta servern
python app.py
```

Backend körs på: http://localhost:5000

### 2. Frontend (React Native)

```bash
cd frontend

# Installera dependencies
npm install

# Starta app
npm start
```

Scanna QR-koden med Expo Go-appen (Android/iOS).

## 📊 Marketmate-Strategin

Appen analyserar aktier enligt Marketmate-filosofin:

### Tre Grundpelare:
1. **Likviditet** - M2, Fed, räntor, penningmängd
2. **Sentiment** - AAII, Fear & Greed, positionering
3. **Teknisk struktur** - Mönster, divergenser, volym

### Entry-Kriterier:
- Positiv divergens i RSI
- MACD bullish crossover
- Stochastic oversold (<20) och vänder upp
- Pris över EMA20 (bullish trend)

### 1/3-Exit Regel:
1. **+3-5%** → Sälj 1/3, flytta stop till break-even
2. **Nästa motstånd** → Sälj 1/3, flytta stop under swing-low
3. **Sista 1/3** → Håll så länge trend kvarstår

### Risk Management:
- Max risk per trade: 1.5-2%
- Stop loss flyttas ALDRIG nedåt
- All handel mekanisk och repeterbar

## 🏗️ Arkitektur

```
MarketsAI/
├── backend/                    # Python Flask API
│   ├── app.py                 # Main API server
│   ├── stock_data.py          # Yahoo Finance integration
│   ├── technical_analysis.py  # RSI, MACD, Stochastic
│   ├── ai_engine.py           # Marketmate AI
│   ├── trade_manager.py       # Position & exit management
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React Native app
│   ├── App.js                 # Main app entry
│   ├── src/
│   │   ├── api/client.js      # Backend API client
│   │   └── screens/
│   │       ├── WatchlistScreen.js
│   │       ├── SignalsScreen.js
│   │       ├── PositionsScreen.js
│   │       └── SettingsScreen.js
│   └── package.json
│
└── Marketmate_Strategy_v2.txt  # Strategy documentation
```

## 📡 API Endpoints

### Stock Data
- `GET /api/stock/price?ticker=VOLVO-B&market=SE`
- `POST /api/stock/prices` - Flera aktier
- `GET /api/stock/info?ticker=VOLVO-B`

### AI Analysis
- `POST /api/analyze` - Analysera aktie
- `POST /api/scan` - Scanna watchlist
- `POST /api/signals/buy` - Köpsignaler

### Positions
- `GET /api/positions` - Alla positioner
- `POST /api/positions` - Lägg till position
- `GET /api/positions/check` - Kolla 1/3-exits
- `POST /api/positions/exit` - Registrera exit

Se `backend/API_DOCS.md` för komplett dokumentation.

## 🔧 Konfiguration

### Backend URL (frontend)
Uppdatera `frontend/src/api/client.js`:

```javascript
// Android emulator
const API_BASE_URL = 'http://10.0.2.2:5000/api';

// Fysisk enhet (byt till din IP)
const API_BASE_URL = 'http://192.168.1.46:5000/api';
```

### Svenska Aktier
Ticker-mappings finns i `backend/stock_data.py`:
- VOLVO-B → VOLV-B.ST
- HM-B → HM-B.ST
- ERIC-B → ERIC-B.ST

## 📱 Skärmbilder

### Watchlist
- Lägg till/ta bort aktier
- Se realtidspriser
- Max 30 aktier

### Köpsignaler
- AI-analyserade signaler
- Entry, Stop, Targets
- RSI, MACD, Score

### Positioner
- Öppna positioner
- Realtids P/L
- Exit-notiser (1/3-regeln)
- Exit-historik

### Inställningar
- API-status
- Prenumeration (50 kr/månad)
- Marketmate-strategi

## 🛠️ Tech Stack

**Backend:**
- Python 3.13
- Flask (REST API)
- yfinance (Yahoo Finance)
- pandas, numpy (Data analysis)
- ta (Technical Analysis)

**Frontend:**
- React Native (Expo)
- React Navigation
- Axios (API client)

**Data:**
- Yahoo Finance API (gratis, real-time)

## 🚧 Nästa Steg

### Kvar att implementera:
- [ ] Google Play Billing (prenumeration)
- [ ] Push notifications (trade-signaler)
- [ ] Grafer/charts
- [ ] Offline-support
- [ ] Dark mode

### Förbättringar:
- [ ] Mer svenska aktier i mappings
- [ ] Historisk performance tracking
- [ ] Portfolio analytics
- [ ] Social trading integration

## 📝 Licens

Detta projekt är skapat för utbildningsändamål.

## 🤝 Bidrag

Baserat på Marketmate-strategin och utvecklad med Claude Code.

---

**⚠️ Disclaimer:** Detta är INTE finansiell rådgivning. All trading innebär risk. Använd appen på egen risk.
