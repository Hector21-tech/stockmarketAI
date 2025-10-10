# Phase 5 Backtest Plan

## Smart Observation by User: "Men kan vi inte hämta data baklänges och test?" 🎯

**Absolutely!** Vi kan bygga historisk percentil-data genom att scanna marknaden baklänges!

---

## Implementation

### 1. **build_percentile_history.py**

Bygger 30+ dagar rolling percentil-historik genom att scanna varje trading day:

```python
from build_percentile_history import build_history

# Build history for 2024
start = datetime(2023, 12, 1)  # 30d buffer before 2024
end = datetime(2024, 12, 31)
sizer = build_history(start, end)
```

**Process:**
1. Scanna OMX30 för varje trading day (2023-12-01 → 2024-12-31)
2. Spara scores i percentile_history.json
3. Bygg 30-day rolling window

**Performance:**
- ~250 trading days × 29 stocks
- ~5-10 minuter total tid
- Sparar persistent historik

### 2. **Phase 5 Backtest Workflow**

Med historisk data kan vi nu köra riktig Phase 5 backtest:

```python
# Step 1: Build historical percentile data
sizer = build_history(start_date, end_date)

# Step 2: For each backtest day:
for date in trading_days:
    # Scan market
    results = scanner.scan_market(date)

    # Calculate percentile-based sizes
    for stock in results:
        percentile = sizer.get_percentile(stock['score'], date)
        stock['size'] = sizer.calculate_position_size(stock['score'], date)

    # Apply Top-N override
    results = mapper.apply_top_n_override(results, top_n=3)

    # Execute trades with percentile sizes
    ...
```

---

## Expected Results

### Phase 3 (Baseline):
- **CAGR:** +5.1%
- **Absolute thresholds:** conf ≥65 = Full, ≥50 = Half, ≥35 = Quarter
- **Problem:** Can't adapt to regime

### Phase 5 (Percentile-Based):
- **CAGR Target:** 8-12%
- **Adaptive thresholds:** Top 20% = Full, 20-40% = Half, 40-60% = Quarter
- **Benefits:** Adapts to bull/bear automatically

### Key Improvements:
1. **Quarter positions:** 77% → 25-35% (better capital utilization)
2. **Half/Full positions:** 23% → 50-65% (higher exposure to winners)
3. **Opportunity selection:** Always picks top-ranked stocks relative to market

---

## Files Created:

1. **build_percentile_history.py** (130 lines)
   - Historical data builder
   - Scans market backwards
   - Builds 30d rolling window

2. **percentile_history.json** (generated)
   - 250+ days of OMX30 scores
   - Used for percentile calculations during backtest

---

## Usage:

### Build History:
```bash
cd backend
python build_percentile_history.py
# Takes 5-10 minutes
# Outputs: percentile_history.json
```

### Run Phase 5 Backtest:
```python
# Coming next: phase5_backtest.py
# Will use percentile_history.json for adaptive sizing
```

---

## Status:

✅ History builder implemented
⏳ Building 2024 data now (in progress...)
⏳ Phase 5 backtest script (next step)
⏳ Comparison: Phase 3 vs Phase 5 (coming)

---

**Insight:** User's suggestion to "hämta data baklänges" was the key to validating Phase 5 WITHOUT waiting 30 days in production! 🎯
