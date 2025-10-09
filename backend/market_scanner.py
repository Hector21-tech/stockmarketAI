"""
Market Scanner - OMX30 Daily Scoring
Scores all OMX30 stocks daily for percentile-based position sizing
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from macro_data import MacroDataFetcher
from ai_service import ai_service
from news_fetcher import news_fetcher
from confidence_calculator import calculate_confidence
from signal_modes import get_mode_config


# OMX30 Stockholm constituents (as of 2024)
OMX30_TICKERS = [
    'ABB', 'ALFA', 'ASSA-B', 'ATCO-A', 'AZN', 'BOL',
    'ELUX-B', 'ERIC-B', 'ESSITY-B', 'EVO', 'GETI-B', 'HM-B',
    'HEXA-B', 'INVE-B', 'KINV-B', 'NIBE-B', 'NDA-SE',
    'SAND', 'SBB-B', 'SCA-B', 'SEB-A', 'SECU-B', 'SHB-A',
    'SKA-B', 'SKF-B', 'SWED-A', 'SWMA', 'TEL2-B', 'VOLV-B'
]


class MarketScanner:
    """
    Scans entire OMX30 index and scores all stocks
    Used for percentile-based position sizing
    """

    def __init__(self, mode: str = 'ai-hybrid'):
        self.fetcher = StockDataFetcher()
        self.analyzer = TechnicalAnalyzer()
        self.macro_fetcher = MacroDataFetcher()
        self.mode = mode
        self.mode_config = get_mode_config(mode)

    def scan_market(self, date: datetime = None, market: str = 'SE') -> List[Dict]:
        """
        Scan all OMX30 stocks and return scores

        Args:
            date: Date to scan for (default: today)
            market: Market (default: SE)

        Returns:
            List of dicts with {ticker, score, confidence, details}
        """
        if date is None:
            date = datetime.now()

        print(f"\n[Market Scanner] Scanning OMX30 for {date.strftime('%Y-%m-%d')}...")

        # Fetch macro data once (shared across all stocks)
        try:
            macro_data = self.macro_fetcher.get_all_macro_data()
            vix_data = macro_data.get('vix')
            spx_trend = macro_data.get('spx_trend')
            macro_regime = macro_data.get('regime')
            sentiment_data = macro_data.get('sentiment')
            macro_score_data = self.macro_fetcher.get_macro_score()
            macro_score = macro_score_data.get('score', 5.0) if macro_score_data else 5.0
        except Exception as e:
            print(f"  Warning: Could not fetch macro data: {e}")
            vix_data = None
            spx_trend = None
            macro_regime = None
            sentiment_data = None
            macro_score = 5.0

        results = []
        successful = 0
        failed = 0

        for ticker in OMX30_TICKERS:
            try:
                # Score individual stock
                stock_result = self._score_stock(
                    ticker=ticker,
                    market=market,
                    vix_data=vix_data,
                    spx_trend=spx_trend,
                    macro_regime=macro_regime,
                    macro_score=macro_score,
                    sentiment_data=sentiment_data
                )

                if stock_result:
                    results.append(stock_result)
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"  Error scoring {ticker}: {e}")
                failed += 1
                continue

        print(f"[Market Scanner] Complete: {successful} scored, {failed} failed")

        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)

        return results

    def _score_stock(self, ticker: str, market: str,
                     vix_data: Dict, spx_trend: Dict, macro_regime: str,
                     macro_score: float, sentiment_data: Dict) -> Dict:
        """
        Score individual stock using same logic as ai_engine

        Returns:
            Dict with ticker, score, confidence, technical details
        """
        try:
            # Fetch price data
            data = self.fetcher.get_historical_data(ticker, period='3mo', market=market)

            if data.empty or len(data) < 50:
                return None

            # Calculate technical indicators
            rsi = self.analyzer.calculate_rsi(data, period=14)
            macd, macd_signal, macd_hist = self.analyzer.calculate_macd(data)
            adx, plus_di, minus_di = self.analyzer.calculate_adx(data)

            # Get latest values
            current_rsi = rsi.iloc[-1]
            current_macd = macd.iloc[-1]
            current_macd_signal = macd_signal.iloc[-1]
            current_price = data['Close'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]

            # Volume analysis
            avg_volume_20 = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

            # Calculate 20-day MA
            ma20 = data['Close'].rolling(window=20).mean().iloc[-1]

            # Simplified technical scoring (Phase 3 logic)
            technical_score = 0

            # RSI
            if current_rsi < 45:
                technical_score += 2
            elif current_rsi < 50:
                technical_score += 1

            # MACD
            if len(macd) > 1:
                prev_macd = macd.iloc[-2]
                prev_macd_signal = macd_signal.iloc[-2]
                if prev_macd < prev_macd_signal and current_macd > current_macd_signal:
                    technical_score += 3  # Bullish crossover
                elif current_macd > current_macd_signal:
                    technical_score += 1

            # Price vs MA
            if current_price > ma20:
                technical_score += 1

            # MACD positive
            if current_macd > 0:
                technical_score += 1

            # Momentum
            if len(data) >= 5:
                price_5d_ago = data['Close'].iloc[-5]
                if current_price > price_5d_ago:
                    technical_score += 1

            # Volume filter
            if volume_ratio < 0.8:
                technical_score -= 1  # Penalty for low volume

            # ADX filter (trend strength)
            if not pd.isna(adx.iloc[-1]) and adx.iloc[-1] < 15:
                technical_score -= 1  # Penalty for choppy market

            # Convert technical score to -10 to +10 range
            base_score = (technical_score - 5) * 2

            # Calculate confidence using Phase 4 softer penalties
            vix_value = vix_data.get('value') if vix_data else None

            confidence_result = calculate_confidence(
                base_score=base_score,
                vix_value=vix_value,
                spx_trend=spx_trend,
                macro_regime=macro_regime,
                macro_score=macro_score,
                sentiment_data=sentiment_data
            )

            return {
                'ticker': ticker,
                'score': technical_score,  # Raw technical score (0-10+)
                'base_score': base_score,  # Normalized (-10 to +10)
                'confidence': confidence_result['confidence'],
                'confidence_level': confidence_result['level'],
                'recommended_size': confidence_result['recommended_size'],
                'price': current_price,
                'rsi': current_rsi,
                'macd': current_macd,
                'volume_ratio': volume_ratio,
                'risk_factors': confidence_result['risk_factors']
            }

        except Exception as e:
            # print(f"    Error in _score_stock for {ticker}: {e}")
            return None


# Singleton instance
market_scanner = MarketScanner()


# Test
if __name__ == "__main__":
    print("Testing Market Scanner...")
    print("=" * 70)

    scanner = MarketScanner(mode='ai-hybrid')

    # Scan current market
    results = scanner.scan_market()

    if results:
        print(f"\nTop 10 Stocks by Technical Score:")
        print("-" * 70)
        print(f"{'Rank':<6} {'Ticker':<10} {'Score':<8} {'Conf%':<8} {'Size':<10} {'Price':<10} {'RSI':<8}")
        print("-" * 70)

        for i, stock in enumerate(results[:10], 1):
            print(f"{i:<6} {stock['ticker']:<10} {stock['score']:<8.1f} "
                  f"{stock['confidence']:<8.1f} {stock['recommended_size']:<10} "
                  f"{stock['price']:<10.2f} {stock['rsi']:<8.1f}")

        print("-" * 70)

        # Show distribution
        sizes = {}
        for stock in results:
            size = stock['recommended_size']
            sizes[size] = sizes.get(size, 0) + 1

        print(f"\nPosition Size Distribution (All {len(results)} stocks):")
        for size in ['full', 'half', 'quarter', 'none']:
            count = sizes.get(size, 0)
            pct = (count / len(results)) * 100 if results else 0
            print(f"  {size.upper():<10}: {count:<3} ({pct:.1f}%)")

    else:
        print("No results returned")

    print("=" * 70)
