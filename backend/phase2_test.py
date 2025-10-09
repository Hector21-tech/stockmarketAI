"""
Phase 2 Enhancement Test
Quick benchmark to validate volume + ADX improvements on top 5 stocks
"""

from backtester import Backtester
import json
from datetime import datetime

# Top 5 performers from OMX30 benchmark
TEST_STOCKS = ["ERIC-B", "ABB", "SAND", "BOL", "EVO"]

# Test period (same as original benchmark)
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"
INITIAL_CAPITAL = 100000
MODES = ["conservative", "aggressive"]

def run_phase2_test():
    """Quick test of Phase 2 improvements"""

    print("=" * 80)
    print("PHASE 2 ENHANCEMENT TEST (Volume + ADX)")
    print("=" * 80)
    print(f"Testing: {', '.join(TEST_STOCKS)}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Enhancement: Volume confirmation + ADX trend strength")
    print("=" * 80)
    print()

    results = {
        "timestamp": datetime.now().isoformat(),
        "enhancements": ["volume_scoring", "adx_scoring"],
        "results": []
    }

    total_tests = len(TEST_STOCKS) * len(MODES)
    current_test = 0

    for ticker in TEST_STOCKS:
        print(f"\n[{ticker}]")

        for mode in MODES:
            current_test += 1
            progress = (current_test / total_tests) * 100

            try:
                # Run backtest with Phase 2 enhancements
                bt = Backtester(
                    ticker=ticker,
                    market='SE',
                    start_date=START_DATE,
                    end_date=END_DATE,
                    initial_capital=INITIAL_CAPITAL,
                    mode=mode
                )

                result = bt.run()
                metrics = result['metrics']

                # Store result
                results["results"].append({
                    "ticker": ticker,
                    "mode": mode,
                    "total_return": metrics.get("total_return", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "total_trades": metrics.get("total_trades", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                })

                # Print progress
                print(f"  {mode:12s}: Return {metrics.get('total_return', 0):+6.1f}%, "
                      f"Trades {metrics.get('total_trades', 0):3d}, "
                      f"Win Rate {metrics.get('win_rate', 0):5.1f}% "
                      f"[{progress:5.1f}%]")

            except Exception as e:
                print(f"  {mode:12s}: ERROR - {str(e)[:50]}")
                results["results"].append({
                    "ticker": ticker,
                    "mode": mode,
                    "error": str(e)
                })

    # Save results
    output_file = "phase2_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    # Generate comparison
    analyze_results(results)

    return results


def analyze_results(results):
    """Compare Phase 2 results with original OMX30 benchmark"""

    print("\n")
    print("=" * 80)
    print("PHASE 2 RESULTS vs BASELINE")
    print("=" * 80)

    valid_results = [r for r in results["results"] if "error" not in r]

    if not valid_results:
        print("No valid results to analyze!")
        return

    # Calculate mode averages
    print("\nMODE COMPARISON:")
    print("-" * 80)

    for mode in MODES:
        mode_results = [r for r in valid_results if r["mode"] == mode]

        if mode_results:
            avg_return = sum(r["total_return"] for r in mode_results) / len(mode_results)
            avg_win_rate = sum(r["win_rate"] for r in mode_results) / len(mode_results)
            avg_trades = sum(r["total_trades"] for r in mode_results) / len(mode_results)
            avg_sharpe = sum(r["sharpe_ratio"] for r in mode_results) / len(mode_results)

            print(f"\n{mode.upper()} MODE (Phase 2 Enhanced)")
            print(f"  Avg Return:    {avg_return:+7.2f}%")
            print(f"  Avg Win Rate:  {avg_win_rate:7.2f}%")
            print(f"  Avg Trades:    {avg_trades:7.1f}")
            print(f"  Avg Sharpe:    {avg_sharpe:7.2f}")

    # Comparison with original benchmark
    print("\n\nCOMPARISON WITH BASELINE (Original OMX30):")
    print("-" * 80)

    # Original baseline results from OMX30 benchmark
    baseline = {
        "conservative": {"return": 1.38, "win_rate": 61.5},
        "aggressive": {"return": 2.57, "win_rate": 57.0},
    }

    for mode in MODES:
        mode_results = [r for r in valid_results if r["mode"] == mode]

        if mode_results:
            avg_return = sum(r["total_return"] for r in mode_results) / len(mode_results)
            avg_win_rate = sum(r["win_rate"] for r in mode_results) / len(mode_results)

            baseline_return = baseline[mode]["return"]
            baseline_win_rate = baseline[mode]["win_rate"]

            return_improvement = avg_return - baseline_return
            win_rate_improvement = avg_win_rate - baseline_win_rate

            print(f"\n{mode.upper()}:")
            print(f"  BASELINE:  Return {baseline_return:+.2f}%, Win Rate {baseline_win_rate:.1f}%")
            print(f"  PHASE 2:   Return {avg_return:+.2f}%, Win Rate {avg_win_rate:.1f}%")
            print(f"  IMPROVEMENT: Return {return_improvement:+.2f}%, Win Rate {win_rate_improvement:+.1f}%")

            if return_improvement > 0:
                print(f"  [+] Phase 2 shows improvement!")
            else:
                print(f"  [-] Phase 2 needs further tuning")

    # Best stock performance
    print("\n\nBEST PERFORMERS (Phase 2):")
    print("-" * 80)

    sorted_results = sorted(valid_results, key=lambda x: x["total_return"], reverse=True)

    for i, result in enumerate(sorted_results[:5], 1):
        print(f"{i}. {result['ticker']:10s} ({result['mode']:12s}): "
              f"{result['total_return']:+6.2f}%, "
              f"{result['total_trades']:3d} trades, "
              f"{result['win_rate']:5.1f}% win rate")

    print("\n")
    print("=" * 80)


if __name__ == "__main__":
    results = run_phase2_test()
    print("\nPhase 2 test complete!")
