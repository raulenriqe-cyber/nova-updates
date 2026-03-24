#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ NOVA TRADING AI - LLM7 OCULUS                           ║
║                      Data Quality Validator v1.0                             ║
║                                                                              ║
║  Valida integridad de datos antes de cada decisión de trading                ║
║  Detecta anomalías, gaps, discontinuidades en precios y volumen              ║
║  Calcula quality_score para dar confianza al consenso                        ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Edition: Scalping AI | M1/M5 Optimization                                   ║
║  Port: 8763 (TCP Server) | Pure Python | Low Latency                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, struct, json, logging, threading, time
import numpy as np
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🔍 LLM7_OCULUS | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

class OCULUS:
    """
    ✨ NOVA LLM7 - OCULUS (Data Quality Validator)
    
    Responsabilidades:
    - Valida estructura y rangos de datos recibidos de mercado
    - Detecta anomalías (gaps, spikes, discontinuidades)
    - Calcula quality_score (0-100%) para cada tick
    - Genera APPROVE/CAUTION/REJECT basado en integridad
    - Protege al sistema de datos corruptos o incompletos
    
    Estrategia:
    1. Validación de estructura (OHLC, volumen, timestamp)
    2. Validación de rangos (precios, indicadores)
    3. Detección de anomalías (price jumps, gaps)
    4. Scoring determinístico sin IA
    5. Rápido (<50ms por análisis)
    
    Autor: Polaricelabs 2026
    """
    
    def __init__(self):
        self.port = 8763  # CNHUSD LLM7 OCULUS
        self.history = deque(maxlen=100)  # Store last 100 validations
        self.data_quality_threshold = 70  # ADJUSTED: Lower for M1 scalping (was 80)
        log.info("[OCULUS] \u2728 Data Quality Validator initialized (Port 8763 CNHUSD)")
        log.info("[OCULUS] 🔍 Scanning for data anomalies and discontinuities")
        log.info("[OCULUS] ⚡ Pure Python | <50ms latency | Scalping optimized")
    
    def _check_data_integrity(self, data):
        """Validate data structure and value ranges
        
        🔴 FIX: Trinity sends indicators at root level ('rsi', 'adx') AND
        closes as 'prices' (not 'closes'). Also check nested paths.
        """
        checks = {
            'price_valid': False,
            'indicators_valid': False,
            'ohlc_valid': False,
            'volume_valid': False,
            'timestamp_valid': False,
        }
        
        try:
            # 1. Check price
            price = float(data.get('price', data.get('current_price', 0)))
            checks['price_valid'] = 0 < price < 1_000_000  # Reasonable range
            
            # 2. Check indicators - try root level AND nested path
            ind = data.get('indicators', {})
            if isinstance(ind, dict):
                current = ind.get('current', ind)  # Try nested 'current' or flat
            else:
                current = {}
            adx = float(data.get('adx', current.get('adx', 0)))
            rsi = float(data.get('rsi', current.get('rsi', 0)))
            checks['indicators_valid'] = (0 < adx <= 100) and (0 < rsi <= 100)
            
            # 3. Check OHLC - 🔴 FIX: Trinity sends 'prices' not 'closes'
            closes = data.get('prices', data.get('closes', []))
            if not closes:
                closes = data.get('bar_data', {}).get('closes', [])
            if not closes:
                closes = data.get('price_data', {}).get('close', [])
            if isinstance(closes, list) and len(closes) >= 10:
                closes_arr = [float(c) for c in closes if c and 0 < float(c) < 1_000_000]
                checks['ohlc_valid'] = len(closes_arr) >= 10
            
            # 4. Check volume - 🔴 FIX: Trinity may not send volumes separately
            volumes = data.get('volumes', [])
            if not volumes:
                candles = data.get('candles', [])
                if candles and isinstance(candles, list):
                    volumes = [c.get('volume', 0) for c in candles if isinstance(c, dict)]
            if isinstance(volumes, list) and len(volumes) > 0:
                vol_arr = [float(v) for v in volumes if v and float(v) > 0]
                checks['volume_valid'] = len(vol_arr) > 0
            else:
                checks['volume_valid'] = True
            
            # 5. Check timestamp
            timestamp = data.get('timestamp', data.get('tick_id', 0))
            checks['timestamp_valid'] = timestamp > 0
            
        except Exception as e:
            log.warning(f"Data integrity check error: {e}")
        
        return checks
    
    def _calculate_data_quality_score(self, data):
        """Calculate overall data quality (0-100) with WEIGHTED scoring
        
        CRITICAL FIX: Different checks have different importance!
        - Price valid: 40% (CRITICAL - without price, nothing works)
        - OHLC valid: 30% (HIGH - needed for patterns/indicators)
        - Indicators valid: 15% (MEDIUM - for confirmation)
        - Volume valid: 10% (LOW - nice to have)
        - Timestamp valid: 5% (LOW - for logging)
        """
        checks = self._check_data_integrity(data)
        
        # WEIGHTED scoring - not all checks are equal!
        weights = {
            'price_valid': 40,      # CRITICAL
            'ohlc_valid': 30,       # HIGH  
            'indicators_valid': 15, # MEDIUM
            'volume_valid': 10,     # LOW
            'timestamp_valid': 5,   # LOW
        }
        
        weighted_score = 0
        for check_name, passed in checks.items():
            if passed:
                weighted_score += weights.get(check_name, 0)
        
        # Ensure score is in 0-100 range
        score = max(0, min(100, int(weighted_score)))
        
        log.debug(f"[OCULUS] Weighted quality: {score}% (checks: {checks})")
        
        return score
    
    def _detect_anomalies(self, data):
        """Detect data anomalies that might affect trading"""
        anomalies = []
        
        try:
            price = float(data.get('price', 0))
            closes = data.get('closes', [])
            
            if closes and len(closes) >= 2:
                closes_arr = [float(c) for c in closes if c and c > 0]
                if len(closes_arr) >= 2:
                    # Check for price jump (sudden spike)
                    price_change_pct = abs((closes_arr[-1] - closes_arr[-2]) / closes_arr[-2] * 100)
                    if price_change_pct > 5:  # More than 5% jump
                        anomalies.append(f"PRICE_JUMP_{price_change_pct:.1f}%")
                    
                    # Check for gap (live price vs last close)
                    if abs(price - closes_arr[-1]) / closes_arr[-1] * 100 > 2:
                        anomalies.append("POSSIBLE_GAP")
            
            # Check for missing data
            if not data.get('closes') or len(data.get('closes', [])) < 10:
                anomalies.append("INSUFFICIENT_HISTORY")
        
        except Exception as e:
            log.debug(f"Anomaly detection error: {e}")
        
        return anomalies
    
    def analyze(self, data):
        """Main analysis method - validate data quality"""
        try:
            symbol = data.get('symbol', 'CNHUSD')
            
            # Calculate quality score
            quality_score = self._calculate_data_quality_score(data)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(data)
            
            # Decision based on quality
            if quality_score >= self.data_quality_threshold:
                decision = 'APPROVE'
                confidence = min(95, quality_score + 10)
            else:
                decision = 'REJECT'
                confidence = 100 - quality_score
            
            # If anomalies detected, downgrade confidence
            if anomalies:
                decision = 'CAUTION'
                confidence = max(40, quality_score - 20)
            
            # Store in history
            result = {
                'decision': decision,
                'confidence': confidence,
                'quality_score': quality_score,
                'anomalies': anomalies,
                'timestamp': time.time()
            }
            self.history.append(result)
            
            log.info(f"[OCULUS] {symbol} | Quality={quality_score}% | Decision={decision} | Anomalies={len(anomalies)}")
            
            return result
        
        except Exception as e:
            log.error(f"[OCULUS] Analysis error: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 50,
                'quality_score': 50,
                'anomalies': ['ERROR'],
                'timestamp': time.time()
            }
    
    def run_server(self):
        """TCP Server loop - listen for requests from Trinity"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)
        log.info(f"[OCULUS] Listening on port {self.port}")
        
        try:
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            log.info("[OCULUS] Shutting down")
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
    oculus = OCULUS()
    oculus.run_server()
