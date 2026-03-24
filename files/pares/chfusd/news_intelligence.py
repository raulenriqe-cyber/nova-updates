"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEWS INTELLIGENCE ENGINE - CHFUSD Market Sentiment                         ║
║  Polarice Labs 2026 | Powered by DuckDuckGo + Ollama                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Search news → Evaluate with LLM → Store B/M/N → Use in decisions           ║
║  Daily files with no duplicates (upsert)                                     ║
║  Optimized for CHFUSD - Swiss Franc / US Dollar                             ║
║  🇨🇭 Safe Haven + SNB + Gold Correlation + EUR Impact Focus                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import hashlib
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import re

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Directories
BASE_DIR = Path(__file__).parent
NEWS_DIR = BASE_DIR / "news_data"
NEWS_DIR.mkdir(exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsIntelligence-CHF")

# Ollama config (use running instance)
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3:8b"  # Model available in your system

# DuckDuckGo config
DDG_SEARCH_URL = "https://api.duckduckgo.com/"

# Symbols to monitor - CHFUSD FOCUSED + correlated pairs
SYMBOLS = ["CHFUSD", "EURCHF", "XAUUSD"]

# Trusted sources for forex + Swiss/European sources
TRUSTED_SOURCES = [
    "reuters", "bloomberg", "forexlive", "fxstreet", "dailyfx",
    "investing.com", "tradingview", "marketwatch", "cnbc",
    "financialjuice", "forexfactory", "ft.com",
    "swissinfo.ch", "nzz.ch", "tagesanzeiger.ch", "blick.ch",
    "snb.ch", "admin.ch", "seco.admin.ch", "ecb.europa.eu",
    "kitco.com", "goldprice.org", "mining.com"
]

# Keywords by symbol - CHFUSD OPTIMIZED for Safe Haven Currency
KEYWORDS = {
    "CHFUSD": [
        "CHFUSD", "swiss franc", "CHF/USD", "swiss franc news",
        "SNB decision", "swiss national bank", "franc forecast",
        "swiss franc dollar", "swiss franc strength", "swiss franc weakness",
        "swiss franc trading", "swiss economy", "swiss inflation",
        "swiss unemployment", "swiss GDP", "swiss KOF index",
        "SNB Jordan", "SNB rate decision", "swiss interest rate",
        "swiss negative rates", "swiss forex intervention",
        "safe haven flows", "risk off swiss franc", "safe haven currency",
        "swiss franc safe haven", "flight to safety CHF",
        "geopolitical risk CHF", "market turmoil swiss franc",
        "swiss franc gold correlation", "gold CHF relationship",
        "swiss gold reserves", "swiss banking system",
        "swiss watch exports", "swiss pharmaceutical exports",
        "swiss trade balance", "swiss current account",
        "EUR CHF parity", "SNB floor", "swiss franc cap",
        "strong swiss franc problem", "CHF appreciation",
        "CHFUSD rally", "CHFUSD crash", "swiss franc forex"
    ],
    "EURCHF": [
        "EURCHF", "EUR/CHF", "euro swiss franc",
        "ECB SNB", "EUR CHF parity", "swiss franc euro",
        "eurozone swiss", "SNB floor EURCHF",
        "swiss franc euro rate", "EUR CHF intervention"
    ],
    "XAUUSD": [
        "XAUUSD", "gold price", "XAU/USD", "gold news today",
        "gold forecast", "gold futures", "gold demand",
        "gold safe haven", "gold fed", "gold inflation hedge",
        "gold rally", "gold crash", "gold central bank buying"
    ]
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEWS FETCHER - DuckDuckGo Instant Answers API
# ═══════════════════════════════════════════════════════════════════════════════

class NewsFetcher:
    """Search news using DuckDuckGo"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_ddg(self, query: str) -> List[Dict]:
        """Search DuckDuckGo and extract relevant results"""
        results = []
        
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_redirect': 1,
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = self.session.get(DDG_SEARCH_URL, params=params, timeout=10)
            data = response.json()
            
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:200],
                            'url': topic.get('FirstURL', ''),
                            'source': 'duckduckgo'
                        })
            
            if data.get('Abstract'):
                results.append({
                    'title': data['Abstract'][:300],
                    'url': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', 'unknown')
                })
                
        except Exception as e:
            logger.warning(f"DDG search error: {e}")
        
        return results
    
    def search_ddg_html(self, query: str) -> List[Dict]:
        """Search DuckDuckGo HTML for more results"""
        results = []
        
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            response = self.session.get(url, timeout=15)
            text = response.text
            
            pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>'
            matches = re.findall(pattern, text)
            
            for url_match, title in matches[:8]:
                if any(src in url_match.lower() for src in TRUSTED_SOURCES):
                    results.append({
                        'title': title.strip()[:200],
                        'url': url_match,
                        'source': next((s for s in TRUSTED_SOURCES if s in url_match.lower()), 'unknown')
                    })
                    
        except Exception as e:
            logger.warning(f"DDG HTML search error: {e}")
        
        return results
    
    def fetch_news_for_symbol(self, symbol: str) -> List[Dict]:
        """Fetch news for specific symbol"""
        all_news = []
        keywords = KEYWORDS.get(symbol, [])
        
        for kw in keywords[:6]:
            news = self.search_ddg(f"{kw} news today")
            for n in news:
                n['symbol'] = symbol
                n['keyword'] = kw
            all_news.extend(news)
            
            news_html = self.search_ddg_html(f"{kw} news")
            for n in news_html:
                n['symbol'] = symbol
                n['keyword'] = kw
            all_news.extend(news_html)
            
            time.sleep(0.5)
        
        return all_news


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS EVALUATOR - Ollama LLM for sentiment analysis
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaNewsEvaluator:
    """Evaluate news using local Ollama LLM"""
    
    def __init__(self, timeout=60):
        self.timeout = timeout
        self.cache = {}
    
    def evaluate_news(self, news_item: Dict) -> Dict:
        """
        Evaluate news with LLM → B (bullish), M (bearish), N (neutral)
        Context-aware: CHFUSD is a safe haven currency.
        - Risk-off / geopolitical tensions → B (CHF strengthens as safe haven)
        - Gold rally → B (CHF-gold correlation)
        - SNB hawkish / rate hikes → B
        - Weak USD → B
        - Risk-on sentiment → M (CHF weakens, capital flows to risk assets)
        - Gold crash → M
        - SNB dovish / intervention to weaken CHF → M
        - Strong USD → M
        """
        title = news_item.get('title', '')
        symbol = news_item.get('symbol', 'CHFUSD')
        
        cache_key = hashlib.md5(f"{title}_{symbol}".encode()).hexdigest()
        if cache_key in self.cache:
            return {**news_item, **self.cache[cache_key]}
        
        prompt = f"""Analyze this financial news for {symbol} trading:

"{title}"

Context: CHFUSD is a SAFE HAVEN currency. Swiss Franc strengthens (CHF/USD UP) with:
- Risk-off sentiment, market turmoil, geopolitical tensions
- Flight to safety, safe haven flows
- Gold rallying (CHF-gold positive correlation)
- SNB hawkish stance or interest rate hikes
- EUR weakness (CHF often correlates with EUR trends)
- Weak US Dollar
- Strong Swiss economic data

Swiss Franc weakens (CHF/USD DOWN) with:
- Risk-on sentiment, market calm, optimism
- Capital flowing OUT of safe havens into risk assets
- Gold crashing
- SNB dovish stance, intervention to weaken CHF, negative rates
- EUR strength
- Strong US Dollar
- Weak Swiss economic data

What is the likely impact on {symbol}?
Reply with ONLY a single letter:
B = Bullish (CHF price likely to go UP vs USD)
M = Bearish (CHF price likely to go DOWN vs USD)
N = Neutral (no clear direction or not relevant)

Your answer (B, M, or N):"""

        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 5}
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('response', '').strip().upper()
                
                if 'B' in text:
                    sentiment = 'B'
                elif 'M' in text:
                    sentiment = 'M'
                else:
                    sentiment = 'N'
                
                self.cache[cache_key] = {'sentiment': sentiment}
                return {**news_item, 'sentiment': sentiment}
            else:
                return {**news_item, 'sentiment': 'N'}
                
        except requests.exceptions.Timeout:
            logger.warning(f"Ollama timeout for: {title[:50]}...")
            return {**news_item, 'sentiment': 'N'}
        except Exception as e:
            logger.warning(f"Ollama error: {e}")
            return {**news_item, 'sentiment': 'N'}
    
    def evaluate_batch(self, news_list: List[Dict]) -> List[Dict]:
        """Evaluate a batch of news"""
        results = []
        for i, news in enumerate(news_list):
            logger.info(f"  Evaluating {i+1}/{len(news_list)}: {news.get('title', '')[:60]}...")
            evaluated = self.evaluate_news(news)
            results.append(evaluated)
            time.sleep(0.2)
        return results
    
    def get_overall_sentiment(self, news_list: List[Dict]) -> Dict:
        """Calculate overall sentiment by symbol"""
        sentiment_by_symbol = {}
        
        for symbol in SYMBOLS:
            symbol_news = [n for n in news_list if n.get('symbol') == symbol]
            
            bullish = sum(1 for n in symbol_news if n.get('sentiment') == 'B')
            bearish = sum(1 for n in symbol_news if n.get('sentiment') == 'M')
            neutral = sum(1 for n in symbol_news if n.get('sentiment') == 'N')
            total = len(symbol_news)
            
            if total == 0:
                sentiment_by_symbol[symbol] = {
                    'sentiment': 'N',
                    'score': 0,
                    'bullish': 0,
                    'bearish': 0,
                    'neutral': 0,
                    'total': 0
                }
            else:
                score = (bullish - bearish) / total
                
                if score > 0.2:
                    overall = 'B'
                elif score < -0.2:
                    overall = 'M'
                else:
                    overall = 'N'
                
                sentiment_by_symbol[symbol] = {
                    'sentiment': overall,
                    'score': round(score, 2),
                    'bullish': bullish,
                    'bearish': bearish,
                    'neutral': neutral,
                    'total': total
                }
        
        return sentiment_by_symbol


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS STORAGE - JSON files per day
# ═══════════════════════════════════════════════════════════════════════════════

class NewsStorage:
    """Store news in daily JSON files"""
    
    def __init__(self):
        self.news_dir = NEWS_DIR
    
    def _get_today_file(self) -> Path:
        today = datetime.now().strftime("%Y%m%d")
        return self.news_dir / f"news_chf_{today}.json"
    
    def _get_hash(self, news_item: Dict) -> str:
        content = f"{news_item.get('title', '')}{news_item.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def load_today(self) -> Dict:
        file_path = self._get_today_file()
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'news': [], 'sentiment': {}, 'last_update': None}
        return {'news': [], 'sentiment': {}, 'last_update': None}
    
    def save_today(self, data: Dict):
        file_path = self._get_today_file()
        data['last_update'] = datetime.now().isoformat()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def upsert_news(self, new_news: List[Dict]) -> Tuple[int, int]:
        """Insert or update news (avoiding duplicates)"""
        data = self.load_today()
        existing_hashes = {self._get_hash(n): n for n in data['news']}
        
        added = 0
        updated = 0
        
        for news in new_news:
            h = self._get_hash(news)
            if h not in existing_hashes:
                data['news'].append(news)
                added += 1
            else:
                # Update if sentiment changed
                if existing_hashes[h].get('sentiment') != news.get('sentiment'):
                    for i, n in enumerate(data['news']):
                        if self._get_hash(n) == h:
                            data['news'][i] = news
                            updated += 1
                            break
        
        self.save_today(data)
        return added, updated
    
    def get_recent_sentiment(self, hours: int = 24) -> Dict:
        """Get sentiment from last N hours"""
        data = self.load_today()
        return data.get('sentiment', {})


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class NewsIntelligenceEngine:
    """Main news intelligence engine for CHFUSD"""
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.evaluator = OllamaNewsEvaluator()
        self.storage = NewsStorage()
    
    def update_news(self):
        """Fetch, evaluate, and store news"""
        logger.info("🇨🇭 Starting news update for CHFUSD...")
        
        all_news = []
        for symbol in SYMBOLS:
            logger.info(f"  Fetching news for {symbol}...")
            news = self.fetcher.fetch_news_for_symbol(symbol)
            logger.info(f"  Found {len(news)} articles for {symbol}")
            all_news.extend(news)
        
        if not all_news:
            logger.warning("No news found")
            return
        
        # Remove duplicates by hash
        seen = {}
        unique_news = []
        for n in all_news:
            h = hashlib.md5(f"{n.get('title', '')}{n.get('url', '')}".encode()).hexdigest()[:16]
            if h not in seen:
                seen[h] = True
                unique_news.append(n)
        
        logger.info(f"  Unique articles: {len(unique_news)}")
        
        # Evaluate with LLM
        logger.info("  Evaluating sentiment with LLM...")
        evaluated_news = self.evaluator.evaluate_batch(unique_news)
        
        # Calculate overall sentiment
        sentiment = self.evaluator.get_overall_sentiment(evaluated_news)
        
        # Store
        added, updated = self.storage.upsert_news(evaluated_news)
        logger.info(f"  Stored: {added} new, {updated} updated")
        
        # Update sentiment summary
        data = self.storage.load_today()
        data['sentiment'] = sentiment
        self.storage.save_today(data)
        
        # Log summary
        for symbol, sent in sentiment.items():
            logger.info(f"  {symbol}: {sent['sentiment']} (score: {sent['score']:.2f}, "
                       f"B:{sent['bullish']} M:{sent['bearish']} N:{sent['neutral']})")
        
        logger.info("🇨🇭 News update complete")
    
    def get_sentiment(self, symbol: str = "CHFUSD") -> Dict:
        """Get current sentiment for symbol"""
        data = self.storage.load_today()
        sentiment = data.get('sentiment', {})
        return sentiment.get(symbol, {'sentiment': 'N', 'score': 0})
    
    def get_all_sentiments(self) -> Dict:
        """Get sentiments for all symbols"""
        data = self.storage.load_today()
        return data.get('sentiment', {})


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API - For use with quantum_core
# ═══════════════════════════════════════════════════════════════════════════════

_news_engine = None

def get_engine() -> NewsIntelligenceEngine:
    """Singleton pattern for news engine"""
    global _news_engine
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    return _news_engine

def get_news_sentiment(symbol: str = "CHFUSD") -> str:
    """Get sentiment for symbol: 'B', 'M', or 'N'"""
    try:
        engine = get_engine()
        sentiment_data = engine.get_sentiment(symbol)
        return sentiment_data.get('sentiment', 'N')
    except:
        return 'N'

def get_news_score(symbol: str = "CHFUSD") -> float:
    """Get sentiment score [-1.0 to 1.0]"""
    try:
        engine = get_engine()
        sentiment_data = engine.get_sentiment(symbol)
        return sentiment_data.get('score', 0.0)
    except:
        return 0.0


def get_trading_bias(symbol: str = "USDCHF") -> Tuple[str, float]:
    """
    Get trading bias for USDCHF based on news sentiment.
    
    CRITICAL DIRECTION MAPPING for USDCHF (reverse pair):
    - News says B = "Bullish CHF" = CHF strengthens = USDCHF goes DOWN = BEARISH for USDCHF price
    - News says M = "Bearish CHF" = CHF weakens = USDCHF goes UP = BULLISH for USDCHF price
    
    Returns:
        (bias, confidence)
        bias: 'BULLISH' (USDCHF up / CHF weak), 'BEARISH' (USDCHF down / CHF strong), 'NEUTRAL'
        confidence: 0.0-1.0
    """
    try:
        engine = get_engine()
        
        # Get sentiment for CHFUSD (our news is classified for CHF strength)
        chf_sentiment = engine.get_sentiment("CHFUSD")
        # Also check correlated pairs
        gold_sentiment = engine.get_sentiment("XAUUSD")
        eurchf_sentiment = engine.get_sentiment("EURCHF")
        
        chf_s = chf_sentiment.get('sentiment', 'N')
        chf_score = chf_sentiment.get('score', 0.0)
        gold_s = gold_sentiment.get('sentiment', 'N')
        gold_score = gold_sentiment.get('score', 0.0)
        
        # Calculate composite confidence from all sources
        total_articles = chf_sentiment.get('total', 0) + gold_sentiment.get('total', 0)
        if total_articles == 0:
            return ('NEUTRAL', 0.1)
        
        # Weight: 70% CHF direct news, 30% gold correlation (both safe havens)
        # Gold UP = risk-off = CHF strong = USDCHF DOWN = BEARISH
        composite_score = chf_score * 0.70 + gold_score * 0.30
        confidence = min(0.85, abs(composite_score) * 0.8 + 0.2)
        
        # ═══════════════════════════════════════════════════════════════════
        # CRITICAL: INVERT for USDCHF trading direction
        # B = Bullish CHF = USDCHF DOWN = BEARISH for our BUY/SELL logic
        # M = Bearish CHF = USDCHF UP = BULLISH for our BUY/SELL logic
        # ═══════════════════════════════════════════════════════════════════
        if composite_score > 0.15:
            # News is Bullish CHF → USDCHF goes DOWN → BEARISH
            return ('BEARISH', max(0.35, confidence))
        elif composite_score < -0.15:
            # News is Bearish CHF → USDCHF goes UP → BULLISH
            return ('BULLISH', max(0.35, confidence))
        else:
            return ('NEUTRAL', 0.15)
    
    except Exception as e:
        logger.debug(f"get_trading_bias error: {e}")
        return ('NEUTRAL', 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for manual testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   🇨🇭 CHFUSD News Intelligence Engine                        ║")
    print("║      Swiss Franc Safe Haven Sentiment Analysis               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    engine = NewsIntelligenceEngine()
    
    print("Updating news...")
    engine.update_news()
    
    print("\n" + "="*60)
    print("CURRENT SENTIMENT SUMMARY:")
    print("="*60)
    
    sentiments = engine.get_all_sentiments()
    for symbol, data in sentiments.items():
        print(f"\n{symbol}:")
        print(f"  Overall: {data['sentiment']}")
        print(f"  Score: {data['score']:.2f}")
        print(f"  Bullish: {data['bullish']} | Bearish: {data['bearish']} | Neutral: {data['neutral']}")
        print(f"  Total analyzed: {data['total']}")
