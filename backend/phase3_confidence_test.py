"""
Phase 3: Confidence System Backtest
Tests confidence-based position sizing with MarketMate risk adjustments
"""

from backtester import Backtester
import json
from datetime import datetime

def test_confidence_backtest():
    """
    Test confidence system with 5 stocks from OMX30
    Compare confidence-adjusted vs baseline performance
    """

    # Test stocks (mix of historically good and bad performers)
    test_stocks = [
        'VOLVO-B',  # Automotive
        'ABB',      # Industrials (historically good)
        'ERIC-B',   # Telecom (historically good)
        'HM-B',     # Retail
        'SAND',     # Construction (historically good)
    ]

    print("=" * 80)
    print("PHASE 3: CONFIDENCE SYSTEM BACKTEST")
    print("=" * 80)
    print("\nTesting MarketMate Confidence-Based Position Sizing")
    print("Period: 2024-01-01 to 2025-01-01")
    print("Mode: Conservative (with confidence adjustment)")
    print("\n" + "=" * 80)

    results = []

    for ticker in test_stocks:
        print(f"\n{'=' * 80}")
        print(f"Testing: {ticker}")
        print("=" * 80)

        # Run backtest with confidence system
        bt = Backtester(
            ticker=ticker,
            market='SE',
            start_date='2024-01-01',
            end_date='2025-01-01',
            initial_capital=100000,
            mode='conservative'
        )

        result = bt.run()

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            results.append({
                'ticker': ticker,
                'error': result['error']
            })
            continue

        # Extract metrics
        metrics = result['metrics']
        trades = result['trades']

        # Calculate confidence statistics
        if trades:
            full_positions = [t for t in trades if t.get('position_size') == 'full']
            half_positions = [t for t in trades if t.get('position_size') == 'half']
            quarter_positions = [t for t in trades if t.get('position_size') == 'quarter']
            avg_confidence = sum(t.get('confidence', 0) for t in trades) / len(trades)

            # Separate winning and losing trades
            winning = [t for t in trades if t['pnl'] > 0]
            losing = [t for t in trades if t['pnl'] <= 0]
        else:
            full_positions = half_positions = quarter_positions = []
            avg_confidence = 0
            winning = losing = []

        # Display results
        print(f"\n[RESULTS FOR {ticker}]")
        print("-" * 80)
        print(f"Total Return: {metrics['total_return']:+.2f}%")
        print(f"CAGR: {metrics['cagr']:.2f}%")
        print(f"Trades: {metrics['total_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.1f}%")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")

        print(f"\n[CONFIDENCE STATISTICS]")
        print(f"Average Confidence: {avg_confidence:.1f}%")
        print(f"Full Positions (100%): {len(full_positions)} trades")
        print(f"Half Positions (50%): {len(half_positions)} trades")
        print(f"Quarter Positions (25%): {len(quarter_positions)} trades")

        if trades:
            print(f"\n[TRADE BREAKDOWN]")
            print(f"Winning Trades: {len(winning)} ({len(winning)/len(trades)*100:.1f}%)")
            if winning:
                print(f"  Avg Win: {sum(t['pnl_percent'] for t in winning)/len(winning):.2f}%")
            print(f"Losing Trades: {len(losing)} ({len(losing)/len(trades)*100:.1f}%)")
            if losing:
                print(f"  Avg Loss: {sum(t['pnl_percent'] for t in losing)/len(losing):.2f}%")

        # Store results
        results.append({
            'ticker': ticker,
            'return': metrics['total_return'],
            'cagr': metrics['cagr'],
            'trades': metrics['total_trades'],
            'win_rate': metrics['win_rate'],
            'sharpe': metrics['sharpe_ratio'],
            'max_dd': metrics['max_drawdown'],
            'avg_confidence': avg_confidence,
            'full_positions': len(full_positions),
            'half_positions': len(half_positions),
            'quarter_positions': len(quarter_positions),
            'winning_trades': len(winning),
            'losing_trades': len(losing)
        })

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 3 SUMMARY - CONFIDENCE SYSTEM")
    print("=" * 80)

    valid_results = [r for r in results if 'error' not in r]

    if valid_results:
        avg_return = sum(r['return'] for r in valid_results) / len(valid_results)
        avg_win_rate = sum(r['win_rate'] for r in valid_results) / len(valid_results)
        avg_sharpe = sum(r['sharpe'] for r in valid_results) / len(valid_results)
        avg_confidence = sum(r['avg_confidence'] for r in valid_results) / len(valid_results)
        total_trades = sum(r['trades'] for r in valid_results)
        total_full = sum(r['full_positions'] for r in valid_results)
        total_half = sum(r['half_positions'] for r in valid_results)
        total_quarter = sum(r['quarter_positions'] for r in valid_results)

        print(f"\n[OVERALL PERFORMANCE]")
        print(f"Average Return: {avg_return:+.2f}%")
        print(f"Average Win Rate: {avg_win_rate:.1f}%")
        print(f"Average Sharpe: {avg_sharpe:.2f}")
        print(f"Average Confidence: {avg_confidence:.1f}%")

        print(f"\n[POSITION SIZE DISTRIBUTION]")
        print(f"Total Trades: {total_trades}")
        print(f"Full Positions: {total_full} ({total_full/total_trades*100:.1f}%)")
        print(f"Half Positions: {total_half} ({total_half/total_trades*100:.1f}%)")
        print(f"Quarter Positions: {total_quarter} ({total_quarter/total_trades*100:.1f}%)")

        print(f"\n[BEST PERFORMER]")
        best = max(valid_results, key=lambda x: x['return'])
        print(f"{best['ticker']}: {best['return']:+.2f}% (Win Rate: {best['win_rate']:.1f}%)")

        print(f"\n[WORST PERFORMER]")
        worst = min(valid_results, key=lambda x: x['return'])
        print(f"{worst['ticker']}: {worst['return']:+.2f}% (Win Rate: {worst['win_rate']:.1f}%)")

        # Save results
        output = {
            'test_date': datetime.now().isoformat(),
            'period': '2024-01-01 to 2025-01-01',
            'mode': 'conservative',
            'stocks_tested': len(test_stocks),
            'summary': {
                'avg_return': avg_return,
                'avg_win_rate': avg_win_rate,
                'avg_sharpe': avg_sharpe,
                'avg_confidence': avg_confidence,
                'total_trades': total_trades,
                'position_distribution': {
                    'full': total_full,
                    'half': total_half,
                    'quarter': total_quarter
                }
            },
            'individual_results': results
        }

        with open('phase3_confidence_results.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n[SUCCESS] Results saved to: phase3_confidence_results.json")

        # Compare to baseline (from OPTIMIZATION_LEARNINGS.md)
        baseline_return = 1.38  # Conservative mode baseline
        improvement = avg_return - baseline_return

        print(f"\n[COMPARISON TO BASELINE]")
        print(f"Baseline (Conservative): +{baseline_return:.2f}%")
        print(f"Phase 3 (w/ Confidence): {avg_return:+.2f}%")
        print(f"Improvement: {improvement:+.2f}% ({improvement/baseline_return*100:+.1f}%)")

        if improvement > 0:
            print("\n[SUCCESS] Confidence system improved performance!")
        else:
            print("\n[WARNING] Performance declined. Need further optimization.")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_confidence_backtest()
