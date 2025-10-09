"""
Test Phase 5 Integration
Tests market_scanner + percentile_sizer + sector_mapper working together
"""

from datetime import datetime, timedelta
from market_scanner import MarketScanner
from percentile_sizer import PercentileSizer
from sector_mapper import SectorMapper


def test_phase5_integration():
    """Test complete Phase 5 workflow"""

    print("\n" + "=" * 80)
    print("PHASE 5 INTEGRATION TEST")
    print("Market Scanner + Percentile Sizer + Sector Mapper")
    print("=" * 80)

    # Initialize modules
    scanner = MarketScanner(mode='ai-hybrid')
    sizer = PercentileSizer(window_days=30, smooth_days=5)
    mapper = SectorMapper(max_per_sector=2)

    # Step 1: Scan current market
    print("\n[Step 1] Scanning OMX30 market...")
    today = datetime.now()
    results = scanner.scan_market(date=today)

    if not results:
        print("ERROR: No scan results!")
        return

    print(f"[OK] Scanned {len(results)} stocks")

    # Step 2: Add to percentile history
    print("\n[Step 2] Adding scores to percentile history...")
    sizer.add_daily_scores(today, results)

    # Show window stats
    stats = sizer.get_window_stats(today)
    if 'error' not in stats:
        print(f"[OK] Percentile window: {stats['data_points']} data points over {stats['window_days']} days")
        print(f"  Mean score: {stats['mean']:.2f}")
        print(f"  Percentile thresholds:")
        print(f"    80th (Full):    {stats.get('percentile_80', 0):.2f}")
        print(f"    60th (Half):    {stats.get('percentile_60', 0):.2f}")
        print(f"    40th (Quarter): {stats.get('percentile_40', 0):.2f}")
    else:
        print(f"⚠️  Warning: {stats['error']}")
        print("  Using fallback absolute thresholds")

    # Step 3: Calculate percentile-based position sizes
    print("\n[Step 3] Calculating percentile-based position sizes...")

    for stock in results:
        score = stock['score']
        # Calculate percentile
        percentile = sizer.get_percentile(score, today)
        # Get percentile-based size
        percentile_size = sizer.calculate_position_size(score, today)

        # Store both
        stock['percentile'] = percentile
        stock['absolute_size'] = stock['recommended_size']  # Original confidence-based size
        stock['percentile_size'] = percentile_size

    print(f"[OK] Calculated percentile sizes for {len(results)} stocks")

    # Step 4: Apply Top-N override with sector cap
    print("\n[Step 4] Applying Top-N override (Top-3, min Half, max 2 per sector)...")

    # Sort by score for Top-N
    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

    # Apply Top-N override using percentile_size
    for stock in results_sorted:
        stock['recommended_size'] = stock['percentile_size']  # Use percentile size as base

    updated_results = mapper.apply_top_n_override(results_sorted, top_n=3, min_size='half')

    overrides = [s for s in updated_results if s.get('top_n_override')]
    print(f"[OK] Applied {len(overrides)} Top-N overrides")

    # Step 5: Show results comparison
    print("\n" + "=" * 80)
    print("RESULTS: Absolute vs Percentile-Based Sizing")
    print("=" * 80)

    print(f"\n{'Rank':<6} {'Ticker':<10} {'Score':<7} {'Pctl%':<7} {'Absolute':<12} {'Percentile':<12} {'Sector':<20} {'Override'}")
    print("-" * 80)

    for i, stock in enumerate(updated_results[:15], 1):
        ticker = stock['ticker']
        score = stock['score']
        percentile = stock.get('percentile', 0)
        abs_size = stock['absolute_size']
        pct_size = stock['percentile_size']
        sector = mapper.get_sector(ticker)
        override = '[TOP-N]' if stock.get('top_n_override') else ''

        print(f"{i:<6} {ticker:<10} {score:<7.1f} {percentile:<7.1f} {abs_size.upper():<12} "
              f"{pct_size.upper():<12} {sector:<20} {override}")

    # Step 6: Distribution comparison
    print("\n" + "=" * 80)
    print("POSITION SIZE DISTRIBUTION COMPARISON")
    print("=" * 80)

    # Count absolute sizes
    abs_sizes = {}
    for stock in updated_results:
        size = stock['absolute_size']
        abs_sizes[size] = abs_sizes.get(size, 0) + 1

    # Count percentile sizes (with overrides)
    pct_sizes = {}
    for stock in updated_results:
        size = stock['recommended_size']  # Final size after overrides
        pct_sizes[size] = pct_sizes.get(size, 0) + 1

    print(f"\n{'Size':<12} {'Absolute (Phase 3)':<25} {'Percentile (Phase 5)':<25}")
    print("-" * 80)

    for size in ['full', 'half', 'quarter', 'none']:
        abs_count = abs_sizes.get(size, 0)
        pct_count = pct_sizes.get(size, 0)
        abs_pct = (abs_count / len(updated_results)) * 100 if updated_results else 0
        pct_pct = (pct_count / len(updated_results)) * 100 if updated_results else 0

        print(f"{size.upper():<12} {abs_count:<3} ({abs_pct:>5.1f}%)           "
              f"{pct_count:<3} ({pct_pct:>5.1f}%)")

    # Highlight improvement
    abs_half_full = abs_sizes.get('half', 0) + abs_sizes.get('full', 0)
    pct_half_full = pct_sizes.get('half', 0) + pct_sizes.get('full', 0)
    abs_half_full_pct = (abs_half_full / len(updated_results)) * 100 if updated_results else 0
    pct_half_full_pct = (pct_half_full / len(updated_results)) * 100 if updated_results else 0

    improvement = pct_half_full_pct - abs_half_full_pct

    print(f"\n{'COMBINED HALF/FULL:':<12} {abs_half_full:<3} ({abs_half_full_pct:>5.1f}%)           "
          f"{pct_half_full:<3} ({pct_half_full_pct:>5.1f}%)  [{improvement:+.1f}pp]")

    # Step 7: Sector diversification check
    print("\n" + "=" * 80)
    print("SECTOR DIVERSIFICATION (Top-N stocks)")
    print("=" * 80)

    top_n_stocks = [s for s in updated_results if s.get('top_n_override')]
    top_n_tickers = [s['ticker'] for s in top_n_stocks]

    if top_n_tickers:
        diversification = mapper.check_sector_diversification(top_n_tickers)

        print(f"\nTop-N Stocks: {len(top_n_tickers)}")
        for ticker in top_n_tickers:
            sector = mapper.get_sector(ticker)
            print(f"  {ticker:<10} → {sector}")

        print(f"\nSector Breakdown:")
        for sector, count in diversification['sector_counts'].items():
            status = '[OK]' if count <= mapper.max_per_sector else '[WARNING]'
            print(f"  {sector:<25}: {count} {status}")

        if diversification['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in diversification['warnings']:
                print(f"  {warning}")
        else:
            print(f"\n✓ Well diversified!")

    print("\n" + "=" * 80)
    print("PHASE 5 INTEGRATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_phase5_integration()
