#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ NOVA TRADING AI - LLM8 CHRONOS                          ║
║                    USDJPY M15 - Samurai Predator Edition                      ║
║                       Timing Optimizer v1.0                                  ║
║                                                                              ║
║  Detecta confluencias temporales y puntos de entrada óptimos                 ║
║  Identifica cuando múltiples indicadores convergen en el mismo punto         ║
║  Calcula timing_multiplier para ajustar tamaño de posición                   ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Edition: Sniper AI | M15 Optimization                                       ║
║  Port: 7863 (TCP Server) | Pure Python | Low Latency                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
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
    format="%(asctime)s | ⏰ LLM8_CHRONOS | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

class CHRONOS:
    """
    ✨ NOVA LLM8 - CHRONOS (Timing Optimizer)
    
    Responsabilidades:
    - Detecta confluencias en indicadores de timing
    - Identifica zonas RSI extremas (oportunidades)
    - Valida alineación entre MACD y OBV
    - Calcula timing_score (0-100%)
    - Genera timing_multiplier para LLM9 (posición sizing)
    
    Estrategia:
    1. Analiza RSI, MACD, OBV, ADX
    2. Busca confluencias (múltiples indicadores alineados)
    3. Puntúa timing quality
    4. Determina READY/PREPARING/WAITING
    5. Multiplica confianza temporal
    
    Autor: Polaricelabs 2026
    """
    
    def __init__(self):
        self.port = 7864  # USDJPY LLM8 port (fixed: was 7862)
        self.history = deque(maxlen=100)
        log.info("[CHRONOS] ✨ Timing Optimizer initialized (Port 7863 USDJPY)")
        log.info("[CHRONOS] ⏰ Detecting temporal confluences")
        log.info("[CHRONOS] ⚡ Pure Python | <50ms latency | M15 optimized")
    
    def _extract_indicators(self, data):
        """🔴 FIX: Extract indicators from various nested structures
        
        Trinity genome structure: data['indicators']['current']['rsi']
        Also try: data['indicators']['rsi'] and data['rsi']
        """
        indicators = data.get('indicators', {})
        
        # Try nested 'current' structure first (quantum_core format)
        current = indicators.get('current', {})
        if current:
            return current
        
        # Try direct indicators dict
        if indicators and 'rsi' in indicators:
            return indicators
        
        # Fallback to flat data structure
        return data
    
    def _detect_time_confluences(self, data):
        """Detect confluences in timing indicators with TREND AWARENESS"""
        confluences = []
        
        try:
            # 🔴 FIX: Extract indicators from nested structure
            ind = self._extract_indicators(data)
            
            # Get indicators that represent timing
            macd = float(ind.get('macd_histogram', ind.get('macd', 0)))
            obv_slope = float(ind.get('obv_slope', 0))
            rsi = float(ind.get('rsi', 50))
            adx = float(ind.get('adx', 20))
            
            # Confluence 1: MACD + OBV alignment (same direction)
            if abs(macd) > 0.5 and abs(obv_slope) > 0.5:
                if (macd > 0) == (obv_slope > 0):  # Same direction
                    confluences.append('MACD_OBV_ALIGNMENT')
            
            # Confluence 2: RSI reversal zones (extremes)
            # CRITICAL FIX: In strong trends (ADX > 35), RSI extremes are MOMENTUM, not reversal
            # Only mark as reversal zone if trend is weak
            if rsi < 30 or rsi > 70:
                if adx < 35:
                    confluences.append('RSI_EXTREME_ZONE')  # Weak trend = possible reversal
                else:
                    confluences.append('RSI_MOMENTUM_ZONE')  # Strong trend = momentum continuation
            
            # Confluence 3: High momentum
            if abs(macd) > 1.0:
                confluences.append('HIGH_MOMENTUM')
        
        except Exception as e:
            log.debug(f"Confluence detection error: {e}")
        
        return confluences
    
    def _calculate_timing_score(self, data):
        """Calculate timing quality (0-100) with IMPROVED formula"""
        score = 50  # Neutral baseline
        
        try:
            # 🔴 FIX: Extract indicators from nested structure
            ind = self._extract_indicators(data)
            
            rsi = float(ind.get('rsi', 50))
            adx = float(ind.get('adx', 20))
            macd = float(ind.get('macd_histogram', ind.get('macd', 0)))
            
            # ═══════════════════════════════════════════════════════════════
            # USDJPY M15 TIMING OPTIMIZATION
            # ADX y MACD umbrales reducidos para mercado menos volátil
            # ═══════════════════════════════════════════════════════════════
            
            # RSI component: Extremes are VERY good entry points
            # 0-30 or 70-100 = +30 points (reversal zones)
            # 30-40 or 60-70 = +15 points (approaching extremes)  
            # 40-60 = 0 points (neutral zone)
            if rsi <= 25 or rsi >= 75:
                rsi_component = 30  # EXTREME - best entries
            elif rsi <= 35 or rsi >= 65:
                rsi_component = 20  # NEAR EXTREME - good entries
            elif rsi <= 40 or rsi >= 60:
                rsi_component = 10  # APPROACHING - decent
            else:
                rsi_component = 0   # NEUTRAL - wait
            
            # ADX component: USDJPY M15 adjusted thresholds
            # USDJPY típicamente tiene ADX más bajo que gold
            # >30 = +25 points (strong trend for forex)
            # 20-30 = +15 points (trend developing)
            # <20 = 0 points (no trend/ranging)
            if adx >= 30:
                adx_component = 25  # Strong trend for USDJPY
            elif adx >= 20:
                adx_component = 15  # Trend developing
            else:
                adx_component = 5   # Ranging market
            
            # MACD component: USDJPY M15 has smaller MACD values
            # Adjust thresholds for forex pair (typically 10x smaller than gold)
            # |MACD| > 0.0005 = +15 points (strong momentum for forex)
            # |MACD| > 0.0002 = +10 points (moderate)
            # |MACD| <= 0.0002 = +5 points (weak)
            abs_macd = abs(macd)
            if abs_macd > 0.0005:
                macd_component = 15  # Strong USDJPY momentum
            elif abs_macd > 0.0002:
                macd_component = 10  # Moderate momentum
            else:
                macd_component = 5   # Weak momentum
            
            score = 20 + rsi_component + adx_component + macd_component
            score = max(20, min(95, score))  # Clamp 20-95
        
        except Exception as e:
            log.debug(f"Timing score error: {e}")
        
        return int(score)
    
    def _calculate_timing_multiplier(self, timing_score):
        """Calculate timing multiplier with EXPANDED range 0.5x - 2.0x
        
        CRITICAL FIX: Previous range was 0.5-1.5x (too small)
        New range matches LLM9 PREDATOR's 0.3-2.0x for consistency
        
        Formula: mult = 0.5 + ((score - 20) / 80) * 1.5
        - Score 20 -> 0.5x (minimum, weak timing)
        - Score 50 -> 1.0x (neutral)
        - Score 80 -> 1.5x (good timing)
        - Score 95 -> 1.9x (excellent timing)
        """
        # Normalize score from 20-95 range to 0-1
        normalized = max(0, min(1, (timing_score - 20) / 75))
        
        # Map to 0.5-2.0 range
        multiplier = 0.5 + (normalized * 1.5)
        
        return round(multiplier, 2)
    
    def analyze(self, data):
        """Main analysis method - detect timing confluences"""
        try:
            symbol = data.get('symbol', 'USDJPY')
            
            # Detect confluences
            confluences = self._detect_time_confluences(data)
            
            # Calculate timing score with IMPROVED formula
            timing_score = self._calculate_timing_score(data)
            
            # Decision logic based on confluences
            if len(confluences) >= 2:
                decision = 'READY'
                confidence = min(90, timing_score + 15)
            elif len(confluences) >= 1:
                decision = 'PREPARING'
                confidence = timing_score
            else:
                decision = 'WAITING'
                confidence = max(40, timing_score - 20)
            
            # Timing multiplier with EXPANDED range (0.5x - 2.0x)
            timing_multiplier = self._calculate_timing_multiplier(timing_score)
            
            result = {
                'decision': decision,
                'confidence': confidence,
                'timing_score': timing_score,
                'confluences': confluences,
                'timing_multiplier': timing_multiplier,
                'timestamp': time.time()
            }
            self.history.append(result)
            
            log.info(f"[CHRONOS] {symbol} | Timing={timing_score}% | Confluences={len(confluences)} | Mult={timing_multiplier:.2f}x")
            
            return result
        
        except Exception as e:
            log.error(f"[CHRONOS] Analysis error: {e}")
            return {
                'decision': 'WAITING',
                'confidence': 50,
                'timing_score': 50,
                'confluences': [],
                'timing_multiplier': 1.0,
                'timestamp': time.time()
            }
    
    def run_server(self):
        """TCP Server loop - listen for requests from Trinity"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)
        log.info(f"[CHRONOS] Listening on port {self.port}")
        
        try:
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            log.info("[CHRONOS] Shutting down")
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
    chronos = CHRONOS()
    chronos.run_server()
