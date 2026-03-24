#!/usr/bin/env python3
"""
+------------------------------------------------------------------------------+
�                    ?? NOVA TRADING AI - TRINITY ORACLE                       �
�                       by Polarice Labs � 2026                                �
�------------------------------------------------------------------------------�
�  Bank-Grade LLM Consensus System with 5-LLM Voting                           �
�  Bayesian + Entropy + Divergence Weighting                                   �
�  Dynamic Performance Tracking & Adaptive Weights                             �
+------------------------------------------------------------------------------+
"""
import socket, json, threading, logging, time, struct, statistics, math, requests
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

# ---------------------------------------------------------------------------------------
# ?? LLM PERFORMANCE TRACKER - Tracks accuracy of each LLM to adjust weights dynamically
# ---------------------------------------------------------------------------------------
class LLMPerformanceTracker:
    """
    Tracks historical performance of each LLM to dynamically adjust voting weights.
    Uses exponential moving average for recent performance emphasis.
    """
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.llm_history = {
            'BAYESIAN': deque(maxlen=window_size),
            'TECHNICAL': deque(maxlen=window_size),
            'CHART': deque(maxlen=window_size),
            'RISK': deque(maxlen=window_size),
            'SUPREME': deque(maxlen=window_size),
            'SMART_MONEY': deque(maxlen=window_size)  # LLM6 tracking
        }
        # Momentum tracking - consecutive same-direction signals
        self.llm_momentum = {name: {'direction': None, 'count': 0} for name in self.llm_history}
        # Consistency tracking - how often LLM changes opinion
        self.llm_consistency = {name: deque(maxlen=20) for name in self.llm_history}
        # Base weights (can be updated based on performance)
        self.base_weights = {
            'BAYESIAN': 1.2,    # Probabilistic reasoning
            'TECHNICAL': 1.0,   # Classic indicators
            'CHART': 1.1,       # Pattern recognition
            'RISK': 0.9,        # Conservative
            'SUPREME': 1.3,     # Deep learning ensemble
            'SMART_MONEY': 1.4,  # LLM6 Smart Money Oracle - highest weight for institutional flow
            'STRATEGIST': 2.0,     # LLM11 - Guru consciousness: strategy + conviction
            'SENTINEL': 1.8        # LLM12 - Quality guardian: execution + reflection
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

class TrinityConsensus:
    def __init__(self):
        log.info('[TRINITY] BANK-GRADE CONSENSUS v3.0 Initialized - GBPUSD')
        log.info('[TRINITY] Features: Bayesian + Entropy + LLM6/7/8/9/10 Integration')
        self.host = '127.0.0.1'
        self.timeout = 5.0  # Increased from 2.0 to allow LLMs more time to respond
        
        # PHASE 1: Core voting LLMs (decide BUY/SELL/HOLD) - GBPUSD PORTS (75xx)
        self.core_llm_ports = {
            'BAYESIAN': 7555,     # GBPUSD LLM1
            'TECHNICAL': 7557,    # GBPUSD LLM2
            'CHART': 7558,        # GBPUSD LLM3
            'RISK': 7559,         # GBPUSD LLM4
            'SUPREME': 7561,      # GBPUSD LLM5
            'SMART_MONEY': 7562   # LLM6 - Smart Money Oracle (GBPUSD)
        }
        
        # PHASE 2: Intelligence enhancement LLMs (quality, timing, execution) - GBPUSD PORTS
        self.enhancement_llm_ports = {
            'OCULUS': 7563,    # GBPUSD LLM7 - Data Quality Validator
            'CHRONOS': 7564,   # GBPUSD LLM8 - Timing Optimizer  
            'PREDATOR': 7565,  # GBPUSD LLM9 - Execution Engine
            'NOVA': 7560,   # GBPUSD LLM10 - Guardian Protector
            'STRATEGIST': 7567,   # GBPUSD LLM11 - Strategist Guru
            'SENTINEL': 7568      # GBPUSD LLM12 - Quality Guardian
        }
        
        # Combine for backward compatibility
        self.llm_ports = {**self.core_llm_ports, **self.enhancement_llm_ports}
        self.tracker = llm_tracker
    
    def _validate_ecosystem_data(self, genome: dict) -> dict:
        """
        ??? ECOSYSTEM DATA VALIDATION
        
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
        
        # --- MEJORADO: Usar sl_analysis pre-procesado de Quimera ---
        sl_analysis = genome.get('sl_analysis', {})
        if sl_analysis:
            consecutive_sl = sl_analysis.get('consecutive_count', 0)
            recommendation = sl_analysis.get('recommendation', 'NORMAL')
            
            if sl_analysis.get('critical', False):
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.2  # Penalizaci�n muy alta
                validation['reason'] += f"SL_CRITICAL({consecutive_sl}); "
                log.warning(f"[ECOSYSTEM] ?? CRITICAL: {consecutive_sl} consecutive SLs - STOP TRADING")
            elif sl_analysis.get('warning', False):
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.5
                validation['reason'] += f"SL_WARNING({consecutive_sl}); "
                log.warning(f"[ECOSYSTEM] ?? WARNING: {consecutive_sl} consecutive SLs detected")
            
            # Verificar tiempo desde �ltimo SL
            seconds_since_sl = sl_analysis.get('seconds_since_last_sl', -1)
            if 0 < seconds_since_sl < 120:  # Menos de 2 min desde SL
                validation['confidence_penalty'] *= 0.6
                validation['reason'] += f"RECENT_SL({seconds_since_sl}s); "
        else:
            # Fallback al m�todo anterior si no hay sl_analysis
            sl_history = genome.get('sl_history', [])
            if len(sl_history) >= 2:
                validation['sl_caution'] = True
                validation['confidence_penalty'] *= 0.6
                validation['reason'] += f"SL_HISTORY({len(sl_history)}); "
                log.warning(f"[ECOSYSTEM] ?? {len(sl_history)} SLs in history detected")
        
        # Check velocity (indicator changes)
        indicators = genome.get('indicators', {}).get('current', {})
        ma_delta = abs(indicators.get('ma_fast_delta', 0))
        rsi_delta = abs(indicators.get('rsi_delta', 0))
        adx_delta = abs(indicators.get('adx_delta', 0))
        
        if ma_delta > 0.5 or rsi_delta > 5 or adx_delta > 2:
            validation['velocity_alert'] = True
            validation['confidence_penalty'] *= 0.7
            validation['reason'] += f"RAPID_CHANGE(MA_?={ma_delta:.3f},RSI_?={rsi_delta:.1f}); "
            log.warning(f"[ECOSYSTEM] ?? Rapid indicator changes detected")
        
        # Check multi-timeframe consensus
        timeframe_analysis = genome.get('timeframe_analysis', [])
        if len(timeframe_analysis) > 1:
            m1_signal = None
            for tf in timeframe_analysis:
                if tf.get('timeframe') == 'M1':
                    m1_signal = tf.get('signal')
            
            if m1_signal:
                disagreement_count = sum(1 for tf in timeframe_analysis 
                                       if tf.get('signal') != m1_signal)
                if disagreement_count >= 2:
                    validation['timeframe_disagreement'] = True
                    validation['confidence_penalty'] *= 0.5
                    validation['reason'] += f"TF_DISAGREE({disagreement_count}); "
                    log.warning(f"[ECOSYSTEM] ?? Multi-timeframe disagreement detected")
        
        validation['is_valid'] = (validation['confidence_penalty'] > 0.3)
        return validation
    
    def _consensus_voting_engine(self, genome: dict) -> dict:
        """
        ?? INTELLIGENT CONSENSUS VOTING ENGINE
        
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
            consensus['reason'] = "No timeframe analysis available"
            return consensus
        
        # ---------------------------------------------------------------
        # VOTE COLLECTION: Extract signal + strength + reason from each TF
        # ---------------------------------------------------------------
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
                
                # ?? INTELLIGENT STRENGTH SCALING
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
        
        # ---------------------------------------------------------------
        # VOTE AGGREGATION: Weighted consensus calculation with reasoning
        # ---------------------------------------------------------------
        
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
        
        # ---------------------------------------------------------------
        # ?? SUPER ENTRADA INTELIGENTE - Decisi�n m�s flexible
        # ---------------------------------------------------------------
        
        # Extract critical timeframes
        m1_vote = tf_votes.get('M1', {})
        m5_vote = tf_votes.get('M5', {})
        m15_vote = tf_votes.get('M15', {})
        
        m1_signal = m1_vote.get('signal', 'HOLD')
        m5_signal = m5_vote.get('signal', 'HOLD')
        m15_signal = m15_vote.get('signal', 'HOLD')
        
        m1_strength = m1_vote.get('strength', 50)
        m5_strength = m5_vote.get('strength', 50)
        
        # ?? SUPER ENTRADA: Detectar SUPER_BUY o SUPER_SELL en razones
        has_super_buy = any('SUPER_BUY' in str(v.get('reason', '')) for v in tf_votes.values())
        has_super_sell = any('SUPER_SELL' in str(v.get('reason', '')) for v in tf_votes.values())
        
        tf_agreement_list = []
        for tf_name, vote in tf_votes.items():
            if vote['signal'] in ['BUY', 'SELL']:
                tf_agreement_list.append((tf_name, vote['signal'], vote['strength']))
        
        # ---------------------------------------------------------------
        # ?? PRIORIDAD 1: SUPER ENTRADA detectada en cualquier TF
        # ---------------------------------------------------------------
        if has_super_buy and buy_votes >= 2:
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(min(95, buy_score * 1.2))
            consensus['reason'] = f"?? SUPER BUY: {buy_votes} TFs confirm ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='BUY'])}) @ {buy_score:.0f}%"
        
        elif has_super_sell and sell_votes >= 2:
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(min(95, sell_score * 1.2))
            consensus['reason'] = f"?? SUPER SELL: {sell_votes} TFs confirm ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='SELL'])}) @ {sell_score:.0f}%"
        
        # ---------------------------------------------------------------
        # ?? PRIORIDAD 2: Consenso fuerte (3+ TFs acuerdo)
        # ---------------------------------------------------------------
        elif buy_votes >= 3 and buy_score > 55:  # Relajado de 65 a 55
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(buy_score)
            consensus['reason'] = f"Strong BUY: {buy_votes} TFs ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='BUY'])}) @ {buy_score:.0f}%"
        
        elif sell_votes >= 3 and sell_score > 55:  # Relajado de 65 a 55
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(sell_score)
            consensus['reason'] = f"Strong SELL: {sell_votes} TFs ({', '.join([tf[0] for tf in tf_agreement_list if tf[1]=='SELL'])}) @ {sell_score:.0f}%"
        
        # ---------------------------------------------------------------
        # ?? PRIORIDAD 3: M1+M5 alineados (muy importante para timing)
        # ---------------------------------------------------------------
        elif m1_signal == m5_signal and m1_signal in ['BUY', 'SELL'] and m1_strength > 55:
            consensus['consensus_decision'] = m1_signal
            consensus['consensus_confidence'] = int(max(m1_strength, m5_strength))
            consensus['reason'] = f"M1+M5 Aligned: {m1_signal} (M1@{m1_strength:.0f}% M5@{m5_strength:.0f}%)"
        
        # ---------------------------------------------------------------
        # ?? PRIORIDAD 4: M1+M15 o M5+M15 alineados
        # ---------------------------------------------------------------
        elif m1_signal == m15_signal and m1_signal in ['BUY', 'SELL'] and m1_strength > 55:
            consensus['consensus_decision'] = m1_signal
            consensus['consensus_confidence'] = int(max(m1_strength, m15_vote.get('strength', 50)))
            consensus['reason'] = f"M1+M15 Aligned: {m1_signal}"
        
        elif m5_signal == m15_signal and m5_signal in ['BUY', 'SELL'] and m5_strength > 55:
            consensus['consensus_decision'] = m5_signal
            consensus['consensus_confidence'] = int(max(m5_strength, m15_vote.get('strength', 50)))
            consensus['reason'] = f"M5+M15 Aligned: {m5_signal}"
        
        # ---------------------------------------------------------------
        # ?? PRIORIDAD 5: Se�al unidireccional (solo BUY o solo SELL)
        # ---------------------------------------------------------------
        elif buy_votes > 0 and sell_votes == 0 and buy_score > 50:
            consensus['consensus_decision'] = 'BUY'
            consensus['consensus_confidence'] = int(buy_score)
            consensus['reason'] = f"Unidirectional BUY: {buy_votes} TF(s) @ {buy_score:.0f}%"
        
        elif sell_votes > 0 and buy_votes == 0 and sell_score > 50:
            consensus['consensus_decision'] = 'SELL'
            consensus['consensus_confidence'] = int(sell_score)
            consensus['reason'] = f"Unidirectional SELL: {sell_votes} TF(s) @ {sell_score:.0f}%"
        
        # ---------------------------------------------------------------
        # ?? HOLD: Solo cuando hay conflicto real o todo d�bil
        # ---------------------------------------------------------------
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
        
        log.info(f"[CONSENSUS] ?? Decision: {consensus['consensus_decision']} @ {consensus['consensus_confidence']}% | "
                f"Alignment: {consensus['alignment_score']}% | Reason: {consensus['reason']}")
        
        return consensus
    
    def analyze(self, genome: dict) -> dict:
        """
        ENHANCED ANALYSIS with 2-Phase LLM Integration
        
        Phase 1: Query Core LLMs (1-5) in parallel for BUY/SELL/HOLD voting
        Phase 2: Query Enhancement LLMs (7-8-9) sequentially with data chaining
        
        This ensures LLM9 PREDATOR receives quality_score from LLM7 and 
        timing_multiplier from LLM8 for proper mathematical integration.
        """
        symbol = genome.get('metadata', {}).get('symbol', 'GBPUSD')
        tick_id = genome.get('tick_id', 0)
        
        # DEBUG: Log genome content for data validation
        price_data = genome.get('price_data', {})
        history_len = len(price_data.get('history', []))
        log.debug(f"[TRINITY-IN] {symbol} tick#{tick_id}: price_data.history has {history_len} bars")
        if history_len == 0:
            log.warning(f"[TRINITY-IN] EMPTY HISTORY! price_data keys: {list(price_data.keys())}, genome keys: {list(genome.keys())}")
        
        # ??? VALIDATE ECOSYSTEM DATA BEFORE QUERYING LLMs
        ecosystem_validation = self._validate_ecosystem_data(genome)
        
        # -------------------------------------------------------------------
        # PHASE 1: Query CORE LLMs (1-5) in parallel for voting
        # -------------------------------------------------------------------
        llm_responses, threads, lock = {}, [], threading.Lock()
        
        for llm_name, port in self.core_llm_ports.items():
            t = threading.Thread(target=self._query_llm, args=(llm_name, port, genome, llm_responses, lock), daemon=True)
            threads.append(t)
            t.start()
        
        # Phase 1b: Also query LLM11 STRATEGIST + LLM12 SENTINEL in parallel
        for llm_name in ['STRATEGIST', 'SENTINEL']:
            if llm_name in self.enhancement_llm_ports:
                port = self.enhancement_llm_ports[llm_name]
                t = threading.Thread(target=self._query_llm, args=(llm_name, port, genome, llm_responses, lock), daemon=True)
                threads.append(t)
                t.start()
        
        for t in threads:
            t.join(timeout=self.timeout)
        
        # [NOVA REPAIR ARCHITECT - FIX CRÍTICO] A-09: Snapshot dict under lock - timed-out threads may still write
        with lock:
            llm_responses = dict(llm_responses)
        
        # -------------------------------------------------------------------
        # PHASE 2: Query ENHANCEMENT LLMs (7-8-9) with data chaining
        # -------------------------------------------------------------------
        
        # ?? Mathematical Validation: Ensure core voting completeness before enhancement
        core_votes_received = len([resp for resp in llm_responses.values() if isinstance(resp, dict) and 'decision' in resp])
        enhancement_weight = min(1.0, core_votes_received / 3.0)  # Scale enhancement based on core completeness
        
        # Step 2a: Query LLM7 OCULUS for quality_score
        # ?? NOVA INTEGRATION: Check if quantum_core sent nova_quality_score
        quality_score = 70  # Default if LLM7 unavailable
        
        # ?? NOVA-MSDA DATA: Use if available (PRIORITY 1)
        if 'nova_quality_score' in genome:
            nova_score = float(genome.get('nova_quality_score', 70))
            oculus_response = self._query_enhancement_llm('OCULUS', 7563, genome)
            
            if oculus_response:
                llm_responses['OCULUS'] = oculus_response
                oculus_score = float(oculus_response.get('quality_score', 70)) * enhancement_weight
                
                # ?? BLEND: Combine NOVA (quantum_core market audit) with OCULUS (LLM7 intelligence)
                # NOVA: Quick ground-truth about data quality
                # OCULUS: Deep analysis of indicators
                # Blend: NOVA gets 40% (quick ground truth), OCULUS gets 60% (deep learning)
                blended_score = (nova_score * 0.40) + (oculus_score * 0.60)
                quality_score = blended_score
                
                log.info(f"[TRINITY] ?? NOVA+OCULUS Blend: {nova_score:.0f}% (NOVA) � 0.40 + {oculus_score:.0f}% (OCULUS) � 0.60 = {quality_score:.0f}%")
            else:
                # OCULUS offline, use NOVA directly
                quality_score = nova_score
                log.info(f"[TRINITY] ?? OCULUS offline, using NOVA score: {quality_score:.0f}%")
        else:
            # No NOVA data, fall back to OCULUS only
            oculus_response = self._query_enhancement_llm('OCULUS', 7563, genome)
            if oculus_response:
                llm_responses['OCULUS'] = oculus_response
                quality_score = float(oculus_response.get('quality_score', 70)) * enhancement_weight
                log.info(f"[TRINITY] LLM7 OCULUS: quality_score={quality_score:.1f}% (weight={enhancement_weight:.2f})")
        
        # Step 2b: Query LLM8 CHRONOS for timing_multiplier
        timing_multiplier = 1.0  # Default if LLM8 unavailable
        chronos_response = self._query_enhancement_llm('CHRONOS', 7564, genome)
        if chronos_response:
            llm_responses['CHRONOS'] = chronos_response
            timing_multiplier = float(chronos_response.get('timing_multiplier', 1.0)) * enhancement_weight
            log.info(f"[TRINITY] LLM8 CHRONOS: timing_multiplier={timing_multiplier:.2f}x (weight={enhancement_weight:.2f})")
        
        # Step 2c: Query LLM9 PREDATOR with quality_score + timing_multiplier
        # ?? Mathematical Integration: Combine all enhancement factors coherently
        quality_factor = quality_score / 100.0  # Normalize to [0,1]
        timing_factor = min(2.0, max(0.5, timing_multiplier))  # Clamp to reasonable bounds
        enhancement_coherence = (quality_factor * timing_factor * enhancement_weight)
        
        # Create enhanced genome with LLM7 and LLM8 outputs
        enhanced_genome = genome.copy()
        enhanced_genome['quality_score'] = quality_score
        enhanced_genome['timing_multiplier'] = timing_multiplier
        
        predator_response = self._query_enhancement_llm('PREDATOR', 7565, enhanced_genome)
        if predator_response:
            llm_responses['PREDATOR'] = predator_response
            rr_ratio = float(predator_response.get('rr_ratio', 0))
            position_mult = float(predator_response.get('position_multiplier', 1.0))
            log.info(f"[TRINITY] LLM9 PREDATOR: rr_ratio={rr_ratio:.2f}, position_mult={position_mult:.2f}x")
        
        # -------------------------------------------------------------------
        # ??? PRE-VALIDATION: Use ecosystem data validator
        # -------------------------------------------------------------------
        
        if not ecosystem_validation['is_valid']:
            log.warning(f"[TRINITY] Ecosystem validation failed: {ecosystem_validation['reason']}")
        
        ecosystem_penalty = ecosystem_validation['confidence_penalty']
        
        # -------------------------------------------------------------------
        # AGGREGATE VOTES (only from CORE LLMs 1-5) + Apply Ecosystem Penalty
        # -------------------------------------------------------------------
        voting_keys = set(self.core_llm_ports.keys()) | {'STRATEGIST', 'SENTINEL'}
        core_responses = {k: v for k, v in llm_responses.items() if k in voting_keys}
        
        # Apply ecosystem validation penalty to all LLM responses
        for llm_name in core_responses:
            if 'confidence' in core_responses[llm_name]:
                core_responses[llm_name]['confidence'] *= ecosystem_penalty
                if ecosystem_penalty < 1.0:
                    core_responses[llm_name]['reason'] = f"{core_responses[llm_name].get('reason', '')} [ECOSYSTEM_CHECK]"
        
        if core_responses:
            decision, confidence, buy_score, sell_score = self._aggregate_votes(core_responses)
        else:
            # ?? CRITICAL: All LLMs timed out - FORCE HOLD to prevent false trades
            # SECURITY FIX: Never trade without real LLM votes
            decision = 'HOLD'  # Force HOLD when no LLMs respond
            confidence = 15    # Very low confidence
            buy_score, sell_score = 50, 50  # Neutral scores
            
            # CRITICAL FIX: Mark fallback votes clearly with LOW CONFIDENCE
            llm_responses.update({
                'BAYESIAN': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True},
                'TECHNICAL': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True},
                'CHART': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True},
                'RISK': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True},
                'SUPREME': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True},
                'SMART_MONEY': {'decision': 'HOLD', 'confidence': 15, 'reason': 'LLM_TIMEOUT_FALLBACK', 'is_fallback': True}
            })
            log.error(f"[TRINITY] ?? ALL LLMs TIMEOUT - FORCED HOLD (no trading without real LLM votes)")
            log.error(f"[TRINITY] ?? Make sure all 6 LLMs are running on ports 7555, 7557, 7558, 7559, 7561, 7562")
        
        # -------------------------------------------------------------------
        # ?? INTELLIGENT CONSENSUS: Cross-validate with Multi-Timeframe Analysis
        # -------------------------------------------------------------------
        # If we have timeframe analysis, use it to validate LLM decision
        consensus_result = self._consensus_voting_engine(genome)
        
        # ?? FINAL DECISION LOGIC: Combine LLM votes + Timeframe consensus
        llm_decision = decision
        llm_confidence = confidence
        tf_decision = consensus_result['consensus_decision']
        tf_confidence = consensus_result['consensus_confidence']
        tf_alignment = consensus_result['alignment_score']
        
        # Decision precedence:
        # 1. If LLM and Timeframe AGREE ? Execute with high confidence
        # 2. If LLM and Timeframe DISAGREE ? HOLD (safety)
        # 3. If Timeframe has perfect alignment (80%+) ? Override weak LLM signal
        
        if llm_decision == tf_decision and llm_decision in ['BUY', 'SELL']:
            # ? AGREEMENT: LLM + Timeframes say same thing
            final_decision = llm_decision
            final_confidence = int((llm_confidence + tf_confidence) / 2 * 1.1)  # 10% boost for alignment
            final_confidence = min(95, final_confidence)
            log.info(f"[TRINITY] ? STRONG CONSENSUS: LLM ({llm_decision}/{llm_confidence}%) + TF ({tf_decision}/{tf_confidence}%) = {final_decision}/{final_confidence}%")
        elif llm_decision != tf_decision and tf_alignment >= 80 and tf_decision in ['BUY', 'SELL']:
            # ? OVERRIDE: Timeframes have perfect alignment, override weak LLM
            final_decision = tf_decision
            final_confidence = int(tf_confidence * 0.85)  # Slightly conservative since LLMs disagreed
            log.info(f"[TRINITY] ? TIMEFRAME OVERRIDE: {tf_alignment}% aligned on {tf_decision} (LLM wanted {llm_decision})")
        elif llm_decision != tf_decision and llm_decision in ['BUY', 'SELL']:
            # ⚠️ CONFLICT: LLMs want to trade, Timeframes don't agree
            # FIX: Trade if LLM confidence >= 62% OR if TF has no data (tf_confidence==0 = TF abstained, not a real conflict)
            # When MT5 sends no timeframe analysis, empty TF must NOT block a strong LLM signal.
            if llm_confidence >= 72 or tf_confidence == 0:  # 🔧 FIX: raised from 60/62→72
                final_decision = llm_decision
                penalty = 0.9 if tf_confidence == 0 else 0.8
                final_confidence = int(llm_confidence * penalty)
                if tf_confidence == 0:
                    log.info(f"[TRINITY] ✅ NO TF DATA: Trusting LLM {llm_decision}/{llm_confidence}% (TF unavailable)")
                else:
                    log.warning(f"[TRINITY] ⚠️ TRADING WITH CAUTION: LLM strong ({llm_confidence}%) but TF uncertain ({consensus_result['reason']})")
            else:
                # Safety: HOLD when there's a real conflict AND LLM confidence is low
                final_decision = 'HOLD'
                final_confidence = max(llm_confidence, tf_confidence)
                log.warning(f"[TRINITY] 🛡️ CONFLICT HOLD: LLM {llm_decision}/{llm_confidence}% vs TF {tf_decision}/{tf_confidence}% - waiting for clarity")
        else:
            # Default: Use LLM decision
            final_decision = llm_decision
            final_confidence = llm_confidence
            log.info(f"[TRINITY] Using LLM decision: {final_decision} @ {final_confidence}%")
        
        decision = final_decision
        confidence = final_confidence
        
        # -------------------------------------------------------------------
        # APPLY ENHANCEMENT MODIFIERS from LLM7-8-9
        # ? RELAXED FOR GBP: Less aggressive penalties, more boosts
        # -------------------------------------------------------------------
        
        # Quality gate: LLM7 OCULUS data quality affects confidence - RELAXED
        if quality_score < 25:
            confidence = max(30, confidence - 15)
            log.warning(f"[TRINITY] Data quality VERY LOW ({quality_score}%) - confidence reduced to {confidence}%")
        elif quality_score < 40:
            confidence = max(35, confidence - 8)
            log.warning(f"[TRINITY] Data quality LOW ({quality_score}%) - confidence reduced to {confidence}%")
        elif quality_score >= 75:
            confidence = min(95, confidence + 5)  # 🔧 FIX: reduced from +15
            log.info(f"[TRINITY] Data quality EXCELLENT ({quality_score}%) - confidence boosted to {confidence}%")
        elif quality_score >= 55:
            confidence = min(92, confidence + 3)  # 🔧 FIX: reduced from +8
            log.info(f"[TRINITY] Data quality GOOD ({quality_score}%) - confidence boosted to {confidence}%")
        
        # Timing: LLM8 CHRONOS timing affects confidence - RELAXED
        if timing_multiplier >= 1.3:
            confidence = min(95, confidence + 5)  # 🔧 FIX: reduced timing boost
            log.info(f"[TRINITY] Excellent timing (mult={timing_multiplier:.2f}x) - confidence boosted to {confidence}%")
        elif timing_multiplier >= 1.1:
            confidence = min(92, confidence + 3)  # 🔧 FIX: reduced timing boost
            log.info(f"[TRINITY] Good timing (mult={timing_multiplier:.2f}x) - confidence boosted to {confidence}%")
        elif timing_multiplier <= 0.4:
            confidence = max(30, confidence - 12)
            log.warning(f"[TRINITY] BAD timing (mult={timing_multiplier:.2f}x) - confidence reduced to {confidence}%")
        elif timing_multiplier <= 0.6:
            confidence = max(35, confidence - 6)
            log.warning(f"[TRINITY] Poor timing (mult={timing_multiplier:.2f}x) - confidence reduced to {confidence}%")
        
        # ? R:R VETO: LLM9 PREDATOR Risk:Reward ratio affects decision
        # ?? RELAXED FOR GBP: Bajar thresholds para permitir m�s trades
        # GBP scalping tiene R:R m�s bajo naturalmente
        if rr_ratio > 0:
            if rr_ratio < 0.35:
                # R:R muy muy bajo - force HOLD (was 0.6)
                log.warning(f"[TRINITY] ?? R:R VETO: {rr_ratio:.2f} < 0.35 - Trade would have bad R:R")
                decision = 'HOLD'
                confidence = max(20, confidence * 0.3)
            elif rr_ratio < 0.7:
                # R:R bajo - reduce confidence but allow (was <1.0 = reduce)
                confidence = max(35, confidence - 8)
                log.warning(f"[TRINITY] ?? Low R:R ({rr_ratio:.2f}) - confidence reduced to {confidence}%")
            elif rr_ratio >= 2.0:
                # Excellent R:R - boost confidence
                confidence = min(95, confidence + 10)
                log.info(f"[TRINITY] ?? Excellent R:R ({rr_ratio:.2f}) - confidence boosted to {confidence}%")
            elif rr_ratio >= 1.2:
                # Good R:R - slight boost (was 1.5)
                confidence = min(92, confidence + 5)
                log.info(f"[TRINITY] ? Good R:R ({rr_ratio:.2f}) - confidence boosted to {confidence}%")
        
        # -------------------------------------------------------------------
        # ?? PHASE 3: Query LLM10 NOVA for AUDIT & EMERGENCY HALT
        # -------------------------------------------------------------------
        
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
        
        # Query LLM10 NOVA
        nova_response = self._query_llm10_nova(genome, trinity_decision)
        llm_responses['NOVA'] = nova_response
        
        # ?? EMERGENCY HALT (Hueco #23)
        if nova_response.get('emergency_halt'):
            log.critical(f"[TRINITY] ?? EMERGENCY HALT triggered by NOVA: {nova_response.get('reasoning')}")
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
        nova_multiplier = nova_response.get('quality_multiplier', 0.7)
        confidence_before = confidence
        confidence = int(confidence * nova_multiplier)
        
        # Clamp to reasonable bounds
        confidence = max(15, min(95, confidence))
        
        # Log the adjustment
        if nova_multiplier < 1.0:
            log.warning(f"[TRINITY] ?? NOVA audit: {nova_response.get('audit_score')}% | "
                       f"Multiplier {nova_multiplier:.2f}x: confidence {confidence_before}% ? {confidence}% (defensive)")
        elif nova_multiplier > 1.0:
            log.info(f"[TRINITY] ?? NOVA audit: {nova_response.get('audit_score')}% | "
                    f"Multiplier {nova_multiplier:.2f}x: confidence {confidence_before}% ? {confidence}% (boost)")
        else:
            log.info(f"[TRINITY] ?? NOVA audit: {nova_response.get('audit_score')}% | "
                    f"Multiplier {nova_multiplier:.2f}x: confidence unchanged at {confidence}%")
        
        # -------------------------------------------------------------------
        # OLD CODE: Apply NOVA-MSDA if provided (for backward compatibility)
        # -------------------------------------------------------------------
        
        old_nova_multiplier = 1.0
        if 'nova_quality_multiplier' in genome:
            old_nova_multiplier = float(genome.get('nova_quality_multiplier', 1.0))
            
            # Apply old NOVA multiplier to final confidence
            confidence_before2 = confidence
            confidence = int(confidence * old_nova_multiplier)
            
            # Clamp to reasonable bounds
            confidence = max(15, min(95, confidence))
            
            # Log the adjustment
            if old_nova_multiplier < 1.0:
                log.warning(f"[TRINITY] ?? NOVA-MSDA multiplier {old_nova_multiplier:.2f}x: confidence {confidence_before2}% ? {confidence}% (defensive)")
            elif old_nova_multiplier > 1.0:
                log.info(f"[TRINITY] ?? NOVA-MSDA multiplier {old_nova_multiplier:.2f}x: confidence {confidence_before2}% ? {confidence}% (boost)")
        
        llm_summary = ', '.join([f"{k}:{v.get('confidence', 0)}%" for k, v in sorted(llm_responses.items())])
        log.info(f'[TRINITY] {symbol} tick#{tick_id}: {decision} @ {confidence}% | LLMs:{len(llm_responses)}/8 [{llm_summary}]')

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
                'hold_score': 100-buy_score-sell_score
            },
            # Enhancement data from LLM7-8-9
            'quality_score': quality_score,
            'timing_multiplier': timing_multiplier,
            'rr_ratio': predator_response.get('rr_ratio', 0) if predator_response else 0,
            'position_multiplier': predator_response.get('position_multiplier', 1.0) if predator_response else 1.0,
            # ?? Consensus voting data
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
                opens = closes.copy()  # Approximate opens from closes
                log.debug(f"[_query_llm] {llm_name}: ? Using bar_data.closes: {len(closes)} prices (LIVE TICK INCLUDED)")
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
                    log.warning(f"[_query_llm] {llm_name}: ?? LOW DATA: {len(closes)} closes, price={price:.2f}")
            
            # Fallback if no history
            if not closes:
                closes = [float(price)]
                log.warning(f"[_query_llm] {llm_name}: ?? No history! Using single price: {price}")
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
                # Changed from > 0.01 to > 0.001 (0.1 pip for GBPUSD)
                # This catches micro-movements that were previously ignored
                if len(closes) > 0:
                    price_diff = abs(closes[-1] - price)
                    if price_diff > 0.001:  # More than 0.1 pip difference
                        # Append current tick price to closes array
                        closes.append(float(price))
                        highs.append(float(price))  # Current tick is its own high
                        lows.append(float(price))   # Current tick is its own low
                        opens.append(closes[-2] if len(closes) > 1 else float(price))  # Open = previous close
                        log.info(f"[_query_llm] {llm_name}: ? LIVE TICK ADDED: {price:.2f} (was {closes[-2]:.2f}, diff={price_diff:.3f})")
                    else:
                        log.debug(f"[_query_llm] {llm_name}: Tick {price:.2f} same as last close (diff={price_diff:.3f})")
                else:
                    # First tick - always add
                    closes.append(float(price))
                    highs.append(float(price))
                    lows.append(float(price))
                    opens.append(float(price))
                    log.info(f"[_query_llm] {llm_name}: ? FIRST TICK: {price:.2f}")
            
            # ============================================================
            # NORMALIZE CANDLES FOR LLM5 (requires 'close', 'open', 'high', 'low', 'volume')
            # ============================================================
            normalized_candles = []
            for i in range(min(len(closes), len(opens), len(highs), len(lows))):
                normalized_candles.append({
                    'close': float(closes[i]),
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'volume': 100.0  # Default volume since MT5 may not provide tick volume on M1
                })
            
            # ============================================================
            # BUILD REQUEST WITH CORRECT FIELD NAMES FOR EACH LLM
            # ============================================================
            # Extract raw indicators from genome
            rsi = float(indicators.get('rsi', 50))
            adx = float(indicators.get('adx', 25))
            atr_raw = float(indicators.get('atr_pips', indicators.get('atr', 0)))
            macd_line = float(indicators.get('macd', 0))  # MACD line (EMA12 - EMA26)
            macd_hist = float(indicators.get('macd_histogram', macd_line * 0.2))  # ? FIX: Use actual histogram, fallback to 20% of MACD line
            
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
            request = {
                'symbol': genome.get('metadata', {}).get('symbol', 'GBPUSD'),
                'price': float(price),
                'current_price': float(price),
                'prices': [float(c) for c in closes],
                'candles': normalized_candles,  # ? FIX: Use normalized candles for LLM5
                
                # === INDICATORS - Multiple naming conventions for compatibility ===
                # Original names (what Trinity currently sends)
                'rsi': float(rsi),
                'adx': float(adx),
                'atr': float(atr_raw),
                'macd': float(macd_line),  # MACD line
                
                # LLM1 expected names (what LLM1 searches for)
                'atr_14': float(atr_raw),  # ? FIX: LLM1 looks for 'atr_14' not 'atr'
                'macd_histogram': float(macd_hist),  # ? FIX: Now uses ACTUAL histogram, not MACD line!
                'sma_50': float(sma_50),  # ? FIX: LLM1 expects SMA_50
                'sma_200': float(sma_200),  # ? FIX: LLM1 expects SMA_200
                'bb_upper': float(bb_upper),  # ? FIX: LLM1 expects Bollinger Upper
                'bb_lower': float(bb_lower),  # ? FIX: LLM1 expects Bollinger Lower
                
                # Bar data structure for LLM3/4/5
                'bar_data': {
                    'closes': [float(c) for c in closes],
                    'highs': [float(h) for h in highs],
                    'lows': [float(l) for l in lows],
                    'opens': [float(o) for o in opens]
                },
                
                # Full indicators dict for any LLM that needs it
                'indicators': indicators,
                'tick_id': genome.get('tick_id', 0)
            }
            
            # DEBUG: Log request details for each LLM
            log.debug(f"[_query_llm] {llm_name}: Sending request with {len(request['prices'])} prices, {len(request['candles'])} candles, price={price:.2f}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, port))
            log.info(f"[TRINITY->{llm_name}] ? Connected to port {port}")
            
            # Send: 4-byte header + JSON
            request_json = json.dumps(request).encode('utf-8')
            sock.sendall(struct.pack('>I', len(request_json)) + request_json)
            log.info(f"[TRINITY->{llm_name}] ?? Sent {len(request_json)} bytes")
            
            # Receive: 4-byte header + JSON
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
                    # Fix: SMART_MONEY devuelve 'recommendation' no 'decision'
                    if 'recommendation' in response and 'decision' not in response:
                        response['decision'] = response['recommendation']
                    decision = response.get('decision', 'HOLD').upper()
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
                            'reason': response.get('reason', ''),
                            # Patterns from LLM5 (SUPREME) - now properly extracted
                            'chart_patterns': chart_patterns_clean,
                            'patterns_found': response.get('patterns_found', len(raw_patterns)),
                            'bullish_patterns': response.get('bullish_patterns', 0),
                            'bearish_patterns': response.get('bearish_patterns', 0),
                        }
                    log.info(f'[TRINITY<-{llm_name}] {decision}@{confidence:.1f}% | Patterns: {len(chart_patterns_clean)}')
            
            sock.close()
        
        except socket.timeout:
            log.warning(f'[TRINITY<-{llm_name}] ? TIMEOUT on port {port} (>2s)')
        except ConnectionRefusedError:
            log.warning(f'[TRINITY<-{llm_name}] ? NOT RUNNING on port {port}')
        except Exception as e:
            log.warning(f'[TRINITY<-{llm_name}] ?? Error: {type(e).__name__}: {e}')
    
    # ---------------------------------------------------------------------------------------
    # ?? BANK-GRADE CONSENSUS ALGORITHM v2.0
    # ---------------------------------------------------------------------------------------
    # This algorithm uses advanced mathematical principles from:
    # - Bayesian Inference (posterior probability estimation)
    # - Game Theory (Nash equilibrium for divergence detection)
    # - Information Theory (Shannon entropy for uncertainty)
    # - Statistical Mechanics (Boltzmann weighting)
    # - Ensemble Learning (weighted meta-learning)
    # ---------------------------------------------------------------------------------------
    
    def _aggregate_votes(self, llm_responses: dict) -> tuple:
        """
        ?? BANK-GRADE CONSENSUS: Ultra-intelligent 5-LLM fusion algorithm
        
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
        
        num_llms = len(llm_responses)
        
        # ---------------------------------------------------------------
        # STEP 1: EXTRACT AND CALIBRATE INDIVIDUAL SIGNALS
        # ---------------------------------------------------------------
        signals = {'BUY': [], 'SELL': [], 'HOLD': []}
        
        # ?? DYNAMIC WEIGHTS: Use LLMPerformanceTracker for adaptive weighting
        llm_weights = {}
        for llm_name in llm_responses.keys():
            llm_weights[llm_name] = self.tracker.get_dynamic_weight(llm_name)
        
        log.debug(f"[BANK-GRADE] Dynamic LLM weights: {llm_weights}")
        
        for llm_name, llm_data in llm_responses.items():
            decision = llm_data.get('decision', 'HOLD')
            raw_confidence = llm_data.get('confidence', 50)
            
            # NORMALIZE DECISIONS: Convert LLM7-8-9 special decisions to standard
            # LLM7 OCULUS: APPROVE/CAUTION/REJECT -> Skip (not a trading decision)
            # LLM8 CHRONOS: READY/PREPARING/WAITING -> Skip (timing, not direction)
            # LLM9 PREDATOR: EXECUTE/WAIT/ABORT -> Skip (execution, not direction)
            if decision in ['APPROVE', 'CAUTION', 'REJECT', 'READY', 'PREPARING', 
                           'WAITING', 'EXECUTE', 'WAIT', 'ABORT', 'ABSTAIN']:  # [NOVA AUDIT F-15]
                continue  # Skip non-voting LLMs
            
            # Normalize other decisions
            if decision not in ['BUY', 'SELL', 'HOLD']:
                decision = 'HOLD'
            
            # Record signal for tracking (used for future dynamic weights)
            self.tracker.record_signal(llm_name, decision, raw_confidence)
            
            # ?? NON-LINEAR CONFIDENCE CALIBRATION (sigmoid-like transformation)
            # This penalizes mid-range confidence and amplifies extremes
            # f(x) = 50 + 50 * tanh(3 * (x/100 - 0.5))
            normalized = raw_confidence / 100.0
            calibrated = 50 + 50 * math.tanh(3 * (normalized - 0.5))
            
            # Apply LLM-specific weight
            weight = llm_weights.get(llm_name, 1.0)
            weighted_conf = calibrated * weight
            
            signals[decision].append({
                'llm': llm_name,
                'raw_conf': raw_confidence,
                'calibrated': calibrated,
                'weighted': weighted_conf,
                'weight': weight
            })
        
        # ---------------------------------------------------------------
        # STEP 2: CALCULATE BAYESIAN POSTERIOR PROBABILITIES
        # ---------------------------------------------------------------
        # P(BUY|evidence) ? P(evidence|BUY) * P(BUY)
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
        likelihood_hold = calculate_likelihood(signals['HOLD']) * 0.65  # 🔧 FIX: HOLD penalty relaxed (was too harsh)
        
        total_likelihood = likelihood_buy + likelihood_sell + likelihood_hold + 1e-10
        
        posterior_buy = likelihood_buy / total_likelihood
        posterior_sell = likelihood_sell / total_likelihood
        posterior_hold = likelihood_hold / total_likelihood
        
        # ---------------------------------------------------------------
        # STEP 3: CALCULATE SHANNON ENTROPY (DISAGREEMENT MEASURE)
        # ---------------------------------------------------------------
        # H = -S p(x) * log2(p(x))
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
        
        # ---------------------------------------------------------------
        # STEP 4: DIVERGENCE DETECTION (CONFLICTING SIGNALS)
        # ---------------------------------------------------------------
        # If BUY and SELL both have strong signals, be cautious
        
        buy_strength = sum(s['weighted'] for s in signals['BUY']) if signals['BUY'] else 0
        sell_strength = sum(s['weighted'] for s in signals['SELL']) if signals['SELL'] else 0
        
        # Divergence score: high when both directions are strong
        if buy_strength > 0 and sell_strength > 0:
            # [NOVA REPAIR ARCHITECT - FIX CRÍTICO] A-01: ratio-based divergence (was min-based, always > 0.5)
            strength_ratio = max(buy_strength, sell_strength) / (min(buy_strength, sell_strength) + 1e-10)
            divergence = 1.0 / strength_ratio  # 0.0 (one side dominates) to 1.0 (equal conflict)
        else:
            divergence = 0.0
        
        # ---------------------------------------------------------------
        # STEP 5: CALCULATE WEIGHTED SCORES FOR EACH ACTION
        # ---------------------------------------------------------------
        
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
        hold_score = calculate_action_score(signals['HOLD'], posterior_hold) * 0.7  # HOLD dampening
        
        # ---------------------------------------------------------------
        # STEP 6: FINAL DECISION WITH CONFIDENCE CALCULATION
        # ---------------------------------------------------------------
        
        total_score = buy_score + sell_score + hold_score + 1e-10
        
        # Normalize scores to percentages
        buy_pct = (buy_score / total_score) * 100
        sell_pct = (sell_score / total_score) * 100
        hold_pct = (hold_score / total_score) * 100
        
        # Decision based on highest score - ?? RELAXED FOR GBP SCALPING
        if buy_score > sell_score and buy_score > hold_score:
            decision = 'BUY'
            # ?? BANK-GRADE: Confidence = weighted average of voting LLMs
            # When majority agrees, use simpler and higher confidence
            vote_count = len(signals['BUY'])
            total_confidence = sum(s['raw_conf'] for s in signals['BUY'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            
            # ?? ELEVATED: Majority bonus (3/5=+8%, 4/5=+17%, 5/5=+26%)
            majority_bonus = 1.0 + (vote_count - 2.5) * 0.09
            confidence = int(raw_conf * majority_bonus * (1 - divergence * 0.35))
            
            # ?? RELAXED: M�nimo 40% para BUY (was 65%, muy restrictivo)
            # quantum_core tiene su propio filtro, no duplicar aqu�
            if confidence < 40:
                decision = 'HOLD'
                confidence = 35
            
        elif sell_score > buy_score and sell_score > hold_score:
            decision = 'SELL'
            vote_count = len(signals['SELL'])
            total_confidence = sum(s['raw_conf'] for s in signals['SELL'])
            raw_conf = total_confidence / vote_count if vote_count > 0 else 50
            majority_bonus = 1.0 + (vote_count - 2.5) * 0.09
            confidence = int(raw_conf * majority_bonus * (1 - divergence * 0.35))
            
            # ?? RELAXED: M�nimo 40% para SELL (was 65%)
            if confidence < 40:
                decision = 'HOLD'
                confidence = 35
            
        else:
            decision = 'HOLD'
            if signals['HOLD']:
                raw_conf = sum(s['raw_conf'] for s in signals['HOLD']) / len(signals['HOLD'])
            else:
                raw_conf = 50
            confidence = int(raw_conf * 0.85)  # HOLD = lower confidence (indecision)
        
        # ---------------------------------------------------------------
        # STEP 7: CONFIDENCE BOUNDS AND FINAL ADJUSTMENTS
        # ---------------------------------------------------------------
        
        # Clamp confidence to valid range
        confidence = max(20, min(95, confidence))
        
        # If high divergence, cap confidence
        if divergence > 0.5:
            confidence = min(confidence, 60)
            log.info(f"[BANK-GRADE] ?? HIGH DIVERGENCE ({divergence:.2f}) - Confidence capped at 60")
        
        # If perfect agreement (all LLMs same decision), boost confidence
        if len(signals[decision]) == num_llms and num_llms >= 5:  # 🔧 FIX: require min 5 voters
            confidence = min(95, confidence + 6)  # 🔧 FIX: +6% not +10%
            log.info(f"[BANK-GRADE] ?? PERFECT AGREEMENT! All {num_llms} LLMs voted {decision}")
        
        # ?? BANK-GRADE LOGGING: Show mathematical analysis
        log.info(f"[BANK-GRADE] ?? ANALYSIS: Bayesian P(BUY)={posterior_buy:.3f} P(SELL)={posterior_sell:.3f} P(HOLD)={posterior_hold:.3f}")
        log.info(f"[BANK-GRADE] ?? ENTROPY: {current_entropy:.3f}/{max_entropy:.3f} = {entropy_penalty:.1%} disagreement | Agreement bonus: {agreement_bonus:.1%}")
        log.info(f"[BANK-GRADE] ?? SCORES: BUY={buy_pct:.1f}% SELL={sell_pct:.1f}% HOLD={hold_pct:.1f}%")
        log.info(f"[BANK-GRADE] ?? DECISION: {decision} @ {confidence}% confidence | Divergence: {divergence:.2%}")
        
        # Ensure buy/sell scores are properly scaled
        buy_score_final = min(100, max(0, buy_pct))
        sell_score_final = min(100, max(0, sell_pct))
        
        return decision, confidence, buy_score_final, sell_score_final
    
    def _fallback_decision(self, genome: dict) -> tuple:
        # [NOVA REPAIR ARCHITECT - FIX CRÍTICO] A-03: HOLD when ALL LLMs timeout (was guessing BUY/SELL@60%)
        log.warning("[FALLBACK] ⚠️ ALL LLMs TIMEOUT - FORCING HOLD (no trade without consensus)")
        return 'HOLD', 15
    
    # -------------------------------------------------------------------
    # ?? LLM10 NOVA INTEGRATION: Query NOVA for audit & emergency halt
    # -------------------------------------------------------------------
    
    def _query_llm10_nova(self, genome: dict, trinity_decision: dict) -> dict:
        """
        ?? QUERY LLM10 NOVA - Auditor de decisiones
        
        LLM10 NOVA audita:
        1. Causalidad de la decisi�n
        2. Validez de datos
        3. Coherencia interna
        4. Riesgos correlacionados
        5. Emergencias/halts
        
        Retorna: {
            'is_valid': bool,
            'quality_multiplier': 0.0-1.0,  # Si 0 = HALT (no hacer nada)
            'audit_score': 0-100,
            'alerts': [],
            'reasoning': str,
            'emergency_halt': bool
        }
        """
        
        try:
            # 1?? ARMAR CONTEXTO COMPLETO para LLM10
            # FIX: Extract bid/ask from multiple possible locations in genome
            bid = genome.get('bid') or genome.get('price_data', {}).get('bid') or genome.get('bar_data', {}).get('current', {}).get('bid', 0)
            ask = genome.get('ask') or genome.get('price_data', {}).get('ask') or genome.get('bar_data', {}).get('current', {}).get('ask', 0)
            
            # Build price_data with bid/ask included
            price_data = genome.get('price_data', {}).copy() if genome.get('price_data') else {}
            price_data['bid'] = bid
            price_data['ask'] = ask
            
            audit_context = {
                'trinity_decision': trinity_decision.get('consensus_decision'),
                'trinity_confidence': trinity_decision.get('consensus_confidence'),
                'trinity_alignment': trinity_decision.get('alignment_score'),
                'trinity_reasoning': trinity_decision.get('reason'),
                
                # Datos del mercado - NOW WITH BID/ASK INCLUDED
                'price_data': price_data,
                'indicators': genome.get('indicators', {}),
                
                # Datos de validaci�n
                'ecosystem_validation': genome.get('_ecosystem_validation', {}),
                
                # Metadata
                'symbol': genome.get('metadata', {}).get('symbol'),
                'timestamp': genome.get('metadata', {}).get('timestamp'),
            }
            
            # 2?? VALIDACI�N PRE-ENV�O (Hueco #5, #10)
            pre_flight = self._validate_audit_context(audit_context)
            if not pre_flight['valid']:
                log.warning(f"[NOVA PRE-FLIGHT] ? {pre_flight['reason']}")
                return {
                    'is_valid': False,
                    'quality_multiplier': 0.0,
                    'audit_score': 0,
                    'alerts': [pre_flight['reason']],
                    'reasoning': 'Pre-flight validation failed',
                    'emergency_halt': True
                }
            
            # 3️ CONECTAR CON LLM10 (CON TIMING)
            start_time = time.time()
            
            try:
                response = requests.post(
                    f'http://{self.host}:7560/audit',
                    json=audit_context,
                    timeout=2.0  # 2 segundos max para LLM10
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                if latency_ms > 500:
                    log.warning(f"[NOVA LATENCY] ?? LLM10 slow: {latency_ms:.0f}ms")
                
                if response.status_code != 200:
                    log.error(f"[NOVA ERROR] HTTP {response.status_code}")
                    return self._fallback_nova_response()
                
                nova_response = response.json()
                
                # 4?? VALIDACI�N POST-RECEPCI�N (Hueco #10)
                post_flight = self._validate_nova_response(nova_response)
                if not post_flight['valid']:
                    log.warning(f"[NOVA POST-FLIGHT] ? {post_flight['reason']}")
                    return self._fallback_nova_response()
                
                # 5?? LOG Y RETORNO
                log.info(f"[NOVA AUDIT] ? Score: {nova_response.get('audit_score')}, "
                        f"Multiplier: {nova_response.get('quality_multiplier')}, "
                        f"Latency: {latency_ms:.0f}ms")
                
                return nova_response
            
            except requests.exceptions.Timeout:
                log.warning(f"[NOVA TIMEOUT] LLM10 no respondi� en 2s")
                return self._fallback_nova_response()
            
            except requests.exceptions.ConnectionError:
                log.error(f"[NOVA CONNECTION] ? No se pudo conectar a puerto 7565")
                return self._fallback_nova_response()
            
            except Exception as e:
                log.error(f"[NOVA ERROR] {str(e)}")
                return self._fallback_nova_response()
        
        except Exception as e:
            log.critical(f"[NOVA CRITICAL] {str(e)}")
            return self._fallback_nova_response()
    
    def _validate_audit_context(self, context: dict) -> dict:
        """VALIDACI�N PRE-ENV�O: Audita que datos enviados a LLM10 son v�lidos"""
        
        errors = []
        
        # ? Validar estructura m�nima
        if not context.get('price_data'):
            errors.append("price_data missing")
        
        if not context.get('indicators'):
            errors.append("indicators missing")
        
        # ? Validar rangos (Hueco #5)
        indicators = context.get('indicators', {}).get('current', {})
        
        rsi = indicators.get('rsi', 50)
        if not (0 <= rsi <= 100):
            errors.append(f"RSI {rsi} outside [0,100]")
        
        adx = indicators.get('adx', 20)
        if not (0 <= adx <= 100):
            errors.append(f"ADX {adx} outside [0,100]")
        
        bid = context.get('price_data', {}).get('bid', 0)
        ask = context.get('price_data', {}).get('ask', 0)
        
        # Log for debugging if bid/ask are zero
        if bid == 0 or ask == 0:
            log.debug(f"[NOVA VALIDATE] bid={bid} ask={ask} from price_data, checking available keys...")
            log.debug(f"[NOVA VALIDATE] price_data keys: {list(context.get('price_data', {}).keys())}")
        
        # ? Validar sanity (Hueco #10) - Only if we have valid prices
        if bid > 0 and ask > 0:
            if bid >= ask:
                errors.append(f"Price corrupted: bid {bid} >= ask {ask}")
        else:
            # Skip price validation if we don't have valid bid/ask - allow system to continue
            log.warning(f"[NOVA VALIDATE] ?? Skipping bid/ask validation (bid={bid}, ask={ask}) - data may not include tick prices")
        
        # ? Validar timestamp (Hueco #6)
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
        """VALIDACI�N POST-RECEPCI�N: Audita que respuesta de LLM10 es v�lida"""
        
        errors = []
        
        # ? Validar estructura
        if 'quality_multiplier' not in response:
            errors.append("quality_multiplier missing")
        
        if 'audit_score' not in response:
            errors.append("audit_score missing")
        
        # ? Validar rangos
        multiplier = response.get('quality_multiplier', 0.5)
        if not (0.0 <= multiplier <= 1.0):
            errors.append(f"Multiplier {multiplier} outside [0.0, 1.0]")
        
        score = response.get('audit_score', 50)
        if not (0 <= score <= 100):
            errors.append(f"Score {score} outside [0, 100]")
        
        # ? Validar l�gica
        if response.get('emergency_halt') and multiplier > 0.5:
            errors.append("Contradiction: emergency_halt=True but multiplier>0.5")
        
        return {
            'valid': len(errors) == 0,
            'reason': ' | '.join(errors) if errors else 'Response valid'
        }
    
    def _fallback_nova_response(self) -> dict:
        """FALLBACK: Si LLM10 falla, �qu� usar? (Hueco #23)"""
        
        return {
            'is_valid': True,
            'quality_multiplier': 0.7,  # Conservador
            'audit_score': 70,
            'alerts': ['LLM10 NOVA unavailable, using fallback'],
            'reasoning': 'LLM10 connection failed',
            'emergency_halt': False
        }

# ? TCP SERVER - Trinity accepts genomes from quantum_core on port 6666
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
                self.dashboard = QuantumDashboard(port=7567)  # GBPUSD dashboard port
                self.dashboard.start_listener()
                log.info('[SERVER] ? Dashboard loaded and listening')
            except Exception as e:
                log.warning(f'[SERVER] ??  Dashboard not available: {e}')
                self.dashboard = None
        
        log.info('[SERVER] Initialization complete')
    
    def run(self, port=7566):
        """Start TCP server on specified port (GBPUSD Trinity on 7566)"""
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
        """Handle genome from quantum_core"""
        try:
            client.settimeout(5)
            
            # Read header (4 bytes)
            header = client.recv(4)
            if not header or len(header) != 4:
                log.warning(f'[CLIENT {addr}] Invalid header')
                client.close()
                return
            
            length = struct.unpack('>I', header)[0]
            
            # Read genome
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
            

            # ═══ PING/ACK HANDLER ═══
            if data == b'PING':
                try:
                    ack_payload = b'ACK'
                    ack_header = struct.pack('>I', len(ack_payload))
                    client.sendall(ack_header + ack_payload)
                except Exception:
                    pass
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

def run_server(port=7566):
    """Run Trinity consensus server with optional dashboard - GBPUSD"""
    server = TrinityServer(dashboard_enabled=True)
    server.run(port=port)

if __name__ == '__main__':
    try:
        log.info('[TRINITY] -----------------------------------------')
        log.info('[TRINITY] TRINITY CONSENSUS ENGINE v1.0 - GBPUSD')
        log.info('[TRINITY] Consensus Orchestrator - 10 LLM Integration')
        log.info('[TRINITY] -----------------------------------------')
        run_server(port=7566)  # GBPUSD Trinity port
    except KeyboardInterrupt:
        log.info('[TRINITY] ?? Stopped by user')
    except Exception as e:
        log.error(f'[TRINITY] FATAL: {e}', exc_info=True)
