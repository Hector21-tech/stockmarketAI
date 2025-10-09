"""
Seasonality Cache Management
File-based cache for stock seasonality data with pre-warming
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from seasonality_analyzer import get_monthly_returns, build_jsonl, gemini_seasonality_analysis


# Cache configuration
CACHE_DIR = Path(__file__).parent / 'cache' / 'seasonality'
CACHE_TTL_DAYS = 30

# OMX30 - Top 30 most liquid Stockholm stocks
TOP_OMX_TICKERS = [
    'VOLV-B.ST',   # Volvo B
    'KINV-B.ST',   # Investor B
    'ERIC-B.ST',   # Ericsson B
    'HM-B.ST',     # H&M B
    'SEB-A.ST',    # SEB A
    'SHB-A.ST',    # Handelsbanken A
    'SWED-A.ST',   # Swedbank A
    'ABB.ST',      # ABB
    'AZN.ST',      # AstraZeneca
    'ATCO-A.ST',   # Atlas Copco A
    'SAND.ST',     # Sandvik
    'ASSA-B.ST',   # Assa Abloy B
    'SKF-B.ST',    # SKF B
    'ALFA.ST',     # Alfa Laval
    'ELUX-B.ST',   # Electrolux B
    'ESSITY-B.ST', # Essity B
    'HEXA-B.ST',   # Hexagon B
    'TEL2-B.ST',   # Tele2 B
    'TELIA.ST',    # Telia
    'ICA.ST',      # ICA Gruppen
    # Additional OMX30 stocks
    'NDA-SE.ST',   # Nordea
    'BOL.ST',      # Boliden
    'SECU-B.ST',   # Securitas B
    'GETI-B.ST',   # Getinge B
    'SCA-B.ST',    # SCA B
    'SSAB-A.ST',   # SSAB A
    'ATCO-B.ST',   # Atlas Copco B
    'EVO.ST',      # Evolution
    'NIBE-B.ST',   # NIBE B
    'SINCH.ST',    # Sinch
]


class SeasonalityCache:
    """
    File-based cache for seasonality data
    Supports pre-warming and lazy-loading
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache

        Args:
            cache_dir: Custom cache directory (default: CACHE_DIR)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, ticker: str, month: int) -> Optional[Dict]:
        """
        Get seasonality data from cache

        Args:
            ticker: Stock ticker
            month: Month number 1-12

        Returns:
            Cached data or None if not found/expired
        """
        cache_file = self._get_cache_file(ticker, month)

        if not cache_file.exists():
            return None

        # Check if cache is expired
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(days=CACHE_TTL_DAYS):
            return None

        # Load and return cache
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading cache for {ticker} month {month}: {e}")
            return None

    def set(self, ticker: str, month: int, data: Dict) -> None:
        """
        Save seasonality data to cache

        Args:
            ticker: Stock ticker
            month: Month number 1-12
            data: Data to cache
        """
        cache_file = self._get_cache_file(ticker, month)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing cache for {ticker} month {month}: {e}")

    def get_or_generate(self, ticker: str, month: int) -> Dict:
        """
        Get from cache or generate on-demand

        Args:
            ticker: Stock ticker
            month: Month number 1-12

        Returns:
            Seasonality data (cached or freshly generated)
        """
        # Try cache first
        cached = self.get(ticker, month)
        if cached is not None:
            return cached

        # Generate fresh data
        data = self._generate_seasonality_data(ticker, month)

        # Cache it
        self.set(ticker, month, data)

        return data

    def warm_cache(self, tickers: Optional[List[str]] = None, month: Optional[int] = None) -> Dict[str, str]:
        """
        Pre-generate cache for specified tickers

        Args:
            tickers: List of tickers (default: TOP_OMX_TICKERS)
            month: Month to warm (default: current month)

        Returns:
            Dict mapping ticker -> status ('success'/'failed')
        """
        if tickers is None:
            tickers = TOP_OMX_TICKERS

        if month is None:
            month = datetime.now().month

        results = {}

        print(f"\n[WARM] Warming seasonality cache for {len(tickers)} tickers (month {month})...")
        print("="*60)

        for i, ticker in enumerate(tickers, 1):
            try:
                print(f"[{i}/{len(tickers)}] Processing {ticker}...", end=' ')

                # Check if cache exists and is fresh
                cache_file = self._get_cache_file(ticker, month)
                if cache_file.exists():
                    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_age < timedelta(days=CACHE_TTL_DAYS):
                        print("[OK] Already cached (fresh)")
                        results[ticker] = 'cached'
                        continue

                # Generate fresh data
                data = self._generate_seasonality_data(ticker, month)

                # Save to cache
                self.set(ticker, month, data)

                print("[OK] Generated & cached")
                results[ticker] = 'success'

            except Exception as e:
                print(f"[FAIL] {e}")
                results[ticker] = f'failed: {e}'

        print("="*60)
        print(f"[DONE] Cache warming complete!")
        print(f"   Success: {sum(1 for s in results.values() if s in ['success', 'cached'])}")
        print(f"   Failed:  {sum(1 for s in results.values() if s.startswith('failed'))}")

        return results

    def clear_cache(self, ticker: Optional[str] = None) -> int:
        """
        Clear cache files

        Args:
            ticker: Clear specific ticker (None = clear all)

        Returns:
            Number of files deleted
        """
        if ticker:
            # Clear specific ticker
            pattern = f"{ticker}_*.json"
            files = list(self.cache_dir.glob(pattern))
        else:
            # Clear all cache
            files = list(self.cache_dir.glob("*.json"))

        count = 0
        for file in files:
            try:
                file.unlink()
                count += 1
            except Exception as e:
                print(f"Error deleting {file}: {e}")

        return count

    def _get_cache_file(self, ticker: str, month: int) -> Path:
        """
        Get cache file path for ticker/month

        Args:
            ticker: Stock ticker
            month: Month number

        Returns:
            Path to cache file
        """
        # Sanitize ticker for filename
        safe_ticker = ticker.replace('.', '_').replace(':', '_')
        return self.cache_dir / f"{safe_ticker}_{month:02d}.json"

    def _generate_seasonality_data(self, ticker: str, month: int) -> Dict:
        """
        Generate fresh seasonality data for ticker/month

        Args:
            ticker: Stock ticker
            month: Month number

        Returns:
            {
                'ticker': str,
                'month': int,
                'historical': Dict,  # Monthly returns
                'ai_analysis': Dict | None,  # Gemini analysis
                'generated_at': str
            }
        """
        # Get historical monthly returns
        try:
            historical = get_monthly_returns(ticker, years=10)
        except Exception as e:
            raise ValueError(f"Failed to fetch historical data: {e}")

        # Get Gemini AI analysis (optional)
        ai_analysis = None
        if os.getenv('GEMINI_API_KEY'):
            try:
                ai_analysis = gemini_seasonality_analysis(ticker, month)
            except Exception as e:
                print(f"Warning: Gemini analysis failed for {ticker}: {e}")
                # Continue without AI analysis

        return {
            'ticker': ticker,
            'month': month,
            'historical': historical,
            'ai_analysis': ai_analysis,
            'generated_at': datetime.now().isoformat()
        }


# CLI interface for cache management
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seasonality cache management")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Warm cache command
    warm_parser = subparsers.add_parser('warm', help='Pre-warm cache for top tickers')
    warm_parser.add_argument('--month', type=int, help='Month to warm (default: current)')
    warm_parser.add_argument('--all-months', action='store_true', help='Warm all 12 months')

    # Clear cache command
    clear_parser = subparsers.add_parser('clear', help='Clear cache')
    clear_parser.add_argument('--ticker', type=str, help='Clear specific ticker (default: all)')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')

    args = parser.parse_args()

    cache = SeasonalityCache()

    if args.command == 'warm':
        if args.all_months:
            # Warm all 12 months
            for m in range(1, 13):
                cache.warm_cache(month=m)
        else:
            # Warm specific or current month
            cache.warm_cache(month=args.month)

    elif args.command == 'clear':
        count = cache.clear_cache(ticker=args.ticker)
        print(f"[OK] Cleared {count} cache file(s)")

    elif args.command == 'stats':
        cache_files = list(cache.cache_dir.glob("*.json"))
        print(f"\n[STATS] Cache Statistics:")
        print(f"   Total files: {len(cache_files)}")
        print(f"   Cache dir: {cache.cache_dir}")

        # Count by age
        now = datetime.now()
        fresh = sum(1 for f in cache_files if now - datetime.fromtimestamp(f.stat().st_mtime) < timedelta(days=7))
        expired = sum(1 for f in cache_files if now - datetime.fromtimestamp(f.stat().st_mtime) > timedelta(days=CACHE_TTL_DAYS))

        print(f"   Fresh (<7 days): {fresh}")
        print(f"   Expired (>{CACHE_TTL_DAYS} days): {expired}")
