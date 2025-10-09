"""
AI Trading Engine - Marketmate Strategy
Analyserar aktier enligt Marketmate-filosofin och genererar trade-signaler
"""

from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from macro_data import MacroDataFetcher
from signal_modes import get_mode_config
from ai_service import ai_service
from seasonality_service import SeasonalityService
from confidence_calculator import calculate_confidence
from news_fetcher import news_fetcher
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
        self.macro_fetcher = MacroDataFetcher()
        self.seasonality_service = SeasonalityService()

    def analyze_stock(self, ticker: str, market: str = "SE", mode: str = "conservative") -> Dict:
        """
        Fullständig analys av aktie enligt Marketmate-strategin

        Args:
            ticker: Aktiesymbol
            market: Marknad (default SE)
            mode: Signal mode ('conservative' eller 'aggressive')

        Returns:
            Dict med analys, signal och trade-setup
        """
        # Hämta mode-konfiguration
        mode_config = get_mode_config(mode)
        # Hämta data
        data = self.fetcher.get_historical_data(ticker, period="3mo", market=market)

        if data.empty:
            return {'error': f'Ingen data for {ticker}'}

        # Teknisk analys
        tech_analysis = self.analyzer.get_full_analysis(data)

        # Hämta makrodata (full dict för seasonality service)
        macro_data = self.macro_fetcher.get_all_macro_data()
        macro_regime = macro_data.get('regime')
        vix_data = macro_data.get('vix')
        sentiment_data = macro_data.get('sentiment')
        macro_score_data = self.macro_fetcher.get_macro_score()

        # Generera signal (inkluderar ticker, market, macro context och mode)
        signal = self._generate_signal(
            analysis=tech_analysis,
            ticker=ticker,
            market=market,
            macro_regime=macro_regime,
            vix_data=vix_data,
            sentiment_data=sentiment_data,
            macro_score_data=macro_score_data,
            macro_data=macro_data,
            mode_config=mode_config
        )

        # Beräkna entry, stop, targets (med mode config)
        trade_setup = self._calculate_trade_levels(tech_analysis, signal, mode_config)

        # Hämta företagsnamn
        try:
            stock_info = self.fetcher.get_stock_info(ticker, market)
            company_name = stock_info.get('longName', stock_info.get('shortName', ticker))
        except:
            company_name = ticker

        return {
            'ticker': ticker,
            'name': company_name,
            'market': market,
            'analysis': tech_analysis,
            'signal': signal,
            'trade_setup': trade_setup,
            'macro_context': {
                'regime': macro_regime,
                'vix': vix_data.get('value') if vix_data else None,
                'fear_greed': sentiment_data.get('fearGreed', {}).get('label') if sentiment_data else None,
                'macro_score': macro_score_data.get('score') if macro_score_data else 5.0,
                'macro_classification': macro_score_data.get('classification') if macro_score_data else 'Unknown',
            },
            'timestamp': data.index[-1].isoformat()
        }

    def _generate_signal(self, analysis: Dict, ticker: str = None, market: str = 'SE',
                        macro_regime: str = None, vix_data: Dict = None, sentiment_data: Dict = None,
                        macro_score_data: Dict = None, macro_data: Dict = None,
                        mode_config: Dict = None) -> Dict:
        """
        Genererar köp/sälj/hold signal baserat på Marketmate-kriterier
        ENHANCED: Nu inkluderar macro regime, VIX, sentiment, seasonality OCH signal mode
        FORMULA: TotalScore = (Technical * tech_weight) + (Macro+Seasonality * macro_weight)

        Args:
            ticker: Stock ticker (för seasonality lookup)
            market: Market code ('SE', 'US', etc.) for ticker formatting
            macro_data: Full macro data dict (för seasonality gates)

        Returns:
            Dict med signal, styrka och motivering
        """
        # Default mode config om inte angiven
        if mode_config is None:
            from signal_modes import get_mode_config
            mode_config = get_mode_config('conservative')
        signals = []
        technical_score = 0

        # === TECHNICAL INDICATORS ===

        # 1. RSI DIVERGENS (Marketmate letar avvikelser)
        if analysis.get('rsi_divergence') == 'bullish':
            signals.append('Positiv divergens i RSI')
            technical_score += 3

        # 2. RSI OVERSOLD
        if analysis.get('rsi') and analysis['rsi'] < 30:
            signals.append('RSI oversold (<30)')
            technical_score += 2

        # 3. MACD CROSSOVER
        if analysis.get('macd', {}).get('crossover') == 'bullish':
            signals.append('MACD bullish crossover')
            technical_score += 2

        # 4. STOCHASTIC OVERSOLD OCH VÄNDER
        stoch = analysis.get('stochastic', {})
        if stoch.get('status') == 'oversold':
            signals.append('Stochastic oversold')
            technical_score += 2

        # 5. PRIS ÖVER EMA (TREND)
        if analysis.get('trend') == 'bullish':
            signals.append('Pris över EMA20 (bullish trend)')
            technical_score += 1

        # 6. VOLYM ANALYS (Marketmate: Volym bekräftar rörelsen!)
        volume_ratio = analysis.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:  # Volym 50% över genomsnitt
            signals.append(f'Hög volym ({volume_ratio:.1f}x genomsnitt)')
            technical_score += 2
        elif volume_ratio > 1.2:  # Volym 20% över genomsnitt
            signals.append(f'Ökad volym ({volume_ratio:.1f}x genomsnitt)')
            technical_score += 1

        # 7. BREAKOUT DETECTION (MarketMate: Trendbrott och breakouts!)
        price = analysis.get('price')
        resistance = analysis.get('resistance')
        support = analysis.get('support')

        # Breakout över resistance
        if resistance and price > resistance * 0.98:  # Inom 2% av breakout
            if price > resistance:
                signals.append('BREAKOUT över motstånd!')
                technical_score += 3  # Starkt köpsignal
            else:
                signals.append('Nära breakout över motstånd')
                technical_score += 1

        # Support håller (pris nära support men över)
        if support and price < support * 1.03 and price > support:
            signals.append('Support håller')
            technical_score += 1

        # === MACRO & SENTIMENT FACTORS ===

        # 8. MARKET REGIME (Marketmate: Likviditet och makro är viktigt!)
        if macro_regime:
            if macro_regime == 'bullish':
                signals.append('BULLISH macro regime')
                technical_score += 2  # Öka viktningen för bullish regime
            elif macro_regime == 'bearish':
                signals.append('[!] BEARISH macro regime')
                technical_score -= 2  # Minska score vid bearish regime

        # 9. VIX / FEAR INDEX
        if vix_data and vix_data.get('value'):
            vix_value = vix_data['value']
            if vix_value < 15:  # Low fear = good for risk assets
                signals.append('Low VIX (complacency)')
                technical_score += 1
            elif vix_value > 25:  # High fear = caution
                signals.append('[!] Elevated VIX (fear)')
                technical_score -= 1

        # 10. SENTIMENT (Fear & Greed)
        if sentiment_data and sentiment_data.get('fearGreed'):
            fg = sentiment_data['fearGreed']
            fg_label = fg.get('label', '')
            if 'Extreme Fear' in fg_label:
                signals.append('Extreme Fear (contrarian buy)')
                technical_score += 2
            elif 'Fear' in fg_label:
                signals.append('Fear sentiment (opportunity)')
                technical_score += 1
            elif 'Extreme Greed' in fg_label:
                signals.append('[!] Extreme Greed (caution)')
                technical_score -= 2

        # === BEARISH SIGNALS ===
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

        # TECHNICAL NET SCORE
        net_technical_score = technical_score - bearish_score

        # === MACRO SCORE INTEGRATION ===
        # Hämta Macro Score (0-10, där 5 är neutral)
        macro_score = 5.0  # Default neutral
        if macro_score_data:
            macro_score = macro_score_data.get('score', 5.0)
            # Lägg till macro score i reasons
            macro_classification = macro_score_data.get('classification', 'Unknown')
            signals.append(f'Makro Score: {macro_score:.1f}/10 ({macro_classification})')

        # === STOCK SEASONALITY MODIFIER ===
        # Hämta stock-specific seasonality modifier (±0.5 poäng med gates)
        seasonality_result = None
        seasonality_modifier = 0.0

        if ticker and macro_data:
            try:
                seasonality_result = self.seasonality_service.get_stock_modifier(
                    ticker=ticker,
                    market=market,
                    macro_data=macro_data
                )
                seasonality_modifier = seasonality_result.get('modifier', 0.0)

                # Lägg till seasonality i signals om modifier != 0
                if seasonality_modifier != 0:
                    raw_return = seasonality_result.get('raw_return', 0)
                    confidence = seasonality_result.get('confidence', 'none')
                    signals.append(
                        f"Seasonal Modifier: {seasonality_modifier:+.2f} "
                        f"(historiskt {raw_return:+.1f}%, {confidence} confidence)"
                    )

                    # Visa gate warning om applicable
                    if seasonality_result.get('gated'):
                        gate_reason = seasonality_result.get('gate_reason')
                        signals.append(f"[!] Seasonal boost reduced: {gate_reason}")
            except Exception as e:
                print(f"Warning: Could not fetch seasonality for {ticker}: {e}")

        # Apply seasonality modifier to macro score
        # Range: macro_score (0-10) + seasonality_modifier (±0.5)
        adjusted_macro_score = macro_score + seasonality_modifier

        # === AI SCORE (för AI-Hybrid mode) ===
        ai_score = 0
        ai_details = None
        ai_weight = mode_config.get('ai_weight', 0.0)

        if ai_weight > 0 and mode_config.get('use_ai', False):
            # Hämta AI score med news sentiment och pattern detection
            # Fetch real news headlines from yfinance
            news_headlines = []
            try:
                if ticker and market:
                    news_headlines = news_fetcher.get_news_headlines(ticker, market, limit=10)
                    print(f"[AI-Hybrid] Fetched {len(news_headlines)} news headlines for {ticker}")
            except Exception as e:
                print(f"[AI-Hybrid] Error fetching news: {e}")
                news_headlines = []

            technical_data = {
                'price': analysis.get('price'),
                'price_5d_ago': analysis.get('price') * 0.97,  # Placeholder
                'volume': analysis.get('volume'),
                'avg_volume': analysis.get('volume', 0) / (analysis.get('volume_ratio', 1.0) or 1.0),
                'price_history': []  # Placeholder - skulle komma från historical data
            }

            ai_result = ai_service.calculate_ai_score(
                ticker=ticker or 'TEMP',
                technical_data=technical_data,
                news_headlines=news_headlines
            )

            # Normalize AI score from 0-10 to match technical scale (-10 to +10)
            # AI 5 = neutral (0), AI 10 = very bullish (+10), AI 0 = very bearish (-10)
            ai_score = (ai_result['ai_score'] - 5) * 2  # Range: -10 to +10
            ai_details = ai_result

            # Lägg till AI components i signals
            if ai_result['sentiment_component'] > 0:
                signals.append(f"[AI] Sentiment: {ai_result['sentiment_component']:.1f}/4")
            if ai_result['pattern_component'] > 0:
                signals.append(f"[AI] Patterns: {ai_result['pattern_component']:.1f}/3")
            signals.append(f"[AI] Momentum: {ai_result['momentum_component']:.1f}/3")

        # MARKETMATE FORMULA: TotalScore = (Technical * weight) + (AI * weight) + (Macro+Seasonality * weight)
        # Normalize adjusted_macro_score from 0-10 to match technical scale (-10 to +10)
        # Macro 5 = neutral (0), Macro 10 = bullish (+10), Macro 0 = bearish (-10)
        # Note: adjusted_macro_score includes seasonality modifier (±0.5)
        normalized_macro = (adjusted_macro_score - 5) * 2  # Range: -10 to +10

        # Combined score (använd mode config weights)
        tech_weight = mode_config.get('tech_weight', 0.7)
        macro_weight = mode_config.get('macro_weight', 0.3)

        if ai_weight > 0:
            # AI-Hybrid mode: (Tech * 0.6) + (AI * 0.3) + (Macro * 0.1)
            combined_score = (net_technical_score * tech_weight) + (ai_score * ai_weight) + (normalized_macro * macro_weight)
        else:
            # Conservative/Aggressive mode: (Tech * weight) + (Macro * weight)
            combined_score = (net_technical_score * tech_weight) + (normalized_macro * macro_weight)

        # MACRO BIAS LOGIC
        # Adjusted Macro < 4: Tone down buy signals (reduce score)
        # Adjusted Macro > 7: Strengthen signals (boost score)
        if adjusted_macro_score < 4:
            combined_score -= 1  # Penalty for weak macro
            signals.append('[!] Svag makro - ton down signals')
        elif adjusted_macro_score > 7:
            combined_score += 1  # Bonus for strong macro
            signals.append('Stark makro - boost signals')

        # BESLUT (baserat på combined_score och mode config)
        min_buy_score = mode_config.get('min_buy_score', 4.0)
        min_strong_score = mode_config.get('min_strong_score', 7.0)

        if combined_score >= min_buy_score:
            action = 'BUY'
            strength = 'STRONG' if combined_score >= min_strong_score else 'MODERATE'
        elif combined_score <= -min_buy_score:
            action = 'SELL'
            strength = 'STRONG' if combined_score <= -min_strong_score else 'MODERATE'
        else:
            action = 'HOLD'
            strength = 'NEUTRAL'

        # CALCULATE CONFIDENCE (MarketMate Risk-Adjusted)
        vix_value = vix_data.get('value') if vix_data else None
        spx_trend = macro_data.get('spx_trend') if macro_data else None

        confidence_result = calculate_confidence(
            base_score=combined_score,
            vix_value=vix_value,
            spx_trend=spx_trend,
            macro_regime=macro_regime,
            macro_score=macro_score,
            sentiment_data=sentiment_data
        )

        result = {
            'action': action,
            'strength': strength,
            'score': round(combined_score, 1),
            'technical_score': net_technical_score,
            'macro_score': macro_score,
            'adjusted_macro_score': round(adjusted_macro_score, 2),
            'reasons': signals,
            'summary': self._generate_summary(action, signals),
            # CONFIDENCE DATA
            'confidence': confidence_result['confidence'],
            'confidence_level': confidence_result['level'],
            'confidence_emoji': confidence_result['emoji'],
            'risk_factors': confidence_result['risk_factors'],
            'recommended_size': confidence_result['recommended_size'],
        }

        # Lägg till AI score om det användes
        if ai_weight > 0 and ai_details:
            result['ai_score'] = ai_details['ai_score']
            result['ai_details'] = ai_details

        # Lägg till seasonality data om det finns
        if seasonality_result:
            result['seasonality'] = {
                'modifier': seasonality_result.get('modifier', 0),
                'raw_return': seasonality_result.get('raw_return', 0),
                'confidence': seasonality_result.get('confidence', 'none'),
                'ai_rationale': seasonality_result.get('ai_rationale', ''),
                'gated': seasonality_result.get('gated', False),
                'gate_reason': seasonality_result.get('gate_reason')
            }

        return result

    def _calculate_trade_levels(self, analysis: Dict, signal: Dict, mode_config: Dict = None) -> Dict:
        """
        Beräknar entry, stop loss och targets enligt Marketmate

        Entry: Nuvarande pris eller över motstånd
        Stop: Under stöd (varierar med mode)
        Target 1: +3-5% (1/3 position)
        Target 2: Nästa motstånd (1/3 position)
        Target 3: Hold så länge trend kvarstår
        """
        # Default mode config om inte angiven
        if mode_config is None:
            from signal_modes import get_mode_config
            mode_config = get_mode_config('conservative')

        price = analysis['price']
        support = analysis.get('support', price * 0.95)
        resistance = analysis.get('resistance', price * 1.05)

        # Entry
        if signal['action'] == 'BUY':
            entry = price
        else:
            entry = None

        # Stop loss (använd mode config buffer)
        stop_loss_buffer = mode_config.get('stop_loss_buffer', 0.025)
        support_based_stop = support * (1 - stop_loss_buffer * 0.2)  # 20% av buffer under support
        price_based_stop = price * (1 - stop_loss_buffer)  # Full buffer under price

        # Använd det som ger tightest stop (högre värde)
        stop_loss = max(support_based_stop, price_based_stop)

        risk_percent = ((price - stop_loss) / price) * 100

        # Targets (Marketmate 1/3-regel) - MÅSTE vara stigande!
        # FIX: Multiplicera PROCENT-avståndet, inte prisnivån
        target_multiplier = mode_config.get('target_multiplier', 1.0)

        # Base percentages för Conservative mode
        base_t1_pct = 0.04    # +4%
        base_t2_pct = 0.071   # +7.1% (ca resistance distance)
        base_t3_pct = 0.15    # +15%

        # Apply multiplier till percentages (inte priset!)
        adjusted_t1_pct = base_t1_pct * target_multiplier
        adjusted_t2_pct = base_t2_pct * target_multiplier
        adjusted_t3_pct = base_t3_pct * target_multiplier

        # Beräkna targets från entry (only if entry exists)
        if entry is not None:
            target_1 = entry * (1 + adjusted_t1_pct)

            # Target 2: Använd adjusted percentage, men säkerställ minst +3% över T1
            target_2_from_pct = entry * (1 + adjusted_t2_pct)
            target_2 = max(target_2_from_pct, target_1 * 1.03)

            # Target 3: Använd adjusted percentage, men säkerställ minst +5% över T2
            target_3_from_pct = entry * (1 + adjusted_t3_pct)
            target_3 = max(target_3_from_pct, target_2 * 1.05)

            # Räkna gain_percent korrekt från entry (inte price)
            gain_1 = ((target_1 - entry) / entry) * 100
            gain_2 = ((target_2 - entry) / entry) * 100
            gain_3 = ((target_3 - entry) / entry) * 100

            # Räkna R/R korrekt
            risk = entry - stop_loss
            reward_t1 = target_1 - entry
            reward_t2 = target_2 - entry
            rr_t1 = reward_t1 / risk if risk > 0 else 0
            rr_t2 = reward_t2 / risk if risk > 0 else 0

            return {
                'entry': round(entry, 2),
                'stop_loss': round(stop_loss, 2),
                'targets': {
                    'target_1': {
                        'price': round(target_1, 2),
                        'gain_percent': round(gain_1, 1),
                        'action': 'Sälj 1/3, flytta stop till break-even'
                    },
                    'target_2': {
                        'price': round(target_2, 2),
                        'gain_percent': round(gain_2, 1),
                        'action': 'Sälj 1/3, flytta stop under swing-low'
                    },
                    'target_3': {
                        'price': round(target_3, 2),
                        'gain_percent': round(gain_3, 1),
                        'action': 'Håll så länge trend kvarstår'
                    }
                },
                'risk_percent': round(risk_percent, 2),
                'risk_reward': round(rr_t2, 2)  # Använd T2 för mer realistisk R/R
            }
        else:
            # No entry = no targets (HOLD or SELL signal)
            return {
                'entry': None,
                'stop_loss': round(stop_loss, 2),
                'targets': None,
                'risk_percent': round(risk_percent, 2),
                'risk_reward': None
            }

    def _generate_summary(self, action: str, reasons: List[str]) -> str:
        """Genererar kort sammanfattning enligt Marketmate-stil"""
        if action == 'BUY':
            return f"Köpläge. {'. '.join(reasons[:3])}."
        elif action == 'SELL':
            return f"Säljläge. {'. '.join(reasons[:3])}."
        else:
            return "Neutral. Inget tydligt läge — avvakta bättre setup."

    def scan_watchlist(self, tickers: List[str], market: str = "SE", mode: str = "conservative") -> List[Dict]:
        """
        Skannar flera aktier och returnerar de med starkast köpsignal

        Args:
            tickers: Lista med aktier att skanna
            market: Marknad
            mode: Signal mode ('conservative' eller 'aggressive')

        Returns:
            Lista med analyser, sorterad efter signal-styrka
        """
        results = []

        for ticker in tickers:
            try:
                analysis = self.analyze_stock(ticker, market, mode)
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

    def get_buy_signals(self, tickers: List[str], market: str = "SE", mode: str = "conservative") -> List[Dict]:
        """
        Returnerar endast aktier med köpsignal

        Args:
            tickers: Lista med aktier
            market: Marknad
            mode: Signal mode ('conservative' eller 'aggressive')

        Returns:
            Lista med köpsignaler
        """
        all_results = self.scan_watchlist(tickers, market, mode)

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
