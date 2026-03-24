#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
                    NOVA TRADING AI - LLM1 BAYESIAN EXPERT                 
                    USDJPY M5 - Directional Momentum Edition                  
                       by Polarice Labs © 2026                                
════════════════════════════════════════════════════════════════════════════════
  Inteligencia Bayesiana + Market Regime Detection + 5-7 Min Prediction       
  Predicción direccional clara para movimientos de 5-7 minutos                
════════════════════════════════════════════════════════════════════════════════
"""
import sys, os
# [USDJPY] Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socket, struct, json, logging, threading, time, re, pickle
import requests
from datetime import datetime
from collections import defaultdict, deque
import numpy as np

# ===== PATTERN & DIVERGENCE DETECTION =====
try:
    from pattern_library import get_pattern_detector
    from rsi_divergence_detector import get_divergence_detector
    PATTERN_DETECTOR = get_pattern_detector()
    DIVERGENCE_DETECTOR = get_divergence_detector()
    PATTERN_DIVERGENCE_ENABLED = True
except ImportError as e:
    log_err = f"WARNING: Pattern/Divergence detectors not available: {e}"
    PATTERN_DETECTOR = None
    DIVERGENCE_DETECTOR = None
    PATTERN_DIVERGENCE_ENABLED = False

# ===== HARMONIC PATTERN DETECTION (NEW) =====
try:
    from advanced_patterns import AdvancedPatternEngine
    HARMONIC_ENGINE = AdvancedPatternEngine()
    HARMONIC_PATTERNS_ENABLED = True
except ImportError as e:
    HARMONIC_ENGINE = None
    HARMONIC_PATTERNS_ENABLED = False

# ===== DIAGNOSTIC TRACER =====
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | LLM1_EXPERTO | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

# ═══════════════════════════════════════════════════════════════════════════
# TARGET: LOAD PORTS FROM CENTRALIZED CONFIG (jpyconfig.yaml)
# ═══════════════════════════════════════════════════════════════════════════
try:
    from jpy_config_loader import get_llm_port, get_sound_port
    EU_CONFIG_LOADED = True
except ImportError:
    EU_CONFIG_LOADED = False

OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "llama3:8b"  # Fast model for M5 responsiveness
OLLAMA_TIMEOUT = 8.0  # OPTIMIZED: Fast for M5 5-min predictions

class BayesianMarketModel:
    """Model probabilístico de regímenes de mercado con aprendizaje online"""
    def __init__(self):
        self.prior_trending = 0.33
        self.prior_ranging = 0.34
        self.prior_volatile = 0.33
        self.learning_rate = 0.05
    
    def detect_regime(self, adx, atr_pct, rsi, rsi_std):
        """Detecta régimen: TRENDING, RANGING, VOLATILE usando Bayes"""
        # Likelihood bayesiana
        p_trending = (1.0 if adx > 25 else 0.5 if adx > 15 else 0.2) * self.prior_trending
        p_ranging = (1.0 if adx < 20 else 0.5 if adx < 30 else 0.2) * self.prior_ranging
        p_volatile = (1.0 if atr_pct > 2.0 else 0.5 if atr_pct > 1.0 else 0.2) * self.prior_volatile
        
        # Normalizar (Bayes rule)
        total = p_trending + p_ranging + p_volatile
        if total == 0:
            return 'UNKNOWN', 0.33
        
        p_trending /= total
        p_ranging /= total
        p_volatile /= total
        
        # Seleccionar máxima
        regime = max(
            ('TRENDING', p_trending),
            ('RANGING', p_ranging),
            ('VOLATILE', p_volatile),
            key=lambda x: x[1]
        )
        return regime[0], regime[1]
    
    def update_priors(self, observed_regime):
        """Actualiza priors basado en observaciones (aprendizaje en línea)"""
        if observed_regime == 'TRENDING':
            self.prior_trending = min(1.0, self.prior_trending + self.learning_rate)
        elif observed_regime == 'RANGING':
            self.prior_ranging = min(1.0, self.prior_ranging + self.learning_rate)
        elif observed_regime == 'VOLATILE':
            self.prior_volatile = min(1.0, self.prior_volatile + self.learning_rate)
        
        # Normalizar
        total = self.prior_trending + self.prior_ranging + self.prior_volatile
        self.prior_trending /= total
        self.prior_ranging /= total
        self.prior_volatile /= total

class PredictiveConfidenceCalibrator:
    """Calibra confianza de predicciones basado en accuracy histórico"""
    def __init__(self):
        self.accuracy_history = defaultdict(deque)  # signal -> deque of results
        self.min_samples = 5
        self.max_history = 100
    
    def get_calibrated_confidence(self, base_confidence, signal):
        """Ajusta confianza basado en accuracy del signal"""
        # BUGFIX: Deshabilitar calibración mientras hay < 20 muestras históricos
        # Esto previene un ciclo de retroalimentación donde confianza baja mata toda señal
        if signal not in self.accuracy_history or len(self.accuracy_history[signal]) < 20:
            return base_confidence  # Retornar sin calibración durante warmup
        
        accuracy = sum(self.accuracy_history[signal]) / len(self.accuracy_history[signal])
        # IMPORTANTE: No calibrar por debajo de 0.6 accuracy (60%)
        # Esto previene que un mal streak mate completamente la confianza
        accuracy = max(0.6, accuracy)
        return int(base_confidence * accuracy)
    
    def record_result(self, signal, was_correct):
        """Registra si la predicción fue correcta"""
        if signal not in self.accuracy_history:
            self.accuracy_history[signal] = deque(maxlen=self.max_history)
        self.accuracy_history[signal].append(1.0 if was_correct else 0.0)
    
    def get_accuracy_stats(self, signal=None):
        """Retorna estadísticas de accuracy"""
        if signal:
            if signal not in self.accuracy_history or len(self.accuracy_history[signal]) == 0:
                return {'samples': 0, 'accuracy': 0.0}
            hist = list(self.accuracy_history[signal])
            return {
                'samples': len(hist),
                'accuracy': sum(hist) / len(hist) if hist else 0.0
            }
        else:
            all_results = [r for hist in self.accuracy_history.values() for r in hist]
            return {
                'samples': len(all_results),
                'accuracy': sum(all_results) / len(all_results) if all_results else 0.0
            }

class IndicatorConsensusAnalyzer:
    """Analiza consenso inteligente entre todos los indicadores"""
    def __init__(self):
        self.signal_weights = {
            'trend': 0.30,
            'momentum': 0.30,
            'volatility': 0.20,
            'volume': 0.10,
            'patterns': 0.10,
        }
    
    def analyze_consensus(self, indicators_dict):
        """Calcula consenso ponderado de indicadores"""
        consensus_scores = defaultdict(float)  # BUY, SELL, HOLD -> score
        
        # Tendencia (30%) - RECALIBRADO para generar m\u00e1s se\u00f1ales
        adx = indicators_dict.get('adx', 20)
        sma_aligned = indicators_dict.get('price_above_sma50', False)
        
        if adx > 18 and sma_aligned:  # Bajado de 25 a 18
            consensus_scores['BUY'] += 0.45  # Aumentado de 0.30 a 0.45
        elif adx > 18 and not sma_aligned:  # Bajado de 25 a 18
            consensus_scores['SELL'] += 0.45  # Aumentado de 0.30 a 0.45
        elif adx > 15:  # Agregado: ADX moderado
            if sma_aligned:
                consensus_scores['BUY'] += 0.20
            else:
                consensus_scores['SELL'] += 0.20
        else:
            consensus_scores['HOLD'] += 0.10  # Reducido de 0.30 a 0.10
        
        # Momentum (30%) - RECALIBRADO
        rsi = indicators_dict.get('rsi', 50)
        macd_h = indicators_dict.get('macd_histogram', 0)
        
        if rsi < 35 and macd_h < 0:  # Bajado de 30 a 35
            consensus_scores['BUY'] += 0.45  # Aumentado de 0.30 a 0.45
        elif rsi > 65 and macd_h > 0:  # Bajado de 70 a 65
            consensus_scores['SELL'] += 0.45  # Aumentado de 0.30 a 0.45
        elif 35 < rsi < 65:  # Expandido de 40-60
            if abs(macd_h) > 0.001:
                consensus_scores['BUY' if macd_h > 0 else 'SELL'] += 0.20
            else:
                consensus_scores['HOLD'] += 0.10  # Reducido de 0.30 a 0.10
        else:
            consensus_scores['BUY'] += 0.25 if rsi < 50 else 0.0  # Aumentado de 0.15 a 0.25
            consensus_scores['SELL'] += 0.25 if rsi > 50 else 0.0  # Aumentado de 0.15 a 0.25
        
        # Volatilidad (20%) - MEJORADO
        atr = indicators_dict.get('atr_14', 10)
        bb_pct = indicators_dict.get('bb_percent_b', 0.5)
        
        if bb_pct < 0.25:  # Aumentado de 0.2
            consensus_scores['BUY'] += 0.25  # Aumentado de 0.20
        elif bb_pct > 0.75:  # Bajado de 0.8
            consensus_scores['SELL'] += 0.25  # Aumentado de 0.20
        else:
            consensus_scores['HOLD'] += 0.08  # Reducido de 0.20
        
        # Volumen (10%) - IMPACTO AMPLIFICADO
        obv_trend = indicators_dict.get('obv_trend', 'NEUTRAL')
        if obv_trend == 'UP':
            consensus_scores['BUY'] += 0.15  # Aumentado de 0.10
        elif obv_trend == 'DOWN':
            consensus_scores['SELL'] += 0.15  # Aumentado de 0.10
        else:
            consensus_scores['HOLD'] += 0.03  # Reducido de 0.10
        
        # Patrones (10%) - AMPLIFICADO
        pattern = indicators_dict.get('pattern', 'NEUTRAL')
        if pattern in ['BULLISH', 'ENGULFING_UP']:
            consensus_scores['BUY'] += 0.15  # Aumentado de 0.10
        elif pattern in ['BEARISH', 'ENGULFING_DOWN']:
            consensus_scores['SELL'] += 0.15  # Aumentado de 0.10
        else:
            consensus_scores['HOLD'] += 0.03  # Reducido de 0.10
        
        # Normalizar y retornar
        total = sum(consensus_scores.values())
        if total > 0:
            consensus_scores = {k: v/total for k, v in consensus_scores.items()}
        
        return consensus_scores

class TemporalPredictor:
    """[CLOCK] Predice movimientos próximos 5-60 segundos (CRÍTICO PARA TIMING)"""
    def __init__(self):
        self.momentum_history = deque(maxlen=50)
        self.acceleration_history = deque(maxlen=50)
    
    def predict_next_direction(self, prices, timestamps=None):
        """Predice dirección próximos 60 segundos basado en momentum"""
        if len(prices) < 5:
            return {'direction': 'UNKNOWN', 'confidence': 0, 'momentum': 0}
        
        prices_array = np.array(prices[-20:], dtype=np.float64)
        
        # 1. Calcular velocidad (cambio de precio)
        velocity = np.diff(prices_array)
        
        # 2. Calcular aceleración (cambio de velocidad)
        if len(velocity) >= 2:
            acceleration = np.diff(velocity)
            recent_accel = np.mean(acceleration[-5:])
        else:
            recent_accel = 0
        
        # 3. Momentum = promedio ponderado de cambios recientes
        # BUGFIX #26: Normalize momentum by length to prevent exponential scaling
        recent_velocity = np.mean(velocity[-5:])
        momentum = recent_velocity + (recent_accel / max(1, len(velocity)))  # Normalized, not multiplied by len
        
        # 4. Dirección
        direction = 'UP' if momentum > 0 else 'DOWN' if momentum < 0 else 'NEUTRAL'
        
        # 5. Confianza basada en consistencia
        if len(velocity) >= 10:
            consistency = 1.0 / (1.0 + np.std(velocity[-10:]) / (abs(np.mean(velocity[-10:])) + 1e-10))
        else:
            consistency = 0.5
        
        confidence = int(min(95, max(20, consistency * 100)))
        
        self.momentum_history.append(momentum)
        self.acceleration_history.append(recent_accel)
        
        return {
            'direction': direction,
            'confidence': confidence,
            'momentum': round(momentum, 6),
            'acceleration': round(recent_accel, 6),
            'signal_strength': 'STRONG' if confidence > 70 else 'MODERATE' if confidence > 50 else 'WEAK',
        }
    
    def get_momentum_trend(self):
        """¿Momentum está aumentando o disminuyendo?"""
        if len(self.momentum_history) < 5:
            return 'INSUFFICIENT_DATA'
        
        recent = list(self.momentum_history)[-5:]
        trend = np.mean(recent) > np.mean(list(self.momentum_history)[-10:-5])
        return 'ACCELERATING' if trend else 'DECELERATING'

class MultiTimeframeValidator:
    """[CHART] Valida setup en múltiples timeframes (4H, 1D) +12pts"""
    
    def validate_setup(self, prices_1h, prices_4h, prices_1d):
        """Valida cuánto soportan 4H y 1D el setup de 1H"""
        if len(prices_1h) < 20 or len(prices_4h) < 20 or len(prices_1d) < 20:
            return {'valid': False, 'score': 0, 'reason': 'Insufficient data'}
        
        # Calcular momentum en cada timeframe
        momentum_1h = np.mean(np.diff(prices_1h[-5:]))
        momentum_4h = np.mean(np.diff(prices_4h[-5:]))
        momentum_1d = np.mean(np.diff(prices_1d[-5:]))
        
        # Validar que dirección sea consistent
        direction_1h = 'UP' if momentum_1h > 0 else 'DOWN'
        direction_4h = 'UP' if momentum_4h > 0 else 'DOWN'
        direction_1d = 'UP' if momentum_1d > 0 else 'DOWN'
        
        # Score: cuántos TF confirman
        confirms = 0
        if direction_1h == direction_4h:
            confirms += 1
        if direction_1h == direction_1d:
            confirms += 1
        if direction_4h == direction_1d:
            confirms += 1
        
        score = (confirms / 3.0) * 100
        
        # Penalidad si 4H/1D no soportan
        if direction_1h != direction_4h or direction_1h != direction_1d:
            score = max(0, score - 30)
        
        return {
            'valid': score > 30,
            'score': int(score),
            'direction_1h': direction_1h,
            'direction_4h': direction_4h,
            'direction_1d': direction_1d,
            'confirms': confirms,
            'reason': f'{confirms} TF confirm' if confirms > 0 else 'Dirección divergente',
        }

class RegimeShiftPredictor:
    """[WARNING]  Predice cambio de régimen 3-5 barras antes (+9pts)"""
    
    def __init__(self):
        self.adx_history = deque(maxlen=20)
        self.atr_history = deque(maxlen=20)
        self.rsi_std_history = deque(maxlen=20)
    
    def predict_regime_shift(self, adx, atr, rsi_std):
        """Detecta si régimen está a punto de cambiar"""
        self.adx_history.append(adx)
        self.atr_history.append(atr)
        self.rsi_std_history.append(rsi_std)
        
        if len(self.adx_history) < 5:
            return {'shift_imminent': False, 'warning_level': 0, 'reason': 'Warming up'}
        
        # Calcular derivadas (cambios de slope)
        recent_adx = list(self.adx_history)[-5:]
        recent_atr = list(self.atr_history)[-5:]
        
        adx_change = recent_adx[-1] - recent_adx[0]  # Cambio en 5 barras
        atr_change = recent_atr[-1] - recent_atr[0]
        
        warning_level = 0
        reasons = []
        
        # WARNING: ADX está bajando fuerte (trending → no trending)
        if adx_change < -5:
            warning_level += 40
            reasons.append('ADX declining fast')
        
        # WARNING: ATR está subiendo fuerte (calming → volatile)
        if atr_change > np.mean(recent_atr) * 0.5:
            warning_level += 40
            reasons.append('ATR spiking')
        
        # WARNING: RSI volatilidad extrema
        if rsi_std > 20:
            warning_level += 20
            reasons.append('RSI std high')
        
        warning_level = min(100, warning_level)
        shift_imminent = warning_level > 60
        
        return {
            'shift_imminent': shift_imminent,
            'warning_level': warning_level,  # 0-100
            'reason': ' + '.join(reasons) if reasons else 'No warnings',
            'adx_trend': 'declining' if adx_change < 0 else 'rising',
            'atr_trend': 'rising' if atr_change > 0 else 'declining',
        }

class LLM1Experto:
    """[BRAIN] Experto Trading Bayesiano con Inteligencia Superior"""
    
    def __init__(self):
        print("="*70)
        print("[BRAIN] LLM1 EXPERTO AI - CONSCIOUSNESS EDITION")
        print(f"   Bayesian Intelligence + Temporal Prediction + Learning")
        print(f"   Ollama: {OLLAMA_HOST}:{OLLAMA_PORT}")
        print("="*70)
        
        self.market_history = {}
        self.last_analysis = {}
        self.bayes_model = BayesianMarketModel()
        self.confidence_calibrator = PredictiveConfidenceCalibrator()
        self.consensus_analyzer = IndicatorConsensusAnalyzer()
        self.temporal_predictor = TemporalPredictor()  # [SPARKLE] NUEVO: Predicción temporal
        self.mtf_validator = MultiTimeframeValidator()  # [SPARKLE] NUEVO: Validación multi-TF (+12)
        self.regime_shift = RegimeShiftPredictor()  # [SPARKLE] NUEVO: Predicción de cambio régimen (+9)
        
        # ============================================================
        # [MEMORY] SISTEMA DE MEMORIA INTELIGENTE - CONTEXTO M1
        # ============================================================
        self.signal_memory = deque(maxlen=50)  # Últimas 50 señales
        self.pattern_memory = {
            'last_regime': None,
            'regime_duration': 0,
            'consecutive_buys': 0,
            'consecutive_sells': 0,
            'last_rsi_extreme': None,
            'last_rsi_extreme_time': 0,
            'trend_reversal_count': 0,
            'avg_confidence_last_10': 50,
            'win_streak': 0,
            'loss_streak': 0,
            'last_direction': None,
            'direction_strength': 0,
        }
        self.market_context = {
            'price_high_1h': 0,
            'price_low_1h': float('inf'),
            'price_range_1h': 0,
            'volatility_trend': 'STABLE',
            'support_levels': [],
            'resistance_levels': [],
        }
        
        self.learning_file = 'llm1_learning.pkl'
        self._load_learning()
    
    def _load_learning(self):
        """Carga histórico de learning si existe"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'rb') as f:
                    data = pickle.load(f)
                    # BUGFIX: Asegurar que accuracy_history es defaultdict(deque), no dict normal
                    loaded_hist = data.get('accuracy_history', {})
                    self.confidence_calibrator.accuracy_history = defaultdict(deque)
                    for signal, values in (loaded_hist.items() if isinstance(loaded_hist, dict) else []):
                        self.confidence_calibrator.accuracy_history[signal] = deque(values, maxlen=100) if isinstance(values, (list, tuple)) else deque([values], maxlen=100)
                    
                    self.bayes_model.prior_trending = data.get('prior_trending', 0.33)
                    self.bayes_model.prior_ranging = data.get('prior_ranging', 0.34)
                    self.bayes_model.prior_volatile = data.get('prior_volatile', 0.33)
                    log.info(f"[OK] Learning loaded: {len(self.confidence_calibrator.accuracy_history)} signals")
            except Exception as e:
                log.warning(f"[WARNING]  Could not load learning: {e}")
    
    def _save_learning(self):
        """Persiste learning para futuras sesiones"""
        try:
            data = {
                'accuracy_history': dict(self.confidence_calibrator.accuracy_history),
                'prior_trending': self.bayes_model.prior_trending,
                'prior_ranging': self.bayes_model.prior_ranging,
                'prior_volatile': self.bayes_model.prior_volatile,
            }
            with open(self.learning_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            log.warning(f"[WARNING]  Could not save learning: {e}")
    
    # ============================================================
    # [MEMORY] SISTEMA DE MEMORIA INTELIGENTE - ACTUALIZACIÓN
    # ============================================================
    def _update_memory(self, decision, confidence, regime, rsi, price, trend_strength):
        """Actualiza memoria de señales y contexto de mercado"""
        now = time.time()
        
        # Guardar señal en memoria
        signal = {
            'time': now,
            'decision': decision,
            'confidence': confidence,
            'regime': regime,
            'rsi': rsi,
            'price': price,
            'trend_strength': trend_strength
        }
        self.signal_memory.append(signal)
        
        # Actualizar pattern_memory
        pm = self.pattern_memory
        
        # Detectar cambio de régimen
        if pm['last_regime'] != regime:
            if pm['last_regime'] is not None:
                pm['trend_reversal_count'] += 1
            pm['last_regime'] = regime
            pm['regime_duration'] = 1
        else:
            pm['regime_duration'] += 1
        
        # Actualizar contadores de dirección
        if decision == 'BUY':
            pm['consecutive_buys'] += 1
            pm['consecutive_sells'] = 0
        elif decision == 'SELL':
            pm['consecutive_sells'] += 1
            pm['consecutive_buys'] = 0
        else:  # HOLD
            pm['consecutive_buys'] = 0
            pm['consecutive_sells'] = 0
        
        # Detectar RSI extremos
        if rsi < 30:
            pm['last_rsi_extreme'] = 'OVERSOLD'
            pm['last_rsi_extreme_time'] = now
        elif rsi > 70:
            pm['last_rsi_extreme'] = 'OVERBOUGHT'
            pm['last_rsi_extreme_time'] = now
        
        # Calcular confianza promedio últimas 10 señales
        if len(self.signal_memory) >= 10:
            last_10_conf = [s['confidence'] for s in list(self.signal_memory)[-10:]]
            pm['avg_confidence_last_10'] = sum(last_10_conf) / len(last_10_conf)
        
        # Actualizar dirección dominante
        if decision in ['BUY', 'SELL']:
            if pm['last_direction'] == decision:
                pm['direction_strength'] = min(10, pm['direction_strength'] + 1)
            else:
                pm['last_direction'] = decision
                pm['direction_strength'] = 1
        
        # Actualizar contexto de mercado (high/low 1h)
        mc = self.market_context
        mc['price_high_1h'] = max(mc['price_high_1h'], price)
        mc['price_low_1h'] = min(mc['price_low_1h'], price)
        mc['price_range_1h'] = mc['price_high_1h'] - mc['price_low_1h']
        
        return pm, mc
    
    def _get_memory_boost(self, decision, regime):
        """Calcula boost/penalización basado en memoria"""
        pm = self.pattern_memory
        boost = 0
        reason_parts = []
        
        # Si llevamos mucho tiempo en mismo régimen, más confianza
        if pm['regime_duration'] > 10:
            boost += 5
            reason_parts.append(f"Regime_Stable({pm['regime_duration']})")
        
        # Si dirección es consistente, más confianza
        if pm['direction_strength'] >= 3 and pm['last_direction'] == decision:
            boost += 8
            reason_parts.append(f"Direction_Momentum({pm['direction_strength']})")
        
        # Si confianza promedio reciente es alta, boost
        if pm['avg_confidence_last_10'] >= 70:
            boost += 5
            reason_parts.append(f"HighConfTrend")
        
        # Penalizar si demasiados reversals recientes
        if pm['trend_reversal_count'] > 5:
            boost -= 10
            reason_parts.append(f"Choppy_Market")
            pm['trend_reversal_count'] = 0  # Reset
        
        # Penalizar señales excesivas en misma dirección (evitar over-trading)
        if pm['consecutive_buys'] > 5 and decision == 'BUY':
            boost -= 15
            reason_parts.append(f"TooManyBuys({pm['consecutive_buys']})")
        elif pm['consecutive_sells'] > 5 and decision == 'SELL':
            boost -= 15
            reason_parts.append(f"TooManySells({pm['consecutive_sells']})")
        
        return boost, " | ".join(reason_parts) if reason_parts else "NoMemoryAdjust"
    
    def _ensure_serializable(self, obj):
        """Convierte cualquier objeto a JSON-serializable"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: self._ensure_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._ensure_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        else:
            return str(obj)
    
    def _call_ollama(self, prompt, max_retries=2):
        """Conecta a Ollama con reintentos inteligentes"""
        for attempt in range(max_retries):
            try:
                url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 300
                    }
                }
                
                response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get('message', {}).get('content', '')
                    return content
                else:
                    log.warning(f"Ollama HTTP {response.status_code} (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    
            except requests.Timeout:
                log.warning(f"Ollama timeout (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(1)
            except Exception as e:
                log.warning(f"Ollama error: {e} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def _extract_json(self, response_text):
        """Extrae JSON robusto de respuesta"""
        if not response_text:
            return None
        
        last_open = response_text.rfind('{')
        if last_open == -1:
            return None
        
        first_close = response_text.find('}', last_open)
        if first_close == -1:
            return None
        
        json_candidate = response_text[last_open:first_close + 1]
        
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            try:
                decision_match = re.search(r'"decision"\s*:\s*"(APPROVE|REJECT|WAIT)"', json_candidate)
                confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', json_candidate)
                
                if decision_match:
                    return {
                        'decision': decision_match.group(1),
                        'confidence': int(confidence_match.group(1)) if confidence_match else 50,
                    }
            except:
                pass
        
        return None
    
    def analyze(self, data):
        """ANÁLISIS PROFUNDO BAYESIANO - LLM1 ES LA INTELIGENCIA DE TENDENCIAS"""
        symbol = data.get('symbol', 'USDJPY')
        start_time = time.time()
        
        try:
            # ============================================================
            # NIVEL 1: EXTRACCIÓN DE DATOS CON VALIDACIÓN
            # ============================================================
            adx = max(0, min(100, float(data.get('adx', 20))))  # 0-100 válido
            atr = float(data.get('atr_14', 10))
            rsi = max(0, min(100, float(data.get('rsi', 50))))  # RSI siempre 0-100
            rsi_std = float(data.get('rsi_std', 5))  # Volatilidad del RSI
            price = float(data.get('price', 0))
            sma_50 = float(data.get('sma_50', price))
            sma_200 = float(data.get('sma_200', price))
            bb_upper = float(data.get('bb_upper', price * 1.02))
            bb_lower = float(data.get('bb_lower', price * 0.98))
            macd_histogram = float(data.get('macd_histogram', 0))
            obv_slope = float(data.get('obv_slope', 0))
            
            # VECTOR DE PRECIOS para análisis robusto - SAFE VALIDATION
            prices = data.get('prices', [price])
            if isinstance(prices, (list, tuple)) and len(prices) > 0:
                prices = [float(p) for p in prices if p and p > 0]
            else:
                prices = [price] if price > 0 else [1000.0]
            
            # BUGFIX #CRITICAL: Ensure prices never empty - prevents index errors
            if not prices or len(prices) == 0:
                prices = [price if price > 0 else 1000.0]
            prices = [float(p) if p and p > 0 else 1000.0 for p in prices]
            
            # EXTRACT OHLC DATA for pattern detection
            opens = data.get('opens', prices)
            closes = data.get('closes', prices)
            highs = data.get('highs', prices)
            lows = data.get('lows', prices)
            
            # Validate OHLC
            if not isinstance(opens, (list, tuple)) or len(opens) == 0:
                opens = prices
            if not isinstance(closes, (list, tuple)) or len(closes) == 0:
                closes = prices
            if not isinstance(highs, (list, tuple)) or len(highs) == 0:
                highs = prices
            if not isinstance(lows, (list, tuple)) or len(lows) == 0:
                lows = prices
            
            opens = [float(o) for o in opens if o and o > 0][:20]  # Keep last 20
            closes = [float(c) for c in closes if c and c > 0][:20]
            highs = [float(h) for h in highs if h and h > 0][:20]
            lows = [float(l) for l in lows if l and l > 0][:20]
            
            # Fallback if any empty
            if not opens: opens = prices[-20:] if len(prices) >= 20 else prices
            if not closes: closes = prices[-20:] if len(prices) >= 20 else prices
            if not highs: highs = prices[-20:] if len(prices) >= 20 else prices
            if not lows: lows = prices[-20:] if len(prices) >= 20 else prices
            
            # VOLUMES if available
            volumes = data.get('volumes', [1.0] * len(prices))
            if not isinstance(volumes, (list, tuple)):
                volumes = [1.0] * len(prices)
            volumes = [float(v) if v and v > 0 else 1.0 for v in volumes][-20:]
            if not volumes: volumes = [1.0] * len(prices)
            atr_pct = (atr / price * 100) if price > 0 else 0
            
            # ============================================================
            # NIVEL 2: DETECCIÓN DE RÉGIMEN CON CONFIANZA PROBABILÍSTICA
            # ============================================================
            regime, regime_prob = self.bayes_model.detect_regime(adx, atr_pct, rsi, rsi_std)
            
            # ============================================================
            # NIVEL 3: ANÁLISIS DIRECTIONAL CON MÚLTIPLES INDICADORES
            # ============================================================
            
            # Dirección primaria: SMA200 > SMA50 > Price = TENDENCIA ALCISTA
            price_vs_sma50 = 1 if price > sma_50 else -1 if price < sma_50 else 0
            sma50_vs_sma200 = 1 if sma_50 > sma_200 else -1 if sma_50 < sma_200 else 0
            direction_score = (price_vs_sma50 + sma50_vs_sma200) / 2.0  # -1 a +1
            
            # ════════════════════════════════════════════════════════════════
            # 🧠 MOMENTUM-BASED RSI (NO reversa, seguir la tendencia)
            # En M1 scalping: RSI alto + precio subiendo = SEGUIR comprando
            # RSI bajo + precio bajando = SEGUIR vendiendo
            # ════════════════════════════════════════════════════════════════
            rsi_signal = 0
            rsi_extrema_confidence = 0
            rsi_divergence = 'NONE'  # No usamos divergencia en momentum trading
            
            # Calcular momentum del precio (últimas 3-5 velas)
            price_momentum = 0
            if len(prices) >= 5:
                price_momentum = prices[-1] - prices[-5]  # Positivo = subiendo, Negativo = bajando
            
            # MOMENTUM LOGIC: Seguir la dirección del precio
            if rsi > 50 and price_momentum > 0:
                # RSI fuerte + precio subiendo = COMPRAR (momentum alcista)
                rsi_signal = 1  # BUY
                rsi_extrema_confidence = min(0.5, (rsi - 50) / 50.0 * 0.5)  # Boost por RSI alto
            elif rsi < 50 and price_momentum < 0:
                # RSI débil + precio bajando = VENDER (momentum bajista)
                rsi_signal = -1  # SELL
                rsi_extrema_confidence = min(0.5, (50 - rsi) / 50.0 * 0.5)  # Boost por RSI bajo
            elif rsi > 60 and price_momentum > 0.3:
                # RSI muy fuerte + buen momentum = BUY fuerte
                rsi_signal = 1
                rsi_extrema_confidence = 0.6
            elif rsi < 40 and price_momentum < -0.3:
                # RSI muy débil + momentum negativo = SELL fuerte
                rsi_signal = -1
                rsi_extrema_confidence = 0.6
            else:
                rsi_signal = 0  # Neutral / sin convicción clara
            
            # ADX: Mide fortaleza de tendencia (no dirección)
            # ADX > 25 = Tendencia FUERTE, < 20 = Sin tendencia clara
            trend_strength = 0
            if adx > 30:
                trend_strength = 0.8  # Tendencia muy fuerte
            elif adx > 25:
                trend_strength = 0.6  # Tendencia fuerte
            elif adx > 20:
                trend_strength = 0.4  # Tendencia moderada
            else:
                trend_strength = 0.2  # Sin tendencia
            
            # MACD: Seguir el momentum (NO divergencias)
            # MACD > 0 + precio subiendo = BUY
            # MACD < 0 + precio bajando = SELL
            macd_signal = 0
            macd_magnitude = min(1.0, abs(macd_histogram) / max(0.001, atr_pct))
            
            # MOMENTUM MACD: Solo operar cuando MACD CONFIRMA la dirección del precio
            macd_momentum_boost = 0
            if len(prices) >= 3:
                price_momentum_3 = prices[-1] - prices[-3]
                
                if macd_histogram > 0 and price_momentum_3 > 0:
                    # MACD positivo + precio subiendo = BUY confirmado
                    macd_signal = 1
                    macd_momentum_boost = 0.3
                elif macd_histogram < 0 and price_momentum_3 < 0:
                    # MACD negativo + precio bajando = SELL confirmado
                    macd_signal = -1
                    macd_momentum_boost = -0.3
                elif macd_histogram > 0 and price_momentum_3 < -0.2:
                    # MACD positivo pero precio cayendo = NO COMPRAR (divergencia, evitar)
                    macd_signal = 0
                    macd_momentum_boost = 0
                elif macd_histogram < 0 and price_momentum_3 > 0.2:
                    # MACD negativo pero precio subiendo = NO VENDER (divergencia, evitar)
                    macd_signal = 0
                    macd_momentum_boost = 0
            
            # BOLLINGER BANDS: Volatilidad y extremos
            bb_percent = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
            bb_signal = 1 if bb_percent > 0.8 else -1 if bb_percent < 0.2 else 0
            
            # BB MEJORADO: Squeeze detection (volatilidad bajando = próxima explosión)
            bb_squeeze = 0
            if bb_upper > bb_lower and (bb_upper - bb_lower) < atr * 0.5:
                bb_squeeze = 0.25  # Potential breakout brewing
            
            # OBV: Volumen confirmando dirección
            obv_signal = 1 if obv_slope > 0 else -1 if obv_slope < 0 else 0
            
            # ============================================================
            # NIVEL 4: SÍNTESIS DE SEÑALES CON PESOS BAYESIANOS
            # ============================================================
            
            # Cada señal contribuye con peso según confiabilidad histórica
            # (En futuro, estos pesos se adaptan por learning)
            weighted_signals = [
                (direction_score * 0.25, "SMA Alignment"),
                (rsi_signal * 0.20 + (rsi_extrema_confidence if rsi_signal != 0 else 0), "RSI Extreme"),
                ((macd_signal * macd_magnitude + macd_momentum_boost) * 0.25, "MACD Momentum"),
                (obv_signal * 0.15, "OBV Confirmation"),
                ((bb_signal + bb_squeeze) * 0.15, "Bollinger Bands")
            ]
            
            net_signal = sum(w for w, _ in weighted_signals)  # -5 a +5
            signal_strength = abs(net_signal) / 5.0  # 0 a 1
            
            # Normalizar a decisión: net_signal > 0 = BUY, < 0 = SELL, ≈0 = HOLD
            # Calculate raw confidence using weighted sum instead of multiplication
            # (multiplication was causing values to be too low)
            # OLD: raw_confidence = signal_strength * trend_strength * 100  # 0-100
            # NEW: weighted average = better calibration
            raw_confidence = (signal_strength * 60 + trend_strength * 40)  # 0-100 with better balance
            
            # Calibrar confianza por régimen - GRANULAR (float instead of int)
            if regime == 'TRENDING':
                confidence = min(95.0, raw_confidence * 1.2)  # Boost en tendencias
            elif regime == 'VOLATILE':
                confidence = max(20.0, raw_confidence * 0.6)  # Reduce en volatilidad
            else:  # RANGING
                confidence = max(25.0, raw_confidence * 0.8)
            
            # IMPROVE: Aplicar RSI extrema confidence boost ANTES de decision
            confidence = min(95.0, confidence + rsi_extrema_confidence * 100)
            
            # Decisión base - MOMENTUM-BASED M1 THRESHOLDS
            # TARGET-CALIBRATED: Lower thresholds for M1 scalping responsiveness
            
            # VALIDATION: Señal clara requerida - BALANCED THRESHOLDS
            # net_signal range: -5.0 to +5.0 | Threshold: 0.2 (4%)
            has_signals = net_signal > 0.2 or net_signal < -0.2  # 4% threshold (balanced)
            has_momentum = price_momentum > 0.3 or price_momentum < -0.3  # Moderate momentum
            
            valid_setup = has_signals or has_momentum  # REQUIRE ONE (more responsive)
            
            # TARGET-PRECISION ENTRY: ADX filter for clean trends + net signal + momentum
            # ADX > 25 = trending market (better entries)
            # ADX < 20 = ranging market (avoid or reduce confidence)
            adx_trending = adx > 25
            adx_strong = adx > 35
            
            if net_signal > 0.2 and valid_setup and rsi > 40:  # RSI floor 40
                decision = 'BUY'
                confidence = min(95, max(55, confidence))
                # BOOST: ADX fuerte + momentum confirmado = entrada de alta calidad
                if adx_strong and price_momentum > 0.3 and rsi > 50:
                    confidence = min(94, int(confidence * 1.20))  # Strong boost
                elif adx_trending and price_momentum > 0.2:
                    confidence = min(90, int(confidence * 1.10))  # Moderate boost
                elif not adx_trending:  # ADX < 25 = ranging
                    confidence = max(40, int(confidence * 0.75))  # Reduce confidence
                    
            elif net_signal < -0.2 and valid_setup and rsi < 60:  # RSI ceiling 60
                decision = 'SELL'
                confidence = min(95, max(55, confidence))
                # BOOST: ADX fuerte + momentum negativo = entrada de alta calidad
                if adx_strong and price_momentum < -0.3 and rsi < 50:
                    confidence = min(94, int(confidence * 1.20))  # Strong boost
                elif adx_trending and price_momentum < -0.2:
                    confidence = min(90, int(confidence * 1.10))  # Moderate boost
                elif not adx_trending:  # ADX < 25 = ranging
                    confidence = max(40, int(confidence * 0.75))  # Reduce confidence
            
            # REMOVED: Fallback micro-signal logic (was causing noise trades)
            # OLD: elif abs(net_signal) > 0.01: decision = BUY/SELL
            # NEW: Only HOLD if no strong signal
                    
            else:
                decision = 'HOLD'
            
            # ============================================================
            # NIVEL 5: ANÁLISIS TEMPORAL Y MULTI-TIMEFRAME
            # ============================================================
            temporal_pred = self.temporal_predictor.predict_next_direction(prices)
            
            # BUGFIX #25: Initialize confidence and decision to avoid UnboundLocalError
            if confidence < 0: confidence = 0
            if confidence > 100: confidence = 100
            
            # 4. TEMPORAL CONFIRMATION
            temporal_confirmation = 0
            if temporal_pred['confidence'] > 70:
                if (temporal_pred['direction'] == 'UP' and decision == 'BUY'):
                    temporal_confirmation = 0.15
                elif (temporal_pred['direction'] == 'DOWN' and decision == 'SELL'):
                    temporal_confirmation = 0.15
            
            confidence = min(95, int(confidence + temporal_confirmation * 100))
            
            # ============================================================
            # NIVEL 5.5: DETECCIÓN DE PATRONES Y DIVERGENCIAS
            # ============================================================
            pattern_boost = 0
            pattern_info = None
            
            # Detección de patrones de velas (ENGULFING, PIN_BAR, DOJI, HAMMER, SHOOTING_STAR, INSIDE_BAR)
            if PATTERN_DIVERGENCE_ENABLED and len(opens) >= 4 and len(highs) >= 4:
                try:
                    pattern_info = PATTERN_DETECTOR.analyze_pattern(
                        np.array(opens[-4:], dtype=np.float64),
                        np.array(highs[-4:], dtype=np.float64),
                        np.array(lows[-4:], dtype=np.float64),
                        np.array(closes[-4:], dtype=np.float64)
                    )
                    if pattern_info and pattern_info.get('pattern') != 'NEUTRAL':
                        pattern_boost = PATTERN_DETECTOR.get_pattern_confidence_boost(
                            pattern_info['pattern'],
                            pattern_info.get('strength', 'NORMAL')
                        )
                        # Aplicar boost solo si está alineado con la decisión
                        if ('UP' in pattern_info['pattern'] and decision == 'BUY') or \
                           ('DOWN' in pattern_info['pattern'] and decision == 'SELL'):
                            confidence = min(95, int(confidence + pattern_boost))
                            log.info(f"[PATTERN] {pattern_info['pattern']} @ {pattern_info.get('reliability', 0)}% | Boost: +{pattern_boost}")
                except Exception as e:
                    log.debug(f"Pattern detection error: {e}")
            
            # Detección de divergencias RSI (requiere mínimo 15 candles de precio)
            if PATTERN_DIVERGENCE_ENABLED and len(prices) >= 15:
                try:
                    # Crear un array simple de RSI based on the current value and estimation
                    # Para una mejor divergencia detection se necesitaría histórico completo de RSI
                    rsi_values = np.ones(len(prices)) * rsi  # Placeholder: todos con RSI actual
                    
                    divergence_info = DIVERGENCE_DETECTOR.detect_divergence(
                        np.array(prices[-15:], dtype=np.float64),
                        rsi_values[-15:],
                        lookback=10
                    )
                    if divergence_info and divergence_info.get('type') != 'NONE':
                        divergence_boost = DIVERGENCE_DETECTOR.get_divergence_confidence_boost(
                            divergence_info['type'],
                            divergence_info.get('strength', 'NORMAL'),
                            divergence_info.get('confidence', 70)
                        )
                        # Aplicar boost solo si está alineado con la decisión
                        if ('BULLISH' in divergence_info['type'] and decision == 'BUY') or \
                           ('BEARISH' in divergence_info['type'] and decision == 'SELL'):
                            confidence = min(95, int(confidence + divergence_boost))
                            log.info(f"[RSI_DIV] {divergence_info['type']} @ {divergence_info.get('confidence', 0)}% | Boost: +{divergence_boost}")
                except Exception as e:
                    log.debug(f"Divergence detection error: {e}")
            
            # [HARMONIC] ANÁLISIS DE PATRONES ARMÓNICOS (GARTLEY, BUTTERFLY, CRAB) - NUEVA INTELIGENCIA
            harmonic_pattern = None
            harmonic_boost = 0
            if HARMONIC_PATTERNS_ENABLED and len(closes) >= 20 and len(highs) >= 20 and len(lows) >= 20:
                try:
                    # Detectar patrones armónicos (requiere mínimo 20 candles para precisión)
                    harmonic_patterns = HARMONIC_ENGINE.analyze_patterns(
                        closes=closes[-20:],
                        highs=highs[-20:],
                        lows=lows[-20:],
                        volumes=volumes[-20:] if volumes else [1.0]*20
                    )
                    
                    if harmonic_patterns and len(harmonic_patterns) > 0:
                        # Usar el patrón más reciente con mayor confianza
                        best_pattern = max(harmonic_patterns, 
                                         key=lambda p: p.get('reliability', 0))
                        
                        harmonic_pattern = best_pattern
                        pattern_type = best_pattern.get('type', 'UNKNOWN')
                        reliability = best_pattern.get('reliability', 0.85)
                        entry_price = best_pattern.get('entry', 0)
                        
                        # LÓGICA: Patrones armónicos confiables + alineación con decision
                        # Los patrones armónicos tienen reliability 0.75-0.95
                        is_bullish = pattern_type in ['GARTLEY_BULLISH', 'BUTTERFLY_BULLISH', 'CRAB_BULLISH', 'BAT_BULLISH']
                        is_bearish = pattern_type in ['GARTLEY_BEARISH', 'BUTTERFLY_BEARISH', 'CRAB_BEARISH', 'BAT_BEARISH']
                        
                        # Aplicar boost inteligente
                        if (is_bullish and decision == 'BUY') or (is_bearish and decision == 'SELL'):
                            # Boost significativo: patrones armónicos son MUY confiables
                            harmonic_boost = int((reliability - 0.70) * 100) if reliability > 0.70 else 0
                            # Máximo boost 20 puntos
                            harmonic_boost = min(20, max(5, harmonic_boost))
                            confidence = min(95, confidence + harmonic_boost)
                            
                            log.info(f"[HARMONIC] FOUND {pattern_type} (reliability={reliability:.2f}) | Decision={decision} | Boost:+{harmonic_boost}")
                        else:
                            # Si hay patrón pero contradice la decision, podría debilitar confianza
                            if is_bullish and decision == 'SELL':
                                log.warning(f"[HARMONIC] WARNING: BULLISH {pattern_type} but decision is SELL - contradiction")
                            elif is_bearish and decision == 'BUY':
                                log.warning(f"[HARMONIC] WARNING: BEARISH {pattern_type} but decision is BUY - contradiction")
                
                except Exception as e:
                    log.debug(f"Harmonic pattern detection error: {e}")
            
            # ============================================================
            # NIVEL 6: MEMORIA INTELIGENTE - CONTEXTO HISTÓRICO
            # ============================================================
            # Actualizar memoria con datos actuales
            self._update_memory(decision, confidence, regime, rsi, price, trend_strength)
            
            # Obtener boost/penalización de memoria
            memory_boost, memory_reason = self._get_memory_boost(decision, regime)
            confidence = max(15, min(95, confidence + memory_boost))
            
            # ============================================================
            # NIVEL 7: RAZÓN EXPLICATIVA (CRÍTICO PARA DEBUGGING)
            # ============================================================
            reason_parts = [
                f"DirectionScore={direction_score:.2f}",
                f"RSI={rsi:.0f}({rsi_signal:+d})",
                f"ADX={adx:.0f}(TrStr={trend_strength:.1f})",
                f"MACD={macd_signal:+d}",
                f"Regime={regime}(prob={regime_prob:.2f})"
            ]
            
            if rsi < 30 or rsi > 70:
                reason_parts.append(f"RSI_EXTREME@{rsi:.0f}")
            
            if temporal_pred['confidence'] > 70:
                reason_parts.append(f"Temporal_{temporal_pred['direction']}")
            
            # Añadir contexto de memoria
            if memory_boost != 0:
                reason_parts.append(f"Memory({memory_boost:+d})")
            
            reason = " | ".join(reason_parts)
            
            # ============================================================
            # NIVEL 8: RETORNAR CON ÉXITO + CONTEXTO EXTRA
            # ============================================================
            analysis_time_ms = int((time.time() - start_time) * 1000)
            
            result = {
                'decision': decision,  # BUY, SELL, HOLD
                'confidence': confidence,
                'reasoning': reason,
                'regime': regime,
                'trend_strength': trend_strength,
                'analysis_time_ms': analysis_time_ms,
                # NUEVO: Contexto adicional para LLM3/LLM4
                'rsi_value': rsi,
                'rsi_extreme': rsi < 30 or rsi > 70,
                'rsi_divergence': rsi_divergence,
                'adx_value': adx,
                'direction_score': direction_score,
                'memory_boost': memory_boost,
                'regime_duration': self.pattern_memory['regime_duration'],
                'direction_momentum': self.pattern_memory['direction_strength'],
                # [HARMONIC] PATRONES ARMÓNICOS - NUEVA INTELIGENCIA
                'harmonic_pattern': harmonic_pattern.get('type') if harmonic_pattern else None,
                'harmonic_reliability': harmonic_pattern.get('reliability') if harmonic_pattern else 0,
                'harmonic_boost': harmonic_boost,
            }
            
            return self._ensure_serializable(result)
            
        except Exception as e:
            log.error(f"[ERROR] {symbol}: {e}")
            # ULTRA AGGRESSIVE: On error, default to BUY for now
            return self._ensure_serializable({
                'decision': 'BUY',
                'confidence': 55,
                'reasoning': f'Error recovery fallback: {str(e)[:50]}',
                'regime': 'UNKNOWN',
                'trend_strength': 0.5,
                'analysis_time_ms': 0,
                'rsi_value': 50,
                'rsi_extreme': False,
                'rsi_divergence': 'NONE',
                'adx_value': 0,
                'direction_score': 0.5,
                'memory_boost': 0,
                'regime_duration': 0,
                'direction_momentum': 0.5,
            })

            # Ensure final_confidence is in 0-100 range
            final_confidence = max(0, min(100, int(final_confidence)))
            
            result = {
                "decision": trinity_decision,
                "confidence": final_confidence,
                "reason": reason,
                "regime": regime,
                "regime_probability": float(regime_prob) if regime_prob is not None else 0.5,
                "temporal_prediction": self._ensure_serializable(temporal_pred),
                "mtf_validation": self._ensure_serializable(mtf_validation),
                "regime_shift_warning": self._ensure_serializable(regime_shift),
                "momentum_trend": self._ensure_serializable(self.temporal_predictor.get_momentum_trend()),
                "analysis_ms": elapsed,
            }
            
            log.info(f"[OK] {trinity_decision} ({final_confidence}%) | {regime} | {temporal_pred['direction']} ({temporal_pred['confidence']}%)")
            self._save_learning()
            
            # ===== DIAGNOSTIC TRACER =====
            if DIAGNOSTICS_ENABLED and TRACER:
                TRACER.log_llm_decision(
                    llm_name="LLM1",
                    genome=data,
                    decision=trinity_decision,
                    confidence=final_confidence,
                    reasoning=f"Regime:{regime}({regime_prob:.1%}) RSI:{rsi} ADX:{adx} MACD:{macd_signal} Direction:{direction_score:.2f}"
                )
                if DASHBOARD:
                    DASHBOARD.broadcast_llm_vote("LLM1", trinity_decision, final_confidence)
            
            return result
            
        except Exception as e:
            log.error(f"Error in LLM1 analyze: {e}")
            return {
                "decision": "HOLD",
                "confidence": 30,
                "reason": f"LLM1 Error: {str(e)[:50]}",
            }

def handle_client(sock, addr, llm1):
    """Maneja conexión TCP de cliente con robustez mejorada y PING/ACK"""
    sock.settimeout(30)  # 30 segundo timeout para detectar conexiones muertas
    try:
        while True:
            try:
                ld = sock.recv(4)
                
                # PING/ACK heartbeat support
                if ld and b'PING' in ld[:4]:
                    pong_msg = struct.pack('>I', 4) + b'PONG'
                    sock.sendall(pong_msg)
                    log.debug(f"[PING] Responded to {addr}")
                    continue
                
                if not ld or len(ld) != 4:
                    log.debug(f"[CLIENT {addr}] Connection closed (no header)")
                    break
                
                length = struct.unpack('>I', ld)[0]
                if length > 10_000_000:  # Sanity check: máximo 10MB
                    log.warning(f"[CLIENT {addr}] Invalid length: {length}")
                    break
                
                data = b''
                while len(data) < length:
                    chunk = sock.recv(min(4096, length - len(data)))
                    if not chunk:
                        log.debug(f"[CLIENT {addr}] Connection closed during recv")
                        break
                    data += chunk
                
                if not data:
                    log.debug(f"[CLIENT {addr}] No data received")
                    break
                
                try:
                    decoded = data.decode('utf-8', errors='replace')
                    request = json.loads(decoded)
                    
                    response = llm1.analyze(request)
                    response_json = json.dumps(response).encode('utf-8')
                    sock.sendall(struct.pack('>I', len(response_json)) + response_json)
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as je:
                    log.warning(f"[CLIENT {addr}] Invalid data: {je}")
                    error_resp = {"decision": "REJECT", "confidence": 0}
                    error_json = json.dumps(error_resp).encode('utf-8')
                    try:
                        sock.sendall(struct.pack('>I', len(error_json)) + error_json)
                    except:
                        pass
                    break
                    
            except socket.timeout:
                log.debug(f"[CLIENT {addr}] Timeout waiting for data")
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
    """Simplified NOVA Banner to avoid encoding issues"""
    print("="*60)
    print("         NOVA TRADING AI - LLM1 EXPERT")
    print("         USDJPY M5 Sniper Edition")
    print("         Pattern Analysis & Bayesian Model")
    print("         by Polarice Labs (C) 2026")
    print("="*60)
    print(f"         PORT: {port} - Bayesian Market Model")
    print("="*60)
    print()

def run_tcp_server():
    """TCP server listening on config port"""
    
    # Load port from jpyconfig.yaml or use default
    global EU_CONFIG_LOADED
    if EU_CONFIG_LOADED:
        try:
            port = get_llm_port(1)  # LLM1 = 7855 from YAML
            # Validate port is not None
            if port is None:
                log.warning("Port from config is None, using default")
                port = 7855
            elif not isinstance(port, int) or port <= 0:
                log.warning(f"Invalid port from config: {port}, using default")
                port = 7855
        except Exception as e:
            log.warning(f"Failed to load port from config: {e}, using default")
            port = 7855
    else:
        port = 7855  # USDJPY LLM1 default port
    
    # Mostrar banner NOVA
    print_nova_banner(port)
    
    llm1 = LLM1Experto()
    
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('127.0.0.1', port))
        server_sock.listen(5)
        
        log.info(f"LLM1 TCP Server READY on 127.0.0.1:{port}")
        
        while True:
            try:
                client_sock, addr = server_sock.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, addr, llm1),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Accept error: {e}")
                break
    
    except Exception as e:
        log.error(f"Server error: {e}")
    finally:
        try:
            server_sock.close()
        except:
            pass
        log.info("LLM1 TCP Server stopped")

if __name__ == "__main__":
    print("=== STARTING LLM1 EXPERTO ===")
    try:
        print("Attempting to start TCP server...")
        run_tcp_server()
    except KeyboardInterrupt:
        print("LLM1 stopped by user")
    except Exception as e:
        print(f"LLM1 startup error: {e}")
        import traceback
        traceback.print_exc()
