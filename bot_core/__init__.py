# bot_core/__init__.py
from .broker import broker, active_positions

# News Screener imports
try:
    from .news_screener import FyersNewsScreener
    from .enhanced_screener import NewsAnalyzer, AdvancedFilters, get_trading_recommendation
    SCREENER_AVAILABLE = True
except ImportError as e:
    print(f"Screener not available: {e}")
    SCREENER_AVAILABLE = False
    FyersNewsScreener = None
    NewsAnalyzer = None
    AdvancedFilters = None
    get_trading_recommendation = None

__all__ = [
    'broker', 
    'active_positions',
    'FyersNewsScreener',
    'NewsAnalyzer',
    'AdvancedFilters',
    'get_trading_recommendation',
    'SCREENER_AVAILABLE'
]