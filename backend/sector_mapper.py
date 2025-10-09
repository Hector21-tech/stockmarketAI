"""
Sector Mapper - OMX30 Sector Classification
Maps stocks to sectors for correlation cap and Top-N override logic
"""

from typing import Dict, List


# OMX30 Sector Classification (GICS-style)
SECTOR_MAP = {
    # Financials
    'SEB-A': 'Financials',
    'SHB-A': 'Financials',
    'SWED-A': 'Financials',
    'SBB-B': 'Real Estate',

    # Industrials
    'ABB': 'Industrials',
    'ALFA': 'Industrials',
    'ASSA-B': 'Industrials',
    'ATCO-A': 'Industrials',
    'SAND': 'Industrials',
    'SKF-B': 'Industrials',
    'VOLV-B': 'Industrials',

    # Technology
    'ERIC-B': 'Technology',
    'HEXA-B': 'Technology',
    'TEL2-B': 'Technology',

    # Consumer Discretionary
    'EVO': 'Consumer Discretionary',
    'HM-B': 'Consumer Discretionary',

    # Consumer Staples
    'ESSITY-B': 'Consumer Staples',

    # Healthcare
    'AZN': 'Healthcare',
    'GETI-B': 'Healthcare',

    # Materials
    'BOL': 'Materials',
    'SCA-B': 'Materials',

    # Communication Services
    'KINV-B': 'Communication Services',

    # Energy
    'NIBE-B': 'Energy',

    # Real Estate (separate from Financials)
    'SBB-B': 'Real Estate',

    # Security & Defense
    'SECU-B': 'Industrials',

    # Building & Construction
    'SKA-B': 'Industrials',
    'SWMA': 'Industrials',

    # Investment Companies
    'INVE-B': 'Financials',

    # ELUX
    'ELUX-B': 'Consumer Discretionary',

    # NDA-SE
    'NDA-SE': 'Industrials'
}


class SectorMapper:
    """
    Maps stocks to sectors and enforces diversification rules
    """

    def __init__(self, max_per_sector: int = 2):
        """
        Args:
            max_per_sector: Maximum positions allowed per sector (default 2)
        """
        self.max_per_sector = max_per_sector
        self.sector_map = SECTOR_MAP

    def get_sector(self, ticker: str) -> str:
        """
        Get sector for a ticker

        Args:
            ticker: Stock ticker

        Returns:
            Sector name or 'Unknown'
        """
        return self.sector_map.get(ticker, 'Unknown')

    def apply_top_n_override(self, ranked_stocks: List[Dict], top_n: int = 3,
                             min_size: str = 'half') -> List[Dict]:
        """
        Apply Top-N override with sector diversification

        Args:
            ranked_stocks: List of {ticker, score, recommended_size, ...} sorted by score
            top_n: Number of top stocks to override (default 3)
            min_size: Minimum size for top stocks (default 'half')

        Returns:
            Updated list with Top-N overrides applied
        """
        if not ranked_stocks:
            return []

        updated_stocks = ranked_stocks.copy()
        sector_counts = {}
        top_n_applied = 0

        for i, stock in enumerate(updated_stocks):
            if top_n_applied >= top_n:
                break

            ticker = stock['ticker']
            sector = self.get_sector(ticker)

            # Check sector cap
            if sector_counts.get(sector, 0) >= self.max_per_sector:
                continue  # Skip this stock, move to next

            # Apply Top-N override
            current_size = stock.get('recommended_size', 'none')
            size_rank = {'none': 0, 'quarter': 1, 'half': 2, 'full': 3}

            if size_rank.get(min_size, 0) > size_rank.get(current_size, 0):
                updated_stocks[i]['recommended_size'] = min_size
                updated_stocks[i]['top_n_override'] = True
                updated_stocks[i]['override_reason'] = f'Top-{top_n_applied+1} signal'

            # Track sector
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
            top_n_applied += 1

        return updated_stocks

    def check_sector_diversification(self, active_positions: List[str]) -> Dict:
        """
        Check current portfolio sector diversification

        Args:
            active_positions: List of ticker symbols currently held

        Returns:
            Dict with sector counts and warnings
        """
        sector_counts = {}

        for ticker in active_positions:
            sector = self.get_sector(ticker)
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Check for overconcentration
        warnings = []
        for sector, count in sector_counts.items():
            if count > self.max_per_sector:
                warnings.append(f'{sector}: {count} positions (max {self.max_per_sector})')

        return {
            'sector_counts': sector_counts,
            'warnings': warnings,
            'diversified': len(warnings) == 0
        }

    def filter_by_sector_cap(self, signals: List[Dict],
                             active_positions: List[str] = None) -> List[Dict]:
        """
        Filter new signals to respect sector cap

        Args:
            signals: List of potential new signals
            active_positions: List of currently held tickers

        Returns:
            Filtered list of signals
        """
        if active_positions is None:
            active_positions = []

        # Count current sector exposure
        sector_counts = {}
        for ticker in active_positions:
            sector = self.get_sector(ticker)
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Filter signals
        filtered_signals = []
        for signal in signals:
            ticker = signal['ticker']
            sector = self.get_sector(ticker)

            # Check if adding this would violate cap
            if sector_counts.get(sector, 0) < self.max_per_sector:
                filtered_signals.append(signal)
                # Increment for next iteration (in case multiple signals from same sector)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
            else:
                # Add rejected reason
                signal['rejected'] = True
                signal['rejection_reason'] = f'Sector cap reached ({sector})'
                filtered_signals.append(signal)

        return filtered_signals


# Singleton instance
sector_mapper = SectorMapper()


# Test
if __name__ == "__main__":
    print("Testing Sector Mapper...")
    print("=" * 70)

    mapper = SectorMapper(max_per_sector=2)

    # Test sector lookup
    print("\nSector Mapping Examples:")
    print("-" * 70)
    test_tickers = ['VOLV-B', 'SEB-A', 'ERIC-B', 'AZN', 'HM-B']
    for ticker in test_tickers:
        sector = mapper.get_sector(ticker)
        print(f"  {ticker:<10} → {sector}")

    # Test Top-N override
    print("\n" + "=" * 70)
    print("Testing Top-N Override (Top-3 with sector cap):")
    print("=" * 70)

    # Simulate ranked stocks
    ranked_stocks = [
        {'ticker': 'VOLV-B', 'score': 8.5, 'recommended_size': 'quarter'},  # Industrials
        {'ticker': 'ABB', 'score': 8.2, 'recommended_size': 'quarter'},      # Industrials
        {'ticker': 'SKF-B', 'score': 7.8, 'recommended_size': 'quarter'},    # Industrials (will be skipped!)
        {'ticker': 'ERIC-B', 'score': 7.5, 'recommended_size': 'quarter'},   # Technology (gets Top-3)
        {'ticker': 'SEB-A', 'score': 7.0, 'recommended_size': 'quarter'},    # Financials
    ]

    print("\nBefore Top-N Override:")
    for stock in ranked_stocks:
        sector = mapper.get_sector(stock['ticker'])
        print(f"  {stock['ticker']:<10} Score: {stock['score']:<5.1f} "
              f"Size: {stock['recommended_size']:<10} Sector: {sector}")

    updated_stocks = mapper.apply_top_n_override(ranked_stocks, top_n=3, min_size='half')

    print("\nAfter Top-N Override (Top-3 get Half minimum, max 2 per sector):")
    for stock in updated_stocks:
        sector = mapper.get_sector(stock['ticker'])
        override = '✓ OVERRIDE' if stock.get('top_n_override') else ''
        print(f"  {stock['ticker']:<10} Score: {stock['score']:<5.1f} "
              f"Size: {stock['recommended_size']:<10} Sector: {sector:<20} {override}")

    # Test diversification check
    print("\n" + "=" * 70)
    print("Testing Portfolio Diversification Check:")
    print("=" * 70)

    active_positions = ['VOLV-B', 'ABB', 'SKF-B', 'ERIC-B']  # 3 Industrials + 1 Tech

    diversification = mapper.check_sector_diversification(active_positions)

    print(f"\nActive Positions: {len(active_positions)}")
    print("\nSector Breakdown:")
    for sector, count in diversification['sector_counts'].items():
        status = '⚠️  WARNING' if count > mapper.max_per_sector else '✓'
        print(f"  {sector:<25}: {count} positions {status}")

    if diversification['warnings']:
        print(f"\n⚠️  Diversification Warnings:")
        for warning in diversification['warnings']:
            print(f"  {warning}")
    else:
        print(f"\n✓ Portfolio is well diversified")

    print("=" * 70)
