# MarketsAI REST API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Health Check
```
GET /health
```
Kollar att API:et fungerar

**Response:**
```json
{
  "status": "healthy",
  "service": "MarketsAI API",
  "version": "1.0.0"
}
```

---

### 2. Aktiedata

#### Hämta pris
```
GET /stock/price?ticker=VOLVO-B&market=SE
```

**Response:**
```json
{
  "ticker": "VOLVO-B",
  "price": 275.80,
  "market": "SE"
}
```

#### Hämta flera priser
```
POST /stock/prices
Content-Type: application/json

{
  "tickers": ["VOLVO-B", "HM-B", "ERIC-B"],
  "market": "SE"
}
```

**Response:**
```json
{
  "prices": {
    "VOLVO-B": 275.80,
    "HM-B": 178.65,
    "ERIC-B": 78.52
  },
  "market": "SE"
}
```

#### Hämta aktieinfo
```
GET /stock/info?ticker=VOLVO-B&market=SE
```

---

### 3. AI-Analys

#### Analysera aktie
```
POST /analyze
Content-Type: application/json

{
  "ticker": "VOLVO-B",
  "market": "SE"
}
```

**Response:**
```json
{
  "ticker": "VOLVO-B",
  "market": "SE",
  "analysis": {
    "price": 275.80,
    "rsi": 53.3,
    "rsi_status": "neutral",
    "macd": { ... },
    "support": 270.0,
    "resistance": 280.0
  },
  "signal": {
    "action": "BUY",
    "strength": "STRONG",
    "score": 7,
    "reasons": ["Positiv divergens i RSI", "MACD bullish crossover"],
    "summary": "Koplage. Positiv divergens i RSI. MACD bullish crossover."
  },
  "trade_setup": {
    "entry": 275.80,
    "stop_loss": 268.50,
    "targets": {
      "target_1": { "price": 286.83, "gain_percent": 4.0 },
      "target_2": { "price": 290.00, "gain_percent": 5.1 },
      "target_3": { "price": 317.17, "gain_percent": 15.0 }
    }
  }
}
```

#### Skanna watchlist
```
POST /scan
Content-Type: application/json

{
  "tickers": ["VOLVO-B", "HM-B", "ERIC-B"],
  "market": "SE"
}
```

#### Hämta köpsignaler
```
POST /signals/buy
Content-Type: application/json

{
  "tickers": ["VOLVO-B", "HM-B", "ERIC-B"],
  "market": "SE"
}
```

**Response:**
```json
{
  "signals": [
    {
      "ticker": "VOLVO-B",
      "signal": { ... },
      "trade_setup": { ... }
    }
  ],
  "count": 1
}
```

---

### 4. Positionshantering

#### Hämta alla positioner
```
GET /positions
```

**Response:**
```json
{
  "positions": [
    {
      "ticker": "VOLVO-B",
      "entry_price": 275.80,
      "current_shares": 300,
      "stop_loss": 268.50,
      "status": "OPEN"
    }
  ],
  "count": 1
}
```

#### Lägg till position
```
POST /positions
Content-Type: application/json

{
  "ticker": "VOLVO-B",
  "entry_price": 275.80,
  "shares": 300,
  "stop_loss": 268.50,
  "targets": {
    "target_1": { "price": 286.83, "gain_percent": 4.0 },
    "target_2": { "price": 290.00, "gain_percent": 5.1 },
    "target_3": { "price": 317.17, "gain_percent": 15.0 }
  },
  "market": "SE"
}
```

#### Kolla positioner (1/3-exits)
```
GET /positions/check
```

**Response:**
```json
{
  "notifications": [
    {
      "type": "TARGET_1",
      "ticker": "VOLVO-B",
      "action": "Sälj 100 st @ 286.83 (+4.0%)",
      "price": 286.83,
      "instruction": "Flytta stop loss till break-even",
      "new_stop": 275.80
    }
  ],
  "count": 1
}
```

#### Registrera exit
```
POST /positions/exit
Content-Type: application/json

{
  "ticker": "VOLVO-B",
  "shares": 100,
  "exit_price": 286.83,
  "exit_type": "TARGET_1"
}
```

#### Uppdatera stop loss
```
PUT /positions/stop-loss
Content-Type: application/json

{
  "ticker": "VOLVO-B",
  "new_stop": 275.80
}
```

---

### 5. Utility

#### Marknadsstatus
```
GET /market-status?market=SE
```

**Response:**
```json
{
  "market": "SE",
  "is_open": true
}
```

#### Hämta strategi
```
GET /strategy
```

---

## Error Responses

```json
{
  "error": "Error message"
}
```

**Status codes:**
- 200: Success
- 201: Created
- 400: Bad request
- 404: Not found
- 500: Internal server error
