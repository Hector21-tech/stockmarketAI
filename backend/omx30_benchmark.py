"""
OMX30 Strategy Benchmark
Tests all three signal modes (Conservative, Aggressive, AI-Hybrid)
across all OMX30 stocks to find the best performing strategy.
"""

import json
from datetime import datetime
from backtester import Backtester
from tickers import OMX30_TICKERS

# Configuration
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"
INITIAL_CAPITAL = 100000
MODES = ["conservative", "aggressive", "ai-hybrid"]

def run_benchmark():
    """Run complete benchmark across all OMX30 stocks and modes"""

    print("=" * 80)
    print("OMX30 STRATEGY BENCHMARK")
    print("=" * 80)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Capital: {INITIAL_CAPITAL:,} SEK")
    print(f"Stocks: {len(OMX30_TICKERS)}")
    print(f"Modes: {', '.join(MODES)}")
    print(f"Total backtests: {len(OMX30_TICKERS) * len(MODES)}")
    print("=" * 80)
    print()

    # Store all results
    all_results = {
        "config": {
            "start_date": START_DATE,
            "end_date": END_DATE,
            "initial_capital": INITIAL_CAPITAL,
            "timestamp": datetime.now().isoformat()
        },
        "results": []
    }

    # Run backtests
    total_tests = len(OMX30_TICKERS) * len(MODES)
    current_test = 0

    for ticker in OMX30_TICKERS:
        print(f"\n[{ticker}]")

        for mode in MODES:
            current_test += 1
            progress = (current_test / total_tests) * 100

            try:
                # Run backtest
                bt = Backtester(
                    ticker=ticker,
                    market='SE',
                    start_date=START_DATE,
                    end_date=END_DATE,
                    initial_capital=INITIAL_CAPITAL,
                    mode=mode
                )
                result = bt.run()

                # Extract key metrics
                metrics = result['metrics']

                # Store result
                all_results["results"].append({
                    "ticker": ticker,
                    "mode": mode,
                    "total_return": metrics.get("total_return", 0),
                    "cagr": metrics.get("cagr", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "total_trades": metrics.get("total_trades", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "final_value": metrics.get("final_value", INITIAL_CAPITAL)
                })

                # Print progress
                print(f"  {mode:12s}: Return {metrics.get('total_return', 0):+6.1f}%, "
                      f"Trades {metrics.get('total_trades', 0):3d}, "
                      f"Win Rate {metrics.get('win_rate', 0):5.1f}% "
                      f"[{progress:5.1f}%]")

            except Exception as e:
                print(f"  {mode:12s}: ERROR - {str(e)[:50]}")
                all_results["results"].append({
                    "ticker": ticker,
                    "mode": mode,
                    "error": str(e)
                })

    # Save raw results
    output_file = "omx30_backtest_results_2024.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    # Generate summary
    generate_summary(all_results)

    return all_results

def generate_summary(results):
    """Generate summary statistics and rankings"""

    print("\n")
    print("=" * 80)
    print("SUMMARY & RANKINGS")
    print("=" * 80)

    # Filter out errors
    valid_results = [r for r in results["results"] if "error" not in r]

    if not valid_results:
        print("No valid results to analyze!")
        return

    # 1. Mode Comparison
    print("\n1. MODE COMPARISON (Average Performance)")
    print("-" * 80)

    mode_stats = {}
    for mode in MODES:
        mode_results = [r for r in valid_results if r["mode"] == mode]

        if mode_results:
            avg_return = sum(r["total_return"] for r in mode_results) / len(mode_results)
            avg_win_rate = sum(r["win_rate"] for r in mode_results) / len(mode_results)
            avg_trades = sum(r["total_trades"] for r in mode_results) / len(mode_results)
            avg_sharpe = sum(r["sharpe_ratio"] for r in mode_results) / len(mode_results)
            avg_drawdown = sum(r["max_drawdown"] for r in mode_results) / len(mode_results)

            mode_stats[mode] = {
                "avg_return": avg_return,
                "avg_win_rate": avg_win_rate,
                "avg_trades": avg_trades,
                "avg_sharpe": avg_sharpe,
                "avg_drawdown": avg_drawdown,
                "count": len(mode_results)
            }

            print(f"\n{mode.upper()}")
            print(f"  Avg Return:    {avg_return:+7.2f}%")
            print(f"  Avg Win Rate:  {avg_win_rate:7.2f}%")
            print(f"  Avg Trades:    {avg_trades:7.1f}")
            print(f"  Avg Sharpe:    {avg_sharpe:7.2f}")
            print(f"  Avg Drawdown:  {avg_drawdown:7.2f}%")
            print(f"  Tested Stocks: {len(mode_results)}")

    # Determine best mode
    best_mode = max(mode_stats.items(), key=lambda x: x[1]["avg_return"])
    print(f"\n** BEST MODE: {best_mode[0].upper()} (Avg Return: {best_mode[1]['avg_return']:+.2f}%) **")

    # 2. Top 10 Stocks (by return, any mode)
    print("\n\n2. TOP 10 STOCKS (Best Performance)")
    print("-" * 80)

    # Find best result for each stock
    stock_best = {}
    for result in valid_results:
        ticker = result["ticker"]
        if ticker not in stock_best or result["total_return"] > stock_best[ticker]["total_return"]:
            stock_best[ticker] = result

    # Sort by return
    top_stocks = sorted(stock_best.values(), key=lambda x: x["total_return"], reverse=True)[:10]

    for i, stock in enumerate(top_stocks, 1):
        print(f"{i:2d}. {stock['ticker']:10s} {stock['total_return']:+7.2f}% "
              f"({stock['mode']:12s}) - {stock['total_trades']:3d} trades, "
              f"{stock['win_rate']:5.1f}% win rate")

    # 3. Worst 5 Stocks
    print("\n\n3. WORST 5 STOCKS")
    print("-" * 80)

    worst_stocks = sorted(stock_best.values(), key=lambda x: x["total_return"])[:5]

    for i, stock in enumerate(worst_stocks, 1):
        print(f"{i}. {stock['ticker']:10s} {stock['total_return']:+7.2f}% "
              f"({stock['mode']:12s}) - {stock['total_trades']:3d} trades")

    # 4. Mode-specific winners
    print("\n\n4. BEST STOCKS PER MODE")
    print("-" * 80)

    for mode in MODES:
        mode_results = [r for r in valid_results if r["mode"] == mode]
        if mode_results:
            best_for_mode = max(mode_results, key=lambda x: x["total_return"])
            print(f"\n{mode.upper()}")
            print(f"  Best: {best_for_mode['ticker']} ({best_for_mode['total_return']:+.2f}%)")
            print(f"  Trades: {best_for_mode['total_trades']}, Win Rate: {best_for_mode['win_rate']:.1f}%")

    # 5. Trading Activity
    print("\n\n5. TRADING ACTIVITY")
    print("-" * 80)

    for mode in MODES:
        mode_results = [r for r in valid_results if r["mode"] == mode]
        if mode_results:
            total_trades = sum(r["total_trades"] for r in mode_results)
            avg_trades_per_stock = total_trades / len(mode_results)
            print(f"{mode:12s}: {total_trades:4d} total trades ({avg_trades_per_stock:.1f} avg per stock)")

    print("\n")
    print("=" * 80)

if __name__ == "__main__":
    results = run_benchmark()
    print("\nBenchmark complete!")
