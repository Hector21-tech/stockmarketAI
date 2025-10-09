"""
News Fetcher
Hämtar news headlines från yfinance för AI sentiment analysis
"""

import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class NewsFetcher:
    """
    Hämtar news headlines från yfinance
    """

    def __init__(self):
        pass

    def get_news_headlines(self, ticker: str, market: str = 'US', limit: int = 10) -> List[str]:
        """
        Hämta senaste news headlines för en ticker

        Args:
            ticker: Stock ticker (e.g., 'AAPL', 'VOLVO-B')
            market: Market ('US' or 'SE')
            limit: Max antal headlines att returnera

        Returns:
            List of news headline strings
        """
        try:
            # Format ticker for yfinance
            if market == 'SE':
                if not ticker.endswith('.ST'):
                    ticker = f"{ticker}.ST"

            # Fetch ticker data
            stock = yf.Ticker(ticker)

            # Get news (yfinance .news property)
            news_data = stock.news

            if not news_data:
                return []

            # Extract headlines (take first 'limit' items)
            headlines = []
            for item in news_data[:limit]:
                # New yfinance structure: title is nested in 'content'
                if 'content' in item and 'title' in item['content']:
                    headlines.append(item['content']['title'])
                # Fallback to old structure
                elif 'title' in item:
                    headlines.append(item['title'])
                elif 'headline' in item:
                    headlines.append(item['headline'])

            return headlines

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []

    def get_news_with_metadata(self, ticker: str, market: str = 'US', limit: int = 10) -> List[Dict]:
        """
        Hämta news med full metadata (title, publisher, timestamp, link)

        Args:
            ticker: Stock ticker
            market: Market ('US' or 'SE')
            limit: Max antal news items

        Returns:
            List of dicts with news metadata
        """
        try:
            # Format ticker for yfinance
            if market == 'SE':
                if not ticker.endswith('.ST'):
                    ticker = f"{ticker}.ST"

            # Fetch ticker data
            stock = yf.Ticker(ticker)

            # Get news
            news_data = stock.news

            if not news_data:
                return []

            # Format news items
            formatted_news = []
            for item in news_data[:limit]:
                # New yfinance structure: data is nested in 'content'
                content = item.get('content', {})
                formatted_news.append({
                    'title': content.get('title') or item.get('title') or item.get('headline', ''),
                    'publisher': content.get('provider', {}).get('displayName', 'Unknown'),
                    'link': content.get('canonicalUrl', {}).get('url', item.get('link', '')),
                    'timestamp': content.get('pubDate', item.get('providerPublishTime', 0)),
                })

            return formatted_news

        except Exception as e:
            print(f"Error fetching news metadata for {ticker}: {e}")
            return []


# Singleton instance
news_fetcher = NewsFetcher()


# Test
if __name__ == "__main__":
    print("Testing News Fetcher...")
    print("=" * 60)

    # Test US stock
    print("\n1. Testing AAPL (US):")
    aapl_news = news_fetcher.get_news_headlines('AAPL', 'US', limit=5)
    print(f"Found {len(aapl_news)} headlines:")
    for i, headline in enumerate(aapl_news, 1):
        print(f"  {i}. {headline}")

    # Test SE stock
    print("\n2. Testing VOLVO-B (SE):")
    volvo_news = news_fetcher.get_news_headlines('VOLVO-B', 'SE', limit=5)
    print(f"Found {len(volvo_news)} headlines:")
    for i, headline in enumerate(volvo_news, 1):
        print(f"  {i}. {headline}")

    print("\n" + "=" * 60)
