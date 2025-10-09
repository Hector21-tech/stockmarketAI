"""
Parameter Optimizer
Finds optimal trading parameters through grid search optimization.
Tests different combinations of stop loss, targets, thresholds, etc.
"""

import json
import itertools
from datetime import datetime
from backtester import Backtester
import numpy as np

# Test stocks (top performers from benchmark)
TEST_STOCKS = [
    "ERIC-B",  # Best performer
    "ABB",     # High win rate
    "SAND",    # Good return
    "BOL",     # Consistent
    "EVO",     # Strong
    "ALFA",    # Solid
    "VOLVO-B", # Stable
    "ATCO-B",  # Reliable
    "HUS-B",   # Good volume
    "SKF-B",   # Industrial
]

# Test period
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"
INITIAL_CAPITAL = 100000

# Parameter grid to search
PARAM_GRID = {
    # Stop loss percentages (as decimal for stop_loss_buffer)
    "stop_loss": [0.008, 0.010, 0.012, 0.015, 0.018, 0.020, 0.025, 0.030],

    # Target multipliers
    "target_multiplier": [0.8, 1.0, 1.2, 1.4, 1.6, 1.8],

    # Minimum buy score thresholds
    "min_score": [1.5, 2.0, 2.5, 3.0, 3.5, 4.0],

    # Weight combinations [tech, macro] (AI will be 1 - tech - macro for ai-hybrid)
    "weights": [
        (0.70, 0.30),  # Current conservative
        (0.85, 0.15),  # Current aggressive
        (0.75, 0.25),  # Balanced
        (0.80, 0.20),  # Tech-heavy
        (0.65, 0.35),  # Macro-heavy
    ]
}


def create_test_config(stop_loss, target_mult, min_score, tech_weight, macro_weight):
    """Create a test configuration"""
    return {
        "stop_loss_buffer": stop_loss,
        "target_multiplier": target_mult,
        "buy_threshold": min_score,
        "tech_weight": tech_weight,
        "macro_weight": macro_weight,
        "ai_weight": 0.0,  # For now, focus on tech/macro optimization
    }


def run_optimization(max_tests=100, target_metric="sharpe"):
    """
    Run parameter optimization

    Args:
        max_tests: Maximum number of parameter combinations to test
        target_metric: Metric to optimize ('sharpe', 'return', 'win_rate', 'profit_factor')
    """

    print("=" * 80)
    print("PARAMETER OPTIMIZATION")
    print("=" * 80)
    print(f"Test Stocks: {', '.join(TEST_STOCKS)}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Target Metric: {target_metric}")
    print(f"Max Tests: {max_tests}")
    print("=" * 80)
    print()

    # Generate all parameter combinations
    all_combinations = list(itertools.product(
        PARAM_GRID["stop_loss"],
        PARAM_GRID["target_multiplier"],
        PARAM_GRID["min_score"],
        PARAM_GRID["weights"]
    ))

    print(f"Total possible combinations: {len(all_combinations)}")

    # Sample if too many
    if len(all_combinations) > max_tests:
        import random
        random.seed(42)
        test_combinations = random.sample(all_combinations, max_tests)
        print(f"Sampling {max_tests} combinations...")
    else:
        test_combinations = all_combinations

    print()

    results = []
    total_tests = len(test_combinations) * len(TEST_STOCKS)
    current_test = 0

    # Test each combination
    for stop_loss, target_mult, min_score, (tech_w, macro_w) in test_combinations:

        config = create_test_config(stop_loss, target_mult, min_score, tech_w, macro_w)

        # Test on all stocks
        stock_results = []

        for ticker in TEST_STOCKS:
            current_test += 1
            progress = (current_test / total_tests) * 100

            try:
                # Create custom backtester with test parameters
                bt = Backtester(
                    ticker=ticker,
                    market='SE',
                    start_date=START_DATE,
                    end_date=END_DATE,
                    initial_capital=INITIAL_CAPITAL,
                    mode='conservative'  # Use conservative as base
                )

                # Override mode config with test parameters
                bt.mode_config = config

                # Run backtest
                result = bt.run()
                metrics = result['metrics']

                stock_results.append({
                    "ticker": ticker,
                    "return": metrics.get("total_return", 0),
                    "sharpe": metrics.get("sharpe_ratio", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "trades": metrics.get("total_trades", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                })

            except Exception as e:
                print(f"[{progress:5.1f}%] {ticker} - ERROR: {str(e)[:30]}")
                continue

        # Calculate aggregate metrics
        if stock_results:
            avg_return = np.mean([r["return"] for r in stock_results])
            avg_sharpe = np.mean([r["sharpe"] for r in stock_results])
            avg_win_rate = np.mean([r["win_rate"] for r in stock_results])
            avg_profit_factor = np.mean([r["profit_factor"] for r in stock_results])
            avg_drawdown = np.mean([r["max_drawdown"] for r in stock_results])
            total_trades = sum([r["trades"] for r in stock_results])

            results.append({
                "config": config,
                "avg_return": avg_return,
                "avg_sharpe": avg_sharpe,
                "avg_win_rate": avg_win_rate,
                "avg_profit_factor": avg_profit_factor,
                "avg_drawdown": avg_drawdown,
                "total_trades": total_trades,
                "stock_results": stock_results
            })

            # Print progress
            print(f"[{progress:5.1f}%] SL={stop_loss*100:.1f}%, Tgt={target_mult:.1f}x, "
                  f"Score={min_score:.1f}, W={tech_w:.0%}/{macro_w:.0%} "
                  f"-> Return={avg_return:+.1f}%, Sharpe={avg_sharpe:.2f}, "
                  f"Win={avg_win_rate:.0f}%")

    # Save all results
    output_file = "parameter_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "stocks": TEST_STOCKS,
                "start_date": START_DATE,
                "end_date": END_DATE,
                "target_metric": target_metric
            },
            "results": results
        }, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    # Analyze results
    analyze_results(results, target_metric)

    return results


def analyze_results(results, target_metric="sharpe"):
    """Analyze optimization results and find best parameters"""

    if not results:
        print("No results to analyze!")
        return

    print("\n")
    print("=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)

    # Sort by target metric
    if target_metric == "sharpe":
        sorted_results = sorted(results, key=lambda x: x["avg_sharpe"], reverse=True)
    elif target_metric == "return":
        sorted_results = sorted(results, key=lambda x: x["avg_return"], reverse=True)
    elif target_metric == "win_rate":
        sorted_results = sorted(results, key=lambda x: x["avg_win_rate"], reverse=True)
    elif target_metric == "profit_factor":
        sorted_results = sorted(results, key=lambda x: x["avg_profit_factor"], reverse=True)
    else:
        sorted_results = results

    # Top 10 configurations
    print(f"\nTOP 10 CONFIGURATIONS (by {target_metric}):")
    print("-" * 80)

    for i, result in enumerate(sorted_results[:10], 1):
        config = result["config"]
        print(f"\n{i}. Stop Loss: {config['stop_loss_buffer']*100:.1f}%, "
              f"Target Mult: {config['target_multiplier']:.1f}x, "
              f"Min Score: {config['buy_threshold']:.1f}")
        print(f"   Weights: Tech {config['tech_weight']:.0%}, Macro {config['macro_weight']:.0%}")
        print(f"   Avg Return: {result['avg_return']:+.2f}%")
        print(f"   Avg Sharpe: {result['avg_sharpe']:.2f}")
        print(f"   Win Rate: {result['avg_win_rate']:.1f}%")
        print(f"   Profit Factor: {result['avg_profit_factor']:.2f}")
        print(f"   Max Drawdown: {result['avg_drawdown']:.1f}%")
        print(f"   Total Trades: {result['total_trades']}")

    # Best configuration
    best = sorted_results[0]
    best_config = best["config"]

    print("\n")
    print("=" * 80)
    print("BEST CONFIGURATION")
    print("=" * 80)
    print(f"Stop Loss Buffer: {best_config['stop_loss_buffer']:.4f} ({best_config['stop_loss_buffer']*100:.1f}%)")
    print(f"Target Multiplier: {best_config['target_multiplier']:.2f}x")
    print(f"Min Buy Score: {best_config['buy_threshold']:.1f}")
    print(f"Tech Weight: {best_config['tech_weight']:.2f}")
    print(f"Macro Weight: {best_config['macro_weight']:.2f}")
    print()
    print(f"Expected Performance:")
    print(f"  Avg Return: {best['avg_return']:+.2f}%")
    print(f"  Avg Sharpe: {best['avg_sharpe']:.2f}")
    print(f"  Win Rate: {best['avg_win_rate']:.1f}%")
    print(f"  Profit Factor: {best['avg_profit_factor']:.2f}")
    print(f"  Max Drawdown: {best['avg_drawdown']:.1f}%")
    print(f"  Total Trades: {best['total_trades']}")
    print("=" * 80)

    # Save best config
    best_config_file = "optimal_parameters_2024.json"
    with open(best_config_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target_metric": target_metric,
            "config": best_config,
            "performance": {
                "avg_return": best['avg_return'],
                "avg_sharpe": best['avg_sharpe'],
                "avg_win_rate": best['avg_win_rate'],
                "avg_profit_factor": best['avg_profit_factor'],
                "avg_drawdown": best['avg_drawdown'],
                "total_trades": best['total_trades']
            }
        }, f, indent=2)

    print(f"\nBest configuration saved to: {best_config_file}")

    # Comparison with current modes
    print("\n\nCOMPARISON WITH CURRENT MODES:")
    print("-" * 80)
    print("(From OMX30 benchmark)")
    print(f"Conservative: +1.38% avg return, 61.5% win rate")
    print(f"Aggressive:   +2.57% avg return, 57.0% win rate")
    print(f"AI-Hybrid:    +2.17% avg return, 58.4% win rate")
    print()
    print(f"OPTIMIZED:    {best['avg_return']:+.2f}% avg return, {best['avg_win_rate']:.1f}% win rate")

    improvement = best['avg_return'] - 2.57  # Compare to best current mode (Aggressive)
    print(f"\nIMPROVEMENT: {improvement:+.2f}% (vs current best)")
    print("=" * 80)


if __name__ == "__main__":
    # Run optimization (testing 100 random combinations)
    # Can adjust max_tests for faster/slower but more/less thorough search
    results = run_optimization(max_tests=100, target_metric="sharpe")
    print("\nOptimization complete!")
