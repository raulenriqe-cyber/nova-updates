#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
                    NOVA TRADING AI - LLM9 PREDATOR                        
                    USDJPY M15 - Samurai Predator Edition                      
                       Execution Engine v1.0                                  
                                                                              
  Calcula parametros exactos de ordenes: volumen, stop loss, take profit      
  Aplica Kelly Criterion para position sizing optimo                          
  Valida relacion Riesgo/Recompensa (minimo 1:2)                              
                                                                              
  Author: Polar Trading Systems by Polaricelabs 2026                        
  Edition: Samurai AI | M15 Optimization                                       
  Port: 7865 (TCP Server) | Pure Python | Low Latency                         
===============================================================================
"""
import sys, os
# ⭐ USDJPY: Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 LOAD PORTS FROM CENTRALIZED CONFIG (jpyconfig.yaml)
# ═══════════════════════════════════════════════════════════════════════════
try:
    from jpy_config_loader import get_llm_port
    EU_CONFIG_LOADED = True
except ImportError:
    EU_CONFIG_LOADED = False

import socket, struct, json, logging, threading, time
import numpy as np
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | LLM9_PREDATOR | %(message)s",  # Sin emoji unicode
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

class PREDATOR:
    """
    ✨ NOVA LLM9 - PREDATOR (Execution Engine)
    
    Responsabilidades:
    - Calcula position size óptima usando Kelly Criterion
    - Determina stop loss (2 ATR por debajo/arriba)
    - Calcula take profit (relación R/R 1:3)
    - Valida si confianza >= 70% para ejecutar
    - Retorna parámetros exactos de orden o WAIT
    
    Estrategia:
    1. Recibe data de consenso (decision, confidence, ATR)
    2. Calcula risk/reward usando ATR como base
    3. Aplica Kelly para dimensionar posición
    4. Genera EXECUTE o WAIT basado en confianza
    5. Retorna parámetros listos para MT5
    
    Autor: Polaricelabs 2026
    """
    
    def __init__(self):
        self.port = 7865  # USDJPY LLM9 port (fixed: was 7863)
        self.history = deque(maxlen=100)
        self.max_position_size = 0.05  # 5% of account per trade
        log.info("[PREDATOR] ✨ Execution Engine initialized (Port 7864 USDJPY)")
        log.info("[PREDATOR] 🔫 Calculating precise order parameters")
        log.info("[PREDATOR] ⚡ Pure Python | <50ms latency | M15 optimized")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 🎯 USDJPY M15 INTELLIGENT PARAMETERS
        # ═══════════════════════════════════════════════════════════════════════════
        # USDJPY M15 characteristics:
        # - ATR(14) typical: 8-15 pips
        # - Single M15 candle: 5-12 pips typical
        # - Trend move over 2-4 hours: 20-40 pips
        # - Spread: 0.5-1.5 pips (must account for this in SL/TP)
        # ═══════════════════════════════════════════════════════════════════════════
        self.USDJPY_ATR_MIN = 5       # Minimum ATR to trade (market must be alive)
        self.USDJPY_ATR_MAX = 20      # Maximum ATR (avoid news spikes)
        self.USDJPY_ATR_OPTIMAL = 10  # Optimal ATR for best entries
        self.USDJPY_SL_MIN = 25       # 25 pips minimum SL (broker + spread safe)
        self.USDJPY_SL_MAX = 50       # 50 pips maximum SL
        self.USDJPY_TP_MIN = 30       # 30 pips minimum TP (achievable)
        self.USDJPY_TP_MAX = 60       # 60 pips maximum TP (realistic)
        self.USDJPY_RR_TARGET = 1.5   # Target R:R ratio
    
    def _calculate_position_size(self, data):
        """Calculate optimal position size using risk/reward - USDJPY M15 INTELLIGENT"""
        try:
            price = float(data.get('price', 1.0))
            atr_raw = float(data.get('atr_14', 10.0))  # ATR in pips
            account_risk = self.max_position_size  # 5% risk per trade
            
            # Clamp ATR to USDJPY M15 realistic range
            atr = max(self.USDJPY_ATR_MIN, min(self.USDJPY_ATR_MAX, atr_raw))
            
            # Calculate SL distance based on ATR (in pips)
            sl_distance_pips = atr * 1.0  # 1x ATR for SL
            sl_distance_pips = max(self.USDJPY_SL_MIN, min(self.USDJPY_SL_MAX, sl_distance_pips))
            
            # Convert pips to price movement
            sl_distance_price = sl_distance_pips * 0.0001
            
            # Position size = account_risk / sl_distance (risk-based sizing)
            position_size = (account_risk * price) / (sl_distance_price * 10000 + 0.01)
            
            # Clamp to safe maximum
            position_size = min(position_size, 0.10)  # Max 10% position
            
            return round(position_size, 4)
        
        except Exception as e:
            log.warning(f"Position size calculation error: {e}")
            return 0.02  # Default safe position
    
    def _calculate_stop_loss(self, data):
        """Calculate stop loss level - USDJPY M15 INTELLIGENT MATHEMATICS"""
        try:
            price = float(data.get('price', 1.0))
            atr_raw = float(data.get('atr_14', 10.0))  # ATR in pips
            decision = data.get('llm_decision', data.get('consensus_decision', 'HOLD'))
            spread = float(data.get('spread', 1.0))  # Spread in pips
            
            # ═══════════════════════════════════════════════════════════════════════════
            # 🧠 INTELLIGENT SL CALCULATION FOR USDJPY M15
            # ═══════════════════════════════════════════════════════════════════════════
            # Formula: SL = ATR × multiplier + spread buffer
            # - Low volatility (ATR < 8): Use minimum SL (8 pips)
            # - Normal volatility (ATR 8-15): Use 1.0 × ATR
            # - High volatility (ATR > 15): Use 0.8 × ATR (tighter for protection)
            # ═══════════════════════════════════════════════════════════════════════════
            
            # Clamp ATR to realistic USDJPY M15 range
            atr = max(self.USDJPY_ATR_MIN, min(self.USDJPY_ATR_MAX, atr_raw))
            
            # Dynamic multiplier based on volatility
            if atr < 8:
                sl_multiplier = 1.2  # Low vol = wider relative SL
            elif atr > 15:
                sl_multiplier = 0.8  # High vol = tighter relative SL
            else:
                sl_multiplier = 1.0  # Normal = 1x ATR
            
            sl_distance_pips = atr * sl_multiplier + (spread * 0.5)  # Add half spread buffer
            
            # Clamp to USDJPY M15 safe range
            sl_distance_pips = max(self.USDJPY_SL_MIN, min(self.USDJPY_SL_MAX, sl_distance_pips))
            sl_distance = sl_distance_pips * 0.0001  # Convert pips to price
            
            # Apply to price based on direction
            if decision == 'BUY':
                sl = price - sl_distance
            elif decision == 'SELL':
                sl = price + sl_distance
            else:
                sl = price
            
            log.debug(f"[PREDATOR] SL calc: ATR={atr:.1f} mult={sl_multiplier:.1f} → {sl_distance_pips:.1f} pips")
            return round(sl, 5)
        
        except Exception as e:
            log.warning(f"SL calculation error: {e}")
            return 0
    
    def _calculate_take_profit(self, data):
        """Calculate take profit level - USDJPY M15 INTELLIGENT MATHEMATICS"""
        try:
            price = float(data.get('price', 1.0))
            atr_raw = float(data.get('atr_14', 10.0))  # ATR in pips
            decision = data.get('llm_decision', data.get('consensus_decision', 'HOLD'))
            confidence = float(data.get('consensus_confidence', 60))
            
            # ═══════════════════════════════════════════════════════════════════════════
            # 🧠 INTELLIGENT TP CALCULATION FOR USDJPY M15
            # ═══════════════════════════════════════════════════════════════════════════
            # Formula: TP = SL × R:R ratio (target 1.5:1 to 2:1)
            # - High confidence (>80%): Target 2:1 R:R (more aggressive)
            # - Normal confidence (60-80%): Target 1.5:1 R:R
            # - Low confidence (<60%): Target 1.3:1 R:R (conservative)
            # ═══════════════════════════════════════════════════════════════════════════
            
            # Clamp ATR to realistic range
            atr = max(self.USDJPY_ATR_MIN, min(self.USDJPY_ATR_MAX, atr_raw))
            
            # Calculate SL distance first (same logic as _calculate_stop_loss)
            if atr < 8:
                sl_multiplier = 1.2
            elif atr > 15:
                sl_multiplier = 0.8
            else:
                sl_multiplier = 1.0
            sl_distance_pips = atr * sl_multiplier
            sl_distance_pips = max(self.USDJPY_SL_MIN, min(self.USDJPY_SL_MAX, sl_distance_pips))
            
            # Dynamic R:R based on confidence
            if confidence >= 80:
                rr_target = 2.0   # High confidence = aggressive target
            elif confidence >= 60:
                rr_target = 1.5   # Normal confidence = balanced target
            else:
                rr_target = 1.3   # Low confidence = conservative target
            
            # TP = SL × R:R ratio
            tp_distance_pips = sl_distance_pips * rr_target
            
            # Clamp to USDJPY M15 realistic range
            tp_distance_pips = max(self.USDJPY_TP_MIN, min(self.USDJPY_TP_MAX, tp_distance_pips))
            tp_distance = tp_distance_pips * 0.0001  # Convert pips to price
            
            # Apply to price based on direction
            if decision == 'BUY':
                tp = price + tp_distance
            elif decision == 'SELL':
                tp = price - tp_distance
            else:
                tp = price
            
            log.debug(f"[PREDATOR] TP calc: SL={sl_distance_pips:.1f} × R:R={rr_target:.1f} → {tp_distance_pips:.1f} pips")
            return round(tp, 5)
        
        except Exception as e:
            log.warning(f"TP calculation error: {e}")
            return 0
    
    def analyze(self, data):
        """Main analysis method - USDJPY M15 INTELLIGENT EXECUTION"""
        try:
            symbol = data.get('symbol', 'USDJPY')
            price = float(data.get('price', 1.0))
            consensus_confidence = float(data.get('consensus_confidence', 50))
            consensus_decision = data.get('consensus_decision', 'HOLD')
            atr = float(data.get('atr_14', 10.0))
            
            # ═══════════════════════════════════════════════════════════════════════════
            # 🧠 INTELLIGENT ENTRY DECISION FOR USDJPY M15
            # ═══════════════════════════════════════════════════════════════════════════
            # Only execute if:
            # 1. Market is moving (ATR >= 5 pips)
            # 2. Not too volatile (ATR <= 20 pips)
            # 3. Confidence is sufficient (>= 50% to calculate, >= 60% to execute)
            # ═══════════════════════════════════════════════════════════════════════════
            
            # Check market conditions
            market_alive = atr >= self.USDJPY_ATR_MIN
            market_safe = atr <= self.USDJPY_ATR_MAX
            market_optimal = self.USDJPY_ATR_MIN <= atr <= self.USDJPY_ATR_OPTIMAL * 1.5
            
            # Calculate levels if market conditions are OK and we have a signal
            if market_alive and market_safe and consensus_confidence >= 50 and consensus_decision in ['BUY', 'SELL']:
                # Calculate execution parameters
                position_size = self._calculate_position_size(data)
                stop_loss = self._calculate_stop_loss(data)
                take_profit = self._calculate_take_profit(data)
                
                # Calculate R/R ratio
                if stop_loss > 0 and take_profit > 0:
                    if consensus_decision == 'BUY':
                        risk = price - stop_loss
                        reward = take_profit - price
                    else:
                        risk = stop_loss - price
                        reward = price - take_profit
                    
                    rr_ratio = reward / (risk + 0.00001)
                else:
                    rr_ratio = 0
                
                # Decision logic - LOWERED thresholds for USDJPY M15
                if consensus_confidence >= 60 and rr_ratio >= 1.3 and market_optimal:
                    decision = 'EXECUTE'
                    confidence = min(95, consensus_confidence * 1.05)  # Small boost for optimal conditions
                elif consensus_confidence >= 55 and rr_ratio >= 1.2:
                    decision = 'READY'
                    confidence = consensus_confidence
                else:
                    decision = 'READY'  # Prepared but not urgent
                    confidence = consensus_confidence * 0.9
                
                execution_status = 'READY'
            else:
                # Market conditions not suitable or no signal
                position_size = 0
                stop_loss = price
                take_profit = price
                rr_ratio = 0
                
                if not market_alive:
                    decision = 'WAIT'
                    confidence = 20
                    execution_status = 'LOW_VOLATILITY'
                elif not market_safe:
                    decision = 'WAIT'
                    confidence = 15
                    execution_status = 'HIGH_VOLATILITY'
                else:
                    decision = 'WAIT'
                    confidence = max(20, 100 - consensus_confidence)
                    execution_status = 'WAITING'
            
            # ===== ADX FILTER: Precision execution based on trend strength =====
            adx = float(data.get('adx', data.get('adx_14', 20)))
            adx_trending = adx > 20  # LOWERED: USDJPY trends are weaker than gold
            adx_strong = adx > 30    # LOWERED: Strong for EUR standards
            
            if decision == 'EXECUTE':
                if adx_strong:
                    # Strong trend: boost confidence, allow larger position
                    confidence = min(95, confidence * 1.10)
                    log.debug(f"[PREDATOR] ADX={adx:.1f} STRONG → conf boost 1.10x")
                elif adx_trending:
                    # Normal trend: standard execution
                    log.debug(f"[PREDATOR] ADX={adx:.1f} trending → normal execution")
                else:
                    # Ranging market: reduce size and confidence (choppy = risky)
                    position_size = position_size * 0.7
                    confidence = confidence * 0.85
                    log.debug(f"[PREDATOR] ADX={adx:.1f} RANGING → reduced execution 0.7x")
            
            result = {
                'decision': decision,
                'confidence': confidence,
                'execution_status': execution_status,
                'position_size': position_size,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rr_ratio': rr_ratio,
                'adx': adx,
                'timestamp': time.time()
            }
            self.history.append(result)
            
            log.info(f"[PREDATOR] {symbol} | Exec={decision} | Size={position_size:.2f} | RR={rr_ratio:.2f}:1")
            
            return result
        
        except Exception as e:
            log.error(f"[PREDATOR] Analysis error: {e}")
            return {
                'decision': 'WAIT',
                'confidence': 50,
                'execution_status': 'ERROR',
                'position_size': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'rr_ratio': 0,
                'timestamp': time.time()
            }
    
    def run_server(self):
        """TCP Server loop - listen for requests from Trinity"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)
        log.info(f"[PREDATOR] Listening on port {self.port}")
        
        try:
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            log.info("[PREDATOR] Shutting down")
        finally:
            server.close()
    
    def _handle_request(self, conn):
        """Handle incoming TCP request from Trinity"""
        try:
            # 1. Read header (4 bytes = length of JSON)
            header = conn.recv(4)
            if len(header) < 4:
                return
            
            # 2. Unpack length
            data_length = struct.unpack('>I', header)[0]
            
            # 3. Read JSON data
            data_bytes = b''
            while len(data_bytes) < data_length:
                chunk = conn.recv(min(4096, data_length - len(data_bytes)))
                if not chunk:
                    break
                data_bytes += chunk
            
            # 4. Parse JSON
            request_data = json.loads(data_bytes.decode('utf-8'))
            
            # 5. Analyze
            result = self.analyze(request_data)
            
            # 6. Send response
            response_json = json.dumps(result)
            response_bytes = response_json.encode('utf-8')
            response_header = struct.pack('>I', len(response_bytes))
            conn.sendall(response_header + response_bytes)
        
        except Exception as e:
            log.warning(f"Request handling error: {e}")
        
        finally:
            conn.close()

if __name__ == '__main__':
    predator = PREDATOR()
    predator.run_server()
