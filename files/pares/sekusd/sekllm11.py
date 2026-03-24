#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║             🧠 NOVA TRADING AI - LLM11 STRATEGIST GURU "EINSTEIN MODE"         ║
║                         THE TRADING CONSCIOUSNESS                              ║
║                    Capas 0-3: Percepción → Decisión                            ║
║                       by Polarice Labs © 2026                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  CAPA 0: PERCEPCIÓN TOTAL (Macro, Cross-Asset, ML Models, Guru File)           ║
║  CAPA 1: COMPRENSIÓN PROFUNDA (Narrativa, Causa-Efecto)                        ║
║  CAPA 2: PROYECCIÓN INTELIGENTE (Escenarios, Fases)                            ║
║  CAPA 3: DECISIÓN ESTRATÉGICA (10-Dim Strategy, Conviction, TP/SL)             ║
║                                                                                ║
║  Port: 5568 (TCP) | Python Deterministic + Optional Ollama Enhancement         ║
║  Protocol: 4-byte big-endian length prefix + UTF-8 JSON                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import socket, struct, json, logging, threading, time, os, re, math, signal, sys
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
import os
from pathlib import Path

# Optional Ollama
try:
    import requests as http_requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Optional shared brain
try:
    import nova_shared_brain as shared_brain
    SHARED_BRAIN_AVAILABLE = True
except ImportError:
    SHARED_BRAIN_AVAILABLE = False

os.makedirs('logs', exist_ok=True)
_log_file = f'logs/llm11_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
_file_handler = logging.FileHandler(_log_file, encoding='utf-8')
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s | 🧠 LLM11 GURU | %(message)s", datefmt='%H:%M:%S')
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger()
log.info(f"[INIT] Log file: {_log_file}")
# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

PORT = 8667
HOST = '127.0.0.1'
SYMBOL = 'SEKUSD'
SENTINEL_PORT = 8668

OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3:8b"  # 🔧 FIX 09/03: 70b no disponible en Ollama local — STRATEGIST (peso 2.0) nunca votaba
OLLAMA_TIMEOUT = 5.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GURU_FILE = os.path.join(BASE_DIR, 'estrategia_guru.txt')
MEMORY_FILE = os.path.join(BASE_DIR, f'memoria_{SYMBOL}.json')
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) != 'proyecto_quimera' else BASE_DIR
CALENDAR_FILE = os.path.join(BASE_DIR, 'economic_calendar.json') if os.path.exists(os.path.join(BASE_DIR, 'economic_calendar.json')) else os.path.join(PROJECT_ROOT, 'economic_calendar.json')

# DXY ICE Index weights (official)
DXY_WEIGHTS = {
    'EURUSD': -0.576,
    'USDJPY': 0.136,
    'GBPUSD': -0.119,
    'USDCAD': 0.091,
    'CHFUSD': 0.036,
    # SEKUSD: 0.042 — not in our system, absorbed into constant
}
DXY_CONSTANT = 50.14348

# Strategy catalog
STRATEGIES = [
    'SCALPING_PULSE', 'SWING_STRUCTURE', 'BREAKOUT_MOMENTUM',
    'HARMONIC_REVERSAL', 'SMART_MONEY_HUNT', 'NEWS_MOMENTUM',
    'FADE_LIQUIDATION', 'TREND_CONTINUATION', 'MEAN_REVERSION',
    'HIBERNATION'
]

SESSIONS = {
    'ASIA':     (0, 8),
    'LONDON':   (8, 12),
    'OVERLAP':  (12, 17),
    'NEW_YORK': (17, 21),
    'OFF':      (21, 24),
}

CONVICTION_LEVELS = {
    'BLOCK':     (0.0,  0.30),
    'MICRO':     (0.30, 0.50),
    'NORMAL':    (0.50, 0.70),
    'REINFORCED':(0.70, 0.85),
    'MAXIMUM':   (0.85, 0.95),
    'KILLER':    (0.95, 1.01),
}


# ═══════════════════════════════════════════════════════════════════
# CAPA 0: PERCEPCIÓN TOTAL
# ═══════════════════════════════════════════════════════════════════

class MacroRadar:
    """Módulo 0.1: Calendario económico 100% local"""

    def __init__(self):
        self.calendar = self._load_calendar()
        self._last_reload = time.time()
        self.RELOAD_INTERVAL = 300  # re-read file every 5 min

    def _load_calendar(self):
        try:
            with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"[MacroRadar] Cannot load calendar: {e}")
            return {"recurring_events": [], "custom_events": []}

    def _maybe_reload(self):
        if time.time() - self._last_reload > self.RELOAD_INTERVAL:
            self.calendar = self._load_calendar()
            self._last_reload = time.time()

    def get_next_event(self, symbol: str) -> dict:
        """Returns next relevant HIGH/MEDIUM impact event for this symbol"""
        self._maybe_reload()
        now = datetime.now(timezone.utc)
        best = None
        best_minutes = float('inf')

        for evt in self.calendar.get('recurring_events', []):
            if evt.get('impact', 'LOW') == 'LOW':
                continue
            affected = evt.get('affected_pairs', [])
            if symbol not in affected and 'ALL' not in [e.upper() for e in affected]:
                continue

            next_time = self._next_occurrence(evt, now)
            if next_time is None:
                continue

            minutes_until = (next_time - now).total_seconds() / 60.0
            if 0 < minutes_until < best_minutes:
                best_minutes = minutes_until
                best = {
                    'name': evt.get('name', 'Unknown'),
                    'currency': evt.get('currency', ''),
                    'impact': evt.get('impact', 'MEDIUM'),
                    'time_utc': next_time.isoformat(),
                    'minutes_until': round(minutes_until, 1),
                    'block_before': evt.get('block_minutes_before', 15),
                    'observe_after': evt.get('observation_minutes_after', 5),
                    'avg_move_pips': evt.get('avg_move_pips', {}).get(symbol, 0),
                }

        # Also check custom_events
        for evt in self.calendar.get('custom_events', []):
            if symbol not in evt.get('affected_pairs', []):
                continue
            try:
                evt_time = datetime.fromisoformat(evt['datetime']).replace(tzinfo=timezone.utc)
                minutes_until = (evt_time - now).total_seconds() / 60.0
                if 0 < minutes_until < best_minutes:
                    best_minutes = minutes_until
                    best = {
                        'name': evt.get('name', 'Custom'),
                        'currency': evt.get('currency', ''),
                        'impact': evt.get('impact', 'HIGH'),
                        'time_utc': evt_time.isoformat(),
                        'minutes_until': round(minutes_until, 1),
                        'block_before': evt.get('block_minutes_before', 15),
                        'observe_after': evt.get('observation_minutes_after', 5),
                        'avg_move_pips': evt.get('avg_move_pips', {}).get(symbol, 0),
                    }
            except Exception:
                continue

        return best or {'name': 'CLEAR', 'minutes_until': 999, 'impact': 'NONE', 'block_before': 0}

    def _next_occurrence(self, evt: dict, now: datetime) -> datetime:
        """Calculate next occurrence of a recurring event"""
        schedule = evt.get('schedule', '')
        time_str = evt.get('time_utc', '13:30')
        h, m = int(time_str.split(':')[0]), int(time_str.split(':')[1])

        try:
            if schedule == 'first_friday':
                return self._next_nth_weekday(now, 4, 1, h, m)  # Friday=4, 1st
            elif schedule == 'every_thursday':
                return self._next_weekday(now, 3, h, m)  # Thursday=3
            elif schedule == 'every_weekday':
                return self._next_weekday_any(now, h, m)
            elif schedule == 'first_business_day':
                return self._next_nth_business_day(now, 1, h, m)
            elif schedule in ('mid_month', 'second_tuesday_or_wednesday'):
                return self._next_mid_month(now, h, m)
            elif schedule in ('end_of_month_quarterly', 'last_friday_of_month'):
                return self._next_end_month(now, h, m)
            elif schedule.endswith('_schedule'):
                # Named schedules: fomc_schedule, ecb_schedule, etc.
                key = schedule.replace('_schedule', '') + '_dates_2026'
                dates = self.calendar.get(key, [])
                return self._next_from_datelist(dates, now, h, m)
            else:
                return None
        except Exception:
            return None

    def _next_nth_weekday(self, now, weekday, nth, h, m):
        """Next Nth occurrence of weekday in a month (e.g., 1st Friday)"""
        for month_offset in range(3):
            year = now.year
            month = now.month + month_offset
            if month > 12:
                month -= 12
                year += 1
            first_day = datetime(year, month, 1, h, m, tzinfo=timezone.utc)
            days_ahead = (weekday - first_day.weekday()) % 7
            target = first_day + timedelta(days=days_ahead + 7 * (nth - 1))
            if target > now:
                return target
        return None

    def _next_weekday(self, now, weekday, h, m):
        days_ahead = (weekday - now.weekday()) % 7
        if days_ahead == 0 and now.hour >= h:
            days_ahead = 7
        return datetime(now.year, now.month, now.day, h, m, tzinfo=timezone.utc) + timedelta(days=days_ahead)

    def _next_weekday_any(self, now, h, m):
        target = datetime(now.year, now.month, now.day, h, m, tzinfo=timezone.utc)
        if target <= now:
            target += timedelta(days=1)
        while target.weekday() >= 5:  # Skip weekends
            target += timedelta(days=1)
        return target

    def _next_nth_business_day(self, now, nth, h, m):
        for month_offset in range(3):
            year = now.year
            month = now.month + month_offset
            if month > 12:
                month -= 12
                year += 1
            day = datetime(year, month, 1, h, m, tzinfo=timezone.utc)
            count = 0
            while count < nth:
                if day.weekday() < 5:
                    count += 1
                if count < nth:
                    day += timedelta(days=1)
            if day > now:
                return day
        return None

    def _next_mid_month(self, now, h, m):
        for month_offset in range(3):
            year = now.year
            month = now.month + month_offset
            if month > 12:
                month -= 12
                year += 1
            target = datetime(year, month, 13, h, m, tzinfo=timezone.utc)
            if target > now:
                return target
        return None

    def _next_end_month(self, now, h, m):
        for month_offset in range(3):
            year = now.year
            month = now.month + month_offset
            if month > 12:
                month -= 12
                year += 1
            # Last business day of month
            if month == 12:
                last_day = datetime(year + 1, 1, 1, h, m, tzinfo=timezone.utc) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1, h, m, tzinfo=timezone.utc) - timedelta(days=1)
            while last_day.weekday() >= 5:
                last_day -= timedelta(days=1)
            last_day = last_day.replace(hour=h, minute=m)
            if last_day > now:
                return last_day
        return None

    def _next_from_datelist(self, dates, now, h, m):
        for d_str in sorted(dates):
            try:
                d = datetime.strptime(d_str, '%Y-%m-%d').replace(hour=h, minute=m, tzinfo=timezone.utc)
                if d > now:
                    return d
            except Exception:
                continue
        return None

    def get_event_proximity(self, symbol: str) -> str:
        """CLEAR / APPROACHING / IMMINENT / DURING / POST"""
        evt = self.get_next_event(symbol)
        mins = evt.get('minutes_until', 999)
        block = evt.get('block_before', 15)

        if mins > 120:
            return 'CLEAR'
        elif mins > block:
            return 'APPROACHING'
        elif mins > 0:
            return 'IMMINENT'
        elif mins > -evt.get('observe_after', 5):
            return 'DURING'
        else:
            return 'POST'


class CrossAssetRadar:
    """Módulo 0.2: Cross-asset awareness via nova_shared_brain.py SQLite"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self._price_cache = {}
        self._last_update = 0

    def get_portfolio_state(self) -> dict:
        """Read all open positions and prices from SharedBrain SQLite"""
        if not SHARED_BRAIN_AVAILABLE:
            return {'positions': [], 'dxy_proxy': 0, 'usd_exposure': 0}

        try:
            # Read regime_states (has last_action, open_positions per symbol)
            overview = shared_brain.get_system_overview()
            regimes = overview.get('regimes', [])

            positions = []
            prices = {}
            for r in regimes:
                sym = r.get('symbol', '')
                prices[sym] = r.get('atr', 0)  # We store price nearby
                if r.get('open_positions', 0) > 0:
                    positions.append({
                        'symbol': sym,
                        'action': r.get('last_action', 'UNKNOWN'),
                        'count': r.get('open_positions', 0),
                    })

            # Calculate DXY proxy from pair prices stored in SharedBrain
            dxy = self._calc_dxy_proxy(prices)

            # Calculate USD directional exposure
            usd_exp = self._calc_usd_exposure(positions)

            return {
                'positions': positions,
                'dxy_proxy': round(dxy, 2),
                'usd_exposure': usd_exp,
                'total_open': sum(p['count'] for p in positions),
                'correlated_risk': self._check_correlated_risk(positions),
            }
        except Exception as e:
            log.debug(f"[CrossAsset] Error: {e}")
            return {'positions': [], 'dxy_proxy': 0, 'usd_exposure': 0}

    def _calc_dxy_proxy(self, prices: dict) -> float:
        """
        DXY ≈ 50.14348 × EURUSD^(-0.576) × USDJPY^(0.136)
                        × GBPUSD^(-0.119) × USDCAD^(0.091) × CHFUSD^(0.036)
        """
        try:
            # We need to get actual prices from SharedBrain regime_states
            # Since regime_states doesn't store raw price, we read from trade_outcomes
            # or from the genome data cached. For now use reasonable defaults.
            eurusd = prices.get('EURUSD', 1.08)
            usdjpy = prices.get('USDJPY', 150.0)
            gbpusd = prices.get('GBPUSD', 1.27)
            usdcad = prices.get('USDCAD', 1.36)
            chfusd = prices.get('CHFUSD', 1.13)

            if eurusd <= 0 or usdjpy <= 0 or gbpusd <= 0:
                return 104.0  # Reasonable default

            dxy = DXY_CONSTANT
            dxy *= (eurusd ** DXY_WEIGHTS['EURUSD'])
            dxy *= (usdjpy ** DXY_WEIGHTS['USDJPY'])
            dxy *= (gbpusd ** DXY_WEIGHTS['GBPUSD'])
            dxy *= (usdcad ** DXY_WEIGHTS['USDCAD'])
            dxy *= (chfusd ** DXY_WEIGHTS['CHFUSD'])

            return dxy
        except Exception:
            return 104.0

    def _calc_usd_exposure(self, positions: list) -> int:
        """
        Positive = LONG USD, Negative = SHORT USD
        BUY EURUSD = SHORT USD (-1), SELL EURUSD = LONG USD (+1)
        BUY XAUUSD = SHORT USD (-1), BUY USDJPY = LONG USD (+1)
        """
        USD_DIRECTION = {
            # symbol: {BUY: usd_direction, SELL: usd_direction}
            'XAUUSD': {'BUY': -1, 'SELL': 1},
            'EURUSD': {'BUY': -1, 'SELL': 1},
            'GBPUSD': {'BUY': -1, 'SELL': 1},
            'AUDUSD': {'BUY': -1, 'SELL': 1},
            'NZDUSD': {'BUY': -1, 'SELL': 1},
            'CHFUSD': {'BUY': -1, 'SELL': 1},
            'USDJPY': {'BUY': 1, 'SELL': -1},
            'USDCAD': {'BUY': 1, 'SELL': -1},
            'BTCUSD': {'BUY': -1, 'SELL': 1},
            'US30USD':{'BUY': -1, 'SELL': 1},
        }
        exposure = 0
        for p in positions:
            sym = p['symbol']
            act = p.get('action', '').upper()
            if act in ('BUY', 'SELL') and sym in USD_DIRECTION:
                exposure += USD_DIRECTION[sym].get(act, 0) * p.get('count', 1)
        return exposure

    def _check_correlated_risk(self, positions: list) -> str:
        """Check if positions are dangerously correlated"""
        if len(positions) < 2:
            return 'LOW'

        # Count USD shorts vs longs
        usd_exp = self._calc_usd_exposure(positions)
        if abs(usd_exp) >= 3:
            return 'CRITICAL'
        elif abs(usd_exp) >= 2:
            return 'HIGH'
        elif abs(usd_exp) >= 1:
            return 'MODERATE'
        return 'LOW'

    def update_price_cache(self, data: dict):
        """Update internal price cache from genome data"""
        price = data.get('price', data.get('bid', 0))
        if price > 0:
            self._price_cache[self.symbol] = price


class GuruFileReader:
    """Módulo 0.4: Read human strategy instructions"""

    def __init__(self):
        self._last_mtime = 0
        self._rules = []
        self._observations = []
        self._bias = 'NEUTRAL'
        self._raw_text = ''
        self._reload()

    def _reload(self):
        try:
            if not os.path.exists(GURU_FILE):
                return
            mtime = os.path.getmtime(GURU_FILE)
            if mtime <= self._last_mtime:
                return
            self._last_mtime = mtime

            with open(GURU_FILE, 'r', encoding='utf-8') as f:
                self._raw_text = f.read()

            self._rules = self._extract_section('REGLAS')
            self._observations = self._extract_section('OBSERVACIONES')
            bias_text = self._extract_section('SESGO')
            if bias_text:
                combined = ' '.join(bias_text).lower()
                if 'alcista' in combined or 'bullish' in combined or 'compra' in combined:
                    self._bias = 'BULLISH'
                elif 'bajista' in combined or 'bearish' in combined or 'venta' in combined:
                    self._bias = 'BEARISH'
                else:
                    self._bias = 'NEUTRAL'

            log.info(f"[Guru] Reloaded: {len(self._rules)} rules, bias={self._bias}")
        except Exception as e:
            log.warning(f"[Guru] Error loading: {e}")

    def _extract_section(self, section_name: str) -> list:
        """Extract lines from a [SECTION] block"""
        lines = []
        in_section = False
        for line in self._raw_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith(f'[{section_name}]'):
                in_section = True
                continue
            if in_section and stripped.startswith('[') and stripped.endswith(']'):
                break
            if in_section and stripped.startswith('='):
                continue
            if in_section and stripped.startswith('-') and len(stripped) > 2:
                lines.append(stripped[1:].strip())
        return lines

    def get_guru_context(self) -> dict:
        self._reload()
        return {
            'bias': self._bias,
            'rules_count': len(self._rules),
            'rules': self._rules[:20],  # Top 20 rules
            'observations': self._observations[:10],
        }

    def check_guru_blocks(self, data: dict) -> list:
        """Check if any guru rules would BLOCK this trade"""
        self._reload()
        blocks = []
        now = datetime.now(timezone.utc)
        hour_utc = now.hour
        minute_utc = now.minute
        weekday = now.strftime('%A').lower()
        price = data.get('price', 0)

        for rule in self._rules:
            rule_lower = rule.lower()

            # Time-based blocks
            if 'no operar' in rule_lower or 'no abrir' in rule_lower:
                # Try to parse time ranges like "08:00-08:05"
                time_match = re.findall(r'(\d{1,2}):(\d{2})\s*[-–a]\s*(\d{1,2}):(\d{2})', rule_lower)
                if time_match:
                    for tm in time_match:
                        start_h, start_m = int(tm[0]), int(tm[1])
                        end_h, end_m = int(tm[2]), int(tm[3])
                        current_mins = hour_utc * 60 + minute_utc
                        start_mins = start_h * 60 + start_m
                        end_mins = end_h * 60 + end_m
                        if start_mins <= current_mins <= end_mins:
                            blocks.append(f"GURU_BLOCK: {rule}")

                # Day-based blocks
                if 'viernes' in rule_lower or 'friday' in rule_lower:
                    if weekday == 'friday':
                        # Check if after certain hour
                        hour_match = re.findall(r'(\d{1,2}):(\d{2})', rule_lower)
                        if hour_match:
                            block_h = int(hour_match[-1][0])
                            if hour_utc >= block_h:
                                blocks.append(f"GURU_BLOCK: {rule}")

            # Price-based observations (soft signals, not blocks)
            if 'sube más de' in rule_lower and 'no comprar' in rule_lower:
                amount_match = re.findall(r'\$(\d+)', rule_lower)
                if amount_match:
                    threshold = float(amount_match[0])
                    daily_change = data.get('daily_change_usd', 0)
                    if daily_change > threshold:
                        blocks.append(f"GURU_BLOCK: {rule}")

        return blocks

    def get_attack_signals(self) -> float:
        """[NOVA F-10] Parse attack signal keywords from guru rules/observations.
        Returns a bonus/penalty to apply to BREAKOUT_MOMENTUM score.
        Positive  = confirm breakout aggressiveness
        Negative  = suppress false breakout risk
        """
        self._reload()
        all_text = ' '.join(self._rules + self._observations).lower()
        bonus = 0.0

        # Positive keywords - confirm breakout / trend strength
        ATTACK_KEYWORDS = [
            'volumen alto', 'sma200', 'fibonacci 61.8', 'nivel redondo',
            'acumulacion', 'soporte fuerte', 'resistencia clara', 'impulso',
            'momentum', 'dxy debil', 'dxy abajo', 'rompimiento confirmado',
            'breakout confirmado', 'expansion', 'fuerza',
        ]
        # Negative keywords - suppress fakeout breakouts
        SUPPRESS_KEYWORDS = [
            'breakout falso', 'fake', 'stop hunting', 'squeeze', 'pullback',
            'rango estrecho', 'liquidez baja', 'spread amplio', 'volumen bajo',
            'no operar', 'no comprar', 'no abrir', 'evitar',
        ]

        for kw in ATTACK_KEYWORDS:
            if kw in all_text:
                bonus += 0.5
        for kw in SUPPRESS_KEYWORDS:
            if kw in all_text:
                bonus -= 0.5

        bonus = max(-3.0, min(3.0, bonus))  # cap +/-3.0
        return bonus
class MLModelReader:
    """Módulo 0.3: Read ML model files for context"""

    def __init__(self, symbol: str):
        self.symbol = symbol

    def get_ml_context(self) -> dict:
        """Read available ML model stats"""
        context = {}
        files_to_check = [
            ('quantum_stats', f'quantum_stats.json'),
            ('rl_stats', f'.rl_stats.json'),
            ('rl_weights', f'rl_weights_{self.symbol}.json'),
        ]

        for key, filename in files_to_check:
            filepath = os.path.join(BASE_DIR, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    # Extract key metrics only
                    if key == 'quantum_stats':
                        context['quantum_win_rate'] = data.get('win_rate', 0)
                        context['quantum_total_trades'] = data.get('total_trades', 0)
                        context['quantum_profit_factor'] = data.get('profit_factor', 0)
                    elif key == 'rl_stats':
                        context['rl_episodes'] = data.get('episodes', 0)
                        context['rl_avg_reward'] = data.get('avg_reward', 0)
                    elif key == 'rl_weights':
                        context['rl_weights_loaded'] = True
                except Exception:
                    pass

        return context


# ═══════════════════════════════════════════════════════════════════
# CAPA 1: COMPRENSIÓN PROFUNDA
# ═══════════════════════════════════════════════════════════════════

class NarrativeEngine:
    """Módulo 1.1 + 1.2: Market narrative + cause-effect classification"""

    def __init__(self):
        self._last_narrative = ''
        self._last_narrative_time = 0
        self.NARRATIVE_INTERVAL = 60  # Re-generate every 60s

    def generate_narrative(self, data: dict, macro: dict, cross: dict) -> dict:
        """
        Generate a causal narrative of what's happening.
        Returns: narrative text, bias, confidence, movement_type
        """
        price = data.get('price', data.get('bid', 0))
        rsi = data.get('rsi', 50)
        adx = data.get('adx', 20)
        atr = data.get('atr', 10)
        macd_hist = data.get('macd_histogram', 0)
        volume_ratio = data.get('volume_ratio', 1.0)
        sma_50 = data.get('sma_50', price)
        sma_200 = data.get('sma_200', price)
        bb_upper = data.get('bb_upper', price * 1.02)
        bb_lower = data.get('bb_lower', price * 0.98)

        # Price position relative to MAs
        above_sma50 = price > sma_50 if sma_50 > 0 else False
        above_sma200 = price > sma_200 if sma_200 > 0 else False
        golden_cross = sma_50 > sma_200 if (sma_50 > 0 and sma_200 > 0) else False

        # ── Movement Type Classification ──
        movement_type = self._classify_movement(data, volume_ratio, adx, atr, macro)

        # ── Bias Calculation ──
        buy_signals = 0
        sell_signals = 0

        if above_sma50: buy_signals += 1
        else: sell_signals += 1
        if above_sma200: buy_signals += 1
        else: sell_signals += 1
        if golden_cross: buy_signals += 1
        else: sell_signals += 1
        if rsi < 30: buy_signals += 2  # Oversold
        elif rsi > 70: sell_signals += 2  # Overbought
        elif rsi > 50: buy_signals += 0.5
        else: sell_signals += 0.5
        if macd_hist > 0: buy_signals += 1
        else: sell_signals += 1
        if volume_ratio > 1.3: buy_signals += 0.5 if macd_hist > 0 else 0
        if volume_ratio > 1.3: sell_signals += 0.5 if macd_hist < 0 else 0

        # DXY inverse for gold
        dxy = cross.get('dxy_proxy', 104)
        if SYMBOL == 'XAUUSD':
            # DXY down = gold up
            if dxy < 103: buy_signals += 1
            elif dxy > 105: sell_signals += 1

        total = buy_signals + sell_signals
        if total > 0:
            bias_score = (buy_signals - sell_signals) / total  # -1 to +1
        else:
            bias_score = 0.0

        if bias_score > 0.3:
            bias = 'BUY_BIAS'
        elif bias_score < -0.3:
            bias = 'SELL_BIAS'
        else:
            bias = 'NEUTRAL'

        confidence = min(0.95, abs(bias_score) * 0.8 + 0.2)

        # Generate narrative text
        narrative = self._build_narrative_text(
            data, macro, cross, movement_type, bias, bias_score, confidence
        )

        return {
            'narrative': narrative,
            'bias': bias,
            'bias_score': round(bias_score, 3),
            'confidence': round(confidence, 3),
            'movement_type': movement_type,
            'above_sma50': above_sma50,
            'above_sma200': above_sma200,
            'golden_cross': golden_cross,
        }

    def _classify_movement(self, data: dict, volume_ratio: float,
                           adx: float, atr: float, macro: dict) -> str:
        """Classify WHY the market is moving"""
        event_proximity = macro.get('minutes_until', 999)

        # EVENT: Within 30 min window of high-impact event
        if event_proximity < 30 and macro.get('impact') == 'HIGH':
            return 'EVENT'

        # FUNDAMENTAL: Strong directional move with volume
        if adx > 30 and volume_ratio > 1.5:
            return 'FUNDAMENTAL'

        # LIQUIDITY: Spike and reversal pattern (whipsaw)
        prices = data.get('prices', data.get('closes', []))
        if len(prices) >= 5:
            recent = prices[-5:]
            if len(recent) >= 5:
                max_p = max(recent)
                min_p = min(recent)
                current = recent[-1]
                range_pct = (max_p - min_p) / max(min_p, 1e-10)
                # If price moved far then came back = liquidity trap
                if range_pct > 0.005 and abs(current - recent[0]) < (max_p - min_p) * 0.3:
                    return 'LIQUIDITY'

        # TECHNICAL: Clean trend with moderate ADX
        if 20 < adx < 40 and volume_ratio < 1.5:
            return 'TECHNICAL'

        # NOISE: Low ADX, low volume
        if adx < 18 and volume_ratio < 0.8:
            return 'NOISE'

        return 'TECHNICAL'  # Default

    def _build_narrative_text(self, data, macro, cross, movement_type,
                              bias, bias_score, confidence) -> str:
        """Build human-readable narrative"""
        price = data.get('price', data.get('bid', 0))
        rsi = data.get('rsi', 50)
        adx = data.get('adx', 20)
        parts = []

        parts.append(f"{SYMBOL} @ {price:.2f}")
        parts.append(f"Movement: {movement_type}")
        parts.append(f"Trend strength: ADX={adx:.1f}, RSI={rsi:.1f}")
        parts.append(f"Narrative bias: {bias} ({bias_score:+.2f})")

        if macro.get('name') != 'CLEAR':
            parts.append(f"MACRO: {macro['name']} in {macro.get('minutes_until', '?')}min")

        dxy = cross.get('dxy_proxy', 0)
        if dxy > 0:
            parts.append(f"DXY proxy: {dxy:.1f}")

        usd_exp = cross.get('usd_exposure', 0)
        if usd_exp != 0:
            direction = 'LONG' if usd_exp > 0 else 'SHORT'
            parts.append(f"Portfolio: {abs(usd_exp)}x {direction} USD")

        return ' | '.join(parts)


# ═══════════════════════════════════════════════════════════════════
# CAPA 2: PROYECCIÓN INTELIGENTE
# ═══════════════════════════════════════════════════════════════════

class PhaseDetector:
    """Módulo 2.2: Market cycle phase detection"""

    def detect_phase(self, data: dict) -> dict:
        """
        Detect market cycle phase:
        ACCUMULATION → MARKUP → DISTRIBUTION → MARKDOWN
        And position within trend: INICIO / MEDIO / FINAL
        """
        adx = data.get('adx', 20)
        rsi = data.get('rsi', 50)
        volume_ratio = data.get('volume_ratio', 1.0)
        price = data.get('price', data.get('bid', 0))
        sma_50 = data.get('sma_50', price)
        sma_200 = data.get('sma_200', price)
        bb_upper = data.get('bb_upper', price * 1.02)
        bb_lower = data.get('bb_lower', price * 0.98)
        macd_hist = data.get('macd_histogram', 0)
        obv_slope = data.get('obv_slope', 0)

        bb_width = (bb_upper - bb_lower) / max(price, 1) if price > 0 else 0.02

        # Phase detection logic
        if adx < 20 and bb_width < 0.015 and volume_ratio > 0.8:
            phase = 'ACCUMULATION'
        elif adx > 25 and price > sma_50 and macd_hist > 0:
            phase = 'MARKUP'
        elif adx < 25 and price > sma_200 and bb_width > 0.02 and volume_ratio < 0.9:
            phase = 'DISTRIBUTION'
        elif adx > 25 and price < sma_50 and macd_hist < 0:
            phase = 'MARKDOWN'
        else:
            phase = 'TRANSITION'

        # Position within trend
        if phase in ('MARKUP', 'MARKDOWN'):
            position = self._detect_trend_position(data, phase)
        else:
            position = 'N/A'

        return {
            'phase': phase,
            'position': position,
            'phase_confidence': self._phase_confidence(data, phase),
        }

    def _detect_trend_position(self, data: dict, phase: str) -> str:
        """INICIO / MEDIO / FINAL of a trend"""
        adx = data.get('adx', 20)
        rsi = data.get('rsi', 50)
        volume_ratio = data.get('volume_ratio', 1.0)

        if phase == 'MARKUP':
            if adx < 30 and rsi < 65 and volume_ratio > 1.0:
                return 'INICIO'
            elif adx > 40 or rsi > 75:
                return 'FINAL'
            else:
                return 'MEDIO'
        elif phase == 'MARKDOWN':
            if adx < 30 and rsi > 35 and volume_ratio > 1.0:
                return 'INICIO'
            elif adx > 40 or rsi < 25:
                return 'FINAL'
            else:
                return 'MEDIO'
        return 'MEDIO'

    def _phase_confidence(self, data: dict, phase: str) -> float:
        adx = data.get('adx', 20)
        if phase in ('MARKUP', 'MARKDOWN') and adx > 25:
            return min(0.9, 0.5 + (adx - 25) * 0.02)
        elif phase == 'ACCUMULATION':
            return 0.6
        elif phase == 'DISTRIBUTION':
            return 0.55
        return 0.4


class ScenarioProjector:
    """Módulo 2.1: Probabilistic scenario generation"""

    def generate_scenarios(self, data: dict, narrative: dict, phase: dict) -> dict:
        """Generate 3 scenarios: bullish, neutral, bearish"""
        price = data.get('price', data.get('bid', 0))
        atr = data.get('atr', data.get('atr_14', 10))
        bias_score = narrative.get('bias_score', 0)
        phase_name = phase.get('phase', 'TRANSITION')

        # Base probabilities from bias
        if bias_score > 0.3:
            p_bull, p_neutral, p_bear = 0.50, 0.30, 0.20
        elif bias_score < -0.3:
            p_bull, p_neutral, p_bear = 0.20, 0.30, 0.50
        else:
            p_bull, p_neutral, p_bear = 0.33, 0.34, 0.33

        # Phase adjustments
        if phase_name == 'MARKUP':
            p_bull += 0.10
            p_bear -= 0.10
        elif phase_name == 'MARKDOWN':
            p_bear += 0.10
            p_bull -= 0.10
        elif phase_name == 'DISTRIBUTION':
            p_bear += 0.05
            p_bull -= 0.05

        # Normalize
        total = p_bull + p_neutral + p_bear
        p_bull /= total
        p_neutral /= total
        p_bear /= total

        return {
            'bullish': {
                'probability': round(p_bull, 2),
                'target': round(price + atr * 2, 2),
                'description': f"Price rises to {price + atr * 2:.2f} (+{atr * 2:.1f})"
            },
            'neutral': {
                'probability': round(p_neutral, 2),
                'range': [round(price - atr * 0.5, 2), round(price + atr * 0.5, 2)],
                'description': f"Consolidation between {price - atr * 0.5:.2f} - {price + atr * 0.5:.2f}"
            },
            'bearish': {
                'probability': round(p_bear, 2),
                'target': round(price - atr * 2, 2),
                'description': f"Price drops to {price - atr * 2:.2f} (-{atr * 2:.1f})"
            }
        }


# ═══════════════════════════════════════════════════════════════════
# CAPA 3: DECISIÓN ESTRATÉGICA
# ═══════════════════════════════════════════════════════════════════

class StrategySelector:
    """Módulo 3.1: 10-dimension strategy selection"""

    def select_strategy(self, dimensions: dict) -> dict:
        """
        Select optimal strategy based on 10 dimensions.
        Returns: strategy name, reason, conviction adjustment
        """
        regime = dimensions.get('regime', 'UNKNOWN')
        phase = dimensions.get('phase', 'TRANSITION')
        session = dimensions.get('session', 'OFF')
        macro_context = dimensions.get('macro_context', 'NEUTRAL')
        event_proximity = dimensions.get('event_proximity', 'CLEAR')
        movement_type = dimensions.get('movement_type', 'TECHNICAL')
        cross_asset = dimensions.get('cross_asset_alignment', 'NEUTRAL')
        portfolio_state = dimensions.get('portfolio_state', 'FLAT')
        recent_performance = dimensions.get('recent_performance', 'NORMAL')
        narrative_bias = dimensions.get('narrative_bias', 'NEUTRAL')

        # ── HARD BLOCKS (return HIBERNATION) ──
        if event_proximity in ('IMMINENT', 'DURING'):
            return {
                'strategy': 'HIBERNATION',
                'reason': f'Event {event_proximity} - blocking all entries',
                'conviction_adj': -1.0
            }

        if session == 'OFF':
            return {
                'strategy': 'HIBERNATION',
                'reason': 'Off-hours session - low liquidity',
                'conviction_adj': -1.0
            }

        if portfolio_state == 'CRITICAL':
            return {
                'strategy': 'HIBERNATION',
                'reason': 'Portfolio correlated risk CRITICAL',
                'conviction_adj': -1.0
            }

        if recent_performance == 'LOSING_STREAK':
            # Allow trading but downgrade 2 levels
            pass  # Handled in conviction

        # ── STRATEGY MATRIX ──
        scores = defaultdict(float)

        # Regime-based scoring
        if regime == 'TRENDING':
            scores['BREAKOUT_MOMENTUM'] += 2.0
            scores['TREND_CONTINUATION'] += 2.5
            scores['SWING_STRUCTURE'] += 1.5
            scores['MEAN_REVERSION'] -= 1.0
        elif regime == 'RANGING':
            scores['MEAN_REVERSION'] += 2.5
            scores['SWING_STRUCTURE'] += 2.0
            scores['SCALPING_PULSE'] += 1.5
            scores['BREAKOUT_MOMENTUM'] -= 1.0
        elif regime == 'VOLATILE':
            scores['FADE_LIQUIDATION'] += 2.0
            scores['SCALPING_PULSE'] += 1.0
            scores['BREAKOUT_MOMENTUM'] += 1.0
            scores['MEAN_REVERSION'] -= 0.5

        # Phase-based scoring
        if phase == 'ACCUMULATION':
            scores['SWING_STRUCTURE'] += 1.5
            scores['SMART_MONEY_HUNT'] += 2.0
        elif phase == 'MARKUP':
            scores['TREND_CONTINUATION'] += 2.0
            scores['BREAKOUT_MOMENTUM'] += 1.5
        elif phase == 'DISTRIBUTION':
            scores['FADE_LIQUIDATION'] += 1.5
            scores['MEAN_REVERSION'] += 1.0
            scores['TREND_CONTINUATION'] -= 1.0
        elif phase == 'MARKDOWN':
            scores['TREND_CONTINUATION'] += 2.0
            scores['BREAKOUT_MOMENTUM'] += 1.0

        # Session-based scoring
        if session == 'LONDON':
            scores['BREAKOUT_MOMENTUM'] += 1.0
            scores['SMART_MONEY_HUNT'] += 1.0
        elif session == 'OVERLAP':
            scores['BREAKOUT_MOMENTUM'] += 1.5
            scores['SCALPING_PULSE'] += 1.0
        elif session == 'NEW_YORK':
            scores['TREND_CONTINUATION'] += 1.0
        elif session == 'ASIA':
            scores['MEAN_REVERSION'] += 1.5
            scores['SCALPING_PULSE'] += 0.5
            scores['BREAKOUT_MOMENTUM'] -= 1.0

        # Movement type scoring
        if movement_type == 'FUNDAMENTAL':
            scores['TREND_CONTINUATION'] += 2.0
            scores['BREAKOUT_MOMENTUM'] += 1.5
            scores['SCALPING_PULSE'] -= 1.0
        elif movement_type == 'LIQUIDITY':
            scores['FADE_LIQUIDATION'] += 3.0
            scores['BREAKOUT_MOMENTUM'] -= 2.0
        elif movement_type == 'EVENT':
            scores['NEWS_MOMENTUM'] += 3.0
        elif movement_type == 'NOISE':
            scores['HIBERNATION'] += 2.0
            scores['SCALPING_PULSE'] -= 1.0

        # Post-event = potential NEWS_MOMENTUM
        if event_proximity == 'POST':
            scores['NEWS_MOMENTUM'] += 2.0

        # Cross-asset alignment
        if cross_asset == 'ALIGNED':
            scores['BREAKOUT_MOMENTUM'] += 0.5
            scores['TREND_CONTINUATION'] += 0.5
        elif cross_asset == 'DIVERGENT':
            scores['HIBERNATION'] += 1.0

        # [NOVA F-10] Guru attack signals - adjust BREAKOUT_MOMENTUM
        guru_attack = dimensions.get('guru_attack_bonus', 0.0)
        if guru_attack != 0.0:
            scores['BREAKOUT_MOMENTUM'] += guru_attack
            log.debug(f"[F-10] Guru attack bonus: {guru_attack:+.1f} -> BREAKOUT_MOMENTUM adjusted")
        # Select best strategy
        if not scores:
            return {'strategy': 'HIBERNATION', 'reason': 'No clear setup', 'conviction_adj': -1.0}

        best_strategy = max(scores, key=scores.get)
        best_score = scores[best_strategy]

        # If best score is too low, hibernate
        if best_score < 1.0:
            return {'strategy': 'HIBERNATION', 'reason': 'No high-conviction setup', 'conviction_adj': -1.0}

        return {
            'strategy': best_strategy,
            'reason': f'{best_strategy} scores {best_score:.1f} ({regime}/{phase}/{session})',
            'conviction_adj': min(0.3, (best_score - 2.0) * 0.1),
            'all_scores': {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])[:5]}
        }


class ConvictionCalculator:
    """Módulo 3.2: Dynamic conviction-based sizing"""

    def calculate(self, narrative: dict, phase: dict, strategy: dict,
                  memory: dict, guru: dict, data: dict) -> dict:
        """
        Calculate conviction score from 0.0 to 1.0
        Maps to: BLOCK / MICRO / NORMAL / REINFORCED / MAXIMUM / KILLER
        """
        score = 0.5  # Base

        # ── Narrative confidence ──
        narr_conf = narrative.get('confidence', 0.5)
        score += (narr_conf - 0.5) * 0.3  # ±0.15

        # ── Phase clarity ──
        phase_conf = phase.get('phase_confidence', 0.5)
        score += (phase_conf - 0.5) * 0.2  # ±0.10

        # ── Strategy score ──
        strat_adj = strategy.get('conviction_adj', 0)
        score += strat_adj

        # ── Bias alignment with proposed action ──
        bias = narrative.get('bias', 'NEUTRAL')
        proposed = data.get('proposed_action', 'HOLD')
        if bias == 'BUY_BIAS' and proposed == 'BUY':
            score += 0.1
        elif bias == 'SELL_BIAS' and proposed == 'SELL':
            score += 0.1
        elif bias != 'NEUTRAL' and proposed != 'HOLD':
            if (bias == 'BUY_BIAS' and proposed == 'SELL') or \
               (bias == 'SELL_BIAS' and proposed == 'BUY'):
                score -= 0.15  # Against narrative

        # ── Guru bias alignment ──
        guru_bias = guru.get('bias', 'NEUTRAL')
        if guru_bias != 'NEUTRAL':
            if (guru_bias == 'BULLISH' and proposed == 'BUY') or \
               (guru_bias == 'BEARISH' and proposed == 'SELL'):
                score += 0.05
            elif (guru_bias == 'BULLISH' and proposed == 'SELL') or \
                 (guru_bias == 'BEARISH' and proposed == 'BUY'):
                score -= 0.10

        # ── Historical performance of this strategy ──
        strat_name = strategy.get('strategy', 'HIBERNATION')
        strat_perf = memory.get('strategy_performance', {}).get(strat_name, {})
        hist_profit = strat_perf.get('profit_usd', 0)
        hist_loss = abs(strat_perf.get('loss_usd', 0))
        if hist_profit + hist_loss > 0:
            profit_ratio = hist_profit / max(hist_loss, 1)
            if profit_ratio > 3:
                score += 0.1
            elif profit_ratio < 1:
                score -= 0.1

        # ── Losing streak penalty ──
        streak = memory.get('totals', {}).get('current_streak', {})
        if streak.get('type') == 'loss':
            loss_count = streak.get('count', 0)
            # -2 conviction levels per 3 consecutive losses
            score -= loss_count * 0.05

        # ── Confidence calibration deflator ──
        deflator = memory.get('confidence_calibration', {}).get('confidence_deflator', 1.0)
        score *= deflator

        # Clamp
        score = max(0.0, min(1.0, score))

        # Map to level
        level = 'BLOCK'
        for lvl, (lo, hi) in CONVICTION_LEVELS.items():
            if lo <= score < hi:
                level = lvl
                break

        # Size multiplier
        size_mult = {
            'BLOCK': 0.0, 'MICRO': 0.25, 'NORMAL': 1.0,
            'REINFORCED': 1.5, 'MAXIMUM': 2.0, 'KILLER': 3.0
        }.get(level, 0.0)

        return {
            'conviction': round(score, 3),
            'level': level,
            'size_multiplier': size_mult,
            'should_trade': level != 'BLOCK',
        }


class SmartTPSL:
    """Módulo 3.3: Conscious TP/SL calculation"""

    def calculate(self, data: dict, strategy: str, conviction: dict,
                  narrative: dict, memory: dict) -> dict:
        """Calculate dynamic TP/SL based on context"""
        price = data.get('price', data.get('bid', 0))
        atr = data.get('atr', data.get('atr_14', 10))
        action = data.get('proposed_action', 'BUY')

        if price <= 0 or atr <= 0:
            return {'tp1': 0, 'tp2': 0, 'tp3': 0, 'sl': 0, 'rr_ratio': 0, 'rr_acceptable': False}  # 🔧 FIX CAT-105

        # ── Base multipliers by strategy ──
        strat_config = {
            'SCALPING_PULSE':     {'sl_atr': 0.8,  'tp1_atr': 1.2, 'tp2_atr': 2.0, 'tp3_atr': 3.0},
            'SWING_STRUCTURE':    {'sl_atr': 1.5,  'tp1_atr': 2.0, 'tp2_atr': 3.5, 'tp3_atr': 5.0},
            'BREAKOUT_MOMENTUM':  {'sl_atr': 1.0,  'tp1_atr': 2.0, 'tp2_atr': 3.5, 'tp3_atr': 5.0},
            'HARMONIC_REVERSAL':  {'sl_atr': 1.2,  'tp1_atr': 1.8, 'tp2_atr': 3.0, 'tp3_atr': 4.0},
            'SMART_MONEY_HUNT':   {'sl_atr': 1.0,  'tp1_atr': 2.0, 'tp2_atr': 3.5, 'tp3_atr': 5.0},
            'NEWS_MOMENTUM':      {'sl_atr': 1.5,  'tp1_atr': 2.5, 'tp2_atr': 4.0, 'tp3_atr': 6.0},
            'FADE_LIQUIDATION':   {'sl_atr': 1.0,  'tp1_atr': 1.5, 'tp2_atr': 2.5, 'tp3_atr': 3.5},
            'TREND_CONTINUATION': {'sl_atr': 1.2,  'tp1_atr': 2.0, 'tp2_atr': 3.5, 'tp3_atr': 5.0},
            'MEAN_REVERSION':     {'sl_atr': 1.0,  'tp1_atr': 1.5, 'tp2_atr': 2.5, 'tp3_atr': 3.5},
        }
        cfg = strat_config.get(strategy, {'sl_atr': 1.2, 'tp1_atr': 2.0, 'tp2_atr': 3.0, 'tp3_atr': 4.0})

        # ── Narrative adjustment ──
        movement = narrative.get('movement_type', 'TECHNICAL')
        if movement == 'FUNDAMENTAL':
            cfg['tp2_atr'] *= 1.3  # Wider TP for fundamental moves
            cfg['tp3_atr'] *= 1.3
        elif movement == 'NOISE':
            cfg['tp1_atr'] *= 0.7  # Tighter for noise
            cfg['tp2_atr'] *= 0.7

        # ── Break-even check ──
        exec_quality = memory.get('execution_quality', {})
        break_even_pips = exec_quality.get('break_even_pips', 2.0)
        # Ensure TP1 covers break-even cost (at minimum)
        min_tp1 = break_even_pips * 3  # 3x break-even minimum

        # ── Calculate levels ──
        if action == 'BUY':
            sl = round(price - atr * cfg['sl_atr'], 2)
            tp1 = round(price + max(atr * cfg['tp1_atr'], min_tp1), 2)
            tp2 = round(price + atr * cfg['tp2_atr'], 2)
            tp3 = round(price + atr * cfg['tp3_atr'], 2)
        else:  # SELL
            sl = round(price + atr * cfg['sl_atr'], 2)
            tp1 = round(price - max(atr * cfg['tp1_atr'], min_tp1), 2)
            tp2 = round(price - atr * cfg['tp2_atr'], 2)
            tp3 = round(price - atr * cfg['tp3_atr'], 2)

        # ── R:R validation ──
        risk = abs(price - sl)
        reward1 = abs(tp1 - price)
        rr_ratio = reward1 / max(risk, 0.01)

        return {
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'risk_pips': round(risk, 2),
            'reward_pips': round(reward1, 2),
            'rr_ratio': round(rr_ratio, 2),
            'rr_acceptable': rr_ratio >= 2.0,
        }


class PortfolioExposureCheck:
    """Módulo 3.4: Portfolio-level risk check"""

    def check(self, cross: dict, proposed_action: str, symbol: str) -> dict:
        """Check if proposed trade would create dangerous exposure"""
        usd_exp = cross.get('usd_exposure', 0)
        total_open = cross.get('total_open', 0)
        correlated_risk = cross.get('correlated_risk', 'LOW')

        # What would this trade add?
        USD_IMPACT = {
            'XAUUSD': {'BUY': -1, 'SELL': 1},
            'EURUSD': {'BUY': -1, 'SELL': 1},
            'GBPUSD': {'BUY': -1, 'SELL': 1},
            'AUDUSD': {'BUY': -1, 'SELL': 1},
            'NZDUSD': {'BUY': -1, 'SELL': 1},
            'CHFUSD': {'BUY': -1, 'SELL': 1},
            'USDJPY': {'BUY': 1, 'SELL': -1},
            'USDCAD': {'BUY': 1, 'SELL': -1},
            'BTCUSD': {'BUY': -1, 'SELL': 1},
            'US30USD':{'BUY': -1, 'SELL': 1},
        }

        proposed_impact = USD_IMPACT.get(symbol, {}).get(proposed_action.upper(), 0)
        new_exposure = usd_exp + proposed_impact

        # Limits
        max_directional = 3  # Max 3x in one USD direction
        max_total = 4  # Max 4 open total (from config)

        warnings = []
        approved = True

        if abs(new_exposure) > max_directional:
            warnings.append(f"USD exposure would be {abs(new_exposure)}x {('LONG' if new_exposure > 0 else 'SHORT')} USD")
            approved = False

        if total_open >= max_total:
            warnings.append(f"Already {total_open} positions open (max {max_total})")
            approved = False

        if correlated_risk in ('CRITICAL', 'HIGH') and abs(new_exposure) > 2:
            warnings.append(f"Correlated risk {correlated_risk} - reducing exposure")
            approved = False

        return {
            'approved': approved,
            'current_usd_exposure': usd_exp,
            'new_usd_exposure': new_exposure,
            'warnings': warnings,
        }


# ═══════════════════════════════════════════════════════════════════
# MEMORY MANAGER
# ═══════════════════════════════════════════════════════════════════

class MemoryManager:
    """Manages the per-pair JSON memory file"""

    def __init__(self):
        self._memory = self._load()
        self._lock = threading.Lock()
        self._dirty = False
        self._last_save = time.time()
        self.SAVE_INTERVAL = 30  # Auto-save every 30s if dirty

    def _load(self) -> dict:
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"[Memory] Error loading: {e}")
        return self._empty_memory()

    def _empty_memory(self) -> dict:
        return {
            'symbol': SYMBOL,
            'created': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'consciousness_phase': 'LEARNING',
            'totals': {
                'total_trades': 0, 'total_profit_usd': 0, 'total_loss_usd': 0,
                'profit_ratio': 0, 'best_day_profit': 0, 'worst_day_loss': 0,
                'longest_winning_streak': 0, 'longest_losing_streak': 0,
                'current_streak': {'type': 'none', 'count': 0}
            },
            'trades': [],
            'strategy_performance': {s: {'trades': 0, 'profit_usd': 0, 'loss_usd': 0} for s in STRATEGIES},
            'loss_autopsy': {},
            'confidence_calibration': {'brackets': {}, 'brier_score': 0, 'confidence_deflator': 1.0},
            'execution_quality': {'avg_slippage_pips': 0, 'avg_spread_pips': 0, 'cost_per_trade_usd': 0, 'break_even_pips': 2.0},
            'edge_monitor': {'rolling_sharpe_50': 0, 'edge_status': 'UNKNOWN'},
            'intraday_heatmap': {},
            'active_vetos': [], 'expired_vetos': [],
            'human_behavior': {},
            'learnings': [],
        }

    def get(self) -> dict:
        with self._lock:
            return self._memory.copy()

    def update(self, path: str, value):
        """Update a nested path like 'totals.total_trades'"""
        with self._lock:
            keys = path.split('.')
            d = self._memory
            for k in keys[:-1]:
                if k not in d:
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value
            self._memory['last_updated'] = datetime.now(timezone.utc).isoformat()
            self._dirty = True

    def record_trade(self, trade: dict):
        """Record a completed trade in memory"""
        with self._lock:
            self._memory.setdefault('trades', []).append(trade)
            totals = self._memory.get('totals', {})
            totals['total_trades'] = totals.get('total_trades', 0) + 1

            pnl = trade.get('pnl_usd', 0)
            if pnl >= 0:
                totals['total_profit_usd'] = totals.get('total_profit_usd', 0) + pnl
            else:
                totals['total_loss_usd'] = totals.get('total_loss_usd', 0) + abs(pnl)

            total_profit = totals.get('total_profit_usd', 0)
            total_loss = totals.get('total_loss_usd', 0)
            totals['profit_ratio'] = total_profit / max(total_loss, 1)

            # Update streak
            streak = totals.get('current_streak', {'type': 'none', 'count': 0})
            result = 'win' if pnl >= 0 else 'loss'
            if streak['type'] == result:
                streak['count'] += 1
            else:
                streak = {'type': result, 'count': 1}
            totals['current_streak'] = streak

            if result == 'win':
                totals['longest_winning_streak'] = max(
                    totals.get('longest_winning_streak', 0), streak['count'])
            else:
                totals['longest_losing_streak'] = max(
                    totals.get('longest_losing_streak', 0), streak['count'])

            self._memory['totals'] = totals

            # Update strategy performance
            strat = trade.get('strategy', 'UNKNOWN')
            sp = self._memory.setdefault('strategy_performance', {})
            if strat not in sp:
                sp[strat] = {'trades': 0, 'profit_usd': 0, 'loss_usd': 0}
            sp[strat]['trades'] += 1
            if pnl >= 0:
                sp[strat]['profit_usd'] += pnl
            else:
                sp[strat]['loss_usd'] += abs(pnl)

            # Update consciousness phase
            tc = totals['total_trades']
            if tc <= 10:
                self._memory['consciousness_phase'] = 'LEARNING'
            elif tc <= 30:
                self._memory['consciousness_phase'] = 'WARMING'
            elif tc <= 50:
                self._memory['consciousness_phase'] = 'CALIBRATING'
            else:
                self._memory['consciousness_phase'] = 'FULL'

            self._memory['last_updated'] = datetime.now(timezone.utc).isoformat()
            self._dirty = True

    def save_if_dirty(self):
        with self._lock:
            if self._dirty and time.time() - self._last_save > self.SAVE_INTERVAL:
                self._save()

    def force_save(self):
        with self._lock:
            self._save()

    def _save(self):
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._memory, f, indent=2, default=str)
            self._dirty = False
            self._last_save = time.time()
        except Exception as e:
            log.error(f"[Memory] Save error: {e}")

    def get_consciousness_phase(self) -> str:
        return self._memory.get('consciousness_phase', 'LEARNING')


# ═══════════════════════════════════════════════════════════════════
# OLLAMA ENHANCEMENT (OPTIONAL)
# ═══════════════════════════════════════════════════════════════════

def _call_ollama_narrative(context: str) -> str:
    """Optional: Use Ollama to generate richer narrative. Falls back gracefully."""
    if not REQUESTS_AVAILABLE:
        return ''
    try:
        prompt = (
            f"You are a senior market analyst. Based on this data, write a 2-sentence "
            f"market narrative explaining WHY the market is moving and what to expect next. "
            f"Be specific and actionable.\n\nData: {context[:1500]}"
        )
        resp = http_requests.post(
            OLLAMA_ENDPOINT,
            json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False,
                  'options': {'temperature': 0.3, 'num_predict': 150}},
            timeout=OLLAMA_TIMEOUT
        )
        if resp.status_code == 200:
            return resp.json().get('response', '')[:300]
    except Exception:
        pass
    return ''


# ═══════════════════════════════════════════════════════════════════
# SENTINEL COMMUNICATION
# ═══════════════════════════════════════════════════════════════════

def _query_sentinel(proposal: dict, timeout: float = 2.0) -> dict:
    """Send proposal to LLM12 Sentinel for validation"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((HOST, SENTINEL_PORT))

        msg = json.dumps(proposal).encode('utf-8')
        sock.sendall(struct.pack('>I', len(msg)) + msg)

        header = b''
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                break
            header += chunk

        if len(header) == 4:
            length = struct.unpack('>I', header)[0]
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk
            if data:
                return json.loads(data.decode('utf-8'))

        sock.close()
    except Exception as e:
        log.debug(f"[Sentinel] Communication error: {e}")

    # Fallback: approve by default if Sentinel is offline
    return {'approved': True, 'checks_passed': 0, 'checks_total': 0, 'fallback': True}


# ═══════════════════════════════════════════════════════════════════
# MAIN LLM11 CLASS
# ═══════════════════════════════════════════════════════════════════

class LLM11StrategistGuru:
    """
    THE TRADING CONSCIOUSNESS - Capas 0-3
    Percepción → Comprensión → Proyección → Decisión
    """

    def __init__(self):
        self.macro = MacroRadar()
        self.cross = CrossAssetRadar(SYMBOL)
        self.guru = GuruFileReader()
        self.ml_reader = MLModelReader(SYMBOL)
        self.narrative_engine = NarrativeEngine()
        self.phase_detector = PhaseDetector()
        self.scenario_projector = ScenarioProjector()
        self.strategy_selector = StrategySelector()
        self.conviction_calc = ConvictionCalculator()
        self.tp_sl = SmartTPSL()
        self.portfolio_check = PortfolioExposureCheck()
        self.memory = MemoryManager()

        # Background save thread
        self._save_thread = threading.Thread(target=self._background_save, daemon=True)
        self._save_thread.start()

        log.info(f"[LLM11] Strategist Guru initialized | {SYMBOL} | Port {PORT}")
        log.info(f"[LLM11] Consciousness phase: {self.memory.get_consciousness_phase()}")

    def _background_save(self):
        while True:
            time.sleep(10)
            self.memory.save_if_dirty()

    def analyze(self, data: dict) -> dict:
        """
        Main analysis pipeline - THE CONSCIOUSNESS FLOW
        Receives genome data from quantum_core via Trinity
        Returns strategic verdict for Trinity consensus
        """
        start = time.time()
        symbol = data.get('symbol', SYMBOL)
        msg_type = data.get('type', 'analyze')

        # ── Handle trade_closed messages ──
        if msg_type == 'trade_closed':
            return self._handle_trade_closed(data)

        # ── Handle sentinel validation requests ──
        if msg_type == 'sentinel_result':
            return self._handle_sentinel_result(data)

        try:
            memory = self.memory.get()
            phase_name = memory.get('consciousness_phase', 'LEARNING')

            # ═══ CAPA 0: PERCEPCIÓN ═══
            macro_info = self.macro.get_next_event(symbol)
            event_proximity = self.macro.get_event_proximity(symbol)

            self.cross.update_price_cache(data)
            cross_state = self.cross.get_portfolio_state()

            guru_context = self.guru.get_guru_context()
            guru_blocks = self.guru.check_guru_blocks(data)

            ml_context = self.ml_reader.get_ml_context()

            # ═══ CAPA 1: COMPRENSIÓN ═══
            narrative = self.narrative_engine.generate_narrative(data, macro_info, cross_state)

            # Ollama enhancement (non-blocking, optional)
            ollama_narrative = ''
            if phase_name in ('CALIBRATING', 'FULL'):
                context_str = f"{symbol} {narrative.get('bias')} ADX={data.get('adx')} RSI={data.get('rsi')} DXY={cross_state.get('dxy_proxy')}"
                ollama_narrative = _call_ollama_narrative(context_str)

            # ═══ CAPA 2: PROYECCIÓN ═══
            phase_info = self.phase_detector.detect_phase(data)
            scenarios = self.scenario_projector.generate_scenarios(data, narrative, phase_info)

            # ═══ CAPA 3: DECISIÓN ═══

            # Determine session
            now_utc = datetime.now(timezone.utc)
            hour = now_utc.hour
            session = 'OFF'
            for sess_name, (start_h, end_h) in SESSIONS.items():
                if start_h <= hour < end_h:
                    session = sess_name
                    break

            # Determine recent performance
            streak = memory.get('totals', {}).get('current_streak', {})
            if streak.get('type') == 'loss' and streak.get('count', 0) >= 3:
                recent_perf = 'LOSING_STREAK'
            elif streak.get('type') == 'win' and streak.get('count', 0) >= 3:
                recent_perf = 'WINNING_STREAK'
            else:
                recent_perf = 'NORMAL'

            # Determine regime from data
            adx = data.get('adx', 20)
            atr = data.get('atr', 10)
            if adx > 25:
                regime = 'TRENDING'
            elif adx < 18:
                regime = 'RANGING'
            else:
                regime = 'VOLATILE' if atr > data.get('atr_avg', atr) * 1.3 else 'RANGING'

            # Cross-asset alignment check
            usd_exp = cross_state.get('usd_exposure', 0)
            if abs(usd_exp) >= 3:
                portfolio_state = 'CRITICAL'
            elif abs(usd_exp) >= 2:
                portfolio_state = 'EXPOSED'
            else:
                portfolio_state = 'FLAT'

            # 10-dimension strategy selection
            dimensions = {
                'regime': regime,
                'phase': phase_info.get('phase', 'TRANSITION'),
                'session': session,
                'macro_context': 'RISK_ON' if narrative.get('bias') == 'BUY_BIAS' else 'RISK_OFF' if narrative.get('bias') == 'SELL_BIAS' else 'NEUTRAL',
                'event_proximity': event_proximity,
                'movement_type': narrative.get('movement_type', 'TECHNICAL'),
                'cross_asset_alignment': 'ALIGNED' if cross_state.get('correlated_risk', 'LOW') in ('LOW', 'MODERATE') else 'DIVERGENT',
                'portfolio_state': portfolio_state,
                'recent_performance': recent_perf,
                'narrative_bias': narrative.get('bias', 'NEUTRAL'),
                'guru_attack_bonus': self.guru.get_attack_signals(),  # [NOVA F-10]
            }

            strategy = self.strategy_selector.select_strategy(dimensions)

            # Handle HIBERNATION
            if strategy['strategy'] == 'HIBERNATION':
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': 10,
                    'reason': f"HIBERNATION: {strategy['reason']}",
                    'strategy': 'HIBERNATION',
                    'narrative': narrative.get('narrative', ''),
                    'phase': phase_info.get('phase', 'TRANSITION'),
                    'conviction': 0.0,
                    'sizing': 'BLOCK',
                    'event': macro_info,
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                }

            # ── Guru rule blocks ──
            if guru_blocks:
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': 15,
                    'reason': f"GURU BLOCK: {guru_blocks[0]}",
                    'strategy': strategy['strategy'],
                    'narrative': narrative.get('narrative', ''),
                    'guru_blocks': guru_blocks,
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                }

            # ── Determine proposed action from narrative ──
            bias = narrative.get('bias', 'NEUTRAL')
            if bias == 'BUY_BIAS':
                proposed_action = 'BUY'
            elif bias == 'SELL_BIAS':
                proposed_action = 'SELL'
            else:
                proposed_action = 'HOLD'

            # In LEARNING phase, use defaults
            if phase_name == 'LEARNING':
                proposed_action = data.get('proposed_action', proposed_action)

            data['proposed_action'] = proposed_action

            # ── Conviction ──
            conviction = self.conviction_calc.calculate(
                narrative, phase_info, strategy, memory, guru_context, data
            )

            if not conviction['should_trade']:
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': round(conviction['conviction'] * 100, 1),
                    'reason': f"Conviction too low: {conviction['conviction']:.2f} ({conviction['level']})",
                    'strategy': strategy['strategy'],
                    'conviction': conviction['conviction'],
                    'sizing': conviction['level'],
                    'narrative': narrative.get('narrative', ''),
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                }

            # ── TP/SL ──
            tp_sl = self.tp_sl.calculate(
                data, strategy['strategy'], conviction, narrative, memory
            )

            # ── Portfolio exposure check ──
            portfolio = self.portfolio_check.check(cross_state, proposed_action, symbol)

            if not portfolio['approved']:
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': 20,
                    'reason': f"PORTFOLIO BLOCK: {'; '.join(portfolio['warnings'])}",
                    'strategy': strategy['strategy'],
                    'conviction': conviction['conviction'],
                    'portfolio': portfolio,
                    'narrative': narrative.get('narrative', ''),
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                }

            # ── R:R check ──
            if not tp_sl.get('rr_acceptable', True):
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': 25,
                    'reason': f"R:R too low: {tp_sl.get('rr_ratio', 0):.1f} (min 2.0)",
                    'strategy': strategy['strategy'],
                    'tp_sl': tp_sl,
                    'narrative': narrative.get('narrative', ''),
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                }

            # ═══ BUILD PROPOSAL FOR SENTINEL ═══
            proposal = {
                'type': 'validate_proposal',
                'symbol': symbol,
                'action': proposed_action,
                'strategy': strategy['strategy'],
                'conviction': conviction['conviction'],
                'sizing': conviction['level'],
                'size_multiplier': conviction['size_multiplier'],
                'tp1': tp_sl['tp1'],
                'tp2': tp_sl['tp2'],
                'tp3': tp_sl['tp3'],
                'sl': tp_sl['sl'],
                'rr_ratio': tp_sl['rr_ratio'],
                'narrative': narrative.get('narrative', ''),
                'narrative_bias': narrative.get('bias', 'NEUTRAL'),
                'movement_type': narrative.get('movement_type', 'TECHNICAL'),
                'phase': phase_info.get('phase', 'TRANSITION'),
                'phase_position': phase_info.get('position', 'N/A'),
                'event': macro_info,
                'event_proximity': event_proximity,
                'portfolio': portfolio,
                'scenarios': scenarios,
                'dimensions': dimensions,
                'consciousness_phase': phase_name,
            }

            # ── Query Sentinel ──
            sentinel_result = _query_sentinel(proposal)

            # ── Handle Sentinel response ──
            if sentinel_result.get('approved', True):
                decision = proposed_action
                conviction_val = conviction['conviction'] * 100  # Convert 0.0-1.0 to 0-100%
                # [NOVA AUDIT F-16] Sentinel offline: apply -10% confidence penalty
                if sentinel_result.get('fallback'):
                    conviction_val *= 0.9
                    log.warning("[LLM11] ⚠️ Sentinel OFFLINE — applying -10% confidence penalty")
                confidence = conviction_val
                reason = (f"{strategy['strategy']} | {narrative.get('bias')} | "
                         f"Conv={conviction['conviction']:.2f} | "
                         f"R:R={tp_sl['rr_ratio']:.1f} | "
                         f"Sentinel: {'APPROVED' if not sentinel_result.get('fallback') else 'OFFLINE(-10%)'}")
            else:
                # Sentinel rejected — maybe retry with adjustments
                reject_reason = sentinel_result.get('reason', 'Unknown')

                # Check if Sentinel suggests modifications
                if sentinel_result.get('suggest_modify'):
                    # Try to adjust (e.g., widen TP for better R:R)
                    modified = sentinel_result.get('modified_params', {})
                    if modified.get('tp1'):
                        tp_sl['tp1'] = modified['tp1']
                    if modified.get('sl'):
                        tp_sl['sl'] = modified['sl']

                    decision = proposed_action
                    confidence = conviction['conviction'] * 100 * 0.9  # Convert + 10% penalty
                    reason = f"MODIFIED by Sentinel: {reject_reason} → Adjusted"
                else:
                    decision = 'HOLD'
                    confidence = 20
                    reason = f"SENTINEL VETO: {reject_reason}"

            elapsed = round((time.time() - start) * 1000, 1)

            return {
                'decision': decision,
                'confidence': round(min(100, max(0, confidence)), 1),
                'reason': reason,
                'strategy': strategy['strategy'],
                'conviction': conviction['conviction'],
                'sizing': conviction['level'],
                'size_multiplier': conviction['size_multiplier'],
                'tp_targets': [tp_sl['tp1'], tp_sl['tp2'], tp_sl['tp3']],
                'sl': tp_sl['sl'],
                'rr_ratio': tp_sl['rr_ratio'],
                'narrative': narrative.get('narrative', ''),
                'ollama_narrative': ollama_narrative[:200] if ollama_narrative else '',
                'movement_type': narrative.get('movement_type', 'TECHNICAL'),
                'phase': phase_info.get('phase', 'TRANSITION'),
                'phase_position': phase_info.get('position', 'N/A'),
                'scenarios': scenarios,
                'event': macro_info,
                'event_proximity': event_proximity,
                'portfolio': portfolio,
                'guru_bias': guru_context.get('bias', 'NEUTRAL'),
                'sentinel': sentinel_result,
                'dimensions': dimensions,
                'consciousness_phase': phase_name,
                'latency_ms': elapsed,
            }

        except Exception as e:
            elapsed = round((time.time() - start) * 1000, 1)
            log.error(f"[LLM11] Analysis error: {e}", exc_info=True)
            return {
                'decision': 'HOLD',
                'confidence': 0,
                'reason': f'LLM11 error: {str(e)[:100]}',
                'strategy': 'ERROR',
                'latency_ms': elapsed,
                'consciousness_phase': self.memory.get_consciousness_phase(),
            }

    def _handle_trade_closed(self, data: dict) -> dict:
        """Process a trade_closed notification — update memory"""
        try:
            trade_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ticket': data.get('ticket', 0),
                'symbol': data.get('symbol', SYMBOL),
                'action': data.get('action', 'UNKNOWN'),
                'entry_price': data.get('entry_price', 0),
                'close_price': data.get('close_price', 0),
                'pnl_usd': data.get('pnl_usd', data.get('pnl', 0)),
                'reason': data.get('reason', 'UNKNOWN'),
                'strategy': data.get('strategy', 'UNKNOWN'),
                'duration_s': data.get('duration_seconds', 0),
            }

            self.memory.record_trade(trade_record)
            self.memory.force_save()

            log.info(f"[LLM11] Trade recorded: {trade_record['action']} "
                    f"PnL=${trade_record['pnl_usd']:.2f} ({trade_record['reason']})")

            return {'status': 'recorded', 'trade': trade_record}

        except Exception as e:
            log.error(f"[LLM11] Trade record error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_sentinel_result(self, data: dict) -> dict:
        """Handle async sentinel validation result"""
        return {'status': 'acknowledged'}


# ═══════════════════════════════════════════════════════════════════
# TCP SERVER
# ═══════════════════════════════════════════════════════════════════

def _get_current_session() -> str:
    hour = datetime.now(timezone.utc).hour
    for name, (start, end) in SESSIONS.items():
        if start <= hour < end:
            return name
    return 'OFF'


def handle_client(sock, addr, llm11: LLM11StrategistGuru):
    """Handle TCP client connection — same protocol as all LLMs"""
    sock.settimeout(30)
    try:
        while True:
            # Read 4-byte header
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

            # Read full payload
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk

            if not data:
                break

            # Parse and analyze
            request = json.loads(data.decode('utf-8', errors='replace'))
            response = llm11.analyze(request)

            # Send response
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
    log.info("  LLM11 STRATEGIST GURU — THE TRADING CONSCIOUSNESS")
    log.info(f"  NOVA TRADING AI by Polarice Labs © 2026")
    log.info(f"  Symbol: {SYMBOL} | Port: {port}")
    log.info(f"  Session: {_get_current_session()}")
    log.info("=" * 70)

    llm11 = LLM11StrategistGuru()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, port))
    server_sock.listen(5)

    log.info(f"[LLM11] TCP Server READY on {HOST}:{port}")

    def signal_handler(sig, frame):
        log.info("[LLM11] Shutting down gracefully...")
        llm11.memory.force_save()
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
                    args=(client_sock, addr, llm11),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"[LLM11] Accept error: {e}")
                time.sleep(0.1)
    finally:
        log.info("[LLM11] Saving memory and shutting down...")
        llm11.memory.force_save()
        server_sock.close()


if __name__ == '__main__':
    main()
