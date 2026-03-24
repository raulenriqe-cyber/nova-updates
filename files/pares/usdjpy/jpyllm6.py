"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                          LLM6 - SMART MONEY ORACLE                          ║
║                    USDJPY M15 - Samurai Predator Edition                      ║
║                                                                              ║
║                  IA PROFUNDA - DECISIONES DE PRECISIÓN                      ║
║                                                                              ║
║  Sistema inteligente de detección de ballenas, trampas y falsas rupturas    ║
║  Con sistema de votación ponderada y análisis de profundidad IA             ║
║                                                                              ║
║  Author: Polar Trading Systems                                              ║
║  Version: 2.0 PRODUCTION - USDJPY M15                                       ║
║  Port: 6004 (TCP Server)                                                    ║
║                                                                              ║
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

import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional
from collections import deque
import logging
import json
from datetime import datetime
import sys
import io
import socket
import struct
import threading
import yaml
import signal
import time

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

# Configurar stdout para UTF-8 en Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Crear handlers con encoding UTF-8
import os
os.makedirs('logs', exist_ok=True)

file_handler = logging.FileHandler('logs/llm6_analysis.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - LLM6 - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(message)s'))  # Console output simple, sin timestamp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.propagate = False


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS - TIPOS DE DATOS CONTROLADOS
# ═══════════════════════════════════════════════════════════════════════════════

class MarketIntention(Enum):
    """Intención de mercado detectada"""
    ACCUMULATION = "ACCUMULATION"           # Compra inteligente
    DISTRIBUTION = "DISTRIBUTION"           # Venta inteligente
    LIQUIDATION = "LIQUIDATION"             # Liquidación (pánico)
    EQUILIBRIUM = "EQUILIBRIUM"             # Sin dirección clara
    WHALE_TRAP = "WHALE_TRAP"               # Trampa de ballena
    SMART_REVERSAL = "SMART_REVERSAL"       # Reversión inteligente


class SweepType(Enum):
    """Tipo de barrida de stops detectada"""
    SUPPORT_SWEEP_UP = "SUPPORT_SWEEP_UP"           # Barre soportes hacia arriba
    RESISTANCE_SWEEP_DOWN = "RESISTANCE_SWEEP_DOWN" # Barre resistencias hacia abajo
    FALSE_BREAK_UP = "FALSE_BREAK_UP"               # Falsa ruptura arriba
    FALSE_BREAK_DOWN = "FALSE_BREAK_DOWN"           # Falsa ruptura abajo
    NONE = "NONE"                                    # Sin barrida


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASS - SALIDA DE LLM6
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SmartMoneySignal:
    """Señal completa de dinero inteligente"""
    # Métricas principales
    obv: float
    ad_line: float
    volume_profile: Dict[float, int]
    order_flow_imbalance: float = 0.0  # -100 a +100
    
    # Detecciones
    sweep_type: SweepType = SweepType.NONE
    sweep_direction: Optional[str] = None  # 'BUY' o 'SELL'
    false_break_probability: float = 0.0   # 0-100%
    
    # Inteligencia
    market_intention: MarketIntention = MarketIntention.EQUILIBRIUM
    whale_confidence: float = 0.0  # 0-100%
    
    # Sistema de votación ponderada
    votes: Dict[str, float] = field(default_factory=dict)  # Sistema de votación
    total_vote_weight: float = 0.0
    
    # Decisión final
    recommendation: str = "HOLD"
    confidence: float = 0.0
    reasoning: str = ""
    
    # Timestamp
    timestamp: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL LLM6
# ═══════════════════════════════════════════════════════════════════════════════

class LLM6_SmartMoney:
    """
    Sistema inteligente de análisis de dinero inteligente.
    
    7 Sistemas de Inteligencia:
    1. On-Balance Volume (OBV)
    2. Accumulation/Distribution Line
    3. Volume Profile
    4. Order Flow Imbalance
    5. Sweep Detection
    6. False Break Detection
    7. Whale Confidence Scoring
    
    + Sistema de votación ponderada para decisiones de precisión
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Inicializar LLM6 con configuración"""
        self.config = config or self._default_config()
        self.history = deque(maxlen=100)  # Histórico de análisis
        logger.info("✅ LLM6 Smart Money Oracle inicializado")
    
    def _default_config(self) -> Dict:
        """Configuración por defecto"""
        return {
            'obv_period': 14,
            'ad_volume_levels': 20,
            'sweep_threshold': 0.02,  # 2%
            'false_break_threshold': 75,  # 75%
            'whale_confidence_min': 60,  # Mínimo para considerar ballena
            'imbalance_persistence_period': 10,
            'vote_weight_obv': 1.2,
            'vote_weight_ad': 1.3,
            'vote_weight_sweep': 1.5,
            'vote_weight_false_break': 1.8,
            'vote_weight_whale': 1.6,
        }
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 1: ON-BALANCE VOLUME (OBV)
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_obv(self, genome: Dict) -> float:
        """
        Calcula On-Balance Volume (OBV)
        
        OBV = OBV_prev + volume si close > open
        OBV = OBV_prev - volume si close < open
        OBV = OBV_prev si close = open
        """
        closes = np.array(genome['closes'][-50:])
        volumes = np.array(genome['volumes'][-50:])
        
        if len(closes) < 2:
            return 0.0
        
        obv = 0.0
        for i in range(len(closes)):
            if closes[i] > closes[i-1] if i > 0 else False:
                obv += volumes[i]
            elif closes[i] < closes[i-1] if i > 0 else False:
                obv -= volumes[i]
        
        return float(obv)
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 2: ACCUMULATION/DISTRIBUTION LINE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_ad_line(self, genome: Dict) -> float:
        """
        Calcula Accumulation/Distribution Line
        
        CLV = ((C - L) - (H - C)) / (H - L)
        A/D = A/D_prev + CLV * Volume
        """
        closes = np.array(genome['closes'][-50:])
        highs = np.array(genome['highs'][-50:])
        lows = np.array(genome['lows'][-50:])
        volumes = np.array(genome['volumes'][-50:])
        
        ad_line = 0.0
        for i in range(len(closes)):
            high_low_range = highs[i] - lows[i]
            
            if high_low_range > 0:
                clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / high_low_range
            else:
                clv = 0.0
            
            ad_line += clv * volumes[i]
        
        return float(ad_line)
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 3: VOLUME PROFILE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _build_volume_profile(self, genome: Dict) -> Dict[float, int]:
        """
        Construye Volume Profile: volumen agregado por nivel de precio
        Mapea 100 velas → 20 niveles de precio
        """
        closes = np.array(genome['closes'][-100:])
        volumes = np.array(genome['volumes'][-100:])
        
        if len(closes) == 0:
            return {}
        
        min_price = closes.min()
        max_price = closes.max()
        price_range = max_price - min_price if max_price > min_price else 1
        
        # Crear 20 bins de precio
        num_levels = 20
        profile = {}
        
        for i, price in enumerate(closes):
            # Calcular nivel de precio
            if price_range > 0:
                level_idx = int((price - min_price) / price_range * (num_levels - 1))
            else:
                level_idx = 0
            
            level_key = min_price + (level_idx * price_range / (num_levels - 1))
            profile[level_key] = profile.get(level_key, 0) + int(volumes[i])
        
        return profile
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 4: ORDER FLOW IMBALANCE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_order_flow_imbalance(self, genome: Dict) -> float:
        """
        Calcula desequilibrio de flujo de órdenes (-100 a +100)
        
        Compara velas alcistas vs bajistas (últimas 10 velas)
        """
        closes = np.array(genome['closes'][-10:])
        opens = np.array(genome['opens'][-10:])
        
        if len(closes) == 0:
            return 0.0
        
        buy_candles = np.sum(closes > opens)
        sell_candles = np.sum(closes < opens)
        
        total = buy_candles + sell_candles
        if total == 0:
            return 0.0
        
        imbalance = ((buy_candles - sell_candles) / total) * 100
        return float(np.clip(imbalance, -100, 100))
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 4B: TREND DETECTION (Para contexto de sweeps)
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_trend(self, genome: Dict) -> str:
        """
        Calcula la tendencia del mercado para contextualizar sweeps
        
        Returns:
            'UP' - Tendencia alcista (sweeps de soporte son legítimos)
            'DOWN' - Tendencia bajista (sweeps de resistencia son legítimos)
            'NEUTRAL' - Sin tendencia clara
            
        CRÍTICO: En una tendencia bajista, un sweep de soportes es una TRAMPA
                 (liquidity grab antes de continuar cayendo)
        """
        closes = np.array(genome['closes'][-30:])
        
        if len(closes) < 10:
            return 'NEUTRAL'
        
        # Método 1: EMA comparison
        ema_fast = self._ema(closes, 8)
        ema_slow = self._ema(closes, 21)
        
        if len(ema_fast) < 3 or len(ema_slow) < 3:
            return 'NEUTRAL'
        
        ema_trend = 'UP' if ema_fast[-1] > ema_slow[-1] else 'DOWN'
        
        # Método 2: Precio actual vs precio hace 15 velas
        price_trend = 'UP' if closes[-1] > closes[-15] else 'DOWN'
        
        # Método 3: Higher highs/lower lows
        recent_10 = closes[-10:]
        first_half_avg = np.mean(recent_10[:5])
        second_half_avg = np.mean(recent_10[5:])
        structure_trend = 'UP' if second_half_avg > first_half_avg else 'DOWN'
        
        # Consenso de 3 métodos
        votes = [ema_trend, price_trend, structure_trend]
        up_votes = votes.count('UP')
        down_votes = votes.count('DOWN')
        
        if up_votes >= 2:
            return 'UP'
        elif down_votes >= 2:
            return 'DOWN'
        return 'NEUTRAL'
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calcula EMA simple"""
        if len(data) < period:
            return data
        
        alpha = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 5: SWEEP DETECTION
    # ═════════════════════════════════════════════════════════════════════════
    
    def _detect_sweeps(self, genome: Dict) -> Tuple[SweepType, Optional[str]]:
        """
        Detecta barridas de stops con MÁXIMA SENSIBILIDAD para M1 scalping
        
        Busca: Precio rompe nivel → liquidación de stops → reversión
        + Micro-sweeps para scalping (wicks largos sin confirmación de volumen)
        + Ultra-sweeps: Cualquier wick que perfore nivel previo
        """
        closes = np.array(genome['closes'][-5:])
        opens = np.array(genome['opens'][-5:])
        lows = np.array(genome['lows'][-5:])
        highs = np.array(genome['highs'][-5:])
        volumes = np.array(genome['volumes'][-5:])
        
        if len(closes) < 3:
            return SweepType.NONE, None
        
        current_close = closes[-1]
        current_open = opens[-1] if len(opens) > 0 else closes[-1]
        current_low = lows[-1]
        current_high = highs[-1]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else current_volume
        
        # Calculate body and wicks
        body_top = max(current_close, current_open)
        body_bottom = min(current_close, current_open)
        candle_range = current_high - current_low
        lower_wick = body_bottom - current_low
        upper_wick = current_high - body_top
        
        # Recent lows/highs for sweep reference (last 3 candles)
        recent_low = min(lows[-4:-1]) if len(lows) > 3 else lows[-2]
        recent_high = max(highs[-4:-1]) if len(highs) > 3 else highs[-2]
        
        # ═══ SWEEP UP (Price swept below support, then recovered) ═══
        # Condition: Current low went BELOW recent lows but closed ABOVE
        swept_below = current_low < recent_low
        recovered_up = current_close > recent_low
        
        if swept_below and recovered_up:
            vol_mult = current_volume / avg_volume if avg_volume > 0 else 1.0
            logger.info(f"🔼 SUPPORT_SWEEP_UP detectado | Low:{current_low:.2f} < Recent:{recent_low:.2f} | Close:{current_close:.2f} | Vol:{vol_mult:.1f}x")
            return SweepType.SUPPORT_SWEEP_UP, "BUY"
        
        # ═══ SWEEP DOWN (Price swept above resistance, then fell) ═══
        # Condition: Current high went ABOVE recent highs but closed BELOW
        swept_above = current_high > recent_high
        recovered_down = current_close < recent_high
        
        if swept_above and recovered_down:
            vol_mult = current_volume / avg_volume if avg_volume > 0 else 1.0
            logger.info(f"🔽 RESISTANCE_SWEEP_DOWN detectado | High:{current_high:.2f} > Recent:{recent_high:.2f} | Close:{current_close:.2f} | Vol:{vol_mult:.1f}x")
            return SweepType.RESISTANCE_SWEEP_DOWN, "SELL"
        
        # ═══ MICRO-SWEEP via wick ratio (no need for perfect level break) ═══
        wick_ratio = 0.50  # Wick must be 50%+ of candle range (lowered from 60%)
        
        if candle_range > 0:
            # Micro sweep down: Long upper wick (rejected from highs)
            if upper_wick / candle_range > wick_ratio:
                logger.info(f"🔻 MICRO_SWEEP_DOWN detectado | Upper wick {upper_wick/candle_range:.0%} of range")
                return SweepType.RESISTANCE_SWEEP_DOWN, "SELL"
            
            # Micro sweep up: Long lower wick (rejected from lows)
            if lower_wick / candle_range > wick_ratio:
                logger.info(f"🔺 MICRO_SWEEP_UP detectado | Lower wick {lower_wick/candle_range:.0%} of range")
                return SweepType.SUPPORT_SWEEP_UP, "BUY"
        
        return SweepType.NONE, None
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 6: FALSE BREAK DETECTION
    # ═════════════════════════════════════════════════════════════════════════
    
    def _detect_false_breaks(self, genome: Dict) -> float:
        """
        Detecta falsas rupturas (probabilidad 0-100%)
        
        Analiza: Longitud de wick, testeo de nivel, cierre invertido
        """
        closes = np.array(genome['closes'][-3:])
        highs = np.array(genome['highs'][-3:])
        lows = np.array(genome['lows'][-3:])
        opens = np.array(genome['opens'][-3:])
        volumes = np.array(genome['volumes'][-3:])
        
        if len(closes) < 2:
            return 0.0
        
        current_close = closes[-1]
        current_open = opens[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])
        
        score = 0.0
        
        # Factor 1: Wick largo (rechazo)
        body = abs(current_close - current_open)
        upper_wick = current_high - max(current_close, current_open)
        lower_wick = min(current_close, current_open) - current_low
        
        if body > 0:
            if upper_wick > body * 1.5:
                score += 25  # Wick largo superior = rechazo
            if lower_wick > body * 1.5:
                score += 25  # Wick largo inferior = rechazo
        
        # Factor 2: Volumen bajo en ruptura
        if current_volume < avg_volume * 0.8:
            score += 20  # Volumen bajo = falsa ruptura probable
        
        # Factor 3: Cierre invertido
        if current_close > current_open and closes[-2] < opens[-2]:  # Cambio a verde
            score += 15
        elif current_close < current_open and closes[-2] > opens[-2]:  # Cambio a rojo
            score += 15
        
        return float(np.clip(score, 0, 100))
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA 7: WHALE CONFIDENCE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_whale_confidence(self, 
                                   obv: float,
                                   ad_line: float,
                                   imbalance: float,
                                   sweep_type: SweepType) -> float:
        """
        Calcula confianza de actividad de ballena (0-100%)
        
        Combina: Persistencia de desequilibrio + Escalación de volumen + Validación de barrida
        OPTIMIZED: Lower thresholds for faster whale detection
        """
        score = 0.0
        
        # Factor 1: Desequilibrio de flujo (0-40 puntos) - LOWERED THRESHOLDS
        abs_imbalance = abs(imbalance)
        if abs_imbalance > 50:  # Was 70
            score += 40
        elif abs_imbalance > 35:  # Was 50
            score += 30
        elif abs_imbalance > 20:  # Was 30
            score += 20
        elif abs_imbalance > 10:  # NEW: Even small imbalance gets points
            score += 10
        
        # Factor 2: OBV signal (0-25 puntos) - gives points for BOTH directions
        if obv != 0:
            score += 25  # Any OBV signal = activity
        
        # Factor 3: A/D line (0-20 puntos) - gives points for BOTH directions
        if ad_line != 0:
            score += 20  # Any A/D signal = activity
        
        # Factor 4: Barrida confirmada (0-20 puntos) - INCREASED importance
        if sweep_type != SweepType.NONE:
            score += 20  # Was 10 - sweeps are critical for scalping
        
        return float(np.clip(score, 0, 100))
    
    # ═════════════════════════════════════════════════════════════════════════
    # SISTEMA DE VOTACIÓN PONDERADA
    # ═════════════════════════════════════════════════════════════════════════
    
    def _calculate_weighted_votes(self, signal: SmartMoneySignal, genome: Dict = None) -> Dict[str, float]:
        """
        Sistema de votación ponderada para decisiones de precisión
        
        Cada componente vota con peso diferente:
        - False Break: 1.8x (muy importante)
        - Sweep: 1.5x (importante) - PERO se invierte si es contra-tendencia (TRAMPA!)
        - Whale: 1.6x (importante)
        - A/D: 1.3x (moderado)
        - OBV: 1.2x (moderado)
        
        CRÍTICO: Los sweeps contra-tendencia son TRAMPAS de liquidez!
        - En DOWNTREND: SUPPORT_SWEEP_UP = TRAMPA → votar SELL
        - En UPTREND: RESISTANCE_SWEEP_DOWN = TRAMPA → votar BUY
        """
        votes = {}
        
        # Calcular tendencia si tenemos genome
        trend = 'NEUTRAL'
        if genome is not None:
            trend = self._calculate_trend(genome)
        
        # Voto 1: False Break Detection (Peso: 1.8)
        if signal.false_break_probability > 75:
            votes['false_break_veto'] = -1.0 * self.config['vote_weight_false_break']
        elif signal.false_break_probability > 50:
            votes['false_break_caution'] = -0.5 * self.config['vote_weight_false_break']
        
        # Voto 2: Sweep Detection (Peso: 1.5) - CON CONTEXTO DE TENDENCIA
        if signal.sweep_type != SweepType.NONE:
            sweep_direction = 1.0 if signal.sweep_direction == 'BUY' else -1.0
            
            # ═══════════════════════════════════════════════════════════════
            # DETECCIÓN DE TRAMPA DE LIQUIDEZ
            # ═══════════════════════════════════════════════════════════════
            is_trap = False
            trap_reason = ""
            
            # En DOWNTREND: sweep hacia arriba (BUY) es TRAMPA
            if trend == 'DOWN' and signal.sweep_direction == 'BUY':
                is_trap = True
                trap_reason = "SUPPORT_SWEEP_UP in DOWNTREND = TRAP → SELL"
                sweep_direction = -1.0  # INVERTIR: votar SELL
                
            # En UPTREND: sweep hacia abajo (SELL) es TRAMPA
            elif trend == 'UP' and signal.sweep_direction == 'SELL':
                is_trap = True
                trap_reason = "RESISTANCE_SWEEP_DOWN in UPTREND = TRAP → BUY"
                sweep_direction = 1.0  # INVERTIR: votar BUY
            
            if is_trap:
                # Voto de trampa con peso aumentado (más confianza en la dirección invertida)
                votes['sweep_trap'] = sweep_direction * self.config['vote_weight_sweep'] * 1.5
                logger.warning(f"🪤 LLM6 TRAP DETECTED: {trap_reason}")
            else:
                # Sweep en línea con la tendencia - señal legítima
                votes['sweep'] = sweep_direction * self.config['vote_weight_sweep']
        
        # Voto 3: Whale Confidence (Peso: 1.6) - VERY SENSITIVE THRESHOLDS
        if signal.whale_confidence > 50:  # Was 70
            votes['whale_strong'] = 1.0 * self.config['vote_weight_whale']
        elif signal.whale_confidence > 30:  # Was 45
            votes['whale_moderate'] = 0.5 * self.config['vote_weight_whale']
        elif signal.whale_confidence > 15:  # NEW: Even small activity
            votes['whale_weak'] = 0.25 * self.config['vote_weight_whale']
        
        # Voto 4: A/D Line (Peso: 1.3)
        if signal.ad_line > 0:
            votes['ad_bullish'] = 1.0 * self.config['vote_weight_ad']
        elif signal.ad_line < 0:
            votes['ad_bearish'] = -1.0 * self.config['vote_weight_ad']
        
        # Voto 5: OBV (Peso: 1.2)
        if signal.obv > 0:
            votes['obv_bullish'] = 1.0 * self.config['vote_weight_obv']
        elif signal.obv < 0:
            votes['obv_bearish'] = -1.0 * self.config['vote_weight_obv']
        
        # Voto 6: Order Flow (Peso: 1.4) - VERY SENSITIVE THRESHOLDS
        if signal.order_flow_imbalance > 20:  # Was 35
            votes['flow_buy'] = 1.0 * 1.4
        elif signal.order_flow_imbalance > 10:  # NEW: mild flow
            votes['flow_buy_mild'] = 0.4 * 1.4
        elif signal.order_flow_imbalance < -20:  # Was -35
            votes['flow_sell'] = -1.0 * 1.4
        elif signal.order_flow_imbalance < -10:  # NEW: mild flow
            votes['flow_sell_mild'] = -0.4 * 1.4
        
        # Voto 7: Market Intention (Peso: 1.7)
        if signal.market_intention == MarketIntention.WHALE_TRAP:
            votes['trap_alert'] = -1.5 * 1.7
        elif signal.market_intention == MarketIntention.SMART_REVERSAL:
            votes['reversal_opportunity'] = 1.5 * 1.7
        
        return votes
    
    # ═════════════════════════════════════════════════════════════════════════
    # CÁLCULO DE INTENCIÓN DE MERCADO
    # ═════════════════════════════════════════════════════════════════════════
    
    def _score_accumulation(self, 
                           obv: float,
                           ad_line: float,
                           imbalance: float) -> MarketIntention:
        """Determina intención de mercado con IA profunda"""
        
        # Acumulación: OBV sube, A/D sube, flujo positivo
        if obv > 0 and ad_line > 0 and imbalance > 40:
            return MarketIntention.ACCUMULATION
        
        # Distribución: OBV baja, A/D baja, flujo negativo
        if obv < 0 and ad_line < 0 and imbalance < -40:
            return MarketIntention.DISTRIBUTION
        
        # Liquidación: Volumen alto, cierre abrupto
        if imbalance < -70 and ad_line < -1000:
            return MarketIntention.LIQUIDATION
        
        return MarketIntention.EQUILIBRIUM
    
    # ═════════════════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: ANALYZE
    # ═════════════════════════════════════════════════════════════════════════
    
    def analyze(self, genome: Dict) -> SmartMoneySignal:
        """
        Análisis completo con todos los 7 sistemas de inteligencia
        
        Retorna: SmartMoneySignal con decisión ponderada
        """
        try:
            # Validar genome
            if not self._validate_genome(genome):
                return self._empty_signal()
            
            # Sistema 1: OBV
            obv = self._calculate_obv(genome)
            
            # Sistema 2: A/D Line
            ad_line = self._calculate_ad_line(genome)
            
            # Sistema 3: Volume Profile
            volume_profile = self._build_volume_profile(genome)
            
            # Sistema 4: Order Flow Imbalance
            order_flow_imbalance = self._calculate_order_flow_imbalance(genome)
            
            # Sistema 5: Sweep Detection
            sweep_type, sweep_direction = self._detect_sweeps(genome)
            
            # Sistema 6: False Break Detection
            false_break_prob = self._detect_false_breaks(genome)
            
            # Sistema 7: Whale Confidence
            whale_confidence = self._calculate_whale_confidence(
                obv, ad_line, order_flow_imbalance, sweep_type
            )
            
            # Determinar intención de mercado
            market_intention = self._score_accumulation(obv, ad_line, order_flow_imbalance)
            
            # Crear signal
            signal = SmartMoneySignal(
                obv=obv,
                ad_line=ad_line,
                volume_profile=volume_profile,
                order_flow_imbalance=order_flow_imbalance,
                sweep_type=sweep_type,
                sweep_direction=sweep_direction,
                false_break_probability=false_break_prob,
                market_intention=market_intention,
                whale_confidence=whale_confidence,
                timestamp=datetime.now().isoformat()
            )
            
            # SISTEMA DE VOTACIÓN PONDERADA - Ahora con contexto de tendencia
            signal.votes = self._calculate_weighted_votes(signal, genome)
            signal.total_vote_weight = sum(signal.votes.values())
            
            # Decisión final basada en votación
            signal = self._make_decision(signal)
            
            # Log detallado
            self._log_analysis(signal)
            
            # Guardar en histórico
            self.history.append(signal)
            
            return signal
        
        except Exception as e:
            logger.error(f"❌ Error en análisis LLM6: {str(e)}", exc_info=True)
            return self._empty_signal()
    
    # ═════════════════════════════════════════════════════════════════════════
    # DECISIÓN FINAL CON VOTACIÓN
    # ═════════════════════════════════════════════════════════════════════════
    
    def _make_decision(self, signal: SmartMoneySignal) -> SmartMoneySignal:
        """Toma decisión basada en sistema de votación ponderada"""
        
        # Hard veto: False break > 75%
        if signal.false_break_probability > 75:
            signal.recommendation = "HOLD"
            signal.confidence = max(15, signal.whale_confidence * 0.2)  # Still show some activity
            signal.reasoning = f"🚫 HARD VETO: False break {signal.false_break_probability:.0f}%"
            return signal
        
        # BASE confidence from whale activity (always contributes)
        base_confidence = signal.whale_confidence * 0.5  # 50% of whale conf as base
        
        # Calcular puntuación ponderada
        if signal.votes:
            total_weight = signal.total_vote_weight
            
            if total_weight > 0.5:  # Voto COMPRA (lowered from 0.8 for faster response)
                signal.recommendation = "BUY"
                signal.confidence = min(100, base_confidence + 40 + (total_weight * 10))
                signal.reasoning = f"✅ COMPRA: Votos {total_weight:.1f} | Ballena {signal.whale_confidence:.0f}%"
            
            elif total_weight < -0.5:  # Voto VENTA (lowered from -0.8 for faster response)
                signal.recommendation = "SELL"
                signal.confidence = min(100, base_confidence + 40 + (abs(total_weight) * 10))
                signal.reasoning = f"✅ VENTA: Votos {total_weight:.1f} | Ballena {signal.whale_confidence:.0f}%"
            
            else:  # Neutral - but still show confidence based on activity
                signal.recommendation = "HOLD"
                signal.confidence = max(25, base_confidence + abs(total_weight) * 8)
                signal.reasoning = f"⏸️  HOLD: Votos {total_weight:.1f} | Ballena {signal.whale_confidence:.0f}%"
        
        else:
            signal.recommendation = "HOLD"
            signal.confidence = max(15, signal.whale_confidence * 0.3)  # Show some activity
            signal.reasoning = f"⏸️  HOLD: Sin votos | Ballena {signal.whale_confidence:.0f}%"
        
        return signal
    
    # ═════════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═════════════════════════════════════════════════════════════════════════
    
    def _validate_genome(self, genome: Dict) -> bool:
        """Valida formato de genome"""
        required_keys = ['closes', 'opens', 'highs', 'lows', 'volumes']
        
        # DEBUG: Log received keys
        received_keys = list(genome.keys())
        logger.debug(f"[DEBUG] Genome keys recibidas: {received_keys}")
        
        if not all(k in genome for k in required_keys):
            missing = [k for k in required_keys if k not in genome]
            logger.debug(f"[DEBUG] Faltan keys: {missing}, intentando extraer...")
            
            # Fallback 1: Extract from 'candles' array
            if 'candles' in genome and isinstance(genome['candles'], list) and len(genome['candles']) >= 3:
                candles = genome['candles']
                genome['closes'] = [c.get('close', c.get('c', 0)) for c in candles]
                genome['opens'] = [c.get('open', c.get('o', 0)) for c in candles]
                genome['highs'] = [c.get('high', c.get('h', 0)) for c in candles]
                genome['lows'] = [c.get('low', c.get('l', 0)) for c in candles]
                genome['volumes'] = [c.get('volume', c.get('v', c.get('tick_volume', 100))) for c in candles]
                logger.info(f"[LLM6] Extracted OHLCV from candles: {len(genome['closes'])} bars")
                return True
            
            # Fallback 2: Extract from bar_data.history
            if 'bar_data' in genome:
                bar_data = genome['bar_data']
                if isinstance(bar_data, dict) and 'history' in bar_data:
                    bar_history = bar_data['history']
                    if bar_history and len(bar_history) >= 3:
                        genome['closes'] = [h.get('close', 0) for h in bar_history]
                        genome['opens'] = [h.get('open', 0) for h in bar_history]
                        genome['highs'] = [h.get('high', 0) for h in bar_history]
                        genome['lows'] = [h.get('low', 0) for h in bar_history]
                        genome['volumes'] = [h.get('volume', 0) for h in bar_history]
                        logger.info(f"[LLM6] Extracted OHLCV from bar_data.history: {len(genome['closes'])} bars")
                        return True
                # bar_data might be a list directly
                elif isinstance(bar_data, list) and len(bar_data) >= 3:
                    genome['closes'] = [h.get('close', 0) for h in bar_data]
                    genome['opens'] = [h.get('open', 0) for h in bar_data]
                    genome['highs'] = [h.get('high', 0) for h in bar_data]
                    genome['lows'] = [h.get('low', 0) for h in bar_data]
                    genome['volumes'] = [h.get('volume', 0) for h in bar_data]
                    logger.info(f"[LLM6] Extracted OHLCV from bar_data list: {len(genome['closes'])} bars")
                    return True
            
            # Fallback 3: Extract from 'prices' if it's OHLCV
            if 'prices' in genome and isinstance(genome['prices'], list) and len(genome['prices']) >= 3:
                prices = genome['prices']
                if isinstance(prices[0], dict):
                    genome['closes'] = [p.get('close', p.get('c', 0)) for p in prices]
                    genome['opens'] = [p.get('open', p.get('o', 0)) for p in prices]
                    genome['highs'] = [p.get('high', p.get('h', 0)) for p in prices]
                    genome['lows'] = [p.get('low', p.get('l', 0)) for p in prices]
                    genome['volumes'] = [p.get('volume', p.get('v', 100)) for p in prices]
                    logger.info(f"[LLM6] Extracted OHLCV from prices: {len(genome['closes'])} bars")
                    return True
                else:
                    # prices is just a list of close prices
                    genome['closes'] = list(prices)
                    genome['opens'] = list(prices)
                    genome['highs'] = [p * 1.001 for p in prices]
                    genome['lows'] = [p * 0.999 for p in prices]
                    genome['volumes'] = [100] * len(prices)
                    logger.info(f"[LLM6] Extracted closes from prices list: {len(genome['closes'])} bars")
                    return True
            
            # Fallback 4: Use current_price to generate synthetic data
            if 'current_price' in genome or 'price' in genome:
                price = genome.get('current_price', genome.get('price', 150.00))
                genome['closes'] = [price] * 50
                genome['opens'] = [price] * 50
                genome['highs'] = [price * 1.0001] * 50
                genome['lows'] = [price * 0.9999] * 50
                genome['volumes'] = [100] * 50
                logger.warning(f"[LLM6] Using synthetic data from current_price: {price}")
                return True
            
            logger.error(f"[LLM6] Genome invalido: No se pudo extraer OHLCV")
            return False
        
        if any(len(genome[k]) < 3 for k in required_keys):
            logger.error(f"[LLM6] Genome: Datos insuficientes")
            return False
        
        return True
    
    def _empty_signal(self) -> SmartMoneySignal:
        """Retorna signal vacío/neutral"""
        return SmartMoneySignal(
            obv=0.0,
            ad_line=0.0,
            volume_profile={},
            order_flow_imbalance=0.0,
            sweep_type=SweepType.NONE,
            false_break_probability=0.0,
            market_intention=MarketIntention.EQUILIBRIUM,
            whale_confidence=0.0,
            recommendation="HOLD",
            confidence=0.0,
            reasoning="No hay datos suficientes",
            timestamp=datetime.now().isoformat()
        )
    
    def _log_analysis(self, signal: SmartMoneySignal):
        """Log detallado del análisis"""
        # Detectar si hubo trampa
        trap_detected = 'sweep_trap' in signal.votes
        trap_status = "🪤 TRAP DETECTED!" if trap_detected else "Normal"
        
        logger.info(f"""
        ╔════════════════════════════════════════════════════╗
        ║            LLM6 SMART MONEY ANALYSIS               ║
        ╠════════════════════════════════════════════════════╣
        ║ Market Intention:    {signal.market_intention.value:30s} ║
        ║ Sweep Type:          {signal.sweep_type.value:30s} ║
        ║ Sweep Context:       {trap_status:30s} ║
        ║ False Break Prob:    {signal.false_break_probability:30.1f}% ║
        ║ Whale Confidence:    {signal.whale_confidence:30.1f}% ║
        ║ Order Flow:          {signal.order_flow_imbalance:30.1f}   ║
        ║ Votes Weight:        {signal.total_vote_weight:30.2f}   ║
        ║ RECOMMENDATION:      {signal.recommendation:30s} ║
        ║ Confidence:          {signal.confidence:30.1f}% ║
        ║ Reasoning:           {signal.reasoning:30s} ║
        ╚════════════════════════════════════════════════════╝
        """)
    
    def get_port_config(self) -> Dict:
        """Retorna configuración de puertos para integración"""
        return {
            'trinity_port': 5001,
            'kraken_port': 5002,
            'executor_port': 5003,
            'llm6_port': 5004,
            'quantum_port': 5005,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TCP SERVER - HANDLE CLIENT CONNECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def handle_client(sock: socket.socket, addr: tuple, llm6: 'LLM6_SmartMoney'):
    """Maneja conexión TCP de cliente"""
    sock.settimeout(30)
    try:
        while True:
            try:
                # Recibir 4-byte length prefix
                ld = sock.recv(4)
                
                # PING/ACK protocol
                if ld and b'PING' in ld[:4]:
                    pong_msg = struct.pack('>I', 4) + b'PONG'
                    sock.sendall(pong_msg)
                    logger.debug(f"[PING] Respondido a {addr}")
                    continue
                
                if not ld or len(ld) != 4:
                    break
                
                # Desempacar longitud
                length = struct.unpack('>I', ld)[0]
                if length > 10_000_000:  # Max 10MB
                    logger.warning(f"[CLIENT {addr}] Longitud inválida: {length}")
                    break
                
                # Recibir payload
                data = b''
                while len(data) < length:
                    chunk = sock.recv(min(4096, length - len(data)))
                    if not chunk:
                        break
                    data += chunk
                
                if not data:
                    break
                
                try:
                    # Decodificar y analizar
                    decoded = data.decode('utf-8', errors='replace')
                    request = json.loads(decoded)
                    
                    logger.debug(f"[LLM6 RX] Claves: {list(request.keys())}")
                    
                    # Ejecutar análisis
                    signal = llm6.analyze(request)
                    
                    # Determinar si hay trampa (sweep invertido)
                    is_trap = 'sweep_trap' in signal.votes
                    
                    # La dirección recomendada del sweep:
                    # - Si es trampa, la dirección se invierte (la señal del sweep es falsa)
                    # - Si no es trampa, usar la dirección original del sweep
                    recommended_direction = signal.sweep_direction
                    if is_trap and signal.sweep_direction:
                        # Invertir: BUY→SELL, SELL→BUY
                        recommended_direction = 'SELL' if signal.sweep_direction == 'BUY' else 'BUY'
                    
                    # Preparar respuesta
                    response = {
                        'recommendation': signal.recommendation,
                        'confidence': signal.confidence,
                        'false_break_probability': signal.false_break_probability,
                        'whale_confidence': signal.whale_confidence,
                        'market_intention': signal.market_intention.value,
                        'sweep_type': signal.sweep_type.value,
                        'sweep_direction': recommended_direction,  # Dirección RECOMENDADA (invertida si trampa)
                        'sweep_direction_raw': signal.sweep_direction,  # Dirección original del sweep
                        'is_trap': is_trap,  # Indica si el sweep es una trampa
                        'reasoning': signal.reasoning,
                        'votes': signal.votes,
                        'total_vote_weight': signal.total_vote_weight,
                    }
                    
                    response_json = json.dumps(response).encode('utf-8')
                    sock.sendall(struct.pack('>I', len(response_json)) + response_json)
                    
                    logger.debug(f"[LLM6 TX] Enviado a {addr}: {signal.recommendation}")
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as je:
                    logger.warning(f"[CLIENT {addr}] Datos inválidos: {je}")
                    error_resp = {
                        "recommendation": "HOLD",
                        "confidence": 0,
                        "reasoning": "Error decodificando request"
                    }
                    error_json = json.dumps(error_resp).encode('utf-8')
                    try:
                        sock.sendall(struct.pack('>I', len(error_json)) + error_json)
                    except:
                        pass
                    break
                    
            except socket.timeout:
                logger.debug(f"[CLIENT {addr}] Timeout")
                break
            except Exception as e:
                logger.warning(f"[CLIENT {addr}] Error: {e}")
                break
    except Exception as e:
        logger.error(f"[CLIENT {addr}] Error fatal: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
        logger.info(f"[DISCONNECT] {addr}")




def run_tcp_server():
    """TCP server listening on config port"""
    
    # USDJPY M5 - Port 7862 (matches jpyquantum_core.py Config.LLM6_PORT)
    try:
        with open('jpyconfig.yaml', 'r') as f:
            config = yaml.safe_load(f) or {}
        port = config.get('llm_settings', {}).get('llm6_port', 7862)
    except Exception as e:
        port = 7862  # FIXED: Was 7860, now matches jpyquantum_core Config
    
    # Colores ANSI para banner NOVA
    Y = '\033[93m'  # Amarillo
    W = '\033[97m'  # Blanco
    G = '\033[92m'  # Verde
    C = '\033[96m'  # Cyan
    D = '\033[90m'  # Dim
    R = '\033[0m'   # Reset
    
    # Banner NOVA
    print(f"""
{Y}+{'='*62}+{R}
{Y}|{R}                                                              {Y}|{R}
{Y}|{R}  {Y}███╗   ██╗{W} ██████╗ ██╗   ██╗ █████╗ {R}                       {Y}|{R}
{Y}|{R}  {Y}████╗  ██║{W}██╔═══██╗██║   ██║██╔══██╗{R}   {C}LLM6 SMART MONEY{R}    {Y}|{R}
{Y}|{R}  {Y}██╔██╗ ██║{W}██║   ██║██║   ██║███████║{R}   {D}Whale Detection{R}     {Y}|{R}
{Y}|{R}  {Y}██║╚██╗██║{W}██║   ██║╚██╗ ██╔╝██╔══██║{R}                       {Y}|{R}
{Y}|{R}  {Y}██║ ╚████║{W}╚██████╔╝ ╚████╔╝ ██║  ██║{R}                       {Y}|{R}
{Y}|{R}  {Y}╚═╝  ╚═══╝{W} ╚═════╝   ╚═══╝  ╚═╝  ╚═╝{R}                       {Y}|{R}
{Y}|{R}                                                              {Y}|{R}
{Y}+{'-'*62}+{R}
{Y}|{R}  {W}Smart Money Oracle v2.0{R}      {D}by Polarice Labs © 2026{R}      {Y}|{R}
{Y}|{R}  {G}● PORT: {port}{R}                  {D}7 Intelligence Systems{R}     {Y}|{R}
{Y}+{'='*62}+{R}
""")
    
    llm6 = LLM6_SmartMoney()
    
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_sock = None
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512 * 1024)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512 * 1024)
        server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        server_sock.bind(('127.0.0.1', port))
        server_sock.listen(5)
        print(f"\n✓ LLM6 listening on 127.0.0.1:{port}")
        print("  (Press Ctrl+C to stop)\n")
        logger.info(f"LLM6 Smart Money Oracle Active on 127.0.0.1:{port}")
        
        while running:
            try:
                server_sock.settimeout(1.0)
                client_sock, addr = server_sock.accept()
                
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, addr, llm6),
                    daemon=True,
                    name=f"LLM6Handler-{addr[0]}"
                )
                thread.start()
                
            except socket.timeout:
                continue
            except OSError as ose:
                if ose.errno == 10048:
                    time.sleep(2)
                    continue
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        if server_sock:
            try:
                server_sock.close()
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN - SERVER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        run_tcp_server()
    except KeyboardInterrupt:
        logger.info("🛑 LLM6 detenido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
