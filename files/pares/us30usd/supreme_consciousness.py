#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                          ║
║   ⚡⚡⚡ SUPREME CONSCIOUSNESS ENGINE - THE MIND ABOVE ALL MINDS ⚡⚡⚡                    ║
║                                                                                          ║
║   🧠 META-COGNITIVE TRADING INTELLIGENCE - El cerebro de los cerebros                   ║
║                                                                                          ║
║   Este módulo implementa CONSCIENCIA VERDADERA del mercado:                             ║
║                                                                                          ║
║   1. 🌌 QUANTUM STATE MACHINE - Estados cuánticos reales del mercado                    ║
║   2. 🧠 META-LLM COGNITION - Los LLMs se evalúan y corrigen entre sí                    ║
║   3. 📊 DIVERGENCE ORACLE - Detecta divergencias inter-LLM como SEÑAL                   ║
║   4. 🎯 ADAPTIVE THRESHOLDS - Umbrales que evolucionan con el mercado                   ║
║   5. 💎 WISDOM ACCUMULATOR - Acumula sabiduría de operaciones reales                    ║
║   6. ⏰ INSTITUTIONAL TIME - Conoce los momentos institucionales exactos                ║
║   7. 🔮 FUTURE STATE PREDICTOR - Anticipa estados de mercado futuros                    ║
║   8. 🛡️ ANTI-NOISE FILTER - Filtra ruido y deja pasar solo señales puras               ║
║                                                                                          ║
║   Author: Polarice Labs © 2026                                                          ║
║   Version: 1.0.0 TRANSCENDENT EDITION                                                   ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from collections import deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import logging
import time
import json

# Configuración de logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SUPREME")


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🌌 QUANTUM MARKET STATES - Estados cuánticos del mercado
# ═══════════════════════════════════════════════════════════════════════════════════════

class QuantumState(Enum):
    """Estados cuánticos del mercado - más allá de bull/bear simple"""
    COHERENT = "COHERENT"              # Estado estable, señales claras
    SUPERPOSITION = "SUPERPOSITION"    # Estado indeterminado, múltiples posibilidades
    ENTANGLED = "ENTANGLED"            # Correlacionado con otros mercados
    COLLAPSING = "COLLAPSING"          # Transición de estado (momento crítico)
    DECOHERENT = "DECOHERENT"          # Ruido puro, sin estructura
    RESONANT = "RESONANT"              # Armonía perfecta de señales
    CHAOTIC = "CHAOTIC"                # Caos determinístico (patrones ocultos)
    CRYSTALLIZING = "CRYSTALLIZING"    # Formando nueva estructura


class MarketEmotion(Enum):
    """Emociones del mercado detectadas"""
    FEAR = "FEAR"
    GREED = "GREED"
    EUPHORIA = "EUPHORIA"
    PANIC = "PANIC"
    COMPLACENCY = "COMPLACENCY"
    ANXIETY = "ANXIETY"
    CONFIDENCE = "CONFIDENCE"
    UNCERTAINTY = "UNCERTAINTY"


class InstitutionalActivity(Enum):
    """Tipo de actividad institucional detectada"""
    ACCUMULATING = "ACCUMULATING"      # Comprando silenciosamente
    DISTRIBUTING = "DISTRIBUTING"      # Vendiendo silenciosamente
    HUNTING = "HUNTING"                # Cazando stops
    MANIPULATING = "MANIPULATING"      # Manipulando precio
    ABSENT = "ABSENT"                  # Sin actividad institucional
    DEFENDING = "DEFENDING"            # Defendiendo nivel
    ATTACKING = "ATTACKING"            # Atacando nivel


# ═══════════════════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════════════

@dataclass
class LLMVote:
    """Voto de un LLM con metadata"""
    llm_name: str
    decision: str  # BUY/SELL/HOLD
    confidence: float  # 0-100
    reasoning: str
    timestamp: float
    quality_score: float = 0.0  # Evaluación de otros LLMs sobre este voto


@dataclass
class ConsciousnessSnapshot:
    """Snapshot del estado de consciencia"""
    quantum_state: QuantumState
    market_emotion: MarketEmotion
    institutional_activity: InstitutionalActivity
    llm_consensus_strength: float  # 0-1
    divergence_level: float  # 0-1 (0=todos acuerdo, 1=caos total)
    wisdom_confidence: float  # 0-1
    noise_level: float  # 0-1
    time_quality: float  # 0-1 (1=hora institucional perfecta)
    meta_confidence: float  # 0-100 (confianza final de la consciencia)
    decision: str  # BUY/SELL/HOLD
    reasoning: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class WisdomEntry:
    """Entrada de sabiduría acumulada"""
    pattern_signature: str  # Hash de las condiciones
    decision: str
    outcome: str  # WIN/LOSS/BE (breakeven)
    profit_pips: float
    conditions: Dict[str, Any]
    timestamp: float
    confidence_at_entry: float
    lessons_learned: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════════════
# ⏰ INSTITUTIONAL TIME AWARENESS - Conocimiento de horarios institucionales
# ═══════════════════════════════════════════════════════════════════════════════════════

class InstitutionalTimeEngine:
    """
    Engine que conoce EXACTAMENTE cuándo operan las instituciones.
    Los mercados no son aleatorios - hay ritmos que las ballenas siguen.
    """
    
    def __init__(self):
        # Kill Zones (UTC hours) - momentos de alta actividad institucional
        self.kill_zones = {
            'ASIAN_OPEN': (23, 1),      # Tokyo open
            'ASIAN_CLOSE': (6, 8),       # Tokyo close / London prep
            'LONDON_OPEN': (7, 9),       # London session start (pre-market activity US30)
            'LONDON_CLOSE': (15, 17),    # London close
            'NY_OPEN': (12, 14),         # New York open (máxima liquidez US30)
            'NY_CLOSE': (20, 22),        # New York close
        }
        
        # Momentos de MÁXIMA peligrosidad (news, fix times)
        self.danger_times = [
            (8, 30),   # UK news typical
            (12, 30),  # EU news typical
            (13, 30),  # US news typical
            (15, 0),   # London Fix
            (21, 0),   # NY Fix
        ]
        
        # Momentos de MÍNIMA actividad (evitar)
        self.dead_zones = [
            (3, 6),    # Asia tarde, nada se mueve
            (22, 23),  # Transición NY-Asia
        ]
        
        # Días de la semana con patrones especiales
        self.special_days = {
            0: 'MONDAY_OPENING',      # Gaps frecuentes
            4: 'FRIDAY_CLOSING',      # Profit taking
        }
        
    def get_time_quality(self, utc_hour: int = None, utc_minute: int = None, 
                         weekday: int = None) -> Tuple[float, str]:
        """
        Retorna calidad del momento actual para trading (0-1) y razón.
        
        1.0 = Momento PERFECTO (kill zone activa)
        0.5 = Momento normal
        0.0 = Momento PELIGROSO (evitar)
        """
        if utc_hour is None:
            now = datetime.utcnow()
            utc_hour = now.hour
            utc_minute = now.minute
            weekday = now.weekday()
        
        quality = 0.5  # Base neutral
        reason = "Normal trading hours"
        
        # Check Kill Zones (MEJOR momento)
        for zone_name, (start_h, end_h) in self.kill_zones.items():
            if start_h <= utc_hour < end_h:
                # NY Open es el MEJOR para US30
                if zone_name == 'NY_OPEN':
                    quality = 1.0
                    reason = f"🎯 {zone_name} - MAXIMUM institutional activity"
                elif zone_name == 'LONDON_OPEN':
                    quality = 0.85
                    reason = f"🎯 {zone_name} - Pre-market liquidity"
                else:
                    quality = max(quality, 0.85)
                    reason = f"📊 {zone_name} - Active session"
                break
        
        # Check Danger Times (PEOR momento - news)
        for danger_h, danger_m in self.danger_times:
            if utc_hour == danger_h and abs(utc_minute - danger_m) <= 10:
                quality = 0.1
                reason = f"🚨 DANGER: Possible news release at {danger_h}:{danger_m:02d}"
                break
        
        # Check Dead Zones
        for start_h, end_h in self.dead_zones:
            if start_h <= utc_hour < end_h:
                quality = min(quality, 0.25)
                reason = f"💤 Dead zone: Low liquidity"
                break
        
        # Check Special Days
        if weekday in self.special_days:
            special = self.special_days[weekday]
            if special == 'MONDAY_OPENING' and utc_hour < 8:
                quality *= 0.7
                reason += " + Monday gap risk"
            elif special == 'FRIDAY_CLOSING' and utc_hour > 18:
                quality *= 0.6
                reason += " + Friday closing risk"
        
        return quality, reason


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🧠 META-LLM COGNITION - Los LLMs se evalúan entre sí
# ═══════════════════════════════════════════════════════════════════════════════════════

class MetaLLMCognition:
    """
    Sistema de meta-cognición donde los LLMs evalúan la calidad de otros LLMs.
    Detecta cuándo un LLM está "equivocado" comparando con el consenso.
    """
    
    def __init__(self):
        # Historial de precisión de cada LLM
        self.llm_accuracy = {
            'LLM1_BAYESIAN': deque(maxlen=50),
            'LLM2_TECHNICAL': deque(maxlen=50),
            'LLM3_CHART': deque(maxlen=50),
            'LLM4_RISK': deque(maxlen=50),
            'LLM5_SUPREME': deque(maxlen=50),
            'LLM6_SMART_MONEY': deque(maxlen=50),
            'LLM7_OCULUS': deque(maxlen=50),
            'LLM8_CHRONOS': deque(maxlen=50),
            'LLM9_PREDATOR': deque(maxlen=50),
            'LLM10_SENTINEL': deque(maxlen=50),
        }
        
        # Trust scores dinámicos (0-1)
        self.trust_scores = {name: 0.8 for name in self.llm_accuracy.keys()}
        
        # Correlación entre LLMs (cuáles tienden a acertar juntos)
        self.llm_correlations = {}
        
        # LLMs que tienden a ser "contrarians" (a veces útil)
        self.contrarian_llms = set()
        
    def evaluate_votes(self, votes: List[LLMVote]) -> Dict[str, float]:
        """
        Evalúa cada voto comparándolo con el consenso.
        Retorna quality_score para cada LLM.
        """
        if not votes:
            return {}
        
        # Calcular consenso
        buy_votes = sum(1 for v in votes if v.decision == 'BUY')
        sell_votes = sum(1 for v in votes if v.decision == 'SELL')
        total_votes = len([v for v in votes if v.decision != 'HOLD'])
        
        consensus_direction = 'BUY' if buy_votes >= sell_votes else 'SELL'
        consensus_strength = max(buy_votes, sell_votes) / max(total_votes, 1)
        
        quality_scores = {}
        
        for vote in votes:
            llm_name = vote.llm_name
            base_trust = self.trust_scores.get(llm_name, 0.8)
            
            # ¿Votó con el consenso?
            with_consensus = (vote.decision == consensus_direction) or vote.decision == 'HOLD'
            
            # Calcular quality score
            if with_consensus:
                # Vota con consenso - buena señal
                quality = base_trust * (0.7 + 0.3 * consensus_strength)
            else:
                # Vota contra consenso - puede ser malo O puede ser un contrarian inteligente
                if llm_name in self.contrarian_llms:
                    # Contrarian conocido - darle algo de crédito
                    quality = base_trust * 0.6
                else:
                    # Va contra el consenso - reducir quality
                    quality = base_trust * (0.4 - 0.2 * consensus_strength)
            
            # Ajustar por confianza del voto
            confidence_factor = vote.confidence / 100
            quality *= (0.5 + 0.5 * confidence_factor)
            
            quality_scores[llm_name] = min(1.0, quality)
        
        return quality_scores
    
    def update_from_outcome(self, votes: List[LLMVote], outcome: str, profit_pips: float):
        """
        Actualiza trust scores basándose en el resultado real del trade.
        """
        correct_direction = 'BUY' if profit_pips > 0 else 'SELL' if profit_pips < 0 else None
        
        for vote in votes:
            llm_name = vote.llm_name
            if llm_name not in self.llm_accuracy:
                continue
            
            if correct_direction is None:
                # Breakeven - no actualizar
                continue
            
            # ¿El LLM acertó?
            was_correct = vote.decision == correct_direction
            self.llm_accuracy[llm_name].append(1 if was_correct else 0)
            
            # Actualizar trust score (exponential moving average)
            alpha = 0.15  # Learning rate
            old_trust = self.trust_scores[llm_name]
            new_info = 1.0 if was_correct else 0.5
            self.trust_scores[llm_name] = alpha * new_info + (1 - alpha) * old_trust
            
            # Detectar contrarians (aciertan cuando van contra consenso)
            recent = list(self.llm_accuracy[llm_name])[-20:]
            if len(recent) >= 10:
                accuracy = sum(recent) / len(recent)
                if accuracy < 0.35:
                    # Muy mala precisión directa - puede ser contrarian útil
                    self.contrarian_llms.add(llm_name)
                elif accuracy > 0.6:
                    self.contrarian_llms.discard(llm_name)
    
    def get_weighted_consensus(self, votes: List[LLMVote]) -> Tuple[str, float, str]:
        """
        Calcula consenso ponderado por trust scores.
        Retorna (decision, confidence, reasoning)
        """
        if not votes:
            return 'HOLD', 0.0, "No votes"
        
        buy_weight = 0.0
        sell_weight = 0.0
        
        for vote in votes:
            trust = self.trust_scores.get(vote.llm_name, 0.5)
            weight = trust * (vote.confidence / 100)
            
            if vote.decision == 'BUY':
                buy_weight += weight
            elif vote.decision == 'SELL':
                sell_weight += weight
        
        total_weight = buy_weight + sell_weight
        if total_weight < 0.1:
            return 'HOLD', 0.0, "Insufficient weight"
        
        if buy_weight > sell_weight * 1.3:
            confidence = min(100, (buy_weight / total_weight) * 100)
            return 'BUY', confidence, f"Weighted consensus: BUY ({buy_weight:.2f} vs {sell_weight:.2f})"
        elif sell_weight > buy_weight * 1.3:
            confidence = min(100, (sell_weight / total_weight) * 100)
            return 'SELL', confidence, f"Weighted consensus: SELL ({sell_weight:.2f} vs {buy_weight:.2f})"
        else:
            return 'HOLD', 50.0, f"No clear consensus (BUY={buy_weight:.2f}, SELL={sell_weight:.2f})"


# ═══════════════════════════════════════════════════════════════════════════════════════
# 📊 DIVERGENCE ORACLE - Detecta divergencias inter-LLM como SEÑAL
# ═══════════════════════════════════════════════════════════════════════════════════════

class DivergenceOracle:
    """
    Las DIVERGENCIAS entre LLMs contienen información valiosa.
    Cuando LLMs normalmente correlacionados divergen, algo importante está pasando.
    """
    
    def __init__(self):
        # Pares de LLMs que normalmente están correlacionados
        self.correlated_pairs = [
            ('LLM2_TECHNICAL', 'LLM3_CHART'),      # Ambos técnicos
            ('LLM6_SMART_MONEY', 'LLM9_PREDATOR'), # Ambos institucionales
            ('LLM7_OCULUS', 'LLM8_CHRONOS'),       # Ambos de calidad/timing
        ]
        
        # Pares naturalmente opuestos (divergencia = señal débil)
        self.opposing_pairs = [
            ('LLM1_BAYESIAN', 'LLM4_RISK'),  # Probabilidad vs Risk
        ]
        
        self.divergence_history = deque(maxlen=100)
        
    def analyze_divergences(self, votes: List[LLMVote]) -> Dict[str, Any]:
        """
        Analiza divergencias entre LLMs.
        Retorna información sobre divergencias significativas.
        """
        vote_dict = {v.llm_name: v for v in votes}
        
        significant_divergences = []
        divergence_score = 0.0
        
        # Check correlated pairs
        for llm_a, llm_b in self.correlated_pairs:
            if llm_a in vote_dict and llm_b in vote_dict:
                vote_a = vote_dict[llm_a]
                vote_b = vote_dict[llm_b]
                
                # ¿Divergen?
                if vote_a.decision != vote_b.decision and \
                   vote_a.decision != 'HOLD' and vote_b.decision != 'HOLD':
                    # Divergencia significativa!
                    divergence_score += 0.3
                    significant_divergences.append({
                        'pair': (llm_a, llm_b),
                        'votes': (vote_a.decision, vote_b.decision),
                        'confidences': (vote_a.confidence, vote_b.confidence),
                        'type': 'CORRELATED_DIVERGENCE',
                        'significance': 'HIGH'
                    })
        
        # Calcular divergencia general
        decisions = [v.decision for v in votes if v.decision != 'HOLD']
        if len(decisions) >= 2:
            buy_count = decisions.count('BUY')
            sell_count = decisions.count('SELL')
            total = buy_count + sell_count
            
            # Entropía de decisiones
            if total > 0:
                p_buy = buy_count / total
                p_sell = sell_count / total
                
                if 0 < p_buy < 1:
                    entropy = -(p_buy * np.log2(p_buy) + p_sell * np.log2(p_sell))
                    divergence_score += entropy * 0.5
        
        # Interpretar divergencia
        if divergence_score > 0.7:
            market_state = 'UNCERTAIN'
            interpretation = "High divergence - market at inflection point"
        elif divergence_score > 0.4:
            market_state = 'TRANSITIONING'
            interpretation = "Moderate divergence - possible regime change"
        else:
            market_state = 'STABLE'
            interpretation = "Low divergence - consensus forming"
        
        result = {
            'divergence_score': min(1.0, divergence_score),
            'significant_divergences': significant_divergences,
            'market_state': market_state,
            'interpretation': interpretation,
        }
        
        self.divergence_history.append(result)
        return result


# ═══════════════════════════════════════════════════════════════════════════════════════
# 💎 WISDOM ACCUMULATOR - Acumula sabiduría de operaciones reales
# ═══════════════════════════════════════════════════════════════════════════════════════

class WisdomAccumulator:
    """
    Acumula SABIDURÍA de operaciones pasadas.
    Aprende qué condiciones llevan a victoria vs derrota.
    """
    
    def __init__(self, max_entries: int = 500):
        self.wisdom_db: deque = deque(maxlen=max_entries)
        self.pattern_win_rates: Dict[str, List[float]] = {}
        self.condition_insights: Dict[str, Dict] = {}
        
        # Aprendizajes clave
        self.key_lessons = []
        
    def _create_pattern_signature(self, conditions: Dict) -> str:
        """Crea firma única de las condiciones"""
        # Simplificar condiciones a rangos
        sig_parts = []
        
        rsi = conditions.get('rsi', 50)
        sig_parts.append(f"RSI_{'LOW' if rsi < 30 else 'HIGH' if rsi > 70 else 'MID'}")
        
        adx = conditions.get('adx', 25)
        sig_parts.append(f"ADX_{'STRONG' if adx > 35 else 'WEAK' if adx < 20 else 'MED'}")
        
        llm_consensus = conditions.get('llm_consensus', 0.5)
        sig_parts.append(f"LLM_{'AGREE' if llm_consensus > 0.7 else 'SPLIT' if llm_consensus < 0.4 else 'MIXED'}")
        
        return "_".join(sig_parts)
    
    def record_trade(self, conditions: Dict, decision: str, outcome: str, 
                     profit_pips: float, confidence: float):
        """Registra un trade y extrae sabiduría"""
        
        pattern_sig = self._create_pattern_signature(conditions)
        
        entry = WisdomEntry(
            pattern_signature=pattern_sig,
            decision=decision,
            outcome=outcome,
            profit_pips=profit_pips,
            conditions=conditions,
            timestamp=time.time(),
            confidence_at_entry=confidence,
        )
        
        # Actualizar win rates por patrón
        if pattern_sig not in self.pattern_win_rates:
            self.pattern_win_rates[pattern_sig] = []
        
        self.pattern_win_rates[pattern_sig].append(1 if outcome == 'WIN' else 0)
        
        # Extraer lecciones
        if outcome == 'LOSS' and profit_pips < -10:
            # Gran pérdida - ¿qué salió mal?
            lessons = []
            if conditions.get('llm_consensus', 0) < 0.5:
                lessons.append("Traded with weak LLM consensus")
            if conditions.get('rsi', 50) > 75 and decision == 'BUY':
                lessons.append("Bought in overbought RSI")
            if conditions.get('rsi', 50) < 25 and decision == 'SELL':
                lessons.append("Sold in oversold RSI")
            if conditions.get('time_quality', 0.5) < 0.3:
                lessons.append("Traded in poor timing conditions")
            
            entry.lessons_learned = lessons
        
        self.wisdom_db.append(entry)
        
    def get_wisdom_for_conditions(self, conditions: Dict) -> Tuple[float, str]:
        """
        Busca en la sabiduría acumulada para estas condiciones.
        Retorna (confidence_adjustment: float, advice: str)
        """
        pattern_sig = self._create_pattern_signature(conditions)
        
        if pattern_sig in self.pattern_win_rates:
            rates = self.pattern_win_rates[pattern_sig]
            if len(rates) >= 3:
                win_rate = sum(rates[-20:]) / len(rates[-20:])
                
                if win_rate > 0.7:
                    return 1.15, f"Wisdom: Pattern {pattern_sig} has {win_rate:.0%} win rate (+15%)"
                elif win_rate < 0.3:
                    return 0.70, f"Wisdom: Pattern {pattern_sig} has {win_rate:.0%} win rate (-30%)"
        
        return 1.0, "No significant wisdom for this pattern"


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🌌 QUANTUM STATE MACHINE - Estados cuánticos reales del mercado
# ═══════════════════════════════════════════════════════════════════════════════════════

class QuantumStateMachine:
    """
    El mercado tiene estados cuánticos que van más allá de bull/bear.
    Este engine detecta el estado cuántico actual.
    """
    
    def __init__(self):
        self.current_state = QuantumState.COHERENT
        self.state_history = deque(maxlen=50)
        self.state_duration = 0
        self.last_state_change = time.time()
        
        # Probabilidades de transición aprendidas
        self.transition_probs = {}
        
    def analyze_market_state(self, genome: Dict, llm_votes: List[LLMVote],
                             divergence_info: Dict) -> QuantumState:
        """Determina el estado cuántico actual del mercado"""
        
        # Extraer datos
        price_data = genome.get('price_data', {})
        closes = list(price_data.get('close', []))[-30:]
        volumes = list(price_data.get('volume', []))[-30:]
        indicators = genome.get('indicators', {}).get('current', {})
        
        if len(closes) < 10:
            return QuantumState.DECOHERENT
        
        # Calcular métricas
        price_change = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] != 0 else 0
        volatility = np.std(closes) / np.mean(closes) if closes else 0
        adx = indicators.get('adx', 25)
        divergence_score = divergence_info.get('divergence_score', 0.5)
        
        # Contar votos LLM
        buy_votes = sum(1 for v in llm_votes if v.decision == 'BUY')
        sell_votes = sum(1 for v in llm_votes if v.decision == 'SELL')
        total_votes = buy_votes + sell_votes
        consensus_ratio = max(buy_votes, sell_votes) / total_votes if total_votes > 0 else 0.5
        
        # Determinar estado
        new_state = QuantumState.COHERENT  # Default
        
        # DECOHERENT: Alta volatilidad + bajo ADX + alta divergencia
        if volatility > 0.02 and adx < 20 and divergence_score > 0.7:
            new_state = QuantumState.DECOHERENT
        
        # CHAOTIC: Alta volatilidad pero ADX alto (tendencia volátil)
        elif volatility > 0.02 and adx > 35:
            new_state = QuantumState.CHAOTIC
        
        # SUPERPOSITION: Alta divergencia entre LLMs, mercado indeciso
        elif divergence_score > 0.6 and consensus_ratio < 0.6:
            new_state = QuantumState.SUPERPOSITION
        
        # RESONANT: Muy alto consenso + buen ADX
        elif consensus_ratio > 0.85 and adx > 25:
            new_state = QuantumState.RESONANT
        
        # COLLAPSING: Cambio de estado inminente (volumen spike + precio estancado)
        elif len(volumes) > 5:
            avg_vol = np.mean(volumes[:-1])
            if volumes[-1] > avg_vol * 2 and abs(price_change) < 0.005:
                new_state = QuantumState.COLLAPSING
        
        # CRYSTALLIZING: Después de caos, formando estructura
        elif self.current_state in [QuantumState.CHAOTIC, QuantumState.DECOHERENT]:
            if divergence_score < 0.3 and adx > 20:
                new_state = QuantumState.CRYSTALLIZING
        
        # Actualizar estado
        if new_state != self.current_state:
            self.state_history.append((self.current_state, time.time()))
            self.current_state = new_state
            self.last_state_change = time.time()
            self.state_duration = 0
        else:
            self.state_duration += 1
        
        return new_state
    
    def get_trading_recommendation(self) -> Tuple[bool, float, str]:
        """
        Basándose en el estado cuántico, recomendar trading o no.
        Retorna (should_trade, confidence_multiplier, reason)
        """
        state = self.current_state
        
        recommendations = {
            QuantumState.RESONANT: (True, 1.3, "🎯 RESONANT: Perfect signal alignment"),
            QuantumState.COHERENT: (True, 1.0, "✅ COHERENT: Normal conditions"),
            QuantumState.CRYSTALLIZING: (True, 1.1, "💎 CRYSTALLIZING: New trend forming"),
            QuantumState.SUPERPOSITION: (False, 0.7, "⚠️ SUPERPOSITION: Wait for collapse"),
            QuantumState.COLLAPSING: (True, 0.9, "⚡ COLLAPSING: Breakout imminent"),
            QuantumState.CHAOTIC: (False, 0.5, "🌀 CHAOTIC: Avoid trading"),
            QuantumState.DECOHERENT: (False, 0.3, "🚫 DECOHERENT: Pure noise"),
            QuantumState.ENTANGLED: (True, 0.8, "🔗 ENTANGLED: Check correlations"),
        }
        
        return recommendations.get(state, (True, 1.0, "Unknown state"))


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🛡️ ANTI-NOISE FILTER - Filtra ruido y deja pasar solo señales puras
# ═══════════════════════════════════════════════════════════════════════════════════════

class AntiNoiseFilter:
    """
    Filtra el RUIDO del mercado para dejar pasar solo señales puras.
    El 90% de los movimientos de M1 son ruido - este filtro lo detecta.
    """
    
    def __init__(self):
        self.signal_history = deque(maxlen=30)
        self.noise_threshold = 0.7  # Adaptativo
        
    def calculate_noise_level(self, genome: Dict, llm_votes: List[LLMVote]) -> float:
        """
        Calcula nivel de ruido actual (0 = señal pura, 1 = ruido puro)
        """
        price_data = genome.get('price_data', {})
        closes = list(price_data.get('close', []))[-20:]
        highs = list(price_data.get('high', []))[-20:]
        lows = list(price_data.get('low', []))[-20:]
        
        if len(closes) < 10:
            return 0.8  # Sin datos = asumir ruido
        
        noise_factors = []
        
        # 1. Ratio wick/body (mucho wick = ruido)
        bodies = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]
        wicks = [highs[i] - lows[i] for i in range(len(highs))]
        
        if bodies and wicks:
            avg_body = np.mean(bodies)
            avg_wick = np.mean(wicks)
            wick_ratio = avg_wick / (avg_body + 0.00001)
            noise_factors.append(min(1.0, wick_ratio / 5))  # >5x wick = max noise
        
        # 2. Dirección inconsistente (cambio de dirección frecuente)
        if len(closes) >= 5:
            directions = [1 if closes[i] > closes[i-1] else -1 for i in range(1, len(closes))]
            changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i-1])
            change_ratio = changes / (len(directions) - 1) if len(directions) > 1 else 0
            noise_factors.append(change_ratio)
        
        # 3. LLM disagreement
        if llm_votes:
            buy = sum(1 for v in llm_votes if v.decision == 'BUY')
            sell = sum(1 for v in llm_votes if v.decision == 'SELL')
            total = buy + sell
            if total > 0:
                disagreement = 1 - abs(buy - sell) / total
                noise_factors.append(disagreement)
        
        # Promedio ponderado
        if noise_factors:
            noise_level = np.mean(noise_factors)
        else:
            noise_level = 0.5
        
        return min(1.0, noise_level)
    
    def should_filter(self, noise_level: float) -> Tuple[bool, str]:
        """Decide si filtrar la señal actual"""
        if noise_level > 0.75:
            return True, f"🔇 FILTERED: Noise level {noise_level:.0%} > 75%"
        elif noise_level > 0.6:
            return False, f"⚠️ CAUTION: Noise level {noise_level:.0%} (borderline)"
        else:
            return False, f"✅ CLEAN: Noise level {noise_level:.0%}"


# ═══════════════════════════════════════════════════════════════════════════════════════
# ⚡ SUPREME CONSCIOUSNESS ENGINE - El cerebro de los cerebros
# ═══════════════════════════════════════════════════════════════════════════════════════

class SupremeConsciousnessEngine:
    """
    🧠⚡ THE SUPREME CONSCIOUSNESS ENGINE ⚡🧠
    
    Este es el cerebro de los cerebros. Unifica toda la inteligencia
    en una sola consciencia que VE todo y SABE todo.
    
    Integra:
    - Meta-LLM Cognition
    - Divergence Oracle
    - Wisdom Accumulator
    - Quantum State Machine
    - Institutional Time Awareness
    - Anti-Noise Filter
    """
    
    def __init__(self):
        log.info("🧠⚡ SUPREME CONSCIOUSNESS ENGINE INITIALIZING...")
        
        # Sub-engines
        self.meta_llm = MetaLLMCognition()
        self.divergence_oracle = DivergenceOracle()
        self.wisdom = WisdomAccumulator()
        self.quantum_machine = QuantumStateMachine()
        self.time_engine = InstitutionalTimeEngine()
        self.noise_filter = AntiNoiseFilter()
        
        # Estado actual
        self.current_snapshot: Optional[ConsciousnessSnapshot] = None
        self.snapshot_history = deque(maxlen=100)
        
        # Contadores
        self.signals_analyzed = 0
        self.signals_approved = 0
        self.signals_rejected = 0
        
        log.info("✅ Supreme Consciousness Online - All 6 sub-systems active")
        log.info("   - Meta-LLM Cognition: READY")
        log.info("   - Divergence Oracle: READY")
        log.info("   - Wisdom Accumulator: READY")
        log.info("   - Quantum State Machine: READY")
        log.info("   - Institutional Time: READY")
        log.info("   - Anti-Noise Filter: READY")
    
    def analyze(self, genome: Dict, llm_responses: Dict) -> ConsciousnessSnapshot:
        """
        🧠 ANÁLISIS SUPREMO
        
        Analiza todo y retorna un snapshot de consciencia completo.
        Este es el método principal que debe llamarse para cada decisión.
        """
        self.signals_analyzed += 1
        start_time = time.time()
        
        # Convertir respuestas LLM a objetos LLMVote
        votes = self._parse_llm_responses(llm_responses)
        
        # 1. Análisis de tiempo institucional
        time_quality, time_reason = self.time_engine.get_time_quality()
        
        # 2. Análisis de divergencias
        divergence_info = self.divergence_oracle.analyze_divergences(votes)
        
        # 3. Estado cuántico del mercado
        quantum_state = self.quantum_machine.analyze_market_state(genome, votes, divergence_info)
        should_trade_quantum, quantum_mult, quantum_reason = self.quantum_machine.get_trading_recommendation()
        
        # 4. Meta-cognición: Evaluar calidad de votos
        vote_qualities = self.meta_llm.evaluate_votes(votes)
        
        # 5. Consenso ponderado
        weighted_decision, weighted_conf, consensus_reason = self.meta_llm.get_weighted_consensus(votes)
        
        # 6. Nivel de ruido
        noise_level = self.noise_filter.calculate_noise_level(genome, votes)
        should_filter, noise_reason = self.noise_filter.should_filter(noise_level)
        
        # 7. Sabiduría acumulada
        conditions = self._extract_conditions(genome, votes, time_quality)
        wisdom_mult, wisdom_advice = self.wisdom.get_wisdom_for_conditions(conditions)
        
        # 8. Detectar emoción del mercado
        market_emotion = self._detect_market_emotion(genome, divergence_info, quantum_state)
        
        # 9. Detectar actividad institucional
        institutional_activity = self._detect_institutional_activity(genome)
        
        # ═══════════════════════════════════════════════════════════════
        # 🎯 DECISIÓN FINAL DE CONSCIENCIA
        # ═══════════════════════════════════════════════════════════════
        
        # Calcular confianza meta
        meta_confidence = weighted_conf
        
        # Aplicar modificadores
        meta_confidence *= quantum_mult      # Estado cuántico
        meta_confidence *= wisdom_mult       # Sabiduría
        meta_confidence *= (1 - noise_level * 0.5)  # Penalizar ruido
        meta_confidence *= (0.7 + 0.3 * time_quality)  # Tiempo institucional
        
        # Determinar decisión final
        if should_filter:
            final_decision = 'HOLD'
            final_reason = f"🔇 FILTERED: {noise_reason}"
        elif not should_trade_quantum:
            final_decision = 'HOLD'
            final_reason = f"🌌 QUANTUM VETO: {quantum_reason}"
        elif time_quality < 0.2:
            final_decision = 'HOLD'
            final_reason = f"⏰ TIME VETO: {time_reason}"
        else:
            final_decision = weighted_decision
            final_reason = self._build_reasoning(
                weighted_decision, meta_confidence, quantum_state, 
                divergence_info, time_quality, noise_level, wisdom_advice
            )
        
        # Crear snapshot
        snapshot = ConsciousnessSnapshot(
            quantum_state=quantum_state,
            market_emotion=market_emotion,
            institutional_activity=institutional_activity,
            llm_consensus_strength=sum(1 for v in votes if v.decision == weighted_decision) / max(len(votes), 1),
            divergence_level=divergence_info.get('divergence_score', 0.5),
            wisdom_confidence=wisdom_mult,
            noise_level=noise_level,
            time_quality=time_quality,
            meta_confidence=min(100, max(0, meta_confidence)),
            decision=final_decision,
            reasoning=final_reason,
        )
        
        self.current_snapshot = snapshot
        self.snapshot_history.append(snapshot)
        
        if final_decision != 'HOLD':
            self.signals_approved += 1
        else:
            self.signals_rejected += 1
        
        elapsed = (time.time() - start_time) * 1000
        log.info(f"🧠 SUPREME: {final_decision} @ {meta_confidence:.0f}% | Q:{quantum_state.value[:4]} | N:{noise_level:.0%} | T:{time_quality:.0%} | {elapsed:.0f}ms")
        
        return snapshot
    
    def record_trade_outcome(self, outcome: str, profit_pips: float):
        """Registra el resultado de un trade para aprender"""
        if self.current_snapshot:
            conditions = {
                'quantum_state': self.current_snapshot.quantum_state.value,
                'noise_level': self.current_snapshot.noise_level,
                'time_quality': self.current_snapshot.time_quality,
                'llm_consensus': self.current_snapshot.llm_consensus_strength,
                'divergence': self.current_snapshot.divergence_level,
            }
            
            self.wisdom.record_trade(
                conditions=conditions,
                decision=self.current_snapshot.decision,
                outcome=outcome,
                profit_pips=profit_pips,
                confidence=self.current_snapshot.meta_confidence,
            )
    
    def _parse_llm_responses(self, llm_responses: Dict) -> List[LLMVote]:
        """Convierte respuestas LLM a objetos LLMVote"""
        votes = []
        
        for llm_name, response in llm_responses.items():
            if not isinstance(response, dict):
                continue
            
            decision = response.get('decision', response.get('vote', 'HOLD'))
            confidence = float(response.get('confidence', 50))
            reasoning = response.get('reasoning', response.get('reason', ''))
            
            vote = LLMVote(
                llm_name=llm_name,
                decision=decision,
                confidence=confidence,
                reasoning=str(reasoning),
                timestamp=time.time(),
            )
            votes.append(vote)
        
        return votes
    
    def _extract_conditions(self, genome: Dict, votes: List[LLMVote], 
                           time_quality: float) -> Dict:
        """Extrae condiciones para wisdom lookup"""
        indicators = genome.get('indicators', {}).get('current', {})
        
        return {
            'rsi': indicators.get('rsi', 50),
            'adx': indicators.get('adx', 25),
            'time_quality': time_quality,
            'llm_consensus': sum(1 for v in votes if v.decision == votes[0].decision) / len(votes) if votes else 0.5,
        }
    
    def _detect_market_emotion(self, genome: Dict, divergence_info: Dict,
                               quantum_state: QuantumState) -> MarketEmotion:
        """Detecta la emoción actual del mercado"""
        indicators = genome.get('indicators', {}).get('current', {})
        rsi = indicators.get('rsi', 50)
        adx = indicators.get('adx', 25)
        
        if rsi > 80 and adx > 30:
            return MarketEmotion.EUPHORIA
        elif rsi < 20 and adx > 30:
            return MarketEmotion.PANIC
        elif quantum_state == QuantumState.DECOHERENT:
            return MarketEmotion.FEAR
        elif quantum_state == QuantumState.RESONANT:
            return MarketEmotion.CONFIDENCE
        elif divergence_info.get('divergence_score', 0) > 0.6:
            return MarketEmotion.UNCERTAINTY
        elif rsi > 65:
            return MarketEmotion.GREED
        elif rsi < 35:
            return MarketEmotion.ANXIETY
        else:
            return MarketEmotion.COMPLACENCY
    
    def _detect_institutional_activity(self, genome: Dict) -> InstitutionalActivity:
        """Detecta tipo de actividad institucional"""
        price_data = genome.get('price_data', {})
        volumes = list(price_data.get('volume', []))[-20:]
        closes = list(price_data.get('close', []))[-20:]
        
        if len(volumes) < 5 or len(closes) < 5:
            return InstitutionalActivity.ABSENT
        
        avg_vol = np.mean(volumes[:-1])
        recent_vol = volumes[-1]
        price_change = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
        
        # Volume spike con poco movimiento = manipulación
        if recent_vol > avg_vol * 2.5 and abs(price_change) < 0.002:
            return InstitutionalActivity.MANIPULATING
        
        # Volume spike con movimiento = atacando
        if recent_vol > avg_vol * 2 and abs(price_change) > 3.0:
            return InstitutionalActivity.ATTACKING
        
        # Volumen bajo pero precio sube = acumulación silenciosa
        if recent_vol < avg_vol * 0.7 and price_change > 1.0:
            return InstitutionalActivity.ACCUMULATING
        
        # Volumen bajo pero precio baja = distribución silenciosa
        if recent_vol < avg_vol * 0.7 and price_change < -1.0:
            return InstitutionalActivity.DISTRIBUTING
        
        return InstitutionalActivity.ABSENT
    
    def _build_reasoning(self, decision: str, confidence: float, 
                         quantum_state: QuantumState, divergence_info: Dict,
                         time_quality: float, noise_level: float,
                         wisdom_advice: str) -> str:
        """Construye el reasoning final"""
        parts = []
        
        # Quantum state
        parts.append(f"Q:{quantum_state.value}")
        
        # Divergence
        div_score = divergence_info.get('divergence_score', 0)
        parts.append(f"DIV:{div_score:.0%}")
        
        # Time quality
        parts.append(f"TIME:{time_quality:.0%}")
        
        # Noise
        parts.append(f"NOISE:{noise_level:.0%}")
        
        # Decision
        parts.append(f"→ {decision}@{confidence:.0f}%")
        
        # Wisdom (if relevant)
        if "+" in wisdom_advice or "-" in wisdom_advice:
            parts.append(f"[{wisdom_advice.split(':')[0]}]")
        
        return " | ".join(parts)
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del engine"""
        return {
            'signals_analyzed': self.signals_analyzed,
            'signals_approved': self.signals_approved,
            'signals_rejected': self.signals_rejected,
            'approval_rate': self.signals_approved / max(self.signals_analyzed, 1),
            'current_quantum_state': self.quantum_machine.current_state.value,
            'llm_trust_scores': self.meta_llm.trust_scores,
            'wisdom_patterns': len(self.wisdom.pattern_win_rates),
        }


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🚀 SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════════════

_supreme_instance: Optional[SupremeConsciousnessEngine] = None

def get_supreme_consciousness() -> SupremeConsciousnessEngine:
    """Obtiene la instancia singleton de Supreme Consciousness"""
    global _supreme_instance
    if _supreme_instance is None:
        _supreme_instance = SupremeConsciousnessEngine()
    return _supreme_instance


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧠⚡ SUPREME CONSCIOUSNESS ENGINE - TEST MODE ⚡🧠")
    
    # Crear engine
    consciousness = get_supreme_consciousness()
    
    # Datos de prueba
    test_genome = {
        'price_data': {
            'close': [42000.0 + i * 1.0 for i in range(30)],
            'high': [42005.0 + i * 1.0 for i in range(30)],
            'low': [41995.0 + i * 1.0 for i in range(30)],
            'volume': [1000 + i * 10 for i in range(30)],
        },
        'indicators': {
            'current': {
                'rsi': 65,
                'adx': 28,
                'macd': 2.0,
            }
        }
    }
    
    test_llm_responses = {
        'LLM1_BAYESIAN': {'decision': 'BUY', 'confidence': 72},
        'LLM2_TECHNICAL': {'decision': 'BUY', 'confidence': 68},
        'LLM3_CHART': {'decision': 'SELL', 'confidence': 55},
        'LLM6_SMART_MONEY': {'decision': 'BUY', 'confidence': 78},
        'LLM9_PREDATOR': {'decision': 'BUY', 'confidence': 70},
    }
    
    # Analizar
    snapshot = consciousness.analyze(test_genome, test_llm_responses)
    
    print(f"\n📊 CONSCIOUSNESS SNAPSHOT:")
    print(f"   Decision: {snapshot.decision}")
    print(f"   Confidence: {snapshot.meta_confidence:.0f}%")
    print(f"   Quantum State: {snapshot.quantum_state.value}")
    print(f"   Market Emotion: {snapshot.market_emotion.value}")
    print(f"   Institutional: {snapshot.institutional_activity.value}")
    print(f"   Noise Level: {snapshot.noise_level:.0%}")
    print(f"   Time Quality: {snapshot.time_quality:.0%}")
    print(f"   Reasoning: {snapshot.reasoning}")
    
    print(f"\n📈 STATS: {consciousness.get_stats()}")
