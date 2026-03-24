#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - LLM3 SUPREME GUARDIAN                ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Pattern Recognition + Harmonic Detection + Candlestick Analysis             ║
║  Port: 5558 (TCP Server) - MATHEMATICAL PRECISION ENHANCED                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import socket
import struct
import json
import logging
import threading
import time
import yaml
import numpy as np
from datetime import datetime

# 🎯 Mathematical Precision: Enhanced pattern correlation
PATTERN_CORRELATION_THRESHOLD = 0.85  # Swiss precision for pattern matching
CANDLESTICK_ACCURACY_FACTOR = 0.92   # Mathematical accuracy requirement
HARMONIC_RATIO_TOLERANCE = 0.02      # Fibonacci ratio precision tolerance

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
logging.basicConfig(
    level=logging.INFO,  # IMPROVED: Changed from DEBUG to INFO (less verbose, better performance)
    format='%(asctime)s | LLM3 v17.03 | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('LLM3')

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
# PATTERN GUARDIAN - PATTERN DETECTION LOGIC
# ============================================================
class PatternGuardian:
    """Detector de patrones y generador de decisiones"""
    
    def __init__(self):
        self.min_confidence = 40
        self.confidence_base = 0.5
    
    def analyze_request(self, request):
        """
        BUGFIX #84: LLM3 MARKET CONTEXT ANALYSIS - INDEPENDENT
        
        LLM3 es el contexto - entiende:
        - Estructura de tendencia (HH/HL/LL/LH)
        - Niveles de soporte/resistencia dinámicos
        - Zonas de liquidez
        - Cambios de régimen
        
        Retorna decisión INDEPENDIENTE basada en contexto.
        """
        try:
            symbol = request.get('symbol', 'XAUUSD').upper().strip()
            current_price = self._safe_float(request.get('current_price', request.get('price', 0)))
            
            # Extraer datos históricos CON VALIDACIÓN
            bar_data = request.get('bar_data', {})
            # FIX CRITICAL: was `if h` which filters out 0/0.0 values AND desynchronizes arrays
            # Use `if h is not None` to only filter actual None values
            highs = [self._safe_float(h) for h in bar_data.get('highs', []) if h is not None]
            lows = [self._safe_float(l) for l in bar_data.get('lows', []) if l is not None]
            closes = [self._safe_float(c) for c in bar_data.get('closes', []) if c is not None]
            opens = [self._safe_float(o) for o in bar_data.get('opens', closes) if o is not None]
            volumes = [self._safe_float(v) for v in bar_data.get('volumes', [1.0]*len(closes)) if v is not None]
            
            # DEBUG: Log received data for diagnostics
            log.info(f"[LLM3 RX] price={current_price:.2f}, closes={len(closes)}, highs={len(highs)}, lows={len(lows)}")
            
            # BUGFIX #CRITICAL: Ensure data is valid - prevent crashes on empty/malformed data
            if len(closes) == 0 or len(highs) == 0 or len(lows) == 0:
                return {
                    'decision': 'HOLD',
                    'confidence': 40,
                    'reason': 'Invalid or empty data received',
                    'pattern': 'ERROR'
                }
            
            # Si no hay datos, usar indicadores como fallback
            if len(closes) < 10:
                indicators = request.get('indicators', {})
                rsi = self._safe_float(indicators.get('rsi', 50))
                adx = self._safe_float(indicators.get('adx', 20))
                atr_pips = self._safe_float(indicators.get('atr_pips', 10))
                
                # MOMENTUM FALLBACK: Seguir la dirección del mercado
                prices = closes if closes else [0]
                price_mom = prices[-1] - prices[-5] if len(prices) >= 5 else 0
                
                if rsi > 50 and price_mom > 0:
                    return {
                        'decision': 'BUY',
                        'confidence': 65,
                        'reason': f'RSI {rsi:.0f} + Momentum UP - Context BULLISH',
                        'pattern': 'MOMENTUM_UP',
                        'context_type': 'FALLBACK'
                    }
                elif rsi < 50 and price_mom < 0:
                    return {
                        'decision': 'SELL',
                        'confidence': 65,
                        'reason': f'RSI {rsi:.0f} + Momentum DOWN - Context BEARISH',
                        'pattern': 'MOMENTUM_DOWN',
                        'context_type': 'FALLBACK'
                    }
                else:
                    return {
                        'decision': 'HOLD',
                        'confidence': 40,
                        'reason': 'Neutral context - Waiting for clarity',
                        'pattern': 'NEUTRAL',
                        'context_type': 'FALLBACK'
                    }
            
            # ================================================================
            # CONTEXT ANALYSIS - INDEPENDENT (no longer waits for prior_analysis)
            # ================================================================
            prior = request.get('prior_analysis', {})  # ← FIX: Define prior from request
            prior_boost = 0.0  # Will be calculated from chart structure, not external data
            prior_reasons = []
            
            # ================================================================
            # ANÁLISIS PROFUNDO DE CONTEXTO (LLM3 OWN ANALYSIS)
            # ================================================================
            
            # NIVEL 1: ESTRUCTURA DE TENDENCIA
            structure = self._analyze_structure(highs, lows, closes)
            
            # NIVEL 2: SOPORTE/RESISTENCIA DINÁMICO
            support_resistance = self._find_dynamic_sr(highs, lows, closes, current_price)
            
            # NIVEL 3: ZONAS DE LIQUIDEZ
            liquidity_zones = self._identify_liquidity_zones(highs, lows, closes)
            
            # NIVEL 4: RÉGIMEN DE MERCADO
            regime = self._identify_regime(highs, lows, closes)
            
            # ================================================================
            # MEMORIA INTERNA - Analizar propios datos sin depender de otros LLMs
            # ================================================================
            memory_score = 0
            memory_reasons = []
            
            # ════════════════════════════════════════════════════════════════
            # 🎯 ADVANCED STRUCTURE: Higher Highs/Lower Lows Detection
            # 🔧 FIX 2026-02-19: Expanded to 30 bars + proper pivot detection + pullback zone
            # Was: 10 bars with crude max/min chunks → Now: proper N-bar pivots + Fibonacci zones
            # ════════════════════════════════════════════════════════════════
            if len(closes) >= 20:
                # Use up to 40 bars for macro context (was 10 — too narrow like a microscope)
                lookback = min(40, len(closes))
                recent_highs = highs[-lookback:]
                recent_lows = lows[-lookback:]
                recent_closes = closes[-lookback:]
                
                # PROPER SWING DETECTION: 2-bar pivot (confirmed by 2 bars each side)
                pivot_highs = []  # (relative_index, price)
                pivot_lows = []
                for i in range(2, lookback - 2):
                    if (recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and
                        recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]):
                        pivot_highs.append((i, recent_highs[i]))
                    if (recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and
                        recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]):
                        pivot_lows.append((i, recent_lows[i]))
                
                if len(pivot_highs) >= 2 and len(pivot_lows) >= 2:
                    sh_prev, sh_last = pivot_highs[-2], pivot_highs[-1]
                    sl_prev, sl_last = pivot_lows[-2], pivot_lows[-1]
                    
                    is_hh = sh_last[1] > sh_prev[1]
                    is_hl = sl_last[1] > sl_prev[1]
                    is_lh = sh_last[1] < sh_prev[1]
                    is_ll = sl_last[1] < sl_prev[1]
                    
                    # 🧠 STRUCTURE TYPE + PULLBACK DETECTION
                    if is_hh and is_hl:
                        memory_score += 1.2
                        memory_reasons.append("HH+HL★")
                        memory_reasons.append("Struct:BULL")
                        
                        # 🧠 PULLBACK DETECTION: If price is pulling back toward Fib zone, BUY is optimal
                        move_range = sh_last[1] - sl_last[1]
                        if move_range > 0:
                            fib_382 = sh_last[1] - move_range * 0.382
                            fib_618 = sh_last[1] - move_range * 0.618
                            if fib_618 <= current_price <= fib_382:
                                memory_score += 1.5  # HUGE boost for pullback entry
                                memory_reasons.append(f"PULLBACK_ZONE★★")
                            elif current_price > sh_last[1]:
                                memory_score -= 0.8  # At/above HH — NOT a good BUY
                                memory_reasons.append("AT_HH_NO_BUY")
                            elif current_price < fib_618:
                                memory_score -= 0.5  # Deep retracement — trend might fail
                                memory_reasons.append("DEEP_RETRACE")
                    
                    elif is_lh and is_ll:
                        memory_score -= 1.2
                        memory_reasons.append("LH+LL★")
                        memory_reasons.append("Struct:BEAR")
                        
                        # 🧠 PULLBACK DETECTION: If price is bouncing toward Fib zone, SELL is optimal
                        move_range = sh_last[1] - sl_last[1]
                        if move_range > 0:
                            fib_382 = sl_last[1] + move_range * 0.382
                            fib_618 = sl_last[1] + move_range * 0.618
                            if fib_382 <= current_price <= fib_618:
                                memory_score -= 1.5  # HUGE boost for pullback SELL
                                memory_reasons.append(f"PULLBACK_ZONE★★")
                            elif current_price < sl_last[1]:
                                memory_score += 0.8  # At/below LL — NOT a good SELL
                                memory_reasons.append("AT_LL_NO_SELL")
                            elif current_price > fib_618:
                                memory_score += 0.5  # Deep bounce — trend might fail
                                memory_reasons.append("DEEP_BOUNCE")
                    
                    elif is_hh and is_ll:
                        memory_reasons.append("Struct:EXPAND")
                    elif is_lh and is_hl:
                        memory_reasons.append("Struct:SQUEEZE")
                    else:
                        memory_reasons.append("Struct:MIXED")
                else:
                    # Not enough pivots — use fallback with consecutive closes
                    if len(recent_closes) >= 3 and recent_closes[-1] > recent_closes[-2] > recent_closes[-3]:
                        memory_score += 0.6
                        memory_reasons.append("ConsecUp")
                        memory_reasons.append("Struct:BULL")
                    elif len(recent_closes) >= 3 and recent_closes[-1] < recent_closes[-2] < recent_closes[-3]:
                        memory_score -= 0.6
                        memory_reasons.append("ConsecDn")
                        memory_reasons.append("Struct:BEAR")
            elif len(closes) >= 10:
                # Minimal fallback for very short data
                recent_closes = closes[-10:]
                if recent_closes[-1] > recent_closes[-2] > recent_closes[-3]:
                    memory_score += 0.6
                    memory_reasons.append("ConsecUp")
                elif recent_closes[-1] < recent_closes[-2] < recent_closes[-3]:
                    memory_score -= 0.6
                    memory_reasons.append("ConsecDn")
            
            # ════════════════════════════════════════════════════════════════════
            # 🌟 LLM5 SUPREME CONTEXT INTEGRATION - INTELIGENCIA MEJORADA
            # LLM5 provee contexto MAESTRO para que LLM3 tome mejores decisiones
            # ════════════════════════════════════════════════════════════════════
            llm5_patterns = prior.get('llm5_top_patterns', [])  # FIXED: correct key
            llm5_bullish = prior.get('llm5_bullish_points', 0)  # Puntos, no count
            llm5_bearish = prior.get('llm5_bearish_points', 0)
            llm5_signal = prior.get('llm5_signal_direction', 'NEUTRAL')
            llm5_strength = prior.get('llm5_signal_strength', 0)
            llm5_confidence = prior.get('llm5_signal_confidence', 0)
            llm5_momentum = prior.get('llm5_momentum_score', 0)
            llm5_regime = prior.get('llm5_volatility_regime', {})
            llm5_recommendation = prior.get('llm5_recommendation_for_llm3', '')
            
            # ═══ INTELIGENCIA 1: Usar señal directa de LLM5 con peso proporcional ═══
            if llm5_signal == 'UP' and llm5_confidence > 0.5:
                boost = 0.5 + (llm5_confidence * 0.8)  # 0.5-1.3 según confianza
                memory_score += boost
                memory_reasons.append(f"LLM5↑({llm5_confidence:.0%})")
            elif llm5_signal == 'DOWN' and llm5_confidence > 0.5:
                boost = 0.5 + (llm5_confidence * 0.8)
                memory_score -= boost
                memory_reasons.append(f"LLM5↓({llm5_confidence:.0%})")
            
            # ═══ INTELIGENCIA 2: Momentum Score de LLM5 (ESCALA: -100 a +100) ═══
            # BUGFIX: Normalizar de -100..+100 a -1..+1 para compatibilidad
            normalized_momentum = llm5_momentum / 100.0 if abs(llm5_momentum) > 1 else llm5_momentum
            if abs(normalized_momentum) > 0.3:
                momentum_boost = normalized_momentum * 0.5  # ±0.15 a ±0.5
                memory_score += momentum_boost
                memory_reasons.append(f"LLM5_Mom({normalized_momentum:+.2f})")
            
            # ═══ INTELIGENCIA 3: Régimen de volatilidad para ajustar thresholds ═══
            regime_type = llm5_regime.get('regime', 'NORMAL') if isinstance(llm5_regime, dict) else 'NORMAL'
            if regime_type == 'COMPRESSING':
                # Squeeze = esperar breakout, más conservador
                memory_reasons.append("LLM5:Squeeze")
            elif regime_type == 'EXPANDING':
                # Tendencia fuerte, más agresivo
                if llm5_signal in ['UP', 'DOWN']:
                    memory_score *= 1.1  # 10% más peso en tendencia
                    memory_reasons.append("LLM5:Expand↑")
            
            # ═══ INTELIGENCIA 4: Patrones de alta confianza de LLM5 ═══
            for pattern in llm5_patterns[:5]:
                pconf = pattern.get('confidence', 0)
                pname = pattern.get('pattern', pattern.get('name', ''))
                direction = pattern.get('expected_direction', '')
                points = pattern.get('points', 5)
                
                if pconf > 0.75 and points >= 7:
                    if direction == 'UP' or 'BULL' in pname.upper() or 'HAMMER' in pname.upper():
                        memory_score += 0.4 * pconf
                        memory_reasons.append(f"LLM5:{pname[:12]}★")
                    elif direction == 'DOWN' or 'BEAR' in pname.upper() or 'ENGULFING_BEAR' in pname.upper():
                        memory_score -= 0.4 * pconf
                        memory_reasons.append(f"LLM5:{pname[:12]}★")
            
            # ═══ INTELIGENCIA 5: Recomendación específica de LLM5 para LLM3 ═══
            if llm5_recommendation:
                memory_reasons.append(f"LLM5_Rec:{llm5_recommendation[:20]}")
            
            # ═══ INTELIGENCIA 6: Balance de puntos bull/bear (ESCALA: 0-100) ═══
            point_diff = llm5_bullish - llm5_bearish  # Rango: -100 a +100
            if abs(point_diff) >= 20:  # Diferencia significativa (20%+)
                point_boost = point_diff * 0.01  # ±0.2 a ±1.0 según diferencia
                memory_score += point_boost
                memory_reasons.append(f"LLM5_Pts({point_diff:+.0f})")
            
            log.debug(f"[LLM5 CONTEXT] Signal:{llm5_signal}@{llm5_confidence:.0%} Mom:{normalized_momentum:+.2f} Regime:{regime_type} Patterns:{len(llm5_patterns)}")
            
            # ================================================================
            # 🧠 DEEP CHART INTELLIGENCE - Candle + Volume + Trap Analysis
            # LLM3 ahora VE las velas de verdad: tamaños, wicks, trampas
            # ================================================================
            chart_intel_score = 0
            chart_intel_reasons = []
            
            if len(closes) >= 5:
                # ═══ CANDLE MORPHOLOGY ANALYSIS ═══
                atr_est = sum(h - l for h, l in zip(highs[-14:], lows[-14:])) / min(14, len(highs)) if len(highs) >= 2 else 1.0
                
                for i in range(-3, 0):
                    if abs(i) > len(closes) or abs(i) > len(opens):
                        continue
                    o = opens[i] if i + len(opens) >= 0 else closes[i]
                    c, h, l = closes[i], highs[i], lows[i]
                    rng = h - l
                    if rng <= 0:
                        continue
                    body = abs(c - o)
                    body_pct = body / rng
                    upper_wick = (h - max(o, c)) / rng
                    lower_wick = (min(o, c) - l) / rng
                    is_bull = c > o
                    
                    if i == -1:  # Última vela = más importante
                        # MARUBOZU (>85% body): Momentum puro, sin duda
                        if body_pct > 0.85:
                            if is_bull:
                                chart_intel_score += 1.5
                                chart_intel_reasons.append("MARUBOZU_BULL★")
                            else:
                                chart_intel_score -= 1.5
                                chart_intel_reasons.append("MARUBOZU_BEAR★")
                        
                        # DOJI (<15% body): Indecisión total
                        elif body_pct < 0.15:
                            chart_intel_score *= 0.5  # Reducir confianza
                            chart_intel_reasons.append("DOJI_INDECISION")
                        
                        # PIN BAR / HAMMER: Rechazo claro
                        if lower_wick > 0.6 and body_pct < 0.3:
                            chart_intel_score += 1.2  # Rechazo bajista = señal alcista
                            chart_intel_reasons.append(f"HAMMER({lower_wick:.0%})")
                        elif upper_wick > 0.6 and body_pct < 0.3:
                            chart_intel_score -= 1.2  # Rechazo alcista = señal bajista
                            chart_intel_reasons.append(f"SHOOTING_STAR({upper_wick:.0%})")
                        
                        # CANDLE SIZE vs ATR
                        if atr_est > 0:
                            size_ratio = rng / atr_est
                            if size_ratio > 1.8:
                                # Vela expansiva = movimiento institucional
                                if body_pct > 0.5:
                                    mult = 1.3 if is_bull else -1.3
                                    chart_intel_score += mult
                                    chart_intel_reasons.append(f"INSTITUTIONAL({size_ratio:.1f}xATR)")
                                else:
                                    chart_intel_reasons.append(f"VOLATILE_REJECT({size_ratio:.1f}xATR)")
                            elif size_ratio < 0.25:
                                chart_intel_reasons.append("MICRO_NOISE")
                
                # ═══ ENGULFING DETECTION ═══
                if len(opens) >= 2:
                    prev_o, prev_c = opens[-2], closes[-2]
                    curr_o, curr_c = opens[-1], closes[-1]
                    
                    # Bullish Engulfing: vela actual envuelve a la anterior
                    if prev_c < prev_o and curr_c > curr_o:  # Bear then Bull
                        if curr_c > prev_o and curr_o < prev_c:
                            chart_intel_score += 2.0
                            chart_intel_reasons.append("ENGULFING_BULL★★")
                    
                    # Bearish Engulfing
                    if prev_c > prev_o and curr_c < curr_o:  # Bull then Bear
                        if curr_c < prev_o and curr_o > prev_c:
                            chart_intel_score -= 2.0
                            chart_intel_reasons.append("ENGULFING_BEAR★★")
                
                # ═══ BULL/BEAR TRAP DETECTION ═══
                if len(highs) >= 5 and len(opens) >= 1:
                    recent_high = max(highs[-5:-1])
                    recent_low = min(lows[-5:-1])
                    
                    # BULL TRAP: Breaks high but closes bearish
                    if highs[-1] > recent_high and closes[-1] < opens[-1]:
                        trap_size = (highs[-1] - recent_high) / atr_est if atr_est > 0 else 0
                        if trap_size > 0.1:
                            chart_intel_score -= 2.5
                            chart_intel_reasons.append(f"🪤BULL_TRAP({trap_size:.2f})")
                    
                    # BEAR TRAP: Breaks low but closes bullish  
                    if lows[-1] < recent_low and closes[-1] > opens[-1]:
                        trap_size = (recent_low - lows[-1]) / atr_est if atr_est > 0 else 0
                        if trap_size > 0.1:
                            chart_intel_score += 2.5
                            chart_intel_reasons.append(f"🪤BEAR_TRAP({trap_size:.2f})")
                
                # ═══ BODY TREND (4/5 same direction = clear trend) ═══
                if len(opens) >= 5:
                    bull_count = sum(1 for i in range(-5, 0) if closes[i] > opens[i])
                    bear_count = 5 - bull_count
                    if bull_count >= 4:
                        chart_intel_score += 1.0
                        chart_intel_reasons.append(f"BODY_UP({bull_count}/5)")
                    elif bear_count >= 4:
                        chart_intel_score -= 1.0
                        chart_intel_reasons.append(f"BODY_DN({bear_count}/5)")
                
                # ═══ VOLUME ANALYSIS ═══
                if len(volumes) >= 5 and any(v > 0 for v in volumes[-5:]):
                    avg_vol = sum(volumes[-5:]) / 5
                    if avg_vol > 0:
                        vol_ratio = volumes[-1] / avg_vol
                        if vol_ratio > 2.0 and len(opens) >= 1:
                            # High volume + directional candle = confirmation
                            if closes[-1] > opens[-1]:
                                chart_intel_score += 0.8
                                chart_intel_reasons.append(f"VOL_BULL({vol_ratio:.1f}x)")
                            else:
                                chart_intel_score -= 0.8
                                chart_intel_reasons.append(f"VOL_BEAR({vol_ratio:.1f}x)")
                        elif vol_ratio > 3.5:
                            chart_intel_reasons.append(f"CLIMAX_VOL({vol_ratio:.1f}x)")
                
                # Cap chart intelligence score
                chart_intel_score = max(-5.0, min(5.0, chart_intel_score))
                
                if chart_intel_reasons:
                    log.info(f"[🧠 CHART_INTEL] Score={chart_intel_score:+.1f} | {', '.join(chart_intel_reasons)}")
            
            # ================================================================
            # SÍNTESIS: DECISIÓN BASADA EN CONTEXTO + PRIOR ANALYSIS
            # ================================================================
            
            context_score = prior_boost + memory_score + chart_intel_score  # 🧠 Include chart intelligence
            reason_parts = (prior_reasons + memory_reasons + chart_intel_reasons).copy()
            
            # Contribución: Estructura (MEJORADO: Detección de patrones armónicos)
            # Harmonic patterns = mayor confiabilidad en reversiones
            harmonic_boost = 0
            if len(closes) >= 5:
                # AB=CD pattern detector (simplified)
                recent_prices = closes[-5:]
                if (recent_prices[0] < recent_prices[1] > recent_prices[2] < recent_prices[3] > recent_prices[4]):
                    harmonic_boost = 0.5  # Alternating pattern = consolidación + breakout prep
            
            if structure['trend'] == 'UPTREND':
                context_score += 1.2 + harmonic_boost  # IMPROVE: was 1, now 1.2 +harmonic
                reason_parts.append(f"Structure:{structure['trend']}★")
            elif structure['trend'] == 'DOWNTREND':
                # 🔴 CRITICAL FIX: DOWNTREND should subtract MORE to balance BUY bias
                # Was: -1.2, Now: -1.5 to properly detect SELL signals
                context_score -= 1.5 + harmonic_boost  # FIX: Increased magnitude to detect SELL properly
                reason_parts.append(f"Structure:{structure['trend']}★")
            
            # Contribución: Soporte/Resistencia (MEJORADO: +1.0 cuando activo)
            if support_resistance['near_support']:
                context_score += 1.0
                reason_parts.append(f"Support@{support_resistance['support']:.0f}")
            elif support_resistance['near_resistance']:
                context_score -= 1.0
                reason_parts.append(f"Resistance@{support_resistance['resistance']:.0f}")
            
            # Contribución: Liquidez (MEJORADO: +0.7 cuando en zona)
            if liquidity_zones['in_zone']:
                zone_type = liquidity_zones['zone_type']
                if zone_type == 'SUPPORT':
                    context_score += 0.7  # IMPROVE: was 0.5, now 0.7
                elif zone_type == 'RESISTANCE':
                    context_score -= 0.7
                reason_parts.append(f"Liq:{zone_type}")
            
            # Contribución: Régimen (MEJORADO: +1.0 cuando trending claro)
            if regime['type'] == 'TRENDING_UP':
                context_score += 1.0
                reason_parts.append(f"Regime:{regime['type']}↑")
            elif regime['type'] == 'TRENDING_DOWN':
                context_score -= 1.0
                reason_parts.append(f"Regime:{regime['type']}↓")
            elif regime['type'] == 'RANGING':
                context_score += 0.2  # Small boost for identified ranging (not uncertain)
                reason_parts.append(f"Regime:RANGING")
            
            # Decisión final basada en score - THRESHOLDS BALANCEADOS
            # 🔴 BUGFIX #85: Symmetric thresholds for BUY/SELL balance
            # Was: if score >= 1.0: BUY, elif score <= -1.0: SELL
            # Now: if score >= 1.3: BUY, elif score <= -1.3: SELL (symmetric)
            
            # 🏦 BANK-GRADE: RSI override for extreme conditions
            indicators = request.get('indicators', {})
            if isinstance(indicators, dict) and 'current' in indicators:
                indicators = indicators.get('current', {})
            rsi = self._safe_float(indicators.get('rsi', request.get('rsi', 50)))
            adx = self._safe_float(indicators.get('adx', 20))  # 🔧 BUGFIX: Define ADX early (used in decision logic below)
            
            # 🧠 MOMENTUM-BASED OVERRIDE: Solo operar cuando indicadores CONFIRMAN la dirección
            # Calcular momentum del precio
            price_mom_5 = closes[-1] - closes[-5] if len(closes) >= 5 else 0
            
            # 🧠 CRITICAL VALIDATION: Context score must STRONGLY support direction
            # NO adivinar - solo operar cuando context_score es CLARO
            # BUY requires: context_score >= +2.0 (strong bullish context)
            # SELL requires: context_score <= -2.0 (strong bearish context)
            # HOLD if: -2.0 < context_score < +2.0 (unclear/ranging)
            
            if context_score >= 2.0:
                # Strong bullish context - allow BUY if RSI not extreme
                if rsi < 75 and adx > 22:
                    decision = 'BUY'
                    confidence = min(88.0, 60.0 + (rsi - 50) * 0.4)
                    pattern = 'MOMENTUM_UP'
                    reason = f'Context:{context_score:.1f}+ RSI:{rsi:.0f} ADX:{adx:.0f} | {" | ".join(reason_parts)}' if reason_parts else f'Strong bullish context'
                    log.info(f"[LLM3] 🟢 STRONG BULLISH CONTEXT (ctx={context_score:.1f}, RSI={rsi:.1f}, ADX={adx:.0f}) → BUY")
                else:
                    decision = 'HOLD'
                    confidence = 55.0
                    pattern = 'HOLD_RSI_EXTREME'
                    reason = f'Context bullish but RSI={rsi:.0f} extreme or ADX={adx:.0f} weak'
            elif context_score <= -2.0:
                # Strong bearish context - allow SELL if RSI not extreme
                if rsi > 25 and adx > 22:
                    decision = 'SELL'
                    confidence = min(88.0, 60.0 + (50 - rsi) * 0.4)
                    pattern = 'MOMENTUM_DOWN'
                    reason = f'Context:{context_score:.1f}- RSI:{rsi:.0f} ADX:{adx:.0f} | {" | ".join(reason_parts)}' if reason_parts else f'Strong bearish context'
                    log.info(f"[LLM3] 🔴 STRONG BEARISH CONTEXT (ctx={context_score:.1f}, RSI={rsi:.1f}, ADX={adx:.0f}) → SELL")
                else:
                    decision = 'HOLD'
                    confidence = 55.0
                    pattern = 'HOLD_RSI_EXTREME'
                    reason = f'Context bearish but RSI={rsi:.0f} extreme or ADX={adx:.0f} weak'
            # RSI > 60 + momentum > 0.5 + context > 0.8 + ADX > 25 = BUY (momentum override)
            # FIX: Was SELL (inverted logic - comment said BUY)
            elif rsi > 60 and price_mom_5 > 0.5 and context_score >= 0.8 and adx > 25:
                decision = 'BUY'
                confidence = min(88.0, 60.0 + (rsi - 50) * 0.4)
                pattern = 'MOMENTUM_UP'
                reason = f'RSI strong ({rsi:.0f}) + Momentum UP + Context {context_score:.1f} + ADX {adx:.0f} | {" | ".join(reason_parts)}' if reason_parts else f'Momentum UP'
                log.info(f"[LLM3] 🟢 MOMENTUM UP (RSI={rsi:.1f}, mom={price_mom_5:.2f}, ctx={context_score:.1f}, ADX={adx:.0f}) → BUY")
            elif context_score >= 1.5:  # BUY threshold raised (was 1.3)
                decision = 'BUY'
                confidence = min(91.0, 55.0 + context_score * 12.0)
                pattern = 'BULLISH_CONTEXT'
                reason = " | ".join(reason_parts) if reason_parts else f"Context bullish (score={context_score:.1f})"
            elif context_score <= -1.5:  # SELL threshold raised (was -1.3)
                decision = 'SELL'
                confidence = min(91.0, 55.0 + abs(context_score) * 12.0)
                pattern = 'BEARISH_CONTEXT'
                reason = " | ".join(reason_parts) if reason_parts else f"Context bearish (score={context_score:.1f})"
            else:
                decision = 'HOLD'
                # IMPROVED: HOLD confidence varies from 30-60% based on how close to threshold
                # Higher score = more likely to break out, so higher confidence in current HOLD
                hold_confidence = 30.0 + abs(context_score) * 23.0  # Range: 30-60%
                confidence = min(60.0, hold_confidence)
                pattern = 'NEUTRAL_CONTEXT'
                reason = " | ".join(reason_parts) if reason_parts else f"Context neutral (score={context_score:.1f})"
            
            # ===== ADX FILTER: Precision entries based on trend strength =====
            # adx already defined above (line ~343)
            adx_trending = adx > 25  # Market has trend
            adx_strong = adx > 35    # Strong directional movement
            
            # Apply ADX-based confidence multiplier
            if decision in ('BUY', 'SELL'):
                if adx_strong:
                    # Strong trend: boost confidence for trend-following entries
                    confidence = min(95.0, confidence * 1.15)
                    log.debug(f"[LLM3] ADX={adx:.1f} STRONG → conf boost 1.15x")
                elif adx_trending:
                    # Normal trend: slight boost
                    confidence = min(92.0, confidence * 1.08)
                    log.debug(f"[LLM3] ADX={adx:.1f} trending → conf boost 1.08x")
                else:
                    # Ranging market: reduce confidence (choppy = risky entries)
                    confidence = confidence * 0.80
                    log.debug(f"[LLM3] ADX={adx:.1f} RANGING → conf reduced 0.80x")
            
            # ===== DIAGNOSTIC TRACER =====
            if DIAGNOSTICS_ENABLED and TRACER:
                TRACER.log_llm_decision(
                    llm_name="LLM3",
                    genome=request,
                    decision=decision,
                    confidence=confidence,
                    reasoning=f"ContextScore:{context_score:.1f} Structure:{structure['trend']} Zone:{liquidity_zones['zone_type']} Regime:{regime['type']} ADX:{adx:.1f}"
                )
                if DASHBOARD:
                    DASHBOARD.broadcast_llm_vote("LLM3", decision, confidence)
            
            return {
                'decision': decision,
                'confidence': confidence,
                'reason': reason,
                'pattern': pattern,
                'context_analysis': {
                    'structure': structure,
                    'support_resistance': support_resistance,
                    'liquidity': liquidity_zones,
                    'regime': regime,
                    'context_score': context_score
                }
            }
            
        except Exception as e:
            log.error(f"[CRITICAL] LLM3 analysis error: {str(e)[:100]}")
            # SAFE FALLBACK: HOLD (no capital arriesgado)
            # On error, wait for reliable data instead of buying blindly
            return {
                'decision': 'HOLD',
                'confidence': 35,
                'reason': f'Analysis error occurred, entering safe mode: {str(e)[:50]}',
                'pattern': 'ERROR_HOLD',
                'error_details': str(e)[:100]
            }
    
    # ================================================================
    # MÉTODOS DE ANÁLISIS DE CONTEXTO
    # ================================================================
    
    def _analyze_structure(self, highs, lows, closes):
        """🔧 FIX 2026-02-19: Proper swing pivot detection with 30-bar window + Fib zones
        Was: crude max/min of 5-bar chunks (10 minutes = microscope view)
        Now: N-bar pivot highs/lows across 30-bar window (30 min = macro context)"""
        if len(closes) < 15:
            return {'trend': 'UNKNOWN', 'strength': 0}
        
        # Use 30 bars (was 10)
        lookback = min(30, len(closes))
        h = highs[-lookback:]
        l = lows[-lookback:]
        
        # Proper 2-bar pivot detection
        pivot_highs = []
        pivot_lows = []
        for i in range(2, lookback - 2):
            if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
                pivot_highs.append(h[i])
            if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
                pivot_lows.append(l[i])
        
        if len(pivot_highs) >= 2 and len(pivot_lows) >= 2:
            hh = pivot_highs[-1] > pivot_highs[-2]
            hl = pivot_lows[-1] > pivot_lows[-2]
            lh = pivot_highs[-1] < pivot_highs[-2]
            ll = pivot_lows[-1] < pivot_lows[-2]
            
            if hh and hl:
                trend = 'UPTREND'
            elif lh and ll:
                trend = 'DOWNTREND'
            elif hh and ll:
                trend = 'EXPANDING'
            elif lh and hl:
                trend = 'CONTRACTING'
            else:
                trend = 'SIDEWAYS'
        else:
            # Fallback to simple comparison
            recent_high = max(h[-5:])
            recent_low = min(l[-5:])
            prior_high = max(h[:len(h)//2]) if len(h) >= 10 else recent_high
            prior_low = min(l[:len(l)//2]) if len(l) >= 10 else recent_low
            
            if recent_high > prior_high and recent_low > prior_low:
                trend = 'UPTREND'
            elif recent_high < prior_high and recent_low < prior_low:
                trend = 'DOWNTREND'
            else:
                trend = 'SIDEWAYS'
            pivot_highs = [max(h[-5:]), max(h[:len(h)//2])]
            pivot_lows = [min(l[-5:]), min(l[:len(l)//2])]
        
        return {
            'trend': trend,
            'recent_high': pivot_highs[-1] if pivot_highs else max(h[-5:]),
            'recent_low': pivot_lows[-1] if pivot_lows else min(l[-5:]),
            'pivot_highs': pivot_highs,
            'pivot_lows': pivot_lows,
            'strength': 'STRONG' if len(pivot_highs) >= 3 else 'WEAK'
        }
    
    def _find_dynamic_sr(self, highs, lows, closes, current_price):
        """Encuentra soporte/resistencia dinámico"""
        if len(closes) < 20:
            return {'near_support': False, 'near_resistance': False, 'support': 0, 'resistance': 0}
        
        # Soporte: nivel de precio previo donde hubo compra
        support = min(lows[-20:])
        
        # Resistencia: nivel previo donde hubo venta
        resistance = max(highs[-20:])
        
        price_range = resistance - support
        distance_to_support = current_price - support
        distance_to_resistance = resistance - current_price
        
        near_support = distance_to_support < price_range * 0.1
        near_resistance = distance_to_resistance < price_range * 0.1
        
        return {
            'support': support,
            'resistance': resistance,
            'near_support': near_support,
            'near_resistance': near_resistance,
            'distance_to_support_pct': (distance_to_support / price_range * 100) if price_range > 0 else 0
        }
    
    def _identify_liquidity_zones(self, highs, lows, closes):
        """Identifica zonas de liquidez donde se acumuló volumen"""
        if len(closes) < 30:
            return {'in_zone': False, 'zone_type': 'UNKNOWN'}
        
        # Zona simple: donde el precio se consolidó (low volatility area)
        recent_volatility = np.std(closes[-10:])
        historical_volatility = np.std(closes[-30:-10]) if len(closes) > 30 else recent_volatility
        
        if recent_volatility < historical_volatility * 0.7:
            # Baja volatilidad = zona de liquidez
            zone_price = np.mean(closes[-10:])
            current = closes[-1]
            
            # FIX: was inverted - price above mean was labeled RESISTANCE (bearish)
            # In an uptrend, price above mean is SUPPORT (bullish acceptance zone)
            if current > np.mean(closes[-30:]):
                zone_type = 'SUPPORT'   # Price found acceptance above mean
            else:
                zone_type = 'RESISTANCE'  # Price below mean = resistance overhead
            
            in_zone = abs(current - zone_price) < recent_volatility * 2
            
            return {
                'in_zone': in_zone,
                'zone_type': zone_type,
                'zone_price': zone_price
            }
        else:
            return {'in_zone': False, 'zone_type': 'VOLATILE'}
    
    def _identify_regime(self, highs, lows, closes):
        """Identifica régimen de mercado"""
        if len(closes) < 20:
            return {'type': 'UNKNOWN', 'strength': 0}
        
        # ADX simplificado
        recent_closes = closes[-20:]
        momentum = np.mean(np.diff(recent_closes))
        volatility = np.std(recent_closes)
        
        # FIX: operator precedence bug - was `volatility > (X if len>50 else False)` 
        # which becomes `volatility > 0` when len<=50 (always True for XAUUSD)
        if len(closes) > 50 and volatility > np.std(closes[-50:]) * 1.5:
            regime_type = 'VOLATILE'
        elif momentum > 0:
            regime_type = 'TRENDING_UP'
        elif momentum < 0:
            regime_type = 'TRENDING_DOWN'
        else:
            regime_type = 'RANGING'
        
        return {
            'type': regime_type,
            'momentum': momentum,
            'volatility': volatility
        }
    
    def _safe_float(self, value):
        """Convierte valor a float de forma segura"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0


# ============================================================
# TCP SERVER - ROBUST IMPLEMENTATION
# ============================================================
class LLM3Server:
    """
    Servidor TCP robusto para LLM3.
    GARANTIZADO: Nunca desconecta abruptamente, siempre responde.
    """
    
    def __init__(self, host='127.0.0.1', port=5558):  # FIXED: LLM3 is 5558
        self.host = host
        self.port = port
        self.guardian = PatternGuardian()
        self.running = True
        self.client_count = 0
        self.response_count = 0
        self.error_count = 0
        
        # Lock para thread-safety
        self.stats_lock = threading.Lock()
    
    def _print_nova_banner(self):
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
{Y}|{R}  {Y}████╗  ██║{W}██╔═══██╗██║   ██║██╔══██╗{R}   {C}LLM3 GUARDIAN{R}       {Y}|{R}
{Y}|{R}  {Y}██╔██╗ ██║{W}██║   ██║██║   ██║███████║{R}   {D}Supreme Protector{R}   {Y}|{R}
{Y}|{R}  {Y}██║╚██╗██║{W}██║   ██║╚██╗ ██╔╝██╔══██║{R}                       {Y}|{R}
{Y}|{R}  {Y}██║ ╚████║{W}╚██████╔╝ ╚████╔╝ ██║  ██║{R}                       {Y}|{R}
{Y}|{R}  {Y}╚═╝  ╚═══╝{W} ╚═════╝   ╚═══╝  ╚═╝  ╚═╝{R}                       {Y}|{R}
{Y}|{R}                                                              {Y}|{R}
{Y}+{'-'*62}+{R}
{Y}|{R}  {W}XAUUSD Scalping Edition{R}      {D}by Polarice Labs © 2026{R}       {Y}|{R}
{Y}|{R}  {G}● PORT: {self.port}{R}                  {D}Whale/Sweep Detection{R}    {Y}|{R}
{Y}+{'='*62}+{R}
""")
    
    def start(self):
        """Inicia servidor - NUNCA falla"""
        # Mostrar banner NOVA
        self._print_nova_banner()
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512 * 1024)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512 * 1024)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)
            
            log.info(f"LLM3 SUPREME GUARDIAN v17.03 Active on {self.host}:{self.port}")
            log.info("   (Press Ctrl+C to stop)")
            
            while self.running:
                try:
                    client_socket, client_addr = server_socket.accept()
                    
                    # Incrementar contador
                    with self.stats_lock:
                        self.client_count += 1
                    
                    log.info(f"✓ Client #{self.client_count} connected from {client_addr[0]}:{client_addr[1]}")
                    
                    # Manejar en thread
                    handler = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_addr),
                        daemon=True,
                        name=f"LLM3-Handler-{self.client_count}"
                    )
                    handler.start()
                
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    log.info("Stopping server...")
                    self.running = False
                except Exception as e:
                    log.error(f"Server accept error: {e}")
                    break
        
        except Exception as e:
            log.critical(f"Failed to start server: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
            log.info(f"Server stopped. Stats: {self.client_count} clients, {self.response_count} responses, {self.error_count} errors")
    
    def _handle_client(self, client_socket, client_addr):
        """
        Maneja cliente - PERSISTENT CONNECTION
        
        IMPORTANTE: Mantiene socket abierto para múltiples requests
        Trinity reutiliza el mismo socket para varias consultas
        """
        log.debug(f"[CLIENT] New connection from {client_addr}")
        
        # Configurar socket
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        try:
            while True:  # LOOP INFINITO para conexión persistente
                response_sent = False
                
                try:
                    client_socket.settimeout(60.0)  # BUGFIX #80: Aumentado a 60s (Trinity tarda entre requests)
                    
                    # ==================== LEER HEADER ====================
                    try:
                        log.debug(f"[CLIENT] Waiting for header from {client_addr}")
                        header_data = client_socket.recv(4)
                        
                        # PING/ACK heartbeat support
                        if header_data and b'PING' in header_data:
                            pong_msg = struct.pack('>I', 4) + b'PONG'
                            client_socket.sendall(pong_msg)
                            log.debug(f"[PING] Responded to {client_addr}")
                            continue  # Wait for next message
                        
                        if not header_data or len(header_data) != 4:
                            log.debug(f"[CLIENT] Connection closed by {client_addr} (empty header)")
                            break  # Cliente cerró conexión
                        
                        msg_length = struct.unpack('>I', header_data)[0]
                        log.debug(f"[CLIENT] Message length: {msg_length} bytes from {client_addr}")
                        
                        # Validar tamaño
                        if msg_length <= 0 or msg_length > 5 * 1024 * 1024:
                            log.warning(f"[CLIENT] Invalid message size: {msg_length} from {client_addr}")
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': f'Invalid message size: {msg_length}',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                            continue  # Esperar siguiente request
                    
                    except socket.timeout:
                        log.debug(f"[CLIENT] Timeout reading header from {client_addr} - closing")
                        break  # Cliente no envía más requests
                    
                    except Exception as e:
                        log.error(f"[CLIENT] Header read error from {client_addr}: {type(e).__name__}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Header read error',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        break
                    
                    # ==================== LEER PAYLOAD ====================
                    try:
                        log.debug(f"[CLIENT] Reading {msg_length} bytes from {client_addr}")
                        payload = b''
                        remaining = msg_length
                        
                        while remaining > 0:
                            chunk_size = min(4096, remaining)
                            chunk = client_socket.recv(chunk_size)
                            
                            if not chunk:
                                log.warning(f"[CLIENT] Connection closed during payload read from {client_addr}")
                                if not response_sent:
                                    self._send_response(client_socket, {
                                        'decision': 'HOLD',
                                        'confidence': 40,
                                        'reason': 'Connection closed during read',
                                        'pattern': 'ERROR'
                                    })
                                    response_sent = True
                                break
                            
                            payload += chunk
                            remaining -= len(chunk)
                        
                        if not chunk:
                            break  # Cliente desconectó
                        
                        log.debug(f"[CLIENT] Complete payload: {len(payload)} bytes from {client_addr}")
                    
                    except socket.timeout:
                        log.warning(f"[CLIENT] Timeout reading payload from {client_addr}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Payload read timeout',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        break
                    
                    except Exception as e:
                        log.error(f"[CLIENT] Payload read error from {client_addr}: {type(e).__name__}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Payload read error',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        break
                    
                    # ==================== PARSEAR JSON ====================
                    try:
                        log.debug(f"[CLIENT] Parsing JSON from {client_addr}")
                        request = json.loads(payload.decode('utf-8'))
                        log.debug(f"[CLIENT] Parsed: action={request.get('action')} from {client_addr}")
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        log.error(f"[CLIENT] JSON parse error from {client_addr}: {e}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Invalid JSON',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        continue  # Esperar siguiente request
                    
                    except Exception as e:
                        log.error(f"[CLIENT] Decode error from {client_addr}: {type(e).__name__}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Decode error',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        continue
                    
                    # ==================== ANALIZAR Y RESPONDER ====================
                    try:
                        log.debug(f"[CLIENT] Analyzing request from {client_addr}")
                        response = self.guardian.analyze_request(request)
                        log.debug(f"[CLIENT] Decision: {response.get('decision')} from {client_addr}")
                        self._send_response(client_socket, response)
                        response_sent = True
                        # CONTINUE esperando siguiente request en el while loop
                    
                    except Exception as e:
                        log.error(f"[CLIENT] Analysis error from {client_addr}: {type(e).__name__}")
                        if not response_sent:
                            self._send_response(client_socket, {
                                'decision': 'HOLD',
                                'confidence': 40,
                                'reason': 'Analysis error',
                                'pattern': 'ERROR'
                            })
                            response_sent = True
                        continue
                
                except Exception as e:
                    log.error(f"[CLIENT] Unexpected error from {client_addr}: {type(e).__name__}: {e}")
                    break
        
        except Exception as e:
            log.error(f"[CLIENT] Fatal error from {client_addr}: {type(e).__name__}: {e}")
        
        finally:
            log.debug(f"[CLIENT] Closing connection from {client_addr}")
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                client_socket.close()
            except:
                pass
            log.debug(f"[CLIENT] Connection closed from {client_addr}")
    
    def _send_response(self, client_socket, response):
        """
        Envía respuesta JSON al cliente.
        GARANTIZADO: No lanza excepción
        """
        try:
            # Asegurar que response tiene todos los keys necesarios
            safe_response = {
                'decision': response.get('decision', 'HOLD'),
                'confidence': int(response.get('confidence', 40)),
                'reason': str(response.get('reason', 'N/A'))[:100],
                'pattern': str(response.get('pattern', 'UNKNOWN'))[:50]
            }
            
            response_bytes = json.dumps(safe_response).encode('utf-8')
            header = struct.pack('>I', len(response_bytes))
            
            log.debug(f"[SEND] Preparing response: {len(response_bytes)} bytes, decision={safe_response['decision']}")
            
            # Enviar con timeout corto
            client_socket.settimeout(5.0)
            client_socket.sendall(header + response_bytes)
            
            log.debug(f"[SEND] Response sent successfully: {safe_response['decision']}")
            
            with self.stats_lock:
                self.response_count += 1
        
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
            # Cliente desconectó - es normal, no loguear como error
            log.warning(f"[SEND] Client disconnected before send: {type(e).__name__}")
            with self.stats_lock:
                self.error_count += 1
        
        except Exception as e:
            log.error(f"[SEND] Response send error: {type(e).__name__}: {e}")
            with self.stats_lock:
                self.error_count += 1


# ============================================================
# ENTRY POINT
# ============================================================
def main():
    """Punto de entrada"""
    try:
        # Cargar config
        port = 5558  # LLM3 is on 5558
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f) or {}
            port = config.get('llm_settings', {}).get('llm3_port', 5558)
        except:
            pass
        
        # Iniciar servidor
        server = LLM3Server(port=port)
        server.start()
    
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    except Exception as e:
        log.critical(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
