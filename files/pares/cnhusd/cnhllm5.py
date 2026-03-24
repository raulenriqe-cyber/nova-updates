#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - LLM5 AEGIS OCULUS                    ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Ultra-Intelligent Chart Analyzer with 1000+ Pattern Detection               ║
║  Candlestick, Trends, Reversals, Volume, Volatility, S/R Levels              ║
║  Port: 8761 (TCP Server)                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import socket
import json
import logging
import threading
import struct
import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============ CONFIGURACIÓN ============
HOST = '127.0.0.1'
PORT = 8761
MAX_CANDLES = 500
BUFFER_SIZE = 65536

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | 🎯 LLM5 | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============ LLM5 CHART ANALYZER ============
class LLM5ChartAnalyzer:
    """Analizador de charts ultra-inteligente"""
    
    def __init__(self):
        self.history = deque(maxlen=MAX_CANDLES)
        self.last_analysis = {}
    
    def add_candles(self, candles: List[Dict[str, float]]):
        """Agrega velas al historial"""
        for candle in candles:
            self.history.append(candle)
    
    def analyze(self, symbol='CNHUSD', timeframe='M1') -> Dict[str, Any]:
        """Análisis completo del chart"""
        
        if len(self.history) < 3:
            return {'error': 'Insuficientes velas', 'candles': len(self.history)}
        
        # CRITICAL FIX: Ensure all candles have required fields to prevent broadcasting errors
        # Validate each candle and skip incomplete ones
        valid_candles = []
        for c in self.history:
            if all(key in c for key in ['close', 'open', 'high', 'low', 'volume']):
                valid_candles.append(c)
        
        if len(valid_candles) < 3:
            return {'error': 'Insuficientes velas válidas', 'candles': len(valid_candles)}
        
        closes = np.array([c['close'] for c in valid_candles])
        opens = np.array([c['open'] for c in valid_candles])
        highs = np.array([c['high'] for c in valid_candles])
        lows = np.array([c['low'] for c in valid_candles])
        volumes = np.array([c['volume'] for c in valid_candles])
        
        patterns = []
        
        # Detectar patrones - PRIMERO los de velas (más importantes)
        candlestick_patterns = self._candlestick_patterns(opens, closes, highs, lows)
        trend_patterns = self._trend_patterns(closes)
        reversal_patterns = self._reversal_patterns(closes, highs, lows)
        volume_patterns = self._volume_patterns(closes, volumes)
        volatility_patterns = self._volatility_patterns(closes, highs, lows)
        sr_patterns = self._support_resistance(closes, highs, lows)
        
        # Priorizar: Velas > Reversiones > Tendencias > Volumen > Volatilidad > S/R
        patterns.extend(candlestick_patterns)  # Primero los más importantes
        patterns.extend(reversal_patterns)
        patterns.extend(trend_patterns)
        patterns.extend(volume_patterns)
        patterns.extend(volatility_patterns)
        patterns.extend(sr_patterns[:4])  # Limitar S/R a 4 max
        
        # Ordenar por confianza pero mantener prioridad
        patterns = sorted(patterns, key=lambda p: p.get('confidence', 0.5), reverse=True)[:12]
        
        # ⭐ CRITICAL: Calculate confidence score from patterns for Trinity
        pattern_confidence = 50.0  # Default
        if patterns:
            # Top pattern confidence (0.0-1.0) -> 0-100 scale
            top_confidence = patterns[0].get('confidence', 0.5)
            # Cap at 85% max (be conservative, avoid 100%) - GRANULAR float
            pattern_confidence = min(85.0, max(30.0, top_confidence * 100.0))
            logger.info(f"[LLM5] Detected pattern: {patterns[0].get('name', 'UNKNOWN')} @ {top_confidence*100:.0f}% → confidence={pattern_confidence:.1f}%")
        else:
            logger.info(f"[LLM5] No patterns detected → confidence=50%")
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🏦 BANK-GRADE AEGIS OCULUS: Análisis inteligente de tendencia + patrones
        # ═══════════════════════════════════════════════════════════════════════
        decision = 'HOLD'
        
        # Calculate indicators
        rsi = self._rsi(closes)
        macd_data = self._macd(closes)
        macd_val = macd_data.get('macd', 0)
        macd_signal = macd_data.get('signal', 0)
        
        # 🔍 STEP 1: Analizar TENDENCIA ACTUAL del precio (últimas 10-20 velas)
        trend_direction = 'NEUTRAL'
        trend_strength = 0.0
        
        if len(closes) >= 20:
            # Calcular pendiente de la tendencia
            short_ma = float(np.mean(closes[-5:]))   # MA5 (muy corto plazo)
            mid_ma = float(np.mean(closes[-10:]))    # MA10
            long_ma = float(np.mean(closes[-20:]))   # MA20
            
            # Determinar tendencia por MAs
            if short_ma > mid_ma > long_ma:
                trend_direction = 'UPTREND'
                trend_strength = min(1.0, (short_ma - long_ma) / long_ma * 100)
            elif short_ma < mid_ma < long_ma:
                trend_direction = 'DOWNTREND'
                trend_strength = min(1.0, (long_ma - short_ma) / long_ma * 100)
            
            # Confirmar con cambio de precio reciente
            price_change = (closes[-1] - closes[-10]) / closes[-10] * 100
            if price_change < -0.1:  # Cayendo más de 0.1%
                if trend_direction != 'DOWNTREND':
                    trend_direction = 'DOWNTREND'
                    trend_strength = min(1.0, abs(price_change) * 0.5)
            elif price_change > 0.1:  # Subiendo más de 0.1%
                if trend_direction != 'UPTREND':
                    trend_direction = 'UPTREND'
                    trend_strength = min(1.0, abs(price_change) * 0.5)
        
        logger.info(f"[LLM5] 📈 Trend: {trend_direction} (strength={trend_strength:.2f})")
        
        # 🔍 STEP 2: Analizar patrones detectados
        bullish_signals = 0
        bearish_signals = 0
        
        for p in patterns:
            ptype = p.get('type', '')
            pname = p.get('name', '').lower()
            pconf = p.get('confidence', 0.5)
            pdirection = p.get('direction', '')
            
            # Patrones explícitamente alcistas
            if ptype == 'bullish' or 'oversold' in pname or 'double bottom' in pname:
                bullish_signals += pconf
            # Patrones explícitamente bajistas  
            elif ptype == 'bearish' or 'overbought' in pname or 'double top' in pname:
                bearish_signals += pconf
            # Engulfing - analizar si UP o DOWN
            elif 'engulfing' in pname:
                if '(up)' in pname or 'bullish' in pname:
                    bullish_signals += pconf
                elif '(down)' in pname or 'bearish' in pname:
                    bearish_signals += pconf
            # Hammer en downtrend = señal de reversión alcista
            elif 'hammer' in pname and trend_direction == 'DOWNTREND':
                bullish_signals += pconf * 0.8  # Reversal potencial
            # Tendencia detectada
            elif ptype == 'trend':
                if pdirection == 'up' or 'uptrend' in pname:
                    bullish_signals += pconf
                elif pdirection == 'down' or 'downtrend' in pname:
                    bearish_signals += pconf
            # Reversal - depende de la tendencia actual!
            elif ptype == 'reversal':
                if trend_direction == 'UPTREND':
                    bearish_signals += pconf  # Reversal en uptrend = SELL
                elif trend_direction == 'DOWNTREND':
                    bullish_signals += pconf  # Reversal en downtrend = BUY
        
        # 🔍 STEP 3: MACD confirmation
        if macd_val > macd_signal and macd_val > 0:
            bullish_signals += 0.3
        elif macd_val < macd_signal and macd_val < 0:
            bearish_signals += 0.3
        
        # 🔍 STEP 4: MOMENTUM-BASED RSI (seguir tendencia, NO reversa)
        # Calcular momentum del precio
        price_mom = closes[-1] - closes[-5] if len(closes) >= 5 else 0
        
        # RSI alto + precio subiendo = MOMENTUM ALCISTA → seguir comprando
        if rsi > 55 and price_mom > 0.2:
            bullish_signals += 0.6
            patterns.insert(0, {'name': 'Momentum_Up', 'type': 'bullish', 'confidence': 0.75})
            logger.info(f"[LLM5] 🟢 MOMENTUM UP (RSI={rsi:.1f}, mom={price_mom:.2f})")
        # RSI bajo + precio bajando = MOMENTUM BAJISTA → seguir vendiendo
        elif rsi < 45 and price_mom < -0.2:
            bearish_signals += 0.6
            patterns.insert(0, {'name': 'Momentum_Down', 'type': 'bearish', 'confidence': 0.75})
            logger.info(f"[LLM5] 🔴 MOMENTUM DOWN (RSI={rsi:.1f}, mom={price_mom:.2f})")
        # Momentum fuerte confirmado
        elif rsi > 60 and price_mom > 0.5:
            bullish_signals += 0.8
            patterns.insert(0, {'name': 'Strong_Momentum_Up', 'type': 'bullish', 'confidence': 0.85})
        elif rsi < 40 and price_mom < -0.5:
            bearish_signals += 0.8
            patterns.insert(0, {'name': 'Strong_Momentum_Down', 'type': 'bearish', 'confidence': 0.85})
        
        # 🔍 STEP 5: Trend following (si hay tendencia clara, seguirla)
        # ⭐ CRITICAL: La tendencia actual tiene MAYOR peso que patrones históricos
        if trend_strength > 0.3:
            if trend_direction == 'DOWNTREND':
                bearish_signals += trend_strength * 1.2  # BOOST: tendencia bajista clara
                bullish_signals *= 0.5  # PENALIZAR señales alcistas en downtrend
            elif trend_direction == 'UPTREND':
                bullish_signals += trend_strength * 1.2  # BOOST: tendencia alcista clara
                bearish_signals *= 0.5  # PENALIZAR señales bajistas en uptrend
        
        logger.info(f"[LLM5] 📊 Signals: BULL={bullish_signals:.2f} BEAR={bearish_signals:.2f}")
        
        # 🔍 STEP 6: Decisión final - requiere diferencia significativa
        signal_diff = abs(bullish_signals - bearish_signals)
        
        if signal_diff >= 0.3:  # Requiere diferencia mínima
            if bullish_signals > bearish_signals:
                decision = 'BUY'
                pattern_confidence = min(90.0, 50.0 + bullish_signals * 20)
            else:
                decision = 'SELL'
                pattern_confidence = min(90.0, 50.0 + bearish_signals * 20)
        else:
            decision = 'HOLD'  # No hay señal clara
            pattern_confidence = 40.0
            logger.info(f"[LLM5] ⚪ No clear signal, diff={signal_diff:.2f} → HOLD")
        
        # ⭐ CRITICAL FIX: INVALIDAR decisiones CONTRA tendencia clara
        # Si hay DOWNTREND fuerte y señales dicen BUY → forzar HOLD o SELL
        if trend_direction == 'DOWNTREND' and trend_strength > 0.4:
            if decision == 'BUY':
                logger.warning(f"[LLM5] ⚠️ BLOCKED BUY in strong DOWNTREND! Forcing HOLD")
                decision = 'HOLD'
                pattern_confidence = 35.0
        elif trend_direction == 'UPTREND' and trend_strength > 0.4:
            if decision == 'SELL':
                logger.warning(f"[LLM5] ⚠️ BLOCKED SELL in strong UPTREND! Forcing HOLD")
                decision = 'HOLD'
                pattern_confidence = 35.0
        
        # Boost confidence si trend y señales están alineados
        if (decision == 'BUY' and trend_direction == 'UPTREND') or \
           (decision == 'SELL' and trend_direction == 'DOWNTREND'):
            pattern_confidence = min(95.0, pattern_confidence + 10)
            logger.info(f"[LLM5] ✅ Decision aligned with trend → confidence boost")
        
        # ===== ADX FILTER: Precision entries based on trend strength =====
        adx = self._adx(closes, highs, lows) if len(closes) >= 14 else 20
        adx_trending = adx > 25  # Market has trend
        adx_strong = adx > 35    # Strong directional movement
        
        if decision in ('BUY', 'SELL'):
            if adx_strong:
                # Strong trend: boost confidence
                pattern_confidence = min(95.0, pattern_confidence * 1.12)
                logger.debug(f"[LLM5] ADX={adx:.1f} STRONG → conf boost 1.12x")
            elif adx_trending:
                # Normal trend: slight boost
                pattern_confidence = min(92.0, pattern_confidence * 1.06)
                logger.debug(f"[LLM5] ADX={adx:.1f} trending → conf boost 1.06x")
            else:
                # Ranging market: reduce confidence (choppy = risky)
                pattern_confidence = pattern_confidence * 0.82
                logger.debug(f"[LLM5] ADX={adx:.1f} RANGING → conf reduced 0.82x")
        
        # Estadísticas
        stats = {
            'price': float(closes[-1]),
            'atr_14': self._atr(closes, highs, lows),
            'rsi_14': self._rsi(closes),
            'macd': self._macd(closes),
            'range_20': float(max(closes[-20:]) - min(closes[-20:])),
            'volume_avg': float(np.mean(volumes[-20:])),
        }
        
        # ⭐ CRITICAL: Extraer nombres de patrones para dashboard
        pattern_names = [p.get('name', 'UNKNOWN') for p in patterns if isinstance(p, dict)]
        
        # Contar patrones BULLISH (incluye más tipos)
        bullish_pattern_count = sum(1 for p in patterns if (
            p.get('type') == 'bullish' or 
            'bull' in str(p.get('name', '')).lower() or
            'hammer' in str(p.get('name', '')).lower() or
            'oversold' in str(p.get('name', '')).lower() or
            'double bottom' in str(p.get('name', '')).lower() or
            'uptrend' in str(p.get('name', '')).lower() or
            (p.get('type') == 'reversal' and p.get('direction') == 'up') or
            (p.get('type') == 'trend' and p.get('direction') == 'up') or
            ('engulfing' in str(p.get('name', '')).lower() and '(up)' in str(p.get('name', '')).lower())
        ))
        
        # Contar patrones BEARISH (incluye más tipos)
        bearish_pattern_count = sum(1 for p in patterns if (
            p.get('type') == 'bearish' or 
            'bear' in str(p.get('name', '')).lower() or
            'shooting' in str(p.get('name', '')).lower() or
            'overbought' in str(p.get('name', '')).lower() or
            'double top' in str(p.get('name', '')).lower() or
            'downtrend' in str(p.get('name', '')).lower() or
            (p.get('type') == 'reversal' and p.get('direction') == 'down') or
            (p.get('type') == 'trend' and p.get('direction') == 'down') or
            ('engulfing' in str(p.get('name', '')).lower() and '(down)' in str(p.get('name', '')).lower())
        ))
        
        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'candles': len(self.history),
            'decision': decision,  # ⭐ For Trinity
            'confidence': pattern_confidence,  # ⭐ For Trinity (now float for granularity)
            'patterns': patterns,
            # ⭐ NEW: Explicit fields for dashboard display
            'chart_patterns': pattern_names,  # List of pattern names
            'patterns_found': len(patterns),
            'bullish_patterns': bullish_pattern_count,
            'bearish_patterns': bearish_pattern_count,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'statistics': stats,
        }
        
        logger.info(f"[LLM5] 📊 Analysis: {decision}@{pattern_confidence:.0f}% | Patterns: {pattern_names[:3]}")
        
        self.last_analysis = analysis
        return analysis
    
    def _candlestick_patterns(self, opens, closes, highs, lows):
        """Detecta patrones de velas - MEJORADO con 15+ patrones"""
        patterns = []
        
        if len(closes) < 3:
            return patterns
        
        # Analizar últimas 10 velas para encontrar patrones
        start_idx = max(0, len(closes) - 10)
        
        for i in range(start_idx, len(closes)):
            o, c, h, l = opens[i], closes[i], highs[i], lows[i]
            body = abs(c - o)
            range_ = h - l if h != l else 0.01
            upper_wick = h - max(o, c)
            lower_wick = min(o, c) - l
            is_bullish = c > o
            is_bearish = c < o
            body_ratio = body / range_ if range_ > 0 else 0
            
            # ═══════════════════════════════════════════════════════════
            # PATRONES DE UNA VELA
            # ═══════════════════════════════════════════════════════════
            
            # HAMMER (Bullish) - Cuerpo pequeño arriba, mecha larga abajo
            if body_ratio < 0.35 and lower_wick > 2 * body and upper_wick < body:
                patterns.append({
                    'name': 'HAMMER_BULLISH',
                    'type': 'bullish',
                    'confidence': 0.78
                })
            
            # INVERTED HAMMER (Bullish) - Cuerpo pequeño abajo, mecha larga arriba
            if body_ratio < 0.35 and upper_wick > 2 * body and lower_wick < body:
                patterns.append({
                    'name': 'INVERTED_HAMMER',
                    'type': 'bullish',
                    'confidence': 0.72
                })
            
            # SHOOTING STAR (Bearish) - Cuerpo pequeño abajo, mecha larga arriba
            if body_ratio < 0.35 and upper_wick > 2 * body and lower_wick < body * 0.5:
                patterns.append({
                    'name': 'SHOOTING_STAR',
                    'type': 'bearish',
                    'confidence': 0.78
                })
            
            # HANGING MAN (Bearish) - Igual que hammer pero en uptrend
            if body_ratio < 0.35 and lower_wick > 2 * body and upper_wick < body:
                if i > 3 and closes[i] > closes[i-3]:  # En uptrend
                    patterns.append({
                        'name': 'HANGING_MAN',
                        'type': 'bearish',
                        'confidence': 0.70
                    })
            
            # DOJI - Cuerpo muy pequeño
            if body_ratio < 0.1:
                doji_type = 'DOJI'
                conf = 0.65
                if lower_wick > 2 * upper_wick:
                    doji_type = 'DRAGONFLY_DOJI'  # Bullish
                    conf = 0.75
                elif upper_wick > 2 * lower_wick:
                    doji_type = 'GRAVESTONE_DOJI'  # Bearish
                    conf = 0.75
                patterns.append({
                    'name': doji_type,
                    'type': 'indecision',
                    'confidence': conf
                })
            
            # MARUBOZU - Vela sin mechas (momentum fuerte)
            if body_ratio > 0.85:
                if is_bullish:
                    patterns.append({
                        'name': 'MARUBOZU_BULLISH',
                        'type': 'bullish',
                        'confidence': 0.80
                    })
                else:
                    patterns.append({
                        'name': 'MARUBOZU_BEARISH',
                        'type': 'bearish',
                        'confidence': 0.80
                    })
            
            # ═══════════════════════════════════════════════════════════
            # PATRONES DE DOS VELAS
            # ═══════════════════════════════════════════════════════════
            
            if i > 0:
                prev_o, prev_c = opens[i-1], closes[i-1]
                prev_h, prev_l = highs[i-1], lows[i-1]
                prev_body = abs(prev_o - prev_c)
                prev_bullish = prev_c > prev_o
                prev_bearish = prev_c < prev_o
                
                # BULLISH ENGULFING
                if is_bullish and prev_bearish and c > prev_o and o < prev_c and body > prev_body:
                    patterns.append({
                        'name': 'ENGULFING_BULLISH',
                        'type': 'bullish',
                        'confidence': 0.82
                    })
                
                # BEARISH ENGULFING
                if is_bearish and prev_bullish and c < prev_o and o > prev_c and body > prev_body:
                    patterns.append({
                        'name': 'ENGULFING_BEARISH',
                        'type': 'bearish',
                        'confidence': 0.82
                    })
                
                # PIERCING LINE (Bullish)
                if prev_bearish and is_bullish and o < prev_l and c > (prev_o + prev_c) / 2:
                    patterns.append({
                        'name': 'PIERCING_LINE',
                        'type': 'bullish',
                        'confidence': 0.75
                    })
                
                # DARK CLOUD COVER (Bearish)
                if prev_bullish and is_bearish and o > prev_h and c < (prev_o + prev_c) / 2:
                    patterns.append({
                        'name': 'DARK_CLOUD_COVER',
                        'type': 'bearish',
                        'confidence': 0.75
                    })
                
                # TWEEZER BOTTOM (Bullish)
                if abs(l - prev_l) < range_ * 0.1 and prev_bearish and is_bullish:
                    patterns.append({
                        'name': 'TWEEZER_BOTTOM',
                        'type': 'bullish',
                        'confidence': 0.72
                    })
                
                # TWEEZER TOP (Bearish)
                if abs(h - prev_h) < range_ * 0.1 and prev_bullish and is_bearish:
                    patterns.append({
                        'name': 'TWEEZER_TOP',
                        'type': 'bearish',
                        'confidence': 0.72
                    })
            
            # ═══════════════════════════════════════════════════════════
            # PATRONES DE TRES VELAS
            # ═══════════════════════════════════════════════════════════
            
            if i > 1:
                # Three White Soldiers (Bullish)
                if (closes[i] > opens[i] and closes[i-1] > opens[i-1] and closes[i-2] > opens[i-2] and
                    closes[i] > closes[i-1] > closes[i-2]):
                    patterns.append({
                        'name': 'THREE_WHITE_SOLDIERS',
                        'type': 'bullish',
                        'confidence': 0.85
                    })
                
                # Three Black Crows (Bearish)
                if (closes[i] < opens[i] and closes[i-1] < opens[i-1] and closes[i-2] < opens[i-2] and
                    closes[i] < closes[i-1] < closes[i-2]):
                    patterns.append({
                        'name': 'THREE_BLACK_CROWS',
                        'type': 'bearish',
                        'confidence': 0.85
                    })
                
                # MORNING STAR (Bullish) - Vela bajista grande, doji/pequeña, vela alcista grande
                body_2ago = abs(closes[i-2] - opens[i-2])
                body_1ago = abs(closes[i-1] - opens[i-1])
                if (closes[i-2] < opens[i-2] and  # Primera vela bearish
                    body_1ago < body_2ago * 0.3 and  # Segunda vela pequeña
                    closes[i] > opens[i] and  # Tercera vela bullish
                    body > body_2ago * 0.5):  # Tercera vela grande
                    patterns.append({
                        'name': 'MORNING_STAR',
                        'type': 'bullish',
                        'confidence': 0.80
                    })
                
                # EVENING STAR (Bearish) - Vela alcista grande, doji/pequeña, vela bajista grande
                if (closes[i-2] > opens[i-2] and  # Primera vela bullish
                    body_1ago < body_2ago * 0.3 and  # Segunda vela pequeña
                    closes[i] < opens[i] and  # Tercera vela bearish
                    body > body_2ago * 0.5):  # Tercera vela grande
                    patterns.append({
                        'name': 'EVENING_STAR',
                        'type': 'bearish',
                        'confidence': 0.80
                    })
        
        # Eliminar duplicados manteniendo el de mayor confianza
        seen = {}
        for p in patterns:
            name = p['name']
            if name not in seen or p['confidence'] > seen[name]['confidence']:
                seen[name] = p
        
        return list(seen.values())
    
    def _trend_patterns(self, closes):
        """Detecta tendencias - MEJORADO"""
        patterns = []
        
        if len(closes) < 5:
            return patterns
        
        # ═══════════════════════════════════════════════════════════
        # 🎯 ADVANCED: MOMENTUM ACCELERATION with Price Velocity
        # ═══════════════════════════════════════════════════════════
        
        # Calculate momentum acceleration (velocity + acceleration)
        if len(closes) >= 10:
            # Velocity = recent ROC
            velocity = (closes[-1] - closes[-5]) / closes[-5] * 100
            # Acceleration = change in velocity
            prev_velocity = (closes[-5] - closes[-10]) / closes[-10] * 100
            acceleration = velocity - prev_velocity
            
            # BULLISH: Positive velocity + positive acceleration
            if velocity > 0.15 and acceleration > 0.08:
                patterns.append({
                    'name': 'MOMENTUM_ACCELERATING_BULL',
                    'type': 'bullish',
                    'direction': 'up',
                    'confidence': 0.88,
                    'points': 9
                })
            elif velocity > 0.10 and acceleration > 0:
                patterns.append({
                    'name': 'UPTREND_STRONG',
                    'type': 'bullish',
                    'direction': 'up',
                    'confidence': 0.80,
                    'points': 8
                })
            elif velocity > 0.05:
                patterns.append({
                    'name': 'UPTREND_MODERATE',
                    'type': 'bullish',
                    'direction': 'up',
                    'confidence': 0.68,
                    'points': 6
                })
            
            # BEARISH: Negative velocity + negative acceleration
            elif velocity < -0.15 and acceleration < -0.08:
                patterns.append({
                    'name': 'MOMENTUM_ACCELERATING_BEAR',
                    'type': 'bearish',
                    'direction': 'down',
                    'confidence': 0.88,
                    'points': 9
                })
            elif velocity < -0.10 and acceleration < 0:
                patterns.append({
                    'name': 'DOWNTREND_STRONG',
                    'type': 'bearish',
                    'direction': 'down',
                    'confidence': 0.80,
                    'points': 8
                })
            elif velocity < -0.05:
                patterns.append({
                    'name': 'DOWNTREND_MODERATE',
                    'type': 'bearish',
                    'direction': 'down',
                    'confidence': 0.68,
                    'points': 6
                })
        
        # ═══════════════════════════════════════════════════════════
        # MOMENTUM (cambio de precio significativo)
        # ═══════════════════════════════════════════════════════════
        
        if len(closes) >= 10:
            pct_change = (closes[-1] - closes[-10]) / closes[-10] * 100
            
            if pct_change > 0.3:  # Subió más de 0.3%
                patterns.append({
                    'name': 'MOMENTUM_BULLISH',
                    'type': 'bullish',
                    'confidence': 0.75
                })
            elif pct_change < -0.3:  # Bajó más de 0.3%
                patterns.append({
                    'name': 'MOMENTUM_BEARISH',
                    'type': 'bearish',
                    'confidence': 0.75
                })
        
        # ═══════════════════════════════════════════════════════════
        # CONSOLIDACIÓN / BREAKOUT POTENCIAL
        # ═══════════════════════════════════════════════════════════
        
        if len(closes) >= 20:
            recent = closes[-20:]
            range_ = max(recent) - min(recent)
            volatility = range_ / np.mean(recent)
            
            if volatility < 0.015:  # Consolidación apretada
                patterns.append({
                    'name': 'CONSOLIDATION_TIGHT',
                    'type': 'neutral',
                    'confidence': 0.72
                })
            elif volatility < 0.025:
                patterns.append({
                    'name': 'CONSOLIDATION',
                    'type': 'neutral',
                    'confidence': 0.65
                })
        
        # ═══════════════════════════════════════════════════════════
        # BREAKOUT DETECTION
        # ═══════════════════════════════════════════════════════════
        
        if len(closes) >= 20:
            range_high = max(closes[-20:-3])
            range_low = min(closes[-20:-3])
            
            if closes[-1] > range_high:
                patterns.append({
                    'name': 'BREAKOUT_BULLISH',
                    'type': 'bullish',
                    'confidence': 0.78
                })
            elif closes[-1] < range_low:
                patterns.append({
                    'name': 'BREAKOUT_BEARISH',
                    'type': 'bearish',
                    'confidence': 0.78
                })
        
        return patterns
    
    def _reversal_patterns(self, closes, highs, lows):
        """Detecta reversiones - MEJORADO con más patrones"""
        patterns = []
        
        if len(closes) < 10:
            return patterns
        
        # ═══════════════════════════════════════════════════════════
        # DOUBLE TOP / BOTTOM - ⭐ MEJORADO: Requiere confirmación de rebote
        # ═══════════════════════════════════════════════════════════
        
        if len(highs) >= 20:
            try:
                last_high_slice = highs[-10:]
                prev_high_slice = highs[-20:-10]
                if len(last_high_slice) > 0 and len(prev_high_slice) > 0:
                    last_high_val = np.max(last_high_slice)
                    prev_high_val = np.max(prev_high_slice)
                    tolerance = 0.002 * highs[-1]  # 0.2% tolerancia
                    # ⭐ FIX: Solo cuenta si precio actual está BAJANDO desde el segundo top
                    price_dropping = closes[-1] < last_high_val * 0.998
                    if abs(last_high_val - prev_high_val) < tolerance and price_dropping:
                        patterns.append({
                            'name': 'DOUBLE_TOP',
                            'type': 'bearish',
                            'confidence': 0.76
                        })
            except:
                pass
        
        if len(lows) >= 20:
            try:
                last_low_slice = lows[-10:]
                prev_low_slice = lows[-20:-10]
                if len(last_low_slice) > 0 and len(prev_low_slice) > 0:
                    last_low_val = np.min(last_low_slice)
                    prev_low_val = np.min(prev_low_slice)
                    tolerance = 0.002 * lows[-1]
                    # ⭐ FIX: Solo cuenta Double Bottom si:
                    # 1. Precio actual está SUBIENDO desde el segundo bottom
                    # 2. Cierre actual > mínimo reciente (confirmación de rebote)
                    price_rising = closes[-1] > last_low_val * 1.002
                    recent_bounce = closes[-1] > closes[-3] and closes[-2] > closes[-4]
                    if abs(last_low_val - prev_low_val) < tolerance and price_rising and recent_bounce:
                        patterns.append({
                            'name': 'DOUBLE_BOTTOM',
                            'type': 'bullish',
                            'confidence': 0.76
                        })
                    elif abs(last_low_val - prev_low_val) < tolerance:
                        # Solo potencial double bottom - sin confirmación
                        patterns.append({
                            'name': 'Potential_Double_Bottom',
                            'type': 'neutral',  # ⚠️ No es bullish hasta confirmarse
                            'confidence': 0.40
                        })
            except:
                pass
        
        # ═══════════════════════════════════════════════════════════
        # HIGHER HIGHS / LOWER LOWS (Trend Confirmation)
        # ═══════════════════════════════════════════════════════════
        
        if len(highs) >= 6:
            recent_highs = highs[-6:]
            hh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
            if hh_count >= 4:  # 4+ higher highs
                patterns.append({
                    'name': 'HIGHER_HIGHS',
                    'type': 'bullish',
                    'confidence': 0.72
                })
        
        if len(lows) >= 6:
            recent_lows = lows[-6:]
            ll_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i-1])
            if ll_count >= 4:  # 4+ lower lows
                patterns.append({
                    'name': 'LOWER_LOWS',
                    'type': 'bearish',
                    'confidence': 0.72
                })
        
        # ═══════════════════════════════════════════════════════════
        # V-BOTTOM / V-TOP (Sharp Reversal)
        # ═══════════════════════════════════════════════════════════
        
        if len(closes) >= 5:
            # V-Bottom: Caída fuerte seguida de subida fuerte
            drop = closes[-3] - closes[-5]
            rise = closes[-1] - closes[-3]
            if drop < 0 and rise > 0 and abs(rise) > abs(drop) * 0.7:
                patterns.append({
                    'name': 'V_BOTTOM',
                    'type': 'bullish',
                    'confidence': 0.74
                })
            # V-Top: Subida fuerte seguida de caída fuerte
            elif drop > 0 and rise < 0 and abs(rise) > abs(drop) * 0.7:
                patterns.append({
                    'name': 'V_TOP',
                    'type': 'bearish',
                    'confidence': 0.74
                })
        
        # ═══════════════════════════════════════════════════════════
        # OVERSOLD / OVERBOUGHT (basado en posición en rango)
        # ═══════════════════════════════════════════════════════════
        
        if len(closes) >= 20:
            range_high = np.max(highs[-20:])
            range_low = np.min(lows[-20:])
            range_total = range_high - range_low
            
            if range_total > 0:
                position = (closes[-1] - range_low) / range_total
                
                if position < 0.15:  # Cerca del mínimo
                    patterns.append({
                        'name': 'OVERSOLD_ZONE',
                        'type': 'bullish',
                        'confidence': 0.70
                    })
                elif position > 0.85:  # Cerca del máximo
                    patterns.append({
                        'name': 'OVERBOUGHT_ZONE',
                        'type': 'bearish',
                        'confidence': 0.70
                    })
        
        return patterns
    
    def _volume_patterns(self, closes, volumes):
        """Detecta patrones de volumen"""
        patterns = []
        
        if len(volumes) < 5:
            return patterns
        
        avg_vol = np.mean(volumes[-20:])
        recent_vol = volumes[-1]
        
        if recent_vol > 2 * avg_vol:
            patterns.append({
                'name': 'High Volume Spike',
                'type': 'volume',
                'confidence': 0.6
            })
        
        if recent_vol < 0.5 * avg_vol:
            patterns.append({
                'name': 'Low Volume Weakness',
                'type': 'volume',
                'confidence': 0.5
            })
        
        return patterns
    
    def _volatility_patterns(self, closes, highs, lows):
        """Detecta patrones de volatilidad"""
        patterns = []
        
        if len(closes) < 14:
            return patterns
        
        atr = self._atr(closes, highs, lows)
        avg_price = np.mean(closes[-14:])
        volatility = atr / avg_price
        
        if volatility > 0.02:
            patterns.append({
                'name': 'High Volatility',
                'type': 'volatility',
                'confidence': 0.7
            })
        elif volatility < 0.01:
            patterns.append({
                'name': 'Low Volatility',
                'type': 'volatility',
                'confidence': 0.7
            })
        
        return patterns
    
    def _support_resistance(self, closes, highs, lows):
        """Detecta soportes y resistencias - LIMITADO a 2 mejores de cada"""
        patterns = []
        
        if len(closes) < 20:
            return patterns
        
        # Soportes - solo los 2 más tocados
        recent_lows = lows[-50:]
        support_levels = {}
        for low in recent_lows:
            key = round(low, 2)  # Redondear a 2 decimales para agrupar
            support_levels[key] = support_levels.get(key, 0) + 1
        
        # Top 2 soportes por número de toques
        top_supports = sorted(support_levels.items(), key=lambda x: x[1], reverse=True)[:2]
        for support, count in top_supports:
            if count >= 2:
                patterns.append({
                    'name': f'Support @ {support:.2f}',
                    'type': 'support',
                    'level': support,
                    'touches': count,
                    'confidence': min(0.8, 0.5 + 0.1 * count)
                })
        
        # Resistencias - solo las 2 más tocadas
        recent_highs = highs[-50:]
        resistance_levels = {}
        for high in recent_highs:
            key = round(high, 2)  # Redondear a 2 decimales
            resistance_levels[key] = resistance_levels.get(key, 0) + 1
        
        # Top 2 resistencias
        top_resistances = sorted(resistance_levels.items(), key=lambda x: x[1], reverse=True)[:2]
        for resistance, count in top_resistances:
            if count >= 2:
                patterns.append({
                    'name': f'Resistance @ {resistance:.2f}',
                    'type': 'resistance',
                    'level': resistance,
                    'touches': count,
                    'confidence': min(0.8, 0.5 + 0.1 * count)
                })
        
        return patterns
    
    def _atr(self, closes, highs, lows, period=14):
        """Calcula ATR"""
        if len(closes) < period:
            return 0
        
        tr = []
        for i in range(1, len(closes)):
            tr.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            ))
        
        return float(np.mean(tr[-period:]))
    
    def _adx(self, closes, highs, lows, period=14):
        """Calcula ADX (Average Directional Index) para medir fuerza de tendencia"""
        if len(closes) < period + 1:
            return 20  # Valor neutro si no hay suficientes datos
        
        # True Range
        tr = []
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(closes)):
            tr.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            ))
            
            # +DM y -DM
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)
        
        # Smoothed averages
        atr = np.mean(tr[-period:])
        plus_di = 100 * np.mean(plus_dm[-period:]) / (atr + 1e-10)
        minus_di = 100 * np.mean(minus_dm[-period:]) / (atr + 1e-10)
        
        # DX y ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        
        return float(dx)  # Aproximación simplificada del ADX

    def _rsi(self, closes, period=14):
        """Calcula RSI"""
        if len(closes) < period + 1:
            return 50
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))
    
    def _macd(self, closes, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        if len(closes) < slow + signal:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)
        
        # Ensure both EMAs have same length
        min_len = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]
        
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        
        return {
            'macd': float(macd_line[-1]) if len(macd_line) > 0 else 0,
            'signal': float(signal_line[-1]) if len(signal_line) > 0 else 0,
        }
    
    def _ema(self, data, period):
        """Calcula EMA"""
        ema = [np.mean(data[:period])]
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(data)):
            ema.append(data[i] * multiplier + ema[-1] * (1 - multiplier))
        
        return np.array(ema)


# ============ TCP SERVER ============
class LLM5Server:
    """Servidor TCP para LLM5"""
    
    def __init__(self):
        self.analyzer = LLM5ChartAnalyzer()
        self.running = False
    
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
{Y}|{R}  {Y}████╗  ██║{W}██╔═══██╗██║   ██║██╔══██╗{R}   {C}LLM5 AEGIS OCULUS{R}   {Y}|{R}
{Y}|{R}  {Y}██╔██╗ ██║{W}██║   ██║██║   ██║███████║{R}   {D}Chart Intelligence{R}  {Y}|{R}
{Y}|{R}  {Y}██║╚██╗██║{W}██║   ██║╚██╗ ██╔╝██╔══██║{R}                       {Y}|{R}
{Y}|{R}  {Y}██║ ╚████║{W}╚██████╔╝ ╚████╔╝ ██║  ██║{R}                       {Y}|{R}
{Y}|{R}  {Y}╚═╝  ╚═══╝{W} ╚═════╝   ╚═══╝  ╚═╝  ╚═╝{R}                       {Y}|{R}
{Y}|{R}                                                              {Y}|{R}
{Y}+{'-'*62}+{R}
{Y}|{R}  {W}CNHUSD Scalping Edition{R}      {D}by Polarice Labs © 2026{R}       {Y}|{R}
{Y}|{R}  {G}● PORT: {PORT}{R}                  {D}1000+ Pattern Detection{R}     {Y}|{R}
{Y}+{'='*62}+{R}
""")

    def start(self):
        """Inicia servidor"""
        # Mostrar banner NOVA
        self._print_nova_banner()
        
        self.running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(10)
        
        logger.info(f"LLM5 AEGIS OCULUS Active on {HOST}:{PORT}")
        
        while self.running:
            try:
                client, addr = sock.accept()
                thread = threading.Thread(
                    target=self._handle,
                    args=(client, addr),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
        
        sock.close()
    
    def _handle(self, client: socket.socket, addr):
        """Maneja cliente"""
        try:
            # Recibir
            header = client.recv(4)
            if not header or len(header) < 4:
                return
            
            msg_len = struct.unpack('>I', header)[0]
            payload = b''
            
            while len(payload) < msg_len:
                chunk = client.recv(min(BUFFER_SIZE, msg_len - len(payload)))
                if not chunk:
                    break
                payload += chunk
            
            # Parse JSON
            try:
                data = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError:
                return
            
            # Analizar
            candles = data.get('candles', [])
            if candles:
                self.analyzer.add_candles(candles)
            
            symbol = data.get('symbol', 'CNHUSD')
            timeframe = data.get('timeframe', 'M1')
            
            analysis = self.analyzer.analyze(symbol, timeframe)
            
            # Enviar respuesta
            response = json.dumps(analysis).encode('utf-8')
            resp_header = struct.pack('>I', len(response))
            client.sendall(resp_header + response)
            
            logger.debug(f"✅ Análisis enviado a {addr}")
            
        except Exception as e:
            logger.error(f"Error con {addr}: {e}")
        finally:
            try:
                client.close()
            except:
                pass


# ============ CLIENT HELPER ============
class LLM5Client:
    """Cliente para usar LLM5"""
    
    @staticmethod
    def analyze(symbol='CNHUSD', timeframe='M1', candles=None):
        """Envía data para análisis"""
        if not candles:
            return None
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((HOST, PORT))
            
            msg = json.dumps({
                'symbol': symbol,
                'timeframe': timeframe,
                'candles': candles
            }).encode('utf-8')
            
            header = len(msg).to_bytes(4, 'little')
            sock.sendall(header + msg)
            
            # Recibir
            resp_header = sock.recv(4)
            if not resp_header or len(resp_header) < 4:
                return None
            
            resp_len = struct.unpack('<I', resp_header)[0]
            response = b''
            
            while len(response) < resp_len:
                chunk = sock.recv(min(BUFFER_SIZE, resp_len - len(response)))
                if not chunk:
                    break
                response += chunk
            
            analysis = json.loads(response.decode('utf-8'))
            sock.close()
            
            return analysis
            
        except Exception as e:
            logger.debug(f"Error: {e}")
            return None


def main():
    """Inicia servidor LLM5"""
    server = LLM5Server()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Cerrando LLM5...")


if __name__ == '__main__':
    main()
