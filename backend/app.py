"""
Flask REST API for MarketsAI
Exponerar backend-funktioner for mobilappen
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from ai_engine import MarketmateAI
from trade_manager import TradeManager
from portfolio_analytics import PortfolioAnalytics
from notification_service import NotificationService
from macro_data import MacroDataFetcher
from signal_modes import get_available_modes, get_mode_config, validate_mode
from alert_scheduler import get_scheduler
import json
import pandas as pd
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# CORS Configuration - Allow requests from Expo web and mobile
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:8082",
            "http://localhost:8083",
            "http://localhost:19000",
            "http://localhost:19006",
            "http://192.168.1.46:8082",
            "http://192.168.1.46:19000",
            "*"  # Allow all for development
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initiera services
fetcher = StockDataFetcher()
analyzer = TechnicalAnalyzer()
ai_engine = MarketmateAI()
trade_manager = TradeManager()
portfolio_analytics = PortfolioAnalytics(trade_manager)
notification_service = NotificationService()
macro_fetcher = MacroDataFetcher()


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


@app.route('/api/stock/quotes', methods=['POST'])
def get_multiple_quotes():
    """Hamtar fullstandiga quotes (pris + change) for flera aktier"""
    data = request.json
    tickers = data.get('tickers', [])
    market = data.get('market', 'SE')

    if not tickers:
        return jsonify({'error': 'tickers required'}), 400

    quotes = fetcher.get_multiple_quotes(tickers, market)

    return jsonify({
        'quotes': quotes,
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


@app.route('/api/stock/search', methods=['GET'])
def search_stocks():
    """Soker efter aktier baserat pa namn eller ticker"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({'results': []})

    if len(query) < 1:
        return jsonify({'results': []})

    results = fetcher.search_ticker(query, limit)

    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })


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


@app.route('/api/stock/omx30', methods=['GET'])
def get_omx30_list():
    """
    Returnerar alla OMX30-aktier med basic info (SNABBT - ingen API call)
    Frontend hamtar priser separat via /api/stock/quotes
    """
    from tickers import OMX30_TICKERS

    # Try to use metadata cache (instant, no API calls)
    try:
        from stock_metadata_cache import StockMetadataCache
        cache = StockMetadataCache()

        stocks = []
        for ticker in OMX30_TICKERS:
            # Get from cache (instant)
            cached = cache.get(ticker, 'SE')

            if cached:
                # Use cached data
                stocks.append({
                    'ticker': cached['ticker'],
                    'name': cached['name'],
                    'market': 'SE',
                    'exchange': 'Stockholm',
                    'symbol': cached['symbol']
                })
            else:
                # Fallback: basic info without API call
                stocks.append({
                    'ticker': ticker,
                    'name': ticker,  # Frontend will update with real name
                    'market': 'SE',
                    'exchange': 'Stockholm',
                    'symbol': fetcher.get_ticker_symbol(ticker, 'SE')
                })

        return jsonify({
            'index': 'OMX30',
            'count': len(stocks),
            'stocks': stocks
        })

    except Exception as e:
        print(f"[WARN] Cache failed, using fallback: {e}")
        # Fallback: return basic info without API calls
        stocks = []
        for ticker in OMX30_TICKERS:
            stocks.append({
                'ticker': ticker,
                'name': ticker,
                'market': 'SE',
                'exchange': 'Stockholm',
                'symbol': fetcher.get_ticker_symbol(ticker, 'SE')
            })

        return jsonify({
            'index': 'OMX30',
            'count': len(stocks),
            'stocks': stocks
        })


# ============ AI ANALYSIS ENDPOINTS ============

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """Analyserar aktie med Marketmate AI"""
    data = request.json
    ticker = data.get('ticker')
    market = data.get('market', 'SE')
    mode = data.get('mode', 'conservative')  # Default: conservative

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    analysis = ai_engine.analyze_stock(ticker, market, mode=mode)

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
    mode = data.get('mode', 'conservative')

    if not tickers:
        return jsonify({'error': 'tickers required'}), 400

    signals = ai_engine.get_buy_signals(tickers, market, mode)

    return jsonify({
        'signals': signals,
        'count': len(signals),
        'mode': mode
    })


# ============ SIGNAL MODES ENDPOINTS ============

@app.route('/api/signal-modes', methods=['GET'])
def get_signal_modes():
    """Hämtar tillgängliga signal modes"""
    modes = get_available_modes()
    return jsonify({
        'modes': modes,
        'count': len(modes)
    })


@app.route('/api/signal-mode', methods=['GET'])
def get_current_signal_mode():
    """Hämtar nuvarande signal mode från settings fil"""
    settings_file = 'signal_mode_settings.json'

    # Default mode
    default_mode = 'conservative'

    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                current_mode = settings.get('mode', default_mode)
        except:
            current_mode = default_mode
    else:
        current_mode = default_mode

    # Validera att mode finns
    if not validate_mode(current_mode):
        current_mode = default_mode

    config = get_mode_config(current_mode)

    return jsonify({
        'mode': current_mode,
        'config': config
    })


@app.route('/api/signal-mode', methods=['POST'])
def set_signal_mode():
    """Sätter signal mode"""
    data = request.json
    mode = data.get('mode', 'conservative')

    # Validera mode
    if not validate_mode(mode):
        return jsonify({'error': 'Invalid mode. Must be "conservative" or "aggressive"'}), 400

    # Spara till settings fil
    settings_file = 'signal_mode_settings.json'
    settings = {'mode': mode}

    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f)

        config = get_mode_config(mode)

        return jsonify({
            'success': True,
            'mode': mode,
            'config': config,
            'message': f'Signal mode changed to {mode}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

    # Hämta last_checked från scheduler
    scheduler = get_scheduler()
    last_check = scheduler.get_last_check()

    return jsonify({
        'notifications': notifications,
        'count': len(notifications),
        'last_checked': last_check
    })


@app.route('/api/alerts/history', methods=['GET'])
def get_alerts_history():
    """Hämtar alert history"""
    limit = request.args.get('limit', 50, type=int)

    scheduler = get_scheduler()
    history = scheduler.get_alerts_history(limit)

    return jsonify({
        'alerts': history,
        'count': len(history)
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


# ============ PORTFOLIO ANALYTICS ENDPOINTS ============

@app.route('/api/portfolio/analytics', methods=['GET'])
def get_portfolio_analytics():
    """Hämtar portfolio analytics metrics"""
    try:
        analytics = portfolio_analytics.get_full_analytics()
        return jsonify(analytics)
    except Exception as e:
        print(f"Error getting portfolio analytics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/history', methods=['GET'])
def get_trade_history():
    """Hämtar trade history (alla entries och exits)"""
    try:
        history = portfolio_analytics.get_trade_history()
        return jsonify({'trades': history, 'count': len(history)})
    except Exception as e:
        print(f"Error getting trade history: {e}")
        return jsonify({'error': str(e)}), 500


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


# ============ MACRO DATA ENDPOINTS ============

@app.route('/api/macro', methods=['GET'])
def get_macro_data():
    """Hamtar alla makroekonomiska indikatorer"""
    try:
        macro_data = macro_fetcher.get_all_macro_data()

        return jsonify({
            'success': True,
            'data': macro_data,
            'timestamp': macro_data.get('timestamp', None)
        })
    except Exception as e:
        print(f"Error fetching macro data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch macro data'
        }), 500


@app.route('/api/correlations/<ticker>', methods=['GET'])
def get_stock_correlations(ticker):
    """Hamtar korrelationer for en specifik aktie"""
    market = request.args.get('market', 'SE')

    try:
        correlations = macro_fetcher.get_stock_correlations(ticker, market)

        if correlations is None:
            return jsonify({'error': f'Could not calculate correlations for {ticker}'}), 404

        return jsonify({
            'success': True,
            'ticker': ticker,
            'market': market,
            'correlations': correlations
        })
    except Exception as e:
        print(f"Error fetching correlations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch correlations'
        }), 500


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


# ============ BACKTESTER ENDPOINT ============

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run strategy backtest"""
    from backtester import Backtester

    data = request.json
    ticker = data.get('ticker')
    market = data.get('market', 'SE')
    start_date = data.get('start_date')  # YYYY-MM-DD or None
    end_date = data.get('end_date')  # YYYY-MM-DD or None
    initial_capital = data.get('initial_capital', 100000)
    mode = data.get('mode', 'conservative')

    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    try:
        # Validate mode
        if not validate_mode(mode):
            return jsonify({'error': f'Invalid mode: {mode}'}), 400

        # Run backtest
        backtester = Backtester(
            ticker=ticker,
            market=market,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            mode=mode
        )

        results = backtester.run()

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Backtest failed'
        }), 500


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


# ============ WEBSOCKET REAL-TIME STREAMING ============

# Track connected clients and their subscriptions
connected_clients = {}
price_cache = {}  # Cache for prices to avoid too many API calls

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    connected_clients[request.sid] = {'watchlist': [], 'active_ticker': None}
    emit('connection_status', {'status': 'connected', 'message': 'Welcome to MarketsAI Real-time'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    if request.sid in connected_clients:
        del connected_clients[request.sid]

@socketio.on('subscribe_watchlist')
def handle_subscribe_watchlist(data):
    """Subscribe to watchlist price updates"""
    tickers = data.get('tickers', [])
    market = data.get('market', 'SE')

    if request.sid in connected_clients:
        connected_clients[request.sid]['watchlist'] = tickers
        connected_clients[request.sid]['market'] = market
        print(f'Client {request.sid} subscribed to watchlist: {tickers}')
        emit('subscribed', {'tickers': tickers, 'market': market})

@socketio.on('unsubscribe_watchlist')
def handle_unsubscribe_watchlist():
    """Unsubscribe from watchlist updates"""
    if request.sid in connected_clients:
        connected_clients[request.sid]['watchlist'] = []
        print(f'Client {request.sid} unsubscribed from watchlist')

def stream_prices():
    """Background task to stream prices to connected clients"""
    while True:
        try:
            time.sleep(5)  # Update every 5 seconds

            # Collect all unique tickers to fetch
            tickers_to_fetch = {}
            for sid, client_data in connected_clients.items():
                watchlist = client_data.get('watchlist', [])
                market = client_data.get('market', 'SE')
                if watchlist:
                    if market not in tickers_to_fetch:
                        tickers_to_fetch[market] = set()
                    tickers_to_fetch[market].update(watchlist)

            # Fetch quotes (price + change) for each market
            for market, tickers in tickers_to_fetch.items():
                if tickers:
                    try:
                        quotes = fetcher.get_multiple_quotes(list(tickers), market)

                        # Cache the quotes
                        for ticker, quote in quotes.items():
                            price_cache[f'{ticker}:{market}'] = quote

                        # Send updates to subscribed clients
                        for sid, client_data in connected_clients.items():
                            if client_data.get('market') == market:
                                client_watchlist = client_data.get('watchlist', [])
                                client_quotes = {t: quotes.get(t) for t in client_watchlist if t in quotes}

                                if client_quotes:
                                    socketio.emit('price_update', {
                                        'quotes': client_quotes,
                                        'market': market,
                                        'timestamp': time.time()
                                    }, room=sid)
                    except Exception as e:
                        print(f'Error fetching quotes for {market}: {e}')

        except Exception as e:
            print(f'Error in price streaming: {e}')
            time.sleep(5)

# Start background price streaming thread
price_stream_thread = threading.Thread(target=stream_prices, daemon=True)
price_stream_thread.start()


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
    print("  GET  /api/stock/search?q=VOLVO&limit=10")
    print("  GET  /api/stock/historical?ticker=VOLVO-B&period=3mo")
    print("  GET  /api/stock/omx30")
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
    print("  GET  /api/macro")
    print("  GET  /api/correlations/<ticker>?market=SE")
    print("  GET  /api/strategy")
    print("  POST /api/backtest")
    print("  POST /api/notifications/register")
    print("  POST /api/notifications/unregister")
    print("  POST /api/notifications/send")
    print("  POST /api/notifications/signal")
    print("  GET  /api/notifications/tokens")
    print("\n" + "="*60)
    print("Running on http://127.0.0.1:5000")
    print("="*60 + "\n")

    # Start alert scheduler (only in werkzeug child process, not reloader parent)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = get_scheduler()
        scheduler.start()

    # Run with SocketIO support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
