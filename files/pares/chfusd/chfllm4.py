#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - LLM4 RISK MANAGER                    ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Kelly Criterion + Volatility-Adjusted Risk + Position Scaling               ║
║  Port: 8604 (TCP Server) - Dynamic Risk Management with AI Learning          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, struct, json, logging, threading, time, pickle, os
import numpy as np
import requests
from collections import defaultdict, deque
import os
from datetime import datetime

# OLLAMA AI CONFIGURATION
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "llama3:8b"
OLLAMA_TIMEOUT = 10.0  # OPTIMIZED: Reduced from 30s for M1 scalping responsiveness

os.makedirs('logs', exist_ok=True)
_log_file = f'logs/llm4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
_file_handler = logging.FileHandler(_log_file, encoding='utf-8')
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s | LLM4_RISK | %(message)s", datefmt='%H:%M:%S')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger()
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

class VolatilityCalculator:
    """Calcula volatilidad en múltiples timeframes"""
    
    @staticmethod
    def atr(prices, period=14):
        """Average True Range - medida de volatilidad"""
        if len(prices) < period:
            return None
        
        trs = []
        for i in range(1, len(prices)):
            tr = max(
                prices[i] - prices[i-1],
                abs(prices[i] - np.min(prices[:i])),
                abs(prices[i] - np.max(prices[:i]))
            )
            trs.append(tr)
        
        return np.mean(trs[-period:])
    
    @staticmethod
    def std_dev(prices, period=20):
        """Desviación estándar = volatilidad histórica"""
        if len(prices) < period:
            return None
        return np.std(prices[-period:])
    
    @staticmethod
    def calculate_volatility_regime(prices):
        """Clasifica regime de volatilidad (LOW/MEDIUM/HIGH)"""
        if len(prices) < 30:
            return 'UNKNOWN'
        
        recent_vol = np.std(prices[-20:])
        historical_vol = np.std(prices[-50:-20]) if len(prices) > 70 else recent_vol
        
        ratio = recent_vol / (historical_vol + 1e-10)
        
        if ratio < 0.8:
            return 'LOW'
        elif ratio < 1.2:
            return 'MEDIUM'
        else:
            return 'HIGH'

class KellyCriterion:
    """Kelly Criterion para position sizing óptimo"""
    
    def __init__(self):
        self.win_rate_history = deque(maxlen=100)
        self.avg_win_history = deque(maxlen=100)
        self.avg_loss_history = deque(maxlen=100)
        self.learning_file = 'llm4_kelly.pkl'
        self._load_learning()
    
    def _load_learning(self):
        """Carga historiales de trading"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'rb') as f:
                    data = pickle.load(f)
                    self.win_rate_history = data.get('win_rate_history', deque(maxlen=100))
                    self.avg_win_history = data.get('avg_win_history', deque(maxlen=100))
                    self.avg_loss_history = data.get('avg_loss_history', deque(maxlen=100))
                    log.info(f"[OK] Kelly learning loaded: {len(self.win_rate_history)} trades")
            except Exception as e:
                log.warning(f"Could not load Kelly learning: {e}")
    
    def _save_learning(self):
        """Persiste learning para futuras sesiones"""
        try:
            data = {
                'win_rate_history': self.win_rate_history,
                'avg_win_history': self.avg_win_history,
                'avg_loss_history': self.avg_loss_history,
            }
            with open(self.learning_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            log.warning(f"Could not save Kelly learning: {e}")
    
    def record_trade(self, win_pips, loss_pips, is_win):
        """Registra resultado de trade"""
        if is_win:
            self.win_rate_history.append(1)
            self.avg_win_history.append(win_pips)
            self.avg_loss_history.append(0)
        else:
            self.win_rate_history.append(0)
            self.avg_win_history.append(0)
            self.avg_loss_history.append(loss_pips)
        
        self._save_learning()
    
    def calculate_kelly_fraction(self):
        """
        Kelly Criterion: f = (p*b - q) / b
        f = Kelly fraction (% de equity a arriesgar)
        p = win probability
        b = ratio ganancia/pérdida promedio
        q = lose probability
        """
        if len(self.win_rate_history) < 10:
            return 0.02  # 2% por defecto
        
        p = sum(self.win_rate_history) / len(self.win_rate_history)  # win rate
        
        avg_win = np.mean([w for w in self.avg_win_history if w > 0]) if any(self.avg_win_history) else 1.0
        avg_loss = np.mean([l for l in self.avg_loss_history if l > 0]) if any(self.avg_loss_history) else 1.0
        
        b = avg_win / (avg_loss + 1e-10)  # ratio ganancia/pérdida
        q = 1.0 - p
        
        if b == 0:
            return 0.01
        
        kelly_frac = (p * b - q) / b
        
        # Clamp to safe range: 1% to 5% (recommended 25% of true Kelly)
        kelly_frac = max(0.01, min(0.05, kelly_frac))
        
        return kelly_frac
    
    def get_stats(self):
        """Retorna estadísticas actuales"""
        if not self.win_rate_history:
            return {
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'kelly_fraction': 0.02,
                'trade_count': 0,
            }
        
        win_rate = sum(self.win_rate_history) / len(self.win_rate_history)
        avg_win = np.mean([w for w in self.avg_win_history if w > 0]) if any(self.avg_win_history) else 0
        avg_loss = np.mean([l for l in self.avg_loss_history if l > 0]) if any(self.avg_loss_history) else 0
        
        return {
            'win_rate': round(win_rate, 3),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'kelly_fraction': self.calculate_kelly_fraction(),
            'trade_count': len(self.win_rate_history),
        }

class VolumeProfileAnalyzer:
    """[CHART] Analiza perfil de volumen (POC, VWAP, Profile shape) +11pts"""
    
    def analyze_volume_profile(self, prices, volumes):
        """Calcula Point of Control, VWAP y forma del perfil"""
        if len(prices) < 20 or len(volumes) < 20:
            return {'valid': False, 'reason': 'Insufficient data'}
        
        # VWAP = suma(price * volume) / suma(volume)
        total_pv = sum(p * v for p, v in zip(prices[-20:], volumes[-20:]))
        total_v = sum(volumes[-20:])
        vwap = total_pv / (total_v + 1e-10) if total_v > 0 else prices[-1]
        
        # POC: bin con mayor volumen
        bins = 10
        price_min, price_max = min(prices[-20:]), max(prices[-20:])
        bin_width = (price_max - price_min + 1e-10) / bins
        
        bin_volumes = [0] * bins
        for p, v in zip(prices[-20:], volumes[-20:]):
            if p <= price_max:
                bin_idx = min(int((p - price_min) / bin_width), bins - 1)
                bin_volumes[bin_idx] += v
        
        poc_bin = np.argmax(bin_volumes)
        poc = price_min + (poc_bin + 0.5) * bin_width
        poc_volume = bin_volumes[poc_bin]
        
        # Forma del perfil (campana, bimodal, etc)
        profile_shape = 'NORMAL' if len([b for b in bin_volumes if b > 0]) > 5 else 'THIN'
        
        # Distance precio actual al POC (importante para calidad de entrada)
        current_price = prices[-1]
        distance_to_poc = abs(current_price - poc) / (bin_width + 1e-10)
        
        # Score de validez: entre más cerca al POC, mejor
        validity_score = max(0, 100 - distance_to_poc * 10)
        
        return {
            'valid': True,
            'vwap': round(vwap, 5),
            'poc': round(poc, 5),
            'poc_volume': int(poc_volume),
            'profile_shape': profile_shape,
            'current_price': round(current_price, 5),
            'distance_to_poc': round(distance_to_poc, 2),
            'validity_score': int(validity_score),  # 0-100, más alto = mejor ejecución
        }

class DynamicRiskCalculator:
    """[CHART_UP] Calcula TP/SL dinámicos basado en ATR y régimen +6pts"""
    
    def calculate_dynamic_targets(self, atr, current_price, regime='UNKNOWN', direction='BUY'):
        """Calcula TP y SL dinámicos"""
        if not atr or atr <= 0:
            return {
                'stop_loss': current_price * (0.995 if direction == 'BUY' else 1.005),
                'take_profit': current_price * (1.01 if direction == 'BUY' else 0.99),
                'risk_reward': 1.0,
            }
        
        if regime == 'VOLATILE':
            # En volatilidad: SL cercano, TP lejano (1:2 RR)
            sl_distance = atr * 1.5
            tp_distance = atr * 3.0
        elif regime == 'TRENDING':
            # En tendencia: SL normal, TP muy lejano (1:4 RR)
            sl_distance = atr * 1.0
            tp_distance = atr * 4.0
        elif regime == 'RANGING':
            # En rango: SL muy cercano, TP cerca (1:2 RR)
            sl_distance = atr * 0.7
            tp_distance = atr * 1.5
        else:
            # Default
            sl_distance = atr * 1.0
            tp_distance = atr * 2.0
        
        if direction == 'BUY':
            stop_loss = current_price - sl_distance
            take_profit = current_price + tp_distance
        else:
            stop_loss = current_price + sl_distance
            take_profit = current_price - tp_distance
        
        risk_reward = tp_distance / (sl_distance + 1e-10)
        
        return {
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'risk_reward': round(risk_reward, 2),
            'sl_distance_pips': round(sl_distance, 2),
            'tp_distance_pips': round(tp_distance, 2),
        }

class FalseMomentumDetector:
    """[LIGHTNING] Detecta momentum falso con divergencias +7pts"""
    
    def detect_false_momentum(self, prices, rsi_values, atr_value):
        """Detecta si momentum es real o falso"""
        if len(prices) < 5 or len(rsi_values) < 5:
            return {'is_false': False, 'confidence': 0, 'reason': 'Insuff data'}
        
        recent_price_change = prices[-1] - prices[-5]  # 5 barras
        recent_rsi_change = rsi_values[-1] - rsi_values[-5]
        
        divergence_price_rsi = False
        reason = ''
        
        # DIVERGENCIA 1: Precio sube pero RSI baja (bearish divergence)
        if recent_price_change > 0 and recent_rsi_change < 0:
            divergence_price_rsi = True
            reason = 'BEARISH_DIVERGENCE: Price UP but RSI DOWN'
        
        # DIVERGENCIA 2: Precio baja pero RSI sube (bullish divergence)
        elif recent_price_change < 0 and recent_rsi_change > 0:
            divergence_price_rsi = True
            reason = 'BULLISH_DIVERGENCE: Price DOWN but RSI UP'
        
        # FALSE MOMENTUM: Momentum alto pero ATR bajo (ruido no señal)
        recent_range = prices[-1] - prices[-5]
        momentum_vs_atr = abs(recent_range) / (atr_value + 1e-10)
        
        if momentum_vs_atr < 0.3:
            return {
                'is_false': True,
                'confidence': 85,
                'reason': 'Momentum vs ATR ratio too low (noise)',
            }
        
        if divergence_price_rsi:
            return {
                'is_false': True,
                'confidence': 75,
                'reason': reason,
            }
        
        return {
            'is_false': False,
            'confidence': 0,
            'reason': 'Momentum appears real',
        }

class LLM4RiskManager:
    """[MONEY] Gestor de Riesgo Dinámico con Inteligencia Superior"""
    
    def __init__(self):
        print("="*70)
        print("[MONEY] LLM4 RISK MANAGER - CONSCIOUSNESS EDITION")
        print("   Kelly Criterion + Volatility-Adjusted Risk + Position Scaling")
        print("="*70)
        
        self.kelly = KellyCriterion()
        self.volatility_calc = VolatilityCalculator()
        self.volume_profile = VolumeProfileAnalyzer()
        self.dynamic_risk = DynamicRiskCalculator()
        self.false_momentum = FalseMomentumDetector()
    
    def _call_ollama(self, prompt, max_retries=2):
        """🤖 Conecta a Ollama para análisis con IA real"""
        for attempt in range(max_retries):
            try:
                url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
                response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
                if response.status_code == 200:
                    result = response.json()
                    if 'message' in result and 'content' in result['message']:
                        return result['message']['content']
                else:
                    log.warning(f"Ollama HTTP {response.status_code} (attempt {attempt+1}/{max_retries})")
            except requests.exceptions.Timeout:
                log.warning(f"Ollama timeout (attempt {attempt+1}/{max_retries})")
            except Exception as e:
                log.warning(f"Ollama error: {e} (attempt {attempt+1}/{max_retries})")
        return None
    
    def analyze(self, data):
        """
        ANÁLISIS PROFUNDO DE RIESGO Y MONEY MANAGEMENT
        
        LLM4 es el gestor de riesgo - determina:
        - Position size óptima usando Kelly Criterion
        - TP/SL dinámicos basados en volatilidad
        - Risk/Reward ratio mínimo 1:2
        - Máxima pérdida por trade (2% del account)
        
        ★ CASCADED: Uses LLM1/LLM2 prior analysis for enhanced decisions
        """
        try:
            symbol = data.get('symbol', 'USDCHF')
            price = float(data.get('price', 0))
            
            # ⭐ CRITICAL FIX: Try multiple sources for prices (Trinity sends different formats)
            prices = []
            
            # DEBUG: Log what we received from Trinity
            log.debug(f"[RISK DATA] Received: price={price}, prices_len={len(data.get('prices', []))}, candles_len={len(data.get('candles', []))}, bar_data={type(data.get('bar_data', {}))}")
            
            # Try source 1: prices as direct list
            if data.get('prices') and isinstance(data.get('prices'), list):
                prices = [float(p) for p in data.get('prices', []) if p and float(p) > 0]
                log.debug(f"[RISK DATA] Source 1 (prices list): {len(prices)} prices")
            
            # Try source 2: candles OHLC
            if not prices:
                candles = data.get('candles', [])
                if isinstance(candles, list) and len(candles) > 0:
                    prices = [float(c.get('close', price)) for c in candles if c and c.get('close')]
            
            # Try source 3: bar_data closes
            if not prices:
                bar_data = data.get('bar_data', {})
                if isinstance(bar_data, dict) and bar_data.get('closes'):
                    prices = [float(c) for c in bar_data.get('closes', []) if c and float(c) > 0]
            
            # Fallback to single price
            if not prices:
                prices = [float(price)] if price > 0 else [1000.0]
            
            # Ensure prices is valid numpy array
            prices = np.array(prices) if prices else np.array([price if price > 0 else 1000.0])
            
            # ================================================================
            # ★ CASCADED ANALYSIS: USE LLM1/LLM2 PRIOR ANALYSIS ★
            # ================================================================
            prior = data.get('prior_analysis', {})
            has_prior = prior.get('primary_analysts_ready', False)
            
            prior_confidence_boost = 0
            prior_direction_hint = None
            prior_reasons = []
            
            if has_prior:
                # Extract LLM1 Bayesian analysis
                llm1_decision = prior.get('llm1_decision', 'HOLD')
                llm1_confidence = prior.get('llm1_confidence', 0)
                llm1_regime = prior.get('llm1_regime', 'UNKNOWN')
                llm1_trend_strength = prior.get('llm1_trend_strength', 0)
                
                # Extract LLM2 Technical analysis
                llm2_decision = prior.get('llm2_decision', 'HOLD')
                llm2_confidence = prior.get('llm2_confidence', 0)
                llm2_tech_score = prior.get('llm2_technical_score', 0)
                llm2_mc_prob = prior.get('llm2_mc_bull_probability', 0.5)
                llm2_support = prior.get('llm2_support')
                llm2_resistance = prior.get('llm2_resistance')
                
                # Analysts consensus
                analysts_consensus = prior.get('analysts_consensus', 'MIXED')
                avg_confidence = prior.get('analysts_avg_confidence', 0)
                
                # ════════════════════════════════════════════════════════
                # NUEVA: Campos de memoria de LLM1 y LLM2
                # ════════════════════════════════════════════════════════
                llm1_rsi_extreme = prior.get('llm1_rsi_extreme', False)
                llm1_rsi_div = prior.get('llm1_rsi_divergence')
                llm1_memory_boost = prior.get('llm1_memory_boost', 0)
                llm1_regime_duration = prior.get('llm1_regime_duration', 0)
                
                llm2_mc_avg = prior.get('llm2_mc_avg_trend', 0.5)
                llm2_market_struct = prior.get('llm2_market_structure', 'NEUTRAL')
                llm2_consecutive_bull = prior.get('llm2_consecutive_bull', 0)
                llm2_consecutive_bear = prior.get('llm2_consecutive_bear', 0)
                
                log.info(f"[LLM4 CASCADE] Prior: LLM1={llm1_decision}@{llm1_confidence}% LLM2={llm2_decision}@{llm2_confidence}% | Consensus={analysts_consensus}")
                
                # ═══ STRONG SIGNAL: Both analysts agree ═══
                if analysts_consensus == 'BUY':
                    prior_direction_hint = 'BUY'
                    prior_confidence_boost = min(20, int(avg_confidence * 0.3))  # Up to 20% boost
                    prior_reasons.append(f"Analysts:BUY@{avg_confidence:.0f}%★")
                elif analysts_consensus == 'SELL':
                    prior_direction_hint = 'SELL'
                    prior_confidence_boost = min(20, int(avg_confidence * 0.3))
                    prior_reasons.append(f"Analysts:SELL@{avg_confidence:.0f}%★")
                elif analysts_consensus == 'MIXED':
                    # Use stronger analyst
                    if llm1_confidence > llm2_confidence and llm1_confidence >= 70:
                        prior_direction_hint = llm1_decision if llm1_decision in ['BUY', 'SELL'] else None
                        prior_confidence_boost = 10
                        prior_reasons.append(f"LLM1:{llm1_decision}@{llm1_confidence}%")
                    elif llm2_confidence >= 70:
                        prior_direction_hint = llm2_decision if llm2_decision in ['BUY', 'SELL'] else None
                        prior_confidence_boost = 10
                        prior_reasons.append(f"LLM2:{llm2_decision}@{llm2_confidence}%")
                
                # ═══ NUEVA: RSI Divergence boost para LLM4 ═══
                if llm1_rsi_div == 'BULLISH' and prior_direction_hint == 'BUY':
                    prior_confidence_boost += 10
                    prior_reasons.append("RSI_DIV:BULL_CONFIRM")
                elif llm1_rsi_div == 'BEARISH' and prior_direction_hint == 'SELL':
                    prior_confidence_boost += 10
                    prior_reasons.append("RSI_DIV:BEAR_CONFIRM")
                
                # ═══ Monte Carlo probability validation ═══
                if llm2_mc_prob > 0.65 and prior_direction_hint == 'BUY':
                    prior_confidence_boost += 5
                    prior_reasons.append(f"MC_Confirms({llm2_mc_prob:.0%})")
                elif llm2_mc_prob < 0.35 and prior_direction_hint == 'SELL':
                    prior_confidence_boost += 5
                    prior_reasons.append(f"MC_Confirms({1-llm2_mc_prob:.0%})")
                
                # ═══ NUEVA: Market structure alignment ═══
                if llm2_market_struct == 'BULLISH' and prior_direction_hint == 'BUY':
                    prior_confidence_boost += 8
                    prior_reasons.append("Struct:BULL_ALIGN")
                elif llm2_market_struct == 'BEARISH' and prior_direction_hint == 'SELL':
                    prior_confidence_boost += 8
                    prior_reasons.append("Struct:BEAR_ALIGN")
                
                # ═══ Trend strength validation (MEJORADO: Predicción de volatilidad) ═══
                # Trend strength bajo = volatilidad inminente
                if llm1_trend_strength > 0.6:
                    prior_confidence_boost += 5
                    prior_reasons.append(f"TrendStr:{llm1_trend_strength:.1f}")
                elif llm1_trend_strength < 0.3:
                    # Volatility rising = be more aggressive with confirmations
                    prior_confidence_boost += 3
                    prior_reasons.append(f"VolRising({llm1_trend_strength:.1f})")
                
                # ═══ NUEVA: Volatility Regime Prediction ═══
                # Si la volatilidad está bajando = próximo breakout (Bollinger Squeeze)
                volatility_regime = data.get('volatility_regime', 'NORMAL')
                if volatility_regime == 'COMPRESSING':
                    prior_confidence_boost += 8
                    prior_reasons.append("VolCompress:BreakoutPending")
                elif volatility_regime == 'EXPANDING':
                    prior_confidence_boost += 5
                    prior_reasons.append("VolExpand:TrendMoment")
                
                # ═══ NUEVA: Régimen estable boost ═══
                if llm1_regime_duration > 15:
                    prior_confidence_boost += 5
                    prior_reasons.append(f"RegimeStable({llm1_regime_duration})")
                
                # ═══ Risk adjustment based on S/R proximity ═══
                if llm2_support and price < llm2_support * 1.02:
                    prior_reasons.append(f"NearSupport")
                elif llm2_resistance and price > llm2_resistance * 0.98:
                    prior_reasons.append(f"NearResistance")
                
                # ══════════════════════════════════════════════════════════════════════
                # 🌟 LLM5 SUPREME CONTEXT - INTELIGENCIA PARA RISK MANAGEMENT
                # LLM5 provee contexto de patrones y volatilidad para ajustar riesgo
                # ══════════════════════════════════════════════════════════════════════
                llm5_signal = prior.get('llm5_signal_direction', 'NEUTRAL')
                llm5_strength = prior.get('llm5_signal_strength', 0)
                llm5_confidence = prior.get('llm5_signal_confidence', 0)
                llm5_momentum = prior.get('llm5_momentum_score', 0)
                llm5_patterns = prior.get('llm5_top_patterns', [])
                llm5_vol_regime = prior.get('llm5_volatility_regime', {})
                llm5_bullish_pts = prior.get('llm5_bullish_points', 0)
                llm5_bearish_pts = prior.get('llm5_bearish_points', 0)
                llm5_rec = prior.get('llm5_recommendation_for_llm4', '')
                
                # ═══ RISK INTEL 1: Señal de LLM5 confirma dirección = menos riesgo ═══
                if llm5_signal == 'UP' and prior_direction_hint == 'BUY' and llm5_confidence > 0.6:
                    prior_confidence_boost += int(llm5_confidence * 12)  # +6-12%
                    prior_reasons.append(f"LLM5:Confirm↑({llm5_confidence:.0%})")
                elif llm5_signal == 'DOWN' and prior_direction_hint == 'SELL' and llm5_confidence > 0.6:
                    prior_confidence_boost += int(llm5_confidence * 12)
                    prior_reasons.append(f"LLM5:Confirm↓({llm5_confidence:.0%})")
                elif prior_direction_hint is not None and llm5_signal != 'NEUTRAL' and llm5_signal != prior_direction_hint:
                    # ⚠️ Divergencia LLM5 vs otros = reducir confianza (SOLO si hay dirección definida)
                    prior_confidence_boost -= 5
                    prior_reasons.append(f"LLM5:Conflict({llm5_signal})")
                
                # ═══ RISK INTEL 2: Régimen de volatilidad para sizing ═══
                vol_regime_type = llm5_vol_regime.get('regime', 'NORMAL') if isinstance(llm5_vol_regime, dict) else 'NORMAL'
                if vol_regime_type == 'HIGH':
                    # Alta volatilidad = reducir tamaño de posición
                    prior_reasons.append("LLM5:HighVol⚠️")
                elif vol_regime_type == 'EXPANDING':
                    # Tendencia desarrollándose = más confianza
                    prior_confidence_boost += 5
                    prior_reasons.append("LLM5:VolExpand")
                elif vol_regime_type == 'COMPRESSING':
                    # Squeeze = prepararsse para breakout
                    prior_reasons.append("LLM5:Squeeze🎯")
                
                # ═══ RISK INTEL 3: Patrones de alta confianza = señales claras ═══
                high_conf_patterns = [p for p in llm5_patterns if p.get('confidence', 0) > 0.8]
                if len(high_conf_patterns) >= 2:
                    prior_confidence_boost += 6
                    prior_reasons.append(f"LLM5:{len(high_conf_patterns)}Patterns★")
                
                # ═══ RISK INTEL 4: Momentum fuerte de LLM5 (ESCALA: -100 a +100) ═══
                # BUGFIX: Normalizar momentum de -100..+100 a -1..+1
                normalized_momentum = llm5_momentum / 100.0 if abs(llm5_momentum) > 1 else llm5_momentum
                if abs(normalized_momentum) > 0.5:
                    if (normalized_momentum > 0 and prior_direction_hint == 'BUY') or \
                       (normalized_momentum < 0 and prior_direction_hint == 'SELL'):
                        prior_confidence_boost += 8
                        prior_reasons.append(f"LLM5:Mom({normalized_momentum:+.2f})")
                
                # ═══ RISK INTEL 5: Balance de puntos para validar dirección (ESCALA: 0-100) ═══
                point_balance = llm5_bullish_pts - llm5_bearish_pts  # Rango: -100 a +100
                if point_balance > 25 and prior_direction_hint == 'BUY':  # 25%+ bullish
                    prior_confidence_boost += 5
                    prior_reasons.append(f"LLM5:BullPts({point_balance:+.0f})")
                elif point_balance < -25 and prior_direction_hint == 'SELL':  # 25%+ bearish
                    prior_confidence_boost += 5
                    prior_reasons.append(f"LLM5:BearPts({point_balance:+.0f})")
                
                log.debug(f"[LLM5 RISK] Signal:{llm5_signal}@{llm5_confidence:.0%} Vol:{vol_regime_type} Mom:{normalized_momentum:+.2f} Pts:{point_balance:+.0f}")
            
            else:  # PARALLEL MODE: Calculate direction from market data directly
                # ═══════════════════════════════════════════════════════════════════════
                # PHASE 9 FIX: Enhanced parallel-mode analysis with local MACD calculation,
                # widened RSI thresholds, SMA crossover, and momentum detection
                # ═══════════════════════════════════════════════════════════════════════
                try:
                    # Get RSI and MACD from indicators that Trinity sends
                    indicators = data.get('indicators', {})
                    fallback_rsi = float(data.get('rsi', indicators.get('rsi', 50)))
                    fallback_macd = float(data.get('macd', indicators.get('macd', 0)))
                    fallback_macd_hist = float(indicators.get('macd_histogram', indicators.get('macd_hist', 0)))
                    
                    # ═══ FIX: If MACD=0 (not calculated upstream), compute locally from prices ═══
                    prices_list = []
                    if isinstance(prices, np.ndarray):
                        prices_list = [float(p) for p in prices if p > 0]
                    elif isinstance(prices, (list, tuple)):
                        prices_list = [float(p) for p in prices if p and float(p) > 0]
                    
                    if abs(fallback_macd) < 1e-8 and abs(fallback_macd_hist) < 1e-8 and len(prices_list) >= 35:
                        # Calculate MACD locally: EMA12 - EMA26, Signal = EMA9 of MACD line
                        def _local_ema(data_arr, period):
                            mult = 2.0 / (period + 1)
                            ema_vals = [float(np.mean(data_arr[:period]))]
                            for val in data_arr[period:]:
                                ema_vals.append(float(val) * mult + ema_vals[-1] * (1 - mult))
                            return np.array(ema_vals)
                        
                        prices_arr = np.array(prices_list)
                        ema_fast = _local_ema(prices_arr, 12)
                        ema_slow = _local_ema(prices_arr, 26)
                        min_len = min(len(ema_fast), len(ema_slow))
                        macd_line_arr = ema_fast[-min_len:] - ema_slow[-min_len:]
                        
                        if len(macd_line_arr) >= 9:
                            signal_ema = _local_ema(macd_line_arr, 9)
                            fallback_macd = float(macd_line_arr[-1])
                            fallback_macd_hist = float(macd_line_arr[-1] - signal_ema[-1])
                        elif len(macd_line_arr) > 0:
                            fallback_macd = float(macd_line_arr[-1])
                        prior_reasons.append(f"MACD_LOCAL({fallback_macd:.6f})")
                    
                    # Determine direction from multiple indicators
                    bullish_signals = 0
                    bearish_signals = 0
                    
                    # ═══ RSI: Widened thresholds 45/55 (was 40/60 - too much dead zone) ═══
                    if fallback_rsi < 45:
                        bullish_signals += 1
                        prior_reasons.append(f"RSI({fallback_rsi:.0f})<45=BULL")
                    elif fallback_rsi > 55:
                        bearish_signals += 1
                        prior_reasons.append(f"RSI({fallback_rsi:.0f})>55=BEAR")
                    
                    # MACD histogram positive = bullish momentum
                    if fallback_macd_hist > 0:
                        bullish_signals += 1
                        prior_reasons.append(f"MACD_H({fallback_macd_hist:.6f})>0=BULL")
                    elif fallback_macd_hist < 0:
                        bearish_signals += 1
                        prior_reasons.append(f"MACD_H({fallback_macd_hist:.6f})<0=BEAR")
                    
                    # MACD line direction
                    if fallback_macd > 0:
                        bullish_signals += 1
                    elif fallback_macd < 0:
                        bearish_signals += 1
                    
                    # ═══ NEW: SMA crossover from closes (10 vs 20 period) ═══
                    if len(prices_list) >= 20:
                        sma_fast = float(np.mean(prices_list[-10:]))
                        sma_slow = float(np.mean(prices_list[-20:]))
                        if sma_fast > sma_slow:
                            bullish_signals += 1
                            prior_reasons.append("SMA10>20=BULL")
                        elif sma_fast < sma_slow:
                            bearish_signals += 1
                            prior_reasons.append("SMA10<20=BEAR")
                    
                    # ═══ NEW: Recent momentum (last 5 bars vs prev 5 bars) ═══
                    if len(prices_list) >= 10:
                        recent_avg = float(np.mean(prices_list[-5:]))
                        prev_avg = float(np.mean(prices_list[-10:-5]))
                        momentum_pct = (recent_avg - prev_avg) / prev_avg * 100 if prev_avg > 0 else 0
                        if momentum_pct > 0.01:
                            bullish_signals += 1
                            prior_reasons.append(f"MOM({momentum_pct:+.3f}%)=BULL")
                        elif momentum_pct < -0.01:
                            bearish_signals += 1
                            prior_reasons.append(f"MOM({momentum_pct:+.3f}%)=BEAR")
                    
                    # Determine direction based on signals (max 20 boost, was 15)
                    if bullish_signals > bearish_signals:
                        prior_direction_hint = 'BUY'
                        prior_confidence_boost = min(20, bullish_signals * 5)
                    elif bearish_signals > bullish_signals:
                        prior_direction_hint = 'SELL'
                        prior_confidence_boost = min(20, bearish_signals * 5)
                    else:
                        prior_direction_hint = 'HOLD'
                        prior_confidence_boost = 5
                        prior_reasons.append("MULTI_IND=NEUTRAL→HOLD")
                    
                    log.info(f"[LLM4 PARALLEL] RSI={fallback_rsi:.1f} MACD={fallback_macd:.6f} HIST={fallback_macd_hist:.6f} → {prior_direction_hint} (Bull:{bullish_signals} Bear:{bearish_signals})")
                    
                    prices_np = np.array(prices_list) if prices_list else np.array([price])
                    if len(prices_np) > 1:
                        volatility = np.std(prices_np)
                        price_range = (np.max(prices_np) - np.min(prices_np)) / np.mean(prices_np) if np.mean(prices_np) > 0 else 0.01
                        prior_confidence_boost += int(price_range * 30)
                        prior_reasons.append(f"Vol-boost({int(price_range * 30)}%)")
                except Exception as e:
                    log.warning(f"[LLM4 PARALLEL ERROR] {e}")
                    prior_confidence_boost = 10
                    prior_direction_hint = 'HOLD'
                    prior_reasons = ["Parallel-error→HOLD"]
            
            # BUGFIX #CRITICAL: Validate and sanitize prices to prevent crashes
            if isinstance(prices, np.ndarray):
                prices = [float(p) for p in prices if p and p > 0]
            elif isinstance(prices, (list, tuple)):
                prices = [float(p) for p in prices if p and p > 0]
            else:
                prices = [price] if price > 0 else []
            
            if not prices or len(prices) == 0:
                prices = [price if price > 0 else 1000.0]
            if price <= 0:
                price = prices[-1] if prices else 1000.0
            
            volumes = data.get('volumes', [1000] * len(prices))
            confidence = float(data.get('confidence', 50))
            
            # ★ Apply prior analysis confidence boost ★
            confidence = confidence + prior_confidence_boost
            confidence = max(0, min(100, confidence))  # Clamp to 0-100
            
            # ★ Use prior direction hint if available and no explicit direction ★
            direction = str(data.get('direction', 'BUY')).upper()
            if prior_direction_hint and direction == 'BUY':  # Only override if default
                direction = prior_direction_hint
                prior_reasons.append(f"Dir→{direction}")
            
            account_equity = float(data.get('account_equity', 10000))
            account_risk_pct = 2.0
            
            # ⭐ REDUCED: Trinity sends 20 bars, so 5 is plenty for analysis
            log.debug(f"[RISK FINAL] prices={len(prices)}, price={price:.2f}, type={type(prices)}")
            if len(prices) < 5 or price <= 0:
                log.warning(f"[RISK ⚠️] INSUFFICIENT DATA: {len(prices)} prices (need 5+), price={price}")
                return {
                    'decision': 'NO_TRADE',
                    'position_size': 0,
                    'reason': f'Insufficient price data (got {len(prices)} prices, need 5+)'
                }
            
            # ================================================================
            # NIVEL 1: VOLATILIDAD Y ATR
            # ================================================================
            atr_value = self.volatility_calc.atr(prices, period=14)
            if atr_value is None or atr_value <= 0:
                atr_value = prices[-1] * 0.001  # Fallback 0.1% de price
            
            std_dev = self.volatility_calc.std_dev(prices, period=20)
            vol_regime = self.volatility_calc.calculate_volatility_regime(prices)
            
            # ================================================================
            # NIVEL 2: KELLY CRITERION DINÁMICO (MEJORADO)
            # ================================================================
            kelly_stats = self.kelly.get_stats()
            kelly_fraction = kelly_stats['kelly_fraction']  # 1%-5%
            
            # MEJORADO: Kelly + volatility regime adaptation
            # Si volatilidad está comprimiendo (squeeze) = esperar breakout (menos Kelly)
            # Si volatilidad está expandiendo = trend momentum (más Kelly)
            vol_multiplier = 1.0
            if vol_regime == 'LOW':
                vol_multiplier = 0.8  # Squeeze detection
            elif vol_regime == 'HIGH':
                vol_multiplier = 1.2  # Trend expansion
            
            # Ajustar Kelly por confianza de la señal - MÁS AGRESIVO
            # Si confidence es baja (<40%), reducir Kelly (50% de kelly_fraction)
            # Si confidence es media (40-70%), usar Kelly normal
            # Si confidence es alta (>70%), usar Kelly completo + 10% bonus
            if confidence < 40:
                adjusted_kelly = kelly_fraction * 0.5
            elif confidence < 70:
                adjusted_kelly = kelly_fraction * 1.0  # Kelly normal
            else:
                adjusted_kelly = kelly_fraction * 1.1  # Bonus para alta confianza
                adjusted_kelly = min(0.05, adjusted_kelly)  # Cap at 5%
            
            # Apply volatility multiplier
            adjusted_kelly = adjusted_kelly * vol_multiplier
            
            # ================================================================
            # NIVEL 3: CÁLCULO DE POSICIÓN
            # ================================================================
            max_loss_dollars = account_equity * (account_risk_pct / 100.0)
            
            # IMPROVE: Risk dinámico basado en volatilidad
            # Volatilidad baja: risk = 1.2 ATR (puede arriesgar más)
            # Volatilidad media: risk = 1.5 ATR (estándar)
            # Volatilidad alta: risk = 1.0 ATR (reducir riesgo)
            vol_ratio = atr_value / (price * 0.01) if price > 0 else 0
            if vol_ratio < 0.002:  # Baja volatilidad
                risk_multiplier = 1.2
            elif vol_ratio > 0.005:  # Alta volatilidad
                risk_multiplier = 1.0
            else:  # Media
                risk_multiplier = 1.5
            
            risk_pips = atr_value * risk_multiplier
            risk_dollars = price * risk_pips  # Aproximado para FOREX
            
            # Position size = max_loss / risk_pips
            if risk_pips > 0:
                position_size = max_loss_dollars / risk_pips * adjusted_kelly
            else:
                position_size = 0.1  # Minimal
            
            # Límites de position - IMPROVE: más flexibles
            max_position = account_equity * 0.12  # IMPROVE: was 10%, now 12%
            min_position = 0.05  # IMPROVE: was 0.1, now 0.05 (más pequeñas ok)
            position_size = max(min_position, min(max_position, position_size))
            
            # ================================================================
            # NIVEL 4: CALCULAR TP/SL DINÁMICOS
            # ================================================================
            # 🐛 FIX: Handle HOLD direction - no trade should be made
            if direction == 'HOLD':
                log.info(f"[LLM4 HOLD] Direction=HOLD, no TP/SL calculation needed")
                return {
                    'decision': 'HOLD',
                    'direction': 'HOLD',
                    'position_size': 0,
                    'stop_loss': 0,
                    'take_profit': 0,
                    'rr_ratio': 0,
                    'confidence': confidence,
                    'risk_reasons': prior_reasons,
                    'reason': 'HOLD - Waiting for clear direction from indicators'
                }
            
            # ════════════════════════════════════════════════════════════════
            # 🎯 ADVANCED TP/SL: Confidence-based dynamic R:R
            # High confidence = wider TP, Low confidence = tighter TP
            # ════════════════════════════════════════════════════════════════
            # Base SL: 0.8-1.0 ATR depending on volatility regime
            if vol_regime == 'HIGH':
                sl_multiplier = 1.2  # Wider stop in high volatility
            elif vol_regime == 'LOW':
                sl_multiplier = 0.7  # Tighter stop in low volatility
            else:
                sl_multiplier = 0.9  # Normal
            
            # Dynamic TP based on confidence
            if confidence > 80:
                rr_target = 2.5  # Very high confidence = 2.5:1
            elif confidence > 70:
                rr_target = 2.2  # High confidence = 2.2:1
            elif confidence > 60:
                rr_target = 2.0  # Medium confidence = 2.0:1
            else:
                rr_target = 1.6  # Lower confidence = conservative 1.6:1
            
            if direction == 'BUY':
                stop_loss = price - (atr_value * sl_multiplier)
                sl_distance = price - stop_loss
                take_profit = price + (sl_distance * rr_target)
            else:  # SELL
                stop_loss = price + (atr_value * sl_multiplier)
                sl_distance = stop_loss - price
                take_profit = price - (sl_distance * rr_target)
            
            rr_ratio = abs(price - take_profit) / abs(price - stop_loss) if abs(price - stop_loss) > 0 else 0
            
            # ================================================================
            # NIVEL 5: FACTORES DE AJUSTE POR VOLATILIDAD
            # ================================================================
            vol_factor = 1.0
            if vol_regime == 'HIGH':
                vol_factor = 0.7  # Reducir posición en volatilidad alta
            elif vol_regime == 'LOW':
                vol_factor = 1.2  # Aumentar posición en volatilidad baja
            
            position_size = position_size * vol_factor
            
            # ================================================================
            # NIVEL 6: VALIDACIÓN - ¿VALE LA PENA OPERAR? (IMPROVED)
            # ================================================================
            decision = 'READY'
            reason_parts = []
            
            # IMPROVE: RR ratio validation más flexible - depende de confianza
            # - Si confianza >= 75%: permite RR > 1.2 (era 1.5)
            # - Si confianza 60-74%: requiere RR > 1.5
            # - Si confianza < 60%: requiere RR > 1.8
            if confidence >= 75:
                min_rr = 1.2  # IMPROVE: was 1.5
            elif confidence >= 60:
                min_rr = 1.5
            else:
                min_rr = 1.8
            
            if rr_ratio < min_rr:
                decision = 'WAIT'
                reason_parts.append(f"RR_LOW:{rr_ratio:.2f}<{min_rr:.1f}(conf:{confidence:.0f}%)")
            
            # IMPROVE: Confianza mínima - balanceada
            if confidence < 35:  # BALANCED: 35% minimum confidence
                decision = 'WAIT'
                reason_parts.append(f"CONFIDENCE_LOW:{confidence:.0f}%")
            
            # Validar position size mínima
            if position_size < min_position:
                decision = 'NO_TRADE'
                reason_parts.append(f"POS_TOO_SMALL")
            
            # ★ Include prior analysis reasons ★
            if prior_reasons:
                reason_parts.extend(prior_reasons)
            
            if not reason_parts:
                reason_parts.append(f"RR:{rr_ratio:.2f} Kelly:{adjusted_kelly:.3f} Pos:{position_size:.2f}lots {vol_regime}")
            
            # ================================================================
            # NIVEL 7: RETORNAR ANÁLISIS COMPLETO
            # ================================================================
            
            # 🏦 BANK-GRADE FIX: Trinity expects BUY/SELL/HOLD, not READY/WAIT
            # Convert internal decision to Trinity-compatible format
            if decision == 'READY':
                trinity_decision = direction  # 'BUY' or 'SELL'
            elif decision == 'WAIT':
                trinity_decision = 'HOLD'  # Wait = don't act now
            elif decision == 'NO_TRADE':
                trinity_decision = 'HOLD'  # No trade = hold
            else:
                trinity_decision = direction if decision in ['BUY', 'SELL'] else 'HOLD'
            
            result = {
                'decision': trinity_decision,  # BUY, SELL, or HOLD (Trinity-compatible)
                'internal_decision': decision,  # Original: READY, WAIT, NO_TRADE
                'direction': direction,  # BUY o SELL
                'confidence': float(round(confidence, 1)),  # 0-100 with 1 decimal place
                'position_size': round(position_size, 2),
                'risk_pips': round(risk_pips, 2),
                'risk_dollars': round(risk_dollars, 2),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'rr_ratio': round(rr_ratio, 2),
                'kelly_fraction': round(kelly_fraction, 4),
                'adjusted_kelly': round(adjusted_kelly, 4),
                'volatility_regime': vol_regime,
                'atr': round(atr_value, 5),
                'prior_boost': prior_confidence_boost,  # ★ New field
                'reason': ' | '.join(reason_parts)
            }
            
            log.info(f"[LLM4] {trinity_decision}@{confidence:.0f}% (internal:{decision}) Pos:{position_size:.2f} RR:{rr_ratio:.2f} Vol:{vol_regime}")
            
            # ===== DIAGNOSTIC TRACER =====
            if DIAGNOSTICS_ENABLED and TRACER:
                TRACER.log_llm_decision(
                    llm_name="LLM4",
                    genome=data,
                    decision=decision,
                    confidence=int(round(confidence)),
                    reasoning=f"Kelly:{adjusted_kelly:.3f} RR:{rr_ratio:.2f} PosSz:{position_size:.2f} Vol:{vol_regime}"
                )
                if DASHBOARD:
                    DASHBOARD.broadcast_llm_vote("LLM4", decision, int(round(confidence)))
            
            return self._sanitize_response(result)
            
        except Exception as e:
            log.error(f"[ERROR] LLM4 analyze: {e}")
            return {
                'decision': 'NO_TRADE',
                'position_size': 0,
                'reason': f'Analysis error: {str(e)[:100]}'
            }
    
    def _sanitize_response(self, obj):
        """Convierte cualquier objeto a JSON-serializable"""
        if obj is None:
            return None
        elif isinstance(obj, dict):
            return {k: self._sanitize_response(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_response(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bool):
            return obj
        elif isinstance(obj, (int, float, str, type(None))):
            return obj
        else:
            return str(obj)


def handle_client(sock, addr, llm4):
    """Maneja conexión TCP con robustez mejorada y PING/ACK"""
    sock.settimeout(30)  # 30 segundo timeout
    try:
        while True:
            try:
                ld = sock.recv(4)
                
                # PING/ACK heartbeat support
                if ld and b'PING' in ld:
                    pong_msg = struct.pack('>I', 4) + b'PONG'
                    sock.sendall(pong_msg)
                    log.debug(f"[PING] Responded to {addr}")
                    continue
                
                if not ld or len(ld) != 4:
                    log.debug(f"[CLIENT {addr}] Connection closed (no header)")
                    break
                
                length = struct.unpack('>I', ld)[0]
                if length > 10_000_000:  # Sanity check
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
                    
                    # ⭐ DEBUG: Log incoming data
                    log.info(f"[LLM4 RX] Keys: {list(request.keys())}")
                    log.info(f"[LLM4 RX] price={request.get('price')}, prices_count={len(request.get('prices', []))}")
                    log.info(f"[LLM4 RX] candles={len(request.get('candles', []))}, bar_data_closes={len(request.get('bar_data', {}).get('closes', []))}")
                    if request.get('prices'):
                        log.info(f"[LLM4 RX] prices_sample: {request.get('prices', [])[:5]}")
                    
                    response = llm4.analyze(request)
                    
                    # BUGFIX: Sanitizar response para evitar datos no-JSON-serializable
                    def sanitize_response(obj):
                        if obj is None:
                            return None
                        elif isinstance(obj, dict):
                            return {k: sanitize_response(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)):
                            return [sanitize_response(item) for item in obj]
                        elif isinstance(obj, (np.integer, np.floating)):
                            return float(obj)
                        elif isinstance(obj, np.ndarray):
                            return obj.tolist()
                        elif isinstance(obj, bool):
                            return obj
                        elif isinstance(obj, (int, float, str, type(None))):
                            return obj
                        else:
                            return str(obj)
                    
                    response = sanitize_response(response)
                    
                    response_json = json.dumps(response).encode('utf-8')
                    sock.sendall(struct.pack('>I', len(response_json)) + response_json)
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as je:
                    log.warning(f"[CLIENT {addr}] Invalid data: {je}")
                    error_resp = {"decision": "NO_TRADE", "position_size": 0}
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
{Y}|{R}  {Y}████╗  ██║{W}██╔═══██╗██║   ██║██╔══██╗{R}   {C}LLM4 RISK MANAGER{R}   {Y}|{R}
{Y}|{R}  {Y}██╔██╗ ██║{W}██║   ██║██║   ██║███████║{R}   {D}Position Control{R}    {Y}|{R}
{Y}|{R}  {Y}██║╚██╗██║{W}██║   ██║╚██╗ ██╔╝██╔══██║{R}                       {Y}|{R}
{Y}|{R}  {Y}██║ ╚████║{W}╚██████╔╝ ╚████╔╝ ██║  ██║{R}                       {Y}|{R}
{Y}|{R}  {Y}╚═╝  ╚═══╝{W} ╚═════╝   ╚═══╝  ╚═╝  ╚═╝{R}                       {Y}|{R}
{Y}|{R}                                                              {Y}|{R}
{Y}+{'-'*62}+{R}
{Y}|{R}  {W}USDCHF Scalping Edition{R}      {D}by Polarice Labs © 2026{R}       {Y}|{R}
{Y}|{R}  {G}● PORT: {port}{R}                  {D}Risk/Reward Analysis{R}        {Y}|{R}
{Y}+{'='*62}+{R}
""")

def run_tcp_server():
    """TCP server listening on config port"""
    import yaml
    
    # Cargar puerto desde config.yaml
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f) or {}
        port = config.get('llm_settings', {}).get('llm4_port', 8604)
    except:
        port = 8604  # LLM4 is RISK on port 8604
    
    # Mostrar banner NOVA
    print_nova_banner(port)
    
    llm4 = LLM4RiskManager()
    
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('127.0.0.1', port))
        server_sock.listen(5)
        
        log.info(f"LLM4 TCP Server READY on 127.0.0.1:{port}")
        
        while True:
            try:
                client_sock, addr = server_sock.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, addr, llm4),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Accept error: {e}")
                break
    
    except Exception as e:
        log.error(f"❌ Server bind/startup error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            server_sock.close()
        except:
            pass
        log.info("LLM4 TCP Server stopped")

if __name__ == "__main__":
    try:
        run_tcp_server()
    except KeyboardInterrupt:
        log.info("🛑 LLM4 stopped by user")
    except Exception as e:
        log.error(f"🔥 LLM4 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
