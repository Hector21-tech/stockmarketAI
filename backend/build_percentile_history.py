"""
Build Percentile History - Historical Data Builder
Scans market backwards to build 30+ days of percentile history for backtesting
"""

from datetime import datetime, timedelta
from market_scanner import MarketScanner
from percentile_sizer import PercentileSizer
import json
import time


def build_history(start_date: datetime, end_date: datetime, output_file: str = 'percentile_history.json'):
    """
    Build percentile history by scanning market for each trading day

    Args:
        start_date: First date to scan
        end_date: Last date to scan
        output_file: Where to save history
    """

    scanner = MarketScanner(mode='ai-hybrid')
    sizer = PercentileSizer(window_days=30, smooth_days=5)

    # Clear existing history
    sizer.score_history = {}

    current_date = start_date
    trading_days = 0
    failed_days = 0

    print(f"\n{'='*80}")
    print(f"BUILDING PERCENTILE HISTORY")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
            current_date += timedelta(days=1)
            continue

        try:
            # Scan market for this date
            results = scanner.scan_market(date=current_date, market='SE')

            if results and len(results) > 0:
                # Add to percentile history
                sizer.add_daily_scores(current_date, results)
                trading_days += 1

                # Show progress every 5 days
                if trading_days % 5 == 0:
                    scores = [r['score'] for r in results]
                    mean_score = sum(scores) / len(scores)
                    print(f"[{current_date.strftime('%Y-%m-%d')}] Day {trading_days}: "
                          f"Scanned {len(results)} stocks, mean score: {mean_score:.2f}")
                    # Extra cooldown every 5 days
                    time.sleep(2.0)
            else:
                failed_days += 1
                print(f"[{current_date.strftime('%Y-%m-%d')}] No data (likely holiday/weekend)")

        except Exception as e:
            failed_days += 1
            print(f"[{current_date.strftime('%Y-%m-%d')}] Error: {e}")

        # Move to next day
        current_date += timedelta(days=1)

    # Save history
    sizer._save_history()

    print(f"\n{'='*80}")
    print(f"HISTORY BUILD COMPLETE")
    print(f"Trading days: {trading_days}")
    print(f"Failed days: {failed_days}")
    print(f"Data saved to: {output_file}")
    print(f"{'='*80}\n")

    # Show final stats
    if trading_days >= 30:
        stats = sizer.get_window_stats(end_date)
        if 'error' not in stats:
            print(f"Final 30-day window stats:")
            print(f"  Data points: {stats['data_points']}")
            print(f"  Mean score: {stats['mean']:.2f}")
            print(f"  Std dev: {stats['std']:.2f}")
            print(f"  Percentile thresholds:")
            print(f"    80th (Full):    {stats['percentile_80']:.2f}")
            print(f"    60th (Half):    {stats['percentile_60']:.2f}")
            print(f"    40th (Quarter): {stats['percentile_40']:.2f}")

    return sizer


if __name__ == "__main__":
    # Build history for 2024 (Jan 1 to Oct 9)
    # We need 30 days before backtest start, so start from early December 2023

    start = datetime(2023, 12, 1)  # Start early to build 30d buffer
    end = datetime(2024, 12, 31)    # Through end of 2024

    print("\nBuilding percentile history for 2024 backtest...")
    print(f"This will scan {(end - start).days} days (~250 trading days)")
    print("This may take 10-15 minutes...\n")

    sizer = build_history(start, end)

    print("\n[OK] History built successfully!")
    print("Ready for Phase 5 backtest with percentile-based sizing.")
