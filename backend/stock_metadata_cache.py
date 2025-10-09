#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Metadata Cache
Pre-caches stock names to speed up search
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import yfinance as yf

# Import ticker mappings
from tickers import SWEDISH_TICKERS


CACHE_FILE = Path(__file__).parent / 'cache' / 'stock_metadata.json'


class StockMetadataCache:
    """
    Pre-caches stock metadata (names, tickers) to avoid yfinance calls during search
    """

    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save cache: {e}")

    def get(self, ticker: str, market: str = 'SE') -> Dict:
        """
        Get cached metadata for ticker

        Returns:
            {'ticker': str, 'name': str, 'market': str, 'exchange': str, 'symbol': str}
            or None if not found
        """
        key = f"{ticker}_{market}"
        return self.cache.get(key)

    def set(self, ticker: str, market: str, name: str, exchange: str, yahoo_symbol: str):
        """Cache metadata for ticker"""
        key = f"{ticker}_{market}"
        self.cache[key] = {
            'ticker': ticker,
            'name': name,
            'market': market,
            'exchange': exchange,
            'symbol': yahoo_symbol,
            'cached_at': datetime.now().isoformat()
        }

    def warm_cache(self, save=True) -> Dict[str, str]:
        """
        Pre-warm cache by fetching all stock names

        Returns:
            Dict mapping ticker -> status
        """
        results = {}

        print(f"\n[WARM] Warming stock metadata cache...")
        print("=" * 60)

        # Get unique Yahoo symbols (avoid duplicates like VOLVO-B and VOLVO B)
        unique_symbols = {}
        for ticker, yahoo_symbol in SWEDISH_TICKERS.items():
            if yahoo_symbol not in unique_symbols:
                unique_symbols[yahoo_symbol] = ticker

        total = len(unique_symbols)

        for i, (yahoo_symbol, ticker) in enumerate(unique_symbols.items(), 1):
            try:
                print(f"[{i}/{total}] {ticker} ({yahoo_symbol})...", end=' ')

                # Check if already cached
                cached = self.get(ticker, 'SE')
                if cached:
                    print("[OK] Already cached")
                    results[ticker] = 'cached'
                    continue

                # Fetch from yfinance
                stock = yf.Ticker(yahoo_symbol)
                info = stock.info

                name = info.get('longName') or info.get('shortName') or ticker

                # Cache it
                self.set(
                    ticker=ticker,
                    market='SE',
                    name=name,
                    exchange='Stockholm',
                    yahoo_symbol=yahoo_symbol
                )

                print(f"[OK] {name}")
                results[ticker] = 'success'

            except Exception as e:
                print(f"[FAIL] {e}")
                # Cache with fallback name
                self.set(
                    ticker=ticker,
                    market='SE',
                    name=ticker,
                    exchange='Stockholm',
                    yahoo_symbol=yahoo_symbol
                )
                results[ticker] = f'failed: {e}'

        if save:
            self._save_cache()
            print("=" * 60)
            print(f"[DONE] Cache saved to {self.cache_file}")
            print(f"   Success: {sum(1 for s in results.values() if s in ['success', 'cached'])}")
            print(f"   Failed:  {sum(1 for s in results.values() if s.startswith('failed'))}")

        return results

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search cached metadata (fast, no API calls)

        Args:
            query: Search term
            limit: Max results

        Returns:
            List of matching stocks
        """
        results = []
        query_upper = query.upper()

        # Search in cache
        for key, data in self.cache.items():
            if len(results) >= limit:
                break

            ticker = data['ticker']
            name = data['name']

            # Match by ticker or name
            if query_upper in ticker.upper() or query_upper in name.upper():
                results.append(data)

        return results

    def clear_cache(self) -> int:
        """Clear all cache"""
        count = len(self.cache)
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        return count


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stock metadata cache management")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Warm cache command
    warm_parser = subparsers.add_parser('warm', help='Pre-warm cache')

    # Search command (for testing)
    search_parser = subparsers.add_parser('search', help='Test search')
    search_parser.add_argument('query', type=str, help='Search query')

    # Clear cache command
    clear_parser = subparsers.add_parser('clear', help='Clear cache')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache stats')

    args = parser.parse_args()

    cache = StockMetadataCache()

    if args.command == 'warm':
        cache.warm_cache()

    elif args.command == 'search':
        results = cache.search(args.query)
        print(f"\n[SEARCH] Results for '{args.query}':")
        print("=" * 60)
        for r in results:
            print(f"  {r['ticker']:15s} {r['name']}")

    elif args.command == 'clear':
        count = cache.clear_cache()
        print(f"[OK] Cleared {count} cache entries")

    elif args.command == 'stats':
        print(f"\n[STATS] Cache Statistics:")
        print(f"   Total entries: {len(cache.cache)}")
        print(f"   Cache file: {cache.cache_file}")
        if cache.cache_file.exists():
            size = cache.cache_file.stat().st_size
            print(f"   File size: {size:,} bytes")
