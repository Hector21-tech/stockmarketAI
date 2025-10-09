"""
MarketMate Confidence Calculator
Converts signal scores to confidence levels (0-100%) with risk adjustments
"""

from typing import Dict, Optional, List


def calculate_confidence(
    base_score: float,
    vix_value: Optional[float] = None,
    spx_trend: Optional[Dict] = None,
    macro_regime: Optional[str] = None,
    macro_score: Optional[float] = None,
    sentiment_data: Optional[Dict] = None
) -> Dict:
    """
    Calculate confidence level for a trading signal

    Args:
        base_score: Combined signal score (-10 to +10)
        vix_value: VIX level
        spx_trend: SPX vs 200MA data {bullish, above_ma, distance_pct}
        macro_regime: bullish/bearish/transition
        macro_score: Macro score (0-10)
        sentiment_data: Fear & Greed data

    Returns:
        Dict with confidence, level, risk_factors, recommended_size
    """

    # 1. NORMALIZE BASE SCORE TO 0-100
    # base_score range: -10 to +10
    # Normalized: 0 to 100 (50 = neutral)
    base_confidence = ((base_score + 10) / 20) * 100
    base_confidence = max(0, min(100, base_confidence))  # Clamp

    # 2. APPLY RISK ADJUSTMENTS
    risk_factors = []
    adjustments = 0

    # VIX - Volatility Risk
    if vix_value is not None:
        if vix_value > 30:
            adjustments -= 25
            risk_factors.append(f"High VIX ({vix_value:.1f}) - Market panic")
        elif vix_value > 25:
            adjustments -= 15
            risk_factors.append(f"Elevated VIX ({vix_value:.1f}) - Increased volatility")
        elif vix_value > 20:
            adjustments -= 5
            risk_factors.append(f"Moderate VIX ({vix_value:.1f})")
        elif vix_value < 15:
            adjustments += 10
            # No risk factor - this is positive

    # SPX Trend - Bull/Bear Market
    if spx_trend:
        if not spx_trend.get('bullish', True):
            adjustments -= 20
            distance = spx_trend.get('distance_pct', 0)
            risk_factors.append(f"Bear Market (SPX {distance:.1f}% below 200MA)")
        elif spx_trend.get('bullish', False):
            distance = spx_trend.get('distance_pct', 0)
            if distance > 5:
                adjustments += 15
                # Boost for strong bull market
            else:
                adjustments += 5

    # Macro Regime
    if macro_regime:
        if macro_regime == 'bearish':
            adjustments -= 15
            risk_factors.append("Bearish macro regime")
        elif macro_regime == 'bullish':
            adjustments += 10

    # Macro Score
    if macro_score is not None:
        if macro_score < 4:
            adjustments -= 10
            risk_factors.append(f"Weak macro (score {macro_score:.1f}/10)")
        elif macro_score > 7:
            adjustments += 10

    # Sentiment - Fear & Greed
    if sentiment_data and sentiment_data.get('fearGreed'):
        fg = sentiment_data['fearGreed']
        fg_label = fg.get('label', '')

        if 'Extreme Greed' in fg_label:
            adjustments -= 10
            risk_factors.append("Extreme Greed - Overheated market")
        elif 'Extreme Fear' in fg_label:
            adjustments += 5  # Contrarian opportunity

    # 3. CALCULATE FINAL CONFIDENCE
    final_confidence = base_confidence + adjustments
    final_confidence = max(0, min(100, final_confidence))  # Clamp to 0-100

    # 4. DETERMINE CONFIDENCE LEVEL
    if final_confidence >= 80:
        level = "STRONG_BUY"
        emoji = "[STRONG]"
        recommended_size = "full"
    elif final_confidence >= 65:
        level = "BUY"
        emoji = "[BUY]"
        recommended_size = "full"
    elif final_confidence >= 50:
        level = "WATCH"
        emoji = "[WATCH]"
        recommended_size = "half"
    elif final_confidence >= 35:
        level = "CAUTION"
        emoji = "[CAUTION]"
        recommended_size = "quarter"
    else:
        level = "AVOID"
        emoji = "[AVOID]"
        recommended_size = "none"

    # 5. BUILD RESPONSE
    return {
        'confidence': round(final_confidence, 1),
        'level': level,
        'emoji': emoji,
        'risk_factors': risk_factors,
        'recommended_size': recommended_size,
        'base_confidence': round(base_confidence, 1),
        'adjustments': round(adjustments, 1),
    }


def get_confidence_description(level: str) -> str:
    """Get user-friendly description of confidence level"""
    descriptions = {
        "STRONG_BUY": "High probability setup with favorable market conditions",
        "BUY": "Good setup with acceptable risk",
        "WATCH": "Moderate setup - consider reduced position size",
        "CAUTION": "Elevated risk - small position only",
        "AVOID": "High risk - wait for better conditions"
    }
    return descriptions.get(level, "Unknown")


def get_size_description(size: str) -> str:
    """Get description of recommended position size"""
    descriptions = {
        "full": "Full position (100% of planned size)",
        "half": "Half position (50% of planned size)",
        "quarter": "Quarter position (25% of planned size)",
        "none": "No position - wait for better setup"
    }
    return descriptions.get(size, "Unknown")


# Example usage and testing
if __name__ == "__main__":
    # Test Case 1: Strong signal in bull market
    print("=" * 60)
    print("TEST 1: Strong technical + Bull market + Low VIX")
    print("=" * 60)
    result = calculate_confidence(
        base_score=8.0,  # Strong technical
        vix_value=14.0,  # Low VIX
        spx_trend={'bullish': True, 'above_ma': True, 'distance_pct': 6.5},
        macro_regime='bullish',
        macro_score=7.5,
        sentiment_data={'fearGreed': {'label': 'Greed'}}
    )
    print(f"Confidence: {result['confidence']}%")
    print(f"Level: {result['emoji']} {result['level']}")
    print(f"Size: {result['recommended_size']}")
    print(f"Risk Factors: {result['risk_factors']}")
    print()

    # Test Case 2: Good signal but bear market + high VIX
    print("=" * 60)
    print("TEST 2: Good technical BUT Bear market + High VIX")
    print("=" * 60)
    result = calculate_confidence(
        base_score=6.0,  # Good technical
        vix_value=32.0,  # High VIX
        spx_trend={'bullish': False, 'above_ma': False, 'distance_pct': -8.2},
        macro_regime='bearish',
        macro_score=3.5,
        sentiment_data={'fearGreed': {'label': 'Extreme Fear'}}
    )
    print(f"Confidence: {result['confidence']}%")
    print(f"Level: {result['emoji']} {result['level']}")
    print(f"Size: {result['recommended_size']}")
    print(f"Risk Factors: {result['risk_factors']}")
    print()

    # Test Case 3: Weak signal in mixed conditions
    print("=" * 60)
    print("TEST 3: Moderate technical + Mixed conditions")
    print("=" * 60)
    result = calculate_confidence(
        base_score=4.0,  # Moderate
        vix_value=22.0,
        spx_trend={'bullish': True, 'above_ma': True, 'distance_pct': 2.1},
        macro_regime='transition',
        macro_score=5.0,
        sentiment_data={'fearGreed': {'label': 'Neutral'}}
    )
    print(f"Confidence: {result['confidence']}%")
    print(f"Level: {result['emoji']} {result['level']}")
    print(f"Size: {result['recommended_size']}")
    print(f"Risk Factors: {result['risk_factors']}")
    print("=" * 60)
