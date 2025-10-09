"""
Yahoo Finance Integration
Hamtar aktiekurser, historisk data och tekniska indikatorer
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import metadata cache for fast search
try:
    from stock_metadata_cache import StockMetadataCache
    CACHE_AVAILABLE = True
except ImportError:
    StockMetadataCache = None
    CACHE_AVAILABLE = False

# Import Swedish tickers
from tickers import SWEDISH_TICKERS

class StockDataFetcher:
    """Hamtar och hanterar aktiedata fran Yahoo Finance"""

    # Svenska aktier suffix
    SWEDISH_SUFFIX = ".ST"  # Stockholm
    US_SUFFIX = ""  # USA behover inget suffix

    # Reference to shared tickers (from tickers.py)
    SWEDISH_TICKERS = SWEDISH_TICKERS

    def __init__(self):
        self.cache = {}  # Cache for att minska API-anrop

        # Initialize metadata cache for fast search (no API calls)
        if StockMetadataCache:
            try:
                self.metadata_cache = StockMetadataCache()
            except:
                self.metadata_cache = None
        else:
            self.metadata_cache = None

    def get_ticker_symbol(self, ticker: str, market: str = "SE") -> str:
        """
        Konverterar ticker till Yahoo Finance format

        Args:
            ticker: Aktiesymbol (t.ex. "VOLVO-B", "AAPL")
            market: "SE" for svenska, "US" for amerikanska

        Returns:
            Formaterad ticker (t.ex. "VOLV-B.ST", "AAPL")
        """
        if market == "SE":
            # Kolla om det finns en mapping
            ticker_upper = ticker.upper()
            if ticker_upper in self.SWEDISH_TICKERS:
                return self.SWEDISH_TICKERS[ticker_upper]
            # Fallback: lagg till .ST
            if not ticker.endswith(self.SWEDISH_SUFFIX):
                return f"{ticker}{self.SWEDISH_SUFFIX}"
        return ticker

    def get_current_price(self, ticker: str, market: str = "SE") -> Optional[float]:
        """
        Hamtar nuvarande pris for aktie

        Args:
            ticker: Aktiesymbol
            market: Marknad (SE/US)

        Returns:
            Nuvarande pris eller None om fel
        """
        try:
            symbol = self.get_ticker_symbol(ticker, market)
            stock = yf.Ticker(symbol)

            # Forst prova att hamta fran info
            try:
                price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
                if price:
                    return float(price)
            except:
                pass

            # Fallback: hamta senaste close-pris
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])

            return None

        except Exception as e:
            print(f"Fel vid hamtning av pris for {ticker}: {e}")
            return None

    def get_historical_data(self, ticker: str, period: str = "3mo",
                           market: str = "SE") -> pd.DataFrame:
        """
        Hamtar historisk prisdata

        Args:
            ticker: Aktiesymbol
            period: Tidsperiod (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            market: Marknad (SE/US)

        Returns:
            DataFrame med OHLCV data
        """
        try:
            symbol = self.get_ticker_symbol(ticker, market)
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)

            if data.empty:
                print(f"Ingen data for {ticker}")
                return pd.DataFrame()

            return data

        except Exception as e:
            print(f"Fel vid hamtning av historisk data for {ticker}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, ticker: str, market: str = "SE") -> Dict:
        """
        Hamtar grundlaggande info om aktie

        Returns:
            Dict med info (name, sector, market cap, etc)
        """
        try:
            symbol = self.get_ticker_symbol(ticker, market)
            stock = yf.Ticker(symbol)
            info = stock.info

            return {
                'ticker': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'currency': info.get('currency', 'SEK' if market == 'SE' else 'USD'),
                'exchange': info.get('exchange', 'STO' if market == 'SE' else 'NMS')
            }

        except Exception as e:
            print(f"Fel vid hamtning av info for {ticker}: {e}")
            return {'ticker': ticker, 'name': ticker}

    def get_stock_quote(self, ticker: str, market: str = "SE") -> Optional[Dict]:
        """
        Hamtar fullstandigt quote (pris, change, changePercent) for aktie

        Args:
            ticker: Aktiesymbol
            market: Marknad (SE/US)

        Returns:
            Dict med price, change, changePercent eller None om fel
        """
        try:
            symbol = self.get_ticker_symbol(ticker, market)
            stock = yf.Ticker(symbol)

            # Hamta fran info
            try:
                info = stock.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')

                if price:
                    # Hamta change data
                    change = info.get('regularMarketChange', 0)
                    change_percent = info.get('regularMarketChangePercent', 0)

                    return {
                        'price': float(price),
                        'change': float(change) if change else 0,
                        'changePercent': float(change_percent) if change_percent else 0
                    }
            except Exception as e:
                print(f"Error getting info for {ticker}: {e}")

            # Fallback: hamta senaste 2 dagar och berakna change
            hist = stock.history(period="2d")
            if not hist.empty and len(hist) >= 2:
                current_price = float(hist['Close'].iloc[-1])
                previous_price = float(hist['Close'].iloc[-2])
                change = current_price - previous_price
                change_percent = (change / previous_price) * 100

                return {
                    'price': current_price,
                    'change': change,
                    'changePercent': change_percent
                }
            elif not hist.empty:
                # Om bara 1 dag finns
                return {
                    'price': float(hist['Close'].iloc[-1]),
                    'change': 0,
                    'changePercent': 0
                }

            return None

        except Exception as e:
            print(f"Fel vid hamtning av quote for {ticker}: {e}")
            return None

    def get_multiple_prices(self, tickers: List[str], market: str = "SE") -> Dict[str, float]:
        """
        Hamtar priser for flera aktier samtidigt

        Args:
            tickers: Lista med aktiesymboler
            market: Marknad

        Returns:
            Dict med ticker: pris
        """
        prices = {}
        for ticker in tickers:
            price = self.get_current_price(ticker, market)
            if price:
                prices[ticker] = price

        return prices

    def get_multiple_quotes(self, tickers: List[str], market: str = "SE") -> Dict[str, Dict]:
        """
        Hamtar quotes (pris + change) for flera aktier samtidigt

        Args:
            tickers: Lista med aktiesymboler
            market: Marknad

        Returns:
            Dict med ticker: {price, change, changePercent}
        """
        quotes = {}
        for ticker in tickers:
            quote = self.get_stock_quote(ticker, market)
            if quote:
                quotes[ticker] = quote

        return quotes

    def is_market_open(self, market: str = "SE") -> bool:
        """
        Kollar om marknaden ar oppen

        Returns:
            True om marknaden ar oppen, annars False
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Helger
        if weekday >= 5:
            return False

        if market == "SE":
            # Stockholm: 09:00 - 17:30 CET
            market_open = now.replace(hour=9, minute=0, second=0)
            market_close = now.replace(hour=17, minute=30, second=0)
        else:  # US
            # NYSE: 09:30 - 16:00 EST (15:30 - 22:00 CET)
            market_open = now.replace(hour=15, minute=30, second=0)
            market_close = now.replace(hour=22, minute=0, second=0)

        return market_open <= now <= market_close

    def search_ticker(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Soker efter aktier baserat pa namn eller ticker
        OPTIMIZED: Uses metadata cache (NO API calls!) for Swedish stocks

        Args:
            query: Sokord (foretag eller ticker)
            limit: Max antal resultat

        Returns:
            Lista med matchande aktier
        """
        results = []
        query_upper = query.upper()

        # FAST PATH: Use metadata cache if available (NO API calls!)
        if self.metadata_cache:
            try:
                cached_results = self.metadata_cache.search(query, limit=limit)
                results.extend(cached_results)
            except Exception as e:
                print(f"[WARN] Metadata cache search failed: {e}")
                # Fall through to slow path below

        # SLOW PATH: Fallback if cache not available or failed
        if not results:
            # 1. Sok bland svenska aktier (SWEDISH_TICKERS) - WITH API CALLS (SLOW!)
            for ticker, yahoo_symbol in self.SWEDISH_TICKERS.items():
                if len(results) >= limit:
                    break
                if query_upper in ticker.upper():
                    try:
                        # Hamta namn for att visa (API CALL - SLOW!)
                        info = self.get_stock_info(ticker, "SE")
                        results.append({
                            'ticker': ticker,
                            'name': info.get('name', ticker),
                            'market': 'SE',
                            'exchange': 'Stockholm',
                            'symbol': yahoo_symbol
                        })
                    except:
                        results.append({
                            'ticker': ticker,
                            'name': ticker,
                            'market': 'SE',
                            'exchange': 'Stockholm',
                            'symbol': yahoo_symbol
                        })

            # 2. Sok efter foretagsnamn bland svenska aktier (SLOW!)
            if len(results) < limit:
                for ticker, yahoo_symbol in self.SWEDISH_TICKERS.items():
                    if len(results) >= limit:
                        break
                    if ticker not in [r['ticker'] for r in results]:  # Undvik dubbletter
                        try:
                            info = self.get_stock_info(ticker, "SE")
                            name = info.get('name', ticker)
                            if query_upper in name.upper():
                                results.append({
                                    'ticker': ticker,
                                    'name': name,
                                    'market': 'SE',
                                    'exchange': 'Stockholm',
                                    'symbol': yahoo_symbol
                                })
                        except:
                            pass

        # 3. Sok bland amerikanska aktier (prova direkt ticker)
        if len(results) < limit:
            try:
                # Prova som US ticker
                stock = yf.Ticker(query_upper)
                info = stock.info
                if info and info.get('regularMarketPrice'):
                    results.append({
                        'ticker': query_upper,
                        'name': info.get('longName', query_upper),
                        'market': 'US',
                        'exchange': info.get('exchange', 'NASDAQ/NYSE'),
                        'symbol': query_upper
                    })
            except:
                pass

        # 4. Vanliga amerikanska aktier (hardkodad lista for snabb search)
        us_common = {
            # Mega Tech
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'GOOG': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.',
            'FB': 'Meta Platforms Inc.',

            # AI & Chips
            'NVDA': 'NVIDIA Corporation',
            'AMD': 'Advanced Micro Devices Inc.',
            'INTC': 'Intel Corporation',
            'AVGO': 'Broadcom Inc.',
            'QCOM': 'Qualcomm Inc.',

            # EV & Auto
            'TSLA': 'Tesla Inc.',
            'F': 'Ford Motor Company',
            'GM': 'General Motors Company',
            'RIVN': 'Rivian Automotive Inc.',
            'LCID': 'Lucid Group Inc.',

            # Streaming & Entertainment
            'NFLX': 'Netflix Inc.',
            'DIS': 'The Walt Disney Company',
            'PARA': 'Paramount Global',
            'WBD': 'Warner Bros. Discovery Inc.',

            # Finance & Banking
            'JPM': 'JPMorgan Chase & Co.',
            'BAC': 'Bank of America Corporation',
            'WFC': 'Wells Fargo & Company',
            'GS': 'Goldman Sachs Group Inc.',
            'MS': 'Morgan Stanley',
            'C': 'Citigroup Inc.',
            'V': 'Visa Inc.',
            'MA': 'Mastercard Inc.',
            'PYPL': 'PayPal Holdings Inc.',
            'SQ': 'Block Inc.',

            # E-commerce & Retail
            'WMT': 'Walmart Inc.',
            'TGT': 'Target Corporation',
            'COST': 'Costco Wholesale Corporation',
            'HD': 'The Home Depot Inc.',
            'NKE': 'Nike Inc.',

            # Energy
            'XOM': 'Exxon Mobil Corporation',
            'CVX': 'Chevron Corporation',
            'COP': 'ConocoPhillips',

            # Healthcare & Pharma
            'JNJ': 'Johnson & Johnson',
            'UNH': 'UnitedHealth Group Inc.',
            'PFE': 'Pfizer Inc.',
            'ABBV': 'AbbVie Inc.',
            'MRK': 'Merck & Co. Inc.',
            'LLY': 'Eli Lilly and Company',

            # Aerospace & Defense
            'BA': 'Boeing Company',
            'LMT': 'Lockheed Martin Corporation',
            'RTX': 'Raytheon Technologies Corporation',

            # Communications
            'T': 'AT&T Inc.',
            'VZ': 'Verizon Communications Inc.',
            'CMCSA': 'Comcast Corporation',

            # Consumer Goods
            'PG': 'Procter & Gamble Company',
            'KO': 'The Coca-Cola Company',
            'PEP': 'PepsiCo Inc.',
            'MCD': "McDonald's Corporation",
            'SBUX': 'Starbucks Corporation',

            # Software & Cloud
            'CRM': 'Salesforce Inc.',
            'ORCL': 'Oracle Corporation',
            'ADBE': 'Adobe Inc.',
            'NOW': 'ServiceNow Inc.',
            'SNOW': 'Snowflake Inc.',
            'PLTR': 'Palantir Technologies Inc.',
        }

        if len(results) < limit:
            for ticker, name in us_common.items():
                if query_upper in ticker or query_upper in name.upper():
                    if ticker not in [r['ticker'] for r in results]:
                        results.append({
                            'ticker': ticker,
                            'name': name,
                            'market': 'US',
                            'exchange': 'NASDAQ/NYSE',
                            'symbol': ticker
                        })

        return results[:limit]


# Test-funktion
if __name__ == "__main__":
    fetcher = StockDataFetcher()

    print("Testing Yahoo Finance integration...")
    print("="*60)

    # Test svenska aktier
    print("\nSVENSKA AKTIER:")
    swedish_stocks = ["VOLVO-B", "HM-B", "ERIC-B"]

    for ticker in swedish_stocks:
        price = fetcher.get_current_price(ticker, "SE")
        if price:
            print(f"{ticker}: {price} SEK")

    # Test amerikanska aktier
    print("\nAMERIKANSKA AKTIER:")
    us_stocks = ["AAPL", "TSLA", "AMD"]

    for ticker in us_stocks:
        price = fetcher.get_current_price(ticker, "US")
        if price:
            print(f"{ticker}: ${price}")

    # Test historisk data
    print("\nHISTORISK DATA (VOLVO-B, senaste 5 dagar):")
    hist = fetcher.get_historical_data("VOLVO-B", period="5d", market="SE")
    if not hist.empty:
        print(hist[['Close']].tail())

    print(f"\nMarknad oppen (SE): {fetcher.is_market_open('SE')}")
    print(f"Marknad oppen (US): {fetcher.is_market_open('US')}")
