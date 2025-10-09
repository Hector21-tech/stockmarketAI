# Phase 5: Percentile-Based Position Sizing 🎯

**Date:** 2025-10-09
**Status:** ✅ Implemented & Tested (Requires 30d history for production)
**Goal:** Adaptive position sizing based on relative ranking, not absolute thresholds

---

## Problem with Phase 3/4 (Absolute Thresholds)

**Phase 3 Issue:**
```python
if confidence >= 65:  return 'full'   # Absolute threshold
elif confidence >= 50: return 'half'
elif confidence >= 35: return 'quarter'
```

**Why this fails:**
- **Bull market:** Top-10 stocks might all score 70-80 → ALL get Full (good!)
- **Bear market:** Top-10 stocks might score 35-45 → ALL get Quarter (bad!)
- **Result:** System can't adapt to market regime

**User's insight:** "Need RELATIVE ranking, not absolute scores!"

---

## Phase 5 Solution: Percentile-Based Sizing

### Core Concept:
```python
# Calculate where stock ranks RELATIVE to all others
percentile = np.percentile(all_market_scores, current_score)

if percentile >= 80:  return 'full'    # Top 20%
elif percentile >= 60: return 'half'   # Top 40%
elif percentile >= 40: return 'quarter'  # Top 60%
else: return 'none'                     # Bottom 40%
```

### Benefits:
- ✅ **Adapts to market regime** - Always finds best opportunities
- ✅ **Consistent exposure** - Always ~20% Full, ~20% Half, ~20% Quarter
- ✅ **No manual tuning** - Thresholds adjust automatically

---

## Architecture

### 1. Market Scanner (`market_scanner.py`)

**Purpose:** Score ALL OMX30 stocks daily

**Key Methods:**
- `scan_market(date)` → Scores all 29 OMX30 stocks
- `_score_stock()` → Technical analysis (RSI, MACD, volume, etc.)

**Output:** List of {ticker, score, confidence, price, rsi, ...}

**Performance:** ~30 seconds to scan entire OMX30

### 2. Percentile Sizer (`percentile_sizer.py`)

**Purpose:** Calculate percentiles with 30d rolling window

**Key Methods:**
- `add_daily_scores(date, scores)` → Add day's scores to history
- `get_percentile(score, date)` → Calculate score's percentile rank
- `calculate_position_size(score)` → Map percentile → size
- `get_window_stats()` → View current percentile thresholds

**Features:**
- 30-day rolling window
- 5-day smoothing (optional, prevents whipsaws)
- Persistent storage (JSON file)
- Adaptive thresholds

**Example:**
```python
sizer = PercentileSizer()

# Add daily market scan
sizer.add_daily_scores(today, scan_results)

# Calculate position size
percentile = sizer.get_percentile(score=7.5, date=today)
# → 85th percentile
size = sizer.calculate_position_size(score=7.5, date=today)
# → 'full' (top 20%)
```

### 3. Sector Mapper (`sector_mapper.py`)

**Purpose:** Top-N override + sector diversification

**Key Methods:**
- `get_sector(ticker)` → Maps ticker to sector (GICS-style)
- `apply_top_n_override(stocks, top_n=3, min_size='half')` → Top-3 get Half minimum
- `check_sector_diversification(positions)` → Check current portfolio
- `filter_by_sector_cap(signals, active_positions)` → Enforce max 2 per sector

**Sector Classification:**
- Financials: SEB-A, SHB-A, SWED-A, INVE-B
- Industrials: ABB, ALFA, VOLV-B, SKF-B, SKA-B (7 stocks)
- Technology: ERIC-B, HEXA-B, TEL2-B
- Healthcare: AZN, GETI-B
- Materials: BOL, SCA-B
- Consumer Discretionary: EVO, HM-B, ELUX-B
- Consumer Staples: ESSITY-B
- Energy: NIBE-B
- Communication Services: KINV-B

**Top-N Logic:**
- Top-3 signals get minimum 'half' size
- BUT respects sector cap (max 2 from same sector)
- If Top-3 has 3× Industrials → #3 gets skipped, #4 from different sector gets override

---

## Integration Test Results

**Test Date:** 2025-10-09
**Stocks Scanned:** 28/29 (SWMA delisted)

### Window Stats (First Day):
```
Data points: 28 (only today's data)
Mean score: 2.57
Percentile thresholds:
  80th (Full):    4.00
  60th (Half):    3.00
  40th (Quarter): 2.00
```

### Position Size Distribution:

| Size | Absolute (Phase 3) | Percentile (Phase 5) |
|------|-------------------|---------------------|
| **Full** | 1 (3.6%) | 1 (3.6%) |
| **Half** | 6 (21.4%) | 6 (21.4%) |
| **Quarter** | 16 (57.1%) | 7 (25.0%) ✅ |
| **None** | 5 (17.9%) | 14 (50.0%) ⚠️ |

**Analysis:**
- Quarter reduced from 57.1% → 25.0% ✅
- But None increased to 50% because only 1 day of data
- **After 30 days:** Distribution will stabilize to ~20/20/20/40

### Top Ranked Stocks:

| Rank | Ticker | Score | Percentile | Size | Sector |
|------|--------|-------|-----------|------|--------|
| 1 | KINV-B | 5.0 | 96.4% | **Full** | Comm Services |
| 2 | ABB | 4.0 | 75.0% | **Half** | Industrials |
| 3 | ALFA | 4.0 | 75.0% | **Half** | Industrials |
| 4 | BOL | 4.0 | 75.0% | **Half** | Materials |
| 5 | ERIC-B | 4.0 | 75.0% | **Half** | Technology |
| 6 | INVE-B | 4.0 | 75.0% | **Half** | Financials |

**Top-N Override:** 0 applied (all Top-3 already had Half or better)

---

## Usage

### Daily Workflow:

```python
from market_scanner import MarketScanner
from percentile_sizer import PercentileSizer
from sector_mapper import SectorMapper

# Initialize
scanner = MarketScanner(mode='ai-hybrid')
sizer = PercentileSizer()
mapper = SectorMapper()

# 1. Scan market
results = scanner.scan_market()

# 2. Add to history
sizer.add_daily_scores(datetime.now(), results)

# 3. Calculate percentile sizes
for stock in results:
    stock['percentile_size'] = sizer.calculate_position_size(
        stock['score'],
        datetime.now()
    )

# 4. Apply Top-N override
results = mapper.apply_top_n_override(results, top_n=3, min_size='half')

# 5. Filter by sector cap (if you have active positions)
active_positions = ['VOLV-B', 'ABB']  # Your current holdings
results = mapper.filter_by_sector_cap(results, active_positions)

# 6. Execute top signals
for signal in results[:5]:
    if signal['recommended_size'] != 'none':
        print(f"BUY {signal['ticker']}: {signal['recommended_size'].upper()} position")
```

---

## Files Created

### Core Modules:
1. **`market_scanner.py`** (288 lines)
   - Scans all OMX30 stocks
   - Returns scores + technical details

2. **`percentile_sizer.py`** (250 lines)
   - 30d rolling percentile calculation
   - Position size mapping
   - History persistence

3. **`sector_mapper.py`** (230 lines)
   - Sector classification (OMX30)
   - Top-N override logic
   - Diversification tracking

### Test & Documentation:
4. **`test_phase5_integration.py`** (179 lines)
   - Integration test for all 3 modules
   - Comparison: Absolute vs Percentile

5. **`PHASE5_README.md`** (this file)
   - Full documentation

### Data Files (Generated):
6. **`percentile_history.json`**
   - 30-day rolling score history
   - Auto-created on first run

---

## Comparison: Phase 3 vs Phase 5

| Feature | Phase 3 (Absolute) | Phase 5 (Percentile) |
|---------|-------------------|---------------------|
| **Thresholds** | Fixed (conf ≥65 = Full) | Adaptive (top 20% = Full) |
| **Market adaptation** | ❌ No | ✅ Yes |
| **Bull market** | Over-allocates | Optimal allocation |
| **Bear market** | Under-allocates | Finds best opportunities |
| **Top-N override** | ❌ No | ✅ Yes (min Half for Top-3) |
| **Sector cap** | ❌ No | ✅ Yes (max 2 per sector) |
| **History required** | No | 30 days for stability |

---

## Known Limitations

### 1. First 30 Days Bootstrap
- **Problem:** With <30 days data, percentiles are unstable
- **Solution:**
  - Use absolute thresholds as fallback for first 30 days
  - Or seed with simulated historical data

### 2. Delisted/Missing Stocks
- SWMA is delisted → not in scan
- Handle gracefully (skip, don't crash)

### 3. Performance
- Scanning 29 stocks takes ~30 seconds
- Consider caching if scanning multiple times per day

### 4. Market Hours
- Scanner uses most recent closing data
- Intraday scanning shows previous day's close

---

## Next Steps (Future Work)

### Phase 5.5: Historical Backtesting
- Build 30d history for 2024 period
- Backtest Phase 5 vs Phase 3
- Expected improvement: +3-5pp CAGR

### Phase 6: Live Integration
- Add Phase 5 to `/api/signals/buy` endpoint
- Frontend: Show percentile rank in UI
- Daily automated scans

### Phase 7: Advanced Features
- **Momentum boost:** If price +8% <5d → temporarily lower trail
- **Earnings filter:** Skip ±1d from earnings for Top-N
- **Correlation tracking:** Limit correlated positions (e.g., VOLV-B + SKF-B)

---

## Performance Expectations

Based on Phase 4 learnings and Phase 5 design:

| Metric | Phase 3 | Phase 5 Target |
|--------|---------|----------------|
| **CAGR** | +5.1% | **8-12%** |
| **Quarter %** | 77% | **25-35%** |
| **Half/Full %** | 23% | **50-65%** |
| **Win Rate** | 64% | 65-75% |
| **Max DD** | ~8% | 12-18% |

**Key Drivers:**
1. ✅ Higher capital utilization (more Half/Full)
2. ✅ Better opportunity selection (percentile ranking)
3. ✅ Top-N override prevents missing best setups
4. ✅ Sector diversification reduces concentration risk

---

## Conclusion

**Phase 5 Status:** ✅ **IMPLEMENTED & READY**

**What We Delivered:**
- ✅ Market scanner for OMX30
- ✅ Percentile-based position sizing
- ✅ Top-N override with sector cap
- ✅ Integration tested successfully
- ✅ Full documentation

**What's Missing:**
- ⏳ 30-day historical data build-up (for production use)
- ⏳ Historical backtest comparison (Phase 3 vs Phase 5)

**Recommendation:**
1. **Short-term:** Use Phase 3 as baseline
2. **Parallel run:** Start collecting percentile data (30 days)
3. **Switch:** After 30 days, switch to Phase 5 percentile-based sizing
4. **Monitor:** Compare Phase 3 vs Phase 5 performance live

---

**Author:** Claude Code + User
**Date:** 2025-10-09
**Next:** Build 30d history → Backtest → Deploy to production
