#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ NOVA TRADING AI - LLM8 CHRONOS                          ║
║                       Timing Optimizer v1.0                                  ║
║                                                                              ║
║  Detecta confluencias temporales y puntos de entrada óptimos                 ║
║  Identifica cuando múltiples indicadores convergen en el mismo punto         ║
║  Calcula timing_multiplier para ajustar tamaño de posición                   ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Edition: Scalping AI | M1/M5 Optimization                                   ║
║  Port: 5563 (TCP Server) | Pure Python | Low Latency                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, struct, json, logging, threading, time
import numpy as np
from datetime import datetime, timezone
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
        self.port = 5563
        self.history = deque(maxlen=100)
        log.info("[CHRONOS] ✨ Timing Optimizer initialized (Port 5563)")
        log.info("[CHRONOS] ⏰ Detecting temporal confluences + SESSION AWARENESS")
        log.info("[CHRONOS] ⚡ Pure Python | <50ms latency | Scalping optimized")
    
    # ════════════════════════════════════════════════════════════════════════
    # 🕐 SESSION AWARENESS — The #1 missing intelligence for XAUUSD timing
    # XAUUSD is most liquid and directional during London/NY overlap
    # ════════════════════════════════════════════════════════════════════════
    
    def _get_session_timing_score(self):
        """
        Calculate timing score based on REAL market session times (UTC).
        
        XAUUSD Session Map:
        - 00:00-07:00 UTC = Asian session (low liquidity, wide spreads, fakeouts)
        - 07:00-08:00 UTC = Pre-London (positioning)
        - 08:00-12:00 UTC = London session (high liquidity, directional)
        - 12:00-16:00 UTC = London/NY overlap (PEAK liquidity, strongest moves)
        - 13:30-14:00 UTC = NY open (volatility spike, news releases)
        - 16:00-20:00 UTC = NY afternoon (declining volume)
        - 20:00-00:00 UTC = Evening (low activity, avoid)
        
        Returns: (session_score, session_name, session_warning)
        """
        try:
            now = datetime.now(timezone.utc)
            hour = now.hour + now.minute / 60.0
            weekday = now.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
            
            # Weekend — no trading
            if weekday >= 5:
                return -30, 'WEEKEND', 'Market closed'
            
            # Friday after 20:00 UTC — weekend gap risk
            if weekday == 4 and hour >= 20.0:
                return -20, 'FRIDAY_CLOSE', 'Weekend gap risk'
            
            # Monday before 08:00 — thin liquidity, gap risk
            if weekday == 0 and hour < 8.0:
                return -10, 'MONDAY_EARLY', 'Thin Monday liquidity'
            
            # Session scoring
            if 12.0 <= hour < 16.0:
                return 25, 'LONDON_NY_OVERLAP', 'PEAK trading window'
            elif 8.0 <= hour < 12.0:
                return 15, 'LONDON_ACTIVE', 'London session active'
            elif 13.5 <= hour < 14.0:
                return 10, 'NY_OPEN', 'NY open volatility spike'
            elif 16.0 <= hour < 20.0:
                return 5, 'NY_AFTERNOON', 'Declining NY volume'
            elif 7.0 <= hour < 8.0:
                return 0, 'PRE_LONDON', 'Pre-London positioning'
            elif 0.0 <= hour < 7.0:
                return -15, 'ASIAN_SESSION', 'Low liquidity, wide spreads'
            else:
                return -10, 'OFF_HOURS', 'Low activity period'
        except Exception as e:
            log.warning(f"[CHRONOS] Session detection error: {e}")
            return 0, 'UNKNOWN', 'Session detection failed'
    
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
    
    def _detect_market_phase(self, data):
        """
        🧠 INTELIGENCIA DE FASES: Detecta cuál es la FASE actual del mercado
        Similar a LLM1 pero enfocado en TIMING
        
        Returns: 'BREAKOUT' | 'ACCUMULATION' | 'DISTRIBUTION' | 'CONSOLIDATION' | 'UNCLEAR'
        """
        try:
            # Extract indicators
            ind = self._extract_indicators(data)
            rsi = float(ind.get('rsi', 50))
            adx = float(ind.get('adx', 20))
            macd = float(ind.get('macd_histogram', ind.get('macd', 0)))
            
            # Get price data — ⭐ FIX: Trinity sends 'prices' and 'bar_data.closes', NOT 'price_data.close'
            closes = data.get('prices', data.get('bar_data', {}).get('closes', []))
            if isinstance(closes, list):
                closes = [float(c) for c in closes if c and float(c) > 0]
            
            if len(closes) < 10:
                return 'UNCLEAR'
            
            # Analizar últimas 10 velas
            recent_closes = closes[-10:]
            price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100
            
            # Calcular volatilidad (desviación estándar)
            volatility = np.std(recent_closes) / np.mean(recent_closes) * 100
            
            # FASE 1: BREAKOUT (ADX alto + dirección clara + volatilidad alta)
            if adx > 35 and abs(price_change) > 0.3 and volatility > 0.15:
                if macd > 0:
                    return 'BREAKOUT_UP'  # Breakout alcista
                else:
                    return 'BREAKOUT_DOWN'  # Breakout bajista
            
            # FASE 2: ACCUMULATION (RSI bajo + ADX bajo + precio lateral/bajando)
            elif rsi < 40 and adx < 30 and abs(price_change) < 0.2:
                return 'ACCUMULATION'
            
            # FASE 3: DISTRIBUTION (RSI alto + ADX bajo + precio lateral/subiendo)
            elif rsi > 60 and adx < 30 and abs(price_change) < 0.2:
                return 'DISTRIBUTION'
            
            # FASE 4: CONSOLIDATION (baja volatilidad + ADX bajo + sin dirección)
            elif volatility < 0.1 and adx < 25 and abs(price_change) < 0.15:
                return 'CONSOLIDATION'
            
            # FASE 5: TRENDING (ADX medio-alto + dirección)
            elif adx > 25 and abs(price_change) > 0.15:
                if macd > 0:
                    return 'TRENDING_UP'
                else:
                    return 'TRENDING_DOWN'
            
            else:
                return 'UNCLEAR'
        
        except Exception as e:
            log.debug(f"Market phase detection error: {e}")
            return 'UNCLEAR'
    
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
            # XAUUSD FIX: lowered threshold 0.5→0.2 (XAU MACD often 0.2-0.5 range)
            if abs(macd) > 0.2 and abs(obv_slope) > 0.2:
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
            
            # Confluence 4: Any trend present - XAU FIX
            # Without this, CONSOLIDATION phase always gives confluences=[] → WAITING.
            # ADX>=15 means directional bias exists — valid entry timing.
            if adx >= 15:
                confluences.append('TREND_ACTIVE')
        
        except Exception as e:
            log.debug(f"Confluence detection error: {e}")
        
        return confluences
    
    def _analyze_candle_patterns(self, data):
        """
        CANDLE PATTERN ANALYSIS - FIX: Now returns DIRECTIONAL boost
        Bullish patterns add positive boost, bearish patterns add negative boost
        
        Returns: (pattern_boost, pattern_names)
            pattern_boost: -25 to +25 (negative=bearish, positive=bullish)
            pattern_names: List of detected patterns
        """
        try:
            # Extract OHLC from candles or bar_data
            candles = data.get('candles', [])
            bar_data = data.get('bar_data', {})
            
            if candles and len(candles) >= 3:
                closes = [c.get('close', 0) for c in candles[-3:]]
                opens = [c.get('open', 0) for c in candles[-3:]]
                highs = [c.get('high', 0) for c in candles[-3:]]
                lows = [c.get('low', 0) for c in candles[-3:]]
            elif bar_data:
                closes = bar_data.get('closes', [])[-3:] if bar_data.get('closes') else []
                opens = bar_data.get('opens', [])[-3:] if bar_data.get('opens') else []
                highs = bar_data.get('highs', [])[-3:] if bar_data.get('highs') else []
                lows = bar_data.get('lows', [])[-3:] if bar_data.get('lows') else []
            else:
                return 0, []
            
            if len(closes) < 2 or not all([closes, opens, highs, lows]):
                return 0, []
            
            pattern_boost = 0
            patterns = []
            
            if len(closes) >= 2:
                prev_close = closes[-2]
                prev_open = opens[-2]
                prev_high = highs[-2]
                prev_low = lows[-2]
                
                curr_close = closes[-1]
                curr_open = opens[-1]
                curr_high = highs[-1]
                curr_low = lows[-1]
                
                prev_body = abs(prev_close - prev_open)
                curr_body = abs(curr_close - curr_open)
                prev_range = prev_high - prev_low
                curr_range = curr_high - curr_low
                
                upper_wick = curr_high - max(curr_close, curr_open)
                lower_wick = min(curr_close, curr_open) - curr_low
                
                # ENGULFING BULLISH → POSITIVE boost (bullish signal)
                if prev_close < prev_open and curr_close > curr_open:
                    if curr_open <= prev_close and curr_close >= prev_open:
                        pattern_boost += 15
                        patterns.append('ENGULFING_BULLISH')
                
                # ENGULFING BEARISH → NEGATIVE boost (bearish signal)
                elif prev_close > prev_open and curr_close < curr_open:
                    if curr_open >= prev_close and curr_close <= prev_open:
                        pattern_boost -= 15  # FIX: was +15 (direction blind)
                        patterns.append('ENGULFING_BEARISH')
                
                # HAMMER → POSITIVE (bullish reversal)
                if curr_body > 0 and curr_range > 0:
                    body_ratio = curr_body / curr_range
                    if lower_wick > curr_body * 2 and upper_wick < curr_body * 0.5 and body_ratio < 0.3:
                        pattern_boost += 12
                        patterns.append('HAMMER')
                
                # SHOOTING STAR → NEGATIVE (bearish reversal)
                if curr_body > 0 and curr_range > 0:
                    body_ratio = curr_body / curr_range
                    if upper_wick > curr_body * 2 and lower_wick < curr_body * 0.5 and body_ratio < 0.3:
                        pattern_boost -= 12  # FIX: was +12 (direction blind)
                        patterns.append('SHOOTING_STAR')
                
                # DOJI → ZERO (indecision should NOT boost timing confidence)
                if curr_range > 0:
                    body_ratio = curr_body / curr_range
                    if body_ratio < 0.1:
                        # FIX: was +8, but indecision = BAD timing, not good
                        pattern_boost -= 5  # Slight penalty for indecision
                        patterns.append('DOJI')
                
                # THREE UP → POSITIVE (strong bullish)
                if len(closes) >= 3:
                    if closes[-1] > closes[-2] > closes[-3] and curr_close > curr_open:
                        pattern_boost += 10
                        patterns.append('THREE_UP')
                
                # THREE DOWN → NEGATIVE (strong bearish)
                if len(closes) >= 3:
                    if closes[-1] < closes[-2] < closes[-3] and curr_close < curr_open:
                        pattern_boost -= 10  # FIX: was +10 (direction blind)
                        patterns.append('THREE_DOWN')
                
                # MARUBOZU → direction depends on color
                if curr_range > 0:
                    wick_ratio = (upper_wick + lower_wick) / curr_range
                    if wick_ratio < 0.15 and curr_body / curr_range > 0.8:
                        if curr_close > curr_open:
                            pattern_boost += 13  # Bullish marubozu
                        else:
                            pattern_boost -= 13  # Bearish marubozu
                        patterns.append('MARUBOZU')
            
            # Clamp to ±25
            pattern_boost = max(-25, min(25, pattern_boost))
            
            return pattern_boost, patterns
        
        except Exception as e:
            log.debug(f"Candle pattern analysis error: {e}")
            return 0, []
    
    def _calculate_timing_score(self, data):
        """🎯 ADVANCED: Timing quality with momentum acceleration analysis"""
        score = 50  # Neutral baseline
        
        try:
            # 🔴 FIX: Extract indicators from nested structure
            ind = self._extract_indicators(data)
            
            rsi = float(ind.get('rsi', 50))
            adx = float(ind.get('adx', 20))
            macd = float(ind.get('macd_histogram', ind.get('macd', 0)))
            # ⭐ FIX: Trinity sends 'prices' and 'bar_data.closes', NOT 'price_data.close'
            closes = data.get('prices', data.get('bar_data', {}).get('closes', []))
            if isinstance(closes, list):
                closes = [float(c) for c in closes if c and float(c) > 0]
            
            # ════════════════════════════════════════════════════════════════
            # 🧠 ADVANCED: RSI with MOMENTUM DIVERGENCE detection
            # ════════════════════════════════════════════════════════════════
            # RSI extremes are best, BUT check if diverging with price
            if len(closes) >= 10:
                price_change = (closes[-1] - closes[-5]) / closes[-5] * 100
                
                # RSI extreme + price moving opposite = DIVERGENCE (extra strong)
                if rsi <= 25 and price_change < -0.1:
                    rsi_component = 35  # Oversold + falling = perfect buy setup
                elif rsi >= 75 and price_change > 0.1:
                    rsi_component = 35  # Overbought + rising = perfect sell setup
                # RSI extreme alone
                elif rsi <= 30 or rsi >= 70:
                    rsi_component = 28
                elif rsi <= 35 or rsi >= 65:
                    rsi_component = 20
                elif rsi <= 40 or rsi >= 60:
                    rsi_component = 12
                # XAU FIX: Credit for near-neutral RSI (was 0 for RSI 40-60)
                elif rsi <= 45 or rsi >= 55:
                    rsi_component = 8
                elif rsi <= 48 or rsi >= 52:
                    rsi_component = 4
                else:
                    rsi_component = 2  # Always give base score (was 0)
            else:
                # Fallback without divergence detection
                if rsi <= 30 or rsi >= 70:
                    rsi_component = 28
                elif rsi <= 35 or rsi >= 65:
                    rsi_component = 20
                elif rsi <= 45 or rsi >= 55:
                    rsi_component = 8
                else:
                    rsi_component = 5
            
            # ════════════════════════════════════════════════════════════════
            # 🧠 ADVANCED: ADX with ACCELERATION (trend strengthening?)
            # ════════════════════════════════════════════════════════════════
            # Get previous ADX to detect acceleration
            prev_adx = float(data.get('prev_adx', adx))
            adx_accel = adx - prev_adx  # Positive = trend strengthening
            
            if adx >= 40:
                adx_component = 28 if adx_accel > 0 else 25  # Strong trend
            elif adx >= 28:
                adx_component = 18 if adx_accel > 0 else 15  # Developing trend
            elif adx >= 20:
                adx_component = 10 if adx_accel > 0 else 8   # Weak trend (was >=22)
            elif adx >= 15:
                adx_component = 6 if adx_accel > 0 else 4    # XAU FIX: 15-20 bracket
            else:
                adx_component = 2  # Near-flat (was 3)
            
            # ════════════════════════════════════════════════════════════════
            # 🧠 ADVANCED: MACD with HISTOGRAM EXPANSION
            # ════════════════════════════════════════════════════════════════
            prev_macd = float(data.get('prev_macd_histogram', macd))
            macd_expanding = abs(macd) > abs(prev_macd)  # Histogram expanding?
            
            abs_macd = abs(macd)
            if abs_macd > 1.8:
                macd_component = 20 if macd_expanding else 15
            elif abs_macd > 1.0:
                macd_component = 15 if macd_expanding else 12
            elif abs_macd > 0.5:
                macd_component = 10 if macd_expanding else 8
            else:
                macd_component = 5
            
            score = 15 + rsi_component + adx_component + macd_component
            score = max(20, min(98, score))  # Clamp 20-98
        
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
        """Main analysis method - detect timing confluences + candle patterns + SESSION AWARENESS"""
        try:
            symbol = data.get('symbol', 'XAUUSD')
            
            # 🕐 NEW: Get REAL session timing score
            session_score, session_name, session_warning = self._get_session_timing_score()
            
            # 🧠 Detectar fase del mercado primero
            market_phase = self._detect_market_phase(data)
            
            # Detect confluences
            confluences = self._detect_time_confluences(data)
            
            # 🕯️ NUEVO: Analizar patrones de velas
            candle_boost, candle_patterns = self._analyze_candle_patterns(data)
            
            # Calculate timing score with IMPROVED formula
            timing_score = self._calculate_timing_score(data)
            
            # 🧠 NUEVO: Ajustar timing score según FASE del mercado
            phase_boost = 0
            if market_phase in ['BREAKOUT_UP', 'BREAKOUT_DOWN']:
                phase_boost = 15  # Breakout = timing perfecto
                timing_score += phase_boost
                log.info(f"[CHRONOS] 🚀 {market_phase} detected - timing boosted +{phase_boost}")
            
            elif market_phase in ['ACCUMULATION', 'DISTRIBUTION']:
                if len(confluences) >= 2:
                    phase_boost = 10  # Buena fase + confluencias = timing bueno
                    timing_score += phase_boost
                    log.info(f"[CHRONOS] 📊 {market_phase} + confluences - timing boosted +{phase_boost}")
            
            elif market_phase == 'CONSOLIDATION':
                phase_boost = -20  # Consolidación = mal timing
                timing_score += phase_boost
                log.info(f"[CHRONOS] ⚠️ CONSOLIDATION - timing reduced {phase_boost}")
            
            # Apply candle pattern boost
            # ⭐ FIX: Strong directional patterns (abs>=10) boost timing quality
            # Small/indecision patterns (DOJI=-5) penalize timing quality (keep sign)
            if candle_boost != 0:
                if abs(candle_boost) >= 10:
                    timing_score += abs(candle_boost)  # Strong pattern = good timing
                else:
                    timing_score += candle_boost  # DOJI/weak = bad timing (negative)
            
            # 🕐 NEW: Apply session timing score — THE key intelligence upgrade
            timing_score += session_score
            if session_score < -10:
                log.warning(f"[CHRONOS] ⚠️ {session_name}: {session_warning} (penalty: {session_score})")
            elif session_score > 10:
                log.info(f"[CHRONOS] 🎯 {session_name}: {session_warning} (boost: +{session_score})")
            
            # Clamp timing score
            timing_score = max(20, min(98, timing_score))
            
            # Decision logic based on confluences AND phase AND candle patterns
            total_signals = len(confluences) + len(candle_patterns)
            
            if total_signals >= 3 and market_phase in ['BREAKOUT_UP', 'BREAKOUT_DOWN', 'TRENDING_UP', 'TRENDING_DOWN']:
                decision = 'READY'
                confidence = min(95, timing_score + 10)
            elif total_signals >= 2 and market_phase not in ['CONSOLIDATION', 'UNCLEAR']:
                decision = 'READY'
                confidence = min(90, timing_score + 5)
            elif total_signals >= 2 and market_phase in ['CONSOLIDATION', 'UNCLEAR']:
                # XAU FIX: CONSOLIDATION + 2 confluences → PREPARING (not WAITING)
                # HMM CONSOLIDATION fires too often at ADX 20-30, incorrectly blocking
                decision = 'PREPARING'
                confidence = max(50, timing_score)
            elif total_signals >= 1 and market_phase not in ['CONSOLIDATION', 'UNCLEAR']:
                decision = 'PREPARING'
                confidence = max(50, timing_score)  # XAU FIX: floor at 50
            else:
                decision = 'WAITING'
                # Floor at 30 so WAITING isn't catastrophic (was 20)
                confidence = max(30, timing_score - 10)
            
            # Timing multiplier with EXPANDED range (0.5x - 2.0x)
            timing_multiplier = self._calculate_timing_multiplier(timing_score)
            
            result = {
                'decision': decision,
                'confidence': confidence,
                'timing_score': timing_score,
                'confluences': confluences,
                'candle_patterns': candle_patterns,
                'candle_direction': 'BULLISH' if candle_boost > 0 else 'BEARISH' if candle_boost < 0 else 'NEUTRAL',
                'timing_multiplier': timing_multiplier,
                'market_phase': market_phase,
                # 🕐 NEW: Session awareness data
                'session_name': session_name,
                'session_score': session_score,
                'session_warning': session_warning,
                'timestamp': time.time()
            }
            self.history.append(result)
            
            log.info(f"[CHRONOS] {symbol} | Timing={timing_score}% | Signals={total_signals} (Conf={len(confluences)}, Candles={len(candle_patterns)}) | Mult={timing_multiplier:.2f}x")
            
            return result
        
        except Exception as e:
            log.error(f"[CHRONOS] Analysis error: {e}")
            return {
                'decision': 'WAITING',
                'confidence': 50,
                'timing_score': 50,
                'confluences': [],
                'candle_patterns': [],
                'timing_multiplier': 1.0,
                'timestamp': time.time()
            }
    
    def run_server(self):
        """TCP Server loop - listen for requests from Trinity"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(5)
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
