#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ✨ NOVA TRADING AI - LLM9 (EXECUTION ENGINE)               ║
║                    Intelligent Order Execution v3.0                          ║
║              HYBRID: Deterministic FAST + Ollama CONTEXT SMART                ║
║                                                                              ║
║  Responsabilidades:                                                          ║
║  • Análisis inteligente de contexto de mercado (Ollama si disponible)        ║
║  • Calcula posición óptima con Kelly Criterion + Risk Management             ║
║  • Determina SL/TP dinámicos basado en volatilidad y confluencia             ║
║  • Valida R:R ratio dinámicamente (no fórmula fija)                          ║
║  • Escala posición 0.3x-2.0x según contexto y confluencia                    ║
║  • Explica cada decisión (transparency para debugging)                       ║
║                                                                              ║
║  Arquitectura HÍBRIDA OPTIMIZADA:                                            ║
║  1. Análisis DETERMINÍSTICO rápido (<50ms) - siempre funciona               ║
║  2. Consulta Ollama para CONTEXTO (<1s timeout) - solo si disponible        ║
║  3. FUSIONA resultados para decisión INTELIGENTE                            ║
║  4. Retorna parámetros ÓPTIMOS con explicación detallada                    ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Edition: Scalping AI M1/M5 | Intelligent Execution | Production Ready       ║
║  Port: 9265 (TCP Server) | Pure Python + Optional Ollama | <100ms latency   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, struct, json, logging, threading, time
import numpy as np
import requests
import signal
import sys
from collections import deque
import os

# ==================== OLLAMA CONFIGURATION ====================
OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 1.0  # Fast timeout - if Ollama takes >1s, use fallback
OLLAMA_TEMPERATURE = 0.3  # Low temperature = deterministic

# ==================== LOGGING ====================
os.makedirs('logs', exist_ok=True)
_log_file = f'logs/llm9_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
_file_handler = logging.FileHandler(_log_file, encoding='utf-8')
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s | 🔫 LLM9 | %(message)s", datefmt='%H:%M:%S')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger()
log.info(f"[INIT] Log file: {_log_file}")
class LLM9:
    """
    ✨ NOVA LLM9 - Execution Intelligence Engine
    
    HYBRID approach:
    - Base logic: Fast deterministic rules (<50ms)
    - Ollama layer: Context analysis for market understanding (<1s)
    - Fallback: Always works, even if Ollama offline
    - Smart scaling: 0.3x-2.0x posición según confluencia
    
    REQUERIMIENTOS:
    - Trinity envía: consensus_confidence, decision, ATR, RSI, prices
    - LLM7 (OCULUS) envía: quality_score (0-100)
    - LLM8 (CHRONOS) envía: timing_multiplier (0-1.0)
    
    RESPONDE CON:
    - decision: EXECUTE, READY, WAIT, ABORT
    - position_size: volumen de la orden
    - stop_loss, take_profit: niveles exactos
    - rr_ratio: relación riesgo/recompensa
    - reason: explicación inteligible
    """
    
    def __init__(self):
        self.port = 9265  # NZDUSD LLM9 PREDATOR
        self.history = deque(maxlen=100)
        self.max_position_size = 0.05  # 5% account risk per trade
        self.running = True
        
        # Ollama health check
        self.ollama_available = self._check_ollama_health()
        self.ollama_cache = {}  # Simple cache for recent analyses
        
        log.info(f"═══════════════════════════════════════════════════════════════")
        log.info(f"[LLM9] ✨ Execution Intelligence Engine v3.0")
        log.info(f"[LLM9] Port: 9265 | Hybrid: Deterministic + Ollama Context")
        log.info(f"[LLM9] Ollama Status: {'🟢 ONLINE (Smart analysis enabled)' if self.ollama_available else '🔴 OFFLINE (Fast fallback active)'}")
        log.info(f"[LLM9] Ready to calculate intelligent order parameters")
        log.info(f"═══════════════════════════════════════════════════════════════")
        
        # Setup Ctrl+C handler
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown"""
        log.info("[LLM9] Shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def _check_ollama_health(self):
        """Check if Ollama is available (quick test)"""
        try:
            response = requests.post(
                OLLAMA_ENDPOINT,
                json={"model": OLLAMA_MODEL, "prompt": "test", "stream": False},
                timeout=0.5
            )
            return response.status_code == 200
        except:
            return False
    
    def _query_ollama_for_context(self, data):
        """
        Consulta Ollama para análisis de contexto (pero RÁPIDO).
        Si tarda >1s, usa fallback.
        
        Returns: (context_analysis, ollama_worked)
        """
        try:
            price = float(data.get('price', 0))
            rsi = float(data.get('rsi', 50))
            atr = float(data.get('atr_14', price * 0.01))
            adx = float(data.get('adx_14', 20))
            consensus_confidence = float(data.get('consensus_confidence', 50))
            
            # Build QUICK prompt (no más de 200 caracteres)
            prompt = f"""ANÁLISIS RÁPIDO:
Precio:{price:.2f} RSI:{rsi:.0f} ATR:{atr:.2f} ADX:{adx:.0f} Conf:{consensus_confidence:.0f}%
¿Contexto? 1-palabra: (Fuerte/Normal/Débil/Caótico)"""
            
            start = time.time()
            response = requests.post(
                OLLAMA_ENDPOINT,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": OLLAMA_TEMPERATURE,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                context_text = result.get('response', 'Normal').strip().lower()
                
                # Extract key word
                if 'fuerte' in context_text or 'strong' in context_text:
                    context = 'STRONG'
                elif 'débil' in context_text or 'weak' in context_text:
                    context = 'WEAK'
                elif 'caótico' in context_text or 'chaos' in context_text:
                    context = 'CHAOTIC'
                else:
                    context = 'NORMAL'
                
                log.info(f"[LLM9] ⚙️ Ollama Context Analysis: {context} ({elapsed:.3f}s)")
                return context, True
        except requests.Timeout:
            log.debug(f"[LLM9] Ollama timeout (>1s) - using fallback")
        except Exception as e:
            log.debug(f"[LLM9] Ollama error: {e}")
        
        # Fallback: deterministic analysis
        return self._analyze_context_deterministic(data), False
    
    def _analyze_context_deterministic(self, data):
        """
        Análisis RÁPIDO sin Ollama. Determinístico, siempre funciona.
        Ejecuta en <10ms.
        """
        try:
            rsi = float(data.get('rsi', 50))
            atr = float(data.get('atr_14', 0.01))
            adx = float(data.get('adx_14', 20))
            price = float(data.get('price', 0))
            
            # ADX = trend strength
            if adx > 35:
                adx_context = 'STRONG'
            elif adx > 25:
                adx_context = 'NORMAL'
            elif adx > 15:
                adx_context = 'WEAK'
            else:
                adx_context = 'CHAOTIC'
            
            # RSI = overbought/oversold
            if rsi > 75 or rsi < 25:
                rsi_context = 'EXTREME'
            elif rsi > 60 or rsi < 40:
                rsi_context = 'BIASED'
            else:
                rsi_context = 'NEUTRAL'
            
            # Combine contexts
            if adx_context == 'CHAOTIC':
                return 'CHAOTIC'
            elif adx_context == 'STRONG' and rsi_context == 'EXTREME':
                return 'STRONG'
            elif adx_context in ['NORMAL', 'WEAK']:
                if rsi_context == 'NEUTRAL':
                    return 'NORMAL'
                else:
                    return 'WEAK'
            else:
                return 'NORMAL'
        
        except:
            return 'NORMAL'
    
    def _calculate_position_size(self, data):
        """
        Calcula posición base usando Kelly Criterion.
        Después se escala con position_multiplier según confluencia.
        """
        try:
            price = float(data.get('price', 0))
            atr = float(data.get('atr_14', price * 0.01))
            account_risk = self.max_position_size  # 5% risk per trade
            
            # Stop loss = 2 * ATR (más conservador que el anterior)
            sl_distance = 2.0 * atr
            
            # Kelly Criterion: Position = Risk / Risk_Distance
            position_size = (account_risk * price) / (sl_distance + 0.0001)
            
            # Clamp to reasonable range
            position_size = min(position_size, self.max_position_size * price)
            
            return max(position_size, 0.01)
        
        except Exception as e:
            log.warning(f"[LLM9] Position size calculation error: {e}")
            return 0.01
    
    def _calculate_stop_loss(self, data):
        """
        🎯 PRECISION SL: Usa el SWING LOW/HIGH más reciente (últimas 3-5 velas) 
        para BUY/SELL + buffer pequeño.
        M1 scalping requiere stops AJUSTADOS al price action real, NO rangos amplios.
        """
        try:
            price = float(data.get('price', 0))
            decision = data.get('consensus_decision', 'SELL')
            
            # Get recent candle ranges
            price_data = data.get('price_data', {})
            highs = price_data.get('high', [])
            lows = price_data.get('low', [])
            
            # STRATEGY: Use recent swing low/high (últimas 3-5 velas)
            if len(highs) >= 5 and len(lows) >= 5:
                recent_highs = highs[-5:]
                recent_lows = lows[-5:]
                
                if decision == 'BUY':
                    # SL = recent swing low - pequeño buffer
                    swing_low = min(recent_lows)
                    buffer = (price - swing_low) * 0.12  # 12% buffer extra
                    sl_distance = (price - swing_low) + buffer
                else:  # SELL
                    # SL = recent swing high + pequeño buffer
                    swing_high = max(recent_highs)
                    buffer = (swing_high - price) * 0.12  # 12% buffer extra
                    sl_distance = (swing_high - price) + buffer
            else:
                # Fallback: usar rango promedio de últimas 3 velas
                if len(highs) >= 3 and len(lows) >= 3:
                    recent_ranges = [highs[i] - lows[i] for i in range(-3, 0)]
                    avg_range = sum(recent_ranges) / 3
                    sl_distance = avg_range * 0.75  # 75% del rango promedio (tight)
                else:
                    sl_distance = price * 0.0018  # 0.18% fallback
            
            # Clamp para broker requirements (M1 scalping forex)
            sl_distance = max(0.0008, min(0.0030, sl_distance))  # Forex: 8-30 pips
            
            if decision == 'BUY':
                stop_loss = price - sl_distance
            else:  # SELL
                stop_loss = price + sl_distance
            
            log.info(f"[LLM9 🎯 SL] {decision}: price={price:.5f} sl={stop_loss:.5f} dist={sl_distance*10000:.1f}pips")
            return stop_loss
        
        except Exception as e:
            log.warning(f"[LLM9] SL calculation error: {e}")
            return price
    
    def _calculate_take_profit(self, data):
        """
        🎯 PRECISION TP: R:R dinámico basado en confidence
        High conf (>75%) = 2.0:1 | Med (60-75%) = 1.8:1 | Low (<60%) = 1.5:1
        """
        try:
            price = float(data.get('price', 0))
            decision = data.get('consensus_decision', 'SELL')
            stop_loss = self._calculate_stop_loss(data)
            
            # Get consensus confidence for dynamic R:R
            confidence = float(data.get('consensus_confidence', 50))
            
            # Dynamic R:R based on confidence
            if confidence > 75:
                rr_ratio = 2.0  # Alta probabilidad → objetivo mayor
            elif confidence > 60:
                rr_ratio = 1.8  # Media probabilidad
            else:
                rr_ratio = 1.5  # Baja probabilidad → objetivo conservador
            
            # Calcular TP basado en SL distance
            if decision == 'BUY':
                sl_distance = price - stop_loss
                tp_distance = sl_distance * rr_ratio
                take_profit = price + tp_distance
            else:  # SELL
                sl_distance = stop_loss - price
                tp_distance = sl_distance * rr_ratio
                take_profit = price - tp_distance
            
            log.info(f"[LLM9 🎯 TP] {decision}: price={price:.5f} tp={take_profit:.5f} R:R={rr_ratio}:1 (conf={confidence:.0f}%)")
            return take_profit
        
        except Exception as e:
            log.warning(f"[LLM9] TP calculation error: {e}")
            return price
    
    def analyze(self, data):
        """
        Main analysis method - Intelligent execution decision.
        
        PROCESO:
        1. Valida inputs de Trinity + LLM7 + LLM8
        2. Análisis RÁPIDO determinístico (<10ms)
        3. Consulta Ollama para CONTEXTO (con timeout fallback)
        4. Calcula parámetros SL/TP/Size
        5. Valida R:R ratio
        6. Escala posición según confluencia
        7. Retorna decisión INTELIGENTE con explicación
        """
        try:
            symbol = data.get('symbol', 'NZDUSD')
            price = float(data.get('price', 0))
            consensus_confidence = float(data.get('consensus_confidence', 50))
            consensus_decision = data.get('consensus_decision', 'HOLD')
            
            # Datos de LLM7 OCULUS y LLM8 CHRONOS
            quality_score = float(data.get('quality_score', 70))  # 0-100
            timing_multiplier = float(data.get('timing_multiplier', 1.0))  # 0-1.0
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 1: INPUT VALIDATION                                        │
            # └─────────────────────────────────────────────────────────────────┘
            log.info(f"═══════════════════════════════════════════════════════════════")
            log.info(f"[LLM9] 📥 INPUT RECEIVED:")
            log.info(f"       • Symbol: {symbol} @ {price:.5f}")
            log.info(f"       • Trinity: Decision={consensus_decision} | Confidence={consensus_confidence:.0f}%")
            log.info(f"       • LLM7 OCULUS: Quality={quality_score:.0f}%")
            log.info(f"       • LLM8 CHRONOS: Timing={timing_multiplier:.2f}x")
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 2: SMART CONTEXT ANALYSIS (Fast + Optional Ollama)         │
            # └─────────────────────────────────────────────────────────────────┘
            market_context, ollama_used = self._query_ollama_for_context(data)
            if ollama_used:
                log.info(f"[LLM9] 🧠 Market Context: {market_context} (via Ollama)")
            else:
                log.info(f"[LLM9] 🧠 Market Context: {market_context} (deterministic)")
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 3: PARAMETER CALCULATION                                   │
            # └─────────────────────────────────────────────────────────────────┘
            base_position_size = self._calculate_position_size(data)
            stop_loss = self._calculate_stop_loss(data)
            take_profit = self._calculate_take_profit(data)
            
            # ⭐ CRITICAL FIX: Initialize risk/reward BEFORE conditional block
            # to prevent "cannot access local variable 'risk'" error
            risk = 0.0
            reward = 0.0
            
            # Calculate R:R ratio
            if stop_loss > 0 and take_profit > 0:
                if consensus_decision == 'BUY':
                    risk = price - stop_loss
                    reward = take_profit - price
                else:
                    risk = stop_loss - price
                    reward = price - take_profit
                
                rr_ratio = reward / (risk + 0.0001) if risk > 0 else 0
            else:
                rr_ratio = 0
            
            log.info(f"[LLM9] 📊 PARAMETERS:")
            log.info(f"       • Entry: {price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            log.info(f"       • Risk: {abs(risk):.2f} pips | Reward: {abs(reward):.2f} pips")
            log.info(f"       • R:R Ratio: {rr_ratio:.2f}:1 | Position Base: {base_position_size:.4f} lots")
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 4: INTELLIGENT SCALING (Context + Confluence)              │
            # └─────────────────────────────────────────────────────────────────┘
            position_multiplier = 1.0
            scaling_reason = ""
            
            # Context-based scaling
            if market_context == 'STRONG':
                position_multiplier *= 1.3  # 30% increase in strong trends
                scaling_reason += "Strong_Trend(1.3x) "
            elif market_context == 'CHAOTIC':
                position_multiplier *= 0.5  # 50% reduction in chaos
                scaling_reason += "Chaotic_Market(0.5x) "
            
            # Confluence-based scaling (quality + timing)
            if quality_score >= 90 and timing_multiplier >= 0.8:
                position_multiplier *= 1.2  # Perfect confluence
                scaling_reason += "Perfect_Confluence(1.2x) "
            elif quality_score < 60 or timing_multiplier < 0.5:
                position_multiplier *= 0.7  # Weak confluence
                scaling_reason += "Weak_Confluence(0.7x) "
            
            # R:R validation
            if rr_ratio < 1.5:
                position_multiplier *= 0.8  # Poor R:R
                scaling_reason += "Poor_RR(0.8x) "
            
            # Clamp to reasonable range
            position_multiplier = np.clip(position_multiplier, 0.3, 2.0)
            
            final_position_size = base_position_size * position_multiplier
            
            log.info(f"[LLM9] 🎯 SCALING: {position_multiplier:.2f}x")
            log.info(f"       • Reason: {scaling_reason if scaling_reason else 'Normal'}")
            log.info(f"       • Final Position: {final_position_size:.4f} lots")
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 5: EXECUTION DECISION LOGIC                                │
            # └─────────────────────────────────────────────────────────────────┘
            if consensus_confidence >= 65 and consensus_decision in ['BUY', 'SELL']:
                if quality_score >= 50 and rr_ratio >= 1.5:
                    decision = 'EXECUTE'
                    execution_status = 'READY'
                    reason = f"All gates passed: Conf={consensus_confidence:.0f}% | Quality={quality_score:.0f}% | RR={rr_ratio:.2f}:1 | Timing={timing_multiplier:.2f}x"
                    log.info(f"[LLM9] ✅ EXECUTE APPROVED")
                else:
                    decision = 'READY'
                    execution_status = 'READY'
                    reason = f"Conf OK but quality or R:R weak - ready if needed"
                    log.info(f"[LLM9] ⏳ READY (conditions sub-optimal)")
            else:
                decision = 'WAIT'
                execution_status = 'WAITING'
                if consensus_confidence < 45:
                    reason = f"Trinity confidence too low: {consensus_confidence:.0f}% < 45%"
                else:
                    reason = f"Decision not BUY/SELL: {consensus_decision}"
                log.info(f"[LLM9] ⏸️ WAIT - {reason}")
            
            # Calculate final confidence
            final_confidence = min(95, int(
                (consensus_confidence * 0.5) +  # Trinity weight
                (quality_score * 0.3) +  # OCULUS weight
                (timing_multiplier * 100 * 0.2)  # CHRONOS weight
            ))
            
            # ┌─────────────────────────────────────────────────────────────────┐
            # │ STEP 6: BUILD RESULT                                            │
            # └─────────────────────────────────────────────────────────────────┘
            result = {
                'decision': decision,
                'confidence': final_confidence,
                'execution_status': execution_status,
                'position_size': final_position_size if decision == 'EXECUTE' else 0,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rr_ratio': rr_ratio,
                'position_multiplier': position_multiplier,
                'market_context': market_context,
                'reason': reason,
                'ollama_used': ollama_used,
                'quality_score_input': quality_score,
                'timing_multiplier_input': timing_multiplier,
                'timestamp': time.time()
            }
            
            self.history.append(result)
            
            log.info(f"[LLM9] 🎁 FINAL RESULT:")
            log.info(f"       • Decision: {decision}")
            log.info(f"       • Confidence: {final_confidence:.0f}%")
            log.info(f"       • Position Size: {final_position_size:.4f} lots")
            log.info(f"       • Reason: {reason}")
            log.info(f"═══════════════════════════════════════════════════════════════")
            
            return result
        
        except Exception as e:
            log.error(f"[LLM9] Analysis error: {e}", exc_info=True)
            return {
                'decision': 'WAIT',
                'confidence': 0,
                'execution_status': 'ERROR',
                'position_size': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'rr_ratio': 0,
                'reason': f'Analysis error: {e}',
                'timestamp': time.time()
            }
    
    def run_server(self):
        """TCP Server - listen for requests from Trinity"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)
        log.info(f"[LLM9] 🔌 Server listening on port {self.port}")
        
        try:
            while self.running:
                conn, addr = server.accept()
                threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            log.info("[LLM9] Shutting down server")
        finally:
            server.close()
    
    def _handle_request(self, conn):
        """Handle incoming TCP request from Trinity"""
        try:
            # Read header (4 bytes = JSON length)
            header = conn.recv(4)
            if len(header) < 4:
                return
            
            # Unpack length
            data_length = struct.unpack('>I', header)[0]
            
            # Read JSON data
            data_bytes = b''
            while len(data_bytes) < data_length:
                chunk = conn.recv(min(4096, data_length - len(data_bytes)))
                if not chunk:
                    break
                data_bytes += chunk
            
            # Parse JSON
            request_data = json.loads(data_bytes.decode('utf-8'))
            
            # Analyze
            result = self.analyze(request_data)
            
            # Send response
            response_json = json.dumps(result)
            response_bytes = response_json.encode('utf-8')
            response_header = struct.pack('>I', len(response_bytes))
            conn.sendall(response_header + response_bytes)
        
        except Exception as e:
            log.warning(f"[LLM9] Request handling error: {e}")
        
        finally:
            conn.close()

if __name__ == '__main__':
    llm9 = LLM9()
    llm9.run_server()
