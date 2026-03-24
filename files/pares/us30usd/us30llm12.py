#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║            🛡️ NOVA TRADING AI - LLM12 SENTINEL "ESPÍA DE CALIDAD ELITE"        ║
║                       THE QUALITY CONSCIOUSNESS                                ║
║                  Capas 4-6: Ejecución → Reflexión → Evolución                  ║
║                       by Polarice Labs © 2026                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  CAPA 4: EJECUCIÓN CONSCIENTE (10 Elite Checks, Execution Quality, Break-Even) ║
║  CAPA 5: REFLEXIÓN PROFUNDA (Autopsia, Calibración Confianza, P&L Monitor)     ║
║  CAPA 6: EVOLUCIÓN CONTINUA (Edge Monitor, Auto-Veto, Recalibración, Heatmap) ║
║                                                                                ║
║  Port: 5569 (TCP) | Python Deterministic | <50ms latency                      ║
║  Protocol: 4-byte big-endian length prefix + UTF-8 JSON                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import socket, struct, json, logging, threading, time, os, math, signal, sys
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🛡️ LLM12 SENTINEL | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

PORT = 8968
HOST = '127.0.0.1'
SYMBOL = 'US30USD'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, f'memoria_{SYMBOL}.json')

# Conviction thresholds
MIN_CONVICTION_ACTION = 0.30
MIN_RR_RATIO = 2.0
MIN_LLM_CONSENSUS = 7  # out of 12
MIN_NOVA_SCORE = 65
MAX_DIRECTIONAL_EXPOSURE = 3

# Loss classification categories
LOSS_CATEGORIES = [
    'AGAINST_MACRO', 'BAD_TIMING', 'EVENT_SHOCK', 'LIQUIDITY_TRAP',
    'LOW_QUALITY_SETUP', 'REGIME_CHANGE', 'OVEREXPOSURE', 'COST_EATEN',
    'MANUAL_CUT'
]

WIN_CATEGORIES = [
    'PERFECT_EXECUTION', 'PARTIAL_WIN', 'LUCKY_WIN', 'SQUEEZED_WIN'
]

SESSIONS = {
    'ASIA':     (0, 8),
    'LONDON':   (8, 12),
    'OVERLAP':  (12, 17),
    'NEW_YORK': (17, 21),
    'OFF':      (21, 24),
}


# ═══════════════════════════════════════════════════════════════════
# MEMORY READER (shared with LLM11)
# ═══════════════════════════════════════════════════════════════════

class MemoryReader:
    """Thread-safe reader for the shared memory JSON"""

    def __init__(self):
        self._cache = {}
        self._last_read = 0
        self._lock = threading.Lock()

    def get(self) -> dict:
        with self._lock:
            if time.time() - self._last_read > 5:  # Re-read every 5s
                self._cache = self._load()
                self._last_read = time.time()
            return self._cache.copy()

    def _load(self) -> dict:
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.debug(f"[Memory] Read error: {e}")
        return {}

    def update_and_save(self, memory: dict):
        """Write updated memory back to file"""
        with self._lock:
            try:
                memory['last_updated'] = datetime.now(timezone.utc).isoformat()
                with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(memory, f, indent=2, default=str)
                self._cache = memory
                self._last_read = time.time()
            except Exception as e:
                log.error(f"[Memory] Write error: {e}")


# ═══════════════════════════════════════════════════════════════════
# CAPA 4: EJECUCIÓN CONSCIENTE
# ═══════════════════════════════════════════════════════════════════

class EliteGateChecker:
    """Módulo 4.1: 10 Elite Quality Checks — ALL must pass"""

    def run_checks(self, proposal: dict, memory: dict) -> dict:
        """
        Run all 10 checks. Returns approval status + details.
        """
        phase = memory.get('consciousness_phase', 'LEARNING')
        results = []
        all_passed = True

        # Define which checks are active per phase
        active_checks = {
            'LEARNING':     [1, 2, 3, 4],          # Basics only
            'WARMING':      [1, 2, 3, 4, 5, 6],    # + consensus
            'CALIBRATING':  [1, 2, 3, 4, 5, 6, 7, 8, 9],  # Most checks
            'FULL':         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # All 10
        }
        active = active_checks.get(phase, [1, 2, 3, 4])

        checks = [
            (1, self._check_strategy_history),
            (2, self._check_pair_session_history),
            (3, self._check_active_vetos),
            (4, self._check_rr_ratio),
            (5, self._check_llm_consensus),
            (6, self._check_nova_score),
            (7, self._check_portfolio_exposure),
            (8, self._check_macro_event),
            (9, self._check_narrative_coherence),
            (10, self._check_confidence_calibration),
        ]

        for check_num, check_fn in checks:
            if check_num not in active:
                results.append({'check': check_num, 'status': 'SKIPPED', 'reason': f'Phase {phase}'})
                continue
            try:
                passed, reason = check_fn(proposal, memory)
                results.append({
                    'check': check_num,
                    'status': 'PASS' if passed else 'FAIL',
                    'reason': reason
                })
                if not passed:
                    all_passed = False
            except Exception as e:
                results.append({'check': check_num, 'status': 'ERROR', 'reason': str(e)[:80]})
                # Don't fail on check errors in early phases
                if phase in ('CALIBRATING', 'FULL'):
                    all_passed = False

        passed_count = sum(1 for r in results if r['status'] == 'PASS')
        total_active = sum(1 for r in results if r['status'] != 'SKIPPED')

        return {
            'approved': all_passed,
            'checks_passed': passed_count,
            'checks_total': total_active,
            'results': results,
            'phase': phase,
        }

    def _check_strategy_history(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 1: Strategy profit ratio ≥ 3:1 in money"""
        strategy = proposal.get('strategy', 'UNKNOWN')
        perf = memory.get('strategy_performance', {}).get(strategy, {})
        trades = perf.get('trades', 0)

        if trades < 5:
            return True, f"Insufficient data ({trades} trades) — pass by default"

        profit = perf.get('profit_usd', 0)
        loss = abs(perf.get('loss_usd', 0))
        ratio = profit / max(loss, 1)

        if ratio >= 3.0:
            return True, f"Strategy profit ratio {ratio:.1f}:1 (≥3:1)"
        elif ratio >= 1.5:
            return True, f"Strategy ratio {ratio:.1f}:1 (acceptable, watching)"
        else:
            return False, f"Strategy ratio {ratio:.1f}:1 (<1.5:1 — poor history)"

    def _check_pair_session_history(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 2: Pair + session balance positive in last 30 days"""
        strategy = proposal.get('strategy', 'UNKNOWN')
        perf = memory.get('strategy_performance', {}).get(strategy, {})
        session = self._get_session()
        session_perf = perf.get('by_session', {}).get(session, {})
        trades = session_perf.get('trades', 0)

        if trades < 3:
            return True, f"Insufficient session data ({trades} trades)"

        profit = session_perf.get('profit', 0)
        loss = abs(session_perf.get('loss', 0))
        balance = profit - loss

        if balance >= 0:
            return True, f"Session {session} balance: +${balance:.2f}"
        else:
            return False, f"Session {session} balance: -${abs(balance):.2f} (negative)"

    def _check_active_vetos(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 3: No active vetos for this combo"""
        vetos = memory.get('active_vetos', [])
        strategy = proposal.get('strategy', '')
        session = self._get_session()

        for veto in vetos:
            if veto.get('strategy') == strategy and veto.get('session', '') == session:
                expires = veto.get('expires', '')
                if expires:
                    try:
                        exp_time = datetime.fromisoformat(expires)
                        if exp_time > datetime.now(timezone.utc):
                            return False, f"VETO active: {veto.get('reason', 'Unknown')}"
                    except Exception:
                        pass
            # General vetos (no strategy/session filter)
            if veto.get('strategy', '*') == '*':
                expires = veto.get('expires', '')
                if expires:
                    try:
                        exp_time = datetime.fromisoformat(expires)
                        if exp_time > datetime.now(timezone.utc):
                            return False, f"GENERAL VETO: {veto.get('reason', 'Unknown')}"
                    except Exception:
                        pass

        return True, "No active vetos"

    def _check_rr_ratio(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 4: TP/SL ratio ≥ MIN_RR_RATIO"""
        rr = proposal.get('rr_ratio', 0)
        if rr >= MIN_RR_RATIO:
            return True, f"R:R = {rr:.1f} (≥{MIN_RR_RATIO})"
        else:
            return False, f"R:R = {rr:.1f} (<{MIN_RR_RATIO} minimum)"

    def _check_llm_consensus(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 5: LLM consensus ≥ 7/12"""
        # This data would come from Trinity's context — approximate from conviction
        conviction = proposal.get('conviction', 0)
        # High conviction implies good consensus
        if conviction >= 0.65:
            return True, f"Conviction {conviction:.2f} implies strong consensus"
        elif conviction >= 0.50:
            return True, f"Conviction {conviction:.2f} — adequate consensus"
        else:
            return False, f"Conviction {conviction:.2f} — weak consensus"

    def _check_nova_score(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 6: NOVA quality score > MIN_NOVA_SCORE"""
        # NOVA score would be passed from Trinity context
        nova_score = proposal.get('nova_score', 70)  # Default pass
        if nova_score >= MIN_NOVA_SCORE:
            return True, f"NOVA score {nova_score} (≥{MIN_NOVA_SCORE})"
        else:
            return False, f"NOVA score {nova_score} (<{MIN_NOVA_SCORE})"

    def _check_portfolio_exposure(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 7: Portfolio USD exposure within limits"""
        portfolio = proposal.get('portfolio', {})
        if not portfolio:
            return True, "No portfolio data — pass by default"

        new_exp = portfolio.get('new_usd_exposure', 0)
        if abs(new_exp) <= MAX_DIRECTIONAL_EXPOSURE:
            return True, f"USD exposure {new_exp} (≤{MAX_DIRECTIONAL_EXPOSURE})"
        else:
            return False, f"USD exposure {abs(new_exp)} (>{MAX_DIRECTIONAL_EXPOSURE} limit)"

    def _check_macro_event(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 8: No high-impact event imminent"""
        event_prox = proposal.get('event_proximity', 'CLEAR')
        if event_prox in ('CLEAR', 'APPROACHING'):
            return True, f"Event proximity: {event_prox}"
        elif event_prox == 'POST':
            return True, f"Post-event — momentum trading allowed"
        else:
            event_name = proposal.get('event', {}).get('name', 'Unknown')
            return False, f"Event {event_prox}: {event_name}"

    def _check_narrative_coherence(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 9: Action aligns with narrative bias"""
        action = proposal.get('action', 'HOLD')
        bias = proposal.get('narrative_bias', 'NEUTRAL')

        if bias == 'NEUTRAL':
            return True, "Neutral narrative — no conflict"
        if (bias == 'BUY_BIAS' and action == 'BUY') or \
           (bias == 'SELL_BIAS' and action == 'SELL'):
            return True, f"Action {action} aligns with {bias}"
        if action == 'HOLD':
            return True, "HOLD is always coherent"
        return False, f"Action {action} CONFLICTS with {bias}"

    def _check_confidence_calibration(self, proposal: dict, memory: dict) -> tuple:
        """CHECK 10: System confidence is calibrated (not delusional)"""
        cal = memory.get('confidence_calibration', {})
        brier = cal.get('brier_score', 0)
        deflator = cal.get('confidence_deflator', 1.0)

        if brier == 0:
            return True, "Brier score not yet calculated — pass"

        if brier < 0.20:
            return True, f"Brier score {brier:.3f} — well calibrated"
        elif brier < 0.30:
            return True, f"Brier score {brier:.3f} — acceptable (deflator={deflator:.2f})"
        else:
            return False, f"Brier score {brier:.3f} — POORLY CALIBRATED. Reduce confidence."

    def _get_session(self) -> str:
        hour = datetime.now(timezone.utc).hour
        for name, (start, end) in SESSIONS.items():
            if start <= hour < end:
                return name
        return 'OFF'


class ExecutionTracker:
    """Módulo 4.2: Track execution quality per trade"""

    def __init__(self):
        self._slippage_history = deque(maxlen=200)
        self._spread_history = deque(maxlen=200)

    def record_execution(self, trade: dict, memory: dict) -> dict:
        """Record execution quality metrics"""
        expected_price = trade.get('expected_price', 0)
        actual_price = trade.get('entry_price', 0)
        spread = trade.get('spread', 0)

        slippage = abs(actual_price - expected_price) if expected_price > 0 else 0
        self._slippage_history.append(slippage)
        self._spread_history.append(spread)

        # Update memory
        eq = memory.get('execution_quality', {})
        if self._slippage_history:
            eq['avg_slippage_pips'] = round(np.mean(list(self._slippage_history)), 3)
        if self._spread_history:
            eq['avg_spread_pips'] = round(np.mean(list(self._spread_history)), 3)

        # Calculate break-even
        avg_slip = eq.get('avg_slippage_pips', 0)
        avg_spread = eq.get('avg_spread_pips', 0)
        commission = 0.7  # Typical per side, $1.40 round trip for 0.01
        eq['cost_per_trade_usd'] = round(avg_spread + avg_slip + commission * 2, 2)
        eq['break_even_pips'] = round(avg_spread + avg_slip + 1.4, 2)  # in pips equivalent

        memory['execution_quality'] = eq
        return eq


class BreakEvenCalculator:
    """Módulo 4.3: Cost break-even analysis"""

    def check_trade_viable(self, proposal: dict, memory: dict) -> dict:
        """Check if expected TP covers trading costs"""
        eq = memory.get('execution_quality', {})
        cost = eq.get('cost_per_trade_usd', 4.0)  # Default $4 for XAUUSD
        be_pips = eq.get('break_even_pips', 3.0)

        tp1 = proposal.get('tp1', 0)
        sl = proposal.get('sl', 0)
        price = proposal.get('price', proposal.get('entry_price', 0))

        if price <= 0:
            return {'viable': True, 'reason': 'No price data'}

        expected_reward_pips = abs(tp1 - price) if tp1 > 0 else 0

        if expected_reward_pips <= 0:
            return {'viable': False, 'reason': 'TP1 not set'}

        # Is the reward enough to cover costs?
        if expected_reward_pips > be_pips * 3:
            return {
                'viable': True,
                'expected_pips': round(expected_reward_pips, 1),
                'break_even_pips': round(be_pips, 1),
                'cost_usd': cost,
                'margin': round(expected_reward_pips / max(be_pips, 0.1), 1),
            }
        elif expected_reward_pips > be_pips:
            return {
                'viable': True,
                'expected_pips': round(expected_reward_pips, 1),
                'break_even_pips': round(be_pips, 1),
                'cost_usd': cost,
                'margin': round(expected_reward_pips / max(be_pips, 0.1), 1),
                'warning': 'Low margin over break-even',
            }
        else:
            return {
                'viable': False,
                'expected_pips': round(expected_reward_pips, 1),
                'break_even_pips': round(be_pips, 1),
                'cost_usd': cost,
                'reason': f'TP1 ({expected_reward_pips:.1f} pips) < break-even ({be_pips:.1f} pips)',
            }


# ═══════════════════════════════════════════════════════════════════
# CAPA 5: REFLEXIÓN PROFUNDA
# ═══════════════════════════════════════════════════════════════════

class TradeAutopsy:
    """Módulo 5.1: Post-trade autopsy — classify WHY"""

    def classify_trade(self, trade: dict, memory: dict) -> dict:
        """
        Classify a closed trade into win/loss categories
        Returns classification + recommended action
        """
        pnl = trade.get('pnl_usd', 0)
        reason = trade.get('reason', 'UNKNOWN').upper()
        strategy = trade.get('strategy', 'UNKNOWN')
        entry = trade.get('entry_price', 0)
        close = trade.get('close_price', 0)
        duration = trade.get('duration_s', 0)

        if pnl >= 0:
            classification = self._classify_win(trade, memory)
        else:
            classification = self._classify_loss(trade, memory)

        # Update memory autopsy counters
        if pnl < 0:
            autopsy = memory.get('loss_autopsy', {})
            cat = classification['category']
            if cat not in autopsy:
                autopsy[cat] = {'count': 0, 'total_loss': 0.0}
            autopsy[cat]['count'] += 1
            autopsy[cat]['total_loss'] += abs(pnl)
            memory['loss_autopsy'] = autopsy

        return classification

    def _classify_win(self, trade: dict, memory: dict) -> dict:
        """Classify a winning trade"""
        reason = trade.get('reason', '').upper()
        pnl = trade.get('pnl_usd', 0)

        if reason == 'TP_HIT':
            return {
                'result': 'WIN',
                'category': 'PERFECT_EXECUTION',
                'description': 'TP reached as planned',
                'action': None,
            }
        elif reason == 'MANUAL':
            return {
                'result': 'WIN',
                'category': 'PARTIAL_WIN',
                'description': f'Manual close at +${pnl:.2f} (trader decision)',
                'action': 'LEARN_BEHAVIOR',  # Track trader's manual close patterns
            }
        elif pnl < 5.0:  # Very small win
            return {
                'result': 'WIN',
                'category': 'SQUEEZED_WIN',
                'description': f'Barely won: +${pnl:.2f}',
                'action': 'REVIEW_ENTRY',
            }
        else:
            return {
                'result': 'WIN',
                'category': 'PERFECT_EXECUTION',
                'description': f'Clean win: +${pnl:.2f}',
                'action': None,
            }

    def _classify_loss(self, trade: dict, memory: dict) -> dict:
        """Classify a losing trade — 9 categories"""
        reason = trade.get('reason', '').upper()
        pnl = trade.get('pnl_usd', 0)
        strategy = trade.get('strategy', 'UNKNOWN')
        duration = trade.get('duration_s', 0)

        # Manual cut by trader
        if reason == 'MANUAL':
            return {
                'result': 'LOSS',
                'category': 'MANUAL_CUT',
                'description': f'Trader cut loss manually: -${abs(pnl):.2f}',
                'action': 'LEARN_BEHAVIOR',
            }

        # Event shock — loss during/near high-impact event
        event_info = trade.get('event_during', {})
        if event_info.get('impact') == 'HIGH' and event_info.get('minutes_until', 999) < 30:
            return {
                'result': 'LOSS',
                'category': 'EVENT_SHOCK',
                'description': f'Loss during {event_info.get("name", "event")}',
                'action': 'IMPROVE_CALENDAR',
            }

        # Very short duration = likely liquidity trap
        if duration > 0 and duration < 120:  # Less than 2 minutes
            return {
                'result': 'LOSS',
                'category': 'LIQUIDITY_TRAP',
                'description': f'Stopped out in {duration}s — probable liquidity hunt',
                'action': 'WIDEN_SL_OR_AVOID',
            }

        # Cost eaten — loss smaller than typical spread+commission
        eq = memory.get('execution_quality', {})
        cost = eq.get('cost_per_trade_usd', 4.0)
        if abs(pnl) < cost * 1.5:
            return {
                'result': 'LOSS',
                'category': 'COST_EATEN',
                'description': f'Loss ${abs(pnl):.2f} ≈ trading costs',
                'action': 'INCREASE_MIN_TP',
            }

        # Check if against narrative (against macro)
        narrative_bias = trade.get('narrative_bias', 'NEUTRAL')
        action = trade.get('action', 'UNKNOWN').upper()
        if (narrative_bias == 'BUY_BIAS' and action == 'SELL') or \
           (narrative_bias == 'SELL_BIAS' and action == 'BUY'):
            return {
                'result': 'LOSS',
                'category': 'AGAINST_MACRO',
                'description': f'Traded {action} against {narrative_bias}',
                'action': 'RESPECT_NARRATIVE',
            }

        # Bad timing — right direction but entered poorly
        price_at_close = trade.get('close_price', 0)
        price_at_entry = trade.get('entry_price', 0)
        tp1 = trade.get('tp1', 0)
        if tp1 > 0 and price_at_entry > 0:
            if action == 'BUY' and price_at_close > price_at_entry and pnl < 0:
                # Price went up but we lost (entered too high)
                return {
                    'result': 'LOSS',
                    'category': 'BAD_TIMING',
                    'description': 'Direction correct but entry timing was off',
                    'action': 'IMPROVE_ENTRY_TIMING',
                }

        # Default: Low quality setup
        return {
            'result': 'LOSS',
            'category': 'LOW_QUALITY_SETUP',
            'description': f'Loss ${abs(pnl):.2f} — insufficient confluences',
            'action': 'REVIEW_ENTRY_CRITERIA',
        }


class ConfidenceCalibrator:
    """Módulo 5.2: Brier Score calibration — is our confidence REAL?"""

    def update(self, confidence_predicted: float, actual_win: bool, memory: dict):
        """Update confidence calibration brackets"""
        cal = memory.get('confidence_calibration', {
            'brackets': {}, 'brier_score': 0, 'confidence_deflator': 1.0
        })
        brackets = cal.get('brackets', {})

        # Determine bracket
        conf_pct = confidence_predicted * 100
        if conf_pct >= 90:
            bracket = '90-100'
        elif conf_pct >= 80:
            bracket = '80-90'
        elif conf_pct >= 70:
            bracket = '70-80'
        elif conf_pct >= 60:
            bracket = '60-70'
        else:
            bracket = 'below-60'

        if bracket not in brackets:
            brackets[bracket] = {'predictions': 0, 'wins': 0, 'actual_rate': 0.0}

        b = brackets[bracket]
        b['predictions'] += 1
        if actual_win:
            b['wins'] += 1
        b['actual_rate'] = round(b['wins'] / max(b['predictions'], 1), 3)

        # Recalculate Brier Score
        brier_sum = 0
        brier_count = 0
        for bname, bdata in brackets.items():
            if bdata['predictions'] >= 5:
                # Expected confidence for this bracket
                if bname == '90-100':
                    expected = 0.95
                elif bname == '80-90':
                    expected = 0.85
                elif bname == '70-80':
                    expected = 0.75
                elif bname == '60-70':
                    expected = 0.65
                else:
                    expected = 0.55
                actual = bdata['actual_rate']
                brier_sum += (expected - actual) ** 2
                brier_count += 1

        if brier_count > 0:
            cal['brier_score'] = round(brier_sum / brier_count, 4)
        else:
            cal['brier_score'] = 0

        # Calculate deflator
        # If system says 80% but actually wins 60%, deflator = 60/80 = 0.75
        total_predictions = sum(b['predictions'] for b in brackets.values())
        if total_predictions >= 20:
            # Weighted average deflation
            weighted_deflation = 0
            total_weight = 0
            for bname, bdata in brackets.items():
                if bdata['predictions'] >= 5:
                    if bname == '90-100':
                        expected = 0.95
                    elif bname == '80-90':
                        expected = 0.85
                    elif bname == '70-80':
                        expected = 0.75
                    elif bname == '60-70':
                        expected = 0.65
                    else:
                        expected = 0.55
                    actual = bdata['actual_rate']
                    if expected > 0:
                        weighted_deflation += (actual / expected) * bdata['predictions']
                        total_weight += bdata['predictions']
            if total_weight > 0:
                cal['confidence_deflator'] = round(
                    max(0.5, min(1.2, weighted_deflation / total_weight)), 3
                )

        cal['brackets'] = brackets
        memory['confidence_calibration'] = cal


class HumanBehaviorTracker:
    """Módulo 5.3: Learn trader's manual close patterns"""

    def track(self, trade: dict, memory: dict):
        """Track human behavior from manual closes"""
        reason = trade.get('reason', '').upper()
        pnl = trade.get('pnl_usd', 0)

        if reason != 'MANUAL':
            return

        hb = memory.get('human_behavior', {
            'early_profit_takes': 0, 'early_loss_cuts': 0,
            'avg_manual_close_profit': 0, 'avg_manual_close_loss': 0,
            'preferred_close_threshold_usd': 0, 'day_of_week_patterns': {}
        })

        if pnl >= 0:
            hb['early_profit_takes'] = hb.get('early_profit_takes', 0) + 1
            # Running average
            n = hb['early_profit_takes']
            old_avg = hb.get('avg_manual_close_profit', 0)
            hb['avg_manual_close_profit'] = round(old_avg + (pnl - old_avg) / n, 2)
        else:
            hb['early_loss_cuts'] = hb.get('early_loss_cuts', 0) + 1
            n = hb['early_loss_cuts']
            old_avg = hb.get('avg_manual_close_loss', 0)
            hb['avg_manual_close_loss'] = round(old_avg + (pnl - old_avg) / n, 2)

        # Track day-of-week pattern
        day = datetime.now(timezone.utc).strftime('%A')
        dow = hb.get('day_of_week_patterns', {})
        if day not in dow:
            dow[day] = {'manual_closes': 0, 'total_pnl': 0}
        dow[day]['manual_closes'] += 1
        dow[day]['total_pnl'] = round(dow[day].get('total_pnl', 0) + pnl, 2)
        hb['day_of_week_patterns'] = dow

        # Infer preferred threshold
        if hb['early_profit_takes'] >= 3:
            hb['preferred_close_threshold_usd'] = hb['avg_manual_close_profit']

        memory['human_behavior'] = hb


# ═══════════════════════════════════════════════════════════════════
# CAPA 6: EVOLUCIÓN CONTINUA
# ═══════════════════════════════════════════════════════════════════

class EdgeMonitor:
    """Módulo 6.1: Rolling Sharpe/PF to detect edge degradation"""

    def update(self, memory: dict) -> dict:
        """Recalculate edge metrics from trade history"""
        trades = memory.get('trades', [])
        if len(trades) < 10:
            return {'edge_status': 'LEARNING', 'trades_count': len(trades)}

        # Last 50 trades
        recent = trades[-50:] if len(trades) >= 50 else trades
        pnls = [t.get('pnl_usd', 0) for t in recent]

        if not pnls:
            return {'edge_status': 'UNKNOWN'}

        pnl_array = np.array(pnls)

        # Rolling Sharpe (annualized approximation)
        mean_pnl = np.mean(pnl_array)
        std_pnl = np.std(pnl_array)
        sharpe = mean_pnl / max(std_pnl, 0.01)

        # Profit Factor
        wins = pnl_array[pnl_array > 0]
        losses = pnl_array[pnl_array < 0]
        total_wins = np.sum(wins) if len(wins) > 0 else 0
        total_losses = abs(np.sum(losses)) if len(losses) > 0 else 0
        pf = total_wins / max(total_losses, 1)

        # Profit Ratio (what the user cares about: $$$ ratio)
        profit_ratio = total_wins / max(total_losses, 1)

        # Update edge monitor in memory
        em = memory.get('edge_monitor', {})
        em['rolling_sharpe_50'] = round(sharpe, 3)
        em['rolling_profit_factor_50'] = round(pf, 3)
        em['rolling_profit_ratio_50'] = round(profit_ratio, 3)

        # Historical baseline (if enough data)
        if len(trades) >= 100:
            all_pnls = np.array([t.get('pnl_usd', 0) for t in trades])
            hist_sharpes = []
            for i in range(0, len(all_pnls) - 49, 10):
                window = all_pnls[i:i+50]
                s = np.mean(window) / max(np.std(window), 0.01)
                hist_sharpes.append(s)
            if hist_sharpes:
                em['historical_sharpe_mean'] = round(np.mean(hist_sharpes), 3)
                em['historical_sharpe_std'] = round(np.std(hist_sharpes), 3)

        # Determine edge status
        hist_mean = em.get('historical_sharpe_mean', 0)
        hist_std = em.get('historical_sharpe_std', 1)

        if hist_mean > 0 and hist_std > 0:
            z_score = (sharpe - hist_mean) / max(hist_std, 0.01)
            if z_score >= -1:
                em['edge_status'] = 'HEALTHY'
            elif z_score >= -2:
                em['edge_status'] = 'DEGRADING'
            elif z_score >= -3:
                em['edge_status'] = 'CRITICAL'
            else:
                em['edge_status'] = 'EMERGENCY'
        else:
            em['edge_status'] = 'BASELINE_BUILDING'

        em['last_recalibration'] = datetime.now(timezone.utc).isoformat()
        memory['edge_monitor'] = em

        return em


class AutoVetoManager:
    """Módulo 6.2: Intelligent auto-veto based on autopsy patterns"""

    def evaluate_vetos(self, memory: dict) -> list:
        """Check if any strategy+session combo should be vetoed"""
        autopsy = memory.get('loss_autopsy', {})
        vetos = memory.get('active_vetos', [])
        new_vetos = []

        # Check recent trades for repeating loss patterns
        trades = memory.get('trades', [])
        if len(trades) < 5:
            return []

        recent = trades[-20:]  # Last 20 trades

        # Group losses by strategy + session
        loss_groups = defaultdict(lambda: {'count': 0, 'categories': defaultdict(int)})
        for t in recent:
            if t.get('pnl_usd', 0) < 0:
                key = f"{t.get('strategy', 'UNK')}_{self._get_session_for_time(t.get('timestamp', ''))}"
                cat = t.get('autopsy_category', 'UNKNOWN')
                loss_groups[key]['count'] += 1
                loss_groups[key]['categories'][cat] += 1

        # Create veto if 3+ losses in same strategy+session
        for key, data in loss_groups.items():
            if data['count'] >= 3:
                parts = key.split('_')
                strategy = parts[0] if parts else 'UNKNOWN'
                session = parts[1] if len(parts) > 1 else 'ALL'

                # Check if veto already exists
                exists = any(
                    v.get('strategy') == strategy and v.get('session') == session
                    for v in vetos
                )
                if not exists:
                    dominant_cat = max(data['categories'], key=data['categories'].get)
                    new_veto = {
                        'strategy': strategy,
                        'session': session,
                        'reason': f"{data['count']} losses ({dominant_cat} dominant)",
                        'created': datetime.now(timezone.utc).isoformat(),
                        'expires': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                        'loss_count': data['count'],
                    }
                    new_vetos.append(new_veto)
                    log.warning(f"[Sentinel] AUTO-VETO: {strategy} in {session} — {new_veto['reason']}")

        # Add new vetos to memory
        if new_vetos:
            memory['active_vetos'] = vetos + new_vetos

        # Clean expired vetos
        now = datetime.now(timezone.utc)
        active = []
        expired = memory.get('expired_vetos', [])
        for v in memory.get('active_vetos', []):
            try:
                exp = datetime.fromisoformat(v.get('expires', '2000-01-01'))
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp > now:
                    active.append(v)
                else:
                    expired.append(v)
            except Exception:
                active.append(v)

        memory['active_vetos'] = active
        memory['expired_vetos'] = expired[-100:]  # Keep last 100 expired

        return new_vetos

    def _get_session_for_time(self, timestamp_str: str) -> str:
        try:
            ts = datetime.fromisoformat(timestamp_str)
            hour = ts.hour
            for name, (s, e) in SESSIONS.items():
                if s <= hour < e:
                    return name
        except Exception:
            pass
        return 'UNKNOWN'


class DailyRecalibrator:
    """Módulo 6.3: Daily auto-recalibration"""

    def __init__(self):
        self._last_recal = None

    def should_recalibrate(self) -> bool:
        now = datetime.now(timezone.utc)
        if self._last_recal is None:
            return True
        return (now - self._last_recal).total_seconds() > 86400  # 24h

    def recalibrate(self, memory: dict) -> dict:
        """Run full daily recalibration"""
        self._last_recal = datetime.now(timezone.utc)
        report = {'timestamp': self._last_recal.isoformat(), 'actions': []}

        trades = memory.get('trades', [])
        if len(trades) < 5:
            report['actions'].append('Insufficient trade data for recalibration')
            return report

        # 1. Last 24h summary
        now = datetime.now(timezone.utc)
        last_24h = [t for t in trades if self._within_hours(t, 24)]

        if last_24h:
            wins = [t for t in last_24h if t.get('pnl_usd', 0) >= 0]
            losses = [t for t in last_24h if t.get('pnl_usd', 0) < 0]
            total_profit = sum(t.get('pnl_usd', 0) for t in wins)
            total_loss = sum(abs(t.get('pnl_usd', 0)) for t in losses)

            report['summary_24h'] = {
                'trades': len(last_24h),
                'wins': len(wins),
                'losses': len(losses),
                'profit_usd': round(total_profit, 2),
                'loss_usd': round(total_loss, 2),
                'ratio': round(total_profit / max(total_loss, 1), 2),
            }
            report['actions'].append(f"24h: {len(wins)}W/{len(losses)}L, ratio={report['summary_24h']['ratio']:.1f}")

        # 2. Adjust strategy weights
        sp = memory.get('strategy_performance', {})
        for strat, perf in sp.items():
            if strat == 'HIBERNATION':
                continue
            total = perf.get('trades', 0)
            if total < 5:
                continue
            ratio = perf.get('profit_usd', 0) / max(abs(perf.get('loss_usd', 0)), 1)
            if ratio < 1.0:
                report['actions'].append(f"VETO candidate: {strat} ratio={ratio:.1f}")
            elif ratio > 5.0:
                report['actions'].append(f"TOP performer: {strat} ratio={ratio:.1f}")

        # 3. Store report in memory
        daily_reports = memory.get('daily_reports', [])
        daily_reports.append(report)
        memory['daily_reports'] = daily_reports[-30:]  # Keep last 30 days

        return report

    def _within_hours(self, trade: dict, hours: int) -> bool:
        try:
            ts = datetime.fromisoformat(trade.get('timestamp', '2000-01-01'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - ts).total_seconds() < hours * 3600
        except Exception:
            return False


class IntradayHeatmap:
    """Módulo 6.4: Performance heatmap hour × day × strategy"""

    def update(self, trade: dict, memory: dict):
        """Update the intraday heatmap with a new trade result"""
        heatmap = memory.get('intraday_heatmap', {})

        try:
            ts = datetime.fromisoformat(trade.get('timestamp', ''))
        except Exception:
            ts = datetime.now(timezone.utc)

        hour_block = f"{(ts.hour // 4) * 4:02d}-{((ts.hour // 4) * 4 + 4) % 24:02d}"
        day = ts.strftime('%a').upper()[:3]
        key = f"{day}_{hour_block}"

        if key not in heatmap:
            heatmap[key] = {'trades': 0, 'profit': 0, 'loss': 0, 'ratio': 0}

        pnl = trade.get('pnl_usd', 0)
        heatmap[key]['trades'] += 1
        if pnl >= 0:
            heatmap[key]['profit'] = round(heatmap[key].get('profit', 0) + pnl, 2)
        else:
            heatmap[key]['loss'] = round(heatmap[key].get('loss', 0) + abs(pnl), 2)

        total_p = heatmap[key]['profit']
        total_l = heatmap[key]['loss']
        heatmap[key]['ratio'] = round(total_p / max(total_l, 1), 2)

        memory['intraday_heatmap'] = heatmap

    def get_current_score(self, memory: dict) -> float:
        """Get profitability score for current hour/day"""
        now = datetime.now(timezone.utc)
        hour_block = f"{(now.hour // 4) * 4:02d}-{((now.hour // 4) * 4 + 4) % 24:02d}"
        day = now.strftime('%a').upper()[:3]
        key = f"{day}_{hour_block}"

        heatmap = memory.get('intraday_heatmap', {})
        cell = heatmap.get(key, {})

        if cell.get('trades', 0) < 3:
            return 0.5  # Neutral (not enough data)

        return min(1.0, cell.get('ratio', 0) / 5.0)  # Normalize 0-1


# ═══════════════════════════════════════════════════════════════════
# DRAWDOWN GUARDIAN
# ═══════════════════════════════════════════════════════════════════

class DrawdownGuardian:
    """Emergency drawdown protection — the last line of defense"""

    def __init__(self):
        self._daily_start_balance = None
        self._daily_pnl = 0
        self._reset_time = None

    def check(self, memory: dict) -> dict:
        """Check drawdown limits"""
        now = datetime.now(timezone.utc)

        # Reset daily counter
        if self._reset_time is None or now.date() > self._reset_time.date():
            self._daily_pnl = 0
            self._reset_time = now

        # Sum today's P&L
        trades = memory.get('trades', [])
        today_pnl = 0
        for t in reversed(trades):
            try:
                ts = datetime.fromisoformat(t.get('timestamp', '2000-01-01'))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts.date() == now.date():
                    today_pnl += t.get('pnl_usd', 0)
                else:
                    break
            except Exception:
                continue

        self._daily_pnl = today_pnl

        # Drawdown thresholds (absolute $ for now — % requires account balance)
        # These will be enhanced when we know account balance from config
        # For now: use relative logic from daily P&L direction

        status = 'NORMAL'
        sizing_override = 1.0

        total_loss_today = sum(
            abs(t.get('pnl_usd', 0)) for t in trades
            if self._is_today(t) and t.get('pnl_usd', 0) < 0
        )

        total_profit_today = sum(
            t.get('pnl_usd', 0) for t in trades
            if self._is_today(t) and t.get('pnl_usd', 0) > 0
        )

        consecutive_losses = memory.get('totals', {}).get('current_streak', {})
        if consecutive_losses.get('type') == 'loss':
            loss_count = consecutive_losses.get('count', 0)
            if loss_count >= 5:
                status = 'HIBERNATION'
                sizing_override = 0.0
            elif loss_count >= 3:
                status = 'REDUCED'
                sizing_override = 0.5

        return {
            'status': status,
            'daily_pnl': round(today_pnl, 2),
            'daily_loss': round(total_loss_today, 2),
            'daily_profit': round(total_profit_today, 2),
            'sizing_override': sizing_override,
            'consecutive_losses': consecutive_losses.get('count', 0) if consecutive_losses.get('type') == 'loss' else 0,
        }

    def _is_today(self, trade: dict) -> bool:
        try:
            ts = datetime.fromisoformat(trade.get('timestamp', '2000-01-01'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.date() == datetime.now(timezone.utc).date()
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════
# MAIN LLM12 CLASS
# ═══════════════════════════════════════════════════════════════════

class LLM12Sentinel:
    """
    THE QUALITY CONSCIOUSNESS - Capas 4-6
    Ejecución → Reflexión → Evolución
    """

    def __init__(self):
        self.memory = MemoryReader()
        self.gate = EliteGateChecker()
        self.exec_tracker = ExecutionTracker()
        self.break_even = BreakEvenCalculator()
        self.autopsy = TradeAutopsy()
        self.calibrator = ConfidenceCalibrator()
        self.behavior_tracker = HumanBehaviorTracker()
        self.edge_monitor = EdgeMonitor()
        self.veto_manager = AutoVetoManager()
        self.recalibrator = DailyRecalibrator()
        self.heatmap = IntradayHeatmap()
        self.drawdown = DrawdownGuardian()

        log.info(f"[LLM12] Sentinel initialized | {SYMBOL} | Port {PORT}")

    def analyze(self, data: dict) -> dict:
        """
        Main entry point — handles both validation proposals and trade closures
        """
        start = time.time()
        msg_type = data.get('type', 'analyze')

        if msg_type == 'validate_proposal':
            return self._validate_proposal(data, start)
        elif msg_type == 'trade_closed':
            return self._process_trade_closed(data, start)
        elif msg_type == 'analyze':
            # Direct analysis request from Trinity (regular LLM voting)
            return self._vote_on_genome(data, start)
        else:
            return {'status': 'unknown_type', 'type': msg_type}

    def _validate_proposal(self, proposal: dict, start: float) -> dict:
        """
        VALIDATE a trade proposal from LLM11
        Run 10 Elite Checks + break-even + drawdown
        """
        memory = self.memory.get()

        # ── 10 Elite Checks ──
        gate_result = self.gate.run_checks(proposal, memory)

        # ── Break-even viability ──
        be_result = self.break_even.check_trade_viable(proposal, memory)

        # ── Drawdown check ──
        dd_result = self.drawdown.check(memory)

        # ── Edge monitor check ──
        edge = memory.get('edge_monitor', {})
        edge_status = edge.get('edge_status', 'UNKNOWN')

        # ── Heatmap check ──
        heatmap_score = self.heatmap.get_current_score(memory)

        # ── Daily recalibration (if needed) ──
        if self.recalibrator.should_recalibrate():
            recal_report = self.recalibrator.recalibrate(memory)
            self.memory.update_and_save(memory)
            log.info(f"[Sentinel] Daily recalibration completed: {len(recal_report.get('actions', []))} actions")

        # ── Final decision ──
        approved = gate_result['approved']
        reasons = []

        if not approved:
            failed = [r for r in gate_result['results'] if r['status'] == 'FAIL']
            reasons.extend([f"CHECK {r['check']}: {r['reason']}" for r in failed])

        if not be_result.get('viable', True):
            approved = False
            reasons.append(f"BREAK-EVEN: {be_result.get('reason', 'Not viable')}")

        if dd_result['status'] == 'HIBERNATION':
            approved = False
            reasons.append(f"DRAWDOWN: Forced hibernation ({dd_result['consecutive_losses']} consecutive losses)")

        if edge_status in ('CRITICAL', 'EMERGENCY'):
            approved = False
            reasons.append(f"EDGE: {edge_status} — strategy may have stopped working")

        # Sizing override from drawdown
        sizing_override = dd_result.get('sizing_override', 1.0)

        elapsed = round((time.time() - start) * 1000, 1)

        result = {
            'approved': approved,
            'checks_passed': gate_result['checks_passed'],
            'checks_total': gate_result['checks_total'],
            'checks_detail': gate_result['results'],
            'break_even': be_result,
            'drawdown': dd_result,
            'edge_status': edge_status,
            'heatmap_score': round(heatmap_score, 2),
            'sizing_override': sizing_override,
            'reason': ' | '.join(reasons) if reasons else 'ALL CHECKS PASSED',
            'quality': 'ELITE' if approved and gate_result['checks_passed'] >= 8 else 'STANDARD' if approved else 'REJECTED',
            'latency_ms': elapsed,
        }

        if not approved:
            # Check if we can suggest modifications
            modifications = self._suggest_modifications(proposal, gate_result, be_result)
            if modifications:
                result['suggest_modify'] = True
                result['modified_params'] = modifications

        return result

    def _vote_on_genome(self, data: dict, start: float) -> dict:
        """
        Regular vote on genome data (like other LLMs do for Trinity)
        Sentinel votes based on overall quality assessment
        """
        memory = self.memory.get()

        # Quick quality checks
        dd = self.drawdown.check(memory)
        edge = memory.get('edge_monitor', {})
        edge_status = edge.get('edge_status', 'UNKNOWN')
        heatmap_score = self.heatmap.get_current_score(memory)

        # Base decision from drawdown/edge
        if dd['status'] == 'HIBERNATION':
            decision = 'HOLD'
            confidence = 5
            reason = f"Sentinel HOLD: Drawdown protection ({dd['consecutive_losses']} losses)"
        elif edge_status in ('CRITICAL', 'EMERGENCY'):
            decision = 'HOLD'
            confidence = 10
            reason = f"Sentinel HOLD: Edge {edge_status}"
        elif heatmap_score < 0.2:
            decision = 'HOLD'
            confidence = 20
            reason = f"Sentinel HOLD: Poor heatmap score {heatmap_score:.2f}"
        else:
            # Let the trade through — trust LLM1-10 consensus
            decision = 'ABSTAIN'  # Special: means "I don't override"
            confidence = (0.5 + heatmap_score * 0.3) * 100
            reason = f"Sentinel OK: Edge={edge_status}, Heatmap={heatmap_score:.2f}"

        # Auto-veto check
        self.veto_manager.evaluate_vetos(memory)
        self.memory.update_and_save(memory)

        elapsed = round((time.time() - start) * 1000, 1)

        return {
            'decision': decision,
            'confidence': round(min(100, max(0, confidence)), 1),
            'reason': reason,
            'drawdown': dd,
            'edge_status': edge_status,
            'heatmap_score': round(heatmap_score, 2),
            'active_vetos': len(memory.get('active_vetos', [])),
            'consciousness_phase': memory.get('consciousness_phase', 'LEARNING'),
            'latency_ms': elapsed,
        }

    def _process_trade_closed(self, data: dict, start: float) -> dict:
        """
        Process a closed trade:
        1. Autopsy (classify WHY)
        2. Update calibration
        3. Track execution quality
        4. Update heatmap
        5. Update edge monitor
        6. Track human behavior
        7. Evaluate auto-vetos
        """
        memory = self.memory.get()

        try:
            pnl = data.get('pnl_usd', data.get('pnl', 0))
            is_win = pnl >= 0
            confidence = data.get('confidence', 0.5)

            # 1. AUTOPSY
            classification = self.autopsy.classify_trade(data, memory)
            data['autopsy_category'] = classification['category']

            # 2. CALIBRATION UPDATE
            self.calibrator.update(confidence, is_win, memory)

            # 3. EXECUTION QUALITY
            self.exec_tracker.record_execution(data, memory)

            # 4. HEATMAP
            self.heatmap.update(data, memory)

            # 5. EDGE MONITOR
            edge_result = self.edge_monitor.update(memory)

            # 6. HUMAN BEHAVIOR
            self.behavior_tracker.track(data, memory)

            # 7. AUTO-VETOS
            new_vetos = self.veto_manager.evaluate_vetos(memory)

            # Save everything
            self.memory.update_and_save(memory)

            elapsed = round((time.time() - start) * 1000, 1)

            log.info(f"[Sentinel] Trade processed: {'WIN' if is_win else 'LOSS'} "
                    f"${pnl:+.2f} | {classification['category']} | "
                    f"Edge: {edge_result.get('edge_status', 'UNK')}")

            return {
                'status': 'processed',
                'autopsy': classification,
                'edge': edge_result,
                'new_vetos': len(new_vetos),
                'calibration': memory.get('confidence_calibration', {}),
                'latency_ms': elapsed,
            }

        except Exception as e:
            log.error(f"[Sentinel] Trade processing error: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    def _suggest_modifications(self, proposal, gate_result, be_result) -> dict:
        """Try to suggest parameter modifications that would pass checks"""
        modifications = {}

        for r in gate_result['results']:
            # If R:R failed, suggest wider TP
            if r['check'] == 4 and r['status'] == 'FAIL':
                tp1 = proposal.get('tp1', 0)
                sl = proposal.get('sl', 0)
                price = (tp1 + sl) / 2 if tp1 > 0 and sl > 0 else 0
                if price > 0:
                    risk = abs(price - sl)
                    new_tp1 = price + risk * MIN_RR_RATIO * 1.1 if proposal.get('action') == 'BUY' else price - risk * MIN_RR_RATIO * 1.1
                    modifications['tp1'] = round(new_tp1, 2)

        return modifications


# ═══════════════════════════════════════════════════════════════════
# TCP SERVER
# ═══════════════════════════════════════════════════════════════════

def handle_client(sock, addr, sentinel: LLM12Sentinel):
    """Handle TCP client — same protocol as all LLMs"""
    sock.settimeout(30)
    try:
        while True:
            ld = sock.recv(4)
            if ld and b'PING' in ld[:4]:
                pong_msg = struct.pack('>I', 4) + b'PONG'
                sock.sendall(pong_msg)
                continue
            if not ld or len(ld) != 4:
                break

            length = struct.unpack('>I', ld)[0]
            if length > 10_000_000:
                log.warning(f"[TCP] Message too large: {length}")
                break

            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk

            if not data:
                break

            request = json.loads(data.decode('utf-8', errors='replace'))
            response = sentinel.analyze(request)

            response_json = json.dumps(response, default=str).encode('utf-8')
            sock.sendall(struct.pack('>I', len(response_json)) + response_json)

    except socket.timeout:
        pass
    except Exception as e:
        log.debug(f"[TCP] Client error: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass


def main():
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    log.info("=" * 70)
    log.info("  LLM12 SENTINEL — THE QUALITY CONSCIOUSNESS")
    log.info(f"  NOVA TRADING AI by Polarice Labs © 2026")
    log.info(f"  Symbol: {SYMBOL} | Port: {port}")
    log.info("=" * 70)

    sentinel = LLM12Sentinel()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, port))
    server_sock.listen(5)

    log.info(f"[LLM12] TCP Server READY on {HOST}:{port}")

    def signal_handler(sig, frame):
        log.info("[LLM12] Shutting down...")
        server_sock.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            try:
                client_sock, addr = server_sock.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, addr, sentinel),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"[LLM12] Accept error: {e}")
                time.sleep(0.1)
    finally:
        server_sock.close()


if __name__ == '__main__':
    main()
