# socket_worker.py
import json
import threading
import time
import requests

# List of stocks to monitor
STOCKS = [
    "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:INFY-EQ",
    "NSE:ICICIBANK-EQ", "NSE:SBIN-EQ", "NSE:BHARTIARTL-EQ",
    "NSE:ITC-EQ", "NSE:HINDUNILVR-EQ", "NSE:KOTAKBANK-EQ", "NSE:LT-EQ", 
    "NSE:AXISBANK-EQ", "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ", "NSE:BAJFINANCE-EQ",
    "NSE:HCLTECH-EQ", "NSE:WIPRO-EQ", "NSE:ULTRACEMCO-EQ", "NSE:TITAN-EQ",
    "NSE:NESTLEIND-EQ", "NSE:SUNPHARMA-EQ", "NSE:TATAMOTORS-EQ", "NSE:ONGC-EQ"
]

# Cache for actual stock prices
PRICE_CACHE = {}
CACHE_LOCK = threading.Lock()

# Global reference to news screener (will be set by app.py)
NEWS_SCREENER = None
SCREENER_RESULTS = []
SCREENER_LOCK = threading.Lock()

# Realistic fallback prices for common Indian stocks (approximate ranges)
FALLBACK_PRICES = {
    "NSE:RELIANCE-EQ": 2450.0,
    "NSE:TCS-EQ": 3850.0,
    "NSE:HDFCBANK-EQ": 1720.0,
    "NSE:INFY-EQ": 1580.0,
    "NSE:ICICIBANK-EQ": 1250.0,
    "NSE:SBIN-EQ": 785.0,
    "NSE:BHARTIARTL-EQ": 1650.0,
    "NSE:ITC-EQ": 465.0,
    "NSE:HINDUNILVR-EQ": 2380.0,
    "NSE:LT-EQ": 3580.0,
    "NSE:AXISBANK-EQ": 1140.0,
    "NSE:KOTAKBANK-EQ": 1780.0,
    "NSE:TATAMOTORS-EQ": 785.0,
    "NSE:ASIANPAINT-EQ": 2420.0,
    "NSE:MARUTI-EQ": 12800.0,
    # Additional stocks for screener
    "NSE:WIPRO-EQ": 445.0,
    "NSE:ULTRACEMCO-EQ": 10200.0,
    "NSE:TITAN-EQ": 3450.0,
    "NSE:NESTLEIND-EQ": 2380.0,
    "NSE:SUNPHARMA-EQ": 1680.0,
    "NSE:ONGC-EQ": 245.0,
    "NSE:NTPC-EQ": 325.0,
    "NSE:POWERGRID-EQ": 285.0,
    "NSE:M&M-EQ": 2780.0,
    "NSE:BAJAJFINSV-EQ": 1650.0,
    "NSE:TECHM-EQ": 1680.0,
    "NSE:ADANIPORTS-EQ": 1280.0,
    "NSE:COALINDIA-EQ": 425.0,
    "NSE:DIVISLAB-EQ": 5950.0,
    "NSE:DRREDDY-EQ": 6250.0,
    "NSE:CIPLA-EQ": 1480.0,
    "NSE:EICHERMOT-EQ": 4850.0,
    "NSE:GRASIM-EQ": 2580.0,
    "NSE:HINDALCO-EQ": 645.0,
    "NSE:INDUSINDBK-EQ": 980.0,
    "NSE:JSWSTEEL-EQ": 920.0,
    "NSE:TATASTEEL-EQ": 165.0,
    "NSE:TATACONSUM-EQ": 1080.0,
    "NSE:HEROMOTOCO-EQ": 4650.0,
    "NSE:BRITANNIA-EQ": 5250.0,
    "NSE:UPL-EQ": 545.0,
    "NSE:APOLLOHOSP-EQ": 6850.0,
    "NSE:ADANIENT-EQ": 2450.0,
    "NSE:BAJAJ-AUTO-EQ": 9500.0,
    "NSE:BEL-EQ": 285.0,
    "NSE:BPCL-EQ": 285.0,
    "NSE:VEDL-EQ": 445.0,
    "NSE:IOC-EQ": 135.0,
}

def set_news_screener(screener_instance):
    """
    Set the news screener instance to be used by socket worker.
    Called by app.py after screener initialization.
    """
    global NEWS_SCREENER
    NEWS_SCREENER = screener_instance
    print("✓ News screener connected to socket worker")

def fetch_actual_prices():
    """
    Fetch actual prices for stocks using multiple methods.
    Tries NSE India API first, then Yahoo Finance as fallback.
    """
    global PRICE_CACHE
    
    for symbol in STOCKS:
        price_found = False
        
        try:
            # Method 1: Try NSE India API
            clean_symbol = symbol.replace("NSE:", "").replace("-EQ", "")
            
            # NSE India quote API
            nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={clean_symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(nse_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price_info = data.get("priceInfo", {})
                current_price = price_info.get("lastPrice")
                
                if current_price:
                    with CACHE_LOCK:
                        PRICE_CACHE[symbol] = float(current_price)
                    print(f"✓ [NSE] {clean_symbol}: ₹{current_price:.2f}")
                    price_found = True
                    continue
        except Exception as e:
            print(f"  [NSE] {clean_symbol}: {str(e)[:50]}")
        
        # Method 2: Try Yahoo Finance
        if not price_found:
            try:
                clean_symbol = symbol.replace("NSE:", "").replace("-EQ", "")
                yahoo_symbol = f"{clean_symbol}.NS"
                
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
                params = {"interval": "1d", "range": "1d"}
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("chart", {}).get("result", [{}])[0]
                    meta = result.get("meta", {})
                    current_price = meta.get("regularMarketPrice")
                    
                    if current_price:
                        with CACHE_LOCK:
                            PRICE_CACHE[symbol] = float(current_price)
                        print(f"✓ [Yahoo] {clean_symbol}: ₹{current_price:.2f}")
                        price_found = True
                        continue
            except Exception as e:
                print(f"  [Yahoo] {clean_symbol}: {str(e)[:50]}")
        
        # Method 3: Use fallback prices
        if not price_found:
            fallback = FALLBACK_PRICES.get(symbol, 1000.0)
            with CACHE_LOCK:
                PRICE_CACHE[symbol] = fallback
            print(f"⚠ [Fallback] {symbol.replace('NSE:', '').replace('-EQ', '')}: ₹{fallback:.2f}")

def get_base_price(symbol):
    """Get the base price for a symbol, with intelligent fallback."""
    with CACHE_LOCK:
        if symbol not in PRICE_CACHE:
            # Use fallback price if available
            return FALLBACK_PRICES.get(symbol, 1000.0)
        return PRICE_CACHE[symbol]

def check_screener_signals(symbol, current_ltp, emit_fn=None):
    """
    Check if the current symbol has any screener signals.
    Emits alerts if significant news-based opportunities are detected.
    """
    global SCREENER_RESULTS
    
    with SCREENER_LOCK:
        for stock in SCREENER_RESULTS:
            if stock.get('symbol') == symbol:
                # Found a screener signal for this stock
                if emit_fn:
                    emit_fn({
                        'type': 'screener_alert',
                        'symbol': symbol,
                        'signal': stock.get('signal'),
                        'action': stock.get('action'),
                        'strength': stock.get('strength'),
                        'price_change': stock.get('price_change'),
                        'volume_ratio': stock.get('volume_ratio'),
                        'news_count': stock.get('news_count'),
                        'current_price': current_ltp,
                        'timestamp': time.time()
                    })
                return stock
    return None

def update_screener_results(results):
    """
    Update the global screener results.
    Called by app.py when new scan results are available.
    """
    global SCREENER_RESULTS
    with SCREENER_LOCK:
        SCREENER_RESULTS = results
    print(f"✓ Updated screener results: {len(results)} opportunities")

def on_tick(symbol, tick_data, emit_fn=None):
    """
    Process tick data and emit to dashboard.
    This is called for each market tick for each stock.
    """
    try:
        # Send tick data to dashboard
        if emit_fn:
            data = {
                'symbol': symbol,
                'ltp': tick_data.get('ltp', 0),
                'vol_traded_today': tick_data.get('vol_traded_today', 0),
                'bidQ': tick_data.get('bidQ', 0),
                'askQ': tick_data.get('askQ', 0),
                'timestamp': tick_data.get('timestamp', time.time()),
                'screener_signal': tick_data.get('screener_signal')
            }
            emit_fn(data)
    except Exception as e:
        print(f"Error in on_tick for {symbol}: {e}")

def refresh_prices_periodically():
    """Background thread to refresh prices every 5 minutes."""
    while True:
        time.sleep(300)  # Wait 5 minutes
        print("\n📊 Refreshing stock prices...")
        fetch_actual_prices()

def run_periodic_screener_scan(emit_fn=None):
    """
    Background thread to run screener scans periodically during market hours.
    Runs every 15 minutes between 9:15 AM and 3:30 PM IST.
    """
    from datetime import datetime
    import pytz
    
    if NEWS_SCREENER is None:
        print("⚠️  News screener not initialized, skipping periodic scans")
        return
    
    ist = pytz.timezone('Asia/Kolkata')
    
    while True:
        try:
            now = datetime.now(ist)
            current_time = now.time()
            
            # Market hours: 9:15 AM to 3:30 PM IST
            market_open = now.replace(hour=9, minute=15, second=0).time()
            market_close = now.replace(hour=15, minute=30, second=0).time()
            
            # Check if market is open and it's a weekday
            is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
            is_market_hours = market_open <= current_time <= market_close
            
            if is_weekday and is_market_hours:
                print(f"\n🔍 Running periodic screener scan at {now.strftime('%H:%M:%S')}...")
                
                if not NEWS_SCREENER.is_scanning:
                    # Run scan
                    results = NEWS_SCREENER.scan_stocks()
                    update_screener_results(results)
                    
                    # Emit results if callback provided
                    if emit_fn:
                        emit_fn({
                            'type': 'screener_complete',
                            'stocks': results,
                            'count': len(results),
                            'timestamp': time.time()
                        })
                    
                    print(f"✓ Scan complete: Found {len(results)} opportunities")
                else:
                    print("⏳ Scan already in progress, skipping...")
                
                # Wait 15 minutes before next scan
                time.sleep(900)
            else:
                # Outside market hours, check every hour
                if is_weekday:
                    print(f"📴 Market closed. Next check in 1 hour (Current: {now.strftime('%H:%M')})")
                else:
                    print(f"📴 Weekend. Next check in 1 hour")
                time.sleep(3600)
                
        except Exception as e:
            print(f"❌ Error in periodic screener: {e}")
            time.sleep(900)  # Wait 15 minutes before retry

# Example generic wrapper for a websocket library's on_message
def fyers_on_message(msg, emit_fn=None):
    """
    msg is the raw payload from the FYERS websocket. FYERS typically returns JSON with 'd' list.
    Each tick in d has structure similar to your snippet: {"symbol": "...", "v": {...}}
    """
    try:
        payload = json.loads(msg)
    except Exception:
        return
    
    for tick in payload.get("d", []):
        symbol = tick.get("symbol")
        v = tick.get("v", {})
        
        # Check for screener signals on this symbol
        current_ltp = v.get("ltp", 0)
        screener_signal = check_screener_signals(symbol, current_ltp, emit_fn)
        
        # Add screener signal to tick data if exists
        if screener_signal:
            v['screener_signal'] = screener_signal
        
        # Process tick with trading bot
        on_tick(symbol, v, emit_fn=emit_fn)

def run_socket_simulator(emit_fn=None, enable_screener=False):
    """
    Simulate ticks using actual stock prices with realistic variations.
    Fetches real prices on first run and refreshes periodically.
    
    Args:
        emit_fn: Callback function to emit data to dashboard
        enable_screener: If True, starts periodic screener scans
    """
    import random
    
    # Fetch actual prices on startup
    print("🚀 Initializing with actual stock prices...")
    print("=" * 60)
    fetch_actual_prices()
    print("=" * 60)
    
    # Start background price refresh thread
    refresh_thread = threading.Thread(target=refresh_prices_periodically, daemon=True)
    refresh_thread.start()
    
    # Start periodic screener if enabled
    if enable_screener and NEWS_SCREENER is not None:
        print("🔍 Starting periodic news screener...")
        screener_thread = threading.Thread(
            target=run_periodic_screener_scan, 
            args=(emit_fn,), 
            daemon=True
        )
        screener_thread.start()
        print("✓ Periodic screener enabled (runs every 15 min during market hours)")
    
    print("✅ Simulator started with real prices\n")
    
    while True:
        for s in STOCKS:
            base_price = get_base_price(s)
            
            # Simulate realistic price movement (±0.5% from base)
            price_variation = random.uniform(-0.005, 0.005)
            current_ltp = round(base_price * (1 + price_variation), 2)
            
            fake = {
                "ltp": current_ltp,
                "vol_traded_today": int(random.random() * 10000),
                "bidQ": int(random.random() * 500),
                "askQ": int(random.random() * 500),
                "timestamp": time.time()
            }
            
            # Check for screener signals
            screener_signal = check_screener_signals(s, current_ltp, emit_fn)
            if screener_signal:
                fake['screener_signal'] = {
                    'signal': screener_signal.get('signal'),
                    'action': screener_signal.get('action'),
                    'strength': screener_signal.get('strength')
                }
            
            on_tick(s, fake, emit_fn=emit_fn)
        
        time.sleep(1)

def run_real_fyers_websocket(access_token, emit_fn=None, enable_screener=False):
    """
    Connect to real Fyers WebSocket for live market data.
    
    Args:
        access_token: Fyers access token
        emit_fn: Callback function to emit data to dashboard
        enable_screener: If True, starts periodic screener scans
    """
    from fyers_apiv3 import fyersModel
    from fyers_apiv3.FyersWebsocket import data_ws
    
    print("🔌 Connecting to Fyers WebSocket...")
    
    # Initialize Fyers WebSocket
    fyers = fyersModel.FyersModel(client_id="YOUR_CLIENT_ID", token=access_token)
    
    def onmessage(message):
        """Handle incoming WebSocket messages"""
        fyers_on_message(message, emit_fn=emit_fn)
    
    def onerror(message):
        """Handle WebSocket errors"""
        print(f"❌ WebSocket Error: {message}")
    
    def onclose(message):
        """Handle WebSocket close"""
        print(f"🔌 WebSocket Closed: {message}")
    
    def onopen():
        """Handle WebSocket open"""
        print("✓ WebSocket Connected")
        # Subscribe to stocks
        data_type = "SymbolUpdate"
        
        # Subscribe in batches to avoid overwhelming
        for i in range(0, len(STOCKS), 50):
            batch = STOCKS[i:i+50]
            fyers.subscribe(symbols=batch, data_type=data_type)
            print(f"✓ Subscribed to {len(batch)} stocks")
    
    # Create WebSocket instance
    data_ws_instance = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=onopen,
        on_close=onclose,
        on_error=onerror,
        on_message=onmessage
    )
    
    # Start periodic screener if enabled
    if enable_screener and NEWS_SCREENER is not None:
        print("🔍 Starting periodic news screener...")
        screener_thread = threading.Thread(
            target=run_periodic_screener_scan, 
            args=(emit_fn,), 
            daemon=True
        )
        screener_thread.start()
        print("✓ Periodic screener enabled")
    
    # Connect to WebSocket
    data_ws_instance.connect()

# Helper function to get screener statistics
def get_screener_stats():
    """Get current screener statistics"""
    with SCREENER_LOCK:
        total = len(SCREENER_RESULTS)
        bullish = sum(1 for s in SCREENER_RESULTS if s.get('signal') == 'BULLISH')
        bearish = sum(1 for s in SCREENER_RESULTS if s.get('signal') == 'BEARISH')
        
        return {
            'total_signals': total,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'last_update': time.time() if SCREENER_RESULTS else None
        }