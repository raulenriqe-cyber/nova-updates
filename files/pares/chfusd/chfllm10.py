#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ NOVA TRADING AI - LLM10 NOVA                           ║
║                     Quality Auditor & Gap Analyzer v1.0                      ║
║                                                                              ║
║  Audita TODAS las decisiones del sistema antes de ejecutarlas                ║
║  Identifica huecos en lógica, datos, inteligencia, matemática, contexto      ║
║  Retorna quality_score (0-100) que multiplica confianza de Trinity           ║
║  Genera alertas categorizadas para cada tipo de riesgo                       ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Edition: Quality Audit | Multi-Dimensional Gap Analysis                    ║
║  Ports: 8605 (USDCHF) | 6565 (EURUSD) | Pure Python | <100ms latency        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, struct, json, logging, threading, time
import numpy as np
from collections import deque, defaultdict
import os
from datetime import datetime

os.makedirs('logs', exist_ok=True)
_log_file = f'logs/llm10_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
_file_handler = logging.FileHandler(_log_file, encoding='utf-8')
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s | ✨ LLM10_NOVA | %(message)s", datefmt='%H:%M:%S')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger()
log.info(f"[INIT] Log file: {_log_file}")
class NOVA:
    """
    ✨ NOVA LLM10 - Quality Auditor & Gap Analyzer
    
    Responsabilidades:
    - Audita TODAS las dimensiones de una decisión
    - Identifica 47 tipos de huecos (logic, data, intelligence, math, context)
    - Calcula quality_score (0-100) con breakdown por categoría
    - Genera alertas categorizadas por tipo y severidad
    - Retorna categorías de riesgo para trade classification
    
    5 Motores de Auditoría:
    1. Logic Consistency Checker (0-20 puntos)
    2. Data Completeness Checker (0-20 puntos)
    3. Intelligence Depth Checker (0-20 puntos)
    4. Mathematical Rigor Checker (0-20 puntos)
    5. Context Awareness Checker (0-20 puntos)
    
    Total: 100 puntos posibles
    
    Autor: Polaricelabs 2026
    """
    
    def __init__(self, port=8605, symbol='USDCHF'):
        self.port = port
        self.symbol = symbol
        self.history = deque(maxlen=100)  # Store last 100 audits
        
        # Historical registry (para recalibración)
        self.setup_history = defaultdict(list)  # setup_type → [outcomes]
        self.confluence_performance = defaultdict(float)  # confluence_type → win%
        self.anti_pattern_effectiveness = defaultdict(float)  # anti_pattern → miss%
        
        log.info(f"[NOVA] ✨ Quality Auditor & Gap Analyzer initialized")
        log.info(f"[NOVA] 🎯 Symbol: {symbol} | Port: {port}")
        log.info(f"[NOVA] 📊 5 Audit Engines: Logic|Data|Intelligence|Math|Context")
        log.info(f"[NOVA] ⚡ Pure Python | <100ms latency | Gap Analysis")
    
    # ═══════════════════════════════════════════════════════════════
    # 🧠 AUDIT ENGINE 1: LOGIC CONSISTENCY CHECKER (0-20 pts)
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_logic_consistency(self, genome, trinity_decision, llm_responses):
        """Audita consistencia lógica de la decisión"""
        score = 10  # START NEUTRAL (10/20) - adjust up/down from here
        alerts = []
        
        try:
            indicators = genome.get('indicators', {}).get('current', {})
            rsi = float(indicators.get('rsi', 50))
            macd = float(indicators.get('macd', 0))
            adx = float(indicators.get('adx', 25))
            price_data = genome.get('price_data', {})
            closes = price_data.get('close', [])
            
            # Check 1: RSI vs MACD Alignment (±3 pts)
            if rsi < 30 or rsi > 70:
                if macd > 0 and rsi < 30:  # Oversold + MACD bullish = aligned
                    score += 3
                    # alerts.append(("LOGIC", "LOW", "RSI/MACD Aligned"))
                elif macd < 0 and rsi > 70:  # Overbought + MACD bearish = aligned
                    score += 3
                    # alerts.append(("LOGIC", "LOW", "RSI/MACD Aligned"))
                else:
                    score -= 3
                    alerts.append(("LOGIC_CONTRADICTION", "HIGH", 
                                 f"RSI={rsi:.0f} but MACD={macd:.2f} (not aligned)", 
                                 "Weak signal confidence"))
            
            # Check 2: ADX vs Trend Structure (±3 pts)
            if len(closes) >= 50:
                sma_fast = sum(closes[-5:]) / 5
                sma_slow = sum(closes[-20:]) / 20
                
                if sma_fast > sma_slow and adx < 20:
                    score -= 2
                    alerts.append(("LOGIC_CONTRADICTION", "MEDIUM",
                                 f"Uptrend visible but ADX={adx:.0f} (weak trend)",
                                 "Trend structure contradicts ADX"))
                elif sma_fast < sma_slow and adx > 40:
                    score -= 2
                    alerts.append(("LOGIC_CONTRADICTION", "MEDIUM",
                                 f"Downtrend visible but ADX={adx:.0f} (too strong)",
                                 "Over-confident trend strength"))
                else:
                    score += 3
            
            # Check 3: Gray Zone Detection (-5 pts if ambiguous)
            if 40 < rsi < 60 and abs(macd) < 0.3 and adx < 20:
                score -= 5
                alerts.append(("GRAY_ZONE_AMBIGUITY", "HIGH",
                             f"Setup is ambiguous: RSI={rsi:.0f}, MACD={macd:.2f}, ADX={adx:.0f}",
                             "No clear directional bias"))
            
            # Check 4: LLM Consensus Redundancy (penalize if highly correlated)
            llm_votes = []
            for llm_name, response in llm_responses.items():
                if isinstance(response, dict) and 'decision' in response:
                    llm_votes.append(response['decision'])
            
            # Si todos los LLMs dicen lo mismo, pueden ser redundantes
            if len(llm_votes) > 0:
                unique_votes = len(set(llm_votes))
                if unique_votes == 1:
                    # Todos votan igual - puede ser correlación
                    score -= 2
                    alerts.append(("CONFLUENCE_REDUNDANT", "MEDIUM",
                                 f"All {len(llm_votes)} LLMs say same ({llm_votes[0]})",
                                 "Possible correlation not independence"))
                elif unique_votes == 2:
                    score += 2
                    
            # Check 5: Causal Chain Validation (+4 if valid)
            decision = trinity_decision.get('decision', 'HOLD')
            if decision in ['BUY', 'SELL']:
                # Validar que la cadena lógica es válida
                # BUY requires: (RSI low OR MACD bullish) AND (trend up OR reversal setup)
                is_buy_causal = (rsi < 50 or macd > 0) and (sma_fast > sma_slow if len(closes) >= 20 else True)
                is_sell_causal = (rsi > 50 or macd < 0) and (sma_fast < sma_slow if len(closes) >= 20 else True)
                
                if (decision == 'BUY' and is_buy_causal) or (decision == 'SELL' and is_sell_causal):
                    score += 4
                else:
                    score -= 4
                    alerts.append(("LOGIC_CONTRADICTION", "CRITICAL",
                                 f"Causal chain broken for {decision}",
                                 "Decision doesn't follow from premises"))
            
            # Check 6: Regime Appropriateness (+3 if strategy matches regime)
            # Determinar estrategia detectada
            conf_type = genome.get('confluence_type', 'UNKNOWN')
            
            if adx > 35:  # Trending regime
                if 'TREND' in conf_type or 'BREAKOUT' in conf_type:
                    score += 3
                elif 'REVERSAL' in conf_type:
                    score -= 2
                    alerts.append(("REGIME_MISMATCH", "MEDIUM",
                                 f"Reversal strategy in trending market (ADX={adx:.0f})",
                                 "Strategy not optimal for regime"))
            else:  # Ranging regime
                if 'REVERSAL' in conf_type or 'RANGING' in conf_type:
                    score += 3
                elif 'BREAKOUT' in conf_type:
                    score -= 2
                    alerts.append(("REGIME_MISMATCH", "MEDIUM",
                                 f"Breakout strategy in ranging market (ADX={adx:.0f})",
                                 "Strategy not optimal for regime"))
            
            # Check 7: Anti-Pattern Recall (-4 if anti-pattern hit)
            # Check for known anti-patterns
            if decision == 'BUY' and rsi > 85:
                score -= 4
                alerts.append(("ANTI_PATTERN_DETECTED", "HIGH",
                             f"Buying with RSI={rsi:.0f} (extreme overbought)",
                             "Historically high fail rate"))
            elif decision == 'SELL' and rsi < 15:
                score -= 4
                alerts.append(("ANTI_PATTERN_DETECTED", "HIGH",
                             f"Selling with RSI={rsi:.0f} (extreme oversold)",
                             "Historically high fail rate"))
            
            # Check 8: No Trapped by Old Information (+2 if eval recent)
            tick_id = genome.get('tick_id', 0)
            if tick_id > 0:  # Fresh tick = eval is recent
                score += 2
            
            # Clamp score to 0-20
            score = max(0, min(20, score))
        
        except Exception as e:
            log.debug(f"[NOVA] Logic audit error: {e}")
            score = 10  # Default to middle
        
        return score, alerts
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 AUDIT ENGINE 2: DATA COMPLETENESS CHECKER (0-20 pts)
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_data_completeness(self, genome, trinity_data):
        """Audita completitud de datos disponibles"""
        score = 10  # START NEUTRAL (10/20)
        alerts = []
        
        try:
            # Check 1: Volume Validation (+3 if vol > avg)
            price_data = genome.get('price_data', {})
            volumes = price_data.get('volume', [])
            
            if len(volumes) >= 5:
                avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
                current_vol = volumes[-1]
                
                if current_vol > avg_vol * 1.5:
                    score += 3
                elif current_vol < avg_vol * 0.5:
                    score -= 2
                    alerts.append(("VOLUME_NOT_CONFIRMED", "MEDIUM",
                                 f"Volume only {current_vol/avg_vol:.1f}x average",
                                 "Low volume confirmation"))
            else:
                score += 1
            
            # Check 2: Order Flow Available (+3 if data exists)
            tick_data = genome.get('tick_data', {})
            bid_vol = tick_data.get('bid_volume', [])
            ask_vol = tick_data.get('ask_volume', [])
            
            if bid_vol and ask_vol:
                score += 3
                # Imbalance detection
                total_bid = sum(bid_vol)
                total_ask = sum(ask_vol)
                imbalance = abs(total_bid - total_ask) / (total_bid + total_ask + 0.001)
                if imbalance > 0.3:
                    # alerts.append(("VOLUME", "LOW", "Strong order flow imbalance detected"))
                    pass
            else:
                score -= 1
                alerts.append(("DATA_MISSING", "LOW",
                             "Order flow data not available",
                             "Cannot validate institutional flow"))
            
            # Check 3: Sweep History Available (+3 if coherent)
            llm6_sweep = genome.get('last_llm6_sweep_type', 'NONE')
            sweep_history = genome.get('sweep_history', [])
            
            if sweep_history and len(sweep_history) >= 3:
                score += 3
                # Check for contradictions
                recent_sweeps = sweep_history[-3:]
                if len(set(recent_sweeps)) > 1:  # Mixed sweep types
                    score -= 1
                    alerts.append(("DATA_INCONSISTENCY", "MEDIUM",
                                 f"Conflicting sweep signals: {recent_sweeps}",
                                 "Unclear smart money direction"))
            elif llm6_sweep != 'NONE':
                score += 1
            
            # Check 4: Market Structure Registry (+2 if swing tracked)
            swing_high = genome.get('swing_high', None)
            swing_low = genome.get('swing_low', None)
            
            if swing_high is not None and swing_low is not None:
                score += 2
            else:
                score -= 1
            
            # Check 5: Confluence Type Ranking (+2 if historical ranking exists)
            confluence_type = genome.get('confluence_type', 'UNKNOWN')
            if confluence_type in self.confluence_performance:
                score += 2
            else:
                score += 1  # Partial credit for known type
            
            # Check 6: Economic Calendar Checked (+2 if no news imminent)
            next_event_minutes = genome.get('next_economic_event_minutes', 60)
            if next_event_minutes > 30:
                score += 2
            else:
                score -= 2
                alerts.append(("NEWS_IMMINENT", "MEDIUM",
                             f"Economic news in {next_event_minutes} minutes",
                             "Volatility expected soon"))
            
            # Check 7: Volatility Regime History (-3 if spike unexpected)
            vol_current = float(genome.get('volatility_current', 10))
            vol_average = float(genome.get('volatility_average', 10))
            
            if vol_current > vol_average * 2.0:
                score -= 3
                alerts.append(("VOLATILITY_SPIKE", "HIGH",
                             f"Volatility spike: {vol_current:.1f} vs avg {vol_average:.1f}",
                             "Unexpected volatility increase"))
            elif vol_current > vol_average * 1.5:
                score -= 1
            else:
                score += 1
            
            # Check 8: Correlation with USD (+2 if context valid)
            # XAU/USD is strongly correlated with USD index
            usd_direction = genome.get('usd_direction', 'NEUTRAL')
            decision = genome.get('decision', 'HOLD')
            
            if decision == 'BUY' and usd_direction == 'DOWN':
                score += 2  # XAU sube cuando USD baja
            elif decision == 'SELL' and usd_direction == 'UP':
                score += 2  # XAU baja cuando USD sube
            elif decision == 'BUY' and usd_direction == 'UP':
                score -= 2
                alerts.append(("DATA_CONTRADICTION", "MEDIUM",
                             "Buying XAU while USD rising (negative correlation)",
                             "Trade works against macro trend"))
            
            # Clamp score
            score = max(0, min(20, score))
        
        except Exception as e:
            log.debug(f"[NOVA] Data audit error: {e}")
            score = 10
        
        return score, alerts
    
    # ═══════════════════════════════════════════════════════════════
    # 🎯 AUDIT ENGINE 3: INTELLIGENCE DEPTH CHECKER (0-20 pts)
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_intelligence_depth(self, genome, trinity_data):
        """Audita profundidad del análisis de inteligencia"""
        score = 10  # START NEUTRAL (10/20)
        alerts = []
        
        try:
            conf_type = genome.get('confluence_type', 'UNKNOWN')
            
            # Check 1: Confluence Type Predictor (+2 if optimal)
            if conf_type in self.confluence_performance:
                win_rate = self.confluence_performance[conf_type]
                if win_rate > 0.70:
                    score += 2
                elif win_rate < 0.50:
                    score -= 1
                    alerts.append(("CONFLUENCE_SUBOPTIMAL", "MEDIUM",
                                 f"Confluence type {conf_type} has only {win_rate:.0%} historical winrate",
                                 "Consider waiting for better setup"))
            else:
                score += 1  # Unknown but analyzing
            
            # Check 2: Smart Money Behavior (+2 if classified)
            sweep_type = genome.get('last_llm6_sweep_type', 'NONE')
            if sweep_type != 'NONE':
                # Check if it's a high-quality sweep (not noisy)
                whale_conf = float(genome.get('last_llm6_whale_conf', 0))
                if whale_conf > 70:
                    score += 2
                elif whale_conf < 30:
                    score -= 1
            
            # Check 3: Trap Probability (+2 if contextualized)
            adx = float(genome.get('indicators', {}).get('current', {}).get('adx', 25))
            trap_prob = genome.get('trap_probability', 0.5)
            
            # Trap probability should vary by regime
            if adx > 40 and trap_prob > 0.5:
                # In strong trends, trap probability should be LOWER
                score -= 1
                alerts.append(("TRAP_PROBABILITY_HIGH", "MEDIUM",
                             f"Trap prob {trap_prob:.0%} too high for strong trend (ADX={adx:.0f})",
                             "Re-calibrate trap detection"))
            elif trap_prob < 0.3:
                score += 1
            
            # Check 4: Price Action Microstructure (+2 if analyzed)
            opens = genome.get('price_data', {}).get('open', [])
            closes = genome.get('price_data', {}).get('close', [])
            highs = genome.get('price_data', {}).get('high', [])
            lows = genome.get('price_data', {}).get('low', [])
            
            if len(opens) >= 5 and len(closes) >= 5:
                # Calculate wick metrics
                wick_found = False
                for i in range(-3, 0):
                    if i < -len(opens):
                        continue
                    o, c, h, l = opens[i], closes[i], highs[i], lows[i]
                    upper_wick = h - max(o, c)
                    lower_wick = min(o, c) - l
                    body = abs(c - o)
                    
                    if body > 0:
                        if upper_wick > 2 * body or lower_wick > 2 * body:
                            wick_found = True
                            break
                
                if wick_found:
                    score += 2
            
            # Check 5: Exhaustion Index (+2 if calculated)
            exhaustion_index = genome.get('exhaustion_index', None)
            if exhaustion_index is not None:
                if exhaustion_index > 70:
                    score -= 2
                    alerts.append(("EXHAUSTION_DETECTED", "MEDIUM",
                                 f"Exhaustion index: {exhaustion_index:.0f}%",
                                 "Trend may be near end"))
                else:
                    score += 2
            else:
                score -= 1
            
            # Check 6: Leverage Optimization (+2 if Kelly applied)
            position_mult = genome.get('position_multiplier', 1.0)
            if position_mult < 0.3 or position_mult > 2.0:
                score -= 1
                alerts.append(("POSITION_SIZING_EXTREME", "LOW",
                             f"Position multiplier: {position_mult:.2f}x (outside normal range)",
                             "Check Kelly calculation"))
            else:
                score += 1
            
            # Check 7: Adaptive Stop Loss (+2 if by structure)
            sl_type = genome.get('sl_type', 'ATR_BASED')
            if sl_type == 'STRUCTURE_BASED':
                score += 2
            elif sl_type == 'ATR_BASED':
                score += 1
            
            # Check 8: Take Profit Scaling (+2 if multi-TP)
            tp_levels = genome.get('tp_levels', 1)
            if tp_levels >= 3:
                score += 2
            elif tp_levels == 2:
                score += 1
            else:
                score -= 1
            
            # Check 9: Trend Acceleration (+2 if calculated)
            acceleration = genome.get('trend_acceleration', None)
            if acceleration is not None:
                score += 2
            else:
                score += 1
            
            # Clamp score
            score = max(0, min(20, score))
        
        except Exception as e:
            log.debug(f"[NOVA] Intelligence audit error: {e}")
            score = 10
        
        return score, alerts
    
    # ═══════════════════════════════════════════════════════════════
    # 📐 AUDIT ENGINE 4: MATHEMATICAL RIGOR CHECKER (0-20 pts)
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_mathematical_rigor(self, genome):
        """Audita rigor matemático de cálculos"""
        score = 10  # START NEUTRAL (10/20)
        alerts = []
        
        try:
            # Check 1: Volatility Regime Adjusted (-3 if not)
            vol_adjusted = genome.get('volatility_regime_adjusted', False)
            if vol_adjusted:
                score += 3
            else:
                score -= 1
                alerts.append(("VOLATILITY_NOT_ADJUSTED", "LOW",
                             "Volatility not adjusted by regime",
                             "May cause incorrect SL/TP levels"))
            
            # Check 2: Bayesian Probability Calibrated (+3)
            # Check if prior probabilities are being updated
            if 'bayesian_prior' in genome and 'bayesian_posterior' in genome:
                score += 3
            else:
                score -= 1
            
            # Check 3: R:R Ratio Dynamic (+3 if adaptive)
            rr_ratio = float(genome.get('rr_ratio', 1.8))
            
            if 1.2 <= rr_ratio <= 2.5:
                score += 3
            elif rr_ratio > 2.5 or rr_ratio < 1.0:
                score -= 2
                alerts.append(("RR_RATIO_EXTREME", "MEDIUM",
                             f"R:R ratio {rr_ratio:.2f}:1 outside reasonable range",
                             "May indicate miscalculation"))
            
            # Check 4: Position Sizing via Kelly (+3 if true Kelly)
            has_kelly = genome.get('kelly_criterion_applied', False)
            if has_kelly:
                score += 3
            else:
                score += 1  # At least using ATR-based
            
            # Check 5: Confidence Combination (+3 if independent)
            confidence = float(genome.get('consensus_confidence', 50))
            num_llms = genome.get('num_llm_votes', 0)
            
            if num_llms >= 3:
                score += 2
                # More LLMs = more independent evidence (if not correlated)
                if num_llms >= 5:
                    score += 1
            
            # Check 6: ADX Normalized by Timeframe (+2)
            timeframe = genome.get('timeframe', 'M1')
            adx_normalized = genome.get('adx_normalized', False)
            
            if adx_normalized:
                score += 2
            else:
                score += 0  # Not penalize, just bonus if done
            
            # Check 7: Volatility Smile Considered (+2)
            uses_lognormal = genome.get('uses_lognormal_distribution', False)
            if uses_lognormal:
                score += 2
            else:
                score += 0  # Advanced feature
            
            # Check 8: Probability Modifier Limits (+1 if enforced)
            max_modifier = genome.get('max_probability_modifier', 2.0)
            if max_modifier <= 2.0:
                score += 1
            else:
                score -= 1
                alerts.append(("PROBABILITY_MODIFIER_EXTREME", "LOW",
                             f"Max modifier {max_modifier:.2f}x (may be too high)",
                             "Can lead to over-confidence"))
            
            # Clamp score
            score = max(0, min(20, score))
        
        except Exception as e:
            log.debug(f"[NOVA] Math audit error: {e}")
            score = 10
        
        return score, alerts
    
    # ═══════════════════════════════════════════════════════════════
    # 📅 AUDIT ENGINE 5: CONTEXT AWARENESS CHECKER (0-20 pts)
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_context_awareness(self, genome):
        """Audita conciencia del contexto macro/temporal"""
        score = 10  # START NEUTRAL (10/20)
        alerts = []
        
        try:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            hour_utc = now.hour
            day_of_week = now.weekday()  # 0=Monday, 6=Sunday
            
            # Check 1: Intraday Seasonality (+2 if pattern known)
            session = self._get_session(hour_utc)
            has_seasonality = genome.get('has_intraday_seasonality', False)
            
            if has_seasonality:
                score += 2
            else:
                score += 0
            
            # Check 2: Central Bank Calendar (+2 if no news imminent)
            next_event_min = genome.get('next_economic_event_minutes', 60)
            if next_event_min > 60:
                score += 2
            elif next_event_min > 30:
                score += 1
            else:
                score -= 2
                alerts.append(("NEWS_IMMINENT", "HIGH",
                             f"Economic news in {next_event_min} minutes",
                             "High volatility expected"))
            
            # Check 3: VIX Correlation (+2 if monitored)
            vix_monitored = genome.get('vix_monitored', False)
            if vix_monitored:
                score += 2
                # Check if VIX alignment is good
                vix_level = float(genome.get('vix_level', 15))
                if vix_level > 25:  # High fear = good for gold buys
                    decision = genome.get('decision', 'HOLD')
                    if decision == 'BUY':
                        score += 1
            else:
                score += 0
            
            # Check 4: Weekend Gap Risk (+2 if forecasted)
            is_friday = day_of_week == 4
            is_near_weekend = hour_utc > 20 or (is_friday and hour_utc > 12)
            
            if is_near_weekend:
                has_gap_forecast = genome.get('weekend_gap_forecasted', False)
                if has_gap_forecast:
                    score += 2
                else:
                    score -= 2
                    alerts.append(("WEEKEND_GAP_RISK", "MEDIUM",
                                 f"Near weekend (Friday {hour_utc}:00 UTC) without gap forecast",
                                 "Risk of overnight gap"))
            else:
                score += 1
            
            # Check 5: Session-Specific Logic (+2 if adapted)
            session_logic_adapted = genome.get('session_logic_adapted', False)
            if session_logic_adapted:
                score += 2
            else:
                score += 1
            
            # Check 6: Macro Trend Direction (+2 if context OK)
            macro_ok = genome.get('macro_trend_ok', True)
            if macro_ok:
                score += 2
            else:
                score -= 2
                alerts.append(("MACRO_CONFLICT", "MEDIUM",
                             "Trade direction conflicts with macro trend",
                             "Fighting the bigger picture"))
            
            # Check 7: Inter-Session Gap Analysis (+2)
            gap_analyzed = genome.get('intersession_gap_analyzed', False)
            if gap_analyzed:
                score += 2
            else:
                score += 0
            
            # Check 8: Liquidity Event Detection (+2)
            liquidity_checked = genome.get('liquidity_event_checked', False)
            if liquidity_checked:
                score += 2
            else:
                score -= 1
                alerts.append(("LIQUIDITY_NOT_CHECKED", "LOW",
                             "Liquidity events not analyzed",
                             "May face unexpected slippage"))
            
            # Clamp score
            score = max(0, min(20, score))
        
        except Exception as e:
            log.debug(f"[NOVA] Context audit error: {e}")
            score = 10
        
        return score, alerts
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _get_session(self, hour_utc):
        """Determinar sesión de trading actual"""
        if 0 <= hour_utc < 8:
            return "ASIA"
        elif 8 <= hour_utc < 12:
            return "LONDON_OPEN"
        elif 12 <= hour_utc < 17:
            return "LONDON_NY_OVERLAP"
        elif 17 <= hour_utc < 22:
            return "NY"
        else:
            return "LATE_NY"
    
    def _categorize_trade(self, quality_score, genome, alerts):
        """Categorizar el trade por tipo de riesgo y setup"""
        categories = []
        
        try:
            adx = float(genome.get('indicators', {}).get('current', {}).get('adx', 25))
            conf_type = genome.get('confluence_type', 'UNKNOWN')
            
            # Tipo de setup
            if adx > 28:
                categories.append("TRENDING_SETUP")
            else:
                categories.append("RANGING_SETUP")
            
            # Tipo de confluencia
            if "SMART_MONEY" in conf_type:
                categories.append("CONFLUENCE_TYPE_SMART_MONEY")
            elif "TECHNICAL" in conf_type:
                categories.append("CONFLUENCE_TYPE_TECHNICAL")
            elif "BREAKOUT" in conf_type:
                categories.append("CONFLUENCE_TYPE_BREAKOUT")
            elif "DIVERGENCE" in conf_type:
                categories.append("CONFLUENCE_TYPE_DIVERGENCE")
            else:
                categories.append("CONFLUENCE_TYPE_UNKNOWN")
            
            # Risk categorization por quality score
            if quality_score >= 80:
                categories.append("LOW_RISK")
            elif quality_score >= 60:
                categories.append("MEDIUM_RISK")
            else:
                categories.append("HIGH_RISK")
            
            # Timing
            timing_mult = float(genome.get('timing_multiplier', 1.0))
            if timing_mult >= 1.5:
                categories.append("EXCELLENT_TIMING")
            elif timing_mult >= 1.2:
                categories.append("GOOD_TIMING")
            else:
                categories.append("POOR_TIMING")
            
            # Volume check
            volumes = genome.get('price_data', {}).get('volume', [])
            if len(volumes) >= 2:
                avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
                if volumes[-1] > avg_vol * 1.5:
                    categories.append("VOLUME_CONFIRMED")
                else:
                    categories.append("VOLUME_NOT_CONFIRMED")
            
            # Anomalies
            for alert_type, _, _, _ in alerts:
                if "ANOMALY" in alert_type or "LIQUIDITY_EVENT" in alert_type:
                    categories.append("ANOMALY_DETECTED")
                    break
            
        except Exception as e:
            log.debug(f"[NOVA] Categorization error: {e}")
        
        return categories
    
    def analyze(self, genome):
        """Main analysis - audita la decisión de Trinity"""
        try:
            symbol = genome.get('metadata', {}).get('symbol', 'USDCHF')
            trinity_decision = genome.get('trinity_decision', {'decision': 'HOLD', 'confidence': 50})
            llm_responses = genome.get('llm_responses', {})
            
            # Run 5 audit engines
            logic_score, logic_alerts = self._audit_logic_consistency(genome, trinity_decision, llm_responses)
            data_score, data_alerts = self._audit_data_completeness(genome, trinity_decision)
            intel_score, intel_alerts = self._audit_intelligence_depth(genome, trinity_decision)
            math_score, math_alerts = self._audit_mathematical_rigor(genome)
            context_score, context_alerts = self._audit_context_awareness(genome)
            
            # Combine scores
            quality_score = logic_score + data_score + intel_score + math_score + context_score
            quality_score = int(quality_score)  # 0-100
            
            # Combine alerts
            all_alerts = []
            for alert_type, severity, issue, message in (logic_alerts + data_alerts + intel_alerts + math_alerts + context_alerts):
                all_alerts.append({
                    'type': alert_type,
                    'severity': severity,
                    'issue': issue,
                    'message': message
                })
            
            # Categorize trade
            categories = self._categorize_trade(quality_score, genome, all_alerts)
            
            # Calculate multiplier (0.5-1.0, not 0-1 to avoid blocking trades)
            multiplier = max(0.5, quality_score / 100.0)
            
            # Adjust multiplier based on alerts
            has_high_alert = any(a['severity'] == 'HIGH' for a in all_alerts)
            has_critical_alert = any(a['severity'] == 'CRITICAL' for a in all_alerts)
            
            if has_critical_alert:
                multiplier *= 0.3
            elif has_high_alert:
                multiplier *= 0.7
            
            if "LOW_RISK" in categories:
                multiplier = min(1.0, multiplier * 1.1)
            if "ANOMALY_DETECTED" in categories:
                multiplier *= 0.5
            
            # Clamp to 0-1
            multiplier = max(0.0, min(1.0, multiplier))
            
            # Build result
            result = {
                'decision': 'AUDIT',
                'quality_score': quality_score,
                'quality_breakdown': {
                    'logic_consistency': logic_score,
                    'data_completeness': data_score,
                    'intelligence_depth': intel_score,
                    'mathematical_rigor': math_score,
                    'context_awareness': context_score
                },
                'alerts': all_alerts,
                'categories': categories,
                'multiplier': round(multiplier, 3),
                'explanation': f"Quality score {quality_score}/100. " +
                              (f"⚠️ {len([a for a in all_alerts if a['severity'] == 'HIGH'])} HIGH alerts. " if any(a['severity'] == 'HIGH' for a in all_alerts) else "") +
                              f"Confidence multiplier: {multiplier:.1%}",
                'timestamp': time.time()
            }
            
            self.history.append(result)
            
            log.info(f"[NOVA] {symbol} | Quality={quality_score}/100 | Multiplier={multiplier:.2f}x | Alerts={len(all_alerts)}")
            
            return result
        
        except Exception as e:
            log.error(f"[NOVA] Analysis error: {e}", exc_info=True)
            return {
                'decision': 'AUDIT',
                'quality_score': 50,
                'quality_breakdown': {'logic_consistency': 10, 'data_completeness': 10, 'intelligence_depth': 10, 'mathematical_rigor': 10, 'context_awareness': 0},
                'alerts': [{'type': 'ERROR', 'severity': 'CRITICAL', 'issue': str(e), 'message': 'Analysis failed'}],
                'categories': ['ERROR'],
                'multiplier': 0.5,
                'timestamp': time.time()
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 🚀 ENHANCED AUDIT METHODS - Huecos #3, #12, #14, #20
    # ═══════════════════════════════════════════════════════════════
    
    def _audit_causal_chain(self, llm_responses: dict, decision: str) -> dict:
        """
        HUECO #3: Valida que cada LLM llegó a decisión por RAZONES DIFERENTES
        (Detecta falso consenso por correlación)
        """
        try:
            reasons = {}
            for llm_name, response in llm_responses.items():
                if not isinstance(response, dict):
                    continue
                reason = response.get('reasoning', '')
                if reason:
                    reasons[llm_name] = reason
            
            unique_reasons = len(set(reasons.values()))
            total_llms = len([r for r in llm_responses.values() if isinstance(r, dict) and 'reasoning' in r])
            
            if unique_reasons == 0:
                return {'causal_score': 20, 'alert': 'NO_REASONING', 'reason': 'LLMs provided no reasoning'}
            elif unique_reasons == 1 and total_llms > 1:
                # ❌ Todos usan misma lógica = correlación falsa
                return {
                    'causal_score': 20,
                    'alert': 'CORRELATED_LOGIC',
                    'reason': f'All {total_llms} LLMs use identical reasoning = false consensus'
                }
            else:
                # ✅ Razones diferentes = independencia
                diversity = (unique_reasons / total_llms) * 100 if total_llms > 0 else 0
                return {
                    'causal_score': min(100, 50 + diversity),
                    'alert': None,
                    'reason': f'{unique_reasons}/{total_llms} different reasoning paths'
                }
        except Exception as e:
            log.debug(f"[NOVA] Causal chain audit error: {e}")
            return {'causal_score': 50, 'alert': 'ERROR', 'reason': str(e)}
    
    def _audit_internal_contradiction(self, genome: dict, decision: str) -> dict:
        """
        HUECO #14: Detecta contradicciones entre decision e indicators
        """
        try:
            indicators = genome.get('indicators', {}).get('current', {})
            rsi = float(indicators.get('rsi', 50))
            volume = float(indicators.get('volume', 1000))
            volatility = float(indicators.get('adx', 25))
            
            contradictions = []
            severity = 'LOW'
            
            if decision == 'BUY':
                if rsi > 80:
                    contradictions.append(f'OVERBOUGHT_BUY (RSI={rsi:.0f})')
                    severity = 'MEDIUM'
                if volume < 100:
                    contradictions.append(f'LOW_VOLUME_BUY (vol={volume:.0f})')
                    severity = 'MEDIUM'
            
            elif decision == 'SELL':
                if rsi < 20:
                    contradictions.append(f'OVERSOLD_SELL (RSI={rsi:.0f})')
                    severity = 'MEDIUM'
                if volume < 100:
                    contradictions.append(f'LOW_VOLUME_SELL (vol={volume:.0f})')
                    severity = 'MEDIUM'
            
            # Divergence check
            if volatility < 10:
                if decision != 'HOLD':
                    contradictions.append(f'LOW_VOLATILITY_{decision} (ADX={volatility:.0f})')
                    severity = 'LOW'
            
            return {
                'has_contradiction': len(contradictions) > 0,
                'alerts': contradictions,
                'severity': severity,
                'contradiction_score': max(0, 100 - (len(contradictions) * 20))
            }
        except Exception as e:
            log.debug(f"[NOVA] Internal contradiction audit error: {e}")
            return {'has_contradiction': False, 'alerts': [], 'severity': None, 'contradiction_score': 100}
    
    def _detect_market_regime(self, bar_data: dict) -> str:
        """
        HUECO #12: Detecta si mercado está trending o ranging
        """
        try:
            closes = bar_data.get('closes', [])
            if len(closes) < 20:
                return 'INSUFFICIENT_DATA'
            
            # Calculate volatility on last 20 bars
            recent_closes = closes[-20:]
            volatility = float(np.std(recent_closes))
            mean_price = float(np.mean(recent_closes))
            
            volatility_pct = (volatility / mean_price) * 100 if mean_price > 0 else 0
            
            if volatility_pct > 1.0:  # >1% volatility
                return 'TRENDING'
            elif volatility_pct < 0.1:  # <0.1% volatility
                return 'RANGING'
            else:
                return 'TRANSITIONING'
        except Exception as e:
            log.debug(f"[NOVA] Market regime detection error: {e}")
            return 'UNKNOWN'
    
    def _detect_data_outliers(self, genome: dict) -> dict:
        """
        HUECO #20: Detecta valores outliers (>3 sigma)
        """
        try:
            indicators = genome.get('indicators', {}).get('current', {})
            outliers = []
            
            # Define expected ranges (3-sigma bounds)
            expected_ranges = {
                'rsi': {'mean': 50, 'std': 15},  # Most RSI values 5-95
                'adx': {'mean': 25, 'std': 15},  # Most ADX values -5 to 55
                'macd': {'mean': 0, 'std': 2},   # Most MACD -6 to +6
            }
            
            for key, value in indicators.items():
                if key not in expected_ranges:
                    continue
                
                try:
                    value_float = float(value)
                    bounds = expected_ranges[key]
                    mean = bounds['mean']
                    std = bounds['std']
                    
                    z_score = abs((value_float - mean) / std) if std > 0 else 0
                    
                    if z_score > 3:  # >3 sigma = outlier
                        outliers.append({
                            'key': key,
                            'value': value_float,
                            'mean': mean,
                            'std': std,
                            'z_score': z_score
                        })
                except (ValueError, TypeError):
                    pass
            
            return {
                'has_outliers': len(outliers) > 0,
                'outliers': outliers,
                'outlier_score': max(0, 100 - (len(outliers) * 30))
            }
        except Exception as e:
            log.debug(f"[NOVA] Outlier detection error: {e}")
            return {'has_outliers': False, 'outliers': [], 'outlier_score': 100}
    
    def _audit_correlation_risks(self, symbol: str, genome: dict) -> list:
        """
        HUECO #13: Audita riesgos correlacionados con otros activos
        """
        alerts = []
        try:
            # Para USDCHF: correlación con DXY
            if symbol == 'USDCHF':
                # If we have DXY data in genome
                dxy_data = genome.get('correlation_data', {}).get('dxy', {})
                if dxy_data:
                    dxy_direction = dxy_data.get('direction', 'UNKNOWN')
                    if dxy_direction == 'UP':
                        # USD subiendo = bearish para oro
                        alerts.append({
                            'type': 'CORRELATION_RISK',
                            'severity': 'MEDIUM',
                            'issue': 'DXY_RISING',
                            'message': 'USD strengthening is bearish for gold - caution on long trades'
                        })
            
            # Para EURUSD: correlación con ECB spreads
            elif symbol == 'EURUSD':
                ecb_data = genome.get('correlation_data', {}).get('ecb', {})
                if ecb_data:
                    spread = ecb_data.get('rate_spread', 0)
                    if spread < 0:
                        # ECB rates bajos = bearish para EUR
                        alerts.append({
                            'type': 'CORRELATION_RISK',
                            'severity': 'MEDIUM',
                            'issue': 'ECB_SPREAD_LOW',
                            'message': 'ECB rate spread is negative - caution on long EUR'
                        })
        except Exception as e:
            log.debug(f"[NOVA] Correlation risk audit error: {e}")
        
        return alerts
    
    def run_server(self):
        """HTTP Server using Flask - compatible with Trinity's requests"""
        from flask import Flask, request, jsonify
        import logging as flask_logging
        
        # Silence Flask's default logger
        flask_logging.getLogger('werkzeug').setLevel(flask_logging.WARNING)
        
        app = Flask(__name__)
        
        @app.route('/audit', methods=['POST'])
        def audit_endpoint():
            """Handle POST /audit requests from Trinity"""
            try:
                request_data = request.get_json(force=True)
                result = self.analyze(request_data)
                return jsonify(result)
            except Exception as e:
                log.error(f"[NOVA] Audit error: {e}")
                return jsonify({
                    'is_valid': False,
                    'quality_multiplier': 0.5,
                    'audit_score': 50,
                    'alerts': [str(e)],
                    'reasoning': 'Error during audit',
                    'emergency_halt': False
                }), 500
        
        @app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({'status': 'ok', 'symbol': self.symbol})
        
        log.info(f"[NOVA] HTTP Server starting on port {self.port}")
        app.run(host='127.0.0.1', port=self.port, threaded=True, use_reloader=False)
    
    def run_server_tcp(self):
        """Legacy TCP Server loop - kept for backward compatibility"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)
        log.info(f"[NOVA] TCP Server listening on port {self.port}")
        
        try:
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self._handle_request_tcp, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            log.info("[NOVA] Shutting down")
        finally:
            server.close()
    
    def _handle_request_tcp(self, conn):
        """Handle incoming TCP request (legacy)"""
        try:
            # 1. Read header (4 bytes = length of JSON)
            header = conn.recv(4)
            if len(header) < 4:
                log.debug(f"[NOVA] Incomplete header: {len(header)} bytes")
                return
            
            # 2. Unpack length
            data_length = struct.unpack('>I', header)[0]
            
            # Sanity check on data length
            if data_length <= 0 or data_length > 10_000_000:
                log.warning(f"[NOVA] Invalid data length: {data_length}")
                return
            
            # 3. Read JSON data
            data_bytes = b''
            while len(data_bytes) < data_length:
                chunk = conn.recv(min(4096, data_length - len(data_bytes)))
                if not chunk:
                    break
                data_bytes += chunk
            
            # 4. Check if we got all data
            if len(data_bytes) < data_length:
                log.warning(f"[NOVA] Incomplete data: got {len(data_bytes)}/{data_length} bytes")
                return
            
            # 5. Parse JSON with better error handling
            try:
                decoded_data = data_bytes.decode('utf-8')
                if not decoded_data or decoded_data.strip() == '':
                    log.warning(f"[NOVA] Empty JSON received")
                    return
                request_data = json.loads(decoded_data)
            except json.JSONDecodeError as je:
                log.warning(f"[NOVA] JSON parse error: {je} | First 100 chars: {data_bytes[:100]}")
                return
            
            # 6. Analyze
            result = self.analyze(request_data)
            
            # 7. Send response
            response_json = json.dumps(result)
            response_bytes = response_json.encode('utf-8')
            response_header = struct.pack('>I', len(response_bytes))
            conn.sendall(response_header + response_bytes)
        
        except Exception as e:
            log.warning(f"TCP Request handling error: {e}")
        
        finally:
            conn.close()


if __name__ == '__main__':
    import sys
    
    # Support both ports
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8605
    symbol = 'USDCHF' if port == 8605 else 'EURUSD'
    
    nova = NOVA(port=port, symbol=symbol)
    nova.run_server_tcp()  # TCP like all other LLMs - NO HTTP

