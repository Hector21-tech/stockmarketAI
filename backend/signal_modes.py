"""
Signal Modes Configuration
Olika tradinglägen för olika riskprofiler och produkttyper
"""

SIGNAL_MODES = {
    'conservative': {
        'name': 'Conservative',
        'icon': '🛡️',
        'description': 'Standardläge. Kräver bekräftelse, lägre risk. Passar aktieköp.',

        # Entry triggers
        'entry_triggers': {
            'breakout_confirmed': True,  # Pris över resistance
            'volume_required': True,     # Volym > 1.2x average
            'macd_crossover': False,     # MACD inte obligatorisk
            'rsi_threshold': 30,         # RSI < 30 för oversold
        },

        # Risk settings
        'stop_loss_buffer': 0.025,  # 2.5% under support
        'target_multiplier': 1.0,    # Standard targets
        'max_risk_percent': 3.0,     # Max 3% risk per trade

        # Scoring
        'tech_weight': 0.7,
        'macro_weight': 0.3,
        'min_buy_score': 4.0,        # Minst 4.0 för BUY
        'min_strong_score': 7.0,     # 7.0+ för STRONG BUY

        # Volume analysis
        'volume_spike_threshold': 1.2,  # 1.2x average
        'volume_weight': 1.0,           # Standard weight

        # Exit settings
        'trailing_stop': 0.015,      # 1.5% trailing
        'time_exit_days': 5,         # Exit om ingen rörelse på 5 dagar
    },

    'aggressive': {
        'name': 'Aggressive',
        'icon': '⚡',
        'description': 'Tidigt inträde vid momentum-start. Anpassad för Mini Futures / Bull-certifikat.',

        # Entry triggers
        'entry_triggers': {
            'breakout_confirmed': False,  # Early entry
            'early_breakout': True,       # Inom 1% av resistance
            'volume_required': True,      # Volym > 1.5x average
            'macd_crossover': True,       # MACD crossover räcker
            'rsi_threshold': 40,          # RSI < 40 (mindre oversold)
        },

        # Risk settings (tightare för leverage)
        'stop_loss_buffer': 0.012,  # 1.2% under support (vid 5x leverage = 6% loss)
        'target_multiplier': 1.3,    # Högre targets (30% mer ambitiösa)
        'max_risk_percent': 2.0,     # Max 2% risk (leverage amplifierar)

        # Scoring
        'tech_weight': 0.85,
        'macro_weight': 0.15,
        'ai_weight': 0.0,  # No AI in Aggressive mode
        'min_buy_score': 2.5,        # Lägre threshold för fler signaler
        'min_strong_score': 5.0,     # 5.0+ för STRONG BUY

        # Volume analysis (strängare)
        'volume_spike_threshold': 1.5,  # 1.5x average
        'volume_weight': 1.5,           # Högre vikt på volym

        # Exit settings (snabbare)
        'trailing_stop': 0.008,      # 0.8% trailing (tightare)
        'time_exit_days': 2,         # Exit om ingen rörelse på 2 dagar
    },

    'ai-hybrid': {
        'name': 'AI-Hybrid',
        'icon': '🤖',
        'description': 'AI-driven med sentiment + patterns. Balanserad mellan tech och AI insights.',

        # Entry triggers
        'entry_triggers': {
            'breakout_confirmed': False,  # Can enter before full breakout
            'early_breakout': True,       # Inom 2% av resistance
            'volume_required': True,      # Volym > 1.3x average
            'macd_crossover': False,      # MACD inte obligatorisk
            'rsi_threshold': 35,          # RSI < 35 för oversold
            'ai_sentiment_required': True,  # Kräver positiv AI sentiment
        },

        # Risk settings (mellan Conservative och Aggressive)
        'stop_loss_buffer': 0.018,  # 1.8% under support
        'target_multiplier': 1.15,   # Något högre targets (+15%)
        'max_risk_percent': 2.5,     # Max 2.5% risk per trade

        # Scoring (60% Tech, 30% AI, 10% Macro)
        'tech_weight': 0.6,
        'ai_weight': 0.3,
        'macro_weight': 0.1,
        'min_buy_score': 3.0,        # Mellan Conservative (4.0) och Aggressive (2.5)
        'min_strong_score': 6.0,     # 6.0+ för STRONG BUY

        # Volume analysis
        'volume_spike_threshold': 1.3,  # 1.3x average
        'volume_weight': 1.2,           # Något högre vikt på volym

        # Exit settings
        'trailing_stop': 0.012,      # 1.2% trailing
        'time_exit_days': 3,         # Exit om ingen rörelse på 3 dagar

        # AI-specific settings
        'use_ai': True,                  # Enable AI analysis
        'min_sentiment_score': 6.0,      # Min sentiment 6/10 för BUY
        'min_pattern_score': 3.0,        # Min pattern score 3/10
    }
}


def get_mode_config(mode='conservative'):
    """
    Hämtar konfiguration för ett signal mode

    Args:
        mode: 'conservative' eller 'aggressive'

    Returns:
        Dict med mode-konfiguration
    """
    if mode not in SIGNAL_MODES:
        print(f"Warning: Unknown mode '{mode}', falling back to conservative")
        mode = 'conservative'

    return SIGNAL_MODES[mode]


def get_available_modes():
    """
    Returnerar lista över tillgängliga modes

    Returns:
        List av dicts med mode info
    """
    modes = []
    for key, config in SIGNAL_MODES.items():
        modes.append({
            'id': key,
            'name': config['name'],
            'icon': config['icon'],
            'description': config['description'],
        })
    return modes


def validate_mode(mode):
    """
    Validerar att ett mode finns

    Args:
        mode: Mode ID

    Returns:
        True om valid, False annars
    """
    return mode in SIGNAL_MODES


# Export för enkel import
__all__ = ['SIGNAL_MODES', 'get_mode_config', 'get_available_modes', 'validate_mode']


# Test-funktion
if __name__ == "__main__":
    print("Testing Signal Modes...")
    print("=" * 60)

    modes = get_available_modes()
    for mode in modes:
        print(f"\n{mode['icon']} {mode['name']} ({mode['id']})")
        print(f"   {mode['description']}")

        config = get_mode_config(mode['id'])
        print(f"   Min BUY Score: {config['min_buy_score']}")
        print(f"   Stop Loss: {config['stop_loss_buffer']*100:.1f}%")
        print(f"   Tech/Macro: {config['tech_weight']}/{config['macro_weight']}")
        print(f"   Target Multiplier: {config['target_multiplier']}x")
