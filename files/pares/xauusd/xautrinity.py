#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 NOVA TRADING AI - TRINITY ORACLE                       ║
║                       by Polarice Labs © 2026                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Bank-Grade LLM Consensus System with 5-LLM Voting                           ║
║  Bayesian + Entropy + Divergence Weighting                                   ║
║  Dynamic Performance Tracking & Adaptive Weights                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, json, threading, logging, time, struct, statistics, math
from datetime import datetime
from collections import deque
import os, sys, io

# Fix Windows console encoding to UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Crear carpeta logs si no existe
os.makedirs('logs', exist_ok=True)

# Configurar logging a archivo Y consola
log_file = f'logs/trinity_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Crear handlers con UTF-8
file_handler = logging.FileHandler(log_file, encoding='utf-8')
stream_handler = logging.StreamHandler()

# Configurar formato
formatter = logging.Formatter('%(asctime)s | [%(threadName)-12s] | %(message)s', datefmt='%H:%M:%S')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
log = logging.getLogger(__name__)
log.info(f"[INIT] Log file: {log_file}")

# ═══════════════════════════════════════════════════════════════════════════════════════
# 🧙 WISE AI GRANDPA - 10 LLM PERFORMANCE TRACKER
# ═══════════════════════════════════════════════════════════════════════════════════════
class LLMPerformanceTracker:
    """
    🧙 WISE AI GRANDPA MODE - Master Intelligence System
    
    Tracks all 10 LLMs with sophisticated weighting based on:
    - Specialty: What each LLM is best at
    - Consistency: How reliable signals are
    - Momentum: Conviction in direction
    - Market Hours: Performance in different sessions
    - Volatility Regime: Performance in different conditions
    """
    def __init__(self, window_size=100):
        self.window_size = window_size
        
        # ALL 12 LLMS - No one left behind!
        llm_names = ['BAYESIAN', 'TECHNICAL', 'CHART', 'RISK', 'SUPREME', 
                     'SMART_MONEY', 'OCULUS', 'CHRONOS', 'PREDATOR', 'NOVA',
                     'STRATEGIST', 'SENTINEL']
        
        self.llm_history = {name: deque(maxlen=window_size) for name in llm_names}
        self.llm_momentum = {name: {'direction': None, 'count': 0} for name in llm_names}
        self.llm_consistency = {name: deque(maxlen=20) for name in llm_names}
        
        # 🧙 WISE AI GRANDPA WEIGHTS - Cada LLM tiene su propósito
        # 🔧 ULTRA-OPTIMIZADO: Máxima inteligencia basada en análisis profundo
        # Priorizar LLMs que entienden CONTEXTO, NARRATIVA y MOMENTUM del mercado
        self.base_weights = {
            # CORE INTELLIGENCE LAYER (Master Analysts)
            'BAYESIAN': 1.4,      # +0.1: Probabilistic + context boosts = powerful
            'TECHNICAL': 1.2,     # +0.1: Classic indicators + trend analysis
            'CHART': 1.7,         # +0.2: Pattern master - Best HH/HL/structure recognition 🎯
            'RISK': 1.1,          # +0.1: Guardian upgraded - better risk assessment
            'SUPREME': 1.8,       # +0.2: Supreme intelligence - Multi-factor analysis ⭐⭐
            'SMART_MONEY': 1.3,   # +0.1: Institutional flow critical for major moves
            
            # PRECISION ENHANCEMENT LAYER (Quality multipliers)
            'OCULUS': 1.3,        # +0.1: Quality validation prevents bad entries
            'CHRONOS': 1.6,       # +0.2: Timing = EVERYTHING - candle pattern master ⏰
            'PREDATOR': 1.5,      # +0.2: Execution precision - optimal entry/exit
            'NOVA': 1.9,          # +0.2: Supreme auditor - Final word on trades 👑👑
            
            # CONSCIOUSNESS LAYER (Strategic intelligence)
            'STRATEGIST': 2.0,    # LLM11 - Guru consciousness: strategy + conviction 🧠
            'SENTINEL': 1.8       # LLM12 - Quality guardian: execution + reflection 🛡️
        }
    
    def record_signal(self, llm_name: str, decision: str, confidence: float):
        """Record a signal from an LLM"""
        if llm_name not in self.llm_history:
            return
        
        # Track consistency (did opinion change from last signal?)
        prev_momentum = self.llm_momentum[llm_name]
        if prev_momentum['direction'] is not None:
            changed = (prev_momentum['direction'] != decision)
            self.llm_consistency[llm_name].append(0 if changed else 1)
        
        # Update momentum
        if prev_momentum['direction'] == decision:
            self.llm_momentum[llm_name]['count'] += 1
        else:
            self.llm_momentum[llm_name] = {'direction': decision, 'count': 1}
    
    def get_dynamic_weight(self, llm_name: str) -> float:
        """Get dynamically adjusted weight based on consistency and momentum"""
        if llm_name not in self.base_weights:
            return 1.0
        
        base = self.base_weights[llm_name]
        
        # Consistency bonus: LLMs that don't flip-flop get higher weight
        consistency = self.llm_consistency.get(llm_name, [])
        if len(consistency) >= 5:
            consistency_score = sum(consistency) / len(consistency)
            consistency_multiplier = 0.8 + (0.4 * consistency_score)  # 0.8 to 1.2
        else:
            consistency_multiplier = 1.0
        
        # Momentum bonus: Strong momentum = higher confidence in signal
        momentum = self.llm_momentum.get(llm_name, {})
        if momentum.get('count', 0) >= 3:
            momentum_bonus = min(0.2, momentum['count'] * 0.03)  # Max +0.2
        else:
            momentum_bonus = 0.0
        
        return base * consistency_multiplier + momentum_bonus

# Global performance tracker instance
llm_tracker = LLMPerformanceTracker()

# ⏰ MARKET HOURS DETECTION - Gold Trading Sessions
# ═════════════════════════════════════════════════════════

def get_market_session() -> dict:
    """
    ⏰ Detecta la sesión de trading actual para XAUUSD/Gold
    
    Gold trading es 24h pero tiene 3 sesiones principales:
    - ASIA: 00:00-08:00 UTC (Tokyo/Sydney) - Moderada volatilidad
    - LONDON: 08:00-16:00 UTC (Europa) - Alta volatilidad 🔥
    - NEW YORK: 13:00-21:00 UTC (USA) - Máxima volatilidad 💥
    - OVERLAP: 13:00-16:00 UTC (London+NY) - BEST TIME! 🎯
    
    Returns:
    {
        'session': 'LONDON' | 'NEW_YORK' | 'ASIA' | 'OVERLAP',
        'volatility_expected': 'HIGH' | 'MEDIUM' | 'LOW',
        'aggression_multiplier': float (0.7 to 1.5),
        'description': str
    }
    """
    try:
        from datetime import datetime
        import pytz
        
        utc_now = datetime.now(pytz.UTC)
        hour_utc = utc_now.hour
    except ImportError:
        # Fallback: pytz not installed, use basic UTC detection without timezone conversion
        import logging
        from datetime import datetime, timezone
        log = logging.getLogger(__name__)
        log.warning("[MARKET HOURS] pytz not installed - using basic UTC time (may be less accurate)")
        utc_now = datetime.now(timezone.utc)
        hour_utc = utc_now.hour
    except Exception as e:
        # Safety fallback: If anything fails, assume moderate session
        import logging
        log = logging.getLogger(__name__)
        log.error(f"[MARKET HOURS] Failed to detect session: {e} - defaulting to MODERATE")
        return {
            'session': 'UNKNOWN',
            'volatility_expected': 'MEDIUM',
            'aggression_multiplier': 1.0,
            'description': '⚠️ Session detection failed - using moderate settings'
        }
    
    # 🎯 OVERLAP (London + NY) - 13:00-16:00 UTC - BEST TIME!
    # 🔧 FIX 2026-03-04: Multipliers reduced from 1.50/1.30/1.40 → 1.12/1.08/1.10
    # Old values inflated mediocre 62% signals to 93% → bad trades
    if 13 <= hour_utc < 16:
        return {
            'session': 'OVERLAP',
            'volatility_expected': 'MAXIMUM',
            'aggression_multiplier': 1.12,
            'description': '🎯 London+NY Overlap - Maximum volume & best opportunities'
        }
    
    # 🔥 LONDON (08:00-16:00 UTC) - High volatility
    elif 8 <= hour_utc < 16:
        return {
            'session': 'LONDON',
            'volatility_expected': 'HIGH',
            'aggression_multiplier': 1.08,
            'description': '🔥 London Session - High volatility, strong trends'
        }
    
    # 💥 NEW YORK (13:00-21:00 UTC) - Maximum volatility
    elif 13 <= hour_utc < 21:
        return {
            'session': 'NEW_YORK',
            'volatility_expected': 'HIGH',
            'aggression_multiplier': 1.10,
            'description': '💥 New York Session - News releases, maximum movement'
        }
    
    # 🌚 ASIA (00:00-08:00 UTC) - Moderate volatility
    elif 0 <= hour_utc < 8:
        return {
            'session': 'ASIA',
            'volatility_expected': 'MEDIUM',
            'aggression_multiplier': 0.95,  # 🔧 Raised from 0.9: XAUUSD trades strong in Asia too
            'description': '🌚 Asian Session - Moderate, range-bound trading'
        }
    
    # OFF-HOURS (21:00-24:00 UTC) - Low volatility
    else:
        return {
            'session': 'OFF_HOURS',
            'volatility_expected': 'LOW',
            'aggression_multiplier': 0.85,  # 🔧 Raised from 0.7: don't destroy good signals in quiet hours
            'description': '😴 Off Hours - Low volume, caution advised'
        }

class TrinityConsensus:
    def __init__(self):
        log.info('╔═══════════════════════════════════════════════════════════════╗')
        log.info('║  🧙 WISE AI GRANDPA MODE - 10 LLM CONSENSUS v4.0            ║')
        log.info('║  "El Amo de los Amos" - Master Trading Intelligence System  ║')
        log.info('╚═══════════════════════════════════════════════════════════════╝')
        log.info('[TRINITY] ALL 10 LLMs Voting + Market Hours Awareness + Adaptive TP/SL')
        self.host = '127.0.0.1'
        self.timeout = 1.5  # FAST: 1.5s max per LLM (was 5.0s)
        self.strategist_timeout = 10.0  # LLM11 uses Ollama llama3:8b — 7s inference + 3s overhead
        self._strategist_cache = {}      # Persistent cache: last known GURU response (updated async)
        
        # 🧙 ALL 10 LLMS VOTE - No more separation between "core" and "enhancement"
        # Each LLM brings unique intelligence to the decision
        self.llm_ports = {
            # FUNDAMENTAL ANALYSIS LAYER
            'BAYESIAN': 5555,      # LLM1 - Probabilistic reasoning
            'TECHNICAL': 5557,     # LLM2 - Technical indicators
            'CHART': 5558,         # LLM3 - Pattern recognition
            'RISK': 5559,          # LLM4 - Risk management
            'SUPREME': 5561,       # LLM5 - Deep learning ensemble
            'SMART_MONEY': 5004,   # LLM6 - Whale/sweep detection
            
            # INTELLIGENCE ENHANCEMENT LAYER
            'OCULUS': 5562,        # LLM7 - Data quality (NOW VOTES!)
            'CHRONOS': 5563,       # LLM8 - Timing optimization (NOW VOTES!)
            'PREDATOR': 5564,      # LLM9 - Execution optimization (NOW VOTES!)
            'NOVA': 5565,          # LLM10 - Supreme auditor (votes in Phase 1, audits in Phase 3)
            
            # CONSCIOUSNESS LAYER
            'STRATEGIST': 5568,    # LLM11 - Guru consciousness (strategy + conviction)
            'SENTINEL': 5569       # LLM12 - Quality guardian (execution + reflection)
        }
        
        # Keep core_llm_ports for backward compatibility (but ALL vote now)
        self.core_llm_ports = {
            'BAYESIAN': 5555, 'TECHNICAL': 5557, 'CHART': 5558,
            'RISK': 5559, 'SUPREME': 5561, 'SMART_MONEY': 5004
        }
        
        self.enhancement_llm_ports = {
            'OCULUS': 5562, 'CHRONOS': 5563, 'PREDATOR': 5564, 'NOVA': 5565
        }
        
        self.tracker = llm_tracker
        
        # 🧠 SPI ADAPTIVE LEARNING — Track structure position results for self-optimization
        self._spi_history = deque(maxlen=200)  # Last 200 SPI-evaluated decisions
        self._spi_zone_stats = {
            'pullback_zone': {'wins': 0, 'losses': 0},   # Entries in Fib 38.2-61.8%
            'at_extreme': {'wins': 0, 'losses': 0},       # Entries at HH or LL
            'midrange': {'wins': 0, 'losses': 0},          # Entries in middle of move
            'counter_trend': {'wins': 0, 'losses': 0},     # Entries against macro trend
            'with_trend': {'wins': 0, 'losses': 0},        # Entries aligned with macro trend
            'bos': {'wins': 0, 'losses': 0}                # Break of structure entries
        }
    
    def spi_record_result(self, spi_context: dict, trade_won: bool):
        """🧠 Record a trade result for SPI adaptive learning"""
        if not spi_context or not spi_context.get('spi_active'):
            return
        
        zone = 'midrange'
        if spi_context.get('in_pullback_zone'):
            zone = 'pullback_zone'
        elif spi_context.get('near_high') or spi_context.get('near_low'):
            zone = 'at_extreme'
        elif spi_context.get('in_breakdown_zone'):
            zone = 'bos'
        
        result_key = 'wins' if trade_won else 'losses'
        self._spi_zone_stats[zone][result_key] += 1
        
        self._spi_history.append({
            'zone': zone,
            'macro_trend': spi_context.get('macro_trend'),
            'price_position_pct': spi_context.get('price_position_pct'),
            'won': trade_won,
            'timestamp': time.time()
        })
        
        # Log adaptive stats periodically
        total = self._spi_zone_stats[zone]['wins'] + self._spi_zone_stats[zone]['losses']
        if total > 0 and total % 5 == 0:
            wr = self._spi_zone_stats[zone]['wins'] / total
            log.info(f"[SPI-LEARN] Zone '{zone}': {self._spi_zone_stats[zone]['wins']}/{total} = {wr:.0%} win rate")
    
    def _validate_ecosystem_data(self, genome: dict) -> dict:
        """
        🛡️ ECOSYSTEM DATA VALIDATION
        
        Returns validation status:
        {
            'is_valid': bool,
            'sl_caution': bool (consecutive SLs),
            'velocity_alert': bool (rapid changes),
            'timeframe_disagreement': bool (multi-TF conflict),
            'confidence_penalty': float (0.5 to 1.0)
        }
        """
        validation = {
            'is_valid': True,
            'sl_caution': False,
            'velocity_alert': False,
            'timeframe_disagreement': False,
            'confidence_penalty': 1.0,
            'reason': ''
        }
        
        # ═══ MEJORADO: Usar sl_analysis pre-procesado de Quimera ═══
        sl_analysis = genome.get('sl_analysis', {})
        if sl_analysis:
            consecutive_sl = sl_analysis.get('consecutive_count', 0)
            recommendation = sl_analysis.get('recommendation', 'NORMAL')
            
            if sl_analysis.get('critical', False):
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.2  # Penalización muy alta
                validation['reason'] += f"SL_CRITICAL({consecutive_sl}); "
                log.warning(f"[ECOSYSTEM] 🚨 CRITICAL: {consecutive_sl} consecutive SLs - STOP TRADING")
            elif sl_analysis.get('warning', False):
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.5
                validation['reason'] += f"SL_WARNING({consecutive_sl}); "
                log.warning(f"[ECOSYSTEM] ⚠️ WARNING: {consecutive_sl} consecutive SLs detected")
            
            # Verificar tiempo desde último SL
            seconds_since_sl = sl_analysis.get('seconds_since_last_sl', -1)
            if 0 < seconds_since_sl < 120:  # Menos de 2 min desde SL
                validation['confidence_penalty'] *= 0.6
                validation['reason'] += f"RECENT_SL({seconds_since_sl}s); "
        else:
            # Fallback al método anterior si no hay sl_analysis
            sl_history = genome.get('sl_history', [])
            if len(sl_history) >= 2:
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.6
                validation['reason'] += f"SL_HISTORY({len(sl_history)}); "
                log.warning(f"[ECOSYSTEM] ⚠️ {len(sl_history)} SLs in history detected")
        
        # Check velocity (indicator changes)
        indicators = genome.get('indicators', {}).get('current', {})
        ma_delta = abs(indicators.get('ma_fast_delta', 0))
        rsi_delta = abs(indicators.get('rsi_delta', 0))
        adx_delta = abs(indicators.get('adx_delta', 0))
        
        if ma_delta > 0.5 or rsi_delta > 5 or adx_delta > 2:
            validation['velocity_alert'] = True
            validation['confidence_penalty'] *= 0.7
            validation['reason'] += f"RAPID_CHANGE(MA_Δ={ma_delta:.3f},RSI_Δ={rsi_delta:.1f}); "
            log.warning(f"[ECOSYSTEM] ⚠️ Rapid indicator changes detected")
        
        # Check multi-timeframe consensus
        timeframe_analysis = genome.get('timeframe_analysis', [])
        if len(timeframe_analysis) > 1:
            m1_signal = None
            for tf in timeframe_analysis:
                if tf.get('timeframe') == 'M1':
                    m1_signal = tf.get('signal')
            
            if m1_signal:
                # Scalping on M1: only M5 and M15 are relevant confirmation TFs.
                # M30 and H1 diverging from M1 is NORMAL and should NOT penalize.
                scalping_tfs = {'M5', 'M15'}
                disagreement_count = sum(1 for tf in timeframe_analysis
                                       if tf.get('timeframe') in scalping_tfs
                                       and tf.get('signal') != m1_signal
                                       and tf.get('signal') != 'HOLD')
                if disagreement_count >= 2:  # Both M5 and M15 opposing M1 = real conflict
                    validation['timeframe_disagreement'] = True
                    validation['confidence_penalty'] *= 0.80
                    validation['reason'] += f"TF_DISAGREE({disagreement_count}); "
                    log.warning(f"[ECOSYSTEM] ⚠️ M5/M15 disagreement with M1 detected")
        
        validation['is_valid'] = (validation['confidence_penalty'] > 0.3)
        return validation
    
    def _consensus_voting_engine(self, genome: dict) -> dict:
        """
        🧠 INTELLIGENT CONSENSUS VOTING ENGINE
        
        Analyzes multiple timeframes with REASONING and STRENGTH
        Each timeframe vote has: signal (BUY/SELL/HOLD) + strength (0-100) + reason (why)
        
        Returns:
        {
            'consensus_decision': 'BUY' | 'SELL' | 'HOLD',
            'consensus_confidence': 0-100,
            'votes': {detailed vote breakdown},
            'alignment_score': 0-100,
            'reason': 'detailed explanation'
        }
        """
        consensus = {
            'consensus_decision': 'HOLD',
            'consensus_confidence': 0,
            'votes': {},
            'alignment_score': 0,
            'reason': ''
        }
        
        # Timeframe weights (priority: closer to current = more weight)
        timeframe_weights = {
            'M1': 0.30,   # Highest priority - immediate action
            'M5': 0.25,   # High priority
            'M15': 0.20,  # Medium
            'M30': 0.15,  # Lower
            'H1': 0.10    # Strategic context
        }
        
        timeframe_analysis = genome.get('timeframe_analysis', [])
        if not timeframe_analysis:
            # 🧠 SYNTHESIZE pseudo-TF analysis from available indicators
            # Instead of returning empty {} (killing consensus), use what we have:
            # ADX = trend strength, RSI = momentum, MA alignment = direction
            _indicators = genome.get('indicators', {}).get('current', {})
            if not _indicators:
                _indicators = genome.get('indicators', {})
            
            _adx = float(_indicators.get('adx', {}).get('value', 25) if isinstance(_indicators.get('adx'), dict) else _indicators.get('adx', 25))
            _rsi = float(_indicators.get('rsi', {}).get('value', 50) if isinstance(_indicators.get('rsi'), dict) else _indicators.get('rsi', 50))
            _ma_fast = float(_indicators.get('ma_fast', _indicators.get('ma5', 0)))
            _ma_slow = float(_indicators.get('ma_slow', _indicators.get('ma20', 0)))
            
            if _ma_fast > 0 and _ma_slow > 0:
                _ma_bullish = _ma_fast > _ma_slow
                _ma_spread = abs(_ma_fast - _ma_slow) / _ma_slow * 100  # % spread
                
                # Determine direction from MA + RSI agreement
                if _ma_bullish and _rsi > 50:
                    _synth_signal = 'BUY'
                    _synth_strength = min(90, 50 + _adx * 0.5 + (_rsi - 50) * 0.3)
                elif not _ma_bullish and _rsi < 50:
                    _synth_signal = 'SELL'
                    _synth_strength = min(90, 50 + _adx * 0.5 + (50 - _rsi) * 0.3)
                else:
                    _synth_signal = 'HOLD'
                    _synth_strength = 40
                
                # ADX determines confidence: strong trend = high agreement
                _synth_alignment = min(95, _adx * 1.2) if _adx > 25 else 30
                
                consensus['consensus_decision'] = _synth_signal
                consensus['consensus_confidence'] = int(_synth_strength)
                consensus['alignment_score'] = _synth_alignment
                _ma_label = 'bull' if _ma_bullish else 'bear'
                consensus['votes'] = {
                    'INDICATORS': {'signal': _synth_signal, 'strength': _synth_strength, 'reason': f'ADX={_adx:.0f} RSI={_rsi:.0f} MA={_ma_label}'}
                }
                consensus['reason'] = f"Synthesized from indicators: ADX={_adx:.0f} RSI={_rsi:.0f}"
                log.info(f"[CONSENSUS] 🧠 Synthesized TF: {_synth_signal}@{_synth_strength:.0f}% | ADX={_adx:.0f} RSI={_rsi:.0f} | Alignment={_synth_alignment:.0f}%")
                return consensus
            
            consensus['reason'] = "No timeframe analysis available"
            return consensus
        
        # ═══════════════════════════════════════════════════════════════
        # VOTE COLLECTION: Extract signal + strength + reason from each TF
        # ═══════════════════════════════════════════════════════════════
        tf_votes = {}
        total_weight = 0
        
        for tf_data in timeframe_analysis:
            tf_name = tf_data.get('timeframe', '')
            signal = tf_data.get('signal', 'HOLD')
            strength = float(tf_data.get('strength', 50))
            reason = tf_data.get('reason', 'No reason given')
            
            if tf_name in timeframe_weights:
                weight = timeframe_weights[tf_name]
                total_weight += weight
                
                # 🧠 INTELLIGENT STRENGTH SCALING
                # If strength is extreme (75+), weight it more heavily
                # If strength is weak (40-60), trust it less
                confidence_multiplier = 1.0
                if strength >= 80:
                    confidence_multiplier = 1.15  # Strong signals get +15%
                elif strength >= 75:
                    confidence_multiplier = 1.10  # Good signals get +10%
                elif strength <= 40:
                    confidence_multiplier = 0.85  # Weak signals get -15%
                
                weighted_strength = strength * weight * confidence_multiplier
                
                tf_votes[tf_name] = {
                    'signal': signal,
                    'strength': strength,
                    'reason': reason,
                    'weight': weight,
                    'confidence_multiplier': confidence_multiplier,
                    'weighted_strength': weighted_strength
                }
                
                log.debug(f"[CONSENSUS] {tf_name}: {signal} @ {strength:.0f}% (weight={weight}, mult={confidence_multiplier:.2f}) - {reason}")
        
        if not tf_votes:
            consensus['reason'] = "No valid timeframe votes"
            return consensus
        
        # ═══════════════════════════════════════════════════════════════
        # VOTE AGGREGATION: Weighted consensus calculation with reasoning
        # ═══════════════════════════════════════════════════════════════
        
        # Count votes by direction
        buy_votes = sum(1 for v in tf_votes.values() if v['signal'] == 'BUY')
        sell_votes = sum(1 for v in tf_votes.values() if v['signal'] == 'SELL')
        hold_votes = sum(1 for v in tf_votes.values() if v['signal'] == 'HOLD')
        
        # Calculate weighted strength (considering both weight and multiplier)
        buy_strength = sum(v['weighted_strength'] for v in tf_votes.values() if v['signal'] == 'BUY')
        sell_strength = sum(v['weighted_strength'] for v in tf_votes.values() if v['signal'] == 'SELL')
        hold_strength = sum(v['weighted_strength'] for v in tf_votes.values() if v['signal'] == 'HOLD')
        
        # Normalize by total weight
        if total_weight > 0:
            buy_score = min(100, buy_strength / total_weight)
            sell_score = min(100, sell_strength / total_weight)
            hold_score = min(100, hold_strength / total_weight)
        else:
            buy_score = sell_score = hold_score = 33.33
        
        # ═══════════════════════════════════════════════════════════════
        # 🧠 SUPER ENTRADA INTELIGENTE - Decisión más flexible
        # ═══════════════════════════════════════════════════════════════
        
        # Extract critical timeframes
        m1_vote = tf_votes.get('M1', {})
        m5_vote = tf_votes.get('M5', {})
        m15_vote = tf_votes.get('M15', {})
        
        m1_signal = m1_vote.get('signal', 'HOLD')
        m5_signal = m5_vote.get('signal', 'HOLD')
        m15_signal = m15_vote.get('signal', 'HOLD')
        
        m1_strength = m1_vote.get('strength', 50)
        m5_strength = m5_vote.get('strength', 50)
        
        # 🎯 SUPER ENTRADA: Detectar SUPER_BUY o SUPER_SELL en razones
        has_super_buy = any('SUPER_BUY' in str(v.get('reason', '')) for v in tf_votes.values())
        has_super_sell = any('SUPER_SELL' in str(v.get('reason', '')) for v in tf_votes.values())
        
        tf_agreement_list = []
        for tf_name, vote in tf_votes.items():
            if vote['signal'] in ['BUY', 'SELL']:
                tf_agreement_list.append((tf_name, vote['signal'], vote['strength']))
        
        # ═══════════════════════════════════════════════════════════════
        # 🚀 PRIORIDAD 1: SUPER ENTRADA detectada en cualquier TF
        # ═══════════════════════════════════════════════════════════════
        if has_super_buy and buy_votes >= 2:
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(min(95, buy_score * 1.2))
            consensus['reason'] = f"🚀 SUPER BUY: {buy_votes} TFs confirm ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='BUY'])}) @ {buy_score:.0f}%"
        
        elif has_super_sell and sell_votes >= 2:
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(min(95, sell_score * 1.2))
            consensus['reason'] = f"🚀 SUPER SELL: {sell_votes} TFs confirm ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='SELL'])}) @ {sell_score:.0f}%"
        
        # ═══════════════════════════════════════════════════════════════
        # 🎯 PRIORIDAD 2: Consenso fuerte (3+ TFs acuerdo)
        # ═══════════════════════════════════════════════════════════════
        elif buy_votes >= 3 and buy_score > 55:  # Relajado de 65 a 55
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(buy_score)
            consensus['reason'] = f"Strong BUY: {buy_votes} TFs ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='BUY'])}) @ {buy_score:.0f}%"
        
        elif sell_votes >= 3 and sell_score > 55:  # Relajado de 65 a 55
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(sell_score)
            consensus['reason'] = f"Strong SELL: {sell_votes} TFs ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='SELL'])}) @ {sell_score:.0f}%"
        
        # ═══════════════════════════════════════════════════════════════
        # 🎯 PRIORIDAD 3: M1+M5 alineados (muy importante para timing)
        # Guard: also require overall buy/sell_score ≥ 40 so H1/M30 opposition still
        # registers — previously this bypassed weighted scoring entirely.
        # ═══════════════════════════════════════════════════════════════
        elif (m1_signal == m5_signal and m1_signal in ['BUY', 'SELL'] and m1_strength > 55
              and (buy_score >= 40 if m1_signal == 'BUY' else sell_score >= 40)):
            consensus['consensus_decision'] = m1_signal
            consensus['consensus_confidence'] = int(max(m1_strength, m5_strength))
            consensus['reason'] = f"M1+M5 Aligned: {m1_signal} (M1@{m1_strength:.0f}% M5@{m5_strength:.0f}%)"
        
        # ═══════════════════════════════════════════════════════════════
        # 🎯 PRIORIDAD 4: M1+M15 o M5+M15 alineados
        # Same guard: weighted score must be plausible.
        # ═══════════════════════════════════════════════════════════════
        elif (m1_signal == m15_signal and m1_signal in ['BUY', 'SELL'] and m1_strength > 55
              and (buy_score >= 40 if m1_signal == 'BUY' else sell_score >= 40)):
            consensus['consensus_decision'] = m1_signal
            consensus['consensus_confidence'] = int(max(m1_strength, m15_vote.get('strength', 50)))
            consensus['reason'] = f"M1+M15 Aligned: {m1_signal}"
        
        elif (m5_signal == m15_signal and m5_signal in ['BUY', 'SELL'] and m5_strength > 55
              and (buy_score >= 40 if m5_signal == 'BUY' else sell_score >= 40)):
            consensus['consensus_decision'] = m5_signal
            consensus['consensus_confidence'] = int(max(m5_strength, m15_vote.get('strength', 50)))
            consensus['reason'] = f"M5+M15 Aligned: {m5_signal}"
        
        # ═══════════════════════════════════════════════════════════════
        # 🎯 PRIORIDAD 5: Señal unidireccional (solo BUY o solo SELL)
        # ═══════════════════════════════════════════════════════════════
        elif buy_votes > 0 and sell_votes == 0 and buy_score > 50:
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(buy_score)
            consensus['reason'] = f"Unidirectional BUY: {buy_votes} TF(s) @ {buy_score:.0f}%"
        
        elif sell_votes > 0 and buy_votes == 0 and sell_score > 50:
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(sell_score)
            consensus['reason'] = f"Unidirectional SELL: {sell_votes} TF(s) @ {sell_score:.0f}%"
        
        # ═══════════════════════════════════════════════════════════════
        # ⚖️ HOLD: Solo cuando hay conflicto real o todo débil
        # ═══════════════════════════════════════════════════════════════
        else:
            consensus['consensus_decision'] = 'HOLD'
            consensus['consensus_confidence'] = int(max(buy_score, sell_score, 40))
            
            if buy_votes == sell_votes and buy_votes > 0:
                consensus['reason'] = f"CONFLICT: {buy_votes} BUY vs {sell_votes} SELL"
            elif buy_score < 45 and sell_score < 45:
                consensus['reason'] = f"WEAK: BUY={buy_score:.0f}% SELL={sell_score:.0f}%"
            else:
                consensus['reason'] = f"MIXED: BUY={buy_score:.0f}% SELL={sell_score:.0f}%"
        
        # Calculate alignment score: how much do TFs agree?
        max_votes = max(buy_votes, sell_votes, hold_votes) if tf_votes else 0
        alignment = (max_votes / len(tf_votes)) * 100 if tf_votes else 0
        consensus['alignment_score'] = int(alignment)
        
        # Store all votes for logging
        consensus['votes'] = tf_votes
        
        log.info(f"[CONSENSUS] 🧠 Decision: {consensus['consensus_decision']} @ {consensus['consensus_confidence']}% | "
                f"Alignment: {consensus['alignment_score']}% | Reason: {consensus['reason']}")
        
        return consensus
    
    def analyze(self, genome: dict) -> dict:
        """
        🧙 WISE AI GRANDPA ANALYSIS - ALL 10 LLMs Vote + Market Hours!
        
        Phase 1: Query ALL 10 LLMs in parallel (everyone votes!)
        Phase 2: Aggregate with sophisticated weighting
        Phase 3: Apply market hours awareness
        Phase 4: NOVA final audit
        
        This is "El Amo de los Amos" - Maximum intelligence!
        """
        symbol = genome.get('metadata', {}).get('symbol', 'XAUUSD')
        tick_id = genome.get('tick_id', 0)
        
        # ⏰ DETECT MARKET SESSION - Gold trading hours matter!
        market_session = get_market_session()
        aggression_mult = market_session['aggression_multiplier']
        log.info(f"[TRINITY] {market_session['description']} (mult={aggression_mult:.2f}x)")
        
        # Add market session to genome so LLMs can use it
        genome['market_session'] = market_session
        
        # DEBUG: Log genome content for data validation
        price_data = genome.get('price_data', {})
        history_len = len(price_data.get('history', []))
        history_len = len(price_data.get('history', []))
        log.debug(f"[TRINITY-IN] {symbol} tick#{tick_id}: price_data.history has {history_len} bars")
        if history_len == 0:
            log.warning(f"[TRINITY-IN] EMPTY HISTORY! price_data keys: {list(price_data.keys())}, genome keys: {list(genome.keys())}")
        
        # 🛡️ VALIDATE ECOSYSTEM DATA BEFORE QUERYING LLMs
        ecosystem_validation = self._validate_ecosystem_data(genome)
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧙 PHASE 1: Query ALL 10 LLMs IN PARALLEL - Everyone votes!
        # ═══════════════════════════════════════════════════════════════════
        llm_responses, threads, lock = {}, [], threading.Lock()
        
        # Query ALL 10 LLMs (not just core 6!)
        for llm_name, port in self.llm_ports.items():
            t = threading.Thread(target=self._query_llm, args=(llm_name, port, genome, llm_responses, lock), daemon=True)
            threads.append(t)
            t.start()
        
        # Join all threads with fast timeout — STRATEGIST (Ollama) will likely miss this window.
        # It continues running as a daemon thread and updates self._strategist_cache when done.
        # That cached value is injected below so GURU votes on the NEXT genome tick.
        for t in threads:
            t.join(timeout=self.timeout)
        
        # CRITICAL FIX: Snapshot dict under lock - timed-out threads may still be writing
        # (moved here from below to place cache injection in the right order)
        with lock:
            llm_responses = dict(llm_responses)
        
        # Inject last known STRATEGIST response if it didn't make the 1.5s window
        if 'STRATEGIST' not in llm_responses and self._strategist_cache:
            llm_responses['STRATEGIST'] = self._strategist_cache
            log.info('[TRINITY] STRATEGIST: using cached response from previous tick')
        
        log.info(f"[TRINITY] 🧙 Received {len(llm_responses)} / {len(self.llm_ports)} LLM responses")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🛡️ PRE-VALIDATION: Use ecosystem data validator
        # ═══════════════════════════════════════════════════════════════════
        
        if not ecosystem_validation['is_valid']:
            log.warning(f"[TRINITY] Ecosystem validation failed: {ecosystem_validation['reason']}")
        
        ecosystem_penalty = ecosystem_validation['confidence_penalty']
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧙 AGGREGATE VOTES FROM ALL 10 LLMs + Apply Ecosystem Penalty
        # No more "core" vs "enhancement" - ALL intelligence matters!
        # ═══════════════════════════════════════════════════════════════════
        
        # 🔧 FIX: Only penalize BUY/SELL signals, NOT HOLD (was paradoxically weakening HOLD
        # during danger periods, making trades MORE likely when they should be LESS likely)
        for llm_name in llm_responses:
            if 'confidence' in llm_responses[llm_name]:
                llm_decision = llm_responses[llm_name].get('decision', 'HOLD')
                if llm_decision in ['BUY', 'SELL']:
                    llm_responses[llm_name]['confidence'] *= ecosystem_penalty
                    if ecosystem_penalty < 1.0:
                        llm_responses[llm_name]['reason'] = f"{llm_responses[llm_name].get('reason', '')} [ECOSYSTEM_CHECK]"
        
        # Aggregate votes from ALL 10 LLMs
        if llm_responses:
            decision, confidence, buy_score, sell_score = self._aggregate_votes(llm_responses)
            log.info(f"[TRINITY] 🧙 10-LLM Vote: {decision} @ {confidence}% (Buy:{buy_score:.0f}% Sell:{sell_score:.0f}%)")
        else:
            # ⚠️ CRITICAL: All LLMs timed out - FORCE HOLD to prevent false trades
            decision = 'HOLD'
            confidence = 15
            buy_score, sell_score = 50, 50
            
            # Mark ALL 10 LLMs as fallback
            for llm_name in self.llm_ports.keys():
                llm_responses[llm_name] = {
                    'decision': 'HOLD', 
                    'confidence': 15, 
                    'reason': 'LLM_TIMEOUT_FALLBACK', 
                    'is_fallback': True
                }
            log.error(f"[TRINITY] 🚫 ALL 10 LLMs TIMEOUT - FORCED HOLD")
        
        # ⏰ APPLY MARKET HOURS MULTIPLIER - London/NY overlap gets boost!
        # 🔧 FIX: Only boost BUY/SELL, not HOLD (was making HOLD look high-confidence)
        if decision in ['BUY', 'SELL']:
            confidence = int(min(95, confidence * aggression_mult))
            log.info(f"[TRINITY] ⏰ Market hours adjusted confidence: {confidence}% (mult={aggression_mult:.2f}x)")
        else:
            log.info(f"[TRINITY] ⏰ Market hours: {decision} not boosted (mult={aggression_mult:.2f}x)")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧠 INTELLIGENT CONSENSUS: Cross-validate with Multi-Timeframe Analysis
        # ═══════════════════════════════════════════════════════════════════
        # If we have timeframe analysis, use it to validate LLM decision
        consensus_result = self._consensus_voting_engine(genome)
        
        # 🎯 FINAL DECISION LOGIC: Combine LLM votes + Timeframe consensus
        llm_decision = decision
        llm_confidence = confidence
        tf_decision = consensus_result['consensus_decision']
        tf_confidence = consensus_result['consensus_confidence']
        tf_alignment = consensus_result['alignment_score']
        
        # ═══════════════════════════════════════════════════════════════
        # 🧠 LLM DECISION IS KING - 12 brains already see ALL data
        # The LLMs receive RSI, MACD, ADX, ATR, patterns, volume,
        # multi-timeframe votes, order flow, sweep data — EVERYTHING.
        # TF consensus uses the SAME data → redundant to override.
        # TF agreement = confidence bonus. TF disagreement = small penalty.
        # NEVER block or reverse the LLM decision.
        # ═══════════════════════════════════════════════════════════════
        
        if llm_decision in ['BUY', 'SELL']:
            final_decision = llm_decision
            
            if llm_decision == tf_decision:
                # ✅ Full agreement — bonus
                final_confidence = int(min(95, llm_confidence * 1.10))
                log.info(f"[TRINITY] ✅ FULL AGREEMENT: LLM+TF both {llm_decision} → {final_confidence}%")
            elif tf_alignment >= 80 and tf_decision in ['BUY', 'SELL']:
                # ⚠️ TFs strongly disagree — small penalty, but LLMs decide
                final_confidence = int(llm_confidence * 0.90)
                log.info(f"[TRINITY] ⚠️ TF disagree ({tf_decision}/{tf_alignment}%) — trusting 12 LLMs: {llm_decision}/{final_confidence}%")
            else:
                # TFs neutral or weakly disagree — minimal penalty
                final_confidence = int(llm_confidence * 0.95)
                log.info(f"[TRINITY] 📊 TF neutral — LLM decision: {llm_decision}/{final_confidence}%")
        else:
            # LLMs say HOLD — but if multi-TF chart structure is overwhelmingly clear,
            # trade the LEVEL rather than waiting for LLM consensus (price reached its mark).
            if tf_decision in ['BUY', 'SELL'] and tf_alignment >= 80 and tf_confidence >= 70:
                final_decision = tf_decision
                final_confidence = int(tf_confidence * 0.80)  # conservative — no LLM backing
                log.info(f"[TRINITY] 🎯 LEVEL INTELLIGENCE: {tf_alignment}% TF alignment on "
                         f"{tf_decision}@{tf_confidence}% overrides LLM-HOLD → {final_decision}@{final_confidence}%")
            else:
                final_decision = llm_decision
                final_confidence = llm_confidence
                log.info(f"[TRINITY] ⏸️ LLMs say {llm_decision} @ {llm_confidence}%")
        
        decision = final_decision
        confidence = final_confidence
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧙 EXTRACT ENHANCEMENT DATA from LLM7-8-9 responses
        # These LLMs provide quality, timing, and execution metadata
        # ═══════════════════════════════════════════════════════════════════
        quality_score = llm_responses.get('OCULUS', {}).get('quality_score', 65)    # Default: moderate quality
        timing_multiplier = llm_responses.get('CHRONOS', {}).get('timing_multiplier', 1.0)  # Default: neutral
        predator_data = llm_responses.get('PREDATOR', {})
        rr_ratio = predator_data.get('rr_ratio', 0)            # Default: unknown
        
        # 🔧 FIX: Extract PREDATOR TP/SL/Entry for propagation to quantum_core
        # Use None defaults so quantum_core can distinguish 'no data' from 'price is 0'
        predator_entry = predator_data.get('entry_price') or None
        # LLM11 returns 'tp_targets' (list) and 'sl' (float), not 'take_profit'/'stop_loss'
        _tp_targets = predator_data.get('tp_targets') or []
        predator_tp = _tp_targets[0] if _tp_targets else (predator_data.get('take_profit') or None)
        predator_sl = predator_data.get('sl') or predator_data.get('stop_loss') or None
        
        # Ensure numeric types (safety against string values)
        quality_score = float(quality_score) if quality_score is not None else 65.0
        timing_multiplier = float(timing_multiplier) if timing_multiplier is not None else 1.0
        rr_ratio = float(rr_ratio) if rr_ratio is not None else 0.0
        predator_entry = float(predator_entry) if predator_entry else None
        predator_tp = float(predator_tp) if predator_tp else None
        predator_sl = float(predator_sl) if predator_sl else None
        
        log.info(f"[TRINITY] 🧙 Enhancement data: Quality={quality_score:.0f}% | Timing={timing_multiplier:.2f}x | R:R={rr_ratio:.2f}")
        if predator_tp and predator_tp > 0 and predator_sl and predator_sl > 0:
            log.info(f"[TRINITY] 🎯 PREDATOR TP/SL: Entry={predator_entry or 0:.2f}, TP={predator_tp:.2f}, SL={predator_sl:.2f}")
        
        # ═══════════════════════════════════════════════════════════════════
        # APPLY ENHANCEMENT MODIFIERS from LLM7-8-9
        # ⭐ NOW BIDIRECTIONAL: Good scores boost, bad scores penalize
        # ═══════════════════════════════════════════════════════════════════
        
        # Quality gate: LLM7 OCULUS data quality affects confidence BIDIRECTIONALLY
        # 🔧 FIX 2026-03-04: Quality modifiers reduced — were too aggressive (+15/-25)
        if quality_score < 40:
            confidence = max(25, confidence - 15)
            log.warning(f"[TRINITY] Data quality VERY LOW ({quality_score}%) - confidence reduced to {confidence}%")
        elif quality_score < 55:
            confidence = max(30, confidence - 8)
            log.warning(f"[TRINITY] Data quality LOW ({quality_score}%) - confidence reduced to {confidence}%")
        elif quality_score >= 80:
            confidence = min(95, confidence + 5)
            log.info(f"[TRINITY] Data quality EXCELLENT ({quality_score}%) - confidence boosted to {confidence}%")
        elif quality_score >= 65:
            confidence = min(92, confidence + 3)
            log.info(f"[TRINITY] Data quality GOOD ({quality_score}%) - confidence boosted to {confidence}%")
        
        # Timing: LLM8 CHRONOS timing affects confidence BIDIRECTIONALLY
        # 🧠 FIX: CHRONOS often returns frozen static value (40%, timing=0.56x)
        # Detect frozen output and limit damage. Static output ≠ bad timing.
        _chronos_conf = llm_responses.get('CHRONOS', {}).get('confidence', 0)
        _chronos_frozen = abs(_chronos_conf - 40.0) < 0.01 and abs(timing_multiplier - 0.56) < 0.05
        
        if _chronos_frozen:
            # CHRONOS is returning static values — don't trust timing signal
            log.warning(f"[TRINITY] ⚠️ CHRONOS FROZEN (conf={_chronos_conf:.0f}%, timing={timing_multiplier:.2f}x) — ignoring timing penalty")
        # 🔧 FIX 2026-03-04: Timing modifiers reduced — were boosting too much
        elif timing_multiplier >= 1.5:
            confidence = min(95, confidence + 5)
            log.info(f"[TRINITY] Excellent timing (mult={timing_multiplier:.2f}x) - confidence boosted to {confidence}%")
        elif timing_multiplier >= 1.2:
            confidence = min(92, confidence + 3)
            log.info(f"[TRINITY] Good timing (mult={timing_multiplier:.2f}x) - confidence boosted to {confidence}%")
        elif timing_multiplier <= 0.6:
            confidence = max(40, confidence - 10)
            log.warning(f"[TRINITY] BAD timing (mult={timing_multiplier:.2f}x) - confidence reduced to {confidence}%")
        elif timing_multiplier <= 0.8:
            confidence = max(40, confidence - 5)
            log.warning(f"[TRINITY] Poor timing (mult={timing_multiplier:.2f}x) - confidence reduced to {confidence}%")
        
        # ⭐ R:R VETO: LLM9 PREDATOR Risk:Reward ratio affects decision
        # 🔧 AJUSTADO: Con TP=20 pips, SL=15 pips, R:R natural = 1.33
        # Bajar threshold de veto porque stops más amplios reducen R:R
        if rr_ratio > 0:
            if rr_ratio < 0.6:
                # R:R muy bajo - force HOLD (antes era 0.8)
                log.warning(f"[TRINITY] 🚫 R:R VETO: {rr_ratio:.2f} < 0.6 - Trade would have bad R:R")
                decision = 'HOLD'
                confidence = max(20, confidence * 0.3)
            elif rr_ratio < 1.0:
                # R:R marginal - reduce confidence (antes era 1.2)
                confidence = max(40, confidence - 10)
                log.warning(f"[TRINITY] ⚠️ Marginal R:R ({rr_ratio:.2f}) - confidence reduced to {confidence}%")
            elif rr_ratio >= 2.5:
                # Excellent R:R - boost confidence
                confidence = min(95, confidence + 10)
                log.info(f"[TRINITY] 💰 Excellent R:R ({rr_ratio:.2f}) - confidence boosted to {confidence}%")
            elif rr_ratio >= 1.5:
                # Good R:R - slight boost (antes era 1.8)
                confidence = min(92, confidence + 5)
                log.info(f"[TRINITY] ✅ Good R:R ({rr_ratio:.2f}) - confidence boosted to {confidence}%")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧠 PHASE 2.5: STRUCTURE POSITION INTELLIGENCE (SPI)
        # "Is price at HH? Wait for pullback. Is price at pullback zone? GO!"
        # This is the MACRO VISION that prevents buying tops and selling bottoms.
        # ═══════════════════════════════════════════════════════════════════
        
        if decision in ['BUY', 'SELL']:
            spi_decision, spi_confidence, spi_context = self._structure_position_intelligence(genome, decision, confidence)
            if spi_context.get('spi_active'):
                # 🛱️ SPI BYPASS GUARD: If LLM + TF already AGREE on direction (conflict gate validated),
                # SPI micro-structure can only ADJUST confidence, NOT override to HOLD.
                # M1 20-bar local structure must not block a trade confirmed by 5 TFs + 4 LLMs.
                _tf_agrees_with_llm = (tf_decision == decision) and tf_confidence >= 40
                _spi_wants_to_block = (spi_decision != decision)
                if _spi_wants_to_block and _tf_agrees_with_llm:
                    log.warning(f"[SPI] ⚠️ SPI wanted to block {decision} but TF+LLM agree ({tf_decision}@{tf_confidence}%) — suppressing SPI override")
                    # Keep both direction AND confidence from LLM consensus
                    # SPI confidence was calculated for its HOLD, not for our SELL/BUY
                    decision = decision
                    # confidence unchanged — do NOT apply spi_confidence here
                elif _spi_wants_to_block:
                    # SPI blocks and TF doesn't agree with LLM — allow SPI override
                    decision = spi_decision
                    confidence = spi_confidence
                else:
                    # SPI agrees with direction — apply its confidence adjustment
                    decision = spi_decision
                    confidence = spi_confidence
                # Store SPI context for downstream use
                genome['_spi_context'] = spi_context
        
        # ═══════════════════════════════════════════════════════════════════
        # 🚀 PHASE 3: Query LLM10 NOVA for AUDIT & EMERGENCY HALT
        # ═══════════════════════════════════════════════════════════════════
        
        # Build full decision context for LLM10
        trinity_decision = {
            'consensus_decision': decision,
            'consensus_confidence': confidence,
            'alignment_score': consensus_result['alignment_score'],
            'reason': consensus_result['reason'],
            'votes': consensus_result['votes']
        }
        
        # Store ecosystem validation in genome for LLM10 access
        genome['_ecosystem_validation'] = ecosystem_validation
        
        # Query LLM10 NOVA — passes ALL individual LLM votes so NOVA has 10-brain context
        nova_response = self._query_llm10_nova(genome, trinity_decision, llm_responses)
        # FIX: Store audit response under separate key to preserve Phase 1 voting data
        llm_responses['NOVA_AUDIT'] = nova_response
        
        # 🚨 EMERGENCY HALT (Hueco #23)
        if nova_response.get('emergency_halt'):
            log.critical(f"[TRINITY] 🛑 EMERGENCY HALT triggered by NOVA: {nova_response.get('reasoning')}")
            return {
                'decision': 'HOLD',
                'confidence': 0,
                'reasoning': f'EMERGENCY_HALT: {nova_response.get("reasoning")}',
                'llm_responses': llm_responses,
                'validation': ecosystem_validation,
                'emergency': True,
                'scores': {
                    'buy_score': 0,
                    'sell_score': 0,
                    'hold_score': 100
                }
            }
        
        # Apply NOVA quality multiplier to final confidence
        # Floor at 0.85: even poor quality NOVA (59/100=0.768) can't cut confidence more than 15%
        nova_multiplier = max(0.85, nova_response.get('quality_multiplier', 1.0))  # Floor 0.85, NEUTRAL default
        confidence_before = confidence
        confidence = int(confidence * nova_multiplier)
        
        # Clamp to reasonable bounds
        confidence = max(15, min(95, confidence))
        
        # Log the adjustment
        if nova_multiplier < 1.0:
            log.warning(f"[TRINITY] 🚀 NOVA audit: {nova_response.get('audit_score')}% | "
                       f"Multiplier {nova_multiplier:.2f}x: confidence {confidence_before}% → {confidence}% (defensive)")
        elif nova_multiplier > 1.0:
            log.info(f"[TRINITY] 🚀 NOVA audit: {nova_response.get('audit_score')}% | "
                    f"Multiplier {nova_multiplier:.2f}x: confidence {confidence_before}% → {confidence}% (boost)")
        else:
            log.info(f"[TRINITY] 🚀 NOVA audit: {nova_response.get('audit_score')}% | "
                    f"Multiplier {nova_multiplier:.2f}x: confidence unchanged at {confidence}%")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🔧 FIX: REMOVED OLD NOVA-MSDA block — was applying NOVA penalty TWICE
        # Phase 3 audit above already applies nova_multiplier. Keeping this
        # would compound: confidence * 0.7 * 0.7 = 49% — killing ALL trades.
        # ═══════════════════════════════════════════════════════════════════
        
        llm_summary = ', '.join([f"{k}:{v.get('confidence', 0)}%" for k, v in sorted(llm_responses.items())])
        log.info(f'[TRINITY] {symbol} tick#{tick_id}: {decision} @ {confidence}% | LLMs:{len(llm_responses)}/{len(self.llm_ports)} [{llm_summary}]')

        # FIX #8: Session-aware minimum confidence gate
        # Prevents low-confidence trades during off-hours (0-8 UTC Asian)
        from datetime import datetime as _dt8
        _utc_h8 = _dt8.utcnow().hour
        _min_conf8 = (68 if _utc_h8 < 8 else
                      57 if _utc_h8 < 12 else
                      60 if _utc_h8 < 17 else 65)
        _tm8 = timing_multiplier  # assigned above when LLM8/CHRONOS queried
        if _tm8 >= 1.2:   _min_conf8 = max(50, _min_conf8 - 3)
        elif _tm8 <= 0.6: _min_conf8 = min(78, _min_conf8 + 6)
        if decision in ('BUY', 'SELL') and confidence < _min_conf8:
            log.info(f'[TRINITY] Session gate ({_utc_h8}h UTC): '
                     f'{confidence}% < min {_min_conf8}% (tm={_tm8:.2f}) -> HOLD')
            decision = 'HOLD'
            confidence = max(confidence, 20)

        return {
            'decision': decision, 
            'confidence': confidence, 
            'llm_responses': llm_responses, 
            'scores': {
                'buy_score': buy_score, 
                'sell_score': sell_score, 
                'hold_score': max(0, 100-buy_score-sell_score)
            },
            # Enhancement data from LLM7-8-9
            'quality_score': quality_score,
            'timing_multiplier': timing_multiplier,
            'rr_ratio': rr_ratio,
            # 🔧 FIX: Use `or` instead of .get() fallback — .get() returns None when key exists with None value
            'position_multiplier': llm_responses.get('PREDATOR', {}).get('position_size') or llm_responses.get('PREDATOR', {}).get('position_multiplier') or 1.0,
            # 🔧 FIX: Propagate PREDATOR TP/SL to root for quantum_core consumption
            'tp': predator_tp,
            'sl': predator_sl,
            'entry_price': predator_entry,
            # 🧠 Consensus voting data
            'consensus': {
                'decision': consensus_result['consensus_decision'],
                'confidence': consensus_result['consensus_confidence'],
                'alignment_score': consensus_result['alignment_score'],
                'votes': consensus_result['votes'],
                'reason': consensus_result['reason']
            },
            # Validation data
            'ecosystem_penalty': ecosystem_penalty,
            'ecosystem_validation': {
                'is_valid': ecosystem_validation['is_valid'],
                'sl_caution': ecosystem_validation['sl_caution'],
                'velocity_alert': ecosystem_validation['velocity_alert'],
                'timeframe_disagreement': ecosystem_validation['timeframe_disagreement'],
                'reason': ecosystem_validation['reason']
            }
        }
    
    def _query_enhancement_llm(self, llm_name: str, port: int, genome: dict) -> dict:
        """Query enhancement LLMs (7-8-9) with simple request format"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)  # Faster timeout for enhancement LLMs
            sock.connect((self.host, port))
            
            # Send request
            request_json = json.dumps(genome).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            
            # Receive response
            response_header = sock.recv(4)
            if response_header and len(response_header) == 4:
                response_length = struct.unpack('>I', response_header)[0]
                response_data = b''
                while len(response_data) < response_length:
                    chunk = sock.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk
                
                if response_data:
                    response = json.loads(response_data.decode('utf-8'))
                    sock.close()
                    return response
            
            sock.close()
            return None
        
        except socket.timeout:
            log.debug(f'[TRINITY<-{llm_name}] TIMEOUT on port {port}')
            return None
        except ConnectionRefusedError:
            log.debug(f'[TRINITY<-{llm_name}] NOT RUNNING on port {port}')
            return None
        except Exception as e:
            log.debug(f'[TRINITY<-{llm_name}] Error: {e}')
            return None
    
    def _query_llm(self, llm_name: str, port: int, genome: dict, responses: dict, lock: threading.Lock):
        try:
            # Get indicators - try both paths (structure can vary)
            indicators = genome.get('indicators', {}).get('current', {})
            if not indicators:
                indicators = genome.get('indicators', {})
            if not isinstance(indicators, dict):
                indicators = {}
            
            price_data = genome.get('price_data', {})
            tick_data = genome.get('tick_data', {})
            
            # Get price from multiple sources
            price = tick_data.get('last', 0)
            if price <= 0:
                bid = tick_data.get('bid', 0)
                ask = tick_data.get('ask', 0)
                if bid > 0 and ask > 0:
                    price = (bid + ask) / 2.0
                else:
                    price = price_data.get('close', 0)
            
            # ============================================================
            # PRIORITY 1: Use bar_data.closes (has LIVE TICK already appended by quantum_core)
            # This is the FIX for stale M1 bar data causing extreme RSI/ADX
            # ============================================================
            bar_data = genome.get('bar_data', {})
            bar_closes = bar_data.get('closes', [])
            
            closes = []
            highs = []
            lows = []
            opens = []
            
            if bar_closes and len(bar_closes) >= 5:
                # bar_data.closes has live tick already - USE IT
                closes = [float(c) for c in bar_closes if c and float(c) > 0]
                highs = [float(h) for h in bar_data.get('highs', bar_closes)]
                lows = [float(l) for l in bar_data.get('lows', bar_closes)]
                opens = [float(o) for o in bar_data.get('opens', closes)]  # ⭐ FIX: Use REAL opens from bar_data
                log.debug(f"[_query_llm] {llm_name}: ✅ Using bar_data.closes: {len(closes)} prices (LIVE TICK INCLUDED)")
            else:
                # FALLBACK: Extract from price_data.history (M1 candles)
                candles = price_data.get('history', [])
                
                for c in candles:
                    if isinstance(c, dict):
                        closes.append(float(c.get('close', c.get('C', price))))
                        highs.append(float(c.get('high', c.get('H', price))))
                        lows.append(float(c.get('low', c.get('L', price))))
                        opens.append(float(c.get('open', c.get('O', price))))
                    elif isinstance(c, (int, float)):
                        closes.append(float(c))
                        highs.append(float(c))
                        lows.append(float(c))
                        opens.append(float(c))
                    elif isinstance(c, str):
                        try:
                            parsed = json.loads(c)
                            if isinstance(parsed, dict):
                                closes.append(float(parsed.get('close', parsed.get('C', price))))
                                highs.append(float(parsed.get('high', parsed.get('H', price))))
                                lows.append(float(parsed.get('low', parsed.get('L', price))))
                                opens.append(float(parsed.get('open', parsed.get('O', price))))
                        except:
                            pass
                
                if len(closes) < 5:
                    log.warning(f"[_query_llm] {llm_name}: ⚠️ LOW DATA: {len(closes)} closes, price={price:.2f}")
            
            # Fallback if no history
            if not closes:
                closes = [float(price)]
                log.warning(f"[_query_llm] {llm_name}: ⚠️ No history! Using single price: {price}")
            if not highs:
                highs = [float(price)]
            if not lows:
                lows = [float(price)]
            if not opens:
                opens = [float(price)]
            
            # ============================================================
            # CRITICAL FIX: ADD CURRENT TICK PRICE TO END OF HISTORY
            # M1 bars only update every minute, but tick price changes every second
            # This ensures LLMs ALWAYS see the CURRENT price, not stale bar data
            # ============================================================
            if price > 0:
                # ALWAYS append current tick price if different from last close
                # Changed from > 0.01 to > 0.001 (0.1 pip for XAUUSD)
                # This catches micro-movements that were previously ignored
                if len(closes) > 0:
                    price_diff = abs(closes[-1] - price)
                    if price_diff > 0.001:  # More than 0.1 pip difference
                        # Append current tick price to closes array
                        closes.append(float(price))
                        highs.append(float(price))  # Current tick is its own high
                        lows.append(float(price))   # Current tick is its own low
                        opens.append(closes[-2] if len(closes) > 1 else float(price))  # Open = previous close
                        log.info(f"[_query_llm] {llm_name}: ✅ LIVE TICK ADDED: {price:.2f} (was {closes[-2]:.2f}, diff={price_diff:.3f})")
                    else:
                        log.debug(f"[_query_llm] {llm_name}: Tick {price:.2f} same as last close (diff={price_diff:.3f})")
                else:
                    # First tick - always add
                    closes.append(float(price))
                    highs.append(float(price))
                    lows.append(float(price))
                    opens.append(float(price))
                    log.info(f"[_query_llm] {llm_name}: ✅ FIRST TICK: {price:.2f}")
            
            # ============================================================
            # NORMALIZE CANDLES FOR LLM5 (requires 'close', 'open', 'high', 'low', 'volume')
            # ============================================================
            # ⭐ FIX: Extract real volumes from bar_data instead of hardcoding 100.0
            bar_volumes = [float(v) for v in bar_data.get('volumes', []) if v] if bar_data else []
            normalized_candles = []
            for i in range(min(len(closes), len(opens), len(highs), len(lows))):
                vol = float(bar_volumes[i]) if i < len(bar_volumes) and bar_volumes[i] else 100.0
                normalized_candles.append({
                    'close': float(closes[i]),
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'volume': vol
                })
            
            # ============================================================
            # BUILD REQUEST WITH CORRECT FIELD NAMES FOR EACH LLM
            # ============================================================
            # Extract raw indicators from genome
            rsi = float(indicators.get('rsi', 50))
            adx = float(indicators.get('adx', 25))
            atr_raw = float(indicators.get('atr_pips', indicators.get('atr', 0)))
            macd_line = float(indicators.get('macd', 0))  # MACD line (EMA12 - EMA26)
            # 🔧 FIX: Fallback was macd_line * 0.2 — fabricated phantom momentum.
            # Zero is honest: 'unknown histogram' rather than fake directional signal.
            macd_hist = float(indicators.get('macd_histogram', 0))
            
            # Calculate SMA indicators from closes if available
            sma_50 = price
            sma_200 = price
            if len(closes) >= 50:
                sma_50 = sum(closes[-50:]) / 50
            if len(closes) >= 200:
                sma_200 = sum(closes[-200:]) / 200
            
            # Calculate Bollinger Bands from closes if available
            bb_upper = price * 1.02
            bb_lower = price * 0.98
            if len(closes) >= 20:
                mean = statistics.mean(closes[-20:])
                stdev = statistics.stdev(closes[-20:]) if len(closes[-20:]) > 1 else 0
                bb_upper = mean + (2.0 * stdev)
                bb_lower = mean - (2.0 * stdev)
            
            # Build request with BOTH original names AND LLM-expected names
            # ⭐ Extract current bar OHLC for LLMs
            current_bar = bar_data.get('current', {})
            current_open = float(current_bar.get('open', opens[-1] if opens else price))
            current_high = float(current_bar.get('high', highs[-1] if highs else price))
            current_low = float(current_bar.get('low', lows[-1] if lows else price))
            current_close = float(current_bar.get('close', price))
            
            request = {
                'symbol': genome.get('metadata', {}).get('symbol', 'XAUUSD'),
                'price': float(price),
                'current_price': float(price),
                # ⭐ Current bar OHLC - available to all LLMs
                'current_open': current_open,
                'current_high': current_high,
                'current_low': current_low,
                'current_close': current_close,
                'prices': [float(c) for c in closes],
                'candles': normalized_candles,  # ← FIX: Use normalized candles for LLM5
                
                # === INDICATORS - Multiple naming conventions for compatibility ===
                # Original names (what Trinity currently sends)
                'rsi': float(rsi),
                'adx': float(adx),
                'atr': float(atr_raw),
                'macd': float(macd_line),  # MACD line
                
                # LLM1 expected names (what LLM1 searches for)
                'atr_14': float(atr_raw),  # ← FIX: LLM1 looks for 'atr_14' not 'atr'
                'macd_histogram': float(macd_hist),  # ← FIX: Now uses ACTUAL histogram, not MACD line!
                'sma_50': float(sma_50),  # ← FIX: LLM1 expects SMA_50
                'sma_200': float(sma_200),  # ← FIX: LLM1 expects SMA_200
                'bb_upper': float(bb_upper),  # ← FIX: LLM1 expects Bollinger Upper
                'bb_lower': float(bb_lower),  # ← FIX: LLM1 expects Bollinger Lower
                
                # Bar data structure for LLM3/4/5
                'bar_data': {
                    'closes': [float(c) for c in closes],
                    'highs': [float(h) for h in highs],
                    'lows': [float(l) for l in lows],
                    'opens': [float(o) for o in opens],
                    'volumes': bar_volumes if bar_volumes else [100.0] * len(closes)
                },
                
                # Full indicators dict for any LLM that needs it
                'indicators': indicators,
                'tick_id': genome.get('tick_id', 0),
                # 🔧 NEW: Market session data for LLM8 CHRONOS timing intelligence
                'market_session': genome.get('market_session', {}),
                # 🔧 NEW: Bid/Ask/Spread for LLM9 PREDATOR execution precision
                'bid': float(tick_data.get('bid', price)),
                'ask': float(tick_data.get('ask', price)),
                'spread': abs(float(tick_data.get('ask', price)) - float(tick_data.get('bid', price))),
            }
            
            # DEBUG: Log request details for each LLM
            log.debug(f"[_query_llm] {llm_name}: Sending request with {len(request['prices'])} prices, {len(request['candles'])} candles, price={price:.2f}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # LLM11 STRATEGIST uses Ollama inference and needs more time
            effective_timeout = self.strategist_timeout if llm_name == 'STRATEGIST' else self.timeout
            sock.settimeout(effective_timeout)
            sock.connect((self.host, port))
            log.info(f"[TRINITY->{llm_name}] ✅ Connected to port {port}")
            
            # Send: 4-byte header + JSON
            request_json = json.dumps(request).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            log.info(f"[TRINITY->{llm_name}] 📤 Sent {len(request_json)} bytes")
            
            # Receive: 4-byte header + JSON (FIX: loop recv for partial headers)
            response_header = b''
            while len(response_header) < 4:
                chunk = sock.recv(4 - len(response_header))
                if not chunk:
                    break
                response_header += chunk
            if response_header and len(response_header) == 4:
                response_length = struct.unpack('>I', response_header)[0]
                response_data = b''
                while len(response_data) < response_length:
                    chunk = sock.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk
                
                if response_data:
                    response = json.loads(response_data.decode('utf-8'))
                    # Fix: SMART_MONEY devuelve 'recommendation' no 'decision'
                    if 'recommendation' in response and 'decision' not in response:
                        response['decision'] = response['recommendation']
                    decision = (response.get('decision') or 'HOLD').upper()
                    # 🔧 FIX: AUDIT is NOVA's Phase 1 response — skip, don't convert to HOLD
                    # Converting to HOLD gives NOVA a 1.9x HOLD vote, suppressing consensus
                    if decision == 'AUDIT':
                        decision = 'NO_TRADE'  # NO_TRADE is already skipped in aggregate
                    if decision not in ['BUY', 'SELL', 'HOLD', 'NO_TRADE']:
                        decision = 'HOLD'
                    confidence = min(100.0, max(0.0, float(response.get('confidence', 50))))
                    
                    with lock:
                        # CRITICAL FIX: LLM5 already provides clean 'chart_patterns' list of strings!
                        # Use it directly instead of extracting from 'patterns' dict list
                        raw_patterns = response.get('patterns', [])
                        chart_patterns_clean = response.get('chart_patterns', [])  # Already clean strings from LLM5
                        
                        if not chart_patterns_clean and raw_patterns:
                            # Fallback: Extract from raw patterns if chart_patterns not provided
                            chart_patterns_clean = []
                            for p in raw_patterns:
                                if isinstance(p, dict):
                                    name = p.get('name', p.get('type', ''))
                                    if name:
                                        chart_patterns_clean.append(str(name))
                                elif isinstance(p, str):
                                    chart_patterns_clean.append(p)
                        
                        responses[llm_name] = {
                            'decision': decision, 
                            'confidence': confidence, 
                            'reason': response.get('reason', response.get('reasoning', '')),
                            # Patterns from LLM5 (SUPREME) - now properly extracted
                            'chart_patterns': chart_patterns_clean,
                            'patterns_found': response.get('patterns_found', len(raw_patterns)),
                            'bullish_patterns': response.get('bullish_patterns', 0),
                            'bearish_patterns': response.get('bearish_patterns', 0),
                            # 🧙 Enhancement fields from LLM7/8/9 (preserved for Trinity analysis)
                            'quality_score': response.get('quality_score', None),       # LLM7 OCULUS
                            'timing_multiplier': response.get('timing_multiplier', None), # LLM8 CHRONOS
                            'timing_score': response.get('timing_score', None),          # LLM8 CHRONOS
                            'rr_ratio': response.get('rr_ratio', None),                  # LLM9 PREDATOR
                            'execution_status': response.get('execution_status', None),  # LLM9 PREDATOR
                            'position_size': response.get('position_size', None),        # LLM9 PREDATOR
                            # 🔧 FIX: Store PREDATOR TP/SL/entry (were lost in transit → always 0)
                            'entry_price': response.get('entry_price', None),            # LLM9 PREDATOR
                            'take_profit': response.get('take_profit', None),            # LLM9 PREDATOR
                            'stop_loss': response.get('stop_loss', None),                # LLM9 PREDATOR
                            # 🔧 F-22: LLM11 STRATEGIST fields (were missing → GURU always HOLD 0%)
                            'strategy': response.get('strategy', None),                  # LLM11 STRATEGIST
                            'conviction': response.get('conviction', None),              # LLM11 STRATEGIST
                            'sizing': response.get('sizing', None),                      # LLM11 STRATEGIST
                            'consciousness_phase': response.get('consciousness_phase', None),  # LLM11 STRATEGIST
                            # 🔧 F-22: LLM12 SENTINEL fields (were missing → SNTL always HOLD 0%)
                            'edge_status': response.get('edge_status', None),            # LLM12 SENTINEL
                            'heatmap_score': response.get('heatmap_score', None),        # LLM12 SENTINEL
                        }
                    log.info(f'[TRINITY<-{llm_name}] {decision}@{confidence:.1f}% | Patterns: {len(chart_patterns_clean)}')
                    # Persist STRATEGIST response so it can be reused when Ollama is slow
                    if llm_name == 'STRATEGIST':
                        self._strategist_cache = dict(responses[llm_name])
            
            sock.close()
        
        except socket.timeout:
            log.warning(f'[TRINITY<-{llm_name}] ⏰ TIMEOUT on port {port} (>{effective_timeout:.0f}s)')
        except ConnectionRefusedError:
            log.warning(f'[TRINITY<-{llm_name}] ❌ NOT RUNNING on port {port}')
        except Exception as e:
            log.warning(f'[TRINITY<-{llm_name}] ⚠️ Error: {type(e).__name__}: {e}')
        finally:
            # ⭐ FIX: Always close socket to prevent file descriptor leak
            try:
                sock.close()
            except Exception:
                pass
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # 🏦 BANK-GRADE CONSENSUS ALGORITHM v2.0
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # This algorithm uses advanced mathematical principles from:
    # - Bayesian Inference (posterior probability estimation)
    # - Game Theory (Nash equilibrium for divergence detection)
    # - Information Theory (Shannon entropy for uncertainty)
    # - Statistical Mechanics (Boltzmann weighting)
    # - Ensemble Learning (weighted meta-learning)
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def _aggregate_votes(self, llm_responses: dict) -> tuple:
        """
        🏦 BANK-GRADE CONSENSUS: Ultra-intelligent 5-LLM fusion algorithm
        
        Mathematical Components:
        1. BAYESIAN POSTERIOR: P(action|evidence) using confidence as likelihood
        2. ENTROPY PENALTY: High disagreement = lower final confidence
        3. MOMENTUM BONUS: Consistent signals get amplified
        4. DIVERGENCE DETECTION: Conflicting signals trigger caution
        5. CONFIDENCE CALIBRATION: Non-linear confidence transformation
        """
        import math
        
        if not llm_responses: 
            return 'HOLD', 50, 50, 50
        
        # FIX: Count only VOTING LLMs — only NOVA_AUDIT is excluded
        # Voting: All 12 LLMs except NOVA_AUDIT = 11 max
        # OCULUS and CHRONOS DO vote (fixed 2026-02-19)
        EXPECTED_VOTING_LLMS = 11  # All 12 minus NOVA_AUDIT
        # Will be updated after signal extraction loop
        num_llms = EXPECTED_VOTING_LLMS
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: EXTRACT AND CALIBRATE INDIVIDUAL SIGNALS
        # ═══════════════════════════════════════════════════════════════
        signals = {'BUY': [], 'SELL': [], 'HOLD': []}
        
        # 🏦 DYNAMIC WEIGHTS: Use LLMPerformanceTracker for adaptive weighting
        llm_weights = {}
        for llm_name in llm_responses.keys():
            llm_weights[llm_name] = self.tracker.get_dynamic_weight(llm_name)
        
        log.debug(f"[BANK-GRADE] Dynamic LLM weights: {llm_weights}")
        
        # 🧠 FROZEN LLM DETECTION: Track static outputs to reduce their influence
        # If an LLM returns the EXACT same confidence 5+ times in a row, it's frozen/broken
        if not hasattr(self, '_llm_history'):
            self._llm_history = {}  # {llm_name: [last_5_confidences]}
        
        # 🧠 NON-VOTING GATE LLMs: These LLMs provide quality/timing/execution
        # data but should NEVER vote on direction. Their enhancement fields
        # (quality_score, timing_multiplier, rr_ratio) are used later.
        # BUG FIX 2026-02-19: These LLMs return HOLD/BUY/SELL after Trinity's
        # _query_llm normalizes their native decisions (APPROVE→HOLD, READY→HOLD).
        # This made them phantom HOLD voters, giving HOLD 5-7 votes vs 2-3 real SELL.
        # Only NOVA_AUDIT is excluded (metadata/audit, not a brain)
        # OCULUS and CHRONOS DO have directional opinions and MUST vote
        NON_VOTING_GATES = {'NOVA_AUDIT'}
        
        for llm_name, llm_data in llm_responses.items():
            decision = llm_data.get('decision', 'HOLD')
            raw_confidence = llm_data.get('confidence', 50)
            
            # 🚫 SKIP NON-VOTING GATES BY NAME (not by decision type)
            # These LLMs were being counted as HOLD voters because their
            # native decisions (APPROVE/READY/etc) got converted to HOLD
            # in _query_llm before reaching this function.
            if llm_name in NON_VOTING_GATES:
                log.debug(f"[BANK-GRADE] Skipping non-voting gate {llm_name} (decision={decision})")
                continue
            
            # Also skip by decision type for any other non-standard responses
            if decision in ['APPROVE', 'CAUTION', 'REJECT', 'READY', 'PREPARING',
                           'WAITING', 'EXECUTE', 'WAIT', 'ABORT', 'NO_TRADE', 'AUDIT',
                           'ABSTAIN']:  # 🔧 AUDIT FIX: LLM12 ABSTAIN was becoming phantom HOLD
                log.debug(f"[BANK-GRADE] Skipping non-voting LLM {llm_name} decision: {decision}")
                continue  # Skip non-voting LLMs
            
            # Normalize other decisions
            if decision not in ['BUY', 'SELL', 'HOLD']:
                decision = 'HOLD'
            
            # 🧠 FROZEN DETECTION: Check if this LLM is returning static values
            if llm_name not in self._llm_history:
                self._llm_history[llm_name] = []
            self._llm_history[llm_name].append(raw_confidence)
            if len(self._llm_history[llm_name]) > 15:
                self._llm_history[llm_name] = self._llm_history[llm_name][-15:]
            
            _is_frozen = False
            _frozen_penalty = 1.0
            # 🔧 F-27 FIX: FROZEN filter was killing 5-6 of 9 voters every tick.
            # LLMs queried every 2s with same data legitimately return same value.
            # Old: 5 reads / var<3.0 / hard EXCLUDE → only 3-4 voters left.
            # New: 10 reads / var<1.0 / WEIGHT PENALTY (no exclude) → all 9 vote.
            if len(self._llm_history[llm_name]) >= 10:
                _last_10 = self._llm_history[llm_name][-10:]
                _variance = max(_last_10) - min(_last_10)
                if _variance < 1.0:  # Truly stuck for 20+ seconds = likely frozen
                    _is_frozen = True
                    _frozen_penalty = 0.4
                    log.info(f"[BANK-GRADE] 🧊 FROZEN LLM: {llm_name} = {raw_confidence:.1f}% (var={_variance:.2f}) → weight x0.4")
                    # 🔧 F-27: Do NOT exclude (no continue). Consistent output ≠ broken.
                    # They still vote with reduced weight. Old `continue` was catastrophic.
                elif _variance < 3.0:  # Low variance → moderate reduction
                    _frozen_penalty = 0.6
                    log.info(f"[BANK-GRADE] 🥶 LOW-VAR LLM: {llm_name} = {raw_confidence:.1f}% (variance={_variance:.2f}) → weight x0.6")
            
            # 🎯 CAP HOLD CONFIDENCE: Prevent single LLM from monopolizing HOLD
            # 🔧 FIX: Was 75% — too aggressive. Strong HOLD convictions (e.g. SMART_MONEY 95%)
            # were silenced, forcing bad trades. Raised to 92% so only extreme values get capped.
            if decision == 'HOLD' and raw_confidence > 92:
                log.debug(f"[BANK-GRADE] {llm_name} HOLD conf capped: {raw_confidence}% -> 92%")
                raw_confidence = 92
            
            # Record signal for tracking (used for future dynamic weights)
            self.tracker.record_signal(llm_name, decision, raw_confidence)
            
            # 🧮 ORACLE-MODE CONFIDENCE CALIBRATION (steep sigmoid)
            # Steeper curve: sharply penalizes lukewarm signals, rewards conviction
            # f(x) = 50 + 50 * tanh(3.5 * (x/100 - 0.5))
            normalized = raw_confidence / 100.0
            calibrated = 50 + 50 * math.tanh(3.5 * (normalized - 0.5))
            
            # Apply LLM-specific weight + frozen penalty
            weight = llm_weights.get(llm_name, 1.0) * _frozen_penalty
            weighted_conf = calibrated * weight
            
            signals[decision].append({
                'llm': llm_name,
                'raw_conf': raw_confidence,
                'calibrated': calibrated,
                'weighted': weighted_conf,
                'weight': weight
            })
        
        # FIX: Use actual voting count — don't inflate denominator with stale expected count
        # Old formula max(actual, EXPECTED) penalized scores when fewer LLMs responded
        actual_voting_count = len(signals['BUY']) + len(signals['SELL']) + len(signals['HOLD'])
        num_llms = max(actual_voting_count, 1)  # At least 1 to avoid division by zero
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: CALCULATE BAYESIAN POSTERIOR PROBABILITIES
        # ═══════════════════════════════════════════════════════════════
        # P(BUY|evidence) ∝ P(evidence|BUY) * P(BUY)
        # Using uniform priors: P(BUY) = P(SELL) = P(HOLD) = 1/3
        
        def calculate_likelihood(signal_list):
            """Calculate aggregate likelihood from LLM signals"""
            if not signal_list:
                return 0.0
            
            # Product of normalized confidences (log-sum for numerical stability)
            log_likelihood = sum(math.log(max(s['weighted'] / 100.0, 0.01)) for s in signal_list)
            # Average weight contribution
            avg_weight = sum(s['weight'] for s in signal_list) / len(signal_list)
            # Count bonus (more LLMs agreeing = higher confidence)
            count_bonus = len(signal_list) / num_llms
            
            return math.exp(log_likelihood) * avg_weight * (1 + count_bonus)
        
        likelihood_buy = calculate_likelihood(signals['BUY'])
        likelihood_sell = calculate_likelihood(signals['SELL'])
        likelihood_hold = calculate_likelihood(signals['HOLD']) * 0.65  # 🔧 FIX: HOLD penalty relaxed (was 0.4 = too harsh, killed HOLD even with majority)
        
        total_likelihood = likelihood_buy + likelihood_sell + likelihood_hold + 1e-10
        
        posterior_buy = likelihood_buy / total_likelihood
        posterior_sell = likelihood_sell / total_likelihood
        posterior_hold = likelihood_hold / total_likelihood
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: CALCULATE SHANNON ENTROPY (DISAGREEMENT MEASURE)
        # ═══════════════════════════════════════════════════════════════
        # H = -Σ p(x) * log2(p(x))
        # High entropy = high disagreement = lower confidence
        
        def entropy(probs):
            """Calculate Shannon entropy of probability distribution"""
            return -sum(p * math.log2(max(p, 1e-10)) for p in probs if p > 0)
        
        distribution = [posterior_buy, posterior_sell, posterior_hold]
        current_entropy = entropy(distribution)
        max_entropy = math.log2(3)  # Maximum entropy for 3 outcomes
        
        # Entropy penalty: 0 (perfect agreement) to 1 (complete disagreement)
        entropy_penalty = current_entropy / max_entropy
        agreement_bonus = 1.0 - entropy_penalty  # Higher is better
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 4: DIVERGENCE DETECTION (CONFLICTING SIGNALS)
        # ═══════════════════════════════════════════════════════════════
        # If BUY and SELL both have strong signals, be cautious
        
        buy_strength = sum(s['weighted'] for s in signals['BUY']) if signals['BUY'] else 0
        sell_strength = sum(s['weighted'] for s in signals['SELL']) if signals['SELL'] else 0
        
        # 🧠 FIX 2026-02-19: RATIO-BASED DIVERGENCE (was min-based)
        # OLD formula: 2*min(B,S)/(B+S) → 0.61 even when SELL dominates 2.3:1
        # NEW formula: 1/ratio → LOW when one side clearly dominates
        # Examples:
        #   SELL=386 vs BUY=169 → ratio=2.28 → div=0.44 (clear signal, low divergence)
        #   SELL=200 vs BUY=200 → ratio=1.0  → div=1.00 (real conflict, max divergence)
        #   SELL=500 vs BUY=100 → ratio=5.0  → div=0.20 (dominant signal, very low)
        # This fixes the mathematical impossibility where divergence was ALWAYS > 0.5
        # with 10 diverse LLMs, which then hard-capped confidence at 55 (below min=63)
        if buy_strength > 0 and sell_strength > 0:
            strength_ratio = max(buy_strength, sell_strength) / (min(buy_strength, sell_strength) + 1e-10)
            divergence = 1.0 / strength_ratio  # 0.0 (one side dominates) to 1.0 (equal conflict)
        else:
            divergence = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 4.5: CONFIDENCE VARIANCE PENALTY (QUALITY OF AGREEMENT)
        # ═══════════════════════════════════════════════════════════════
        # If LLMs agree on direction but have wildly different confidence
        # levels (e.g., 95% vs 55%), the agreement quality is lower.
        # High variance = less reliable consensus
        
        def _confidence_variance_penalty(signal_list):
            """Penalize when agreeing LLMs have high confidence spread"""
            if len(signal_list) < 2:
                return 1.0  # No penalty with 0-1 signals
            confs = [s['raw_conf'] for s in signal_list]
            mean_c = sum(confs) / len(confs)
            variance = sum((c - mean_c) ** 2 for c in confs) / len(confs)
            stdev = variance ** 0.5
            # stdev > 25 = significant disagreement in conviction
            # Penalty: 0% at stdev=0, up to 15% at stdev=35+
            penalty = min(stdev / 35.0, 1.0) * 0.15
            return 1.0 - penalty
        
        conf_var_buy = _confidence_variance_penalty(signals['BUY'])
        conf_var_sell = _confidence_variance_penalty(signals['SELL'])
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 5: CALCULATE WEIGHTED SCORES FOR EACH ACTION
        # ═══════════════════════════════════════════════════════════════
        
        def calculate_action_score(signal_list, posterior):
            """Calculate final score for an action"""
            if not signal_list:
                return 0.0
            
            # Base: sum of weighted confidences
            base_score = sum(s['weighted'] for s in signal_list)
            
            # Normalize by number of LLMs
            normalized = base_score / (num_llms * 100)
            
            # Apply posterior probability
            bayesian_score = normalized * (1 + posterior)
            
            # Apply agreement bonus
            final_score = bayesian_score * (0.5 + 0.5 * agreement_bonus)
            
            return final_score * 100  # Scale to 0-100
        
        buy_score = calculate_action_score(signals['BUY'], posterior_buy)
        sell_score = calculate_action_score(signals['SELL'], posterior_sell)
        hold_score = calculate_action_score(signals['HOLD'], posterior_hold) * 0.70  # 🔧 FIX: HOLD dampening relaxed (was 0.5 = too harsh)
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 6: FINAL DECISION WITH CONFIDENCE CALCULATION
        # ═══════════════════════════════════════════════════════════════
        
        total_score = buy_score + sell_score + hold_score + 1e-10
        
        # Normalize scores to percentages
        buy_pct = (buy_score / total_score) * 100
        sell_pct = (sell_score / total_score) * 100
        hold_pct = (hold_score / total_score) * 100
        
        # Decision based on highest score - 🎯 ELEVATED STANDARDS
        # 🧠 FIX 2026-02-19: Score dominance bonus — when one direction CRUSHES the others,
        # the signal is clear even with few voters. Prevents HOLD zombie from 5 passive LLMs
        # killing 3 strong directional votes.
        if buy_score > sell_score and buy_score > hold_score:
            decision = 'BUY'
            vote_count = len(signals['BUY'])
            total_confidence = sum(s['raw_conf'] for s in signals['BUY'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            
            # 🚀 HYPER-INTELLIGENCE: Aggressive momentum bonus (4+ LLMs = GO!)
            majority_bonus = 1.0 + (vote_count - 3.0) * 0.14
            
            # 🧠 SCORE DOMINANCE: meaningful epsilon to prevent trillion ratios
            score_ratio = buy_score / (max(sell_score, hold_score) + 1.0)  # 🔧 FIX: epsilon=1.0 not 1e-10
            if score_ratio >= 2.0:
                dominance_bonus = min(1.12, 1.0 + (score_ratio - 2.0) * 0.03)  # 🔧 FIX: capped at 1.12 not 1.25
                log.info(f"[Trinity] 🧠 BUY SCORE DOMINANCE: ratio={score_ratio:.1f}x → bonus={dominance_bonus:.2f}")
            else:
                dominance_bonus = 1.0
            
            # 🎯 SMART DIVERGENCE: Only penalize if divergence is significant
            divergence_factor = max(divergence - 0.2, 0) * 0.35
            
            # 🧠 BLEND raw LLM confidence with Bayesian ensemble score
            # 60/40 blend: ensemble intelligence + individual conviction
            blended_conf = raw_conf * 0.6 + buy_pct * 0.4  # 🔧 FIX: 60% raw + 40% Bayesian (was inverted)
            confidence = round(blended_conf * majority_bonus * dominance_bonus * (1 - divergence_factor) * conf_var_buy)
            
            # 🧠 FIX 2026-02-19: CONVICTION AMPLIFIER — same as SELL
            if vote_count >= 2:
                high_conf_voters = sum(1 for s in signals['BUY'] if s['raw_conf'] >= 60)
                if high_conf_voters >= 2:
                    avg_conviction = sum(s['raw_conf'] for s in signals['BUY'] if s['raw_conf'] >= 60) / high_conf_voters
                    conviction_boost = (high_conf_voters - 1) * (avg_conviction - 55) / 100.0 * 0.15
                    conviction_boost = max(0, min(0.20, conviction_boost))
                    confidence = round(confidence * (1.0 + conviction_boost))
                    if conviction_boost > 0.02:
                        log.info(f"[Trinity] 🔥 BUY CONVICTION: {high_conf_voters} strong voters (avg={avg_conviction:.0f}%) → +{conviction_boost:.1%}")
            
            # 🔥 INTELLIGENT THRESHOLD: Lowered from 63→45 to stop killing valid signals
            # The old min_confidence=63 was a death trap: Bayesian ensemble could say
            # 70% BUY but if individual LLMs averaged 36%, confidence=36 < 63 → HOLD.
            # 🔧 F-28 FIX: Old min=48 was unreachable after multiplicative penalties.
            # FROZEN weight reduction + majority_bonus + divergence + calibration
            # stack to reduce 62% raw → ~45% calculated → fail min=48 → HOLD.
            if score_ratio >= 2.0 and vote_count >= 2:
                min_confidence = 35  # Strong Bayesian signal = trust it
            elif vote_count >= 4 and divergence <= 0.3:
                min_confidence = 38
            else:
                min_confidence = 40
            if confidence < min_confidence:
                decision = 'HOLD'
                confidence = 45
                log.info(f"[Trinity] ⚠️ BUY→HOLD: conf={confidence} < min={min_confidence} (raw={raw_conf:.0f} blend={blended_conf:.0f})")
            
        elif sell_score > buy_score and sell_score > hold_score:
            decision = 'SELL'
            vote_count = len(signals['SELL'])
            total_confidence = sum(s['raw_conf'] for s in signals['SELL'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            
            # 🚀 HYPER-INTELLIGENCE: Same aggressive bonus for SELL
            majority_bonus = 1.0 + (vote_count - 3.0) * 0.14
            
            # 🧠 SCORE DOMINANCE: meaningful epsilon to prevent trillion ratios
            score_ratio = sell_score / (max(buy_score, hold_score) + 1.0)  # 🔧 FIX: epsilon=1.0 not 1e-10
            if score_ratio >= 2.0:
                dominance_bonus = min(1.12, 1.0 + (score_ratio - 2.0) * 0.03)  # 🔧 FIX: capped at 1.12 not 1.25
                log.info(f"[Trinity] 🧠 SELL SCORE DOMINANCE: ratio={score_ratio:.1f}x → bonus={dominance_bonus:.2f}")
            else:
                dominance_bonus = 1.0
            
            # 🎯 SMART DIVERGENCE: Only penalize if divergence is significant
            divergence_factor = max(divergence - 0.2, 0) * 0.35
            
            # 🧠 BLEND raw LLM confidence with Bayesian ensemble score
            blended_conf = raw_conf * 0.6 + sell_pct * 0.4  # 🔧 FIX: 60% raw + 40% Bayesian (was inverted)
            confidence = round(blended_conf * majority_bonus * dominance_bonus * (1 - divergence_factor) * conf_var_sell)
            
            # 🧠 FIX 2026-02-19: CONVICTION AMPLIFIER — lowered threshold from 70→60
            # because LLMs on M1 Gold rarely exceed 60% confidence individually.
            if vote_count >= 2:
                high_conf_voters = sum(1 for s in signals['SELL'] if s['raw_conf'] >= 60)
                if high_conf_voters >= 2:
                    avg_conviction = sum(s['raw_conf'] for s in signals['SELL'] if s['raw_conf'] >= 60) / high_conf_voters
                    conviction_boost = (high_conf_voters - 1) * (avg_conviction - 55) / 100.0 * 0.15
                    conviction_boost = max(0, min(0.20, conviction_boost))  # Cap at 20%
                    confidence = round(confidence * (1.0 + conviction_boost))
                    if conviction_boost > 0.02:
                        log.info(f"[Trinity] 🔥 SELL CONVICTION: {high_conf_voters} strong voters (avg={avg_conviction:.0f}%) → +{conviction_boost:.1%}")
            
            # 🔥 INTELLIGENT THRESHOLD: Lowered from 63→45
            # 🔧 F-28 FIX: Same as BUY side — reduced thresholds.
            if score_ratio >= 2.0 and vote_count >= 2:
                min_confidence = 35  # Strong Bayesian signal = trust it
            elif vote_count >= 4 and divergence <= 0.3:
                min_confidence = 38
            else:
                min_confidence = 40
            if confidence < min_confidence:
                decision = 'HOLD'
                confidence = 45
                log.info(f"[Trinity] ⚠️ SELL→HOLD: conf={confidence} < min={min_confidence} (raw={raw_conf:.0f} blend={blended_conf:.0f})")
            
        else:
            decision = 'HOLD'
            if signals['HOLD']:
                raw_conf = sum(s['raw_conf'] for s in signals['HOLD']) / len(signals['HOLD'])
            else:
                raw_conf = 50
            confidence = int(raw_conf * 0.85)  # HOLD = lower confidence (indecision)
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 7: CONFIDENCE BOUNDS AND FINAL ADJUSTMENTS
        # ═══════════════════════════════════════════════════════════════
        
        # Clamp confidence to valid range
        confidence = max(20, min(95, confidence))
        
        # If high divergence, cap confidence - ORACLE: stricter cap
        if divergence > 0.5:
            confidence = min(confidence, 55)
            log.info(f"[BANK-GRADE] ⚠️ HIGH DIVERGENCE ({divergence:.2f}) - Confidence capped at 55")
        
        # If perfect agreement (all voting LLMs same decision), boost confidence
        # 🔧 FIX: Require at least 5 REAL voters (frozen excluded) and cap bonus at +6%
        if len(signals[decision]) == actual_voting_count and actual_voting_count >= 5:
            confidence = min(95, confidence + 6)
            log.info(f"[BANK-GRADE] 🎯 PERFECT AGREEMENT! All {actual_voting_count} voting LLMs voted {decision} (+6%)")
        
        # 🏦 BANK-GRADE LOGGING: Show mathematical analysis
        log.info(f"[BANK-GRADE] 📊 ANALYSIS: Bayesian P(BUY)={posterior_buy:.3f} P(SELL)={posterior_sell:.3f} P(HOLD)={posterior_hold:.3f}")
        log.info(f"[BANK-GRADE] 📈 ENTROPY: {current_entropy:.3f}/{max_entropy:.3f} = {entropy_penalty:.1%} disagreement | Agreement bonus: {agreement_bonus:.1%}")
        log.info(f"[BANK-GRADE] 🎲 SCORES: BUY={buy_pct:.1f}% SELL={sell_pct:.1f}% HOLD={hold_pct:.1f}%")
        log.info(f"[BANK-GRADE] 🏦 DECISION: {decision} @ {confidence}% confidence | Divergence: {divergence:.2%}")
        
        # Ensure buy/sell scores are properly scaled
        buy_score_final = min(100, max(0, buy_pct))
        sell_score_final = min(100, max(0, sell_pct))
        
        return decision, confidence, buy_score_final, sell_score_final
    
    def _fallback_decision(self, genome: dict) -> tuple:
        rsi, macd, adx = genome.get('rsi', 50), genome.get('macd', 0), genome.get('adx', 25)
        if rsi > 70 or macd < 0:
            return 'SELL', 60
        elif rsi < 30 or macd > 0:
            return 'BUY', 60
        else:
            return 'HOLD', 40
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🧠 STRUCTURE POSITION INTELLIGENCE (SPI) v1.0 — 2026-02-19
    # ═══════════════════════════════════════════════════════════════════════════════
    # Answers the question: "WHERE is price in the macro structure?"
    # - At a swing HIGH → don't BUY, wait for pullback
    # - At a swing LOW → don't SELL, wait for bounce
    # - In PULLBACK ZONE (Fib 38.2-61.8%) → OPTIMAL entry WITH trend
    # - Exhaustion beyond last swing → possible REVERSAL
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _structure_position_intelligence(self, genome: dict, decision: str, confidence: int) -> tuple:
        """
        🧠 SPI: Analyzes macro structure to filter decisions
        
        Returns: (adjusted_decision, adjusted_confidence, spi_context)
        
        Philosophy: "The trend is UP, but we're at the TOP.
        Wait for it to pull back to the optimal zone, THEN enter."
        """
        try:
            # ═══ EXTRACT OHLCV DATA ═══
            bar_data = genome.get('bar_data', {})
            closes = [float(c) for c in bar_data.get('closes', []) if c]
            highs = [float(h) for h in bar_data.get('highs', []) if h]
            lows = [float(l) for l in bar_data.get('lows', []) if l]
            
            price = float(genome.get('price_data', {}).get('close', 0) or 0)
            if price <= 0 and closes:
                price = closes[-1]
            
            if len(closes) < 20 or price <= 0:
                return decision, confidence, {'spi_active': False, 'reason': 'Insufficient data'}
            
            # ═══ STEP 1: PROPER SWING POINT DETECTION (N-bar pivot) ═══
            # Use 3-bar pivots for M1 (each pivot confirmed by 3 bars on each side)
            pivot_n = 3
            swing_highs = []  # [(index, price)]
            swing_lows = []   # [(index, price)]
            
            for i in range(pivot_n, len(highs) - pivot_n):
                is_pivot_high = True
                is_pivot_low = True
                for j in range(1, pivot_n + 1):
                    if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                        is_pivot_high = False
                    if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                        is_pivot_low = False
                if is_pivot_high:
                    swing_highs.append((i, highs[i]))
                if is_pivot_low:
                    swing_lows.append((i, lows[i]))
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return decision, confidence, {'spi_active': False, 'reason': f'Not enough swings: SH={len(swing_highs)}, SL={len(swing_lows)}'}
            
            # ═══ STEP 2: MACRO TREND IDENTIFICATION ═══
            sh_prev, sh_last = swing_highs[-2], swing_highs[-1]
            sl_prev, sl_last = swing_lows[-2], swing_lows[-1]
            
            hh = sh_last[1] > sh_prev[1]  # Higher High
            hl = sl_last[1] > sl_prev[1]  # Higher Low
            lh = sh_last[1] < sh_prev[1]  # Lower High
            ll = sl_last[1] < sl_prev[1]  # Lower Low
            
            if hh and hl:
                macro_trend = 'UPTREND'
            elif lh and ll:
                macro_trend = 'DOWNTREND'
            elif hh and ll:
                macro_trend = 'EXPANDING'  # Volatility expansion
            elif lh and hl:
                macro_trend = 'CONTRACTING'  # Squeeze/consolidation
            else:
                macro_trend = 'MIXED'
            
            # ═══ STEP 3: FIBONACCI RETRACEMENT ZONES ═══
            # Calculate FROM the last completed move (last swing low → last swing high for uptrend)
            if macro_trend == 'UPTREND':
                # Last move: from swing_low to swing_high
                move_start = sl_last[1]   # last Higher Low
                move_end = sh_last[1]     # last Higher High
            elif macro_trend == 'DOWNTREND':
                # Last move: from swing_high to swing_low
                move_start = sh_last[1]   # last Lower High
                move_end = sl_last[1]     # last Lower Low
            else:
                # For EXPANDING/CONTRACTING/MIXED, use the most recent range
                move_start = min(sl_last[1], sl_prev[1])
                move_end = max(sh_last[1], sh_prev[1])
            
            move_range = abs(move_end - move_start)
            if move_range < 0.01:  # Prevent division by zero
                return decision, confidence, {'spi_active': False, 'reason': 'Move too small'}
            
            # Fib levels for retracement
            if macro_trend == 'UPTREND':
                fib_0 = move_end      # Top of move (0% retracement)
                fib_236 = move_end - move_range * 0.236
                fib_382 = move_end - move_range * 0.382
                fib_500 = move_end - move_range * 0.500
                fib_618 = move_end - move_range * 0.618
                fib_786 = move_end - move_range * 0.786
                fib_100 = move_start  # Bottom of move (100% retracement)
            elif macro_trend == 'DOWNTREND':
                fib_0 = move_end      # Bottom of move (0% retracement)
                fib_236 = move_end + move_range * 0.236
                fib_382 = move_end + move_range * 0.382
                fib_500 = move_end + move_range * 0.500
                fib_618 = move_end + move_range * 0.618
                fib_786 = move_end + move_range * 0.786
                fib_100 = move_start  # Top of move (100% retracement)
            else:
                fib_0 = move_end
                fib_382 = (move_start + move_end) / 2 - move_range * 0.118
                fib_500 = (move_start + move_end) / 2
                fib_618 = (move_start + move_end) / 2 + move_range * 0.118
                fib_236 = fib_382
                fib_786 = fib_618
                fib_100 = move_start
            
            # ═══ STEP 4: WHERE IS PRICE IN THE STRUCTURE? ═══
            # Calculate price position as % of the last move
            if macro_trend == 'UPTREND':
                price_position_pct = ((price - move_start) / move_range) * 100  # 100% = at top (HH), 0% = at bottom (HL)
            elif macro_trend == 'DOWNTREND':
                price_position_pct = ((move_start - price) / move_range) * 100  # 100% = at bottom (LL), 0% = at top (LH)
            else:
                price_position_pct = ((price - min(move_start, move_end)) / move_range) * 100
            
            # Distance from key levels
            dist_to_last_high = abs(price - sh_last[1])
            dist_to_last_low = abs(price - sl_last[1])
            near_high = dist_to_last_high < move_range * 0.10  # Within 10% of last swing high
            near_low = dist_to_last_low < move_range * 0.10    # Within 10% of last swing low
            
            # Is price in the optimal pullback zone (Fib 38.2% - 61.8%)?
            if macro_trend == 'UPTREND':
                in_pullback_zone = fib_618 <= price <= fib_382  # Price pulled back to golden zone
                in_extension_zone = price > sh_last[1]  # Price above last swing high = extension
                in_breakdown_zone = price < sl_last[1]  # Price below last swing low = structure broken
            elif macro_trend == 'DOWNTREND':
                in_pullback_zone = fib_382 <= price <= fib_618  # Price bounced to golden zone
                in_extension_zone = price < sl_last[1]  # Price below last swing low = extension
                in_breakdown_zone = price > sh_last[1]  # Price above last swing high = structure broken
            else:
                in_pullback_zone = False
                in_extension_zone = False
                in_breakdown_zone = False
            
            # ═══ STEP 5: APPLY STRUCTURAL WISDOM ═══
            spi_adjustment = 0  # Confidence adjustment
            spi_override = None  # If not None, overrides decision
            spi_reason = []
            
            # 🧠 ADX-AWARE: Strong trend changes how we interpret position
            _spi_indicators = genome.get('indicators', {}).get('current', {})
            if not _spi_indicators:
                _spi_indicators = genome.get('indicators', {})
            _spi_adx = float(_spi_indicators.get('adx', {}).get('value', 25) if isinstance(_spi_indicators.get('adx'), dict) else _spi_indicators.get('adx', 25))
            _strong_trend = _spi_adx >= 40  # ADX 40+ = strong directional trend
            _extreme_trend = _spi_adx >= 55  # ADX 55+ = extreme momentum
            
            if macro_trend == 'UPTREND':
                if decision == 'BUY':
                    if near_high or price_position_pct > 90:
                        if _extreme_trend and in_extension_zone:
                            # 🔥 MOMENTUM BREAKOUT — ADX 55+ means this is a real breakout, not chasing
                            spi_adjustment = +5
                            spi_reason.append(f"🔥 MOMENTUM BUY: ADX={_spi_adx:.0f} + extension = breakout continuation (pos={price_position_pct:.0f}%)")
                        elif _strong_trend and in_extension_zone:
                            # 📈 TREND CONTINUATION — ADX 40+ with extension, mild caution only
                            spi_adjustment = -8
                            spi_reason.append(f"📈 Trend continuation BUY: ADX={_spi_adx:.0f} (pos={price_position_pct:.0f}%) — mild caution")
                        else:
                            # ⚠️ BUYING AT THE TOP without trend support
                            spi_adjustment = -20
                            spi_reason.append(f"⚠️ BUY at HH zone (pos={price_position_pct:.0f}%) — wait for pullback")
                        if price_position_pct > 120 and not _extreme_trend:
                            spi_override = 'HOLD'
                            spi_reason.append(f"🚫 BLOCKED: Price at {price_position_pct:.0f}% — overextended without ADX support")
                    elif in_pullback_zone:
                        # ✅ PERFECT ENTRY — buying the pullback in an uptrend
                        spi_adjustment = +15
                        spi_reason.append(f"✅ OPTIMAL BUY: Pullback to Fib zone (pos={price_position_pct:.0f}%)")
                    elif price_position_pct > 75:
                        # ⚠️ Late entry — milder penalty if trend is strong
                        spi_adjustment = -5 if _strong_trend else -12
                        spi_reason.append(f"⚠️ Late BUY: Near top (pos={price_position_pct:.0f}%) ADX={_spi_adx:.0f}")
                    elif price_position_pct < 30:
                        # Price deep in retracement — might be breaking structure
                        spi_adjustment = -10
                        spi_reason.append(f"⚠️ Deep retracement (pos={price_position_pct:.0f}%) — trend might be failing")
                    else:
                        spi_adjustment = +5
                        spi_reason.append(f"✅ BUY in trend midrange (pos={price_position_pct:.0f}%)")
                
                elif decision == 'SELL':
                    if near_high or price_position_pct > 85:
                        # ✅ SELLING at the top of an uptrend — counter-trend but good location
                        spi_adjustment = +10
                        spi_reason.append(f"✅ SELL near HH (pos={price_position_pct:.0f}%) — reversal potential")
                    elif near_low or price_position_pct < 15:
                        # 🚫 SELLING AT THE BOTTOM of uptrend — worst possible
                        spi_adjustment = -25
                        spi_override = 'HOLD'
                        spi_reason.append(f"🚫 BLOCKED: SELL at HL zone (pos={price_position_pct:.0f}%) — counter-trend at worst level")
                    else:
                        # Counter-trend sell in middle — risky
                        spi_adjustment = -10
                        spi_reason.append(f"⚠️ Counter-trend SELL (pos={price_position_pct:.0f}%) — against uptrend")
            
            elif macro_trend == 'DOWNTREND':
                if decision == 'SELL':
                    if near_low or price_position_pct > 90:
                        if _extreme_trend and in_extension_zone:
                            # 🔥 MOMENTUM BREAKDOWN — ADX 55+ means real breakdown
                            spi_adjustment = +5
                            spi_reason.append(f"🔥 MOMENTUM SELL: ADX={_spi_adx:.0f} + extension = breakdown continuation (pos={price_position_pct:.0f}%)")
                        elif _strong_trend and in_extension_zone:
                            # 📉 TREND CONTINUATION — ADX 40+ with extension
                            spi_adjustment = -8
                            spi_reason.append(f"📉 Trend continuation SELL: ADX={_spi_adx:.0f} (pos={price_position_pct:.0f}%) — mild caution")
                        else:
                            # ⚠️ SELLING AT THE BOTTOM without trend support
                            spi_adjustment = -20
                            spi_reason.append(f"⚠️ SELL at LL zone (pos={price_position_pct:.0f}%) — wait for bounce")
                        if price_position_pct > 120 and not _extreme_trend:
                            spi_override = 'HOLD'
                            spi_reason.append(f"🚫 BLOCKED: Price at {price_position_pct:.0f}% — overextended without ADX support")
                    elif in_pullback_zone:
                        # ✅ PERFECT ENTRY — selling the bounce in a downtrend
                        spi_adjustment = +15
                        spi_reason.append(f"✅ OPTIMAL SELL: Bounce to Fib zone (pos={price_position_pct:.0f}%)")
                    elif price_position_pct > 75:
                        spi_adjustment = -5 if _strong_trend else -12
                        spi_reason.append(f"⚠️ Late SELL: Near bottom (pos={price_position_pct:.0f}%) ADX={_spi_adx:.0f}")
                    elif price_position_pct < 30:
                        spi_adjustment = -10
                        spi_reason.append(f"⚠️ Deep bounce (pos={price_position_pct:.0f}%) — trend might be failing")
                    else:
                        spi_adjustment = +5
                        spi_reason.append(f"✅ SELL in trend midrange (pos={price_position_pct:.0f}%)")
                
                elif decision == 'BUY':
                    if near_low or price_position_pct > 85:
                        # Counter-trend BUY at bottom — reversal play
                        spi_adjustment = +10
                        spi_reason.append(f"✅ BUY near LL (pos={price_position_pct:.0f}%) — reversal potential")
                    elif near_high or price_position_pct < 15:
                        # 🚫 BUYING AT THE TOP of a downtrend
                        spi_adjustment = -25
                        spi_override = 'HOLD'
                        spi_reason.append(f"🚫 BLOCKED: BUY at LH zone (pos={price_position_pct:.0f}%) — counter-trend at worst level")
                    else:
                        spi_adjustment = -10
                        spi_reason.append(f"⚠️ Counter-trend BUY (pos={price_position_pct:.0f}%) — against downtrend")
            
            else:
                # EXPANDING / CONTRACTING / MIXED — be extra cautious
                if near_high and decision == 'BUY':
                    spi_adjustment = -15
                    spi_reason.append(f"⚠️ BUY near range top in {macro_trend}")
                elif near_low and decision == 'SELL':
                    spi_adjustment = -15
                    spi_reason.append(f"⚠️ SELL near range bottom in {macro_trend}")
            
            # ═══ STEP 6: BREAK OF STRUCTURE (BOS) DETECTION ═══
            if in_breakdown_zone:
                if macro_trend == 'UPTREND' and decision == 'SELL':
                    spi_adjustment = +20  # Structure broken DOWN — SELL is smart
                    spi_reason.append(f"🔥 BOS: Uptrend structure BROKEN — price below last HL")
                elif macro_trend == 'DOWNTREND' and decision == 'BUY':
                    spi_adjustment = +20  # Structure broken UP — BUY is smart
                    spi_reason.append(f"🔥 BOS: Downtrend structure BROKEN — price above last LH")
            
            if in_extension_zone:
                if macro_trend == 'UPTREND' and decision == 'BUY':
                    if _extreme_trend:
                        spi_reason.append(f"🔥 Extension OK: ADX={_spi_adx:.0f} confirms momentum breakout")
                    elif _strong_trend:
                        spi_adjustment -= 3  # Mild caution with strong ADX
                        spi_reason.append(f"📈 Extension mild caution: ADX={_spi_adx:.0f} supports but not extreme")
                    else:
                        spi_adjustment -= 10  # Chasing without ADX support
                        spi_reason.append(f"⚠️ Extension: Price beyond last HH — chasing breakout (ADX={_spi_adx:.0f})")
                elif macro_trend == 'DOWNTREND' and decision == 'SELL':
                    if _extreme_trend:
                        spi_reason.append(f"🔥 Extension OK: ADX={_spi_adx:.0f} confirms momentum breakdown")
                    elif _strong_trend:
                        spi_adjustment -= 3
                        spi_reason.append(f"📉 Extension mild caution: ADX={_spi_adx:.0f} supports but not extreme")
                    else:
                        spi_adjustment -= 10
                        spi_reason.append(f"⚠️ Extension: Price beyond last LL — chasing breakdown (ADX={_spi_adx:.0f})")
            
            # ═══ STEP 7: APPLY ADJUSTMENTS ═══
            adjusted_confidence = max(15, min(95, confidence + spi_adjustment))
            adjusted_decision = spi_override if spi_override else decision
            
            if adjusted_decision != decision or spi_adjustment != 0:
                log.info(f"[SPI] 🧠 STRUCTURE POSITION INTELLIGENCE:")
                log.info(f"[SPI]   Macro trend: {macro_trend} | Swings: SH={len(swing_highs)} SL={len(swing_lows)}")
                log.info(f"[SPI]   Last move: {move_start:.2f} → {move_end:.2f} (${move_range:.2f})")
                log.info(f"[SPI]   Price position: {price_position_pct:.0f}% | Fib zone: {fib_382:.2f}-{fib_618:.2f}")
                log.info(f"[SPI]   Near high: {near_high} | Near low: {near_low} | Pullback zone: {in_pullback_zone}")
                for r in spi_reason:
                    log.info(f"[SPI]   {r}")
                log.info(f"[SPI]   Decision: {decision}→{adjusted_decision} | Confidence: {confidence}→{adjusted_confidence} (adj={spi_adjustment:+d})")
            
            spi_context = {
                'spi_active': True,
                'macro_trend': macro_trend,
                'price_position_pct': round(price_position_pct, 1),
                'move_start': move_start,
                'move_end': move_end,
                'move_range': move_range,
                'fib_382': fib_382,
                'fib_500': fib_500,
                'fib_618': fib_618,
                'in_pullback_zone': in_pullback_zone,
                'in_extension_zone': in_extension_zone,
                'in_breakdown_zone': in_breakdown_zone,
                'near_high': near_high,
                'near_low': near_low,
                'swing_highs_count': len(swing_highs),
                'swing_lows_count': len(swing_lows),
                'last_swing_high': sh_last[1],
                'last_swing_low': sl_last[1],
                'adjustment': spi_adjustment,
                'reasons': spi_reason
            }
            
            return adjusted_decision, adjusted_confidence, spi_context
        
        except Exception as e:
            log.warning(f"[SPI] Error in structure analysis: {e}")
            return decision, confidence, {'spi_active': False, 'reason': f'Error: {e}'}
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 LLM10 NOVA INTEGRATION: Query NOVA for audit & emergency halt
    # ═══════════════════════════════════════════════════════════════════
    
    def _query_llm10_nova(self, genome: dict, trinity_decision: dict, llm_votes: dict = None) -> dict:
        """
        🚀 QUERY LLM10 NOVA via TCP — FULL 10-BRAIN CONTEXT
        NOVA recibe: decisión de Trinidad + votos individuales de los 10 LLMs
        + contexto de mercado completo (OHLC, sesión, volatilidad, MA cascade).
        Sin esto NOVA es un auditor ciego que sólo ve el veredicto final.
        """

        try:
            # 1️⃣ ARMAR CONTEXTO COMPLETO para LLM10
            bid = genome.get('bid') or genome.get('price_data', {}).get('bid') or genome.get('bar_data', {}).get('current', {}).get('bid', 0)
            ask = genome.get('ask') or genome.get('price_data', {}).get('ask') or genome.get('bar_data', {}).get('current', {}).get('ask', 0)

            price_data = genome.get('price_data', {}).copy() if genome.get('price_data') else {}
            price_data['bid'] = bid
            price_data['ask'] = ask

            # 🧠 INDIVIDUAL LLM VOTES — el corazón de los 10 cerebros
            # Sanitize: keep only serializable summary (decision, confidence, reason)
            def _safe_vote(v):
                if not isinstance(v, dict):
                    return {'decision': str(v), 'confidence': 0, 'reason': 'raw'}
                return {
                    'decision'  : v.get('decision', 'HOLD'),
                    'confidence': v.get('confidence', 0),
                    'reason'    : str(v.get('reason', ''))[:200],
                }

            individual_votes = {}
            if llm_votes:
                for name, resp in llm_votes.items():
                    individual_votes[name] = _safe_vote(resp)

            # Vote summary counts for quick audit
            vote_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            for v in individual_votes.values():
                vote_counts[v.get('decision', 'HOLD')] = vote_counts.get(v.get('decision', 'HOLD'), 0) + 1

            # 📊 MARKET CONTEXT — datos técnicos para que NOVA razone sobre el gráfico
            bar_current = genome.get('bar_data', {}).get('current', {})
            closes_raw   = genome.get('bar_data', {}).get('closes', [])
            highs_raw    = genome.get('bar_data', {}).get('highs', [])
            lows_raw     = genome.get('bar_data', {}).get('lows', [])

            # Compute MA5/MA20 on-the-fly so NOVA can see trend direction
            ma_context = {}
            if len(closes_raw) >= 20:
                ma5  = sum(closes_raw[-5:])  / 5
                ma20 = sum(closes_raw[-20:]) / 20
                price_now = closes_raw[-1]
                ma_context = {
                    'ma5'         : round(ma5,  5),
                    'ma20'        : round(ma20, 5),
                    'price_vs_ma5': 'ABOVE' if price_now > ma5  else 'BELOW',
                    'price_vs_ma20': 'ABOVE' if price_now > ma20 else 'BELOW',
                    'ma5_vs_ma20' : 'ABOVE' if ma5 > ma20 else 'BELOW',
                    'trend_signal': 'BULLISH' if price_now > ma5 > ma20 else ('BEARISH' if price_now < ma5 < ma20 else 'MIXED'),
                }

            audit_context = {
                # ── TRINITY SUMMARY ──
                'trinity_decision'  : trinity_decision.get('consensus_decision'),
                'trinity_confidence': trinity_decision.get('consensus_confidence'),
                'trinity_alignment' : trinity_decision.get('alignment_score'),
                'trinity_reasoning' : trinity_decision.get('reason'),

                # ── 10 LLM INDIVIDUAL VOTES ── (núcleo del audit)
                'llm_votes'         : individual_votes,
                'vote_counts'       : vote_counts,          # {BUY:3, SELL:1, HOLD:2}
                'llm_count'         : len(individual_votes),

                # ── PRECIO Y OHLC ──
                'price_data'        : price_data,
                'bar_current'       : bar_current,          # open/high/low/close/volume actual
                'candle_direction'  : ('BULL' if bar_current.get('close', 0) >= bar_current.get('open', 0) else 'BEAR') if bar_current else 'UNKNOWN',

                # ── INDICADORES ──
                'indicators'        : genome.get('indicators', {}),
                'ma_context'        : ma_context,           # MA5/MA20 trend bias

                # ── CONTEXTO DE SESIÓN ──
                'session'           : genome.get('session', genome.get('metadata', {}).get('session', 'UNKNOWN')),
                'volatility_regime' : genome.get('volatility_regime', 'NORMAL'),
                'flash_crash'       : genome.get('flash_crash_detected', False),
                'whale_detected'    : genome.get('whale_detected', False),

                # ── VALIDACIÓN ──
                'ecosystem_validation': genome.get('_ecosystem_validation', {}),
                'spi_context'         : genome.get('_spi_context', {}),

                # ── METADATA ──
                'symbol'            : genome.get('metadata', {}).get('symbol') or genome.get('symbol'),
                'timestamp'         : genome.get('metadata', {}).get('timestamp'),
            }
            
            # 2️⃣ VALIDACIÓN PRE-ENVÍO
            pre_flight = self._validate_audit_context(audit_context)
            if not pre_flight['valid']:
                log.warning(f"[NOVA PRE-FLIGHT] ❌ {pre_flight['reason']}")
                return {
                    'is_valid': False,
                    'quality_multiplier': 0.0,
                    'audit_score': 0,
                    'alerts': [pre_flight['reason']],
                    'reasoning': 'Pre-flight validation failed',
                    'emergency_halt': True
                }
            
            # 3️⃣ CONECTAR CON LLM10 VIA TCP (mismo protocolo que LLM1-9)
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)  # Same timeout as other LLMs (1.5s)
            sock.connect((self.host, 5565))
            
            # Send: 4-byte big-endian header + JSON
            request_json = json.dumps(audit_context).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            
            # Receive: 4-byte big-endian header + JSON
            response_header = b''
            while len(response_header) < 4:
                chunk = sock.recv(4 - len(response_header))
                if not chunk:
                    raise socket.error("Connection closed reading header")
                response_header += chunk
            
            response_length = struct.unpack('>I', response_header)[0]
            if response_length > 10_000_000:
                raise ValueError(f"Response too large: {response_length}")
            
            response_data = b''
            while len(response_data) < response_length:
                chunk = sock.recv(min(4096, response_length - len(response_data)))
                if not chunk:
                    break
                response_data += chunk
            
            sock.close()
            
            latency_ms = (time.time() - start_time) * 1000
            
            if latency_ms > 500:
                log.warning(f"[NOVA LATENCY] ⚠️ LLM10 slow: {latency_ms:.0f}ms")
            
            nova_response = json.loads(response_data.decode('utf-8'))
            
            # 4️⃣ VALIDACIÓN POST-RECEPCIÓN
            post_flight = self._validate_nova_response(nova_response)
            if not post_flight['valid']:
                log.warning(f"[NOVA POST-FLIGHT] ❌ {post_flight['reason']}")
                return self._fallback_nova_response()
            
            log.info(f"[NOVA AUDIT] ✅ Score: {nova_response.get('audit_score')}, "
                    f"Multiplier: {nova_response.get('quality_multiplier')}, "
                    f"Latency: {latency_ms:.0f}ms")
            
            return nova_response
        
        except socket.timeout:
            log.warning(f"[NOVA TIMEOUT] LLM10 no respondió en {self.timeout}s")
            return self._fallback_nova_response()
        
        except ConnectionRefusedError:
            log.error(f"[NOVA CONNECTION] ❌ LLM10 not running on port 5565")
            return self._fallback_nova_response()
        
        except Exception as e:
            log.error(f"[NOVA ERROR] {str(e)}")
            return self._fallback_nova_response()
    
    def _validate_audit_context(self, context: dict) -> dict:
        """VALIDACIÓN PRE-ENVÍO: Audita que datos enviados a LLM10 son válidos"""
        
        errors = []
        
        # ✅ Validar estructura mínima
        if not context.get('price_data'):
            errors.append("price_data missing")

        # ⚠️ Note: indicators can be empty/missing when genome has no current indicators yet
        # Do NOT block here — RSI/ADX will default to safe values below
        if not context.get('indicators'):
            log.debug("[NOVA VALIDATE] indicators empty — using defaults (not blocking)")
        
        # ✅ Validar rangos (Hueco #5)
        indicators = context.get('indicators', {}).get('current', {})
        
        rsi = indicators.get('rsi', 50)
        if not (0 <= rsi <= 100):
            errors.append(f"RSI {rsi} outside [0,100]")
        
        adx = indicators.get('adx', 20)
        if not (0 <= adx <= 100):
            errors.append(f"ADX {adx} outside [0,100]")
        
        # FIX: Try multiple locations for bid/ask (price_data has priority, but fallback to root context)
        bid = context.get('price_data', {}).get('bid', 0)
        ask = context.get('price_data', {}).get('ask', 0)
        
        # Log for debugging if bid/ask are zero
        if bid == 0 or ask == 0:
            log.debug(f"[NOVA VALIDATE] bid={bid} ask={ask} from price_data, checking available keys...")
            log.debug(f"[NOVA VALIDATE] price_data keys: {list(context.get('price_data', {}).keys())}")
        
        # ✅ Validar sanity (Hueco #10) - Only if we have valid prices
        if bid > 0 and ask > 0:
            if bid >= ask:
                errors.append(f"Price corrupted: bid {bid} >= ask {ask}")
        else:
            # Skip price validation if we don't have valid bid/ask - allow system to continue
            log.warning(f"[NOVA VALIDATE] ⚠️ Skipping bid/ask validation (bid={bid}, ask={ask}) - data may not include tick prices")
        
        # ✅ Validar timestamp (Hueco #6)
        timestamp = context.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    ts_obj = datetime.fromisoformat(timestamp)
                else:
                    ts_obj = datetime.fromtimestamp(timestamp)
                
                age = datetime.now() - ts_obj
                if age.total_seconds() > 30:
                    errors.append(f"Data is {age.total_seconds():.0f}s old (stale)")
            except:
                pass  # Si timestamp no es parseable, ignorar
        
        return {
            'valid': len(errors) == 0,
            'reason': ' | '.join(errors) if errors else 'All checks passed'
        }
    
    def _validate_nova_response(self, response: dict) -> dict:
        """VALIDACIÓN POST-RECEPCIÓN: Audita que respuesta de LLM10 es válida"""
        
        errors = []
        
        # ✅ Validar estructura
        if 'quality_multiplier' not in response:
            errors.append("quality_multiplier missing")
        
        if 'audit_score' not in response:
            errors.append("audit_score missing")
        
        # ✅ Validar rangos
        multiplier = response.get('quality_multiplier', 0.5)
        if not (0.0 <= multiplier <= 1.5):
            errors.append(f"Multiplier {multiplier} outside [0.0, 1.5]")
        
        score = response.get('audit_score', 50)
        if not (0 <= score <= 100):
            errors.append(f"Score {score} outside [0, 100]")
        
        # ✅ Validar lógica
        if response.get('emergency_halt') and multiplier > 0.5:
            errors.append("Contradiction: emergency_halt=True but multiplier>0.5")
        
        return {
            'valid': len(errors) == 0,
            'reason': ' | '.join(errors) if errors else 'Response valid'
        }
    
    def _fallback_nova_response(self) -> dict:
        """FALLBACK: Si LLM10 falla — NEUTRAL, no penalizar.
        NOVA offline NO debe matar la confianza de Trinity.
        multiplier=0.7 cortaba 30% de cada señal válida cada tick sin NOVA UP.
        """
        return {
            'is_valid': True,
            'quality_multiplier': 1.0,  # NEUTRAL — NOVA offline no penaliza
            'audit_score': 70,
            'alerts': ['LLM10 NOVA unavailable, using fallback (neutral)'],
            'reasoning': 'LLM10 connection failed — neutral pass-through',
            'emergency_halt': False
        }

# ⭐ TCP SERVER - Trinity accepts genomes from quantum_core on port 6666
class TrinityServer:
    """Trinity TCP Server with optional Dashboard integration"""
    
    def __init__(self, dashboard_enabled=True):
        self.trinity = TrinityConsensus()
        self.dashboard = None
        self.running = True
        self.lock = threading.RLock()
        self.metrics = {
            'ticks_processed': 0,
            'start_time': time.time(),
        }
        
        log.info('[SERVER] Initialization started')
        
        # Try to load dashboard if enabled
        if dashboard_enabled:
            try:
                log.info('[SERVER] Loading dashboard...')
                from trinity_dashboard_v3 import QuantumDashboard
                self.dashboard = QuantumDashboard(port=6667)
                self.dashboard.start_listener()
                log.info('[SERVER] ✅ Dashboard loaded and listening')
            except Exception as e:
                log.warning(f'[SERVER] ⚠️  Dashboard not available: {e}')
                self.dashboard = None
        
        log.info('[SERVER] Initialization complete')
    
    def run(self, port=6666):
        """Start TCP server on specified port"""
        log.info(f"[SERVER] Starting TCP server on port {port}...")
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', port))
            server.listen(5)
            log.info(f'[SERVER] Listening on 127.0.0.1:{port} - READY FOR CONNECTIONS')
        except Exception as e:
            log.error(f'[SERVER] Failed to bind: {e}', exc_info=True)
            return
        
        # Status thread
        threading.Thread(target=self._print_status, daemon=True).start()
        
        log.info("[SERVER] Entering accept loop...")
        while self.running:
            try:
                client, addr = server.accept()
                log.info(f'[SERVER] Connection from {addr}')
                threading.Thread(
                    target=self._handle_client, 
                    args=(client, addr), 
                    daemon=True
                ).start()
            except Exception as e:
                log.error(f'[SERVER] Accept error: {e}', exc_info=True)
    
    def _handle_client(self, client, addr):
        """Handle genome from quantum_core (or heartbeat PING)"""
        try:
            client.settimeout(5)
            
            # Read header (4 bytes)
            header = client.recv(4)
            if not header or len(header) != 4:
                log.warning(f'[CLIENT {addr}] Invalid header')
                client.close()
                return
            
            length = struct.unpack('>I', header)[0]
            
            # Read payload
            data = b''
            while len(data) < length:
                chunk = client.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk
            
            if not data:
                log.warning(f'[CLIENT {addr}] No data')
                client.close()
                return
            
            # HEARTBEAT: Respond to PING with ACK (quantum_core NetworkHeartbeat)
            if data == b'PING':
                ack_header = struct.pack('>I', 3)
                client.sendall(ack_header + b'ACK')
                client.close()
                return
            
            # Parse and analyze
            genome = json.loads(data.decode('utf-8'))
            result = self.trinity.analyze(genome)
            log.info(f'[CLIENT {addr}] Result: {result["decision"]} @ {result["confidence"]}%')
            
            # Update dashboard if available
            if self.dashboard:
                try:
                    llm_responses = result.get('llm_responses', {})
                    LLM_MAP = {'BAYESIAN': 'LLM1', 'TECHNICAL': 'LLM2', 'CHART': 'LLM3', 'RISK': 'LLM4', 'SUPREME': 'LLM5'}
                    
                    for llm_name, llm_data in llm_responses.items():
                        if isinstance(llm_data, dict):
                            dashboard_name = LLM_MAP.get(llm_name, llm_name)
                            self.dashboard.update_llm(
                                dashboard_name,
                                llm_data.get('decision', 'HOLD'),
                                llm_data.get('confidence', 0),
                                llm_data.get('reason', '')[:40]
                            )
                    
                    # Update trinity consensus
                    scores = result.get('scores', {})
                    self.dashboard.update_trinity(
                        result.get('decision', 'HOLD'),
                        result.get('confidence', 0),
                        scores.get('buy_score', 0),
                        scores.get('sell_score', 0),
                        scores.get('hold_score', 0)
                    )
                except Exception as e:
                    log.debug(f'[CLIENT {addr}] Dashboard update error: {e}')
            
            with self.lock:
                self.metrics['ticks_processed'] += 1
            
            # Send response
            response = json.dumps(result).encode('utf-8')
            response_header = struct.pack('>I', len(response))
            client.sendall(response_header + response)
            
        except Exception as e:
            log.error(f'[CLIENT {addr}] Error: {e}')
        finally:
            try:
                client.close()
            except:
                pass
    
    def _print_status(self):
        """Print status every 30 seconds"""
        while self.running:
            try:
                time.sleep(30)
                with self.lock:
                    uptime = time.time() - self.metrics['start_time']
                    log.info(f"[STATUS] Uptime: {uptime/60:.1f}min | Ticks: {self.metrics['ticks_processed']}")
            except Exception as e:
                log.error(f"[STATUS] Error: {e}")

def run_server(port=6666):
    """Run Trinity consensus server with optional dashboard"""
    server = TrinityServer(dashboard_enabled=True)
    server.run(port=port)

if __name__ == '__main__':
    try:
        log.info('[TRINITY] ═════════════════════════════════════════')
        log.info('[TRINITY] TRINITY CONSENSUS ENGINE v1.0')
        log.info('[TRINITY] Consensus Orchestrator - 5 LLM Integration')
        log.info('[TRINITY] ═════════════════════════════════════════')
        run_server(port=6666)
    except KeyboardInterrupt:
        log.info('[TRINITY] 🛑 Stopped by user')
    except Exception as e:
        log.error(f'[TRINITY] FATAL: {e}', exc_info=True)
