"""
Seasonality Service
Combines macro (S&P 500) + stock-specific seasonality with AI explanations
"""

import os
from datetime import datetime
from typing import Dict, Optional
import yfinance as yf

# Import from seasonality_analyzer
from seasonality_analyzer import get_monthly_returns, gemini_seasonality_analysis

# Import macro data for gates
from macro_data import MacroDataFetcher


class SeasonalityService:
    """
    Provides stock seasonality modifiers with regim-gates

    Philosophy:
    - Macro seasonality (S&P 500) = 80% weight (primary)
    - Stock seasonality = ±0.5 modifier (tie-breaker for Fas 3)
    - Gates: Bear regime = 0.5×, Risk-off = 0×
    """

    def __init__(self):
        self.cache = {}  # Simple dict cache for historical data
        self.macro_fetcher = MacroDataFetcher()

    def get_stock_modifier(
        self,
        ticker: str,
        month: Optional[int] = None,
        macro_data: Optional[Dict] = None,
        market: str = 'SE'
    ) -> Dict:
        """
        Calculate stock seasonality modifier with gates

        Args:
            ticker: Stock ticker (e.g., 'VOLV-B.ST')
            month: Month number 1-12 (default: current month)
            macro_data: Pre-fetched macro data (optional, for performance)

        Returns:
            {
                'modifier': float,           # -0.5 to +0.5
                'raw_return': float,         # Historical avg return %
                'confidence': str,           # 'none'/'low'/'medium'/'high'
                'n': int,                    # Sample size
                'ai_rationale': str,         # Gemini explanation
                'gated': bool,               # True if gates reduced/blocked
                'gate_reason': str | None    # Reason for gating
            }
        """
        if month is None:
            month = datetime.now().month

        # Convert ticker to yfinance format (add market suffix if needed)
        yf_ticker = self._format_ticker(ticker, market)

        # Fetch macro data if not provided
        if macro_data is None:
            macro_data = self.macro_fetcher.get_all_macro_data()

        # 1. Get historical data (cached)
        cache_key = f"{yf_ticker}_{month}"
        if cache_key in self.cache:
            hist_data = self.cache[cache_key]
        else:
            try:
                hist_data = get_monthly_returns(yf_ticker, years=10)
                self.cache[cache_key] = hist_data
            except Exception as e:
                print(f"Error fetching seasonality for {yf_ticker}: {e}")
                return self._empty_result(f"Data unavailable: {e}")

        # 2. Extract monthly return (convert decimal to percentage)
        raw_return_decimal = hist_data.get(month, 0.0)
        raw_return = raw_return_decimal * 100  # 0.055618 -> 5.56%

        # Count sample size (approximate: 10 years ≈ 10 samples per month)
        n = 10  # Could be improved by counting actual data points

        # 3. Determine confidence level based on sample size
        if n < 10:
            confidence = 'none'
            base_modifier = 0  # Too little data
        elif n < 20:
            confidence = 'low'
            base_modifier = raw_return * 0.025  # Scale to ±0.5 range
        else:
            confidence = 'medium'  # OMX rarely has >20 years clean data
            base_modifier = raw_return * 0.05

        # Cap at ±0.5
        base_modifier = max(-0.5, min(0.5, base_modifier))

        # 4. Apply gates
        gated = False
        gate_reason = None
        final_modifier = base_modifier

        # Get regime and VIX
        regime = macro_data.get('regime', 'transition')
        vix_data = macro_data.get('vix', {})
        vix = vix_data.get('value', 15) if vix_data else 15

        # Gate 1: Bear regime (halvera effekten)
        if regime == 'bearish':
            final_modifier *= 0.5
            gated = True
            gate_reason = 'Bear market regime'

        # Gate 2: Risk-off conditions (nollställ)
        # VIX ≥ 25 or SPX drawdown ≤ -10%
        spx_drawdown = self._get_spx_drawdown()
        if vix >= 25 or (spx_drawdown is not None and spx_drawdown <= -10):
            final_modifier = 0
            gated = True
            if vix >= 25:
                gate_reason = f'Risk-off: VIX {vix:.1f}'
            else:
                gate_reason = f'Risk-off: SPX {spx_drawdown:.1f}% drawdown'

        # 5. Get Gemini AI explanation (with fallback)
        ai_rationale = self._get_ai_explanation(yf_ticker, month, raw_return, n)

        return {
            'modifier': round(final_modifier, 2),
            'raw_return': round(raw_return, 2),
            'confidence': confidence,
            'n': n,
            'ai_rationale': ai_rationale,
            'gated': gated,
            'gate_reason': gate_reason
        }

    def _get_spx_drawdown(self) -> Optional[float]:
        """
        Calculate S&P 500 drawdown from 52-week high

        Returns:
            Drawdown percentage (negative number)
        """
        try:
            spx = yf.Ticker('^GSPC')
            hist = spx.history(period='1y')

            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            high_52w = hist['Close'].max()

            drawdown = ((current_price - high_52w) / high_52w) * 100
            return drawdown
        except Exception as e:
            print(f"Error calculating SPX drawdown: {e}")
            return None

    def _get_ai_explanation(
        self,
        ticker: str,
        month: int,
        raw_return: float,
        n: int
    ) -> str:
        """
        Get Gemini AI explanation for seasonality pattern
        Falls back to simple text if Gemini unavailable

        Args:
            ticker: Stock ticker
            month: Month number
            raw_return: Historical return %
            n: Sample size

        Returns:
            Human-readable explanation
        """
        # Check if Gemini is available
        if not os.getenv('GEMINI_API_KEY'):
            # Fallback to simple explanation
            return self._fallback_explanation(ticker, month, raw_return, n)

        try:
            # Try Gemini analysis
            result = gemini_seasonality_analysis(ticker, month)
            if result and 'rationale' in result:
                return result['rationale']
            else:
                return self._fallback_explanation(ticker, month, raw_return, n)
        except Exception as e:
            print(f"Gemini seasonality analysis failed: {e}")
            return self._fallback_explanation(ticker, month, raw_return, n)

    def _fallback_explanation(
        self,
        ticker: str,
        month: int,
        raw_return: float,
        n: int
    ) -> str:
        """
        Generate simple fallback explanation without AI

        Returns:
            Basic statistical description
        """
        month_name = datetime(2000, month, 1).strftime('%B')

        if abs(raw_return) < 1.0:
            bias = "neutral"
        elif raw_return > 0:
            bias = "positiv"
        else:
            bias = "negativ"

        confidence_note = ""
        if n < 15:
            confidence_note = " (begränsad historik)"

        return (
            f"{month_name} har historiskt {bias} bias för {ticker} "
            f"med genomsnittlig avkastning {raw_return:+.1f}% "
            f"baserat på {n} års data{confidence_note}."
        )

    def _format_ticker(self, ticker: str, market: str) -> str:
        """
        Convert ticker to yfinance format

        Args:
            ticker: Ticker symbol (e.g., 'VOLV-B' or 'AAPL')
            market: Market code ('SE', 'US', etc.)

        Returns:
            Formatted ticker for yfinance (e.g., 'VOLV-B.ST' for SE market)
        """
        # If ticker already has suffix, return as-is
        if '.' in ticker:
            return ticker

        # Add market suffix for non-US markets
        if market == 'SE':
            return f"{ticker}.ST"
        elif market == 'NO':
            return f"{ticker}.OL"
        elif market == 'DK':
            return f"{ticker}.CO"
        elif market == 'FI':
            return f"{ticker}.HE"
        # US stocks don't need suffix
        return ticker

    def _empty_result(self, reason: str) -> Dict:
        """
        Return empty result when data unavailable

        Args:
            reason: Reason for empty result

        Returns:
            Empty seasonality result
        """
        return {
            'modifier': 0.0,
            'raw_return': 0.0,
            'confidence': 'none',
            'n': 0,
            'ai_rationale': f"Ingen säsongsdata tillgänglig. {reason}",
            'gated': False,
            'gate_reason': None
        }


# Test function
if __name__ == "__main__":
    print("Testing Seasonality Service...")
    print("="*60)

    service = SeasonalityService()

    # Test tickers
    test_cases = [
        ('VOLV-B.ST', 10, 'Volvo Oktober'),
        ('KINV-B.ST', 7, 'Investor Juli'),
        ('HM-B.ST', 9, 'H&M September'),
    ]

    for ticker, month, description in test_cases:
        print(f"\n{description}:")
        print("-"*60)
        result = service.get_stock_modifier(ticker, month)
        print(f"Modifier: {result['modifier']:+.2f}")
        print(f"Raw Return: {result['raw_return']:+.2f}%")
        print(f"Confidence: {result['confidence']}")
        print(f"Gated: {result['gated']}")
        if result['gated']:
            print(f"Gate Reason: {result['gate_reason']}")
        print(f"AI Rationale: {result['ai_rationale']}")
