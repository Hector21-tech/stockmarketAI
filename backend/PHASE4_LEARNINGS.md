# Phase 4: Adaptive Sizing & Exit Strategy - Learnings

**Date:** 2025-10-09
**Goal:** Increase CAGR from 5.1% to 8-12% through adaptive position sizing and better exits

## Changes Implemented:

### 1. Softened Regime Penalties (`confidence_calculator.py`)
**Before (Phase 3):**
- VIX >30: -25 points
- VIX >25: -15 points
- Bear market: -20 points
- Bearish macro: -15 points

**After (Phase 4):**
- VIX ≥28: -15 points (only extreme panic)
- VIX >22: -5 points
- Confirmed bear (SPX <-5% from 200MA): -12 points
- Bearish macro: -2 to -8 points (only if confirmed bear)

**Rationale:** Only penalize in EXTREME bear conditions, not regular volatility.

### 2. ATR-Based 2-Stage Trailing Stop (`backtester.py`)
**Implementation:**
- **Stage 1:** Initial trail = max(1.5×ATR, 1.2% of entry)
  - Trails current price (not highest)
  - Protects capital with volatility-adjusted stop

- **Stage 2:** Activated when profit ≥ 1.5R (1.5× initial risk)
  - Trail = 2.2×ATR under highest price
  - Locks in profits while allowing trend to run

**Code:** New `_calculate_atr()` method + dynamic stop updates in `_check_exits()`

### 3. Lower Confidence Thresholds (REVERTED)
**Attempted:**
- Full: 80→75, 65→60
- Half: 50→45
- Quarter: 35→30

**Result:** TOO MANY low-quality entries (27 vs 14 trades, 51.9% vs 64.3% win rate)

**REVERTED to Phase 3 thresholds** - softer penalties alone gave enough extra signals.

---

## Test Results: Phase 3 vs Phase 4

### VOLVO-B 2024 (Full Year Backtest)

**Phase 3 (Baseline):**
- Final: 102,440 SEK (+2.44%)
- Trades: 14
- Win Rate: 64.3%
- Position Sizes: 64.3% Quarter, 35.7% Half
- Exit Reasons: Fixed stop loss + fixed targets

**Phase 4 Revised (Softer penalties + ATR trailing):**
- Final: 99,926 SEK (-0.07%)
- Trades: 27 (↑93% more trades!)
- Win Rate: 51.9% (↓12.4pp)
- Position Sizes: 92.6% Quarter (!), 7.4% Half
- Exit Reasons:
  - 44.4% STOP_LOSS
  - 25.9% TARGET_1
  - 14.8% TRAILING_STOP ✅ (new!)
  - 7.4% TARGET_2
  - 3.7% TARGET_3

**Improvement:** **-2.51 percentage points** (WORSE!)

---

## Root Cause Analysis:

### Why Phase 4 Failed:

1. **Softer penalties → More signals**
   - Higher confidence scores across the board
   - More entries passing threshold
   - But NOT higher quality entries!

2. **Quarter position overload**
   - 92.6% Quarter positions (up from 64.3%)
   - Even with softer penalties, most signals still marginal
   - Small position sizes = small gains, full-sized losses when stopped

3. **Trailing stop works but can't compensate**
   - 4 TRAILING_STOP exits (14.8%) - feature works!
   - But too many bad entries to offset

4. **Missing the key insight: PERCENTILE-BASED SIZING**
   - Absolute thresholds (confidence ≥50 = Half) don't adapt to market regime
   - In bull market: Top 10 stocks might all score 65-75 → all get Half/Full
   - In bear market: Top 10 might score 35-45 → all get Quarter
   - We need RELATIVE ranking, not absolute scores!

---

## What We Learned:

### ✅ What Worked:
1. **ATR-based trailing stop** - Technical implementation solid
2. **2-stage stop logic** - Correctly identifies 1.5R profit and tightens trail
3. **Softer penalties** - Correctly reduces over-penalization in moderate volatility

### ❌ What Didn't Work:
1. **Absolute confidence thresholds** - Don't adapt to market regime
2. **Softening penalties alone** - Creates more noise, not more quality
3. **Single-stock backtest** - Can't test percentile-based sizing properly

### 🎯 What's Missing (User Was Right!):

**1. Percentile-Based Position Sizing** (Top priority!)
```python
# Pseudo-code for future implementation:
def calculate_position_size(score, daily_all_scores):
    percentile = np.percentile(daily_all_scores, score)

    if percentile >= 80:  # Top 20%
        return 'full'
    elif percentile >= 60:  # Top 40%
        return 'half'
    elif percentile >= 40:  # Top 60%
        return 'quarter'
    else:
        return 'skip'
```

**Benefits:**
- Adapts to market regime automatically
- Always finds the BEST opportunities relative to current conditions
- In bull market: Higher bar for Full (more competition)
- In bear market: Lower bar for Full (best of bad options)

**Requirements:**
- Market-wide scanner (all OMX30 stocks)
- Daily ranking system
- 30-day rolling window for percentile calculation

**2. Top-N Override** (Prevents missing best setups)
```python
# Top-3 daily signals get minimum Half position
if daily_rank <= 3 and not near_earnings():
    position_size = max(position_size, 'half')
```

**With sector correlation cap:**
- Max 2 positions from same sector
- Diversification constraint

**3. Momentum Boost for Acceleration**
- If price +8% in <5 days → temporarily lower trail
- Catches parabolic moves

---

## Phase 4 Verdict: **INCOMPLETE**

### What We Delivered:
- ✅ Softer regime penalties
- ✅ ATR-based 2-stage trailing stop (technical implementation)
- ✅ Feature flag for Phase 3 vs Phase 4 comparison

### What We Didn't Deliver (But Should):
- ❌ Percentile-based position sizing (requires market scanner)
- ❌ Top-N override (requires daily ranking)
- ❌ Sector correlation cap (requires market-wide data)

### Recommendation:
**Phase 4 is technically solid but strategically incomplete.**

To achieve 8-12% CAGR targets:
1. Keep ATR trailing stop (good exit strategy)
2. Keep softened penalties (reduces over-cautiousness)
3. **MUST ADD:** Percentile-based sizing + Top-N override
4. **MUST ADD:** Market-wide scanner for daily ranking

**Next Steps:**
- Implement `market_scanner.py` for OMX30 daily scoring
- Add percentile calculation with 30d rolling window
- Add Top-N override logic in position sizing
- Add sector correlation tracking
- Re-test Phase 4 with complete system

---

## Code Changes:

### Files Modified:
1. `backend/confidence_calculator.py`
   - Softened VIX penalties (lines 42-52)
   - Softened bear market penalties (lines 54-73)
   - Softened macro regime penalties (lines 75-93)

2. `backend/backtester.py`
   - Added `use_trailing_stop` parameter (line 19)
   - Added `_calculate_atr()` method (lines 109-133)
   - Updated entry logic with ATR calculation (lines 317-367)
   - Implemented 2-stage trailing stop in `_check_exits()` (lines 380-449)

3. `backend/PHASE4_LEARNINGS.md` (this file)

### Feature Flags:
```python
# Enable Phase 4 features
bt = Backtester(
    ticker='VOLVO-B',
    mode='ai-hybrid',
    use_trailing_stop=True  # Phase 4: ATR-based trailing
)

# Disable for Phase 3 baseline
bt = Backtester(
    ticker='VOLVO-B',
    mode='ai-hybrid',
    use_trailing_stop=False  # Phase 3: Fixed stops
)
```

---

## Performance Target (Not Met):

| Metric | Phase 3 | Phase 4 Target | Phase 4 Actual | Status |
|--------|---------|----------------|----------------|--------|
| CAGR | +5.1% | 8-12% | -0.07% | ❌ MISS |
| Quarter-size % | 77% | 25-35% | 92.6% | ❌ WORSE |
| Half/Full % | 23% | 60-70% | 7.4% | ❌ WORSE |
| Max DD | ~8% | 12-18% | N/A | - |
| Win Rate | 64% | 65-75% | 51.9% | ❌ WORSE |

**Conclusion:** Phase 4 implementation is incomplete. Trailing stop works, but **percentile-based sizing is THE critical missing piece** to achieve targets.

---

**Author:** Claude Code + User Analysis
**Status:** Implemented but Incomplete (needs market scanner)
**Next Phase:** Phase 5 - Market Scanner + Percentile Sizing
