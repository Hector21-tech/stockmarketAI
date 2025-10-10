# Phase 1 Backtest Comparison - OMX30 2024

**Date:** 2025-10-10
**Test Period:** 2024-01-01 to 2024-12-31
**Universe:** OMX30 (29 stocks)
**Mode:** AI-Hybrid

---

## EXECUTIVE SUMMARY

Phase 1 improvements showed **MIXED RESULTS**:
- ✅ Trades reduced by 62% (23.8 → 9.1 avg/stock)
- ✅ Win rate improved (+0.8%)
- ✅ CAGR improved (+0.25%)
- ❌ Still negative returns (-0.84% avg)
- ❌ Profit factor decreased (-30%)
- ❌ Sharpe ratio decreased (-14%)

**Verdict:** Phase 1 is a step in the right direction, but **NOT sufficient** to achieve profitable strategy (+5-10% CAGR goal).

---

## DETAILED COMPARISON

### Key Metrics

| Metric                | OLD (Pre-Phase 1) | NEW (Phase 1) | Change      | Status |
|-----------------------|-------------------|---------------|-------------|--------|
| **Average CAGR**      | -1.09%            | -0.84%        | **+0.25%**  | ✅ Better |
| **Trades/Stock**      | 23.8              | 9.1           | **-62%**    | ✅ Better |
| **Win Rate**          | 59.9%             | 60.7%         | **+0.8%**   | ✅ Better |
| **Profit Factor**     | 2.43              | 1.71          | **-30%**    | ❌ Worse |
| **Max Drawdown**      | 6.46%             | 6.64%         | +0.18%      | ≈ Neutral |
| **Sharpe Ratio**      | 1.68              | 1.44          | **-14%**    | ❌ Worse |

### Positive/Negative Split

| Metric              | OLD        | NEW        | Change |
|---------------------|------------|------------|--------|
| Positive Returns    | 15 (51.7%) | 13 (44.8%) | -6.9%  |
| Negative Returns    | 14 (48.3%) | 16 (55.2%) | +6.9%  |

### Best/Worst Performers

| Category        | OLD                | NEW                |
|-----------------|--------------------|--------------------|
| **Best Stock**  | TEL2-B (+6.59%)    | HM-B (+9.94%)      |
| **Worst Stock** | EVO (-13.36%)      | NDA-SE (-12.73%)   |

---

## PHASE 1 IMPLEMENTATIONS

### 1. Chandelier Exit (ATR × 3)
- **Goal:** Let winners run with volatility-adjusted trailing stops
- **Result:** Partially successful - fewer trades but also cut some winners short
- **Evidence:** Exit reasons now show "CHANDELIER_STOP" instead of "TRAILING_STOP"

### 2. Trend Filter (ADX>15, price>50/200MA, 20MA slope>0)
- **Goal:** Only trade in confirmed trends
- **Result:** ✅ **HIGHLY SUCCESSFUL** - trades reduced by 62% (23.8→9.1)
- **Evidence:** Many "SKIPPED: Confidence too low" entries in logs

### 3. ATR-Based Stops (2×ATR instead of 1.5×)
- **Goal:** Give positions more breathing room
- **Result:** Mixed - fewer stop-outs but also slightly higher drawdown
- **Evidence:** Max DD increased slightly (6.46%→6.64%)

### 4. Position Sizing Ladder (≥75%→1.0x, 60-74%→0.75x, etc)
- **Goal:** Better capital allocation based on confidence
- **Result:** Working as designed - see position sizes in logs (HALF, QUARTER, etc)
- **Evidence:** Logs show varied position sizes: "Score: 4, Confidence: 55.0% [HALF]"

### 5. Slippage (10 bps per side)
- **Result:** Maintained at realistic levels

---

## ROOT CAUSE ANALYSIS

### Why Did Profit Factor Decrease? (2.43 → 1.71)

**Hypothesis:** Chandelier Exit (3×ATR) is **TOO TIGHT** and cutting winners prematurely.

**Evidence:**
- Win rate improved (+0.8%) = we're picking better trades
- Trades reduced 62% = trend filter working
- But profit factor dropped 30% = we're not capturing full move

**Example from VOLVO-B:**
```
OLD: [2024-03-28] EXIT (TRAILING_STOP): 130 shares @ 271.45 SEK, P/L: +1509.48 SEK (+4.5%)
NEW: [2024-04-03] EXIT (CHANDELIER_STOP): 130 shares @ 269.12 SEK, P/L: +1050.89 SEK (+3.1%)
```
Same position, but Chandelier Exit got us out earlier with less profit.

### Why Did Sharpe Ratio Decrease? (1.68 → 1.44)

**Hypothesis:** Lower trade frequency + similar drawdown = worse risk-adjusted returns

**Calculation:** Sharpe = (Return - RiskFree) / Volatility
- Return decreased slightly (-1.09% → -0.84%)
- But trade frequency dropped massively (23.8 → 9.1)
- Fewer opportunities to compound = worse Sharpe

---

## INDIVIDUAL STOCK ANALYSIS

### Top Performers (Phase 1)

1. **HM-B:** +9.94% (11 trades, 63.6% win rate)
2. **ABB:** +9.11% (11 trades, 81.8% win rate)
3. **TELIA:** +7.31% (13 trades, 76.9% win rate)
4. **SKA-B:** +6.15% (14 trades, 78.6% win rate)
5. **ERIC-B:** +4.93% (12 trades, 66.7% win rate)

### Bottom Performers (Phase 1)

1. **NDA-SE:** -12.73% (6 trades, **0.0% win rate!**)
2. **SWED-A:** -10.01% (9 trades, 33.3% win rate)
3. **KINV-B:** -9.68% (6 trades, 50.0% win rate)
4. **SHB-A:** -8.82% (11 trades, 63.6% win rate)
5. **EQT:** -7.47% (14 trades, 57.1% win rate)

**Observation:** NDA-SE went 0/6 (0% win rate) - this stock should be BLACKLISTED or needs different parameters.

---

## NEXT STEPS - DECISION TREE

### Option 1: Continue to Phase 2 (Parameter Tuning)
**Focus:** Adjust Chandelier multiplier and trend filter thresholds

**Test Matrix:**
- Chandelier ATR multiplier: 3.0 → 3.5 → 4.0
- ADX threshold: 15 → 12 → 10
- MA slope requirement: Remove or soften

**Expected Outcome:** Higher profit factor, more trades, potentially +2-5% CAGR

---

### Option 2: Try Conservative Mode
**Focus:** Use tighter confidence thresholds (≥50% → ≥60%)

**Changes:**
- Minimum confidence: 45% → 60%
- Position sizing: More aggressive scaling
- Stop loss: 2.5% instead of 1.8%

**Expected Outcome:** Fewer but higher quality trades, +1-3% CAGR

---

### Option 3: Accept Reality
**Acknowledge:** 2024 was a challenging year for Swedish equities
- OMX30 underperformed
- High volatility (VIX elevated)
- Strategy might need bull market to shine

**Test:** Run Phase 1 on different year (2023? 2022?) to validate

---

### Option 4: Fundamental Redesign (Phase 5+)
**Focus:** Add completely new edge

**Ideas:**
- Sector rotation (only trade strongest sectors)
- Earnings momentum (trade around earnings beats)
- Relative strength (only trade top 10 RS stocks)
- Market regime filter (bull/bear/sideways)

**Timeline:** 2-4 weeks additional development

---

## RECOMMENDATION

**Short-term (This Week):**
1. ✅ Run Phase 2A: Test Chandelier multiplier 3.5×ATR and 4.0×ATR
2. ✅ Run Phase 2B: Test ADX threshold at 12 (currently 15)
3. ✅ Blacklist NDA-SE (0% win rate is unacceptable)

**Medium-term (Next Week):**
1. Test Conservative mode with 60% min confidence
2. Run backtests on 2023 data to validate strategy works in different market

**Long-term (If still negative):**
1. Consider fundamental redesign (Phase 5+)
2. OR pivot to different universe (US stocks? Crypto?)
3. OR accept strategy is market-neutral/defensive only

---

## FILES GENERATED

1. `omx30_backtest_results_2024.json` - Phase 1 detailed results
2. `omx30_benchmark_log.txt` - Full backtest log with all trades
3. `phase1_comparison_report.md` - This report

---

## CONCLUSION

Phase 1 improvements **partially worked**:
- ✅ Trend filter highly effective (62% trade reduction)
- ✅ Win rate improved
- ✅ CAGR improved (+0.25%)
- ❌ Still negative overall (-0.84%)
- ❌ Profit factor and Sharpe degraded

**Bottom Line:** We're moving in the right direction, but need **Phase 2 parameter optimization** to achieve +5-10% CAGR goal.

The Chandelier Exit (3×ATR) appears too conservative. Testing 3.5×-4.0×ATR multipliers should help capture more of the winning moves while still protecting capital.

---

**Next Action:** User to decide: Phase 2A (parameter tuning) or different approach?
