"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEWS INTELLIGENCE ENGINE - AUDUSD Market Sentiment                         ║
║  Polarice Labs 2026 | Powered by DuckDuckGo + Ollama                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Busca noticias → Evalúa con LLM → Guarda B/M/N → Usa en decisiones         ║
║  Archivos por día sin duplicados (upsert)                                    ║
║  Optimizado para AUDUSD - Australian Dollar / US Dollar                      ║
║  🦘 Carry + Commodity Currency | RBA + China + Iron Ore + Gold Focus         ║
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

# Directorios
BASE_DIR = Path(__file__).parent
NEWS_DIR = BASE_DIR / "news_data"
NEWS_DIR.mkdir(exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsIntelligence-AUD")

# Ollama config (usar el que ya está corriendo)
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3:8b"  # Modelo disponible en tu sistema

# DuckDuckGo config
DDG_SEARCH_URL = "https://api.duckduckgo.com/"

# Símbolos a monitorear - AUDUSD FOCUSED + correlated pairs
SYMBOLS = ["AUDUSD", "NZDUSD", "XAUUSD"]

# Fuentes confiables para forex + Australian/Asia-Pacific sources
TRUSTED_SOURCES = [
    "reuters", "bloomberg", "forexlive", "fxstreet", "dailyfx",
    "investing.com", "tradingview", "marketwatch", "cnbc",
    "financialjuice", "forexfactory", "ft.com",
    "abc.net.au", "smh.com.au", "afr.com", "theaustralian.com.au",
    "rba.gov.au", "abs.gov.au", "scmp.com", "nikkei.com",
    "mining.com", "kitco.com", "goldprice.org"
]

# Keywords por símbolo - AUDUSD OPTIMIZED for Commodity/Carry Currency
KEYWORDS = {
    "AUDUSD": [
        "AUDUSD", "aussie dollar", "AUD/USD", "australian dollar news",
        "RBA decision", "reserve bank australia", "aussie forecast",
        "australian dollar", "fed aussie", "aussie strength",
        "aussie trading", "aussie weakness", "australian economy",
        "australian inflation", "australian employment", "australian gdp",
        "australian retail sales", "australian CPI", "australian trade balance",
        "RBA rate decision", "RBA Bullock", "reserve bank australia rate",
        "iron ore price", "iron ore futures", "BHP rio tinto",
        "copper price", "commodity prices today", "gold price AUD",
        "China PMI", "China GDP", "China manufacturing", "China stimulus",
        "China trade data", "China property", "Beijing economic policy",
        "carry trade AUD", "risk sentiment forex", "ASX 200",
        "australian bond yield", "sydney session forex",
        "AUDUSD rally", "AUDUSD crash", "aussie forex", "commodity currency"
    ],
    "NZDUSD": [
        "NZDUSD", "kiwi dollar", "NZD/USD", "new zealand dollar news",
        "RBNZ decision", "reserve bank new zealand", "kiwi forecast",
        "new zealand economy", "new zealand dairy prices",
        "kiwi trading", "nzd strength", "nzd weakness"
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
    """Busca noticias usando DuckDuckGo"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_ddg(self, query: str) -> List[Dict]:
        """Busca en DuckDuckGo y extrae resultados relevantes"""
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
        """Busca en DuckDuckGo HTML para más resultados"""
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
        """Busca noticias para un símbolo específico"""
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
# NEWS EVALUATOR - Ollama LLM para análisis de sentimiento
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaNewsEvaluator:
    """Evalúa noticias usando Ollama LLM local"""
    
    def __init__(self, timeout=60):
        self.timeout = timeout
        self.cache = {}
    
    def evaluate_news(self, news_item: Dict) -> Dict:
        """
        Evalúa una noticia con LLM → B (bullish), M (bearish), N (neutral)
        Context-aware: AUDUSD is a commodity/carry currency.
        - China growth positive → B (AUD strengthens)
        - Iron ore/copper UP → B
        - RBA hawkish → B
        - Risk-on sentiment → B
        - China slowdown → M
        - Commodity crash → M
        - Risk-off / USD strength → M
        """
        title = news_item.get('title', '')
        symbol = news_item.get('symbol', 'AUDUSD')
        
        cache_key = hashlib.md5(f"{title}_{symbol}".encode()).hexdigest()
        if cache_key in self.cache:
            return {**news_item, **self.cache[cache_key]}
        
        prompt = f"""Analyze this financial news for {symbol} trading:

"{title}"

Context: AUDUSD is a commodity/carry currency. Australian Dollar strengthens with:
- China growth, stimulus, or strong PMI data
- Rising iron ore, copper, gold, commodity prices
- RBA hawkish stance or rate hikes
- Risk-on sentiment in global markets
- Strong Australian economic data (employment, GDP, CPI)

Australian Dollar weakens with:
- China slowdown, property crisis, weak PMI
- Falling commodity prices
- RBA dovish stance or rate cuts
- Risk-off sentiment, USD strength
- Weak Australian economic data

What is the likely impact on {symbol}?
Reply with ONLY a single letter:
B = Bullish (AUD price likely to go UP)
M = Bearish (AUD price likely to go DOWN)  
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
        """Evalúa un batch de noticias"""
        results = []
        for i, news in enumerate(news_list):
            logger.info(f"  Evaluating {i+1}/{len(news_list)}: {news.get('title', '')[:60]}...")
            evaluated = self.evaluate_news(news)
            results.append(evaluated)
            time.sleep(0.2)
        return results
    
    def get_overall_sentiment(self, news_list: List[Dict]) -> Dict:
        """Calcula el sentimiento general por símbolo"""
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
# NEWS STORAGE - JSON files por día
# ═══════════════════════════════════════════════════════════════════════════════

class NewsStorage:
    """Almacena noticias en archivos JSON por día"""
    
    def __init__(self):
        self.news_dir = NEWS_DIR
    
    def _get_today_file(self) -> Path:
        today = datetime.now().strftime("%Y%m%d")
        return self.news_dir / f"news_aud_{today}.json"
    
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
                pass
        return {'date': datetime.now().strftime("%Y-%m-%d"), 'news': {}, 'sentiment': {}}
    
    def save(self, data: Dict):
        file_path = self._get_today_file()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def upsert_news(self, news_list: List[Dict]) -> int:
        """Inserta o actualiza noticias sin duplicados"""
        data = self.load_today()
        new_count = 0
        
        for news in news_list:
            hash_id = self._get_hash(news)
            if hash_id not in data['news']:
                data['news'][hash_id] = {
                    **news,
                    'added_at': datetime.now().isoformat()
                }
                new_count += 1
        
        self.save(data)
        return new_count
    
    def update_sentiment(self, sentiment: Dict):
        data = self.load_today()
        data['sentiment'] = sentiment
        data['sentiment_updated_at'] = datetime.now().isoformat()
        self.save(data)
    
    def get_sentiment_for_llm(self) -> Dict:
        """
        Retorna el sentimiento en formato optimizado para LLM.
        AUDUSD focused with cross-asset correlation (NZDUSD, XAUUSD).
        """
        data = self.load_today()
        sentiment = data.get('sentiment', {})
        
        if not sentiment:
            return {
                'AUDUSD': 'N', 'NZDUSD': 'N', 'XAUUSD': 'N',
                'summary': 'No news data available today',
                'confidence': 0
            }
        
        summaries = []
        for symbol in SYMBOLS:
            s = sentiment.get(symbol, {})
            sent = s.get('sentiment', 'N')
            score = s.get('score', 0)
            total = s.get('total', 0)
            emoji = '📈' if sent == 'B' else ('📉' if sent == 'M' else '➡️')
            summaries.append(f"{symbol}:{sent}{emoji}(score:{score},n={total})")
        
        # AUDUSD-specific confidence calculation
        aud_score = abs(sentiment.get('AUDUSD', {}).get('score', 0))
        aud_total = sentiment.get('AUDUSD', {}).get('total', 0)
        aud_conf = min(1.0, aud_score * (1 + min(aud_total, 10) * 0.1))
        
        # Boost confidence if correlated assets (Gold, NZD) agree with AUD direction
        aud_sent = sentiment.get('AUDUSD', {}).get('sentiment', 'N')
        gold_sent = sentiment.get('XAUUSD', {}).get('sentiment', 'N')
        nzd_sent = sentiment.get('NZDUSD', {}).get('sentiment', 'N')
        
        correlation_boost = 0
        if aud_sent == gold_sent and aud_sent != 'N':
            correlation_boost += 0.05  # Gold confirms AUD direction
        if aud_sent == nzd_sent and aud_sent != 'N':
            correlation_boost += 0.05  # NZD (sister currency) confirms
        
        aud_conf = min(1.0, aud_conf + correlation_boost)
        
        return {
            'AUDUSD': sentiment.get('AUDUSD', {}).get('sentiment', 'N'),
            'NZDUSD': sentiment.get('NZDUSD', {}).get('sentiment', 'N'),
            'XAUUSD': sentiment.get('XAUUSD', {}).get('sentiment', 'N'),
            'summary': ' | '.join(summaries),
            'confidence': aud_conf,
            'confidence_AUDUSD': aud_conf,
            'raw': sentiment
        }


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS INTELLIGENCE ENGINE - Orquestador principal
# ═══════════════════════════════════════════════════════════════════════════════

class NewsIntelligenceEngine:
    """
    Motor principal de inteligencia de noticias para AUDUSD.
    Orquesta: Fetch → Evaluate → Store → Provide to LLM
    🦘 Commodity/Carry currency focus: RBA, China, Iron Ore, Gold, Risk Sentiment
    """
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.evaluator = OllamaNewsEvaluator()
        self.storage = NewsStorage()
        self.last_fetch_time = None
        self.fetch_interval = timedelta(minutes=90)
    
    def should_fetch(self) -> bool:
        if self.last_fetch_time is None:
            return True
        return datetime.now() - self.last_fetch_time > self.fetch_interval
    
    def fetch_and_evaluate(self) -> Dict:
        """
        Flujo completo:
        1. Busca noticias en DuckDuckGo (AUDUSD, NZDUSD, XAUUSD)
        2. Evalúa con Ollama (B/M/N) with commodity/carry context
        3. Guarda sin duplicados
        4. Calcula sentimiento general con correlación cross-asset
        """
        logger.info("=" * 60)
        logger.info("🦘 AUDUSD NEWS INTELLIGENCE - Starting fetch cycle...")
        logger.info("=" * 60)
        
        all_news = []
        
        for symbol in SYMBOLS:
            logger.info(f"🔍 Fetching news for {symbol}...")
            news = self.fetcher.fetch_news_for_symbol(symbol)
            all_news.extend(news)
        
        if not all_news:
            logger.warning("No news found!")
            return self.storage.get_sentiment_for_llm()
        
        logger.info(f"🤖 Evaluating {len(all_news)} news items with Ollama...")
        evaluated_news = self.evaluator.evaluate_batch(all_news)
        
        new_count = self.storage.upsert_news(evaluated_news)
        logger.info(f"💾 Saved {new_count} new news items")
        
        all_stored = list(self.storage.load_today()['news'].values())
        overall_sentiment = self.evaluator.get_overall_sentiment(all_stored)
        self.storage.update_sentiment(overall_sentiment)
        
        for symbol, sent in overall_sentiment.items():
            emoji = '📈' if sent['sentiment'] == 'B' else ('📉' if sent['sentiment'] == 'M' else '➡️')
            logger.info(f"  {symbol}: {sent['sentiment']} {emoji} (score: {sent['score']})")
        
        self.last_fetch_time = datetime.now()
        return self.storage.get_sentiment_for_llm()
    
    def get_context_for_llm(self) -> Dict:
        """Obtiene el contexto de noticias para usar en decisiones LLM."""
        if self.should_fetch():
            logger.info("🦘 News data stale, fetching fresh news...")
            return self.fetch_and_evaluate()
        
        sentiment = self.storage.get_sentiment_for_llm()
        sentiment['should_consider'] = sentiment.get('confidence', 0) > 0.15
        return sentiment
    
    def get_trading_bias(self, symbol: str) -> Tuple[str, float]:
        """
        Retorna el sesgo de trading para un símbolo.
        AUDUSD-aware: uses cross-asset correlation for higher confidence.
        """
        sentiment = self.storage.get_sentiment_for_llm()
        s = sentiment.get(symbol, 'N')
        
        if symbol == 'AUDUSD':
            conf = sentiment.get('confidence_AUDUSD', sentiment.get('confidence', 0.5))
        else:
            conf = sentiment.get('confidence', 0.5)
        
        if s == 'B':
            return ('BULLISH', max(0.4, conf))
        elif s == 'M':
            return ('BEARISH', max(0.4, conf))
        else:
            return ('NEUTRAL', 0.2)


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Ejecuta el motor de noticias standalone"""
    print("=" * 70)
    print("🦘 NEWS INTELLIGENCE ENGINE - AUDUSD")
    print("   Commodity & Carry Currency | RBA + China + Iron Ore + Gold")
    print("   Powered by DuckDuckGo + Ollama | Polarice Labs 2026")
    print("=" * 70)
    
    engine = NewsIntelligenceEngine()
    sentiment = engine.fetch_and_evaluate()
    
    print("\n" + "=" * 70)
    print("📊 TODAY'S MARKET SENTIMENT:")
    print("=" * 70)
    print(f"   🦘 AUDUSD: {sentiment.get('AUDUSD', 'N')}")
    print(f"   🥝 NZDUSD: {sentiment.get('NZDUSD', 'N')}")
    print(f"   🥇 XAUUSD: {sentiment.get('XAUUSD', 'N')}")
    print(f"   Summary: {sentiment.get('summary', 'N/A')}")
    print(f"   Confidence: {sentiment.get('confidence_AUDUSD', 0):.2f}")
    print("=" * 70)
    
    return sentiment


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - Para usar desde otros módulos
# ═══════════════════════════════════════════════════════════════════════════════

_news_engine = None

def get_news_sentiment() -> Dict:
    """
    Función helper para obtener sentimiento desde otros módulos.
    
    Usage:
        from news_intelligence import get_news_sentiment
        sentiment = get_news_sentiment()
        if sentiment['AUDUSD'] == 'B':
            # Bias bullish para AUD - commodities strong
    """
    global _news_engine
    
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    
    return _news_engine.get_context_for_llm()


def get_trading_bias(symbol: str) -> Tuple[str, float]:
    """
    Obtiene el sesgo de trading para un símbolo.
    
    Usage:
        from news_intelligence import get_trading_bias
        bias, confidence = get_trading_bias('AUDUSD')
        # bias = 'BULLISH', 'BEARISH', or 'NEUTRAL'
    """
    global _news_engine
    
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    
    return _news_engine.get_trading_bias(symbol)


if __name__ == "__main__":
    main()
