#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM LEARNING FEEDBACK SYSTEM
Enseña a los 4 LLMs cuándo sus decisiones fueron correctas o incorrectas.

Los LLM aprenden a través de:
1. Pattern recognition: Qué patrones llevan a ganancias
2. Context memory: Recordar mercados similares que salieron bien/mal
3. Confidence calibration: Ajustar confianza según histórico de aciertos
4. Sweep detection learning: Mejorar en detectar sweeps válidos
"""

import json
import logging
from collections import deque, defaultdict
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger("LLMFeedback")

class LLMMemoryBank:
    """Memoria episódica para que los LLMs aprendan de cada trade"""
    
    def __init__(self, max_episodes=500):
        """
        Almacena episodios de trading para que los LLMs reconozcan patrones.
        
        Un episodio = contexto → decisión → resultado
        """
        self.episodes = deque(maxlen=max_episodes)
        self.success_patterns = defaultdict(int)
        self.failure_patterns = defaultdict(int)
        self.llm_accuracy = {'llm1': 0.5, 'llm2': 0.5, 'llm3': 0.5, 'llm4': 0.5}
        self.trades_by_llm = {'llm1': [], 'llm2': [], 'llm3': [], 'llm4': []}
        self.pattern_confidence = {}
        
    def record_episode(self, context, llm_decisions, trade_result):
        """
        Registra un episodio (trade) para aprendizaje.
        
        Args:
            context: dict con {'rsi': 25, 'trend': 'UP', 'patterns': [...], 'volatility': 'LOW'}
            llm_decisions: dict con {'llm1': 'BUY', 'llm2': 'BUY', ...}
            trade_result: dict con {'pnl': 45.23, 'exit_reason': 'TP', 'duration': 5}
        """
        episode = {
            'timestamp': datetime.now(),
            'context': context,
            'llm_decisions': llm_decisions,
            'result': trade_result,
            'was_winning': trade_result.get('pnl', 0) > 0,
            'pnl': trade_result.get('pnl', 0)
        }
        
        self.episodes.append(episode)
        
        # Update success/failure patterns
        context_pattern = self._pattern_from_context(context)
        if episode['was_winning']:
            self.success_patterns[context_pattern] += 1
        else:
            self.failure_patterns[context_pattern] += 1
        
        # Update LLM accuracy
        for llm_name, llm_decision in llm_decisions.items():
            self.trades_by_llm[llm_name].append({
                'decision': llm_decision,
                'was_winning': episode['was_winning'],
                'pnl': episode['pnl']
            })
            
            # Calculate win rate for this LLM
            trades = self.trades_by_llm[llm_name]
            if len(trades) > 0:
                wins = sum(1 for t in trades if t['was_winning'])
                self.llm_accuracy[llm_name] = wins / len(trades)
        
        return episode
    
    def _pattern_from_context(self, context):
        """Convierte contexto a patrón identificable para aprendizaje"""
        pattern_elements = []
        
        # RSI range
        rsi = context.get('rsi', 50)
        if rsi < 30:
            pattern_elements.append('RSI_OVERSOLD')
        elif rsi > 70:
            pattern_elements.append('RSI_OVERBOUGHT')
        else:
            pattern_elements.append('RSI_NORMAL')
        
        # Trend
        trend = context.get('trend', 'UNKNOWN')
        pattern_elements.append(f'TREND_{trend}')
        
        # Volatility
        vol = context.get('volatility_regime', 'NORMAL')
        pattern_elements.append(f'VOL_{vol}')
        
        # Patterns detected
        patterns = context.get('patterns_detected', [])
        if patterns:
            pattern_elements.append('PATTERNS_YES')
        else:
            pattern_elements.append('PATTERNS_NO')
        
        return '_'.join(pattern_elements)
    
    def get_best_context_for_pattern(self, pattern_type):
        """
        Retorna los contextos más exitosos para un patrón dado.
        
        Sirve para que los LLMs sepan cuál es la mejor configuración.
        Por ej: "ENGULFING pattern funciona mejor con RSI < 30 + UPTREND + LOW VOL"
        """
        contexts_for_pattern = []
        
        for episode in self.episodes:
            if pattern_type in episode['context'].get('patterns_detected', []):
                contexts_for_pattern.append({
                    'context': episode['context'],
                    'was_winning': episode['was_winning'],
                    'pnl': episode['pnl']
                })
        
        if not contexts_for_pattern:
            return None
        
        # Sort by PnL descending
        contexts_for_pattern.sort(key=lambda x: x['pnl'], reverse=True)
        
        # Return top 3
        return contexts_for_pattern[:3]
    
    def get_llm_report(self, llm_name):
        """Reporte de desempeño para un LLM específico"""
        trades = self.trades_by_llm.get(llm_name, [])
        
        if not trades:
            return {'llm': llm_name, 'trades': 0, 'accuracy': 0.5}
        
        wins = sum(1 for t in trades if t['was_winning'])
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / len(trades) if trades else 0
        
        return {
            'llm': llm_name,
            'trades': len(trades),
            'accuracy': self.llm_accuracy[llm_name],
            'win_rate': f"{(wins / len(trades) * 100):.1f}%",
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl
        }


class LLMSweepDetectionLearner:
    """Enseña a los LLMs a detectar sweeps válidos vs falsas alarmas"""
    
    def __init__(self):
        self.sweep_detections = deque(maxlen=200)
        self.true_positives = 0  # LLM detectó sweep y resultó en ganancia
        self.false_positives = 0  # LLM detectó sweep pero fue pérdida
        self.true_negatives = 0  # LLM no detectó sweep y fue correcto
        self.false_negatives = 0  # LLM no detectó sweep pero hay swing
        self.sweep_accuracy = 0.5
        
    def record_sweep_detection(self, llm_detected_sweep, actual_sweep_occurred, trade_pnl):
        """
        Registra si la detección de sweep fue correcta.
        
        Args:
            llm_detected_sweep: bool - LLM said there's a sweep
            actual_sweep_occurred: bool - Did market actually sweep?
            trade_pnl: float - Did trade make/lose money?
        """
        detection = {
            'timestamp': datetime.now(),
            'llm_detected': llm_detected_sweep,
            'actual': actual_sweep_occurred,
            'profitable': trade_pnl > 0,
            'pnl': trade_pnl
        }
        self.sweep_detections.append(detection)
        
        # Update confusion matrix
        if llm_detected_sweep and actual_sweep_occurred:
            if trade_pnl > 0:
                self.true_positives += 1  # Correct sweep detection + profit
        elif llm_detected_sweep and not actual_sweep_occurred:
            self.false_positives += 1  # False alarm
        elif not llm_detected_sweep and not actual_sweep_occurred:
            if trade_pnl > 0:
                self.true_negatives += 1  # Correctly skipped false pattern
        else:  # No detection but there was a sweep
            self.false_negatives += 1  # Missed opportunity
        
        # Recalculate sweep accuracy
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        if total > 0:
            correct = self.true_positives + self.true_negatives
            self.sweep_accuracy = correct / total
        
        return detection
    
    def get_sweep_calibration(self):
        """
        Retorna cómo los LLMs deberían calibrar sus umbrales de sweep detection.
        
        Si hay muchos false_positives → reducir sensibilidad
        Si hay muchos false_negatives → aumentar sensibilidad
        """
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        if total < 10:
            return {'recommendation': 'WAIT', 'reason': 'insufficient_data', 'samples': total}
        
        fp_rate = self.false_positives / max(1, self.false_positives + self.true_positives)
        fn_rate = self.false_negatives / max(1, self.false_negatives + self.true_negatives)
        
        if fp_rate > 0.5:
            return {
                'recommendation': 'REDUCE_SENSITIVITY',
                'reason': f'Too many false positives ({fp_rate:.1%})',
                'action': 'Increase sweep threshold (fewer sweeps accepted)',
                'accuracy': self.sweep_accuracy
            }
        elif fn_rate > 0.5:
            return {
                'recommendation': 'INCREASE_SENSITIVITY',
                'reason': f'Too many false negatives ({fn_rate:.1%})',
                'action': 'Decrease sweep threshold (more sweeps accepted)',
                'accuracy': self.sweep_accuracy
            }
        else:
            return {
                'recommendation': 'BALANCED',
                'reason': f'Sweep detection working well',
                'accuracy': self.sweep_accuracy
            }


class LLMConfidenceCalibrator:
    """Enseña a los LLMs a ser más precisos sobre su confianza"""
    
    def __init__(self):
        self.confidence_buckets = defaultdict(lambda: {'correct': 0, 'incorrect': 0})
        self.calibration_curve = {}
        
    def record_confidence(self, llm_confidence, was_correct):
        """
        Registra si un LLM que dijo estar X% confiante realmente acertó.
        
        Esto calibra la confianza reportada vs confianza real.
        """
        # Bucket confidence into 10% ranges: 50-60%, 60-70%, etc
        bucket = int(llm_confidence / 10) * 10
        bucket_label = f"{bucket}-{bucket+10}"
        
        if was_correct:
            self.confidence_buckets[bucket_label]['correct'] += 1
        else:
            self.confidence_buckets[bucket_label]['incorrect'] += 1
    
    def get_calibration_advice(self):
        """
        Retorna si los LLMs están sobrecconfiados o subeconfiados.
        
        Sobrecconfiado: Dice 80% pero solo acierta 60% de las veces
        Subconfiado: Dice 50% pero acierta 80% de las veces
        """
        advice = {}
        
        for bucket, counts in self.confidence_buckets.items():
            total = counts['correct'] + counts['incorrect']
            if total > 5:
                actual_accuracy = counts['correct'] / total
                # BUG FIX #30: Protect against split() returning empty list
                bucket_parts = bucket.split('-')
                if len(bucket_parts) >= 1 and bucket_parts[0].isdigit():
                    stated_confidence = (int(bucket_parts[0]) + 5) / 100
                else:
                    stated_confidence = 0.5
                
                if actual_accuracy < stated_confidence * 0.8:
                    advice[bucket] = f"OVERCONFIDENT: Says {stated_confidence:.0%} but only correct {actual_accuracy:.0%}"
                elif actual_accuracy > stated_confidence * 1.2:
                    advice[bucket] = f"UNDERCONFIDENT: Says {stated_confidence:.0%} but correct {actual_accuracy:.0%}"
                else:
                    advice[bucket] = f"WELL_CALIBRATED: Says {stated_confidence:.0%}, correct {actual_accuracy:.0%}"
        
        return advice


class LLMPatternLearner:
    """Enseña a los LLMs cuáles patrones funcionan mejor en diferentes contextos"""
    
    def __init__(self):
        self.pattern_statistics = defaultdict(lambda: {
            'successes': 0,
            'failures': 0,
            'total_pnl': 0,
            'contexts': []
        })
        self.best_patterns = []
        self.worst_patterns = []
        
    def record_pattern_outcome(self, pattern_name, context, was_winning, pnl):
        """Registra el resultado de un trade basado en un patrón"""
        stats = self.pattern_statistics[pattern_name]
        
        if was_winning:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        stats['total_pnl'] += pnl
        stats['contexts'].append({'context': context, 'winning': was_winning, 'pnl': pnl})
        
        # Keep only last 50 contexts
        stats['contexts'] = stats['contexts'][-50:]
    
    def get_pattern_success_rate(self, pattern_name):
        """Retorna el win rate para un patrón específico"""
        stats = self.pattern_statistics.get(pattern_name)
        if not stats:
            return 0.5
        
        total = stats['successes'] + stats['failures']
        if total == 0:
            return 0.5
        
        return stats['successes'] / total
    
    def get_best_patterns(self, min_trades=10):
        """Retorna los patrones con mejor track record"""
        best = []
        
        for pattern, stats in self.pattern_statistics.items():
            total = stats['successes'] + stats['failures']
            if total >= min_trades:
                win_rate = stats['successes'] / total
                avg_pnl = stats['total_pnl'] / total
                best.append({
                    'pattern': pattern,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_trades': total
                })
        
        best.sort(key=lambda x: x['win_rate'] * x['avg_pnl'], reverse=True)
        return best[:5]  # Top 5
    
    def get_worst_patterns(self, min_trades=10):
        """Retorna los patrones con peor track record"""
        worst = []
        
        for pattern, stats in self.pattern_statistics.items():
            total = stats['successes'] + stats['failures']
            if total >= min_trades:
                win_rate = stats['successes'] / total
                avg_pnl = stats['total_pnl'] / total
                worst.append({
                    'pattern': pattern,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_trades': total
                })
        
        worst.sort(key=lambda x: x['win_rate'] * x['avg_pnl'])
        return worst[:5]  # Bottom 5


class UnifiedLLMFeedback:
    """
    Sistema unificado de feedback para los 4 LLMs.
    
    Integra:
    - Memory bank (qué aprendió de cada trade)
    - Sweep detector (sweep validation)
    - Confidence calibration (confianza acertada)
    - Pattern learner (patrones que funcionan)
    """
    
    def __init__(self):
        self.memory_bank = LLMMemoryBank()
        self.sweep_learner = LLMSweepDetectionLearner()
        self.confidence_calibrator = LLMConfidenceCalibrator()
        self.pattern_learner = LLMPatternLearner()
        self.logger = logging.getLogger("LLMFeedback")
        self.total_trades_analyzed = 0
        
    def record_trade_outcome(self, llm_decisions, context, patterns_detected, 
                            sweep_detected, trade_pnl, trade_duration):
        """
        Registra el outcome de un trade para feedback de LLMs.
        
        Args:
            llm_decisions: {'llm1': 'BUY', 'llm2': 'SELL', ...}
            context: market context dict
            patterns_detected: list of pattern names
            sweep_detected: bool
            trade_pnl: float
            trade_duration: int (minutes)
        """
        self.total_trades_analyzed += 1
        
        # 1. Memory bank: recordar este trade
        trade_result = {
            'pnl': trade_pnl,
            'duration': trade_duration,
            'exit_reason': 'TP' if trade_pnl > 0 else 'SL',
            'profitable': trade_pnl > 0
        }
        
        episode = self.memory_bank.record_episode(context, llm_decisions, trade_result)
        self.logger.info(f"[LLMMemory] Trade #{self.total_trades_analyzed}: {episode['was_winning']}, PnL={trade_pnl:.2f}")
        
        # 2. Sweep learning: evaluar detección de sweeps
        for llm_name, llm_decision in llm_decisions.items():
            # Asumir que si LLM decidió BUY/SELL, detectó sweep
            llm_detected_sweep = llm_decision in ['BUY', 'SELL']
            self.sweep_learner.record_sweep_detection(llm_detected_sweep, sweep_detected, trade_pnl)
        
        # 3. Pattern learning: qué patrones llevaron a ganancias
        for pattern in patterns_detected:
            self.pattern_learner.record_pattern_outcome(pattern, context, trade_pnl > 0, trade_pnl)
        
        # 4. Confidence calibration: fueron confiados y tuvieron razón?
        # (This would need confidence data from LLMs)
        
        return episode
    
    def get_llm_performance_report(self):
        """Reporte de desempeño de los 4 LLMs"""
        report = {
            'total_trades': self.total_trades_analyzed,
            'llm_reports': {},
            'pattern_insights': {},
            'sweep_calibration': self.sweep_learner.get_sweep_calibration(),
            'best_patterns': self.pattern_learner.get_best_patterns(),
            'worst_patterns': self.pattern_learner.get_worst_patterns()
        }
        
        for llm_name in ['llm1', 'llm2', 'llm3', 'llm4']:
            report['llm_reports'][llm_name] = self.memory_bank.get_llm_report(llm_name)
        
        return report
    
    def generate_learning_prompt_for_llm(self, llm_name):
        """
        Genera un prompt que educa al LLM sobre qué funcionó y qué no.
        
        Esto puede ser enviado al LLM para que "recuerde" en futuros trades.
        """
        llm_report = self.memory_bank.get_llm_report(llm_name)
        best_patterns = self.pattern_learner.get_best_patterns(min_trades=5)
        worst_patterns = self.pattern_learner.get_worst_patterns(min_trades=5)
        sweep_calib = self.sweep_learner.get_sweep_calibration()
        
        prompt = f"""
# {llm_name.upper()} LEARNING FEEDBACK REPORT

## Performance Summary
- Total Trades: {llm_report['trades']}
- Accuracy: {llm_report['accuracy']:.1%}
- Win Rate: {llm_report['win_rate']}
- Total PnL: ${llm_report['total_pnl']:.2f}
- Avg PnL per Trade: ${llm_report['avg_pnl']:.2f}

## Best Performing Patterns
{json.dumps([p for p in best_patterns if p['win_rate'] > 0.6], indent=2)}

## Patterns to Avoid
{json.dumps([p for p in worst_patterns if p['win_rate'] < 0.4], indent=2)}

## Sweep Detection Feedback
{sweep_calib.get('recommendation')}: {sweep_calib.get('reason')}
Current Sweep Detection Accuracy: {sweep_calib.get('accuracy', 0.5):.1%}

## Learning Instructions
1. FOCUS on patterns with > 60% win rate
2. AVOID patterns with < 40% win rate
3. {sweep_calib.get('action', 'Continue current sweep detection')}
4. Be more conservative when {sweep_calib.get('reason', 'the market is uncertain')}
"""
        
        return prompt
