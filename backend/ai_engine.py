"""
AI Trading Engine - Marketmate Strategy
Analyserar aktier enligt Marketmate-filosofin och genererar trade-signaler
"""

from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from typing import Dict, List, Optional
import json

class MarketmateAI:
    """
    AI-motor baserad pa Marketmate-strategin:
    - Likviditet (M2, Fed, räntor)
    - Sentiment (AAII, Fear & Greed, positionering)
    - Teknisk struktur (mönster, divergenser, volym, momentum)
    """

    # Ladda Marketmate-strategin
    STRATEGY = """
    MARKETMATE STRATEGY:

    1. FILOSOFI
    - Följ marknaden, inte förutse den
    - Ligga rätt i riktning, inte pricka topp/botten
    - Disciplin före gissning, Data före känsla

    2. TRADE SETUP
    - Entry: Köp vid teknisk bekräftelse
    - Position: 1/2 eller 1/3 size
    - Stop loss: Under stöd
    - Indikatorer: RSI, MACD, Stochastic

    3. ENTRY-SIGNALER
    - Positiv divergens i RSI (pris ner, RSI upp)
    - MACD bullish crossover
    - Stochastic oversold (<20) och vänder upp
    - Bryt över motstånd med volym
    - Tekniska mönster: bullflagga, triangel, breakout

    4. EXIT (1/3-REGELN)
    - +3-5% eller första motstånd → sälj 1/3
    - Flytta stop till break-even
    - Nästa 1/3 vid nästa motstånd
    - Flytta stop under swing-low
    - Sista 1/3 så länge trend kvarstår

    5. RISK
    - Max risk per case: 1.5-2%
    - Stop loss flyttas aldrig nedåt
    - All handel mekanisk, repeterbar
    """

    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.analyzer = TechnicalAnalyzer()

    def analyze_stock(self, ticker: str, market: str = "SE") -> Dict:
        """
        Fullständig analys av aktie enligt Marketmate-strategin

        Returns:
            Dict med analys, signal och trade-setup
        """
        # Hämta data
        data = self.fetcher.get_historical_data(ticker, period="3mo", market=market)

        if data.empty:
            return {'error': f'Ingen data for {ticker}'}

        # Teknisk analys
        tech_analysis = self.analyzer.get_full_analysis(data)

        # Generera signal
        signal = self._generate_signal(tech_analysis)

        # Beräkna entry, stop, targets
        trade_setup = self._calculate_trade_levels(tech_analysis, signal)

        return {
            'ticker': ticker,
            'market': market,
            'analysis': tech_analysis,
            'signal': signal,
            'trade_setup': trade_setup,
            'timestamp': data.index[-1].isoformat()
        }

    def _generate_signal(self, analysis: Dict) -> Dict:
        """
        Genererar köp/sälj/hold signal baserat på Marketmate-kriterier

        Returns:
            Dict med signal, styrka och motivering
        """
        signals = []
        score = 0

        # 1. RSI DIVERGENS (Marketmate letar avvikelser)
        if analysis.get('rsi_divergence') == 'bullish':
            signals.append('Positiv divergens i RSI')
            score += 3

        # 2. RSI OVERSOLD
        if analysis.get('rsi') and analysis['rsi'] < 30:
            signals.append('RSI oversold (<30)')
            score += 2

        # 3. MACD CROSSOVER
        if analysis.get('macd', {}).get('crossover') == 'bullish':
            signals.append('MACD bullish crossover')
            score += 2

        # 4. STOCHASTIC OVERSOLD OCH VÄNDER
        stoch = analysis.get('stochastic', {})
        if stoch.get('status') == 'oversold':
            signals.append('Stochastic oversold')
            score += 2

        # 5. PRIS ÖVER EMA (TREND)
        if analysis.get('trend') == 'bullish':
            signals.append('Pris över EMA20 (bullish trend)')
            score += 1

        # 6. VOLYM (kontrollera ovanlig volym)
        # TODO: Jämför med genomsnittlig volym

        # BEARISH SIGNALER
        bearish_score = 0

        if analysis.get('rsi_divergence') == 'bearish':
            signals.append('VARNING: Negativ divergens i RSI')
            bearish_score += 3

        if analysis.get('rsi') and analysis['rsi'] > 70:
            signals.append('VARNING: RSI overbought (>70)')
            bearish_score += 2

        if analysis.get('macd', {}).get('crossover') == 'bearish':
            signals.append('VARNING: MACD bearish crossover')
            bearish_score += 2

        # BESLUT
        net_score = score - bearish_score

        if net_score >= 5:
            action = 'BUY'
            strength = 'STRONG' if net_score >= 7 else 'MODERATE'
        elif net_score <= -5:
            action = 'SELL'
            strength = 'STRONG' if net_score <= -7 else 'MODERATE'
        else:
            action = 'HOLD'
            strength = 'WEAK'

        return {
            'action': action,
            'strength': strength,
            'score': net_score,
            'reasons': signals,
            'summary': self._generate_summary(action, signals)
        }

    def _calculate_trade_levels(self, analysis: Dict, signal: Dict) -> Dict:
        """
        Beräknar entry, stop loss och targets enligt Marketmate

        Entry: Nuvarande pris eller över motstånd
        Stop: Under stöd (max 2% risk)
        Target 1: +3-5% (1/3 position)
        Target 2: Nästa motstånd (1/3 position)
        Target 3: Hold så länge trend kvarstår
        """
        price = analysis['price']
        support = analysis.get('support', price * 0.95)
        resistance = analysis.get('resistance', price * 1.05)

        # Entry
        if signal['action'] == 'BUY':
            entry = price
        else:
            entry = None

        # Stop loss (under stöd, max 2% risk)
        stop_loss = support * 0.98
        risk_percent = ((price - stop_loss) / price) * 100

        # Targets (Marketmate 1/3-regel)
        target_1 = price * 1.04  # +4% (första 1/3)
        target_2 = resistance    # Nästa motstånd (andra 1/3)
        target_3 = price * 1.15  # +15% (sista 1/3, låt den rulla)

        return {
            'entry': round(entry, 2) if entry else None,
            'stop_loss': round(stop_loss, 2),
            'targets': {
                'target_1': {
                    'price': round(target_1, 2),
                    'gain_percent': 4.0,
                    'action': 'Sälj 1/3, flytta stop till break-even'
                },
                'target_2': {
                    'price': round(target_2, 2),
                    'gain_percent': round(((target_2 - price) / price) * 100, 1),
                    'action': 'Sälj 1/3, flytta stop under swing-low'
                },
                'target_3': {
                    'price': round(target_3, 2),
                    'gain_percent': 15.0,
                    'action': 'Håll så länge trend kvarstår'
                }
            },
            'risk_percent': round(risk_percent, 2),
            'risk_reward': round((target_1 - price) / (price - stop_loss), 2)
        }

    def _generate_summary(self, action: str, reasons: List[str]) -> str:
        """Genererar kort sammanfattning enligt Marketmate-stil"""
        if action == 'BUY':
            return f"Koplage. {'. '.join(reasons[:3])}."
        elif action == 'SELL':
            return f"Saljlage. {'. '.join(reasons[:3])}."
        else:
            return "Inget tydligt lage. Bevaka for signal."

    def scan_watchlist(self, tickers: List[str], market: str = "SE") -> List[Dict]:
        """
        Skannar flera aktier och returnerar de med starkast köpsignal

        Args:
            tickers: Lista med aktier att skanna
            market: Marknad

        Returns:
            Lista med analyser, sorterad efter signal-styrka
        """
        results = []

        for ticker in tickers:
            try:
                analysis = self.analyze_stock(ticker, market)
                if 'error' not in analysis:
                    results.append(analysis)
            except Exception as e:
                print(f"Fel vid analys av {ticker}: {e}")

        # Sortera efter signal score
        results.sort(
            key=lambda x: x['signal']['score'] if x['signal']['action'] == 'BUY' else -100,
            reverse=True
        )

        return results

    def get_buy_signals(self, tickers: List[str], market: str = "SE") -> List[Dict]:
        """
        Returnerar endast aktier med köpsignal

        Returns:
            Lista med köpsignaler
        """
        all_results = self.scan_watchlist(tickers, market)

        buy_signals = [
            r for r in all_results
            if r['signal']['action'] == 'BUY'
        ]

        return buy_signals


# Test-funktion
if __name__ == "__main__":
    print("Testing Marketmate AI Engine...")
    print("="*60)

    ai = MarketmateAI()

    # Test med några svenska aktier
    watchlist = ["VOLVO-B", "HM-B", "ERIC-B"]

    print("\nSkannar watchlist...")
    print("-"*60)

    results = ai.scan_watchlist(watchlist, market="SE")

    for result in results:
        if 'error' not in result:
            ticker = result['ticker']
            signal = result['signal']
            setup = result['trade_setup']
            analysis = result['analysis']

            print(f"\n{ticker}")
            print(f"Pris: {analysis['price']:.2f} SEK")
            print(f"Signal: {signal['action']} ({signal['strength']})")
            print(f"Score: {signal['score']}")
            print(f"RSI: {analysis['rsi']:.1f} ({analysis['rsi_status']})")
            print(f"Skal: {', '.join(signal['reasons'][:3])}")

            if setup['entry']:
                print(f"\nTRADE SETUP:")
                print(f"Entry: {setup['entry']} SEK")
                print(f"Stop: {setup['stop_loss']} SEK (Risk: {setup['risk_percent']}%)")
                print(f"Target 1: {setup['targets']['target_1']['price']} SEK (+{setup['targets']['target_1']['gain_percent']}%)")
                print(f"Target 2: {setup['targets']['target_2']['price']} SEK (+{setup['targets']['target_2']['gain_percent']}%)")

            print("-"*60)

    # Visa endast kopsignaler
    print("\n\nKOPSIGNALER:")
    print("="*60)

    buy_signals = ai.get_buy_signals(watchlist, market="SE")

    if buy_signals:
        for signal in buy_signals:
            print(f"\n{signal['ticker']}: {signal['signal']['summary']}")
    else:
        print("Inga kopsignaler just nu.")
