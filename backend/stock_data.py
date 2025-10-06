"""
Yahoo Finance Integration
Hamtar aktiekurser, historisk data och tekniska indikatorer
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class StockDataFetcher:
    """Hamtar och hanterar aktiedata fran Yahoo Finance"""

    # Svenska aktier suffix
    SWEDISH_SUFFIX = ".ST"  # Stockholm
    US_SUFFIX = ""  # USA behover inget suffix

    # Mapping for svenska aktier (ticker -> Yahoo symbol)
    SWEDISH_TICKERS = {
        "VOLVO-B": "VOLV-B.ST",
        "VOLVO B": "VOLV-B.ST",
        "HM-B": "HM-B.ST",
        "HM B": "HM-B.ST",
        "H&M-B": "HM-B.ST",
        "H&M B": "HM-B.ST",
        "ERIC-B": "ERIC-B.ST",
        "ERIC B": "ERIC-B.ST",
        "ABB": "ABB.ST",
        "ATCO-A": "ATCO-A.ST",
        "ATCO A": "ATCO-A.ST",
        "AZN": "AZN.ST",
        "SAND": "SAND.ST",
        "SEB-A": "SEB-A.ST",
        "SEB A": "SEB-A.ST",
        "SINCH": "SINCH.ST",
        "SKF-B": "SKF-B.ST",
        "SKF B": "SKF-B.ST",
        "TELIA": "TELIA.ST",
    }

    def __init__(self):
        self.cache = {}  # Cache for att minska API-anrop

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

    def search_ticker(self, query: str) -> List[Dict]:
        """
        Soker efter aktier baserat pa namn eller ticker

        Args:
            query: Sokord

        Returns:
            Lista med matchande aktier
        """
        # TODO: Implementera sokfunktion
        # For nu returnerar vi bara query som ticker
        return [{'ticker': query.upper(), 'name': query.upper()}]


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
