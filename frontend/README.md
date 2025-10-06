# MarketsAI - React Native App

AI-driven aktieanalys baserad på Marketmate-strategin.

## Installation

### 1. Installera dependencies
```bash
cd frontend
npm install
```

### 2. Starta utvecklingsservern
```bash
npm start
```

### 3. Kör appen
- **Android**: `npm run android` eller skanna QR-koden i Expo Go-appen
- **iOS**: `npm run ios` (kräver macOS)
- **Web**: `npm run web`

## Konfiguration

### Backend URL
Uppdatera backend URL i `src/api/client.js`:

```javascript
// For Android emulator
const API_BASE_URL = 'http://10.0.2.2:5000/api';

// For fysisk enhet (andras till din dators IP)
const API_BASE_URL = 'http://192.168.1.46:5000/api';
```

För att hitta din dators IP:
- **Windows**: `ipconfig` (leta efter "IPv4 Address")
- **Mac/Linux**: `ifconfig` (leta efter "inet")

## Funktioner

### 📊 Watchlist
- Lagg till upp till 30 aktier
- Se realtidspriser
- Swipe for att ta bort

### 🎯 Kopsignaler
- AI-analyserar alla aktier i watchlist
- Visar endast aktier med kopsignal
- Entry, Stop Loss, Targets (1/3-regeln)
- Score och RSI

### 💼 Positioner
- Tracka dina oppna positioner
- Automatiska notiser for 1/3-exits
- Realtids P/L
- Exit-historik

### ⚙️ Installningar
- API-status
- Prenumeration (50 kr/manad)
- Marketmate-strategi

## Projektstruktur

```
frontend/
├── App.js                    # Main app entry
├── package.json             # Dependencies
├── app.json                 # Expo config
└── src/
    ├── api/
    │   └── client.js        # API client
    └── screens/
        ├── WatchlistScreen.js
        ├── SignalsScreen.js
        ├── PositionsScreen.js
        └── SettingsScreen.js
```

## Backend

Se backend README for att starta backend-servern:
```bash
cd backend
python app.py
```

Backend maste kora pa http://localhost:5000 for att appen ska fungera.

## Troubleshooting

### "Network Error"
- Kontrollera att backend-servern kor
- Verifiera att API_BASE_URL ar korrekt
- Testa backend: `curl http://localhost:5000/api/health`

### "Cannot connect to server"
- Om du kor pa fysisk enhet, anvand datorns IP (inte localhost)
- Kontrollera att firewall tillater port 5000

## Naasta steg

- [ ] Implementera Google Play Billing
- [ ] Push notifications for trade-signaler
- [ ] Offline-support
- [ ] Dark mode
- [ ] Grafer/charts
