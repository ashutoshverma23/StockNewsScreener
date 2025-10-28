from flask import Flask, render_template, session, redirect, jsonify, request
from flask_socketio import SocketIO, emit
from auth import auth_bp
import os
import threading
from datetime import datetime
from dotenv import load_dotenv

# Import your existing bot components
from socket_worker import run_socket_simulator, fyers_on_message
from bot_core import broker, active_positions

# Import news screener components
from bot_core.news_screener import FyersNewsScreener
from bot_core.enhanced_screener import NewsAnalyzer, AdvancedFilters, get_trading_recommendation

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this")

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Global screener instance
news_screener = None
screener_lock = threading.Lock()

# Routes
@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    # Check if user is authenticated
    if "access_token" not in session:
        return redirect("/login")
    
    return render_template("index.html")

@app.route("/screener")
def screener_dashboard():
    """News screener dashboard page"""
    if "access_token" not in session:
        return redirect("/login")
    
    return render_template("screener.html")

# Helper function to serialize datetime objects
def serialize_positions(positions):
    """Convert positions dict to JSON-serializable format"""
    serialized = {}
    for symbol, pos in positions.items():
        serialized[symbol] = {
            "entry": pos["entry"],
            "side": pos["side"],
            "qty": pos["qty"],
            "entry_time": pos["entry_time"].isoformat() if isinstance(pos.get("entry_time"), datetime) else str(pos.get("entry_time", ""))
        }
    return serialized

# SocketIO event handlers for trading bot
@socketio.on('connect')
def handle_connect():
    print('Client connected to dashboard')
    # Send initial status
    socketio.emit('tick', {
        'symbol': 'SYSTEM',
        'ltp': 0,
        'signal': 'CONNECTED',
        'broker_stats': broker.stats(),
        'active_positions': serialize_positions(active_positions)
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from dashboard')

# Callback function to emit data from bot_core to dashboard
def emit_to_dashboard(data):
    """
    This function is called by bot_core.on_tick() to push data to dashboard
    Handles datetime serialization before sending
    """
    # Serialize active_positions to make it JSON-compatible
    if 'active_positions' in data:
        data['active_positions'] = serialize_positions(data['active_positions'])
    
    socketio.emit('tick', data)

# News Screener API Routes
@app.route('/api/screener/initialize', methods=['POST'])
def initialize_screener():
    """Initialize news screener with current access token"""
    global news_screener
    
    if "access_token" not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        access_token = session.get('access_token')
        with screener_lock:
            news_screener = FyersNewsScreener(access_token)
        
        return jsonify({
            'message': 'News screener initialized successfully',
            'status': 'ready'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screener/scan', methods=['POST'])
def start_screener_scan():
    """Start scanning stocks for news-based opportunities"""
    global news_screener
    
    if news_screener is None:
        # Try to initialize with session token
        if "access_token" not in session:
            return jsonify({'error': 'Screener not initialized. Please login first.'}), 401
        
        try:
            access_token = session.get('access_token')
            with screener_lock:
                news_screener = FyersNewsScreener(access_token)
        except Exception as e:
            return jsonify({'error': f'Failed to initialize screener: {str(e)}'}), 500
    
    if news_screener.is_scanning:
        return jsonify({'message': 'Scan already in progress'}), 400
    
    # Run scan in background thread
    def run_scan():
        try:
            results = news_screener.scan_stocks()
            # Emit results via SocketIO for real-time updates
            socketio.emit('screener_results', {
                'stocks': results,
                'count': len(results),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error during scan: {e}")
            socketio.emit('screener_error', {'error': str(e)})
    
    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()
    
    return jsonify({'message': 'Scan started', 'status': 'scanning'})

@app.route('/api/screener/results', methods=['GET'])
def get_screener_results():
    """Get current scan results"""
    global news_screener
    
    if news_screener is None:
        return jsonify({
            'error': 'Screener not initialized',
            'is_scanning': False,
            'stocks': [],
            'count': 0
        }), 200
    
    return jsonify({
        'is_scanning': news_screener.is_scanning,
        'stocks': news_screener.screened_stocks,
        'count': len(news_screener.screened_stocks),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/screener/status', methods=['GET'])
def get_screener_status():
    """Get scanner status"""
    global news_screener
    
    return jsonify({
        'initialized': news_screener is not None,
        'is_scanning': news_screener.is_scanning if news_screener else False,
        'authenticated': 'access_token' in session
    })

@app.route('/api/screener/analyze/<symbol>', methods=['GET'])
def analyze_stock_detail(symbol):
    """Get detailed analysis for a specific stock"""
    global news_screener
    
    if news_screener is None:
        return jsonify({'error': 'Screener not initialized'}), 401
    
    try:
        # Format symbol for Fyers
        fyers_symbol = f"NSE:{symbol}-EQ" if not symbol.startswith('NSE:') else symbol
        
        # Get historical data
        df = news_screener.get_historical_data(fyers_symbol, days=30)
        if df is None:
            return jsonify({'error': 'Failed to fetch stock data'}), 404
        
        # Get current quote
        current_quote = news_screener.get_current_quote(fyers_symbol)
        if current_quote is None:
            return jsonify({'error': 'Failed to fetch current quote'}), 404
        
        # Analyze volume and price
        analysis = news_screener.analyze_volume_and_price(df, current_quote)
        
        # Fetch news
        news = news_screener.fetch_news_for_stock(fyers_symbol)
        
        # Enhanced analysis
        news_summary = NewsAnalyzer.get_news_summary(news)
        strength_score = AdvancedFilters.calculate_strength_score(analysis, news_summary, df)
        has_correlation = AdvancedFilters.check_price_volume_correlation(df, current_quote)
        is_breakout = AdvancedFilters.check_breakout(df, current_quote)
        
        # Determine signal
        signal = news_screener.determine_signal(analysis, len(news))
        
        # Get trading recommendation
        recommendation = None
        if signal:
            recommendation = get_trading_recommendation(signal, strength_score, news_summary)
        
        return jsonify({
            'symbol': fyers_symbol,
            'current_quote': current_quote,
            'analysis': analysis,
            'news': news[:5],
            'news_summary': news_summary,
            'signal': signal,
            'strength_score': strength_score,
            'recommendation': recommendation,
            'has_price_volume_correlation': has_correlation,
            'is_breakout': is_breakout,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screener/settings', methods=['GET', 'POST'])
def screener_settings():
    """Get or update screener settings"""
    if request.method == 'GET':
        return jsonify({
            'volume_threshold': float(os.getenv('VOLUME_SURGE_THRESHOLD', 2.0)),
            'price_change_min': float(os.getenv('PRICE_CHANGE_MIN', 3.0)),
            'price_change_max': float(os.getenv('PRICE_CHANGE_MAX', 15.0)),
            'lookback_days': int(os.getenv('LOOKBACK_DAYS', 5)),
            'min_price': float(os.getenv('MIN_PRICE', 20)),
            'max_price': float(os.getenv('MAX_PRICE', 5000))
        })
    
    # POST: Update settings (stored in session or database)
    data = request.get_json()
    session['screener_settings'] = data
    return jsonify({'message': 'Settings updated', 'settings': data})

# SocketIO events for screener
@socketio.on('screener_connect')
def handle_screener_connect():
    """Handle connection to screener dashboard"""
    print('Client connected to screener')
    emit('screener_status', {
        'initialized': news_screener is not None,
        'is_scanning': news_screener.is_scanning if news_screener else False
    })

@socketio.on('request_screener_update')
def handle_screener_update_request():
    """Client requesting latest screener results"""
    if news_screener:
        emit('screener_results', {
            'stocks': news_screener.screened_stocks,
            'count': len(news_screener.screened_stocks),
            'timestamp': datetime.now().isoformat()
        })

# Start the trading bot in a background thread
def start_bot():
    print("Starting trading bot simulator...")
    
    # Check if we should enable screener integration
    enable_screener = os.getenv('ENABLE_PERIODIC_SCREENER', 'false').lower() == 'true'
    
    # Use simulator for testing (replace with real FYERS websocket when ready)
    run_socket_simulator(emit_fn=emit_to_dashboard, enable_screener=enable_screener)
    
    # For real FYERS connection, use:
    # from socket_worker import run_real_fyers_websocket
    # access_token = session.get('access_token')
    # run_real_fyers_websocket(access_token, emit_fn=emit_to_dashboard, enable_screener=enable_screener)

# Start bot thread when app starts
bot_thread = None

@app.before_request
def start_bot_once():
    global bot_thread
    if bot_thread is None:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()

# Initialize screener on first authenticated request
@app.before_request
def initialize_screener_once():
    global news_screener
    if news_screener is None and "access_token" in session:
        try:
            access_token = session.get('access_token')
            with screener_lock:
                if news_screener is None:  # Double-check
                    news_screener = FyersNewsScreener(access_token)
                    print("News screener initialized with session token")
        except Exception as e:
            print(f"Failed to auto-initialize screener: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Intraday Trading Bot Dashboard")
    print("=" * 60)
    print("Main Dashboard: http://127.0.0.1:5000/dashboard")
    print("News Screener: http://127.0.0.1:5000/screener")
    print("First-time users: http://127.0.0.1:5000/login")
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)