# 📈 Trading News Screener

A comprehensive Flask-based algorithmic trading system that combines real-time market data analysis with news-driven stock screening for automated intraday trading and delivery investment opportunities.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Fyers API](https://img.shields.io/badge/Fyers-API%20v3-orange.svg)](https://fyers.in/api-documentation)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 🤖 Automated Trading Bot
- **Real-time Market Data**: Live price streaming via Fyers WebSocket/Simulator
- **Smart Strategy Engine**: Configurable buy/sell signals with technical indicators

### 📰 News-Based Stock Screener
- **News Intelligence**: Fetches and analyzes recent news for 50+ liquid stocks
- **Volume Analysis**: Detects unusual volume surges (2x+ average)
- **Price Movement Tracking**: Identifies significant price changes (3-15%)
- **Sentiment Analysis**: Categorizes news as bullish/bearish
- **Dual Trading Strategies**: 
  - **Bullish** → Buy for delivery (5-30 day hold)
  - **Bearish** → Sell intraday (same-day exit)
- **Interactive UI**: Filter, sort, and analyze opportunities in real-time

### 🔐 Authentication & Security
- **Fyers OAuth Integration**: Secure API authentication
- **Session Management**: Token-based access control
- **Environment Variables**: Secure credential storage

## 📸 Screenshots

### News Screener Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  📊 Found 12 Opportunities  |  [All] [Bullish] [Bearish]│
│─────────────────────────────────────────────────────────│
│  🟢 RELIANCE     BULLISH STRONG                         │
│     ₹2,450  +4.2%  |  Volume: 3.5x  |  News: 5         │
│     Action: BUY (Delivery)  |  Contract news detected   │
│─────────────────────────────────────────────────────────│
│  🔴 TATAMOTORS   BEARISH MODERATE                       │
│     ₹785  -3.8%  |  Volume: 2.8x  |  News: 3           │
│     Action: SELL (Intraday)  |  Loss warning issued     │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Fyers Trading Account ([Sign up](https://fyers.in/))
- NewsAPI Key ([Get free key](https://newsapi.org/))

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/ashutoshverma23/StockNewsScreener.git
cd StockNewsScreener
```

2. **Create virtual environment**

```bash
python -m venv .venv

# On Windows (prefer using command prompt for windows)
.venv\Scripts\activate

# On Mac/Linux
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:

```bash
# Fyers API Configuration
FYERS_CLIENT_ID=your_client_id_here
FYERS_SECRET_KEY=your_secret_key_here
FYERS_REDIRECT_URI=http://localhost:5000/callback
FYERS_ACCESS_TOKEN=

# Flask Configuration
SECRET_KEY=your-secret-key-change-this-to-something-random
DEBUG=True

# News Screener Configuration
NEWS_API_KEY=your_newsapi_key_here
ENABLE_PERIODIC_SCREENER=true

# Screening Parameters (Optional)
VOLUME_SURGE_THRESHOLD=2.0
PRICE_CHANGE_MIN=3.0
PRICE_CHANGE_MAX=15.0
LOOKBACK_DAYS=5
MIN_PRICE=20
MAX_PRICE=5000
```

5. **Run the application**

```bash
python app.py
```

6. **Authenticate with Fyers**
- **Login**: http://localhost:5000
  If you are authenticated with Fyers(need to do every trading day), then it will automatically direct to dashboard
  otherwise it will automatically open Fyers authentication page, after you authenticate, it will store the access-token, and you are ready to start your scan

8. **Access the dashboards**

- **Trading Bot**: http://localhost:5000/dashboard
- **News Screener**: http://localhost:5000/screener

## 📁 Project Structure

```
intraday-trading-bot/
│
├── app.py                          # Main Flask application
├── socket_worker.py                # WebSocket/data streaming handler
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
│
├── auth/                           # Authentication module
│   ├── __init__.py
│   └── routes.py                   # OAuth routes
│
├── bot_core/                       # Trading bot core logic
│   ├── __init__.py
│   ├── broker.py                   # Broker interface & order management
│   ├── strategy.py                 # Trading strategy implementation
│   ├── news_screener.py           # News-based stock screener
│   ├── enhanced_screener.py       # Advanced sentiment analysis
│   └── fyers_auth.py              # Authentication helper
│
├── templates/                      # HTML templates
│   ├── index.html                 # Trading bot dashboard
│   ├── screener.html              # News screener dashboard
│   └── login.html                 # Login page
│
├── static/                         # Static assets (optional)
│   ├── css/
│   ├── js/
│   └── images/
│
└── utils/                          # Utility functions
    └── helpers.py
```

## 🎯 Usage Guide

#### 1. Strategy Configuration

Edit `bot_core/strategy.py` to customize:

```python
# Entry conditions
VOLUME_THRESHOLD = 1.5      # Minimum volume spike
RSI_OVERSOLD = 30           # Buy signal
RSI_OVERBOUGHT = 70         # Sell signal

# Risk management
STOP_LOSS_PERCENT = 2.0     # 2% stop loss
TARGET_PROFIT_PERCENT = 3.0 # 3% target
MAX_POSITIONS = 5           # Maximum concurrent positions
```

### News Screener

#### 1. Run Manual Scan

1. Navigate to http://localhost:5000/
2. Click **"Start Scan"** button
3. Wait 30-60 seconds for results
4. Use filters to view:
   - **All**: All opportunities
   - **Bullish**: Buy signals for delivery
   - **Bearish**: Sell signals for intraday

Scans run automatically every 15 minutes during market hours (9:15 AM - 3:30 PM IST).

#### 3. Analyze Specific Stocks

```python
import requests

# Get detailed analysis for a stock
response = requests.get('http://localhost:5000/api/screener/analyze/RELIANCE')
analysis = response.json()

print(f"Signal: {analysis['signal']['signal']}")
print(f"Strength: {analysis['strength_score']}/100")
print(f"Recommendation: {analysis['recommendation']['entry']}")
```

## 🔧 Configuration

### Screening Parameters

Adjust sensitivity in `.env`:

```bash
# More aggressive (more signals)
VOLUME_SURGE_THRESHOLD=1.5    # Lower = more sensitive
PRICE_CHANGE_MIN=2.0          # Smaller moves
LOOKBACK_DAYS=7               # More days of news

# More conservative (fewer, higher quality signals)
VOLUME_SURGE_THRESHOLD=3.0    # Higher = less sensitive
PRICE_CHANGE_MIN=5.0          # Bigger moves only
LOOKBACK_DAYS=3               # Recent news only
```

### Stock Universe

Edit `bot_core/news_screener.py`:

```python
def get_nse_symbols(self):
    """Add/remove stocks to scan"""
    symbols = [
        "NSE:RELIANCE-EQ",
        "NSE:TCS-EQ",
        "NSE:YOURSTOCK-EQ",  # Add your stocks
        # ... more stocks
    ]
    return symbols
```

### News Sources

Default: NewsAPI.org (100 requests/day free)

Alternative: Google News RSS (unlimited, free):

```python
import feedparser

def fetch_news_for_stock(self, stock_name):
    clean_name = stock_name.replace('NSE:', '').replace('-EQ', '')
    url = f"https://news.google.com/rss/search?q={clean_name}+stock"
    
    feed = feedparser.parse(url)
    return [{
        'title': entry.title,
        'url': entry.link,
        'publishedAt': entry.published
    } for entry in feed.entries[:5]]
```

## 📊 API Reference

### News Screener Endpoints

```
GET  /screener                      - Screener dashboard
POST /api/screener/initialize       - Initialize screener
POST /api/screener/scan             - Start stock scan
GET  /api/screener/results          - Get scan results
GET  /api/screener/analyze/<symbol> - Detailed stock analysis
GET  /api/screener/status           - Screener status
```

## ⚠️ Important Notes

### API Limitations

- **Fyers**: Check rate limits in [documentation](https://fyers.in/api-documentation)
- **NewsAPI**: 100 requests/day on free tier
- **WebSocket**: Connection stability depends on network

### Data Accuracy

- News may have lag (1-5 minutes)
- Volume data updates during market hours
- After-market orders not reflected immediately
- Always verify signals before trading

## 🐛 Troubleshooting

### Common Issues

**1. Authentication Failed**

```bash
# Re-authenticate
python bot_core/fyers_auth.py

# Update .env with new token manually (access token is provided in the URL of the Fyers Page after successfull Authentication)
FYERS_ACCESS_TOKEN=new_token_here
```

**2. No News Found**

```bash
# Check API key (litmit reached)
echo $NEWS_API_KEY 

# Try Google News instead (free, no key needed)
# Edit bot_core/news_screener.py fetch_news_for_stock()
```

**3. No Screening Results**

```bash
# Lower thresholds in .env
VOLUME_SURGE_THRESHOLD=1.5
PRICE_CHANGE_MIN=2.0

# Or scan during market hours only
```

### Get Help

- Check logs: `tail -f app.log`
- Run diagnostics: `python diagnose_project.py`
- Review Fyers API docs: https://fyers.in/api-documentation
- Check NewsAPI status: https://newsapi.org/account

## 📚 Documentation

- [Fyers API Documentation](https://fyers.in/api-documentation)
- [Fyers Python SDK](https://github.com/fyers-api/fyers-apiv3)
- [NewsAPI Documentation](https://newsapi.org/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ Performance

- **Scan Speed**: 50 stocks in ~30-60 seconds
- **WebSocket**: Real-time updates (< 100ms latency)
- **Memory**: ~100MB typical usage
- **CPU**: Low usage during idle, moderate during scans

## 🔄 Changelog

### Version 1.0.0 (Current)
- ✨ Initial release
- 📰 News-based stock screener
- 🔐 Fyers OAuth authentication
- 📊 Interactive dashboards
- 🔄 WebSocket real-time updates
- 📈 Advanced sentiment analysis

### Planned Features
- 📱 Mobile app
- 🤖 Machine learning price prediction
- 📊 Advanced charting with TradingView
- 🔔 Telegram/Email alerts
- 📈 Backtesting engine
- 🎯 Multiple strategy support
- 📊 Portfolio analytics

## 👨‍💻 Author

**Your Name**
- GitHub: [@ashutoshverma23](https://github.com/ashutoshverma23)
- Email: ashutoshrgnict@gmail.com
- LinkedIn: [ashutosh-verma23](https://www.linkedin.com/in/ashutosh-verma23/)

## 🙏 Acknowledgments

- Fyers API for market data
- NewsAPI for news aggregation
- Flask community for excellent framework
- All contributors and testers

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Disclaimer**: This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this software. Always do your own research and consult with financial advisors before making investment decisions.

**Happy Trading! 📈💰**

Made with ❤️ and Python
