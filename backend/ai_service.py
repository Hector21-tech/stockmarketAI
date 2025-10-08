"""
AI Service using Google Gemini 2.0
Provides sentiment analysis and pattern detection
"""

import os
import google.generativeai as genai
from typing import Dict, List, Optional
import json

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class AIService:
    """
    AI Service wrapper för Gemini 2.0 Flash
    Används för sentiment analysis och pattern detection
    """

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp') if GEMINI_API_KEY else None
        self.enabled = bool(GEMINI_API_KEY)

    def analyze_sentiment(self, ticker: str, news_headlines: List[str]) -> Dict:
        """
        Analysera sentiment från news headlines med Gemini

        Args:
            ticker: Stock ticker
            news_headlines: Lista med headlines

        Returns:
            {
                'sentiment_score': 0-10 (0=very bearish, 5=neutral, 10=very bullish),
                'sentiment_label': 'Bullish'/'Neutral'/'Bearish',
                'reasoning': 'AI explanation'
            }
        """
        if not self.enabled or not news_headlines:
            return {
                'sentiment_score': 5.0,
                'sentiment_label': 'Neutral',
                'reasoning': 'No AI or news available'
            }

        try:
            # Prepare prompt
            headlines_text = "\n".join([f"- {h}" for h in news_headlines[:10]])  # Max 10

            prompt = f"""
Analyze the sentiment of these news headlines for stock {ticker}.

Headlines:
{headlines_text}

Provide your analysis in JSON format:
{{
    "sentiment_score": <number 0-10 where 0=very bearish, 5=neutral, 10=very bullish>,
    "sentiment_label": "<Bullish/Neutral/Bearish>",
    "reasoning": "<brief 1-sentence explanation>"
}}

Be conservative - only give extreme scores (0-2 or 8-10) for very strong sentiment.
"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse JSON från response
            # Remove markdown code blocks om de finns
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)

            # Validate och sanitize
            sentiment_score = max(0.0, min(10.0, float(result.get('sentiment_score', 5.0))))

            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': result.get('sentiment_label', 'Neutral'),
                'reasoning': result.get('reasoning', 'AI analysis')
            }

        except Exception as e:
            print(f"AI Sentiment error: {e}")
            return {
                'sentiment_score': 5.0,
                'sentiment_label': 'Neutral',
                'reasoning': f'AI error: {str(e)}'
            }

    def detect_patterns(self, ticker: str, price_data: List[Dict]) -> Dict:
        """
        Detektera chart patterns med Gemini

        Args:
            ticker: Stock ticker
            price_data: Lista med {date, open, high, low, close, volume}

        Returns:
            {
                'patterns': ['Double Bottom', 'Bull Flag'],
                'pattern_score': 0-10,
                'reasoning': 'AI explanation'
            }
        """
        if not self.enabled or not price_data:
            return {
                'patterns': [],
                'pattern_score': 0.0,
                'reasoning': 'No AI or data available'
            }

        try:
            # Ta senaste 20 candlesticks för pattern detection
            recent_candles = price_data[-20:]

            # Formatera data för AI
            candles_text = "\n".join([
                f"{i+1}. Close: {c.get('close', 0):.2f}, High: {c.get('high', 0):.2f}, Low: {c.get('low', 0):.2f}"
                for i, c in enumerate(recent_candles)
            ])

            prompt = f"""
Analyze this price data for stock {ticker} and identify chart patterns.

Recent 20 candles (oldest to newest):
{candles_text}

Look for patterns like:
- Double Bottom / Double Top
- Head and Shoulders / Inverse H&S
- Bull Flag / Bear Flag
- Triangle (ascending/descending)
- Cup and Handle
- Breakout patterns

Provide your analysis in JSON format:
{{
    "patterns": ["<pattern name 1>", "<pattern name 2>"],
    "pattern_score": <number 0-10 based on pattern strength>,
    "reasoning": "<brief 1-sentence explanation>"
}}

Only include patterns you're confident about (>70% confidence).
"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)

            # Validate
            pattern_score = max(0.0, min(10.0, float(result.get('pattern_score', 0.0))))

            return {
                'patterns': result.get('patterns', []),
                'pattern_score': pattern_score,
                'reasoning': result.get('reasoning', 'AI pattern detection')
            }

        except Exception as e:
            print(f"AI Pattern detection error: {e}")
            return {
                'patterns': [],
                'pattern_score': 0.0,
                'reasoning': f'AI error: {str(e)}'
            }

    def calculate_ai_score(self, ticker: str, technical_data: Dict, news_headlines: List[str] = None) -> Dict:
        """
        Beräknar total AI score baserat på sentiment + patterns + momentum

        Args:
            ticker: Stock ticker
            technical_data: Dict med price data, RSI, MACD, etc.
            news_headlines: Optional lista med news

        Returns:
            {
                'ai_score': 0-10,
                'sentiment_component': 0-4,
                'pattern_component': 0-3,
                'momentum_component': 0-3,
                'details': {...}
            }
        """
        ai_score = 0.0
        details = {}

        # 1. Sentiment Analysis (0-4 points)
        sentiment_component = 0.0
        if news_headlines and self.enabled:
            sentiment_result = self.analyze_sentiment(ticker, news_headlines)
            # Convert 0-10 scale to 0-4 points
            sentiment_score = sentiment_result['sentiment_score']
            if sentiment_score >= 7:
                sentiment_component = 4.0 * ((sentiment_score - 5) / 5)  # 7-10 → 1.6-4.0
            elif sentiment_score <= 3:
                sentiment_component = -2.0 * ((5 - sentiment_score) / 5)  # 0-3 → -2.0-0
            # 3-7 → 0-1.6 linear
            else:
                sentiment_component = 1.6 * ((sentiment_score - 3) / 4)

            details['sentiment'] = sentiment_result
        else:
            sentiment_component = 0.0  # Neutral när ingen news
            details['sentiment'] = {'reasoning': 'No news or AI disabled'}

        ai_score += max(0, sentiment_component)  # Only add positive sentiment

        # 2. Pattern Detection (0-3 points)
        pattern_component = 0.0
        if self.enabled and technical_data.get('price_history'):
            pattern_result = self.detect_patterns(ticker, technical_data['price_history'])
            # Convert 0-10 pattern_score to 0-3 points
            pattern_component = (pattern_result['pattern_score'] / 10) * 3
            details['patterns'] = pattern_result
        else:
            details['patterns'] = {'reasoning': 'No data or AI disabled'}

        ai_score += pattern_component

        # 3. Momentum Analysis (0-3 points) - Regelbaserad backup
        momentum_component = 0.0

        # ROC (Rate of Change)
        price = technical_data.get('price', 0)
        price_5d_ago = technical_data.get('price_5d_ago', price)
        if price_5d_ago > 0:
            roc = ((price - price_5d_ago) / price_5d_ago) * 100
            if roc > 5:
                momentum_component += 2.0
            elif roc > 2:
                momentum_component += 1.0

        # Volume momentum
        volume = technical_data.get('volume', 0)
        avg_volume = technical_data.get('avg_volume', volume)
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio > 1.5:
                momentum_component += 1.0
            elif volume_ratio > 1.2:
                momentum_component += 0.5

        momentum_component = min(3.0, momentum_component)  # Cap at 3
        ai_score += momentum_component

        details['momentum'] = {
            'roc': roc if 'roc' in locals() else 0,
            'volume_ratio': volume_ratio if 'volume_ratio' in locals() else 1.0,
            'score': momentum_component
        }

        return {
            'ai_score': round(ai_score, 1),
            'sentiment_component': round(sentiment_component, 1),
            'pattern_component': round(pattern_component, 1),
            'momentum_component': round(momentum_component, 1),
            'details': details
        }


# Singleton instance
ai_service = AIService()


# Test function
if __name__ == "__main__":
    print("Testing AI Service...")
    print("=" * 60)

    print(f"AI Enabled: {ai_service.enabled}")
    print(f"Model: {ai_service.model}")

    if ai_service.enabled:
        # Test sentiment
        test_headlines = [
            "Company reports record earnings",
            "Stock price soars on positive outlook",
            "Analysts upgrade to buy rating"
        ]

        sentiment = ai_service.analyze_sentiment("TEST", test_headlines)
        print(f"\nSentiment Analysis:")
        print(f"  Score: {sentiment['sentiment_score']}/10")
        print(f"  Label: {sentiment['sentiment_label']}")
        print(f"  Reasoning: {sentiment['reasoning']}")
    else:
        print("\nAI is disabled - set GEMINI_API_KEY in .env to enable")
