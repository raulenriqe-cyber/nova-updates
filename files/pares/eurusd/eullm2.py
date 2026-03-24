#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - LLM2 TECHNICAL EXPERT                ║
║                    EURUSD M15 - Sniper Predator Edition                      ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Monte Carlo Probability + Fibonacci Detection + Technical Consensus         ║
║  Port: 6557 (TCP Server) - EURUSD M15                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import sys, os
# ⭐ EURUSD: Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 LOAD PORTS FROM CENTRALIZED CONFIG (euconfig.yaml)
# ═══════════════════════════════════════════════════════════════════════════
try:
    from eu_config_loader import get_llm_port
    EU_CONFIG_LOADED = True
except ImportError:
    EU_CONFIG_LOADED = False

import json, socket, struct, logging, threading, time, numpy as np, yaml
from collections import deque
from datetime import datetime

# ===== PATTERN DETECTION =====
try:
    from pattern_library import get_pattern_detector
    PATTERN_DETECTOR = get_pattern_detector()
    PATTERN_ENABLED = True
except ImportError:
    PATTERN_DETECTOR = None
    PATTERN_ENABLED = False

# ============================================================
# LOGGING SETUP
# ============================================================
os.makedirs('logs', exist_ok=True)
_log_file = f'logs/llm2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
_file_handler = logging.FileHandler(_log_file, encoding='utf-8')
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter('%(asctime)s | LLM2 v17.03 | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger('LLM2')
log.info(f"[INIT] Log file: {_log_file}")
# ============================================================
# DIAGNOSTIC TRACER
# ============================================================
try:
    from LLM_DECISION_TRACER import get_tracer
    from REALTIME_DECISION_DASHBOARD import get_dashboard
    TRACER = get_tracer()
    DASHBOARD = get_dashboard()
    DIAGNOSTICS_ENABLED = True
except ImportError:
    TRACER = None
    DASHBOARD = None
    DIAGNOSTICS_ENABLED = False


# ============================================================
# TECHNICAL ANALYSIS ENGINE - LLM2 SPECIALIZES IN STRUCTURE
# ============================================================
class FibonacciAnalyzer:
    """Detecta niveles Fibonacci y proyecciones"""
    
    @staticmethod
    def calculate_levels(low, high):
        """Calcula 7 niveles Fibonacci"""
        diff = high - low
        if diff <= 0:
            return {'error': 'Invalid range'}
        
        return {
            '0.0': low,
            '0.236': low + diff * 0.236,
            '0.382': low + diff * 0.382,
            '0.5': low + diff * 0.5,
            '0.618': low + diff * 0.618,
            '0.786': low + diff * 0.786,
            '1.0': high,
        }
    
    @staticmethod
    def find_support_resistance(prices):
        """Encuentra soportes y resistencias via Fibonacci"""
        if len(prices) < 20:
            return {'support': None, 'resistance': None, 'levels': {}}
        
        recent = prices[-20:]
        low = min(recent)
        high = max(recent)
        current = prices[-1]
        
        levels = FibonacciAnalyzer.calculate_levels(low, high)
        if 'error' in levels:
            return {'support': low, 'resistance': high, 'levels': {}}
        
        # Support: nivel más cercano abajo del precio
        supports = [v for k, v in levels.items() if v < current]
        support = max(supports) if supports else low
        
        # Resistance: nivel más cercano arriba del precio
        resistances = [v for k, v in levels.items() if v > current]
        resistance = min(resistances) if resistances else high
        
        return {
            'support': float(support),
            'resistance': float(resistance),
            'levels': {k: float(v) for k, v in levels.items()},
        }


class MonteCarloSimulator:
    """Simula múltiples escenarios de precio"""
    
    @staticmethod
    def simulate_price_paths(current_price, atr, periods=10, simulations=500):
        """Simula 500 escenarios de precio en próximas N barras"""
        np.random.seed()
        
        if current_price <= 0 or atr <= 0:
            return {
                'mean': float(current_price),
                'median': float(current_price),
                'std': 0.0,
                'bull_probability': 0.5,
            }
        
        # Volatilidad por período
        daily_volatility = (atr / current_price) if current_price > 0 else 0.01
        
        # Matriz: (simulations x periods)
        paths = np.zeros((simulations, periods))
        paths[:, 0] = current_price
        
        for t in range(1, periods):
            returns = np.random.normal(0, daily_volatility, simulations)
            paths[:, t] = paths[:, t-1] * (1 + returns)
        
        final_prices = paths[:, -1]
        bull_count = np.sum(final_prices > current_price)
        
        return {
            'mean': float(np.mean(final_prices)),
            'median': float(np.median(final_prices)),
            'std': float(np.std(final_prices)),
            'percentile_5': float(np.percentile(final_prices, 5)),
            'percentile_25': float(np.percentile(final_prices, 25)),
            'percentile_75': float(np.percentile(final_prices, 75)),
            'percentile_95': float(np.percentile(final_prices, 95)),
            'bull_probability': float(bull_count / simulations),
        }


class LLM2TechnicalExpert:
    """Advanced technical analysis with Monte Carlo + Memory System"""
    
    def __init__(self):
        log.info("[STARTUP] LLM2 Technical Expert - Monte Carlo + Fibonacci + Memory")
        self.memory = {'EURUSD': deque(maxlen=300)}
        self.decision_history = deque(maxlen=100)
        
        # ============================================================
        # [MEMORY] SISTEMA DE MEMORIA INTELIGENTE - ANÁLISIS TÉCNICO
        # ============================================================
        self.pattern_memory = {
            'support_touches': 0,
            'resistance_touches': 0,
            'last_support': 0,
            'last_resistance': float('inf'),
            'consecutive_bull_signals': 0,
            'consecutive_bear_signals': 0,
            'mc_bull_trend': deque(maxlen=20),  # Últimas 20 prob Monte Carlo
            'fib_levels_hit': [],
            'breakout_count': 0,
        }
        self.market_structure = {
            'last_swing_high': 0,
            'last_swing_low': float('inf'),
            'trend_direction': 'NEUTRAL',
            'swing_count': 0,
        }
    
    def analyze(self, genome):
        """Main analysis function for genome data"""
        start_time = time.time()
        
        try:
            symbol = genome.get('symbol', 'EURUSD')
            
            # Extract data with safe defaults - try multiple sources
            price = float(genome.get('price', 0))
            
            # Try to get indicators from both root level and indicators.current
            indicators_root = genome.get('indicators', {})
            if isinstance(indicators_root, dict) and 'current' in indicators_root:
                indicators = indicators_root.get('current', {})
            else:
                indicators = indicators_root
            
            # Extract each indicator trying multiple field names
            atr_val = indicators.get('atr', indicators.get('atr_14', indicators.get('atr_pips', 10)))
            atr = float(genome.get('atr', float(genome.get('atr_14', float(atr_val)))))
            rsi = float(genome.get('rsi', float(indicators.get('rsi', 50))))
            adx = float(genome.get('adx', float(indicators.get('adx', 20))))
            
            # ⭐ CRITICAL FIX: Try multiple sources for prices (Trinity sends different formats)
            prices_list = []
            
            # Try source 1: prices as direct list
            if genome.get('prices') and isinstance(genome.get('prices'), list):
                prices_list = [float(p) for p in genome.get('prices', []) if p and float(p) > 0]
            
            # Try source 2: candles OHLC
            if not prices_list:
                candles = genome.get('candles', [])
                if isinstance(candles, list) and len(candles) > 0:
                    prices_list = [float(c.get('close', price)) for c in candles if c and c.get('close')]
            
            # Try source 3: bar_data closes
            if not prices_list:
                bar_data = genome.get('bar_data', {})
                if isinstance(bar_data, dict) and bar_data.get('closes'):
                    prices_list = [float(c) for c in bar_data.get('closes', []) if c and float(c) > 0]
            
            # Fallback to single price
            if not prices_list:
                prices_list = [float(price)] if price > 0 else [1000.0]
            
            # Convert to numpy array
            prices = np.array(prices_list) if prices_list else np.array([price if price > 0 else 1000.0])
            
            # ============================================================
            # FIBONACCI ANALYSIS
            # ============================================================
            fib_sr = FibonacciAnalyzer.find_support_resistance(prices)
            support = fib_sr.get('support', min(prices))
            resistance = fib_sr.get('resistance', max(prices))
            
            # Score proximity to support/resistance
            if support and resistance and support < resistance:
                range_val = resistance - support
                if range_val > 0:
                    dist_support = abs(price - support) / range_val
                    dist_resistance = abs(price - resistance) / range_val
                    
                    fib_score = 0
                    if dist_support < 0.05:
                        fib_score += 30  # Near support
                    if dist_resistance < 0.05:
                        fib_score += 30  # Near resistance
                else:
                    fib_score = 0
            else:
                fib_score = 0
            
            # ============================================================
            # MONTE CARLO SIMULATION
            # ============================================================
            mc_sim = MonteCarloSimulator.simulate_price_paths(price, atr, periods=10, simulations=500)
            bull_prob = mc_sim.get('bull_probability', 0.5)
            
            # ============================================================
            # TECHNICAL CONSENSUS
            # ============================================================
            
            # Consolidation check - M1 GOLD: ATR very low = reduced confidence
            # CHANGE: Don't return early, just reduce confidence
            # MEJORADO: Reducir penalty a 5-8 para permitir valores dinámicos
            consolidation_penalty = 0
            if atr < 0.5:
                consolidation_penalty = 5  # Reduce confidence by 5 if extreme consolidation (was 25)
            elif atr < 1.0:
                consolidation_penalty = 3  # Reduce by 3 if tight consolidation (was 10)
            
            # Signal generation
            bull_signals = 0
            bear_signals = 0
            
            # ════════════════════════════════════════════════════════════════
            # 🧠 MOMENTUM-BASED RSI (seguir tendencia, NO reversa)
            # ════════════════════════════════════════════════════════════════
            rsi_momentum_signal = 0
            price_momentum_5 = prices[-1] - prices[-5] if len(prices) >= 5 else 0
            
            # RSI > 50 + precio subiendo = MOMENTUM ALCISTA → BUY
            if rsi > 50 and price_momentum_5 > 0:
                rsi_momentum_signal = 0.5
                bull_signals += 1.5
            # RSI < 50 + precio bajando = MOMENTUM BAJISTA → SELL
            elif rsi < 50 and price_momentum_5 < 0:
                rsi_momentum_signal = -0.5
                bear_signals += 1.5
            # RSI fuerte (>60) + buen momentum = señal más fuerte
            elif rsi > 60 and price_momentum_5 > 0.2:
                bull_signals += 2
                rsi_momentum_signal = 0.8
            elif rsi < 40 and price_momentum_5 < -0.2:
                bear_signals += 2
                rsi_momentum_signal = -0.8
            
            self._last_rsi = rsi
            
            # ADX Analysis (trend strength, not direction)
            if adx > 25:  # Strong trend
                if price > (sum(prices[-5:]) / 5):  # Price above 5-bar average
                    bull_signals += 1
                else:
                    bear_signals += 1
            elif adx > 20:  # Moderate trend
                if price > (sum(prices[-5:]) / 5):
                    bull_signals += 0.5
                else:
                    bear_signals += 0.5
            
            # Monte Carlo
            if bull_prob > 0.65:
                bull_signals += 1
            elif bull_prob < 0.35:
                bear_signals += 1
            
            # Fibonacci proximity (MEJORADO: Detectar rebotes anticipados)
            support_proximity = 0
            resistance_proximity = 0
            
            # 🎯 PRECISION S/R: Solo dar señal si el precio REBOTA del nivel, no solo toca
            # Esto evita entradas en medio de un rompimiento fallido
            if support and support > 0:
                support_proximity = abs(price - support) / support * 100  # % distance
                price_above_support = price > support  # Precio ya rebotó arriba
                if support_proximity < 0.5 and price_above_support:  # Muy cerca + rebotando
                    bull_signals += 1.8  # Strong support bounce
                elif support_proximity < 1.0 and price_above_support:
                    bull_signals += 1.0  # Clean bounce
                elif support_proximity < 0.5 and not price_above_support:  # Rompiendo soporte!
                    bear_signals += 0.8  # Support break = bearish
            
            if resistance and resistance > 0:
                resistance_proximity = abs(price - resistance) / resistance * 100
                price_below_resistance = price < resistance  # Precio rechazado abajo
                if resistance_proximity < 0.5 and price_below_resistance:  # Muy cerca + rechazando
                    bear_signals += 1.8  # Strong resistance rejection
                elif resistance_proximity < 1.0 and price_below_resistance:
                    bear_signals += 1.0  # Clean rejection
                elif resistance_proximity < 0.5 and not price_below_resistance:  # Rompiendo resistencia!
                    bull_signals += 0.8  # Resistance break = bullish
            
            # ============================================================
            # DECISION LOGIC - BALANCED SNIPER MODE (RESPONSIVE BUT PRECISE)
            # ============================================================
            
            technical_score = (bull_signals - bear_signals) / max(1, bull_signals + bear_signals) if (bull_signals + bear_signals) > 0 else 0
            signal_strength = (bull_signals + bear_signals) / 10.0  # Magnitude of total signals (0-1 scale for 10 signals)
            
            # 🎯 PRECISION ENTRY: ADX confirmation for cleaner trades
            adx = float(genome.get('adx', 25))
            adx_trending = adx > 25
            adx_strong = adx > 35
            
            if bull_signals >= 1.5 and technical_score > 0.20 and rsi > 40:
                decision = 'BUY'
                base_conf = 55.0 + (technical_score * 80.0)
                # ADX boost: Trending = +10%, Strong = +18%
                if adx_strong:
                    confidence = min(94.0, base_conf * 1.18)
                elif adx_trending:
                    confidence = min(90.0, base_conf * 1.10)
                else:
                    confidence = min(75.0, base_conf * 0.85)  # Ranging = reduce
                reason = f'Bull ({bull_signals:.1f}) + ADX {adx:.0f} + RSI {rsi:.0f}'
                
            elif bear_signals >= 1.5 and technical_score < -0.20 and rsi < 60:
                decision = 'SELL'
                base_conf = 55.0 + (abs(technical_score) * 80.0)
                # ADX boost: Trending = +10%, Strong = +18%
                if adx_strong:
                    confidence = min(94.0, base_conf * 1.18)
                elif adx_trending:
                    confidence = min(90.0, base_conf * 1.10)
                else:
                    confidence = min(75.0, base_conf * 0.85)  # Ranging = reduce
                reason = f'Bear ({bear_signals:.1f}) + ADX {adx:.0f} + RSI {rsi:.0f}'
                
            # 🔴 MOMENTUM OVERRIDE: Solo si el momentum CONFIRMA la dirección
            elif rsi > 65 and price_momentum_5 < -0.3:  # RSI alto pero precio cayendo = posible agotamiento
                decision = 'HOLD'
                confidence = 40.0
                reason = f'RSI alto ({rsi:.1f}) pero precio cayendo → esperar confirmación'
            elif rsi < 35 and price_momentum_5 > 0.3:  # RSI bajo pero precio subiendo = posible rebote
                decision = 'HOLD'
                confidence = 40.0
                reason = f'RSI bajo ({rsi:.1f}) pero precio subiendo → esperar confirmación'
                
            else:
                decision = 'HOLD'
                # MEJORADO: Confianza GRANULAR con fracciones para sensibilidad a cambios pequeños
                # Ahora varía incluso cuando technical_score = 0 (señales balanceadas)
                signal_strength_confidence = 35.0 + signal_strength * 35.0  # 35-70 based on magnitude
                score_confidence = abs(technical_score) * 30.0  # 0-30 based on direction
                confidence = min(85.0, signal_strength_confidence + score_confidence)
                confidence = max(30.0, confidence)
                reason = f'Mixed signals (bull={bull_signals:.1f}, bear={bear_signals:.1f}), strength={signal_strength:.2f}'
            
            # Apply consolidation penalty to confidence (fractional for granularity)
            confidence = max(20.0, confidence - consolidation_penalty)
            
            # ============================================================
            # MEMORY UPDATE - ESTRUCTURA DE MERCADO
            # ============================================================
            pm = self.pattern_memory
            ms = self.market_structure
            
            # Actualizar tendencia Monte Carlo
            pm['mc_bull_trend'].append(bull_prob)
            mc_avg = sum(pm['mc_bull_trend']) / len(pm['mc_bull_trend']) if pm['mc_bull_trend'] else 0.5
            
            # Detectar toques S/R
            if support and abs(price - support) < atr * 0.1:
                pm['support_touches'] += 1
                pm['last_support'] = support
            if resistance and abs(price - resistance) < atr * 0.1:
                pm['resistance_touches'] += 1
                pm['last_resistance'] = resistance
            
            # Actualizar señales consecutivas
            if decision == 'BUY':
                pm['consecutive_bull_signals'] += 1
                pm['consecutive_bear_signals'] = 0
            elif decision == 'SELL':
                pm['consecutive_bear_signals'] += 1
                pm['consecutive_bull_signals'] = 0
            
            # Detectar swing highs/lows
            if price > ms['last_swing_high']:
                ms['last_swing_high'] = price
                ms['swing_count'] += 1
            if price < ms['last_swing_low']:
                ms['last_swing_low'] = price
                ms['swing_count'] += 1
            
            # Determinar dirección de estructura
            if price > ms['last_swing_high'] * 0.998:
                ms['trend_direction'] = 'BULLISH'
            elif price < ms['last_swing_low'] * 1.002:
                ms['trend_direction'] = 'BEARISH'
            
            # ============================================================
            # RETURN ANALYSIS + CONTEXTO EXTRA PARA LLM3/LLM4
            # ============================================================
            analysis_time_ms = int((time.time() - start_time) * 1000)
            
            result = {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reason,
                'technical_score': float(technical_score),
                'bull_signals': float(bull_signals),
                'bear_signals': float(bear_signals),
                'mc_bull_probability': float(bull_prob),
                'support': float(support) if support else None,
                'resistance': float(resistance) if resistance else None,
                'fib_score': float(fib_score),
                'analysis_time_ms': analysis_time_ms,
                # NUEVO: Contexto adicional para LLM3/LLM4
                'mc_avg_trend': float(mc_avg),
                'support_touches': pm['support_touches'],
                'resistance_touches': pm['resistance_touches'],
                'market_structure': ms['trend_direction'],
                'consecutive_bull': pm['consecutive_bull_signals'],
                'consecutive_bear': pm['consecutive_bear_signals'],
            }
            
            # DIAGNOSTICS
            if DIAGNOSTICS_ENABLED and TRACER:
                TRACER.log_llm_decision(
                    llm_name="LLM2",
                    genome=genome,
                    decision=decision,
                    confidence=confidence,
                    reasoning=reason
                )
                if DASHBOARD:
                    DASHBOARD.broadcast_llm_vote("LLM2", decision, confidence)
            
            return result
            
        except Exception as e:
            log.error(f"[ERROR] LLM2 analysis failed: {e}")
            analysis_time_ms = int((time.time() - start_time) * 1000)
            return {
                'decision': 'HOLD',
                'confidence': 30,
                'reasoning': f'Analysis error: {str(e)[:100]}',
                'analysis_time_ms': analysis_time_ms,
            }


def handle_client(sock, addr, expert):
    """Maneja conexión TCP de cliente"""
    sock.settimeout(30)
    try:
        while True:
            try:
                ld = sock.recv(4)
                
                if ld and b'PING' in ld[:4]:
                    pong_msg = struct.pack('>I', 4) + b'PONG'
                    sock.sendall(pong_msg)
                    log.debug(f"[PING] Responded to {addr}")
                    continue
                
                if not ld or len(ld) != 4:
                    break
                
                length = struct.unpack('>I', ld)[0]
                if length > 10_000_000:
                    log.warning(f"[CLIENT {addr}] Invalid length: {length}")
                    break
                
                data = b''
                while len(data) < length:
                    chunk = sock.recv(min(4096, length - len(data)))
                    if not chunk:
                        break
                    data += chunk
                
                if not data:
                    break
                
                try:
                    decoded = data.decode('utf-8', errors='replace')
                    request = json.loads(decoded)
                    
                    # ⭐ DEBUG: Log incoming data - ENHANCED to diagnose stale prices bug
                    log.info(f"[LLM2 RX] Keys: {list(request.keys())}")
                    log.info(f"[LLM2 RX] price={request.get('price')}, rsi={request.get('rsi')}, adx={request.get('adx')}, atr={request.get('atr')}")
                    prices_arr = request.get('prices', [])
                    log.info(f"[LLM2 RX] prices_count={len(prices_arr)} candles_count={len(request.get('candles', []))}")
                    if prices_arr:
                        log.info(f"[LLM2 RX] prices FIRST 5: {prices_arr[:5]}")
                        log.info(f"[LLM2 RX] prices LAST 5:  {prices_arr[-5:]}")  # ← Show end of array!
                        # Check if current tick is in prices array
                        current_px = request.get('price', 0)
                        if current_px > 0 and prices_arr:
                            gap = abs(prices_arr[-1] - current_px)
                            if gap > 0.5:
                                log.warning(f"[LLM2 RX] ⚠️ STALE DATA: current={current_px:.2f} but last_close={prices_arr[-1]:.2f} GAP={gap:.2f}!")
                    
                    response = expert.analyze(request)
                    response_json = json.dumps(response).encode('utf-8')
                    sock.sendall(struct.pack('>I', len(response_json)) + response_json)
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as je:
                    log.warning(f"[CLIENT {addr}] Invalid data: {je}")
                    error_resp = {"decision": "HOLD", "confidence": 0}
                    error_json = json.dumps(error_resp).encode('utf-8')
                    try:
                        sock.sendall(struct.pack('>I', len(error_json)) + error_json)
                    except:
                        pass
                    break
                    
            except socket.timeout:
                break
            except Exception as e:
                log.warning(f"[CLIENT {addr}] Error: {e}")
                break
    
    except Exception as e:
        log.warning(f"[CLIENT {addr}] Connection error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass


def print_nova_banner(port):
    """NOVA Banner con estilo amarillo/blanco"""
    Y = '\033[93m'  # Amarillo
    W = '\033[97m'  # Blanco
    G = '\033[92m'  # Verde
    C = '\033[96m'  # Cyan
    D = '\033[90m'  # Dim
    R = '\033[0m'   # Reset
    
    print(f"""
{Y}+{'='*62}+{R}
{Y}|{R}                                                              {Y}|{R}
{Y}|{R}  {Y}███╗   ██╗{W} ██████╗ ██╗   ██╗ █████╗ {R}                       {Y}|{R}
{Y}|{R}  {Y}████╗  ██║{W}██╔═══██╗██║   ██║██╔══██╗{R}   {C}LLM2 TECHNICAL{R}      {Y}|{R}
{Y}|{R}  {Y}██╔██╗ ██║{W}██║   ██║██║   ██║███████║{R}   {D}Indicator Expert{R}    {Y}|{R}
{Y}|{R}  {Y}██║╚██╗██║{W}██║   ██║╚██╗ ██╔╝██╔══██║{R}                       {Y}|{R}
{Y}|{R}  {Y}██║ ╚████║{W}╚██████╔╝ ╚████╔╝ ██║  ██║{R}                       {Y}|{R}
{Y}|{R}  {Y}╚═╝  ╚═══╝{W} ╚═════╝   ╚═══╝  ╚═╝  ╚═╝{R}                       {Y}|{R}
{Y}|{R}                                                              {Y}|{R}
{Y}+{'-'*62}+{R}
{Y}|{R}  {W}EURUSD M15 Sniper Edition{R}      {D}by Polarice Labs © 2026{R}       {Y}|{R}
{Y}|{R}  {G}● PORT: {port}{R}                  {D}RSI/MACD/BB/ADX{R}              {Y}|{R}
{Y}+{'='*62}+{R}
""")


def start_server():
    """Inicia servidor TCP en puerto 6556 - EURUSD M15"""
    try:
        config_file = 'euconfig.yaml'
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        except:
            config = {}
        
        port = config.get('llm_settings', {}).get('llm2_port', 6557)
        if not port or port < 1024:
            port = 6557  # FIXED: Was 6556 (EXECUTOR PORT!), now 6557

    except Exception as e:
        log.warning(f"Could not read config: {e}")
        port = 6557  # FIXED: Was 6556
    
    # Mostrar banner NOVA
    print_nova_banner(port)
    
    host = '127.0.0.1'
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(5)
    
    log.info(f"LLM2 TCP Server READY on {host}:{port}")
    
    expert = LLM2TechnicalExpert()
    
    try:
        while True:
            try:
                client_sock, client_addr = server_sock.accept()
                log.info(f"[CLIENT] New connection from {client_addr}")
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, client_addr, expert),
                    daemon=True
                )
                client_thread.start()
            except KeyboardInterrupt:
                log.info("[SHUTDOWN] Received interrupt")
                break
            except Exception as e:
                log.error(f"[ERROR] Accept error: {e}")
                continue
    
    except Exception as e:
        log.error(f"[FATAL] Server error: {e}")
    finally:
        server_sock.close()
        log.info("[SHUTDOWN] Server closed")


if __name__ == "__main__":
    start_server()
