"""
Enhanced News Screener with Sentiment Analysis
This version includes basic sentiment analysis for news articles
"""
import re
from collections import Counter

class NewsAnalyzer:
    """Analyze news sentiment and categorize news types"""
    
    # Positive keywords for bullish signals
    POSITIVE_KEYWORDS = {
        'contract', 'deal', 'win', 'won', 'awarded', 'growth', 'profit', 
        'surge', 'gain', 'record', 'high', 'acquisition', 'expand', 
        'partnership', 'collaboration', 'success', 'breakthrough', 'innovation',
        'dividend', 'buyback', 'upgrade', 'positive', 'approval', 'order',
        'revenue', 'beat', 'exceed', 'strong', 'robust', 'bullish'
    }
    
    # Negative keywords for bearish signals
    NEGATIVE_KEYWORDS = {
        'loss', 'losses', 'decline', 'drop', 'fall', 'fell', 'down', 'weak',
        'miss', 'missed', 'below', 'concern', 'worry', 'risk', 'threat',
        'lawsuit', 'investigation', 'fraud', 'scandal', 'downgrade', 'cut',
        'layoff', 'fire', 'closure', 'bankruptcy', 'debt', 'bearish', 'warning'
    }
    
    # High-impact news categories
    MAJOR_NEWS_TYPES = {
        'contract': ['contract', 'deal', 'order', 'awarded'],
        'financial': ['profit', 'revenue', 'earnings', 'results', 'quarter'],
        'acquisition': ['acquisition', 'merger', 'takeover', 'buyout'],
        'regulatory': ['approval', 'license', 'compliance', 'regulation'],
        'legal': ['lawsuit', 'court', 'legal', 'case', 'settlement'],
        'management': ['ceo', 'cfo', 'appointment', 'resignation', 'chairman'],
        'product': ['launch', 'product', 'service', 'innovation']
    }
    
    @staticmethod
    def analyze_sentiment(news_articles):
        """
        Analyze sentiment of news articles
        Returns: sentiment_score (-1 to 1), positive_count, negative_count
        """
        if not news_articles:
            return 0, 0, 0
        
        positive_count = 0
        negative_count = 0
        
        for article in news_articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            text = f"{title} {description}"
            
            # Count positive keywords
            for keyword in NewsAnalyzer.POSITIVE_KEYWORDS:
                if keyword in text:
                    positive_count += 1
            
            # Count negative keywords
            for keyword in NewsAnalyzer.NEGATIVE_KEYWORDS:
                if keyword in text:
                    negative_count += 1
        
        # Calculate sentiment score
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total
        
        return sentiment_score, positive_count, negative_count
    
    @staticmethod
    def categorize_news(news_articles):
        """Categorize news into major types"""
        categories = []
        
        for article in news_articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            text = f"{title} {description}"
            
            for category, keywords in NewsAnalyzer.MAJOR_NEWS_TYPES.items():
                if any(keyword in text for keyword in keywords):
                    categories.append(category)
                    break
        
        return categories
    
    @staticmethod
    def is_major_news(news_articles):
        """Check if there's major/impactful news"""
        categories = NewsAnalyzer.categorize_news(news_articles)
        
        # Major news categories
        major_categories = {'contract', 'acquisition', 'regulatory', 'legal'}
        
        return any(cat in major_categories for cat in categories)
    
    @staticmethod
    def get_news_summary(news_articles):
        """Get a summary of news sentiment and type"""
        if not news_articles:
            return "No recent news"
        
        sentiment_score, pos_count, neg_count = NewsAnalyzer.analyze_sentiment(news_articles)
        categories = NewsAnalyzer.categorize_news(news_articles)
        is_major = NewsAnalyzer.is_major_news(news_articles)
        
        # Determine sentiment label
        if sentiment_score > 0.3:
            sentiment_label = "Highly Positive"
        elif sentiment_score > 0:
            sentiment_label = "Positive"
        elif sentiment_score < -0.3:
            sentiment_label = "Highly Negative"
        elif sentiment_score < 0:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        # Get most common category
        if categories:
            most_common = Counter(categories).most_common(1)[0][0]
            category_str = f"{most_common.title()} News"
        else:
            category_str = "General News"
        
        return {
            'sentiment': sentiment_label,
            'sentiment_score': sentiment_score,
            'category': category_str,
            'is_major': is_major,
            'positive_keywords': pos_count,
            'negative_keywords': neg_count
        }


# Additional filters for better screening
class AdvancedFilters:
    """Additional filtering logic for better stock selection"""
    
    @staticmethod
    def check_price_volume_correlation(df, current_quote):
        """
        Check if price movement is supported by volume
        Strong moves should have strong volume
        """
        if df is None or len(df) < 5:
            return False
        
        # Get recent price changes
        recent_returns = df['close'].pct_change().tail(5)
        recent_volumes = df['volume'].tail(5)
        
        # Calculate correlation
        correlation = recent_returns.corr(recent_volumes)
        
        # For bullish: positive correlation is good
        # For bearish: negative correlation can indicate selling pressure
        return abs(correlation) > 0.3
    
    @staticmethod
    def check_breakout(df, current_quote):
        """Check if stock is breaking out from recent range"""
        if df is None or len(df) < 20:
            return False
        
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        current_price = current_quote['ltp']
        
        # Check if breaking above recent high or below recent low
        breakout_above = current_price > recent_high * 1.02  # 2% above high
        breakdown_below = current_price < recent_low * 0.98  # 2% below low
        
        return breakout_above or breakdown_below
    
    @staticmethod
    def calculate_strength_score(analysis, news_summary, df):
        """
        Calculate overall strength score for the signal
        Score from 0-100
        """
        score = 0
        
        # Volume score (30 points)
        volume_ratio = analysis['volume_ratio']
        if volume_ratio > 5:
            score += 30
        elif volume_ratio > 3:
            score += 25
        elif volume_ratio > 2:
            score += 20
        else:
            score += 10
        
        # Price change score (25 points)
        price_change = abs(analysis['price_change'])
        if price_change > 8:
            score += 25
        elif price_change > 5:
            score += 20
        elif price_change > 3:
            score += 15
        else:
            score += 10
        
        # News sentiment score (25 points)
        if news_summary:
            sentiment_score = news_summary.get('sentiment_score', 0)
            if news_summary.get('is_major', False):
                score += 15  # Major news bonus
            
            if abs(sentiment_score) > 0.5:
                score += 10
            elif abs(sentiment_score) > 0.2:
                score += 5
        
        # Range/volatility score (20 points)
        range_ratio = analysis.get('range_ratio', 0)
        if range_ratio > 2:
            score += 20
        elif range_ratio > 1.5:
            score += 15
        elif range_ratio > 1:
            score += 10
        
        return min(score, 100)


def get_trading_recommendation(signal, strength_score, news_summary):
    """Generate detailed trading recommendation"""
    if not signal:
        return None
    
    recommendations = {
        'signal_type': signal['signal'],
        'action': signal['action'],
        'strength': signal['strength'],
        'confidence_score': strength_score
    }
    
    # Entry suggestion
    if signal['signal'] == 'BULLISH':
        if strength_score > 75:
            recommendations['entry'] = "Strong Buy - Enter at current levels"
            recommendations['target'] = "5-10% upside potential"
            recommendations['stop_loss'] = "3-4% below entry"
        else:
            recommendations['entry'] = "Buy on dips - Wait for minor correction"
            recommendations['target'] = "3-7% upside potential"
            recommendations['stop_loss'] = "2-3% below entry"
    
    else:  # BEARISH
        if strength_score > 75:
            recommendations['entry'] = "Strong Sell - Short at current levels (Intraday only)"
            recommendations['target'] = "3-7% downside expected"
            recommendations['stop_loss'] = "2% above entry"
        else:
            recommendations['entry'] = "Sell on bounce - Wait for minor rally"
            recommendations['target'] = "2-5% downside expected"
            recommendations['stop_loss'] = "1.5% above entry"
    
    # Risk level
    if strength_score > 80:
        recommendations['risk_level'] = "Low Risk"
    elif strength_score > 60:
        recommendations['risk_level'] = "Medium Risk"
    else:
        recommendations['risk_level'] = "High Risk"
    
    # News impact
    if news_summary:
        recommendations['news_impact'] = news_summary['sentiment']
        recommendations['news_type'] = news_summary['category']
    
    return recommendations


# Example usage in the main screener
"""
# In the scan_stocks method, enhance the signal determination:

# Analyze news sentiment
news_summary = NewsAnalyzer.get_news_summary(news)

# Calculate strength score
strength_score = AdvancedFilters.calculate_strength_score(analysis, news_summary, df)

# Check additional filters
has_correlation = AdvancedFilters.check_price_volume_correlation(df, current_quote)
is_breakout = AdvancedFilters.check_breakout(df, current_quote)

# Get trading recommendation
recommendation = get_trading_recommendation(signal, strength_score, news_summary)

# Add to stock data
stock_data.update({
    'news_summary': news_summary,
    'strength_score': strength_score,
    'recommendation': recommendation,
    'has_price_volume_correlation': has_correlation,
    'is_breakout': is_breakout
})
"""