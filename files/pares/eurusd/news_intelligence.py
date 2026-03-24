"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEWS INTELLIGENCE ENGINE - XAUUSD & EURUSD Market Sentiment                ║
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
        symbol = news_item.get('symbol', 'XAUUSD')
        title = news_item.get('title', '')
        
        prompt = f"""Eres un analista de trading forex/commodities. Evalúa esta noticia para {symbol}.

NOTICIA: "{title}"

Responde SOLO con una letra:
- B si es BULLISH (positivo para el precio, probable subida)
- M si es BEARISH (negativo para el precio, probable bajada)  
- N si es NEUTRAL (sin impacto claro)

Para {symbol}:
- XAUUSD (Oro): Inflación alta=B, Fed hawkish=M, Incertidumbre=B, Risk-off=B
- EURUSD: ECB hawkish=B, Fed hawkish=M, EU economía fuerte=B, Crisis Europa=M

Responde SOLO con B, M o N:"""

        response = self._call_ollama(prompt)
        
        if response:
            # Extraer solo la letra
            response = response.upper().strip()
            if 'B' in response[:5]:
                return 'B'
            elif 'M' in response[:5]:
                return 'M'
            else:
                return 'N'
        
        return 'N'  # Default neutral si falla
    
    def evaluate_batch(self, news_list: List[Dict]) -> List[Dict]:
        """Evalúa un lote de noticias"""
        for news in news_list:
            sentiment = self.evaluate_news(news)
            news['sentiment'] = sentiment
            logger.debug(f"[{news.get('symbol')}] {sentiment}: {news.get('title', '')[:50]}...")
            time.sleep(0.3)  # Rate limiting
        
        return news_list
    
    def get_overall_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        Calcula el sentimiento general del día.
        Considera el peso de cada noticia.
        
        Returns:
            {
                'XAUUSD': {'sentiment': 'B', 'score': 0.6, 'bullish': 3, 'bearish': 1, 'neutral': 1},
                'EURUSD': {'sentiment': 'M', 'score': -0.4, 'bullish': 1, 'bearish': 3, 'neutral': 2}
            }
        """
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
        """Genera hash único para una noticia (evitar duplicados)"""
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
        """
        Inserta o actualiza noticias (sin duplicados).
        Returns: número de noticias nuevas agregadas
        """
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
        """
        Retorna el sentimiento en formato optimizado para LLM.
        Formato minimalista: {'XAUUSD': 'B', 'EURUSD': 'M', 'summary': '...'}
        """
        data = self.load_today()
        sentiment = data.get('sentiment', {})
        
        if not sentiment:
            return {
                'XAUUSD': 'N',
                'EURUSD': 'N', 
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
        
        # Calculate per-symbol confidence from score (score is -1 to +1, confidence is 0 to 1)
        xau_score = abs(sentiment.get('XAUUSD', {}).get('score', 0))
        eur_score = abs(sentiment.get('EURUSD', {}).get('score', 0))
        xau_total = sentiment.get('XAUUSD', {}).get('total', 0)
        eur_total = sentiment.get('EURUSD', {}).get('total', 0)
        
        # Confidence = score magnitude * article count factor (more articles = more confidence)
        xau_conf = min(1.0, xau_score * (1 + min(xau_total, 10) * 0.1))  # Up to +100% boost from articles
        eur_conf = min(1.0, eur_score * (1 + min(eur_total, 10) * 0.1))
        
        return {
            'XAUUSD': sentiment.get('XAUUSD', {}).get('sentiment', 'N'),
            'EURUSD': sentiment.get('EURUSD', {}).get('sentiment', 'N'),
            'summary': ' | '.join(summaries),
            'confidence': max(xau_conf, eur_conf),  # Use max, not min - show strongest signal
            'confidence_xauusd': xau_conf,  # Per-symbol confidence
            'confidence_eurusd': eur_conf,
            'raw': sentiment
        }


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS INTELLIGENCE ENGINE - Orquestador principal
# ═══════════════════════════════════════════════════════════════════════════════

class NewsIntelligenceEngine:
    """
    Motor principal de inteligencia de noticias.
    Orquesta: Fetch → Evaluate → Store → Provide to LLM
    """
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.evaluator = OllamaNewsEvaluator()
        self.storage = NewsStorage()
        self.last_fetch_time = None
        self.fetch_interval = timedelta(minutes=90)  # Cada 1h 30min
    
    def should_fetch(self) -> bool:
        """Determina si debe buscar nuevas noticias"""
        if self.last_fetch_time is None:
            return True
        
        return datetime.now() - self.last_fetch_time > self.fetch_interval
    
    def fetch_and_evaluate(self) -> Dict:
        """
        Flujo completo:
        1. Busca noticias en DuckDuckGo
        2. Evalúa con Ollama (B/M/N)
        3. Guarda sin duplicados
        4. Calcula sentimiento general
        """
        logger.info("=" * 60)
        logger.info("📰 NEWS INTELLIGENCE - Starting fetch cycle...")
        logger.info("=" * 60)
        
        all_news = []
        
        # 1. Buscar noticias para cada símbolo
        for symbol in SYMBOLS:
            logger.info(f"🔍 Fetching news for {symbol}...")
            news = self.fetcher.fetch_news_for_symbol(symbol)
            all_news.extend(news)
        
        if not all_news:
            logger.warning("No news found!")
            return self.storage.get_sentiment_for_llm()
        
        # 2. Evaluar con Ollama
        logger.info(f"🤖 Evaluating {len(all_news)} news items with Ollama...")
        evaluated_news = self.evaluator.evaluate_batch(all_news)
        
        # 3. Guardar sin duplicados
        new_count = self.storage.upsert_news(evaluated_news)
        logger.info(f"💾 Saved {new_count} new news items (total today: {len(self.storage.load_today()['news'])})")
        
        # 4. Calcular sentimiento general
        all_stored = list(self.storage.load_today()['news'].values())
        overall_sentiment = self.evaluator.get_overall_sentiment(all_stored)
        self.storage.update_sentiment(overall_sentiment)
        
        # Log resultado
        for symbol, sent in overall_sentiment.items():
            emoji = '📈' if sent['sentiment'] == 'B' else ('📉' if sent['sentiment'] == 'M' else '➡️')
            logger.info(f"  {symbol}: {sent['sentiment']} {emoji} (score: {sent['score']}, B:{sent['bullish']}/M:{sent['bearish']}/N:{sent['neutral']})")
        
        self.last_fetch_time = datetime.now()
        
        return self.storage.get_sentiment_for_llm()
    
    def get_context_for_llm(self) -> Dict:
        """
        Obtiene el contexto de noticias para usar en decisiones LLM.
        Si no hay data reciente, busca nuevas.
        
        Returns formato optimizado:
        {
            'XAUUSD': 'B',           # B=Bullish, M=Bearish, N=Neutral
            'EURUSD': 'M',
            'summary': 'XAUUSD:B📈(score:0.4,n=5) | EURUSD:M📉(score:-0.3,n=4)',
            'confidence': 0.3,       # 0-1 qué tan seguro
            'should_consider': True  # Si vale la pena considerar en decisión
        }
        """
        # Verificar si necesita actualizar
        if self.should_fetch():
            logger.info("📰 News data stale, fetching fresh news...")
            return self.fetch_and_evaluate()
        
        # Retornar data existente
        sentiment = self.storage.get_sentiment_for_llm()
        
        # Agregar flag de si vale la pena considerar
        sentiment['should_consider'] = sentiment.get('confidence', 0) > 0.15
        
        return sentiment
    
    def get_trading_bias(self, symbol: str) -> Tuple[str, float]:
        """
        Retorna el sesgo de trading para un símbolo.
        
        Returns:
            (bias, confidence)
            bias: 'BULLISH', 'BEARISH', 'NEUTRAL'
            confidence: 0-1
        """
        sentiment = self.storage.get_sentiment_for_llm()
        s = sentiment.get(symbol, 'N')
        
        # Get per-symbol confidence (use symbol-specific if available)
        if symbol == 'XAUUSD':
            conf = sentiment.get('confidence_xauusd', sentiment.get('confidence', 0.5))
        elif symbol == 'EURUSD':
            conf = sentiment.get('confidence_eurusd', sentiment.get('confidence', 0.5))
        else:
            conf = sentiment.get('confidence', 0.5)
        
        # Ensure minimum confidence when we have a clear bias
        if s == 'B':
            return ('BULLISH', max(0.4, conf))  # At least 40% confidence if BULLISH
        elif s == 'M':
            return ('BEARISH', max(0.4, conf))  # At least 40% confidence if BEARISH
        else:
            return ('NEUTRAL', 0.2)


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE EXECUTION - Para ejecutar independientemente
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Ejecuta el motor de noticias standalone"""
    print("=" * 70)
    print("📰 NEWS INTELLIGENCE ENGINE - XAUUSD & EURUSD")
    print("   Powered by DuckDuckGo + Ollama | Polarice Labs 2026")
    print("=" * 70)
    
    engine = NewsIntelligenceEngine()
    
    # Primera búsqueda
    sentiment = engine.fetch_and_evaluate()
    
    print("\n" + "=" * 70)
    print("📊 TODAY'S MARKET SENTIMENT:")
    print("=" * 70)
    print(f"   XAUUSD: {sentiment.get('XAUUSD', 'N')}")
    print(f"   EURUSD: {sentiment.get('EURUSD', 'N')}")
    print(f"   Summary: {sentiment.get('summary', 'N/A')}")
    print("=" * 70)
    
    # Mostrar archivo guardado
    storage = NewsStorage()
    file_path = storage._get_today_file()
    print(f"\n💾 News saved to: {file_path}")
    
    return sentiment


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTION - Para usar desde otros módulos
# ═══════════════════════════════════════════════════════════════════════════════

# Instancia global para reusar
_news_engine = None

def get_news_sentiment() -> Dict:
    """
    Función helper para obtener sentimiento desde otros módulos.
    
    Usage:
        from news_intelligence import get_news_sentiment
        sentiment = get_news_sentiment()
        if sentiment['XAUUSD'] == 'B':
            # Bias bullish para oro
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
        bias, confidence = get_trading_bias('XAUUSD')
        # bias = 'BULLISH', 'BEARISH', or 'NEUTRAL'
    """
    global _news_engine
    
    if _news_engine is None:
        _news_engine = NewsIntelligenceEngine()
    
    return _news_engine.get_trading_bias(symbol)


if __name__ == "__main__":
    main()
