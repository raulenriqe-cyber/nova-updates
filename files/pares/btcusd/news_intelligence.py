"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEWS INTELLIGENCE ENGINE - BTCUSD Market Sentiment                         ║
║  Polarice Labs 2026 | Powered by DuckDuckGo + Ollama                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Busca noticias → Evalúa con LLM → Guarda B/M/N → Usa en decisiones         ║
║  Archivos por día sin duplicados (upsert)                                    ║
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
logger = logging.getLogger("NewsIntelligence")

# Ollama config (usar el que ya está corriendo)
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3:8b"  # Modelo disponible en tu sistema

# DuckDuckGo config
DDG_SEARCH_URL = "https://api.duckduckgo.com/"

# Símbolos a monitorear
SYMBOLS = ["XAUUSD", "EURUSD", "USDJPY", "BTCUSD"]

# Fuentes confiables para forex/commodities/crypto
TRUSTED_SOURCES = [
    "reuters", "bloomberg", "forexlive", "fxstreet", "dailyfx",
    "investing.com", "tradingview", "kitco", "marketwatch", "cnbc",
    "financialjuice", "forexfactory", "goldprice", "bullionvault",
    "coindesk", "cointelegraph", "cryptonews", "bitcoinmagazine"
]

# Keywords por símbolo
KEYWORDS = {
    "XAUUSD": [
        "gold price", "gold news", "XAUUSD", "gold market",
        "gold forecast", "precious metals", "gold trading",
        "fed gold", "inflation gold", "gold bullion",
        "gold rally", "gold crash", "gold outlook"
    ],
    "EURUSD": [
        "EURUSD", "euro dollar", "EUR/USD", "euro news",
        "ECB decision", "fed decision", "euro forecast",
        "european central bank", "federal reserve",
        "euro trading", "dollar strength", "euro weakness"
    ],
    "USDJPY": [
        "USDJPY", "yen dollar", "USD/JPY", "yen news",
        "BOJ decision", "bank of japan", "yen forecast",
        "japanese yen", "fed japan", "yen intervention",
        "yen trading", "yen strength", "yen weakness",
        "japan economy", "japan inflation"
    ],
    "BTCUSD": [
        "BTCUSD", "bitcoin price", "BTC/USD", "bitcoin news",
        "bitcoin forecast", "cryptocurrency", "bitcoin trading",
        "bitcoin rally", "bitcoin crash", "bitcoin outlook",
        "crypto market", "bitcoin etf", "bitcoin halving",
        "bitcoin whale", "bitcoin mining", "blockchain"
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
            # DuckDuckGo Instant Answer API
            params = {
                'q': query,
                'format': 'json',
                'no_redirect': 1,
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = self.session.get(DDG_SEARCH_URL, params=params, timeout=10)
            data = response.json()
            
            # Extraer resultados relacionados
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:200],
                            'url': topic.get('FirstURL', ''),
                            'source': 'duckduckgo'
                        })
            
            # Abstract si existe
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
            # Búsqueda HTML (más resultados)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            response = self.session.get(url, timeout=15)
            
            # Parsear resultados básicos (sin BeautifulSoup para simplicidad)
            # Buscar patrones de resultados
            text = response.text
            
            # Extraer títulos y URLs con regex simple
            pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>'
            matches = re.findall(pattern, text)
            
            for url, title in matches[:10]:
                # Verificar si es de fuente confiable
                is_trusted = any(src in url.lower() for src in TRUSTED_SOURCES)
                
                results.append({
                    'title': title.strip(),
                    'url': url,
                    'source': 'web',
                    'trusted': is_trusted
                })
                
        except Exception as e:
            logger.warning(f"DDG HTML search error: {e}")
        
        return results
    
    def fetch_news_for_symbol(self, symbol: str) -> List[Dict]:
        """Busca noticias para un símbolo específico"""
        all_results = []
        keywords = KEYWORDS.get(symbol, [symbol])
        
        for keyword in keywords[:4]:  # Limitar búsquedas
            query = f"{keyword} news today {datetime.now().strftime('%Y')}"
            
            # Buscar con ambos métodos
            results = self.search_ddg(query)
            results.extend(self.search_ddg_html(query))
            
            for r in results:
                r['symbol'] = symbol
                r['keyword'] = keyword
                r['fetched_at'] = datetime.now().isoformat()
            
            all_results.extend(results)
            time.sleep(0.5)  # Rate limiting
        
        # Eliminar duplicados por URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url_hash = hashlib.md5(r.get('url', '').encode()).hexdigest()
            if url_hash not in seen_urls:
                seen_urls.add(url_hash)
                unique_results.append(r)
        
        logger.info(f"[{symbol}] Found {len(unique_results)} unique news items")
        return unique_results


# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA EVALUATOR - Evalúa noticias como B/M/N
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaNewsEvaluator:
    """Evalúa noticias con Ollama LLM → B (bueno), M (malo), N (neutral)"""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self.api_url = f"{host}/api/generate"
    
    def _call_ollama(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Llama a Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Baja temperatura para respuestas consistentes
                    "num_predict": 50    # Respuesta corta
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                logger.warning(f"Ollama error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
            return None
    
    def evaluate_news(self, news_item: Dict) -> str:
        """
        Evalúa una noticia y retorna:
        B = Bullish/Bueno (precio sube)
        M = Bearish/Malo (precio baja)
        N = Neutral (sin impacto claro)
        """
        symbol = news_item.get('symbol', 'BTCUSD')
        title = news_item.get('title', '')
        
        # Prompt con contexto para cripto
        prompt = f"""Eres un analista de trading EXPERTO en forex, commodities y criptomonedas.

TAREA: Evalúa si esta noticia es positiva (B), negativa (M), o neutral (N) para {symbol}.

NOTICIA: "{title}"

=== INSTRUCCIONES CRÍTICAS ===
1. LEE LA NOTICIA COMPLETAMENTE
2. ENTIENDE QUÉ SIGNIFICA PARA EL {symbol}
3. NO responder por responder - si no está claro, responde N
4. Responde SOLO con B, M o N

=== CONTEXTO POR SÍMBOLO ===

XAUUSD (ORO):
  - SUBE (B) cuando: hay INFLACIÓN, incertidumbre, Fed baja tasas, dólar débil, guerra/crisis, miedo
  - BAJA (M) cuando: dólar fuerte, tasas suben, confianza en mercados, deflación

EURUSD (EURO):
  - SUBE (B) cuando: ECB sube tasas, economía EU fuerte, dólar débil, EUR política positiva
  - BAJA (M) cuando: Fed sube tasas, dólar fuerte, problemas EU, inflación EU

USDJPY (YEN):
  - SUBE (B) cuando: Fed hawkish, BOJ dovish, dólar fuerte, tasas US suben
  - BAJA (M) cuando: BOJ hawkish, Fed dovish, intervención japonesa, yen refugio

BTCUSD (BITCOIN):
  - SUBE (B) cuando: ETF aprobación, adopción institucional, halving, dólar débil, inflación
  - BAJA (M) cuando: regulación negativa, SEC enforcement, hacks, quiebras exchanges

=== RESPUESTA ===
Solo UNA LETRA (B, M o N):"""

        response = self._call_ollama(prompt)
        
        if response:
            # Extraer letra - busca en primeros 10 chars
            response = response.upper().strip()
            if 'B' in response[:10]:
                return 'B'
            elif 'M' in response[:10]:
                return 'M'
            elif 'N' in response[:10]:
                return 'N'
        
        return 'N'  # Default si no hay respuesta clara
    
    def evaluate_batch(self, news_list: List[Dict]) -> List[Dict]:
        """Evalúa un lote de noticias"""
        for news in news_list:
            sentiment = self.evaluate_news(news)
            news['sentiment'] = sentiment
            logger.debug(f"[{news.get('symbol')}] {sentiment}: {news.get('title', '')[:50]}...")
            time.sleep(0.3)  # Rate limiting
        
        return news_list
    
    def get_overall_sentiment(self, news_list: List[Dict]) -> Dict:
        """Calcula el sentimiento general del día"""
        result = {}
        
        for symbol in SYMBOLS:
            symbol_news = [n for n in news_list if n.get('symbol') == symbol]
            
            bullish = sum(1 for n in symbol_news if n.get('sentiment') == 'B')
            bearish = sum(1 for n in symbol_news if n.get('sentiment') == 'M')
            neutral = sum(1 for n in symbol_news if n.get('sentiment') == 'N')
            total = len(symbol_news) or 1
            
            # Score: -1 (full bearish) to +1 (full bullish)
            score = (bullish - bearish) / total
            
            # Determinar sentimiento final
            if score > 0.2:
                final_sentiment = 'B'
            elif score < -0.2:
                final_sentiment = 'M'
            else:
                final_sentiment = 'N'
            
            result[symbol] = {
                'sentiment': final_sentiment,
                'score': round(score, 2),
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral,
                'total': total
            }
        
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS STORAGE - Guarda por día sin duplicados
# ═══════════════════════════════════════════════════════════════════════════════

class NewsStorage:
    """Almacena noticias por día con upsert (sin duplicados)"""
    
    def __init__(self, storage_dir: Path = NEWS_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
    
    def _get_today_file(self) -> Path:
        """Retorna el archivo del día actual"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.storage_dir / f"news_{today}.json"
    
    def _get_news_hash(self, news: Dict) -> str:
        """Genera hash único para una noticia"""
        key = f"{news.get('symbol', '')}|{news.get('title', '')}|{news.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def load_today(self) -> Dict:
        """Carga las noticias del día"""
        file_path = self._get_today_file()
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'updated_at': datetime.now().isoformat(),
            'news': {},
            'sentiment': {}
        }
    
    def save(self, data: Dict):
        """Guarda las noticias del día"""
        file_path = self._get_today_file()
        data['updated_at'] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved news to {file_path}")
    
    def upsert_news(self, news_list: List[Dict]) -> int:
        """Inserta o actualiza noticias (sin duplicados)"""
        data = self.load_today()
        new_count = 0
        
        for news in news_list:
            news_hash = self._get_news_hash(news)
            
            if news_hash not in data['news']:
                data['news'][news_hash] = news
                new_count += 1
        
        self.save(data)
        return new_count
    
    def update_sentiment(self, sentiment: Dict):
        """Actualiza el sentimiento general del día"""
        data = self.load_today()
        data['sentiment'] = sentiment
        data['sentiment_updated_at'] = datetime.now().isoformat()
        self.save(data)
    
    def get_sentiment_for_llm(self) -> Dict:
        """Retorna el sentimiento en formato optimizado para LLM"""
        data = self.load_today()
        sentiment = data.get('sentiment', {})
        
        if not sentiment:
            return {
                'XAUUSD': 'N', 'EURUSD': 'N', 'USDJPY': 'N', 'BTCUSD': 'N',
                'summary': 'No news data available today',
                'confidence': 0
            }
        
        # Construir resumen
        summaries = []
        for symbol in SYMBOLS:
            s = sentiment.get(symbol, {})
            sent = s.get('sentiment', 'N')
            score = s.get('score', 0)
            total = s.get('total', 0)
            
            emoji = '📈' if sent == 'B' else ('📉' if sent == 'M' else '➡️')
            summaries.append(f"{symbol}:{sent}{emoji}(score:{score},n={total})")
        
        return {
            'XAUUSD': sentiment.get('XAUUSD', {}).get('sentiment', 'N'),
            'EURUSD': sentiment.get('EURUSD', {}).get('sentiment', 'N'),
            'USDJPY': sentiment.get('USDJPY', {}).get('sentiment', 'N'),
            'BTCUSD': sentiment.get('BTCUSD', {}).get('sentiment', 'N'),
            'summary': ' | '.join(summaries),
            'confidence': max(abs(sentiment.get(s, {}).get('score', 0)) for s in SYMBOLS),
            'raw': sentiment
        }


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS INTELLIGENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class NewsIntelligenceEngine:
    """Motor principal de inteligencia de noticias"""
    
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
        """Flujo completo: Busca → Evalúa → Guarda → Calcula sentimiento"""
        logger.info("📰 NEWS INTELLIGENCE - Starting fetch cycle...")
        
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
        
        self.last_fetch_time = datetime.now()
        return self.storage.get_sentiment_for_llm()
    
    def get_context_for_llm(self) -> Dict:
        if self.should_fetch():
            return self.fetch_and_evaluate()
        return self.storage.get_sentiment_for_llm()
    
    def get_trading_bias(self, symbol: str) -> Tuple[str, float]:
        sentiment = self.storage.get_sentiment_for_llm()
        s = sentiment.get(symbol, 'N')
        conf = sentiment.get('confidence', 0.5)
        
        if s == 'B':
            return ('BULLISH', max(0.4, conf))
        elif s == 'M':
            return ('BEARISH', max(0.4, conf))
        else:
            return ('NEUTRAL', 0.2)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_news_engine = None

def get_news_sentiment() -> Dict:
    global _news_engine
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    return _news_engine.get_context_for_llm()

def get_trading_bias(symbol: str) -> Tuple[str, float]:
    global _news_engine
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    return _news_engine.get_trading_bias(symbol)


def main():
    """Ejecuta el motor de noticias standalone"""
    print("=" * 70)
    print("📰 NEWS INTELLIGENCE ENGINE - XAU/EUR/JPY/BTC")
    print("   Powered by DuckDuckGo + Ollama | Polarice Labs 2026")
    print("=" * 70)
    
    engine = NewsIntelligenceEngine()
    sentiment = engine.fetch_and_evaluate()
    
    print("\n" + "=" * 70)
    print("📊 TODAY'S MARKET SENTIMENT:")
    print("=" * 70)
    for sym in SYMBOLS:
        print(f"   {sym}: {sentiment.get(sym, 'N')}")
    print(f"   Summary: {sentiment.get('summary', 'N/A')}")
    print("=" * 70)
    
    return sentiment


if __name__ == "__main__":
    main()
