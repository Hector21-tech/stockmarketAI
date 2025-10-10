"""
Macro Data Fetcher
Hämtar makroekonomiska indikatorer från olika källor
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time

class MacroDataFetcher:
    """Hämtar makroekonomisk data"""

    def __init__(self, cache_ttl=300):
        """
        Initialize with ticker symbols for macro indicators

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.tickers = {
            'dxy': 'DX-Y.NYB',  # Dollar Index
            'vix': '^VIX',       # VIX Fear Index
            'treasury_10y': '^TNX',  # 10-Year Treasury Yield
            'spx': '^GSPC',      # S&P 500
            'nasdaq': '^IXIC',   # Nasdaq Composite
            'gold': 'GC=F',      # Gold Futures
            'oil': 'CL=F',       # Crude Oil Futures
        }

        # Cache for macro data (avoid rate limiting)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}

    def _get_cached(self, key: str, fetch_func):
        """
        Generic cache getter with TTL

        Args:
            key: Cache key
            fetch_func: Function to call if cache miss

        Returns:
            Cached or fresh data
        """
        now = time.time()

        # Check if we have valid cached data
        if key in self._cache and key in self._cache_timestamps:
            age = now - self._cache_timestamps[key]
            if age < self.cache_ttl:
                # Cache hit - return cached data
                return self._cache[key]

        # Cache miss or expired - fetch new data
        try:
            data = fetch_func()
            if data is not None:
                self._cache[key] = data
                self._cache_timestamps[key] = now
            return data
        except Exception as e:
            # Return stale cache if available (fallback)
            if key in self._cache:
                print(f"Warning: Using stale cache for {key} due to error: {e}")
                return self._cache[key]
            raise

    def get_dxy(self) -> Optional[Dict]:
        """
        Hämtar Dollar Index (DXY) data (cached for 5 min)

        Returns:
            Dict med current value, change, changePercent
        """
        def fetch_dxy():
            try:
                ticker = yf.Ticker(self.tickers['dxy'])
                hist = ticker.history(period='5d')

                if hist.empty:
                    return None

                current_value = float(hist['Close'].iloc[-1])
                previous_value = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_value
                change = current_value - previous_value
                change_percent = (change / previous_value * 100) if previous_value != 0 else 0

                return {
                    'value': current_value,
                    'change': change,
                    'changePercent': change_percent,
                    'unit': '',
                    'label': 'Dollar Index (DXY)',
                    'timestamp': datetime.now().isoformat(),
                }
            except Exception as e:
                print(f"Error fetching DXY: {e}")
                return None

        return self._get_cached('dxy', fetch_dxy)

    def get_vix(self) -> Optional[Dict]:
        """
        Hämtar VIX (Fear Index) data (cached for 5 min)

        Returns:
            Dict med current value, change, changePercent
        """
        def fetch_vix():
            try:
                ticker = yf.Ticker(self.tickers['vix'])
                hist = ticker.history(period='5d')

                if hist.empty:
                    return None

                current_value = float(hist['Close'].iloc[-1])
                previous_value = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_value
                change = current_value - previous_value
                change_percent = (change / previous_value * 100) if previous_value != 0 else 0

                return {
                    'value': current_value,
                    'change': change,
                    'changePercent': change_percent,
                    'unit': '',
                    'label': 'VIX (Fear Index)',
                    'timestamp': datetime.now().isoformat(),
                }
            except Exception as e:
                print(f"Error fetching VIX: {e}")
                return None

        return self._get_cached('vix', fetch_vix)

    def get_treasury_10y(self) -> Optional[Dict]:
        """
        Hämtar 10-Year Treasury Yield data (cached for 5 min)

        Returns:
            Dict med current value, change, changePercent
        """
        def fetch_treasury():
            try:
                ticker = yf.Ticker(self.tickers['treasury_10y'])
                hist = ticker.history(period='5d')

                if hist.empty:
                    return None

                current_value = float(hist['Close'].iloc[-1])
                previous_value = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_value
                change = current_value - previous_value
                change_percent = (change / previous_value * 100) if previous_value != 0 else 0

                return {
                    'value': current_value,
                    'change': change,
                    'changePercent': change_percent,
                    'unit': '%',
                    'label': '10-Year Treasury',
                    'timestamp': datetime.now().isoformat(),
                }
            except Exception as e:
                print(f"Error fetching Treasury 10Y: {e}")
                return None

        return self._get_cached('treasury_10y', fetch_treasury)

    def get_m2_money_supply(self) -> Optional[Dict]:
        """
        Hämtar M2 Money Supply data

        Note: M2 data är inte real-time, uppdateras månadsvis av Fed.
        För nu använder vi mock data. I framtiden kan vi integrera FRED API.

        Returns:
            Dict med current value, change, changePercent
        """
        try:
            # TODO: Integrera FRED API för real M2 data
            # För nu returnerar vi senaste kända värde (exempel från Dec 2024)
            return {
                'value': 21234.5,  # Billions of dollars
                'change': 52.3,
                'changePercent': 0.25,
                'unit': 'B',
                'label': 'M2 Money Supply',
                'timestamp': datetime.now().isoformat(),
                'note': 'Updated monthly - Latest available data',
            }
        except Exception as e:
            print(f"Error fetching M2: {e}")
            return None

    def get_fed_funds_rate(self) -> Optional[Dict]:
        """
        Hämtar Federal Funds Rate

        Note: Fed Funds rate uppdateras vid FOMC-möten (ca 8 ggr/år).
        För nu använder vi mock data. I framtiden kan vi integrera FRED API.

        Returns:
            Dict med current value, change, changePercent
        """
        try:
            # TODO: Integrera FRED API för real Fed Funds data
            # För nu returnerar vi senaste kända värde
            return {
                'value': 5.33,  # Percent
                'change': 0.0,
                'changePercent': 0.0,
                'unit': '%',
                'label': 'Fed Funds Rate',
                'timestamp': datetime.now().isoformat(),
                'note': 'Updated at FOMC meetings',
            }
        except Exception as e:
            print(f"Error fetching Fed Funds: {e}")
            return None

    def get_fear_greed_index(self) -> Optional[Dict]:
        """
        Hämtar CNN Fear & Greed Index

        Note: CNN Fear & Greed Index är inte direkt tillgänglig via API utan scraping.
        För nu använder vi VIX som proxy för att beräkna sentiment.

        Returns:
            Dict med fear/greed värde, label, color
        """
        try:
            # TODO: Implementera scraping eller hitta alternativ API för Fear & Greed Index
            # För nu, använd VIX som proxy
            vix_data = self.get_vix()
            if not vix_data:
                return None

            vix_value = vix_data['value']

            # VIX-baserad Fear/Greed calculation
            # VIX < 12: Extreme Greed
            # VIX 12-15: Greed
            # VIX 15-20: Neutral
            # VIX 20-30: Fear
            # VIX > 30: Extreme Fear

            if vix_value < 12:
                label = 'Extreme Greed'
                value = 85
                emoji = '🤑'
                color = '#16a34a'  # green
            elif vix_value < 15:
                label = 'Greed'
                value = 70
                emoji = '😊'
                color = '#22c55e'  # light green
            elif vix_value < 20:
                label = 'Neutral'
                value = 50
                emoji = '😐'
                color = '#94a3b8'  # gray
            elif vix_value < 30:
                label = 'Fear'
                value = 30
                emoji = '😰'
                color = '#f59e0b'  # orange
            else:
                label = 'Extreme Fear'
                value = 15
                emoji = '😱'
                color = '#ef4444'  # red

            return {
                'value': value,
                'label': label,
                'emoji': emoji,
                'color': color,
                'source': 'VIX-based calculation',
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching Fear & Greed Index: {e}")
            return None

    def get_put_call_ratio(self) -> Optional[Dict]:
        """
        Hämtar Put/Call Ratio

        Note: Real-time P/C ratio kräver premium data feed.
        För nu använder vi en uppskattning baserad på VIX.

        Returns:
            Dict med P/C ratio och interpretation
        """
        try:
            # TODO: Integrera real put/call ratio från CBOE eller alternativ källa
            # För nu, uppskattar vi baserat på VIX
            vix_data = self.get_vix()
            if not vix_data:
                return None

            vix_value = vix_data['value']

            # Rough estimation: Higher VIX = Higher Put/Call Ratio
            # Normal range: 0.7 - 1.3
            # VIX 15 = P/C ~0.8 (normal)
            # VIX 30 = P/C ~1.2 (bearish)

            estimated_pc = 0.5 + (vix_value / 40)
            estimated_pc = min(max(estimated_pc, 0.4), 1.5)  # Clamp between 0.4 and 1.5

            # Interpretation
            if estimated_pc < 0.7:
                interpretation = 'Bullish - Low hedging activity'
            elif estimated_pc > 1.1:
                interpretation = 'Bearish - High hedging activity'
            else:
                interpretation = 'Neutral - Normal hedging activity'

            return {
                'value': estimated_pc,
                'interpretation': interpretation,
                'source': 'VIX-based estimation',
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching Put/Call Ratio: {e}")
            return None

    def get_sentiment_data(self) -> Dict:
        """
        Hämtar all sentiment-data

        Returns:
            Dict med fear/greed index och put/call ratio
        """
        return {
            'fearGreed': self.get_fear_greed_index(),
            'putCallRatio': self.get_put_call_ratio(),
        }

    def get_sentiment_data_cached(self, vix_data: Optional[Dict]) -> Dict:
        """
        Hämtar sentiment-data från cached VIX (undviker duplicerade requests)

        Args:
            vix_data: Pre-fetched VIX data

        Returns:
            Dict med fear/greed index och put/call ratio
        """
        # Beräkna Fear & Greed från cached VIX
        fear_greed = None
        if vix_data:
            vix_value = vix_data['value']
            if vix_value < 12:
                fear_greed = {'value': 85, 'label': 'Extreme Greed', 'emoji': '🤑', 'color': '#16a34a', 'source': 'VIX-based'}
            elif vix_value < 15:
                fear_greed = {'value': 70, 'label': 'Greed', 'emoji': '😊', 'color': '#22c55e', 'source': 'VIX-based'}
            elif vix_value < 20:
                fear_greed = {'value': 50, 'label': 'Neutral', 'emoji': '😐', 'color': '#94a3b8', 'source': 'VIX-based'}
            elif vix_value < 30:
                fear_greed = {'value': 30, 'label': 'Fear', 'emoji': '😰', 'color': '#f59e0b', 'source': 'VIX-based'}
            else:
                fear_greed = {'value': 15, 'label': 'Extreme Fear', 'emoji': '😱', 'color': '#ef4444', 'source': 'VIX-based'}
            fear_greed['timestamp'] = datetime.now().isoformat()

        # Beräkna Put/Call från cached VIX
        put_call = None
        if vix_data:
            vix_value = vix_data['value']
            estimated_pc = 0.5 + (vix_value / 40)
            estimated_pc = min(max(estimated_pc, 0.4), 1.5)
            if estimated_pc < 0.7:
                interpretation = 'Bullish - Low hedging activity'
            elif estimated_pc > 1.1:
                interpretation = 'Bearish - High hedging activity'
            else:
                interpretation = 'Neutral - Normal hedging activity'
            put_call = {
                'value': estimated_pc,
                'interpretation': interpretation,
                'source': 'VIX-based estimation',
                'timestamp': datetime.now().isoformat(),
            }

        return {
            'fearGreed': fear_greed,
            'putCallRatio': put_call,
        }

    def calculate_correlation(self, ticker1: str, ticker2: str, period: str = '3mo') -> Optional[float]:
        """
        Beräknar korrelation mellan två tickers

        Args:
            ticker1: Första tickern
            ticker2: Andra tickern
            period: Tidsperiod för beräkning

        Returns:
            Correlation coefficient (-1 till 1)
        """
        try:
            # Hämta historisk data för båda tickers
            data1 = yf.Ticker(ticker1).history(period=period)
            data2 = yf.Ticker(ticker2).history(period=period)

            if data1.empty or data2.empty:
                return None

            # Beräkna dagliga returns
            returns1 = data1['Close'].pct_change().dropna()
            returns2 = data2['Close'].pct_change().dropna()

            # Align dates
            aligned = pd.DataFrame({'asset1': returns1, 'asset2': returns2}).dropna()

            if len(aligned) < 10:  # Behöver minst 10 datapunkter
                return None

            # Beräkna correlation
            correlation = aligned['asset1'].corr(aligned['asset2'])

            return float(correlation)
        except Exception as e:
            print(f"Error calculating correlation between {ticker1} and {ticker2}: {e}")
            return None

    def get_stock_correlations(self, stock_ticker: str, market: str = 'SE') -> Optional[Dict]:
        """
        Beräknar korrelationer mellan en aktie och major indices/commodities

        Args:
            stock_ticker: Ticker för aktien (t.ex. 'VOLVO-B')
            market: Marknad (SE, US, etc)

        Returns:
            Dict med korrelationer till SPX, Nasdaq, Gold, Oil
        """
        try:
            # Format ticker för yfinance
            if market == 'SE':
                yf_ticker = f"{stock_ticker}.ST"
            else:
                yf_ticker = stock_ticker

            correlations = {
                'spx': self.calculate_correlation(yf_ticker, self.tickers['spx']),
                'nasdaq': self.calculate_correlation(yf_ticker, self.tickers['nasdaq']),
                'gold': self.calculate_correlation(yf_ticker, self.tickers['gold']),
                'oil': self.calculate_correlation(yf_ticker, self.tickers['oil']),
            }

            return correlations
        except Exception as e:
            print(f"Error getting stock correlations: {e}")
            return None

    def get_market_correlations(self) -> Dict:
        """
        Hämtar korrelationer mellan major indices och commodities

        Returns:
            Dict med correlation matrix
        """
        try:
            assets = ['spx', 'nasdaq', 'gold', 'oil']
            correlation_matrix = {}

            for i, asset1 in enumerate(assets):
                correlation_matrix[asset1] = {}
                for asset2 in assets:
                    if asset1 == asset2:
                        correlation_matrix[asset1][asset2] = 1.0
                    else:
                        corr = self.calculate_correlation(
                            self.tickers[asset1],
                            self.tickers[asset2]
                        )
                        correlation_matrix[asset1][asset2] = corr

            return {
                'matrix': correlation_matrix,
                'labels': {
                    'spx': 'S&P 500',
                    'nasdaq': 'Nasdaq',
                    'gold': 'Gold',
                    'oil': 'Oil',
                },
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error getting market correlations: {e}")
            return None

    def get_seasonality_data(self, ticker: str = '^GSPC', market: str = 'US') -> Optional[Dict]:
        """
        Beräknar seasonality patterns för en ticker

        Args:
            ticker: Ticker att analysera (default S&P 500)
            market: Marknad

        Returns:
            Dict med monthly performance stats
        """
        try:
            # Hämta 5 års historisk data för seasonality analysis
            data = yf.Ticker(ticker).history(period='5y')

            if data.empty:
                return None

            # Beräkna monthly returns
            data['Month'] = data.index.month
            data['Return'] = data['Close'].pct_change()

            # Group by month and calculate statistics
            monthly_stats = {}
            for month in range(1, 13):
                month_data = data[data['Month'] == month]['Return'].dropna()

                if len(month_data) > 0:
                    monthly_stats[month] = {
                        'avg_return': float(month_data.mean() * 100),  # Convert to percentage
                        'win_rate': float((month_data > 0).sum() / len(month_data) * 100),
                        'occurrences': int(len(month_data)),
                    }
                else:
                    monthly_stats[month] = {
                        'avg_return': 0,
                        'win_rate': 0,
                        'occurrences': 0,
                    }

            # Find best and worst months
            best_month = max(monthly_stats.items(), key=lambda x: x[1]['avg_return'])
            worst_month = min(monthly_stats.items(), key=lambda x: x[1]['avg_return'])

            # Current month
            current_month = datetime.now().month
            current_month_stats = monthly_stats.get(current_month, {})

            month_names = [
                '', 'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]

            return {
                'monthly_stats': monthly_stats,
                'best_month': {
                    'month': best_month[0],
                    'name': month_names[best_month[0]],
                    'avg_return': best_month[1]['avg_return'],
                },
                'worst_month': {
                    'month': worst_month[0],
                    'name': month_names[worst_month[0]],
                    'avg_return': worst_month[1]['avg_return'],
                },
                'current_month': {
                    'month': current_month,
                    'name': month_names[current_month],
                    'avg_return': current_month_stats.get('avg_return', 0),
                    'win_rate': current_month_stats.get('win_rate', 0),
                },
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error calculating seasonality: {e}")
            return None

    def get_spx_trend(self) -> Optional[Dict]:
        """
        Hamtar S&P 500 pris och 200-dagars MA for bull/bear market detection (cached for 5 min)

        Returns:
            Dict med SPX price, 200MA, och bull market status
        """
        def fetch_spx():
            try:
                ticker = yf.Ticker('^GSPC')
                hist = ticker.history(period='1y')  # 1 ar for 200-dagars MA

                if hist.empty or len(hist) < 200:
                    return None

                current_price = float(hist['Close'].iloc[-1])
                ma_200 = float(hist['Close'].rolling(window=200).mean().iloc[-1])

                above_ma = current_price > ma_200
                distance_pct = ((current_price - ma_200) / ma_200) * 100

                return {
                    'price': current_price,
                    'ma200': ma_200,
                    'above_ma': above_ma,
                    'distance_pct': distance_pct,
                    'bullish': above_ma,  # SPX > 200MA = bull market
                    'label': 'S&P 500 vs 200MA',
                    'timestamp': datetime.now().isoformat(),
                }
            except Exception as e:
                print(f"Error fetching SPX trend: {e}")
                return None

        return self._get_cached('spx_trend', fetch_spx)

    def get_all_macro_data(self) -> Dict:
        """
        Hämtar all makrodata i en request med rate limiting

        Returns:
            Dict med alla makroindikatorer
        """
        # Hämta data med delays för att undvika rate limiting
        m2 = self.get_m2_money_supply()  # No delay, local data
        fed_funds = self.get_fed_funds_rate()  # No delay, local data

        dxy = self.get_dxy()
        time.sleep(0.5)  # Rate limiting delay

        vix = self.get_vix()  # Hämta VIX en gång och återanvänd
        time.sleep(0.5)

        treasury = self.get_treasury_10y()
        time.sleep(0.5)

        spx_trend = self.get_spx_trend()
        time.sleep(0.5)

        # Återanvänd cached VIX för regime och sentiment (undvik duplicerade requests)
        regime = self._calculate_market_regime_cached(vix)
        sentiment = self.get_sentiment_data_cached(vix)

        # Correlations är dyrt (16 requests), skippa för nu eller använd långsam cache
        correlations = None  # TODO: Cache correlations för 1 timme

        # Seasonality är också dyrt (5 års data), cacha längre
        seasonality = self.get_seasonality_data()

        return {
            'm2': m2,
            'fedFunds': fed_funds,
            'dxy': dxy,
            'vix': vix,
            'treasury10y': treasury,
            'spx_trend': spx_trend,
            'regime': regime,
            'sentiment': sentiment,
            'correlations': correlations,
            'seasonality': seasonality,
        }

    def get_usd_sek(self) -> Optional[Dict]:
        """
        Hämtar USD/SEK exchange rate

        Returns:
            Dict med current value, change, changePercent
        """
        try:
            ticker = yf.Ticker('USDSEK=X')
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_value = float(hist['Close'].iloc[-1])
            previous_value = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_value
            change = current_value - previous_value
            change_percent = (change / previous_value * 100) if previous_value != 0 else 0

            return {
                'value': current_value,
                'change': change,
                'changePercent': change_percent,
                'unit': 'SEK',
                'label': 'USD/SEK',
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching USD/SEK: {e}")
            return None

    def get_macro_score(self) -> Dict:
        """
        Beräknar MakroScore 0-10 enligt MarketMate viktning:
        - Räntor (30%)
        - Inflation (20%)
        - PMI (20%)
        - VIX (15%)
        - USD/SEK (10%)
        - Övrigt (5%)

        Returns:
            Dict med macro_score (0-10) och breakdown
        """
        # Hämta alla indikatorer
        treasury_data = self.get_treasury_10y()
        vix_data = self.get_vix()
        usd_sek_data = self.get_usd_sek()

        # Default scores
        interest_score = 0  # -2 to +2
        inflation_score = 0  # -2 to +2
        pmi_score = 0  # -2 to +2
        vix_score = 0  # -2 to +1
        forex_score = 0  # -1 to +1

        # 1. RÄNTOR (30%) - 10Y Treasury som proxy
        if treasury_data:
            treasury_yield = treasury_data['value']
            # Logik: Stigande = negativt, Sjunkande = positivt
            # Används treasury change som proxy
            if treasury_yield > 4.5:
                interest_score = -2  # Höga räntor = negativt
            elif treasury_yield > 4.0:
                interest_score = -1
            elif treasury_yield > 3.5:
                interest_score = 0
            elif treasury_yield > 3.0:
                interest_score = 1
            else:
                interest_score = 2  # Låga räntor = positivt

        # 2. INFLATION (20%) - Antar 2-3% som normalt (ingen live data)
        # Placeholder: Neutral 0 (kan inte hämta live CPI data enkelt)
        inflation_score = 0

        # 3. PMI (20%) - Placeholder (ingen enkel källa)
        # Antar 50-55 = neutral/expansion
        pmi_score = 1  # Optimistisk default

        # 4. VIX (15%)
        if vix_data:
            vix_value = vix_data['value']
            if vix_value >= 25:
                vix_score = -2  # Hög rädsla = negativt
            elif vix_value >= 20:
                vix_score = -1
            elif vix_value >= 15:
                vix_score = 0
            else:
                vix_score = 1  # Låg rädsla = positivt

        # 5. USD/SEK (10%)
        if usd_sek_data:
            usd_sek_value = usd_sek_data['value']
            if usd_sek_value >= 10.8:
                forex_score = 1  # Stark USD = positivt för export
            elif usd_sek_value >= 10.3:
                forex_score = 0
            else:
                forex_score = -1  # Svag USD = negativt

        # Beräkna viktad score (normalisera till 0-10)
        # Raw weighted score: -10 to +10 baserat på vikter
        weighted_score = (
            interest_score * 0.30 * 2.5 +  # Max ±2 * 0.30 * 2.5 = ±1.5
            inflation_score * 0.20 * 2.5 +  # Max ±2 * 0.20 * 2.5 = ±1.0
            pmi_score * 0.20 * 2.5 +  # Max ±2 * 0.20 * 2.5 = ±1.0
            vix_score * 0.15 * 2.5 +  # Max ±2 * 0.15 * 2.5 = ±0.75
            forex_score * 0.10 * 2.5  # Max ±1 * 0.10 * 2.5 = ±0.25
        )  # Total: ±4.5

        # Normalisera till 0-10 skala (5 = neutral)
        macro_score = 5 + weighted_score  # Range: 0.5 to 9.5
        macro_score = max(0, min(10, macro_score))  # Clamp 0-10

        # Klassificering
        if macro_score >= 8:
            classification = "Stark positiv makrotrend"
        elif macro_score >= 5:
            classification = "Neutral/stabil"
        else:
            classification = "Svag/negativ"

        return {
            'score': round(macro_score, 1),
            'classification': classification,
            'breakdown': {
                'interest_rate': {'score': interest_score, 'weight': '30%', 'value': treasury_data['value'] if treasury_data else None},
                'inflation': {'score': inflation_score, 'weight': '20%', 'value': None},  # Placeholder
                'pmi': {'score': pmi_score, 'weight': '20%', 'value': None},  # Placeholder
                'vix': {'score': vix_score, 'weight': '15%', 'value': vix_data['value'] if vix_data else None},
                'forex': {'score': forex_score, 'weight': '10%', 'value': usd_sek_data['value'] if usd_sek_data else None},
            }
        }

    def _calculate_market_regime(self) -> str:
        """
        Beräknar market regime baserat på makroindikatorer

        Returns:
            'bullish', 'bearish', eller 'transition'
        """
        vix_data = self.get_vix()
        if not vix_data:
            return 'transition'
        return self._calculate_market_regime_cached(vix_data)

    def _calculate_market_regime_cached(self, vix_data: Optional[Dict]) -> str:
        """
        Beräknar market regime från cached VIX data

        Args:
            vix_data: Pre-fetched VIX data

        Returns:
            'bullish', 'bearish', eller 'transition'
        """
        if not vix_data:
            return 'transition'

        vix_value = vix_data['value']

        if vix_value < 15:
            return 'bullish'
        elif vix_value > 25:
            return 'bearish'
        else:
            return 'transition'


# Test-funktion
if __name__ == "__main__":
    print("Testing Macro Data Fetcher...")
    print("="*60)

    fetcher = MacroDataFetcher()

    print("\nHämtar makrodata...")
    macro_data = fetcher.get_all_macro_data()

    print("\n📊 Macro Dashboard Data:")
    print(f"M2 Money Supply: {macro_data['m2']}")
    print(f"Fed Funds Rate: {macro_data['fedFunds']}")
    print(f"DXY: {macro_data['dxy']}")
    print(f"VIX: {macro_data['vix']}")
    print(f"Treasury 10Y: {macro_data['treasury10y']}")
    print(f"Market Regime: {macro_data['regime']}")
