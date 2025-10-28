import os
import logging
from datetime import datetime, timedelta
from fyers_apiv3 import fyersModel
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
import requests
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Fyers Configuration
CLIENT_ID = os.getenv('FYERS_CLIENT_ID', 'YOUR_CLIENT_ID')
SECRET_KEY = os.getenv('FYERS_SECRET_KEY', 'YOUR_SECRET_KEY')
REDIRECT_URI = os.getenv('FYERS_REDIRECT_URI', 'http://localhost:5000/callback')
ACCESS_TOKEN = os.getenv('FYERS_ACCESS_TOKEN', '')

# News API Configuration (Using NewsAPI.org or similar)
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '5a44d7d1eb2d4f47b505e67befe6e551')

# Screening Parameters (loaded from environment with sensible defaults)
# Reduced thresholds to find more opportunities
VOLUME_SURGE_THRESHOLD = float(os.getenv('VOLUME_SURGE_THRESHOLD', '1.5'))  # 1.5x average volume (was 2.0)
PRICE_CHANGE_MIN = float(os.getenv('PRICE_CHANGE_MIN', '1.0'))  # Minimum 1% price change (was 3.0)
PRICE_CHANGE_MAX = float(os.getenv('PRICE_CHANGE_MAX', '20.0'))  # Maximum 20% price change (was 15.0)
LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', '5'))  # Days to check for news
MIN_PRICE = float(os.getenv('MIN_PRICE', '10'))  # Minimum stock price (was 20)
MAX_PRICE = float(os.getenv('MAX_PRICE', '10000'))  # Maximum stock price (was 5000)

class FyersNewsScreener:
    def __init__(self, access_token):
        self.fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=access_token)
        self.screened_stocks = []
        self.is_scanning = False
        
    def get_nse_symbols(self):
        """Get list of NSE symbols to scan"""
        # Top liquid NSE stocks
        symbols = [
            "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:INFY-EQ",
            "NSE:ICICIBANK-EQ", "NSE:HINDUNILVR-EQ", "NSE:SBIN-EQ", "NSE:BHARTIARTL-EQ",
            "NSE:ITC-EQ", "NSE:KOTAKBANK-EQ", "NSE:LT-EQ", "NSE:AXISBANK-EQ",
            "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ", "NSE:BAJFINANCE-EQ", "NSE:HCLTECH-EQ",
            "NSE:WIPRO-EQ", "NSE:ULTRACEMCO-EQ", "NSE:TITAN-EQ", "NSE:NESTLEIND-EQ",
            "NSE:SUNPHARMA-EQ", "NSE:TATAMOTORS-EQ", "NSE:ONGC-EQ", "NSE:NTPC-EQ",
            "NSE:POWERGRID-EQ", "NSE:M&M-EQ", "NSE:BAJAJFINSV-EQ", "NSE:TECHM-EQ",
            "NSE:ADANIPORTS-EQ", "NSE:COALINDIA-EQ", "NSE:DIVISLAB-EQ", "NSE:DRREDDY-EQ",
            "NSE:CIPLA-EQ", "NSE:EICHERMOT-EQ", "NSE:GRASIM-EQ", "NSE:HINDALCO-EQ",
            "NSE:INDUSINDBK-EQ", "NSE:JSWSTEEL-EQ", "NSE:TATASTEEL-EQ", "NSE:TATACONSUM-EQ",
            "NSE:HEROMOTOCO-EQ", "NSE:BRITANNIA-EQ", "NSE:UPL-EQ", "NSE:APOLLOHOSP-EQ",
            "NSE:ADANIENT-EQ", "NSE:ADANIGREEN-EQ", "NSE:ADANITRANS-EQ", "NSE:BAJAJ-AUTO-EQ",
            "NSE:BEL-EQ", "NSE:BPCL-EQ", "NSE:VEDL-EQ", "NSE:IOC-EQ"
        ]
        return symbols
    
    def get_historical_data(self, symbol, days=30):
        """Fetch historical data from Fyers"""
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            data = {
                "symbol": symbol,
                "resolution": "D",  # Daily data
                "date_format": "1",
                "range_from": from_date.strftime("%Y-%m-%d"),
                "range_to": to_date.strftime("%Y-%m-%d"),
                "cont_flag": "1"
            }
            
            response = self.fyers.history(data=data)
            
            if response.get('s') == 'ok':
                candles = response.get('candles', [])
                if candles:
                    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    return df
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.warning(f"API error for {symbol}: {error_msg}")
            return None
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_current_quote(self, symbol):
        """Get current quote for a symbol"""
        try:
            data = {"symbols": symbol}
            response = self.fyers.quotes(data=data)
            
            if response.get('s') == 'ok':
                quote = response.get('d', [{}])[0]
                return {
                    'ltp': quote.get('v', {}).get('lp', 0),
                    'volume': quote.get('v', {}).get('volume', 0),
                    'change_percent': quote.get('v', {}).get('ch', 0),
                    'prev_close': quote.get('v', {}).get('prev_close_price', 0)
                }
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.warning(f"Quote API error for {symbol}: {error_msg}")
            return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def fetch_news_for_stock(self, stock_name):
        """Fetch recent news for a stock"""
        try:
            # Remove exchange prefix and -EQ suffix
            clean_name = stock_name.replace('NSE:', '').replace('-EQ', '')
            
            # Using NewsAPI.org (you can replace with any news API)
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': f'{clean_name} stock OR {clean_name} shares',
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime('%Y-%m-%d'),
                'apiKey': NEWS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                return articles[:5]  # Return top 5 news
            return []
        except Exception as e:
            logger.error(f"Error fetching news for {stock_name}: {e}")
            return []
    
    def analyze_volume_and_price(self, df, current_quote):
        """Analyze volume surge and price movement"""
        if df is None or len(df) < 10:
            return None
        
        # Calculate average volume (excluding today)
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = current_quote['volume']
        
        # Volume surge ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Price change percentage
        price_change = current_quote['change_percent']
        
        # Calculate volatility (ATR-like)
        df['range'] = df['high'] - df['low']
        avg_range = df['range'].mean()
        current_range = abs(current_quote['ltp'] - current_quote['prev_close'])
        range_ratio = current_range / avg_range if avg_range > 0 else 0
        
        return {
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'range_ratio': range_ratio,
            'avg_volume': avg_volume,
            'current_volume': current_volume
        }
    
    def determine_signal(self, analysis, news_count):
        """Determine bullish or bearish signal"""
        if analysis is None:
            return None
        
        volume_surge = analysis['volume_ratio'] >= VOLUME_SURGE_THRESHOLD
        price_change = abs(analysis['price_change'])
        significant_move = PRICE_CHANGE_MIN <= price_change <= PRICE_CHANGE_MAX
        has_news = news_count > 0
        
        # Made news optional - focus on volume and price movement
        if volume_surge and significant_move:
            signal_strength = 'STRONG' if analysis['volume_ratio'] > 3 else 'MODERATE'
            if has_news:
                signal_strength = 'VERY STRONG'
            
            if analysis['price_change'] > 0:
                return {
                    'signal': 'BULLISH',
                    'action': 'BUY (Delivery)',
                    'strength': signal_strength
                }
            else:
                return {
                    'signal': 'BEARISH',
                    'action': 'SELL (Intraday)',
                    'strength': signal_strength
                }
        return None
    
    def scan_stocks(self):
        """Main scanning function"""
        self.is_scanning = True
        self.screened_stocks = []
        symbols = self.get_nse_symbols()
        
        logger.info(f"Starting scan of {len(symbols)} stocks...")
        logger.info(f"Screening parameters - Volume Threshold: {VOLUME_SURGE_THRESHOLD}x, Price Change: {PRICE_CHANGE_MIN}%-{PRICE_CHANGE_MAX}%, Price Range: ₹{MIN_PRICE}-₹{MAX_PRICE}")
        
        processed = 0
        skipped_no_data = 0
        skipped_no_quote = 0
        skipped_price_range = 0
        skipped_no_analysis = 0
        found_signals = 0
        
        for symbol in symbols:
            try:
                processed += 1
                # Get historical data
                df = self.get_historical_data(symbol, days=30)
                if df is None:
                    skipped_no_data += 1
                    if processed % 10 == 0:
                        logger.info(f"Processed {processed}/{len(symbols)} symbols...")
                    continue
                
                # Get current quote
                current_quote = self.get_current_quote(symbol)
                if current_quote is None:
                    skipped_no_quote += 1
                    continue
                
                # Check if price is in range
                if current_quote['ltp'] < MIN_PRICE or current_quote['ltp'] > MAX_PRICE:
                    skipped_price_range += 1
                    continue
                
                # Analyze volume and price
                analysis = self.analyze_volume_and_price(df, current_quote)
                if analysis is None:
                    skipped_no_analysis += 1
                    continue
                
                # Fetch news
                news = self.fetch_news_for_stock(symbol)
                
                # Determine signal
                signal = self.determine_signal(analysis, len(news))
                
                if signal:
                    stock_data = {
                        'symbol': symbol,
                        'name': symbol.replace('NSE:', '').replace('-EQ', ''),
                        'ltp': current_quote['ltp'],
                        'price_change': analysis['price_change'],
                        'volume_ratio': analysis['volume_ratio'],
                        'signal': signal['signal'],
                        'action': signal['action'],
                        'strength': signal['strength'],
                        'news_count': len(news),
                        'news': news[:3],  # Top 3 news items
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.screened_stocks.append(stock_data)
                    found_signals += 1
                    logger.info(f"✓ Found opportunity: {symbol} - {signal['signal']} ({signal['strength']})")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by volume ratio (most active first)
        self.screened_stocks.sort(key=lambda x: x['volume_ratio'], reverse=True)
        
        self.is_scanning = False
        logger.info("=" * 60)
        logger.info(f"Scan complete!")
        logger.info(f"Processed: {processed}, Signals found: {found_signals}")
        logger.info(f"Skipped - No data: {skipped_no_data}, No quote: {skipped_no_quote}, Price range: {skipped_price_range}, No analysis: {skipped_no_analysis}")
        logger.info("=" * 60)
        
        return self.screened_stocks

# Global screener instance
screener = None

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start scanning stocks"""
    global screener
    
    if screener is None:
        return jsonify({'error': 'Fyers not authenticated'}), 401
    
    if screener.is_scanning:
        return jsonify({'message': 'Scan already in progress'}), 400
    
    # Run scan in background thread
    thread = Thread(target=screener.scan_stocks)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scan started'})

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get scan results"""
    global screener
    
    if screener is None:
        return jsonify({'error': 'Fyers not authenticated'}), 401
    
    return jsonify({
        'is_scanning': screener.is_scanning,
        'stocks': screener.screened_stocks,
        'count': len(screener.screened_stocks)
    })

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Fyers"""
    global screener
    
    data = request.get_json()
    access_token = data.get('access_token', ACCESS_TOKEN)
    
    if not access_token:
        return jsonify({'error': 'Access token required'}), 400
    
    try:
        screener = FyersNewsScreener(access_token)
        return jsonify({'message': 'Authentication successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get scanner status"""
    global screener
    
    return jsonify({
        'authenticated': screener is not None,
        'is_scanning': screener.is_scanning if screener else False
    })

if __name__ == '__main__':
    # Check if access token is provided
    if ACCESS_TOKEN:
        screener = FyersNewsScreener(ACCESS_TOKEN)
        logger.info("Fyers screener initialized with access token")
    else:
        logger.warning("No access token provided. Use /api/authenticate endpoint.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)