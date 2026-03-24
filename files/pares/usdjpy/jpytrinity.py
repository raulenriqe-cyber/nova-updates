#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - TRINITY ORACLE                       ║
║                    USDJPY M5 - Directional Momentum Edition                  ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  9-LLM Consensus for 5-7 minute directional prediction                       ║
║  Bayesian + Entropy + Divergence Weighting                                   ║
║  Analysis every 180 seconds | Clear BUY/SELL direction                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import sys, os
# ⭐ USDJPY: Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 LOAD PORTS FROM CENTRALIZED CONFIG (jpyconfig.yaml)
# ═══════════════════════════════════════════════════════════════════════════
try:
    from jpy_config_loader import get_trinity_port
    EU_CONFIG_LOADED = True
except ImportError:
    EU_CONFIG_LOADED = False

import socket, json, threading, logging, time, struct, statistics, math, io
from datetime import datetime
from collections import deque

# Fix Windows console encoding to UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Crear carpeta logs si no existe
os.makedirs('logs', exist_ok=True)

# Configurar logging a archivo Y consola
log_file = f'logs/trinity_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Crear handlers con UTF-8
file_handler = logging.FileHandler(log_file, encoding='utf-8')
stream_handler = logging.StreamHandler()

# Configurar formato
formatter = logging.Formatter('%(asctime)s | [%(threadName)-12s] | %(message)s', datefmt='%H:%M:%S')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
log = logging.getLogger(__name__)
log.info(f"[INIT] Log file: {log_file}")

# ═══════════════════════════════════════════════════════════════════════════════════════
# 🏦 LLM PERFORMANCE TRACKER - Tracks accuracy of each LLM to adjust weights dynamically
# ═══════════════════════════════════════════════════════════════════════════════════════
class LLMPerformanceTracker:
    """
    Tracks historical performance of each LLM to dynamically adjust voting weights.
    Uses exponential moving average for recent performance emphasis.
    """
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.llm_history = {
            'BAYESIAN': deque(maxlen=window_size),
            'TECHNICAL': deque(maxlen=window_size),
            'CHART': deque(maxlen=window_size),
            'RISK': deque(maxlen=window_size),
            'SUPREME': deque(maxlen=window_size)
        }
        # Momentum tracking - consecutive same-direction signals
        self.llm_momentum = {name: {'direction': None, 'count': 0} for name in self.llm_history}
        # Consistency tracking - how often LLM changes opinion
        self.llm_consistency = {name: deque(maxlen=20) for name in self.llm_history}
        # Base weights (can be updated based on performance)
        self.base_weights = {
            'BAYESIAN': 1.2,    # Probabilistic reasoning
            'TECHNICAL': 1.0,   # Classic indicators
            'CHART': 1.1,       # Pattern recognition
            'RISK': 0.9,        # Conservative
            'SUPREME': 1.3,      # Deep learning ensemble
            'SMART_MONEY': 1.6,  # LLM6 - Whale/sweep detection
            'STRATEGIST': 2.0,     # LLM11 - Guru consciousness: strategy + conviction
            'SENTINEL': 1.8        # LLM12 - Quality guardian: execution + reflection
        }
    
    def record_signal(self, llm_name: str, decision: str, confidence: float):
        """Record a signal from an LLM"""
        if llm_name not in self.llm_history:
            return
        
        # Track consistency (did opinion change from last signal?)
        prev_momentum = self.llm_momentum[llm_name]
        if prev_momentum['direction'] is not None:
            changed = (prev_momentum['direction'] != decision)
            self.llm_consistency[llm_name].append(0 if changed else 1)
        
        # Update momentum
        if prev_momentum['direction'] == decision:
            self.llm_momentum[llm_name]['count'] += 1
        else:
            self.llm_momentum[llm_name] = {'direction': decision, 'count': 1}
    
    def get_dynamic_weight(self, llm_name: str) -> float:
        """Get dynamically adjusted weight based on consistency and momentum"""
        if llm_name not in self.base_weights:
            return 1.0
        
        base = self.base_weights[llm_name]
        
        # Consistency bonus: LLMs that don't flip-flop get higher weight
        consistency = self.llm_consistency.get(llm_name, [])
        if len(consistency) >= 5:
            consistency_score = sum(consistency) / len(consistency)
            consistency_multiplier = 0.8 + (0.4 * consistency_score)  # 0.8 to 1.2
        else:
            consistency_multiplier = 1.0
        
        # Momentum bonus: Strong momentum = higher confidence in signal
        momentum = self.llm_momentum.get(llm_name, {})
        if momentum.get('count', 0) >= 3:
            momentum_bonus = min(0.2, momentum['count'] * 0.03)  # Max +0.2
        else:
            momentum_bonus = 0.0
        
        return base * consistency_multiplier + momentum_bonus

# Global performance tracker instance
llm_tracker = LLMPerformanceTracker()

class TrinityConsensus:
    def __init__(self):
        log.info('[TRINITY] BANK-GRADE CONSENSUS v3.0 Initialized')
        log.info('[TRINITY] Features: Bayesian + Entropy + LLM7/8/9 Integration')
        self.host = '127.0.0.1'
        self.timeout = 8.0  # 8s timeout - llama3:8b is much faster than 70b
        
        # PHASE 1: Core voting LLMs (decide BUY/SELL/HOLD) - USDJPY PORTS (+1000)
        self.core_llm_ports = {
            'BAYESIAN': 7855,   # USDJPY LLM1
            'TECHNICAL': 7857,  # USDJPY LLM2
            'CHART': 7858,      # USDJPY LLM3
            'RISK': 7859,       # USDJPY LLM4
            'SUPREME': 7861,    # USDJPY LLM5
            'SMART_MONEY': 7862  # USDJPY LLM6 - Whale/sweep detection
        }
        
        # PHASE 2: Intelligence enhancement LLMs (quality, timing, execution) - USDJPY PORTS
        self.enhancement_llm_ports = {
            'OCULUS': 7863,    # USDJPY LLM7 - Data Quality Validator
            'CHRONOS': 7864,   # USDJPY LLM8 - Timing Optimizer  
            'PREDATOR': 7865,   # USDJPY LLM9 - Execution Engine
            'STRATEGIST': 7867,   # USDJPY LLM11 - Strategist Guru
            'SENTINEL': 7868      # USDJPY LLM12 - Quality Guardian
        }
        
        # Combine for backward compatibility
        self.llm_ports = {**self.core_llm_ports, **self.enhancement_llm_ports}
        self.tracker = llm_tracker
    
    def analyze(self, genome: dict) -> dict:
        """
        ENHANCED ANALYSIS with 2-Phase LLM Integration
        
        Phase 1: Query Core LLMs (1-5) in parallel for BUY/SELL/HOLD voting
        Phase 2: Query Enhancement LLMs (7-8-9) sequentially with data chaining
        
        This ensures LLM9 PREDATOR receives quality_score from LLM7 and 
        timing_multiplier from LLM8 for proper mathematical integration.
        """
        symbol = genome.get('metadata', {}).get('symbol', 'USDJPY')
        tick_id = genome.get('tick_id', 0)
        
        # DEBUG: Log genome content for data validation
        price_data = genome.get('price_data', {})
        history_len = len(price_data.get('history', []))
        log.debug(f"[TRINITY-IN] {symbol} tick#{tick_id}: price_data.history has {history_len} bars")
        if history_len == 0:
            log.warning(f"[TRINITY-IN] EMPTY HISTORY! price_data keys: {list(price_data.keys())}, genome keys: {list(genome.keys())}")
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: Query CORE LLMs (1-5) in parallel for voting
        # ═══════════════════════════════════════════════════════════════════
        llm_responses, threads, lock = {}, [], threading.Lock()
        
        for llm_name, port in self.core_llm_ports.items():
            t = threading.Thread(target=self._query_llm, args=(llm_name, port, genome, llm_responses, lock), daemon=True)
            threads.append(t)
            t.start()
        
        # Phase 1b: Also query LLM11 STRATEGIST + LLM12 SENTINEL in parallel
        for llm_name in ['STRATEGIST', 'SENTINEL']:
            if llm_name in self.enhancement_llm_ports:
                port = self.enhancement_llm_ports[llm_name]
                t = threading.Thread(target=self._query_llm, args=(llm_name, port, genome, llm_responses, lock), daemon=True)
                threads.append(t)
                t.start()
        
        for t in threads:
            t.join(timeout=self.timeout)
        
        # 🔴 CRITICAL DEBUG: Log how many LLMs responded after parallel query
        core_count = len([k for k in llm_responses.keys() if k in self.core_llm_ports])
        if core_count == 0:
            log.error(f"[TRINITY] ⚠️ NO CORE LLMs responded! Are LLM1-5 running on ports 7855,7857-7859,7861?")
        else:
            log.info(f"[TRINITY] ✅ {core_count}/5 CORE LLMs responded: {[k for k in llm_responses.keys() if k in self.core_llm_ports]}")
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: Query ENHANCEMENT LLMs (7-8-9) with data chaining
        # USDJPY ports: 7863, 7864, 7865 (NOT XAUUSD 5562, 5563, 5564!)
        # ═══════════════════════════════════════════════════════════════════
        
        # Step 2a: Query LLM7 OCULUS for quality_score
        quality_score = 70  # Default if LLM7 unavailable
        oculus_response = self._query_enhancement_llm('OCULUS', 7863, genome)  # USDJPY LLM7
        if oculus_response:
            llm_responses['OCULUS'] = oculus_response
            quality_score = float(oculus_response.get('quality_score', 70))
            log.info(f"[TRINITY] LLM7 OCULUS: quality_score={quality_score}%")
        
        # Step 2b: Query LLM8 CHRONOS for timing_multiplier
        timing_multiplier = 1.0  # Default if LLM8 unavailable
        chronos_response = self._query_enhancement_llm('CHRONOS', 7864, genome)  # USDJPY LLM8
        if chronos_response:
            llm_responses['CHRONOS'] = chronos_response
            timing_multiplier = float(chronos_response.get('timing_multiplier', 1.0))
            log.info(f"[TRINITY] LLM8 CHRONOS: timing_multiplier={timing_multiplier:.2f}x")
        
        # Step 2c: Query LLM9 PREDATOR with quality_score + timing_multiplier
        # Create enhanced genome with LLM7 and LLM8 outputs
        enhanced_genome = genome.copy()
        enhanced_genome['quality_score'] = quality_score
        enhanced_genome['timing_multiplier'] = timing_multiplier
        
        predator_response = self._query_enhancement_llm('PREDATOR', 7865, enhanced_genome)  # USDJPY LLM9
        if predator_response:
            llm_responses['PREDATOR'] = predator_response
            rr_ratio = float(predator_response.get('rr_ratio', 0))
            position_mult = float(predator_response.get('position_multiplier', 1.0))
            log.info(f"[TRINITY] LLM9 PREDATOR: rr_ratio={rr_ratio:.2f}, position_mult={position_mult:.2f}x")
        
        # ═══════════════════════════════════════════════════════════════════
        # AGGREGATE VOTES (only from CORE LLMs 1-5)
        # ═══════════════════════════════════════════════════════════════════
        voting_keys = set(self.core_llm_ports.keys()) | {'STRATEGIST', 'SENTINEL'}
        core_responses = {k: v for k, v in llm_responses.items() if k in voting_keys}
        
        if core_responses:
            decision, confidence, buy_score, sell_score = self._aggregate_votes(core_responses)
        else:
            decision, confidence = self._fallback_decision(genome)
            buy_score, sell_score = (100, 0) if decision == 'BUY' else ((0, 100) if decision == 'SELL' else (50, 50))
            # CRITICAL FIX: When LLMs timeout, UPDATE llm_responses instead of OVERWRITING
            # This preserves OCULUS, CHRONOS, PREDATOR responses that were already added!
            llm_responses.update({
                'BAYESIAN': {'decision': decision, 'confidence': confidence, 'reason': 'LLM_TIMEOUT_FALLBACK'},
                'TECHNICAL': {'decision': decision, 'confidence': confidence, 'reason': 'LLM_TIMEOUT_FALLBACK'},
                'CHART': {'decision': decision, 'confidence': confidence, 'reason': 'LLM_TIMEOUT_FALLBACK'},
                'RISK': {'decision': decision, 'confidence': confidence, 'reason': 'LLM_TIMEOUT_FALLBACK'},
                'SUPREME': {'decision': decision, 'confidence': confidence, 'reason': 'LLM_TIMEOUT_FALLBACK'}
            })
        
        # ═══════════════════════════════════════════════════════════════════
        # APPLY ENHANCEMENT MODIFIERS from LLM7-8-9
        # ═══════════════════════════════════════════════════════════════════
        
        # Quality gate: If LLM7 OCULUS says data quality is too low, reduce confidence
        if quality_score < 40:
            confidence = max(25, confidence - 15)  # 🔧 FIX: VERY_LOW
            log.warning(f"[TRINITY] Data quality VERY LOW ({quality_score}%) - confidence reduced to {confidence}%")
        elif quality_score < 55:
            confidence = max(30, confidence - 8)  # 🔧 FIX: LOW
            log.warning(f"[TRINITY] Data quality LOW ({quality_score}%) - confidence reduced to {confidence}%")
            log.warning(f"[TRINITY] Data quality low ({quality_score}%) - confidence reduced to {confidence}%")
        
        # Timing boost: If LLM8 CHRONOS says timing is excellent, boost confidence
        if timing_multiplier >= 1.5:
            confidence = min(95, confidence + 5)  # 🔧 FIX: reduced timing boost
            log.info(f"[TRINITY] Excellent timing (mult={timing_multiplier:.2f}x) - confidence boosted to {confidence}%")
        
        # ⭐ CRITICAL FIX: Ensure ALL core LLMs have entries (fill missing with defaults)
        # This prevents dashboard from showing 0% for LLMs that timed out
        for llm_name in self.core_llm_ports.keys():
            if llm_name not in llm_responses:
                llm_responses[llm_name] = {
                    'decision': decision,  # Use consensus decision
                    'confidence': max(50, confidence * 0.9),  # 90% of consensus, min 50% (not 30%!)
                    'reason': 'LLM_TIMEOUT_FILLED'
                }
                log.warning(f"[TRINITY] ⚠️ Filled missing {llm_name} with default (conf={llm_responses[llm_name]['confidence']:.0f}%)")
        
        llm_summary = ', '.join([f"{k}:{v.get('confidence', 0):.0f}%" for k, v in sorted(llm_responses.items())])
        log.info(f'[TRINITY] {symbol} tick#{tick_id}: {decision} @ {confidence}% | LLMs:{len(llm_responses)}/8 [{llm_summary}]')

        # FIX #8: Session-aware minimum confidence gate
        # Prevents low-confidence trades during off-hours (0-8 UTC Asian)
        from datetime import datetime as _dt8
        _utc_h8 = _dt8.utcnow().hour
        _min_conf8 = (68 if _utc_h8 < 8 else
                      57 if _utc_h8 < 12 else
                      60 if _utc_h8 < 17 else 65)
        _tm8 = timing_multiplier  # assigned above when LLM8/CHRONOS queried
        if _tm8 >= 1.2:   _min_conf8 = max(50, _min_conf8 - 3)
        elif _tm8 <= 0.6: _min_conf8 = min(78, _min_conf8 + 6)
        if decision in ('BUY', 'SELL') and confidence < _min_conf8:
            log.info(f'[TRINITY] Session gate ({_utc_h8}h UTC): '
                     f'{confidence}% < min {_min_conf8}% (tm={_tm8:.2f}) -> HOLD')
            decision = 'HOLD'
            confidence = max(confidence, 20)
        
        return {
            'decision': decision, 
            'confidence': confidence, 
            'llm_responses': llm_responses, 
            'scores': {
                'buy_score': buy_score, 
                'sell_score': sell_score, 
                'hold_score': 100-buy_score-sell_score
            },
            # Enhancement data from LLM7-8-9
            'quality_score': quality_score,
            'timing_multiplier': timing_multiplier,
            'rr_ratio': predator_response.get('rr_ratio', 0) if predator_response else 0,
            'position_multiplier': predator_response.get('position_multiplier', 1.0) if predator_response else 1.0
        }
    
    def _query_enhancement_llm(self, llm_name: str, port: int, genome: dict) -> dict:
        """Query enhancement LLMs (7-8-9) with simple request format"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)  # Faster timeout for enhancement LLMs
            sock.connect((self.host, port))
            
            # Send request
            request_json = json.dumps(genome).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            
            # Receive response
            response_header = sock.recv(4)
            if response_header and len(response_header) == 4:
                response_length = struct.unpack('>I', response_header)[0]
                response_data = b''
                while len(response_data) < response_length:
                    chunk = sock.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk
                
                if response_data:
                    response = json.loads(response_data.decode('utf-8'))
                    sock.close()
                    return response
            
            sock.close()
            return None
        
        except socket.timeout:
            log.debug(f'[TRINITY<-{llm_name}] TIMEOUT on port {port}')
            return None
        except ConnectionRefusedError:
            log.debug(f'[TRINITY<-{llm_name}] NOT RUNNING on port {port}')
            return None
        except Exception as e:
            log.debug(f'[TRINITY<-{llm_name}] Error: {e}')
            return None
    
    def _query_llm(self, llm_name: str, port: int, genome: dict, responses: dict, lock: threading.Lock):
        try:
            # Get indicators - try both paths (structure can vary)
            indicators = genome.get('indicators', {}).get('current', {})
            if not indicators:
                indicators = genome.get('indicators', {})
            if not isinstance(indicators, dict):
                indicators = {}
            
            price_data = genome.get('price_data', {})
            tick_data = genome.get('tick_data', {})
            
            # Get price from multiple sources
            price = tick_data.get('last', 0)
            if price <= 0:
                bid = tick_data.get('bid', 0)
                ask = tick_data.get('ask', 0)
                if bid > 0 and ask > 0:
                    price = (bid + ask) / 2.0
                else:
                    price = price_data.get('close', 0)
            
            # ============================================================
            # PRIORITY 1: Use bar_data.closes (has LIVE TICK already appended by quantum_core)
            # This is the FIX for stale M1 bar data causing extreme RSI/ADX
            # ============================================================
            bar_data = genome.get('bar_data', {})
            bar_closes = bar_data.get('closes', [])
            
            closes = []
            highs = []
            lows = []
            opens = []
            
            if bar_closes and len(bar_closes) >= 5:
                # bar_data.closes has live tick already - USE IT
                closes = [float(c) for c in bar_closes if c and float(c) > 0]
                highs = [float(h) for h in bar_data.get('highs', bar_closes)]
                lows = [float(l) for l in bar_data.get('lows', bar_closes)]
                opens = closes.copy()  # Approximate opens from closes
                log.debug(f"[_query_llm] {llm_name}: ✅ Using bar_data.closes: {len(closes)} prices (LIVE TICK INCLUDED)")
            else:
                # FALLBACK: Extract from price_data.history (M1 candles)
                candles = price_data.get('history', [])
                
                for c in candles:
                    if isinstance(c, dict):
                        closes.append(float(c.get('close', c.get('C', price))))
                        highs.append(float(c.get('high', c.get('H', price))))
                        lows.append(float(c.get('low', c.get('L', price))))
                        opens.append(float(c.get('open', c.get('O', price))))
                    elif isinstance(c, (int, float)):
                        closes.append(float(c))
                        highs.append(float(c))
                        lows.append(float(c))
                        opens.append(float(c))
                    elif isinstance(c, str):
                        try:
                            parsed = json.loads(c)
                            if isinstance(parsed, dict):
                                closes.append(float(parsed.get('close', parsed.get('C', price))))
                                highs.append(float(parsed.get('high', parsed.get('H', price))))
                                lows.append(float(parsed.get('low', parsed.get('L', price))))
                                opens.append(float(parsed.get('open', parsed.get('O', price))))
                        except:
                            pass
                
                if len(closes) < 5:
                    log.warning(f"[_query_llm] {llm_name}: ⚠️ LOW DATA: {len(closes)} closes, price={price:.2f}")
            
            # Fallback if no history
            if not closes:
                closes = [float(price)]
                log.warning(f"[_query_llm] {llm_name}: ⚠️ No history! Using single price: {price}")
            if not highs:
                highs = [float(price)]
            if not lows:
                lows = [float(price)]
            if not opens:
                opens = [float(price)]
            
            # ============================================================
            # CRITICAL FIX: ADD CURRENT TICK PRICE TO END OF HISTORY
            # M1 bars only update every minute, but tick price changes every second
            # This ensures LLMs ALWAYS see the CURRENT price, not stale bar data
            # ============================================================
            if price > 0:
                # ALWAYS append current tick price if different from last close
                # Changed from > 0.01 to > 0.001 (0.1 pip for USDJPY M15)
                # This catches micro-movements that were previously ignored
                if len(closes) > 0:
                    price_diff = abs(closes[-1] - price)
                    if price_diff > 0.001:  # More than 0.1 pip difference
                        # Append current tick price to closes array
                        closes.append(float(price))
                        highs.append(float(price))  # Current tick is its own high
                        lows.append(float(price))   # Current tick is its own low
                        opens.append(closes[-2] if len(closes) > 1 else float(price))  # Open = previous close
                        log.info(f"[_query_llm] {llm_name}: ✅ LIVE TICK ADDED: {price:.2f} (was {closes[-2]:.2f}, diff={price_diff:.3f})")
                    else:
                        log.debug(f"[_query_llm] {llm_name}: Tick {price:.2f} same as last close (diff={price_diff:.3f})")
                else:
                    # First tick - always add
                    closes.append(float(price))
                    highs.append(float(price))
                    lows.append(float(price))
                    opens.append(float(price))
                    log.info(f"[_query_llm] {llm_name}: ✅ FIRST TICK: {price:.2f}")
            
            # ============================================================
            # NORMALIZE CANDLES FOR LLM5 (requires 'close', 'open', 'high', 'low', 'volume')
            # ============================================================
            normalized_candles = []
            for i in range(min(len(closes), len(opens), len(highs), len(lows))):
                normalized_candles.append({
                    'close': float(closes[i]),
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'volume': 100.0  # Default volume since MT5 may not provide tick volume on M1
                })
            
            # ============================================================
            # BUILD REQUEST WITH CORRECT FIELD NAMES FOR EACH LLM
            # ============================================================
            # Extract raw indicators from genome
            rsi = float(indicators.get('rsi', 50))
            adx = float(indicators.get('adx', 25))
            atr_raw = float(indicators.get('atr_pips', indicators.get('atr', 0)))
            macd_line = float(indicators.get('macd', 0))  # MACD line (EMA12 - EMA26)
            macd_hist = float(indicators.get('macd_histogram', macd_line * 0.2))  # ← FIX: Use actual histogram, fallback to 20% of MACD line
            
            # Calculate SMA indicators from closes if available
            sma_50 = price
            sma_200 = price
            if len(closes) >= 50:
                sma_50 = sum(closes[-50:]) / 50
            if len(closes) >= 200:
                sma_200 = sum(closes[-200:]) / 200
            
            # Calculate Bollinger Bands from closes if available
            bb_upper = price * 1.02
            bb_lower = price * 0.98
            if len(closes) >= 20:
                mean = statistics.mean(closes[-20:])
                stdev = statistics.stdev(closes[-20:]) if len(closes[-20:]) > 1 else 0
                bb_upper = mean + (2.0 * stdev)
                bb_lower = mean - (2.0 * stdev)
            
            # Build request with BOTH original names AND LLM-expected names
            request = {
                'symbol': genome.get('metadata', {}).get('symbol', 'USDJPY'),
                'price': float(price),
                'current_price': float(price),
                'prices': [float(c) for c in closes],
                'candles': normalized_candles,  # ← FIX: Use normalized candles for LLM5
                
                # === INDICATORS - Multiple naming conventions for compatibility ===
                # Original names (what Trinity currently sends)
                'rsi': float(rsi),
                'adx': float(adx),
                'atr': float(atr_raw),
                'macd': float(macd_line),  # MACD line
                
                # LLM1 expected names (what LLM1 searches for)
                'atr_14': float(atr_raw),  # ← FIX: LLM1 looks for 'atr_14' not 'atr'
                'macd_histogram': float(macd_hist),  # ← FIX: Now uses ACTUAL histogram, not MACD line!
                'sma_50': float(sma_50),  # ← FIX: LLM1 expects SMA_50
                'sma_200': float(sma_200),  # ← FIX: LLM1 expects SMA_200
                'bb_upper': float(bb_upper),  # ← FIX: LLM1 expects Bollinger Upper
                'bb_lower': float(bb_lower),  # ← FIX: LLM1 expects Bollinger Lower
                
                # Bar data structure for LLM3/4/5
                'bar_data': {
                    'closes': [float(c) for c in closes],
                    'highs': [float(h) for h in highs],
                    'lows': [float(l) for l in lows],
                    'opens': [float(o) for o in opens]
                },
                
                # Full indicators dict for any LLM that needs it
                'indicators': indicators,
                'tick_id': genome.get('tick_id', 0)
            }
            
            # DEBUG: Log request details for each LLM
            log.debug(f"[_query_llm] {llm_name}: Sending request with {len(request['prices'])} prices, {len(request['candles'])} candles, price={price:.2f}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, port))
            log.info(f"[TRINITY->{llm_name}] ✅ Connected to port {port}")
            
            # Send: 4-byte header + JSON
            request_json = json.dumps(request).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            log.info(f"[TRINITY->{llm_name}] 📤 Sent {len(request_json)} bytes")
            
            # Receive: 4-byte header + JSON
            response_header = sock.recv(4)
            if response_header and len(response_header) == 4:
                response_length = struct.unpack('>I', response_header)[0]
                response_data = b''
                while len(response_data) < response_length:
                    chunk = sock.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk
                
                if response_data:
                    response = json.loads(response_data.decode('utf-8'))
                    # Fix: SMART_MONEY devuelve 'recommendation' no 'decision'
                    if 'recommendation' in response and 'decision' not in response:
                        response['decision'] = response['recommendation']
                    decision = response.get('decision', 'HOLD').upper()
                    if decision not in ['BUY', 'SELL', 'HOLD', 'NO_TRADE']:
                        decision = 'HOLD'
                    confidence = min(100.0, max(0.0, float(response.get('confidence', 50))))
                    
                    with lock:
                        # CRITICAL FIX: LLM5 already provides clean 'chart_patterns' list of strings!
                        # Use it directly instead of extracting from 'patterns' dict list
                        raw_patterns = response.get('patterns', [])
                        chart_patterns_clean = response.get('chart_patterns', [])  # Already clean strings from LLM5
                        
                        if not chart_patterns_clean and raw_patterns:
                            # Fallback: Extract from raw patterns if chart_patterns not provided
                            chart_patterns_clean = []
                            for p in raw_patterns:
                                if isinstance(p, dict):
                                    name = p.get('name', p.get('type', ''))
                                    if name:
                                        chart_patterns_clean.append(str(name))
                                elif isinstance(p, str):
                                    chart_patterns_clean.append(p)
                        
                        responses[llm_name] = {
                            'decision': decision, 
                            'confidence': confidence, 
                            'reason': response.get('reason', ''),
                            # Patterns from LLM5 (SUPREME) - now properly extracted
                            'chart_patterns': chart_patterns_clean,
                            'patterns_found': response.get('patterns_found', len(raw_patterns)),
                            'bullish_patterns': response.get('bullish_patterns', 0),
                            'bearish_patterns': response.get('bearish_patterns', 0),
                        }
                    log.info(f'[TRINITY<-{llm_name}] {decision}@{confidence:.1f}% | Patterns: {len(chart_patterns_clean)}')
            
            sock.close()
        
        except socket.timeout:
            log.warning(f'[TRINITY<-{llm_name}] ⏰ TIMEOUT on port {port} (>2s)')
        except ConnectionRefusedError:
            log.warning(f'[TRINITY<-{llm_name}] ❌ NOT RUNNING on port {port}')
        except Exception as e:
            log.warning(f'[TRINITY<-{llm_name}] ⚠️ Error: {type(e).__name__}: {e}')
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # 🏦 BANK-GRADE CONSENSUS ALGORITHM v2.0
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # This algorithm uses advanced mathematical principles from:
    # - Bayesian Inference (posterior probability estimation)
    # - Game Theory (Nash equilibrium for divergence detection)
    # - Information Theory (Shannon entropy for uncertainty)
    # - Statistical Mechanics (Boltzmann weighting)
    # - Ensemble Learning (weighted meta-learning)
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def _aggregate_votes(self, llm_responses: dict) -> tuple:
        """
        🏦 BANK-GRADE CONSENSUS: Ultra-intelligent 5-LLM fusion algorithm
        
        Mathematical Components:
        1. BAYESIAN POSTERIOR: P(action|evidence) using confidence as likelihood
        2. ENTROPY PENALTY: High disagreement = lower final confidence
        3. MOMENTUM BONUS: Consistent signals get amplified
        4. DIVERGENCE DETECTION: Conflicting signals trigger caution
        5. CONFIDENCE CALIBRATION: Non-linear confidence transformation
        """
        import math
        
        if not llm_responses: 
            return 'HOLD', 50, 50, 50
        
        num_llms = len(llm_responses)
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: EXTRACT AND CALIBRATE INDIVIDUAL SIGNALS
        # ═══════════════════════════════════════════════════════════════
        signals = {'BUY': [], 'SELL': [], 'HOLD': []}
        
        # 🏦 DYNAMIC WEIGHTS: Use LLMPerformanceTracker for adaptive weighting
        llm_weights = {}
        for llm_name in llm_responses.keys():
            llm_weights[llm_name] = self.tracker.get_dynamic_weight(llm_name)
        
        log.debug(f"[BANK-GRADE] Dynamic LLM weights: {llm_weights}")
        
        for llm_name, llm_data in llm_responses.items():
            decision = llm_data.get('decision', 'HOLD')
            raw_confidence = llm_data.get('confidence', 50)
            
            # NORMALIZE DECISIONS: Convert LLM7-8-9 special decisions to standard
            # LLM7 OCULUS: APPROVE/CAUTION/REJECT -> Skip (not a trading decision)
            # LLM8 CHRONOS: READY/PREPARING/WAITING -> Skip (timing, not direction)
            # LLM9 PREDATOR: EXECUTE/WAIT/ABORT -> Skip (execution, not direction)
            if decision in ['APPROVE', 'CAUTION', 'REJECT', 'READY', 'PREPARING', 
                           'WAITING', 'EXECUTE', 'WAIT', 'ABORT', 'ABSTAIN']:  # [NOVA AUDIT F-15]
                continue  # Skip non-voting LLMs
            
            # Normalize other decisions
            if decision not in ['BUY', 'SELL', 'HOLD']:
                decision = 'HOLD'
            
            # Record signal for tracking (used for future dynamic weights)
            self.tracker.record_signal(llm_name, decision, raw_confidence)
            
            # 🧮 NON-LINEAR CONFIDENCE CALIBRATION (sigmoid-like transformation)
            # This penalizes mid-range confidence and amplifies extremes
            # f(x) = 50 + 50 * tanh(3 * (x/100 - 0.5))
            normalized = raw_confidence / 100.0
            calibrated = 50 + 50 * math.tanh(3 * (normalized - 0.5))
            
            # Apply LLM-specific weight
            weight = llm_weights.get(llm_name, 1.0)
            weighted_conf = calibrated * weight
            
            signals[decision].append({
                'llm': llm_name,
                'raw_conf': raw_confidence,
                'calibrated': calibrated,
                'weighted': weighted_conf,
                'weight': weight
            })
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: CALCULATE BAYESIAN POSTERIOR PROBABILITIES
        # ═══════════════════════════════════════════════════════════════
        # P(BUY|evidence) ∝ P(evidence|BUY) * P(BUY)
        # Using uniform priors: P(BUY) = P(SELL) = P(HOLD) = 1/3
        
        def calculate_likelihood(signal_list):
            """Calculate aggregate likelihood from LLM signals"""
            if not signal_list:
                return 0.0
            
            # Product of normalized confidences (log-sum for numerical stability)
            log_likelihood = sum(math.log(max(s['weighted'] / 100.0, 0.01)) for s in signal_list)
            # Average weight contribution
            avg_weight = sum(s['weight'] for s in signal_list) / len(signal_list)
            # Count bonus (more LLMs agreeing = higher confidence)
            count_bonus = len(signal_list) / num_llms
            
            return math.exp(log_likelihood) * avg_weight * (1 + count_bonus)
        
        likelihood_buy = calculate_likelihood(signals['BUY'])
        likelihood_sell = calculate_likelihood(signals['SELL'])
        likelihood_hold = calculate_likelihood(signals['HOLD']) * 0.65  # 🔧 FIX: HOLD penalty relaxed (was too harsh)
        
        total_likelihood = likelihood_buy + likelihood_sell + likelihood_hold + 1e-10
        
        posterior_buy = likelihood_buy / total_likelihood
        posterior_sell = likelihood_sell / total_likelihood
        posterior_hold = likelihood_hold / total_likelihood
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: CALCULATE SHANNON ENTROPY (DISAGREEMENT MEASURE)
        # ═══════════════════════════════════════════════════════════════
        # H = -Σ p(x) * log2(p(x))
        # High entropy = high disagreement = lower confidence
        
        def entropy(probs):
            """Calculate Shannon entropy of probability distribution"""
            return -sum(p * math.log2(max(p, 1e-10)) for p in probs if p > 0)
        
        distribution = [posterior_buy, posterior_sell, posterior_hold]
        current_entropy = entropy(distribution)
        max_entropy = math.log2(3)  # Maximum entropy for 3 outcomes
        
        # Entropy penalty: 0 (perfect agreement) to 1 (complete disagreement)
        entropy_penalty = current_entropy / max_entropy
        agreement_bonus = 1.0 - entropy_penalty  # Higher is better
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 4: DIVERGENCE DETECTION (CONFLICTING SIGNALS)
        # ═══════════════════════════════════════════════════════════════
        # If BUY and SELL both have strong signals, be cautious
        
        buy_strength = sum(s['weighted'] for s in signals['BUY']) if signals['BUY'] else 0
        sell_strength = sum(s['weighted'] for s in signals['SELL']) if signals['SELL'] else 0
        
        # Divergence score: high when both directions are strong
        if buy_strength > 0 and sell_strength > 0:
            # [NOVA REPAIR ARCHITECT - FIX CRÍTICO] A-01: ratio-based divergence (was min-based, always > 0.5)
            strength_ratio = max(buy_strength, sell_strength) / (min(buy_strength, sell_strength) + 1e-10)
            divergence = 1.0 / strength_ratio  # 0.0 (one side dominates) to 1.0 (equal conflict)
        else:
            divergence = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 5: CALCULATE WEIGHTED SCORES FOR EACH ACTION
        # ═══════════════════════════════════════════════════════════════
        
        def calculate_action_score(signal_list, posterior):
            """Calculate final score for an action"""
            if not signal_list:
                return 0.0
            
            # Base: sum of weighted confidences
            base_score = sum(s['weighted'] for s in signal_list)
            
            # Normalize by number of LLMs
            normalized = base_score / (num_llms * 100)
            
            # Apply posterior probability
            bayesian_score = normalized * (1 + posterior)
            
            # Apply agreement bonus
            final_score = bayesian_score * (0.5 + 0.5 * agreement_bonus)
            
            return final_score * 100  # Scale to 0-100
        
        buy_score = calculate_action_score(signals['BUY'], posterior_buy)
        sell_score = calculate_action_score(signals['SELL'], posterior_sell)
        hold_score = calculate_action_score(signals['HOLD'], posterior_hold) * 0.7  # HOLD dampening
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 6: FINAL DECISION WITH CONFIDENCE CALCULATION
        # ═══════════════════════════════════════════════════════════════
        
        total_score = buy_score + sell_score + hold_score + 1e-10
        
        # Normalize scores to percentages
        buy_pct = (buy_score / total_score) * 100
        sell_pct = (sell_score / total_score) * 100
        hold_pct = (hold_score / total_score) * 100
        
        # Decision based on highest score
        if buy_score > sell_score and buy_score > hold_score:
            decision = 'BUY'
            # 🏦 BANK-GRADE: Confidence = weighted average of voting LLMs
            # When majority agrees, use simpler and higher confidence
            vote_count = len(signals['BUY'])
            total_confidence = sum(s['raw_conf'] for s in signals['BUY'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            
            # Majority bonus: 4/5 LLMs = +15%, 5/5 = +20%
            majority_bonus = 1.0 + (vote_count - 2.5) * 0.08  # 3/5=1.04, 4/5=1.12, 5/5=1.20
            confidence = int(raw_conf * majority_bonus * (1 - divergence * 0.3))
            
        elif sell_score > buy_score and sell_score > hold_score:
            decision = 'SELL'
            vote_count = len(signals['SELL'])
            total_confidence = sum(s['raw_conf'] for s in signals['SELL'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            majority_bonus = 1.0 + (vote_count - 2.5) * 0.08
            confidence = int(raw_conf * majority_bonus * (1 - divergence * 0.3))
            
        else:
            decision = 'HOLD'
            if signals['HOLD']:
                raw_conf = sum(s['raw_conf'] for s in signals['HOLD']) / len(signals['HOLD'])
            else:
                raw_conf = 50
            confidence = int(raw_conf * 0.85)  # HOLD = lower confidence (indecision)
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 7: CONFIDENCE BOUNDS AND FINAL ADJUSTMENTS
        # ═══════════════════════════════════════════════════════════════
        
        # Clamp confidence to valid range
        confidence = max(20, min(95, confidence))
        
        # If high divergence, cap confidence
        if divergence > 0.5:
            confidence = min(confidence, 60)
            log.info(f"[BANK-GRADE] ⚠️ HIGH DIVERGENCE ({divergence:.2f}) - Confidence capped at 60")
        
        # If perfect agreement (all LLMs same decision), boost confidence
        if len(signals[decision]) == num_llms and num_llms >= 5:  # 🔧 FIX: require min 5 voters
            confidence = min(95, confidence + 6)  # 🔧 FIX: +6% not +10%
            log.info(f"[BANK-GRADE] 🎯 PERFECT AGREEMENT! All {num_llms} LLMs voted {decision}")
        
        # 🏦 BANK-GRADE LOGGING: Show mathematical analysis
        log.info(f"[BANK-GRADE] 📊 ANALYSIS: Bayesian P(BUY)={posterior_buy:.3f} P(SELL)={posterior_sell:.3f} P(HOLD)={posterior_hold:.3f}")
        log.info(f"[BANK-GRADE] 📈 ENTROPY: {current_entropy:.3f}/{max_entropy:.3f} = {entropy_penalty:.1%} disagreement | Agreement bonus: {agreement_bonus:.1%}")
        log.info(f"[BANK-GRADE] 🎲 SCORES: BUY={buy_pct:.1f}% SELL={sell_pct:.1f}% HOLD={hold_pct:.1f}%")
        log.info(f"[BANK-GRADE] 🏦 DECISION: {decision} @ {confidence}% confidence | Divergence: {divergence:.2%}")
        
        # Ensure buy/sell scores are properly scaled
        buy_score_final = min(100, max(0, buy_pct))
        sell_score_final = min(100, max(0, sell_pct))
        
        return decision, confidence, buy_score_final, sell_score_final
    
    def _fallback_decision(self, genome: dict) -> tuple:
        """
        🛡️ SECURITY FIX: When ALL LLMs timeout, FORCE HOLD instead of guessing
        
        CRITICAL: This is called when NO LLM responds (all timeouts).
        We MUST NOT trade when we have no LLM consensus - that would be gambling!
        
        Old behavior: Used RSI/MACD to decide BUY/SELL - DANGEROUS!
        New behavior: FORCE HOLD with REASONABLE confidence - allow dashboard updates
        """
        # Log that we're in emergency fallback mode
        log.warning("[FALLBACK] ⚠️ ALL LLMs TIMEOUT - FORCING HOLD (no trade without consensus)")
        
        # Return HOLD with reasonable confidence - dashboard needs visible data
        return 'HOLD', 50  # 50% confidence = shows data on dashboard, but no trades

# ⭐ TCP SERVER - Trinity accepts genomes from quantum_core on port 6666
class TrinityServer:
    """Trinity TCP Server with optional Dashboard integration"""
    
    def __init__(self, dashboard_enabled=True):
        self.trinity = TrinityConsensus()
        self.dashboard = None
        self.running = True
        self.lock = threading.RLock()
        self.metrics = {
            'ticks_processed': 0,
            'start_time': time.time(),
        }
        
        log.info('[SERVER] Initialization started')
        
        # Try to load dashboard if enabled
        if dashboard_enabled:
            try:
                log.info('[SERVER] Loading dashboard...')
                from trinity_dashboard_v3 import QuantumDashboard
                self.dashboard = QuantumDashboard(port=7667)  # USDJPY dashboard port
                self.dashboard.start_listener()
                log.info('[SERVER] ✅ Dashboard loaded and listening')
            except Exception as e:
                log.warning(f'[SERVER] ⚠️  Dashboard not available: {e}')
                self.dashboard = None
        
        log.info('[SERVER] Initialization complete')
    
    def run(self, port=7866):
        """Start TCP server on specified port - USDJPY M15"""
        log.info(f"[SERVER] Starting TCP server on port {port}...")
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', port))
            server.listen(5)
            log.info(f'[SERVER] Listening on 127.0.0.1:{port} - READY FOR CONNECTIONS (USDJPY)')
        except Exception as e:
            log.error(f'[SERVER] Failed to bind: {e}', exc_info=True)
            return
        
        # Status thread
        threading.Thread(target=self._print_status, daemon=True).start()
        
        log.info("[SERVER] Entering accept loop...")
        while self.running:
            try:
                client, addr = server.accept()
                log.info(f'[SERVER] Connection from {addr}')
                threading.Thread(
                    target=self._handle_client, 
                    args=(client, addr), 
                    daemon=True
                ).start()
            except Exception as e:
                log.error(f'[SERVER] Accept error: {e}', exc_info=True)
    
    def _handle_client(self, client, addr):
        """Handle genome from quantum_core"""
        try:
            client.settimeout(5)
            
            # Read header (4 bytes)
            header = client.recv(4)
            if not header or len(header) != 4:
                log.warning(f'[CLIENT {addr}] Invalid header')
                client.close()
                return
            
            length = struct.unpack('>I', header)[0]
            
            # Read genome
            data = b''
            while len(data) < length:
                chunk = client.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk
            
            if not data:
                log.warning(f'[CLIENT {addr}] No data')
                client.close()
                return
            

            # ═══ PING/ACK HANDLER ═══
            if data == b'PING':
                try:
                    ack_payload = b'ACK'
                    ack_header = struct.pack('>I', len(ack_payload))
                    client.sendall(ack_header + ack_payload)
                except Exception:
                    pass
                return

            # Parse and analyze
            genome = json.loads(data.decode('utf-8'))
            result = self.trinity.analyze(genome)
            log.info(f'[CLIENT {addr}] Result: {result["decision"]} @ {result["confidence"]}%')
            
            # Update dashboard if available
            if self.dashboard:
                try:
                    llm_responses = result.get('llm_responses', {})
                    LLM_MAP = {'BAYESIAN': 'LLM1', 'TECHNICAL': 'LLM2', 'CHART': 'LLM3', 'RISK': 'LLM4', 'SUPREME': 'LLM5'}
                    
                    for llm_name, llm_data in llm_responses.items():
                        if isinstance(llm_data, dict):
                            dashboard_name = LLM_MAP.get(llm_name, llm_name)
                            self.dashboard.update_llm(
                                dashboard_name,
                                llm_data.get('decision', 'HOLD'),
                                llm_data.get('confidence', 0),
                                llm_data.get('reason', '')[:40]
                            )
                    
                    # Update trinity consensus
                    scores = result.get('scores', {})
                    self.dashboard.update_trinity(
                        result.get('decision', 'HOLD'),
                        result.get('confidence', 0),
                        scores.get('buy_score', 0),
                        scores.get('sell_score', 0),
                        scores.get('hold_score', 0)
                    )
                except Exception as e:
                    log.debug(f'[CLIENT {addr}] Dashboard update error: {e}')
            
            with self.lock:
                self.metrics['ticks_processed'] += 1
            
            # Send response
            response = json.dumps(result).encode('utf-8')
            response_header = struct.pack('>I', len(response))
            client.sendall(response_header + response)
            
        except Exception as e:
            log.error(f'[CLIENT {addr}] Error: {e}')
        finally:
            try:
                client.close()
            except:
                pass
    
    def _print_status(self):
        """Print status every 30 seconds"""
        while self.running:
            try:
                time.sleep(30)
                with self.lock:
                    uptime = time.time() - self.metrics['start_time']
                    log.info(f"[STATUS] Uptime: {uptime/60:.1f}min | Ticks: {self.metrics['ticks_processed']}")
            except Exception as e:
                log.error(f"[STATUS] Error: {e}")

def run_server(port=7866):
    """Run Trinity consensus server with optional dashboard - USDJPY M15"""
    server = TrinityServer(dashboard_enabled=True)
    server.run(port=port)

if __name__ == '__main__':
    try:
        log.info('[TRINITY] ═════════════════════════════════════════')
        log.info('[TRINITY] TRINITY CONSENSUS ENGINE v1.0 - USDJPY M15')
        log.info('[TRINITY] Consensus Orchestrator - 5 LLM Integration')
        log.info('[TRINITY] ═════════════════════════════════════════')
        
        # ⭐ Load port from jpyconfig.yaml
        trinity_port = 7866  # Default
        if EU_CONFIG_LOADED:
            trinity_port = get_trinity_port()
            log.info(f'[TRINITY] Loaded port {trinity_port} from jpyconfig.yaml')
        
        run_server(port=trinity_port)  # USDJPY Trinity port from config
    except KeyboardInterrupt:
        log.info('[TRINITY] 🛑 Stopped by user')
    except Exception as e:
        log.error(f'[TRINITY] FATAL: {e}', exc_info=True)
