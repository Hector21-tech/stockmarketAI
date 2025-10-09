# Strategy Optimization Learnings

**Date:** 2025-10-09
**Objective:** Improve trading strategy performance from baseline +2.57% to target +8-12%

---

## Baseline Performance (OMX30 Benchmark)

Tested all 3 modes across 29 OMX30 stocks (2024-01-01 to 2025-01-01):

| Mode | Avg Return | Win Rate | Best Performer |
|------|-----------|----------|----------------|
| **Conservative** | +1.38% | 61.5% | ERIC-B (+9.2%) |
| **Aggressive** | **+2.57%** | 57.0% | ERIC-B (+17.5%) |
| **AI-Hybrid** | +2.17% | 58.4% | ERIC-B (+13.1%) |

**Baseline Winner:** Aggressive mode (+2.57%)

---

## Phase 1: Parameter Optimization ❌

**Hypothesis:** Optimal stop loss, targets, thresholds, and weights will improve performance.

**Method:**
- Grid search: 1440 possible combinations
- Tested 100 random samples
- Parameters: stop_loss (0.8%-3.0%), target_multiplier (0.8x-1.8x), min_score (1.5-4.0), weights
- Optimization target: Sharpe Ratio
- Test stocks: Top 10 performers (ERIC-B, ABB, SAND, BOL, EVO, ALFA, VOLVO-B, ATCO-B, HUS-B, SKF-B)

**Best Configuration Found:**
```json
{
  "stop_loss_buffer": 0.03,  // 3.0%
  "target_multiplier": 1.8,
  "buy_threshold": 4.0,
  "tech_weight": 0.85,
  "macro_weight": 0.15
}
```

**Results:**
- Avg Return: **+1.53%** (vs baseline +2.57%)
- Avg Sharpe: 3.04
- Win Rate: 54.4%
- **IMPROVEMENT: -1.04%** ❌

**Conclusion:**
- Parameter tuning ALONE cannot fix the strategy
- The issue is not the parameters, but the fundamental approach
- Too many false signals leading to stop losses

---

## Phase 2: Volume + ADX Enhancement ❌

**Hypothesis:** Adding volume and ADX filters will reduce low-quality trades.

### Approach 1: Scoring (FAILED)

Added points for high volume and strong ADX:
- +2 points if volume > 150% avg
- +1 point if volume > 120% avg
- +2 points if ADX > 25
- +1 point if ADX > 20

**Results:**
- Conservative: **-3.50%** (vs baseline +1.38%) → -4.88% worse ❌
- Aggressive: **-2.85%** (vs baseline +2.57%) → -5.42% worse ❌

**Problem:** Adding points INCREASED trades (20-30 vs 10-15 baseline), leading to more losses.

### Approach 2: Filters (FAILED)

Used volume and ADX as minimum requirements:
- Filter out if volume < 80% avg (too thin)
- Filter out if ADX < 15 (too choppy)

**Results:**
- Conservative: **-1.78%** (vs baseline +1.38%) → -3.16% worse ❌
- Aggressive: **-2.65%** (vs baseline +2.57%) → -5.22% worse ❌

**Problem:** Filters reduced bad trades but not enough. Stock-specific performance varied wildly.

**Individual Stock Performance (Phase 2 Filters):**
| Stock | Return | Trades | Win Rate | Assessment |
|-------|--------|--------|----------|------------|
| ABB | **+15.0%** | 14 | 71.4% | Excellent ✓ |
| ERIC-B | **+7.4%** | 19 | 63.2% | Good ✓ |
| SAND | +1.5% | 14 | 57.1% | Marginal |
| BOL | **-10.3%** | 27 | 51.9% | Bad ✗ |
| EVO | **-26.6%** | 29 | 34.5% | Disaster ✗ |

**Key Insight:** EVO had 29 trades with only 34.5% win rate, dragging down the average.

---

## Root Cause Analysis

### Why Parameter Optimization Failed
1. **Stop losses trigger too often** - Markets are volatile, 1-3% stops get hit frequently
2. **Entry quality is poor** - Technical signals alone aren't enough (RSI, MACD produce many false positives)
3. **No market context** - Strategy trades in all conditions (bull, bear, high VIX)

### Why Volume/ADX Filters Failed
1. **Filters too lenient** - ADX > 15 still allows choppy markets
2. **No macro awareness** - Doesn't avoid bear markets or sector downtrends
3. **Stock-specific issues** - Some stocks (EVO, BOL) performed terribly regardless of filters

---

## Key Learnings

### ✅ What Works
1. **ABB is a star performer** - +15% with 71% win rate (consistent across all tests)
2. **ERIC-B is reliable** - +7-17% across different modes
3. **1/3 exit strategy works** - When winning, targets are hit in sequence
4. **Conservative mode has higher win rate** - But lower returns

### ❌ What Doesn't Work
1. **Parameter tuning alone** - Can't fix fundamental strategy flaws
2. **Volume/ADX scoring** - Adding points creates MORE trades (bad)
3. **Lenient filters** - ADX > 15, volume > 0.8x are too permissive
4. **Trading all conditions** - Need to avoid bear markets and high volatility

### 🔍 Core Issues
1. **Too many trades** - 15-30 trades/year per stock is excessive
2. **Low win rates** - 34-57% is not sustainable (need 60%+)
3. **Stop losses cluster** - Many sequential losses indicate poor entries
4. **No macro filter** - Strategy doesn't know when NOT to trade

---

## Next Steps: Phase 3 (Market Regime Filter)

**Hypothesis:** Only trade when macro conditions are favorable.

**Implementation:**
```python
def should_trade(ticker, market='SE'):
    """
    Check if market conditions are favorable for trading

    Returns: True if ALL conditions met:
    1. SPX > 200-day MA (bull market)
    2. VIX < 25 (low volatility)
    3. Macro Score > 0 (positive regime)
    4. Sector not in severe downtrend
    """
    # Fetch macro data
    macro = get_macro_data()

    # Check bull market
    if macro['spx_vs_ma200'] < 0:
        return False  # Bear market

    # Check volatility
    if macro['vix'] > 25:
        return False  # Too volatile

    # Check macro regime
    if macro['macro_score'] <= 0:
        return False  # Bearish macro

    return True
```

**Expected Improvement:**
- Reduce trades by 30-50% (only trade in favorable conditions)
- Increase win rate to 65%+ (better timing)
- Avoid disaster periods like EVO's -26.6%

**Target Metrics:**
- Avg Return: +5-8%
- Win Rate: 65%+
- Max Drawdown: <15%
- Sharpe Ratio: >2.0

---

## Alternative Approaches (Future)

If Phase 3 doesn't reach target, consider:

### Phase 4: AI-Hybrid Enhancement
- Gemini API news sentiment (-5 to +5)
- Earnings calendar awareness
- Sector rotation detection
- Pattern recognition (H&S, Double Bottom, etc.)

### Phase 5: Exit Strategy Improvements
- Trailing stops (protect profits)
- ATR-based dynamic targets (adapt to volatility)
- Signal-based early exits (MACD bearish crossover = exit)

### Phase 6: Stock-Specific Optimization
- Whitelist only high-performers (ABB, ERIC-B, SAND)
- Blacklist disasters (EVO, TELIA, HM-B)
- Sector-based parameter tuning

---

## Success Criteria

**Minimum Acceptable Performance:**
- Avg Return: +5%
- Win Rate: 60%+
- Sharpe Ratio: >1.5

**Target Performance:**
- Avg Return: +8-12%
- Win Rate: 65%+
- Sharpe Ratio: >2.0
- Max Drawdown: <15%

**Stretch Goal:**
- Avg Return: +15%+
- Win Rate: 70%+
- Sharpe Ratio: >3.0

---

## Files Created

1. `parameter_optimizer.py` - Grid search optimization engine
2. `parameter_optimization_results.json` - Full results (100 tests)
3. `optimal_parameters_2024.json` - Best config found
4. `phase2_test.py` - Volume/ADX enhancement tester
5. `phase2_test_results.json` - Phase 2 results
6. `OPTIMIZATION_LEARNINGS.md` - This document

---

**Last Updated:** 2025-10-09
**Next Action:** Implement Phase 3 (Market Regime Filter)
**Status:** Phase 1 & 2 complete, both unsuccessful. Moving to Phase 3.
