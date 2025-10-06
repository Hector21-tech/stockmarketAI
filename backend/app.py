"""
Flask REST API for MarketsAI
Exponerar backend-funktioner for mobilappen
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from ai_engine import MarketmateAI
from trade_manager import TradeManager
from notification_service import NotificationService
import json

app = Flask(__name__)
CORS(app)  # Tillat requests fran React Native

# Initiera services
fetcher = StockDataFetcher()
analyzer = TechnicalAnalyzer()
ai_engine = MarketmateAI()
trade_manager = TradeManager()
notification_service = NotificationService()


# ============ STOCK DATA ENDPOINTS ============

@app.route('/api/stock/price', methods=['GET'])
def get_stock_price():
    """Hamtar pris for en aktie"""
    ticker = request.args.get('ticker')
    market = request.args.get('market', 'SE')

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    price = fetcher.get_current_price(ticker, market)

    if price is None:
        return jsonify({'error': f'No data for {ticker}'}), 404

    return jsonify({
        'ticker': ticker,
        'price': price,
        'market': market
    })


@app.route('/api/stock/prices', methods=['POST'])
def get_multiple_prices():
    """Hamtar priser for flera aktier"""
    data = request.json
    tickers = data.get('tickers', [])
    market = data.get('market', 'SE')

    if not tickers:
        return jsonify({'error': 'tickers required'}), 400

    prices = fetcher.get_multiple_prices(tickers, market)

    return jsonify({
        'prices': prices,
        'market': market
    })


@app.route('/api/stock/info', methods=['GET'])
def get_stock_info():
    """Hamtar info om aktie"""
    ticker = request.args.get('ticker')
    market = request.args.get('market', 'SE')

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    info = fetcher.get_stock_info(ticker, market)

    return jsonify(info)


@app.route('/api/stock/historical', methods=['GET'])
def get_historical_data():
    """Hamtar historisk prisdata for charts med tekniska indikatorer"""
    ticker = request.args.get('ticker')
    market = request.args.get('market', 'SE')
    period = request.args.get('period', '3mo')  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    interval = request.args.get('interval', '1d')  # 1m, 5m, 15m, 1h, 1d, 1wk, 1mo

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    df = fetcher.get_historical_data(ticker, period, market)

    if df.empty:
        return jsonify({'error': f'No data for {ticker}'}), 404

    # Calculate technical indicators
    rsi = analyzer.calculate_rsi(df)
    macd_line, signal_line, histogram = analyzer.calculate_macd(df)
    ema_20 = analyzer.calculate_ema(df, 20)
    sma_50 = analyzer.calculate_sma(df, 50)
    k_percent, d_percent = analyzer.calculate_stochastic(df)
    bb_upper, bb_middle, bb_lower = analyzer.calculate_bollinger_bands(df)

    # Convert DataFrame to JSON-friendly format
    data = []
    for index, row in df.iterrows():
        idx = df.index.get_loc(index)

        data_point = {
            'timestamp': int(index.timestamp() * 1000),  # Convert to milliseconds
            'date': index.strftime('%Y-%m-%d'),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume']) if 'Volume' in row else 0,
        }

        # Add technical indicators (handle NaN values)
        if not pd.isna(rsi.iloc[idx]):
            data_point['rsi'] = float(rsi.iloc[idx])

        if not pd.isna(macd_line.iloc[idx]):
            data_point['macd'] = {
                'macd': float(macd_line.iloc[idx]),
                'signal': float(signal_line.iloc[idx]) if not pd.isna(signal_line.iloc[idx]) else None,
                'histogram': float(histogram.iloc[idx]) if not pd.isna(histogram.iloc[idx]) else None,
            }

        # Add moving averages
        if not pd.isna(ema_20.iloc[idx]):
            data_point['ema20'] = float(ema_20.iloc[idx])

        if not pd.isna(sma_50.iloc[idx]):
            data_point['sma50'] = float(sma_50.iloc[idx])

        # Add stochastic
        if not pd.isna(k_percent.iloc[idx]) and not pd.isna(d_percent.iloc[idx]):
            data_point['stochastic'] = {
                'k': float(k_percent.iloc[idx]),
                'd': float(d_percent.iloc[idx])
            }

        # Add bollinger bands
        if not pd.isna(bb_upper.iloc[idx]) and not pd.isna(bb_middle.iloc[idx]) and not pd.isna(bb_lower.iloc[idx]):
            data_point['bollinger'] = {
                'upper': float(bb_upper.iloc[idx]),
                'middle': float(bb_middle.iloc[idx]),
                'lower': float(bb_lower.iloc[idx])
            }

        data.append(data_point)

    return jsonify({
        'ticker': ticker,
        'market': market,
        'period': period,
        'interval': interval,
        'data': data,
        'count': len(data)
    })


# ============ AI ANALYSIS ENDPOINTS ============

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """Analyserar aktie med Marketmate AI"""
    data = request.json
    ticker = data.get('ticker')
    market = data.get('market', 'SE')

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    analysis = ai_engine.analyze_stock(ticker, market)

    return jsonify(analysis)


@app.route('/api/scan', methods=['POST'])
def scan_watchlist():
    """Skannar watchlist"""
    data = request.json
    tickers = data.get('tickers', [])
    market = data.get('market', 'SE')

    if not tickers:
        return jsonify({'error': 'tickers required'}), 400

    results = ai_engine.scan_watchlist(tickers, market)

    return jsonify({
        'results': results,
        'count': len(results)
    })


@app.route('/api/signals/buy', methods=['POST'])
def get_buy_signals():
    """Hamtar endast kopsignaler"""
    data = request.json
    tickers = data.get('tickers', [])
    market = data.get('market', 'SE')

    if not tickers:
        return jsonify({'error': 'tickers required'}), 400

    signals = ai_engine.get_buy_signals(tickers, market)

    return jsonify({
        'signals': signals,
        'count': len(signals)
    })


# ============ POSITION MANAGEMENT ENDPOINTS ============

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Hamtar alla oppna positioner"""
    positions = trade_manager.get_open_positions()

    return jsonify({
        'positions': [p.to_dict() for p in positions],
        'count': len(positions)
    })


@app.route('/api/positions', methods=['POST'])
def add_position():
    """Lagger till ny position"""
    data = request.json

    required_fields = ['ticker', 'entry_price', 'shares', 'stop_loss', 'targets']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} required'}), 400

    position = trade_manager.add_position(
        ticker=data['ticker'],
        entry_price=data['entry_price'],
        shares=data['shares'],
        stop_loss=data['stop_loss'],
        targets=data['targets'],
        market=data.get('market', 'SE')
    )

    return jsonify({
        'success': True,
        'position': position.to_dict()
    }), 201


@app.route('/api/positions/<ticker>', methods=['GET'])
def get_position_summary(ticker):
    """Hamtar sammanfattning for position"""
    summary = trade_manager.get_position_summary(ticker)

    if not summary:
        return jsonify({'error': f'No position found for {ticker}'}), 404

    return jsonify(summary)


@app.route('/api/positions/check', methods=['GET'])
def check_positions():
    """Kollar alla positioner mot targets och stop loss"""
    notifications = trade_manager.check_positions()

    return jsonify({
        'notifications': notifications,
        'count': len(notifications)
    })


@app.route('/api/positions/exit', methods=['POST'])
def execute_exit():
    """Registrerar exit (forsaljning)"""
    data = request.json

    required_fields = ['ticker', 'shares', 'exit_price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} required'}), 400

    success = trade_manager.execute_exit(
        ticker=data['ticker'],
        shares=data['shares'],
        exit_price=data['exit_price'],
        exit_type=data.get('exit_type', 'MANUAL')
    )

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to execute exit'}), 400


@app.route('/api/positions/stop-loss', methods=['PUT'])
def update_stop_loss():
    """Uppdaterar stop loss"""
    data = request.json

    if 'ticker' not in data or 'new_stop' not in data:
        return jsonify({'error': 'ticker and new_stop required'}), 400

    success = trade_manager.update_stop_loss(
        ticker=data['ticker'],
        new_stop=data['new_stop']
    )

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update stop loss'}), 400


# ============ UTILITY ENDPOINTS ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'MarketsAI API',
        'version': '1.0.0'
    })


@app.route('/api/market-status', methods=['GET'])
def market_status():
    """Kollar om marknaden ar oppen"""
    market = request.args.get('market', 'SE')

    is_open = fetcher.is_market_open(market)

    return jsonify({
        'market': market,
        'is_open': is_open
    })


# ============ STRATEGY ENDPOINT ============

@app.route('/api/strategy', methods=['GET'])
def get_strategy():
    """Returnerar Marketmate-strategin"""
    try:
        with open('../Marketmate_Strategy_v2.txt', 'r', encoding='utf-8') as f:
            strategy = f.read()

        return jsonify({
            'strategy': strategy
        })
    except FileNotFoundError:
        return jsonify({
            'strategy': ai_engine.STRATEGY
        })


# ============ NOTIFICATION ENDPOINTS ============

@app.route('/api/notifications/register', methods=['POST'])
def register_push_token():
    """Registrera push token for en anvandare"""
    data = request.json
    user_id = data.get('user_id', 'default')
    push_token = data.get('push_token')

    if not push_token:
        return jsonify({'error': 'push_token required'}), 400

    success = notification_service.register_push_token(user_id, push_token)

    if success:
        return jsonify({
            'success': True,
            'message': 'Push token registered successfully'
        })
    else:
        return jsonify({'error': 'Invalid push token'}), 400


@app.route('/api/notifications/unregister', methods=['POST'])
def unregister_push_token():
    """Ta bort push token"""
    data = request.json
    user_id = data.get('user_id', 'default')

    success = notification_service.remove_push_token(user_id)

    return jsonify({
        'success': success,
        'message': 'Push token removed' if success else 'No token found'
    })


@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """Skicka en push-notifikation"""
    data = request.json
    push_token = data.get('push_token')
    title = data.get('title')
    body = data.get('body')
    notification_data = data.get('data', {})

    if not push_token or not title or not body:
        return jsonify({'error': 'push_token, title, and body required'}), 400

    success = notification_service.send_notification(
        push_token,
        title,
        body,
        notification_data
    )

    if success:
        return jsonify({'success': True, 'message': 'Notification sent'})
    else:
        return jsonify({'error': 'Failed to send notification'}), 500


@app.route('/api/notifications/signal', methods=['POST'])
def send_signal_notification():
    """Skicka notifikation om ny trading signal"""
    data = request.json
    user_id = data.get('user_id', 'default')
    ticker = data.get('ticker')
    action = data.get('action')
    strength = data.get('strength')
    reason = data.get('reason')

    if not all([ticker, action, strength, reason]):
        return jsonify({'error': 'ticker, action, strength, and reason required'}), 400

    # Hamta push token for anvandaren
    tokens = notification_service.get_registered_tokens()
    push_token = tokens.get(user_id)

    if not push_token:
        return jsonify({'error': 'No push token registered for user'}), 404

    success = notification_service.notify_new_signal(
        push_token,
        ticker,
        action,
        strength,
        reason
    )

    if success:
        return jsonify({'success': True, 'message': 'Signal notification sent'})
    else:
        return jsonify({'error': 'Failed to send notification'}), 500


@app.route('/api/notifications/tokens', methods=['GET'])
def get_registered_tokens():
    """Hamta alla registrerade tokens (for admin/debug)"""
    tokens = notification_service.get_registered_tokens()
    return jsonify({
        'tokens': tokens,
        'count': len(tokens)
    })


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============ MAIN ============

if __name__ == '__main__':
    print("="*60)
    print("MarketsAI API starting...")
    print("="*60)
    print("\nEndpoints:")
    print("  GET  /api/health")
    print("  GET  /api/stock/price?ticker=VOLVO-B&market=SE")
    print("  POST /api/stock/prices")
    print("  GET  /api/stock/info?ticker=VOLVO-B")
    print("  GET  /api/stock/historical?ticker=VOLVO-B&period=3mo")
    print("  POST /api/analyze")
    print("  POST /api/scan")
    print("  POST /api/signals/buy")
    print("  GET  /api/positions")
    print("  POST /api/positions")
    print("  GET  /api/positions/<ticker>")
    print("  GET  /api/positions/check")
    print("  POST /api/positions/exit")
    print("  PUT  /api/positions/stop-loss")
    print("  GET  /api/market-status?market=SE")
    print("  GET  /api/strategy")
    print("  POST /api/notifications/register")
    print("  POST /api/notifications/unregister")
    print("  POST /api/notifications/send")
    print("  POST /api/notifications/signal")
    print("  GET  /api/notifications/tokens")
    print("\n" + "="*60)
    print("Running on http://127.0.0.1:5000")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
