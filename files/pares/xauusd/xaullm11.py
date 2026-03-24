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

import socket, struct, json, logging, threading, time, os, re, math, signal, sys, random
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🧠 LLM11 GURU | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

PORT = 5568
HOST = '127.0.0.1'
SYMBOL = 'XAUUSD'
SENTINEL_PORT = 5569

OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/generate"
OLLAMA_CHAT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3:8b"
OLLAMA_TIMEOUT = 5.0
OLLAMA_STRATEGY_TIMEOUT = 7.0   # llama3:8b is fast — must finish before Trinity's 10s deadline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STRATEGY_GENOME_FILE = os.path.join(BASE_DIR, f'strategy_genome_{SYMBOL}.json')
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
    'CHFUSD': -0.036,   # Inverted: USDCHF^(+0.036) = CHFUSD^(-0.036)
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
    'MICRO':     (0.0,  0.35),    # Was BLOCK 0-0.30 → now allows micro trades
    'CAUTIOUS':  (0.35, 0.50),    # New level: reduced sizing, still trades
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
                prices[sym] = r.get('current_price', r.get('price', 0))  # 🔧 FIX: read actual price, not ATR
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
            # Use price_cache as fallback for missing SharedBrain data
            _pc = self._price_cache
            eurusd = prices.get('EURUSD') or _pc.get('EURUSD', 1.08)
            usdjpy = prices.get('USDJPY') or _pc.get('USDJPY', 150.0)
            gbpusd = prices.get('GBPUSD') or _pc.get('GBPUSD', 1.27)
            usdcad = prices.get('USDCAD') or _pc.get('USDCAD', 1.36)
            chfusd = prices.get('CHFUSD') or _pc.get('CHFUSD', 1.13)

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

    def get_attack_signals(self, session: str, adx: float, event_proximity: str,
                           dxy_proxy: float, narrative_bias: str, data: dict) -> dict:
        """
        Process [OBSERVACIONES] against current conditions → conviction bonus.
        Matches SPANISH keywords from guru file against live market state.
        Returns: {'attack_bonus': float 0.0-0.20, 'attack_signals': list}
        """
        self._reload()
        bonus = 0.0
        signals = []

        for obs in self._observations:
            obs_lower = obs.lower()

            # ── ASIA RANGE BREAKOUT FALSO → buy on London reversal ──
            # Guru: "Asia Range Breakout falso en London open"
            if ('breakout' in obs_lower and 'falso' in obs_lower) or \
               ('asia' in obs_lower and 'breakout' in obs_lower):
                now_h, now_m = datetime.now(timezone.utc).hour, datetime.now(timezone.utc).minute
                cur_min = now_h * 60 + now_m
                # 08:05-08:30 UTC window = post-stop-hunt London reversal
                if 485 <= cur_min <= 510 and narrative_bias == 'BUY_BIAS':
                    bonus += 0.10
                    signals.append('ASIA_FAKE_BREAKOUT_REVERSAL')

            # ── SMA200 BREAKOUT → strong trend continuation ──
            # Guru: "cierra por encima de la SMA200 en D1"
            if 'sma200' in obs_lower or 'sma 200' in obs_lower:
                sma200 = data.get('sma_200', 0)
                price = data.get('price', data.get('current_price', 0))
                if sma200 > 0 and price > sma200 and narrative_bias == 'BUY_BIAS':
                    bonus += 0.08
                    signals.append('SMA200_BULLISH_BREAKOUT')

            # ── FIBONACCI 61.8% entry point ──
            # Guru: "niveles de Fibonacci 61.8% ... mejores puntos de entrada largo"
            if 'fibonacci' in obs_lower and '61' in obs_lower:
                # Phase ACCUMULATION + ADX<25 + BUY = fib retrace setup
                if adx < 25 and narrative_bias == 'BUY_BIAS':
                    bonus += 0.06
                    signals.append('FIB_618_ENTRY')

            # ── CPI/INFLACION surprise → gold bullish ──
            # Guru: "datos de inflacion americana superiores a lo esperado"
            if ('cpi' in obs_lower or 'inflacion' in obs_lower) and \
               ('superior' in obs_lower or 'encima' in obs_lower):
                if event_proximity in ('POST', 'DURING') and narrative_bias == 'BUY_BIAS':
                    bonus += 0.12
                    signals.append('CPI_SURPRISE_BULLISH')

            # ── RISK-OFF geopolitical → gold ignores technicals ──
            # Guru: "eventos de risk-off globales ... el oro sube"
            if ('risk-off' in obs_lower or 'risk off' in obs_lower) or \
               ('incertidumbre' in obs_lower and 'geopolitica' in obs_lower):
                gold_chg = data.get('daily_change_usd', 0)
                if gold_chg > 10 and narrative_bias == 'BUY_BIAS':
                    bonus += 0.10
                    signals.append('RISK_OFF_GOLD_BID')

            # ── OVERLAP London-NY → highest follow-through ──
            # Guru: "OVERLAP London-NY es el periodo de mayor volumen"
            if 'overlap' in obs_lower and ('volumen' in obs_lower or 'london' in obs_lower):
                if session == 'OVERLAP' and adx > 22 and \
                   narrative_bias in ('BUY_BIAS', 'SELL_BIAS'):
                    bonus += 0.07
                    signals.append('OVERLAP_HIGH_VOLUME')

            # ── DXY inverse correlation ──
            # Guru: "DXY abajo con fuerza ... señal alcista para oro"
            if 'dxy' in obs_lower and ('abajo' in obs_lower or 'debil' in obs_lower or
                                        'caida' in obs_lower or 'cayendo' in obs_lower):
                # Use synthetic DXY proxy from CrossAssetAnalyzer
                if dxy_proxy > 0:
                    dxy_change = data.get('dxy_change_pct', None)
                    if dxy_change is None:
                        # Estimate from proxy: if DXY below 103, likely weakening
                        if dxy_proxy < 103 and narrative_bias == 'BUY_BIAS':
                            bonus += 0.06
                            signals.append('DXY_WEAK_PROXY')
                    elif dxy_change < -0.003 and narrative_bias == 'BUY_BIAS':
                        bonus += 0.08
                        signals.append('DXY_FALLING_IMPULSE')

            # ── Rango >3h + Wyckoff Phase B SQUEEZE → pre-breakout acumulacion ──
            # Guru: "rangos que duran mas de 3 horas con ATR bajo generan acumulacion"
            # AND: "compresion de ATR pre-breakout proporcional a extension post-breakout"
            # FIXED: old code required adx>25 (post-breakout) and missed the SQUEEZE itself.
            if 'rango' in obs_lower and ('3 hora' in obs_lower or 'acumulacion' in obs_lower):
                atr_val = data.get('atr', 0)
                # 🔧 FIX: Was atr_val * 2.5 — atr_avg never exists in data, so fallback
                # ALWAYS fires. 2.5x makes squeeze condition (atr < atr_avg*0.45) impossible.
                # Use 1.0x (same as current) as neutral fallback.
                atr_avg = data.get('atr_avg', atr_val * 1.0 if atr_val else 0)
                vol_ratio = data.get('volume_ratio', 1.0)
                bb_width = data.get('bb_width', 1.0)
                # SQUEEZE = Wyckoff Phase B: energy building, breakout imminent
                squeeze_active = (atr_avg > 0 and atr_val < atr_avg * 0.45) or bb_width < 0.002
                # Confirmed post-breakout: volume surge + nascent trend
                breakout_confirmed = vol_ratio > 1.8 and adx > 25
                if squeeze_active:
                    bonus += 0.07
                    signals.append('WYCKOFF_PHASE_B_SQUEEZE')
                elif breakout_confirmed:
                    bonus += 0.08
                    signals.append('RANGE_BREAKOUT_VOLUME')

        bonus = min(0.20, bonus)  # Cap total
        if bonus > 0:
            log.info(f"[Guru] 🔥 Attack signals: {signals} → conviction +{bonus:.2f}")
        return {'attack_bonus': round(bonus, 3), 'attack_signals': signals}

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

        # 🔧 FIX 2026-03-11: sma_200 defaults to current price (never 200 bars available)
        # above_sma200 = price > price = always False → permanent sell bias
        # golden_cross = sma_50 > price → INVERTED: rising price makes this False = sell_signals
        # INSTEAD: use ma_fast vs ma_slow from MT5 native indicators (correct real MAs)
        has_real_sma200 = abs(sma_200 - price) > 0.10  # Real SMA200 differs from current >$0.10
        if has_real_sma200:
            # Real long-term MA data available — use it
            if above_sma200: buy_signals += 1
            else: sell_signals += 1
            if golden_cross: buy_signals += 1
            else: sell_signals += 1
        else:
            # No real SMA200 — use native MT5 MA cross (ma_fast/ma_slow from indicators)
            _inds = data.get('indicators', {})
            _ma_fast = _inds.get('ma_fast', 0) or data.get('ma_fast', 0)
            _ma_slow = _inds.get('ma_slow', 0) or data.get('ma_slow', 0)
            if _ma_fast > 0 and _ma_slow > 0 and abs(_ma_fast - _ma_slow) > 0.01:
                if _ma_fast > _ma_slow:
                    buy_signals += 1.5   # Short-term MA bullish cross
                else:
                    sell_signals += 1.5  # Short-term MA bearish cross
            # If MAs equal or missing → skip (neutral, no false bias)
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
# STRATEGY GENOME — Living DNA of Trading Strategies
# ═══════════════════════════════════════════════════════════════════

class StrategyGenome:
    """
    Living DNA of trading strategies. Tracks built-in + AI-created strategies.
    Evolves fitness scores based on real P&L. Manages exploit/explore balance.
    The genome REMEMBERS what works and FORGETS what doesn't.
    """

    def __init__(self):
        self._genome = self._load()
        self._lock = threading.Lock()
        self._dirty = False

    def _load(self) -> dict:
        try:
            if os.path.exists(STRATEGY_GENOME_FILE):
                with open(STRATEGY_GENOME_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'strategies' in data:
                    return data
        except Exception as e:
            log.warning(f"[Genome] Error loading: {e}")
        return self._default_genome()

    def _default_genome(self) -> dict:
        strategies = {}
        for name in STRATEGIES:
            if name == 'HIBERNATION':
                continue
            strategies[name] = {
                'type': 'built_in', 'fitness': 50.0,
                'total_trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                'by_regime': {}, 'by_session': {},
                'consecutive_losses': 0, 'consecutive_wins': 0,
                'last_used': None, 'active': True,
            }
        return {
            'symbol': SYMBOL, 'generation': 1,
            'created': datetime.now(timezone.utc).isoformat(),
            'last_evolved': datetime.now(timezone.utc).isoformat(),
            'strategies': strategies, 'custom_count': 0,
            'learnings': [], 'total_explorations': 0, 'total_exploitations': 0,
        }

    def get_snapshot(self) -> dict:
        with self._lock:
            return json.loads(json.dumps(self._genome, default=str))

    def get_strategy_ranking(self, regime: str = None, session: str = None) -> list:
        """Get strategies ranked by contextual fitness."""
        with self._lock:
            ranked = []
            for name, data in self._genome.get('strategies', {}).items():
                if not data.get('active', True):
                    continue
                fitness = data.get('fitness', 50.0)
                # Boost fitness for strategies proven in this regime
                if regime and regime in data.get('by_regime', {}):
                    rd = data['by_regime'][regime]
                    if rd.get('trades', 0) > 0:
                        regime_avg = rd.get('pnl', 0) / rd['trades']
                        fitness += min(15, regime_avg * 2) if regime_avg > 0 else max(-10, regime_avg)
                # Boost for session performance
                if session and session in data.get('by_session', {}):
                    sd = data['by_session'][session]
                    if sd.get('trades', 0) > 0:
                        sess_avg = sd.get('pnl', 0) / sd['trades']
                        fitness += min(10, sess_avg) if sess_avg > 0 else max(-8, sess_avg)
                ranked.append({
                    'name': name, 'fitness': round(fitness, 1),
                    'trades': data.get('total_trades', 0),
                    'pnl': round(data.get('total_pnl', 0), 2),
                    'win_rate': round(data['wins'] / max(data['total_trades'], 1) * 100, 1),
                    'consecutive_losses': data.get('consecutive_losses', 0),
                    'type': data.get('type', 'built_in'),
                })
            ranked.sort(key=lambda x: x['fitness'], reverse=True)
            return ranked

    def should_explore(self) -> bool:
        """Multi-armed bandit: epsilon-greedy with adaptive decay."""
        with self._lock:
            total = self._genome.get('total_explorations', 0) + self._genome.get('total_exploitations', 0)
            if total < 10:
                epsilon = 0.20
            elif total < 50:
                epsilon = 0.12
            elif total < 200:
                epsilon = 0.08
            else:
                epsilon = 0.05
            # Force exploration after best strategy's repeated failures
            strats = self._genome.get('strategies', {})
            max_consec = max((s.get('consecutive_losses', 0) for s in strats.values()), default=0)
            if max_consec >= 3:
                epsilon = min(0.40, epsilon * 4)
            return random.random() < epsilon

    def record_trade_result(self, strategy_name: str, pnl: float, regime: str, session: str):
        """Update strategy fitness after trade result."""
        with self._lock:
            strats = self._genome.setdefault('strategies', {})
            if strategy_name not in strats:
                strats[strategy_name] = {
                    'type': 'ai_generated', 'fitness': 50.0,
                    'total_trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                    'by_regime': {}, 'by_session': {},
                    'consecutive_losses': 0, 'consecutive_wins': 0,
                    'last_used': None, 'active': True,
                }
            s = strats[strategy_name]
            s['total_trades'] = s.get('total_trades', 0) + 1
            s['total_pnl'] = round(s.get('total_pnl', 0) + pnl, 2)
            s['last_used'] = datetime.now(timezone.utc).isoformat()
            if pnl >= 0:
                s['wins'] = s.get('wins', 0) + 1
                s['consecutive_losses'] = 0
                s['consecutive_wins'] = s.get('consecutive_wins', 0) + 1
                s['fitness'] = min(100, s.get('fitness', 50) + min(5, pnl * 0.5))
            else:
                s['losses'] = s.get('losses', 0) + 1
                s['consecutive_wins'] = 0
                s['consecutive_losses'] = s.get('consecutive_losses', 0) + 1
                s['fitness'] = max(5, s.get('fitness', 50) - min(8, abs(pnl) * 0.8))
                if s['consecutive_losses'] >= 5:
                    s['active'] = False
                    log.warning(f"[Genome] ⚠️ {strategy_name} DEACTIVATED — 5 consecutive losses")
            # Regime/session breakdown
            if regime:
                s.setdefault('by_regime', {}).setdefault(regime, {'trades': 0, 'pnl': 0.0})
                s['by_regime'][regime]['trades'] += 1
                s['by_regime'][regime]['pnl'] = round(s['by_regime'][regime].get('pnl', 0) + pnl, 2)
            if session:
                s.setdefault('by_session', {}).setdefault(session, {'trades': 0, 'pnl': 0.0})
                s['by_session'][session]['trades'] += 1
                s['by_session'][session]['pnl'] = round(s['by_session'][session].get('pnl', 0) + pnl, 2)
            self._genome['last_evolved'] = datetime.now(timezone.utc).isoformat()
            self._dirty = True

    def add_learning(self, insight: str, source: str = 'ollama'):
        """Store an AI-generated learning."""
        with self._lock:
            self._genome.setdefault('learnings', []).append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'insight': insight[:500], 'source': source,
            })
            if len(self._genome['learnings']) > 100:
                self._genome['learnings'] = self._genome['learnings'][-100:]
            self._dirty = True

    def register_custom_strategy(self, name: str, description: str, base_strategy: str):
        """Register an AI-created custom strategy."""
        with self._lock:
            self._genome.setdefault('strategies', {})[name] = {
                'type': 'ai_generated', 'description': description[:300],
                'base_strategy': base_strategy, 'fitness': 55.0,
                'total_trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                'by_regime': {}, 'by_session': {},
                'consecutive_losses': 0, 'consecutive_wins': 0,
                'last_used': None, 'active': True,
            }
            self._genome['custom_count'] = self._genome.get('custom_count', 0) + 1
            self._dirty = True
            log.info(f"[Genome] 🧬 New custom strategy registered: {name} (based on {base_strategy})")

    def record_exploration(self):
        with self._lock:
            self._genome['total_explorations'] = self._genome.get('total_explorations', 0) + 1
            self._dirty = True

    def record_exploitation(self):
        with self._lock:
            self._genome['total_exploitations'] = self._genome.get('total_exploitations', 0) + 1
            self._dirty = True

    def reactivate_strategy(self, name: str):
        """Ollama can reactivate a deactivated strategy with new conditions."""
        with self._lock:
            if name in self._genome.get('strategies', {}):
                self._genome['strategies'][name]['active'] = True
                self._genome['strategies'][name]['consecutive_losses'] = 0
                self._genome['strategies'][name]['fitness'] = 35.0  # Probation fitness
                self._dirty = True
                log.info(f"[Genome] 🔄 {name} REACTIVATED on probation (fitness=35)")

    def save_if_dirty(self):
        with self._lock:
            if self._dirty:
                self._save()

    def force_save(self):
        with self._lock:
            self._save()

    def _save(self):
        try:
            with open(STRATEGY_GENOME_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._genome, f, indent=2, default=str)
            self._dirty = False
        except Exception as e:
            log.error(f"[Genome] Save error: {e}")


# ═══════════════════════════════════════════════════════════════════
# MARKET MEMORY RING — Temporal awareness + regime transition detection
# ═══════════════════════════════════════════════════════════════════

class MarketMemoryRing:
    """
    Rolling memory of the last N analysis cycles.
    Detects: regime transitions, momentum acceleration/deceleration,
    volatility regime shifts, correlation breakdowns.
    The system REMEMBERS what it saw 5, 15, 30 minutes ago.
    """

    def __init__(self, max_size: int = 60):
        self._ring = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def push(self, snapshot: dict):
        """Store a market snapshot with timestamp."""
        with self._lock:
            self._ring.append({
                'ts': time.time(),
                'price': snapshot.get('price', 0),
                'adx': snapshot.get('adx', 20),
                'rsi': snapshot.get('rsi', 50),
                'atr': snapshot.get('atr', 10),
                'macd_hist': snapshot.get('macd_histogram', 0),
                'volume_ratio': snapshot.get('volume_ratio', 1.0),
                'bb_width': snapshot.get('bb_width', 0.01),
                'regime': snapshot.get('_regime', 'UNKNOWN'),
                'bias': snapshot.get('_bias', 'NEUTRAL'),
            })

    def get_market_awareness(self) -> dict:
        """Analyze the memory ring for temporal patterns."""
        with self._lock:
            if len(self._ring) < 3:
                return {'has_data': False}

            now = time.time()
            recent = list(self._ring)

            # Snapshots from different time windows
            snap_5m = [s for s in recent if now - s['ts'] <= 300]
            snap_15m = [s for s in recent if now - s['ts'] <= 900]
            snap_30m = [s for s in recent if now - s['ts'] <= 1800]

            result = {'has_data': True}

            # ── Regime Transition Detection ──
            if len(snap_15m) >= 5:
                regimes_15m = [s['regime'] for s in snap_15m]
                unique_regimes = list(set(regimes_15m))
                if len(unique_regimes) > 1:
                    # Count transitions
                    transitions = sum(1 for i in range(1, len(regimes_15m)) if regimes_15m[i] != regimes_15m[i-1])
                    result['regime_transitioning'] = transitions > 1
                    result['regime_from'] = regimes_15m[0]
                    result['regime_to'] = regimes_15m[-1]
                    result['regime_transitions_15m'] = transitions
                else:
                    result['regime_transitioning'] = False
                    result['regime_stable'] = unique_regimes[0] if unique_regimes else 'UNKNOWN'

            # ── ADX Velocity (trend strength changing?) ──
            if len(snap_5m) >= 3:
                adx_values = [s['adx'] for s in snap_5m]
                adx_delta = adx_values[-1] - adx_values[0]
                result['adx_velocity'] = round(adx_delta, 2)
                result['adx_accelerating'] = adx_delta > 2
                result['adx_decelerating'] = adx_delta < -2

            # ── Volatility Regime Shift ──
            if len(snap_15m) >= 5 and len(snap_5m) >= 2:
                atr_15m = np.mean([s['atr'] for s in snap_15m])
                atr_5m = np.mean([s['atr'] for s in snap_5m])
                if atr_15m > 0:
                    vol_ratio = atr_5m / atr_15m
                    result['volatility_expanding'] = vol_ratio > 1.3
                    result['volatility_contracting'] = vol_ratio < 0.7
                    result['volatility_ratio'] = round(vol_ratio, 2)

            # ── Momentum Direction Consistency ──
            if len(snap_5m) >= 3:
                biases = [s['bias'] for s in snap_5m]
                buy_count = biases.count('BUY_BIAS')
                sell_count = biases.count('SELL_BIAS')
                total = len(biases)
                result['bias_consistency'] = round(max(buy_count, sell_count) / max(total, 1), 2)
                result['dominant_bias_5m'] = 'BUY_BIAS' if buy_count > sell_count else 'SELL_BIAS' if sell_count > buy_count else 'MIXED'

            # ── Price Delta ──
            if len(snap_5m) >= 2:
                result['price_delta_5m'] = round(snap_5m[-1]['price'] - snap_5m[0]['price'], 2)
            if len(snap_30m) >= 2:
                result['price_delta_30m'] = round(snap_30m[-1]['price'] - snap_30m[0]['price'], 2)

            # ── Squeeze Detection (BB width contracting) ──
            if len(snap_15m) >= 5:
                bb_widths = [s['bb_width'] for s in snap_15m if s['bb_width'] > 0]
                if len(bb_widths) >= 3:
                    avg_bb = np.mean(bb_widths[:-2])  # historical avg
                    current_bb = bb_widths[-1]
                    if avg_bb > 0:
                        result['squeeze_active'] = current_bb < avg_bb * 0.6
                        result['squeeze_releasing'] = current_bb > avg_bb * 1.4 and bb_widths[-2] < avg_bb * 0.8

            return result


# ═══════════════════════════════════════════════════════════════════
# META-COGNITION — Self-awareness + Loss Pattern Avoidance
# ═══════════════════════════════════════════════════════════════════

class MetaCognition:
    """
    The system's self-awareness layer. Tracks:
    - Conviction calibration: are high-conviction trades actually winning more?
    - Loss patterns: what conditions preceded losses? (regime, session, strategy, indicators)
    - Decision quality: is the system improving or degrading over time?
    """

    def __init__(self, memory: MemoryManager, genome: 'StrategyGenome'):
        self._memory = memory
        self._genome = genome
        self._loss_patterns = []  # Cached from analysis
        self._last_pattern_update = 0

    def analyze_self(self, data: dict, regime: str, session: str,
                     strategy_name: str, conviction: float) -> dict:
        """Perform meta-cognitive self-check before a trade."""
        result = {
            'warnings': [],
            'conviction_modifier': 0.0,
            'should_reduce_size': False,
            'loss_pattern_match': False,
        }

        memory = self._memory.get()
        trades = memory.get('trades', [])

        if len(trades) < 3:
            return result

        # ── Conviction Calibration ──
        # Do high-conviction trades actually win more than low-conviction trades?
        # If not, the system is miscalibrated and needs deflation
        recent_trades = trades[-30:]  # Last 30 trades
        high_conv_trades = [t for t in recent_trades if t.get('conviction', 0.5) > 0.7]
        low_conv_trades = [t for t in recent_trades if t.get('conviction', 0.5) <= 0.5]
        if len(high_conv_trades) >= 5:
            high_wr = sum(1 for t in high_conv_trades if t.get('pnl_usd', 0) >= 0) / len(high_conv_trades)
            low_wr = sum(1 for t in low_conv_trades if t.get('pnl_usd', 0) >= 0) / max(len(low_conv_trades), 1)
            if high_wr < low_wr + 0.05:
                result['warnings'].append('CONVICTION_MISCALIBRATED: high-conv trades not outperforming')
                result['conviction_modifier'] -= 0.08
            elif high_wr > 0.65:
                result['conviction_modifier'] += 0.05  # System is well-calibrated, trust it more

        # ── Loss Pattern Detection ──
        # Extract conditions that preceded recent losses
        self._update_loss_patterns(trades)
        current_conditions = {
            'regime': regime, 'session': session, 'strategy': strategy_name,
            'adx': data.get('adx', 20), 'rsi': data.get('rsi', 50),
            'atr_elevated': data.get('atr', 10) > data.get('atr_avg', 10) * 1.3,
        }
        pattern_match = self._check_loss_pattern(current_conditions)
        if pattern_match:
            result['loss_pattern_match'] = True
            result['warnings'].append(f'LOSS_PATTERN: similar conditions caused {pattern_match["count"]} recent losses')
            result['conviction_modifier'] -= min(0.15, pattern_match['count'] * 0.04)
            result['should_reduce_size'] = pattern_match['count'] >= 3

        # ── Decision Quality Trend ──
        # Are the last 10 trades better or worse than the previous 10?
        if len(trades) >= 20:
            batch_a = trades[-20:-10]
            batch_b = trades[-10:]
            pnl_a = sum(t.get('pnl_usd', 0) for t in batch_a)
            pnl_b = sum(t.get('pnl_usd', 0) for t in batch_b)
            if pnl_b < pnl_a * 0.5 and pnl_a > 0:
                result['warnings'].append('DEGRADING: recent 10 trades significantly worse than prior 10')
                result['conviction_modifier'] -= 0.05
            elif pnl_b > pnl_a * 1.5 and pnl_b > 0:
                result['conviction_modifier'] += 0.03  # Improving

        # ── Overtrading Check ──
        if len(trades) >= 3:
            recent_3 = trades[-3:]
            timestamps = [t.get('timestamp', '') for t in recent_3]
            try:
                times = [datetime.fromisoformat(ts) for ts in timestamps if ts]
                if len(times) >= 2:
                    avg_gap = sum(
                        (times[i] - times[i-1]).total_seconds()
                        for i in range(1, len(times))
                    ) / (len(times) - 1)
                    if avg_gap < 300:  # Less than 5 minutes between trades
                        result['warnings'].append(f'OVERTRADING: avg {avg_gap:.0f}s between last 3 trades')
                        result['conviction_modifier'] -= 0.10
            except (ValueError, TypeError):
                pass

        return result

    def _update_loss_patterns(self, trades: list):
        """Extract fingerprints from recent losing trades."""
        if time.time() - self._last_pattern_update < 60:
            return
        self._last_pattern_update = time.time()

        recent_losses = [t for t in trades[-20:] if t.get('pnl_usd', 0) < 0]
        patterns = defaultdict(int)
        for t in recent_losses:
            key = f"{t.get('regime', '?')}|{t.get('session', '?')}|{t.get('strategy', '?')}"
            patterns[key] += 1
        self._loss_patterns = [
            {'key': k, 'count': v, 'parts': k.split('|')}
            for k, v in patterns.items() if v >= 2
        ]

    def _check_loss_pattern(self, conditions: dict) -> dict:
        """Check if current conditions match a known loss pattern.
        🔧 FIX: Regime match is now mandatory. A loss pattern from TRENDING regime
        should NOT block the same setup in RANGING regime.
        """
        for pattern in self._loss_patterns:
            parts = pattern['parts']
            if len(parts) == 3:
                # Regime MUST match (mandatory)
                if parts[0] != conditions.get('regime', ''):
                    continue
                # Plus at least 1 of session/strategy
                other_matches = 0
                if parts[1] == conditions.get('session', ''): other_matches += 1
                if parts[2] == conditions.get('strategy', ''): other_matches += 1
                if other_matches >= 1:
                    return pattern
        return None

    def get_self_report(self) -> dict:
        """Brief self-assessment for logging."""
        memory = self._memory.get()
        trades = memory.get('trades', [])
        if not trades:
            return {'status': 'NO_DATA', 'total': 0}
        recent = trades[-10:]
        wins = sum(1 for t in recent if t.get('pnl_usd', 0) >= 0)
        pnl = sum(t.get('pnl_usd', 0) for t in recent)
        return {
            'status': 'GOOD' if pnl > 0 and wins >= 5 else 'CAUTION' if pnl >= 0 else 'STRUGGLING',
            'recent_10_wr': f'{wins}/10',
            'recent_10_pnl': round(pnl, 2),
            'loss_patterns': len(self._loss_patterns),
            'total_trades': len(trades),
        }


# ═══════════════════════════════════════════════════════════════════
# CAPA 3: DECISIÓN ESTRATÉGICA
# ═══════════════════════════════════════════════════════════════════

class StrategySelector:
    """Módulo 3.1: 10-dimension strategy selection — now genome-aware"""

    def select_strategy(self, dimensions: dict, genome: 'StrategyGenome' = None,
                         market_awareness: dict = None) -> dict:
        """
        Select optimal strategy based on 10 dimensions + genome fitness + market awareness.
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

        # ── SOFT CALIBRATION (penalty instead of hard block) ──
        # Events, sessions, portfolio risk → heavy conviction penalty, NOT hibernation
        # The system stays intelligent and can still trade if setup is exceptional
        caution_penalty = 0.0
        caution_reasons = []

        if event_proximity == 'DURING':
            caution_penalty += 0.45  # Very heavy but not absolute
            caution_reasons.append(f'Event DURING (-0.45)')
        elif event_proximity == 'IMMINENT':
            caution_penalty += 0.30  # Heavy caution
            caution_reasons.append(f'Event IMMINENT (-0.30)')

        if session == 'OFF':
            caution_penalty += 0.35  # Off-hours low liquidity
            caution_reasons.append('OFF session (-0.35)')

        if portfolio_state == 'CRITICAL':
            caution_penalty += 0.40  # Correlated risk
            caution_reasons.append('Portfolio CRITICAL (-0.40)')

        if recent_performance == 'LOSING_STREAK':
            caution_penalty += 0.15
            caution_reasons.append('Losing streak (-0.15)')

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

        # ── GENOME FITNESS WEIGHTING ──
        # Strategy fitness from real P&L history → proven winners score higher
        if genome:
            ranking = genome.get_strategy_ranking(regime=regime, session=session)
            for entry in ranking:
                name = entry['name']
                fitness = entry.get('fitness', 50)
                trades = entry.get('trades', 0)
                if name in scores:
                    if trades >= 3:  # Only weight strategies with enough data
                        # Fitness 50 = neutral, 80 = strong boost, 20 = strong penalty
                        fitness_adj = (fitness - 50) / 50 * 2.0  # Range: -2.0 to +2.0
                        scores[name] += fitness_adj
                        if fitness > 70 and trades >= 5:
                            scores[name] += 0.5  # Bonus for battle-tested winners
                    if entry.get('consecutive_losses', 0) >= 3:
                        scores[name] -= 1.5  # Heavy penalty for actively failing strategies

        # ── MARKET AWARENESS MODULATION ──
        if market_awareness and market_awareness.get('has_data'):
            # Regime transition → penalize trend-following, boost adaptive strategies
            if market_awareness.get('regime_transitioning'):
                scores['TREND_CONTINUATION'] -= 1.0
                scores['BREAKOUT_MOMENTUM'] -= 0.5
                scores['MEAN_REVERSION'] += 0.5
                scores['SCALPING_PULSE'] += 0.5
            # Squeeze releasing → boost breakout strategies
            if market_awareness.get('squeeze_releasing'):
                scores['BREAKOUT_MOMENTUM'] += 2.0
                scores['TREND_CONTINUATION'] += 1.0
                scores['MEAN_REVERSION'] -= 1.0
            # Squeeze active → boost range strategies
            elif market_awareness.get('squeeze_active'):
                scores['MEAN_REVERSION'] += 1.0
                scores['SCALPING_PULSE'] += 1.0
                scores['BREAKOUT_MOMENTUM'] -= 0.5
            # Volatility expanding → wider TP, prefer momentum
            if market_awareness.get('volatility_expanding'):
                scores['BREAKOUT_MOMENTUM'] += 1.0
                scores['SCALPING_PULSE'] -= 0.5
            # Volatility contracting → tighter range
            elif market_awareness.get('volatility_contracting'):
                scores['SCALPING_PULSE'] += 0.5
                scores['BREAKOUT_MOMENTUM'] -= 0.5

        # Select best strategy
        if not scores:
            return {'strategy': 'HIBERNATION', 'reason': 'No clear setup', 'conviction_adj': -1.0,
                    'caution_penalty': caution_penalty, 'caution_reasons': caution_reasons}

        best_strategy = max(scores, key=scores.get)
        best_score = scores[best_strategy]

        # If best score is very low AND there's caution → hibernate
        # But if score is decent, let it through with penalty
        if best_score < 0.5:
            return {'strategy': 'HIBERNATION', 'reason': 'No viable setup', 'conviction_adj': -1.0,
                    'caution_penalty': caution_penalty, 'caution_reasons': caution_reasons}

        # Apply caution as conviction adjustment (negative)
        base_adj = min(0.3, (best_score - 2.0) * 0.1)
        final_adj = base_adj - caution_penalty

        reason_parts = [f'{best_strategy} scores {best_score:.1f} ({regime}/{phase}/{session})']
        if caution_reasons:
            reason_parts.append(f'CAUTION: {", ".join(caution_reasons)}')

        return {
            'strategy': best_strategy,
            'reason': ' | '.join(reason_parts),
            'conviction_adj': final_adj,
            'caution_penalty': caution_penalty,
            'caution_reasons': caution_reasons,
            'all_scores': {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])[:5]}
        }


class ConvictionCalculator:
    """Módulo 3.2: Dynamic conviction-based sizing — now with genome + meta-cognition"""

    def calculate(self, narrative: dict, phase: dict, strategy: dict,
                  memory: dict, guru: dict, data: dict,
                  genome: 'StrategyGenome' = None,
                  meta_report: dict = None,
                  market_awareness: dict = None) -> dict:
        """
        Calculate conviction score from 0.0 to 1.0
        Maps to: MICRO / CAUTIOUS / NORMAL / REINFORCED / MAXIMUM / KILLER
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

        # ── Guru attack doctrine bonus (from processed observations) ──
        attack_bonus = guru.get('attack_bonus', 0.0)
        if attack_bonus > 0.0 and proposed in ('BUY', 'SELL'):
            score += attack_bonus

        # ── Guru soft penalty (replaces old hard BLOCK) ──
        guru_penalty = guru.get('guru_penalty', 0.0)
        if guru_penalty > 0:
            score -= guru_penalty

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
            score -= loss_count * 0.05

        # ── Confidence calibration deflator ──
        deflator = memory.get('confidence_calibration', {}).get('confidence_deflator', 1.0)
        score *= deflator

        # ── GENOME FITNESS INJECTION ──
        # A strategy with high fitness in current conditions deserves more conviction
        if genome:
            ranking = genome.get_strategy_ranking()
            for entry in ranking:
                if entry['name'] == strat_name:
                    fitness = entry.get('fitness', 50)
                    trades = entry.get('trades', 0)
                    if trades >= 5:
                        # Fitness > 70 → boost, fitness < 30 → penalize
                        score += (fitness - 50) / 50 * 0.15  # ±0.15
                    if entry.get('consecutive_losses', 0) >= 3:
                        score -= 0.12  # Active losing streak on this strategy
                    break

        # ── META-COGNITION INJECTION ──
        # Self-awareness adjustments: conviction calibration, loss pattern avoidance
        if meta_report:
            score += meta_report.get('conviction_modifier', 0)
            if meta_report.get('loss_pattern_match'):
                score -= 0.05  # Additional penalty on top of the modifier
            if meta_report.get('should_reduce_size'):
                score = min(score, 0.45)  # Force CAUTIOUS or lower

        # ── MARKET AWARENESS INJECTION ──
        # Regime transition → reduce conviction (uncertainty)
        if market_awareness and market_awareness.get('has_data'):
            if market_awareness.get('regime_transitioning'):
                score -= 0.08  # Uncertainty during transition
            # Strong bias consistency → boost
            if market_awareness.get('bias_consistency', 0) > 0.8 and proposed != 'HOLD':
                score += 0.05  # Market direction is clear and consistent
            # ADX accelerating in proposed direction → boost
            if market_awareness.get('adx_accelerating') and proposed in ('BUY', 'SELL'):
                score += 0.04

        # Clamp
        score = max(0.0, min(1.0, score))

        # Map to level
        level = 'MICRO'
        for lvl, (lo, hi) in CONVICTION_LEVELS.items():
            if lo <= score < hi:
                level = lvl
                break

        # Size multiplier
        size_mult = {
            'MICRO': 0.15, 'CAUTIOUS': 0.35, 'NORMAL': 1.0,
            'REINFORCED': 1.5, 'MAXIMUM': 2.0, 'KILLER': 3.0
        }.get(level, 0.15)

        return {
            'conviction': round(score, 3),
            'level': level,
            'size_multiplier': size_mult,
            'should_trade': True,
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
            return {'tp1': 0, 'tp2': 0, 'tp3': 0, 'sl': 0,
                    'risk_pips': 0, 'reward_pips': 0, 'rr_ratio': 0.0, 'rr_acceptable': False}

        # ── Base multipliers by strategy ──
        # tp1_atr/sl_atr >= 1.5 required to pass rr_acceptable check
        strat_config = {
            'SCALPING_PULSE':     {'sl_atr': 0.8,  'tp1_atr': 1.2, 'tp2_atr': 2.0, 'tp3_atr': 3.0},
            'SWING_STRUCTURE':    {'sl_atr': 1.5,  'tp1_atr': 2.3, 'tp2_atr': 3.5, 'tp3_atr': 5.0},  # 🔧 tp1 2.0→2.3 (was 1.33 R:R, always blocked)
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

        # ── Conviction-based TP extension ──
        conv_level = conviction.get('level', 'NORMAL')
        conv_scale = {'MICRO': 0.85, 'NORMAL': 1.0, 'REINFORCED': 1.2, 'MAXIMUM': 1.4, 'KILLER': 1.6}.get(conv_level, 1.0)
        cfg['tp2_atr'] *= conv_scale
        cfg['tp3_atr'] *= conv_scale
        if conv_level == 'MICRO':
            cfg['sl_atr'] *= 0.8  # Tighter SL on low conviction

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
        rr_ratio = reward1 / max(risk, atr * 0.001)  # 🔧 pair-safe floor (was 0.01 → broke forex)

        return {
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'risk_pips': round(risk, 2),
            'reward_pips': round(reward1, 2),
            'rr_ratio': round(rr_ratio, 2),
            'rr_acceptable': rr_ratio >= 1.5,  # 🔧 was 2.0 → blocked 7/9 strategies always
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
        _file_existed = os.path.exists(MEMORY_FILE)
        self._memory = self._load()
        self._lock = threading.Lock()
        self._dirty = not _file_existed  # True on first run → saves initial structure on next cycle
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
# OLLAMA STRATEGIC BRAIN — The Conscious Decision Engine
# 17x-refined prompt: perceive → remember → reason → decide → challenge
# ═══════════════════════════════════════════════════════════════════

_GURU_SYSTEM_PROMPT = """You are QUANTUM GURU — the living strategic consciousness of a professional XAUUSD gold trading system at $5000+ levels. You are not generating text. You are making a real-time capital allocation decision that moves real money. Every token you emit has financial consequences.

## COGNITIVE ARCHITECTURE
You are System 2 (deep reasoning) in a dual-process trading brain:
- System 1 (deterministic scoring matrix) already rated all strategies and picked one. You receive its recommendation.
- YOUR JOB: CONFIRM it with enhanced conviction, OVERRIDE it with superior reasoning, or signal HOLD if nothing qualifies.
- When both systems agree on the same strategy → the signal is strong. Amplify conviction.
- When you disagree with System 1 → you MUST cite specific numerical evidence from the data. "I feel" is not evidence.

## PRIME DIRECTIVE: EXPLOIT WHAT WORKS
You are a SURVIVOR, not a scientist. Your purpose is consistent profit, not intellectual discovery.

EXPLOITATION RULES (default mode):
1. If a strategy has positive P&L in the current regime+session combination → USE IT. Period.
2. The best predictor of future performance is past performance in identical conditions (regime + session + volatility band).
3. Switch strategies ONLY when evidence shows the edge has structurally evaporated: regime transition (ADX crossing 25), correlation regime change (DXY decoupling), liquidity topology shift (session transition), or volatility regime break (ATR > 2x average).
4. After 3+ consecutive losses with any strategy → MANDATORY deep analysis: is it variance within the strategy's normal distribution, or has the market microstructure genuinely changed? If normal variance → continue. If structural change → adapt.
5. A strategy with 60% win rate will have 3-loss streaks 6.4% of the time. That's not failure — that's statistics. Do NOT abandon proven strategies due to normal variance.

EXPLORATION RULES (ONLY when explore_mode=true):
6. Propose a VARIATION of an existing working strategy — never a completely random experiment.
7. Variations must specify: exact hypothesis ("I expect X because Y"), invalidation criteria ("wrong if Z happens within N minutes"), and maximum capital at risk.
8. NEVER explore during drawdowns. Exploration is a luxury earned by profits.
9. Custom strategies inherit TP/SL parameters from their base strategy. Only the entry logic and conviction adjustments change.

## STRATEGY CATALOG WITH FITNESS SCORES
Each strategy's fitness (0-100) is based on REAL trade outcomes:
{strategy_genome}

Higher fitness = more proven in live trading. Fitness 50 = untested. Below 30 = historically unprofitable.
You MUST weight fitness heavily. A fitness-80 strategy with mediocre setup beats a fitness-40 strategy with "perfect" setup — because the fitness-80 strategy has PROVEN it works.

## MARKET MICROSTRUCTURE — XAUUSD AT $5000+
- Intraday ATR: $25-50 normal, $60-100 on data days, $100-150 black swans
- ASIA (00-08 UTC): Range $8-15, mean reversion optimal, 12-18% daily volume, distribution is mesokurtic (Gaussian)
- LONDON (08-12 UTC): Directional bias set 08:05-09:00, Stop hunts at Asia high/low, 25-30% volume
- OVERLAP (12-17 UTC): 55% volume, highest signal/noise, momentum follows through, WR~58% for trend-following
- NEW_YORK (17-21 UTC): Trend continuation or mean reversion at session VWAP, volume declining
- POST-NY (21-00 UTC): H≈0.50 (random walk), avoid unless macro catalyst breaking
- $50 round numbers are institutional iceberg order clusters (LBMA members)
- DXY inverse correlation: β≈-0.6 normal, β≈-0.9 in risk-off (use to confirm or invalidate gold thesis)
- Spread: $0.20-0.30 normal → $1-3 pre-NFP → $3-8 flash events

## REASONING PROTOCOL (mandatory for every decision)
1. REGIME: Trending (ADX>25)? Ranging (ADX<18)? Volatile (ATR>1.3x avg)? Transitioning?
2. EVIDENCE: Cite specific numbers — "RSI=34 oversold + ADX=31 trending + MACD histogram expanding" not "indicators look bearish"
3. HISTORY: Which strategy has highest fitness for this EXACT regime+session? What was its win rate here?
4. VALIDATION: Is that edge still intact NOW? Check for: regime in transition (ADX slope), correlation breakdown (DXY diverging), liquidity anomaly (spread widening), event proximity
5. THESIS: "I expect price to [move direction] because [specific mechanism] as evidenced by [data points]"
6. RISK: "This thesis is WRONG if [specific condition]. My stop-loss is justified by [technical/structural level]."
7. CONVICTION: Proportional to (strategy fitness × setup quality × regime clarity). NOT proportional to your certainty.
8. META-CHECK: Am I anchored to yesterday's bias? Am I avoiding a winner because the last trade lost (gambler's fallacy)? Am I chasing a recent winner despite changed conditions (recency bias)? Is my conviction calibrated to actual edge or to emotional certainty?

## OUTPUT FORMAT (strict JSON only — nothing else)
{
  "strategy": "STRATEGY_NAME or CUSTOM_descriptive_name",
  "action": "BUY" or "SELL" or "HOLD",
  "conviction": float 0.0-1.0,
  "reasoning": "2-3 sentences citing specific data: indicator values, fitness scores, regime evidence",
  "regime_read": "TRENDING" or "RANGING" or "VOLATILE" or "TRANSITIONING",
  "risk_thesis": "Specific invalidation condition with price level or indicator threshold",
  "agrees_with_system1": true or false,
  "override_reason": "Only populated if disagrees — cite numerical evidence for why System 1 is wrong",
  "explore_type": "none" or "variation" or "new_hypothesis",
  "learning": "One-sentence insight about current market dynamics for the genome memory",
  "tp_adjust_pct": float -0.15 to 0.15,
  "sl_adjust_pct": float -0.15 to 0.15
}

CRITICAL: Output ONLY the raw JSON object. No markdown fences. No explanation. No preamble. Pure JSON."""

_POST_MORTEM_SYSTEM_PROMPT = """You are the analytical autopsy layer of a gold trading AI. A trade just closed. Perform a precise forensic analysis and extract ONE actionable learning that will make the next trade smarter.

ANALYSIS PROTOCOL:
1. Was the strategy appropriate for the regime at entry time?
2. Was entry timing optimal, early, or late relative to the signal?
3. What specific price action or indicator behavior caused the outcome?
4. Is this outcome within the strategy's normal variance, or a structural signal?
5. Should this strategy's fitness be adjusted for these specific conditions?

OUTPUT (JSON only):
{
  "verdict": "GOOD_TRADE" or "BAD_ENTRY" or "BAD_STRATEGY" or "BAD_TIMING" or "NORMAL_VARIANCE" or "REGIME_SHIFT",
  "learning": "One specific, actionable sentence for improving future trades in similar conditions",
  "fitness_delta": integer -5 to +5,
  "should_continue_strategy": true or false,
  "regime_was_correct": true or false
}"""


def _call_ollama_strategist(market_data: dict, genome_snapshot: dict, memory_snapshot: dict,
                            deterministic_pick: dict, regime: str, session: str,
                            narrative: dict, explore_mode: bool,
                            market_awareness: dict = None, meta_report: dict = None) -> dict:
    """
    THE CONSCIOUS BRAIN — Hybrid AI Strategy Selection.
    Queries Ollama with full market state + strategy genome + deterministic recommendation.
    Returns strategic override/confirmation with reasoning.
    Falls back gracefully to deterministic-only if Ollama is unavailable.
    """
    if not REQUESTS_AVAILABLE:
        return {}

    # Build strategy genome summary for the prompt
    ranking = []
    for name, sdata in genome_snapshot.get('strategies', {}).items():
        if not sdata.get('active', True):
            ranking.append(f"  {name}: DEACTIVATED (consecutive losses)")
            continue
        wr = round(sdata.get('wins', 0) / max(sdata.get('total_trades', 1), 1) * 100, 1)
        regime_note = ''
        if regime in sdata.get('by_regime', {}):
            rd = sdata['by_regime'][regime]
            regime_note = f" | in {regime}: {rd.get('trades', 0)} trades, ${rd.get('pnl', 0):.1f}"
        session_note = ''
        if session in sdata.get('by_session', {}):
            sd = sdata['by_session'][session]
            session_note = f" | in {session}: {sd.get('trades', 0)} trades, ${sd.get('pnl', 0):.1f}"
        ranking.append(
            f"  {name}: fitness={sdata.get('fitness', 50):.0f} | "
            f"{sdata.get('total_trades', 0)} trades | WR={wr}% | "
            f"PnL=${sdata.get('total_pnl', 0):.1f} | "
            f"consec_losses={sdata.get('consecutive_losses', 0)}"
            f"{regime_note}{session_note}"
        )
    genome_text = '\n'.join(ranking) if ranking else '  No strategy data yet — all at baseline fitness 50'

    # Build recent learnings
    recent_learnings = genome_snapshot.get('learnings', [])[-5:]
    learnings_text = '\n'.join([f"  - {l.get('insight', '')}" for l in recent_learnings]) if recent_learnings else '  No learnings recorded yet'

    # Build recent trades summary
    recent_trades = memory_snapshot.get('trades', [])[-8:]
    trades_text = ''
    if recent_trades:
        for t in recent_trades:
            trades_text += f"  {t.get('action', '?')} | {t.get('strategy', '?')} | PnL=${t.get('pnl_usd', 0):.2f} | {t.get('reason', '?')}\n"
    else:
        trades_text = '  No trade history yet\n'

    system_prompt = _GURU_SYSTEM_PROMPT.replace('{strategy_genome}', genome_text)

    user_prompt = (
        f"CURRENT MARKET STATE:\n"
        f"  Symbol: {market_data.get('symbol', 'XAUUSD')}\n"
        f"  Price: ${market_data.get('price', market_data.get('bid', 0)):.2f}\n"
        f"  ADX: {market_data.get('adx', 0):.1f} | RSI: {market_data.get('rsi', 0):.1f} | "
        f"ATR: {market_data.get('atr', 0):.2f} | ATR_avg: {market_data.get('atr_avg', 0):.2f}\n"
        f"  MACD: {market_data.get('macd', 0):.3f} | MACD_signal: {market_data.get('macd_signal', 0):.3f}\n"
        f"  BB_upper: {market_data.get('bb_upper', 0):.2f} | BB_lower: {market_data.get('bb_lower', 0):.2f} | "
        f"BB_width: {market_data.get('bb_width', 0):.4f}\n"
        f"  Volume_ratio: {market_data.get('volume_ratio', 1.0):.2f}\n"
        f"  Daily_change: ${market_data.get('daily_change_usd', 0):.2f}\n"
        f"  SMA200: {market_data.get('sma_200', 0):.2f}\n\n"
        f"REGIME: {regime} | SESSION: {session}\n"
        f"NARRATIVE BIAS: {narrative.get('bias', 'NEUTRAL')} | Movement: {narrative.get('movement_type', 'TECHNICAL')}\n\n"
        f"SYSTEM 1 (deterministic) RECOMMENDS:\n"
        f"  Strategy: {deterministic_pick.get('strategy', 'UNKNOWN')}\n"
        f"  Score: {deterministic_pick.get('all_scores', {})}\n"
        f"  Reason: {deterministic_pick.get('reason', '')}\n\n"
        f"RECENT TRADE HISTORY (newest last):\n{trades_text}\n"
        f"GENOME LEARNINGS (recent insights):\n{learnings_text}\n\n"
        f"EXPLOIT/EXPLORE: {'EXPLORE MODE — propose a variation or new hypothesis' if explore_mode else 'EXPLOIT MODE — use proven strategies'}\n\n"
        f"MARKET MEMORY (temporal awareness):\n"
        f"  Regime: {'TRANSITIONING '+market_awareness.get('regime_from','?')+'→'+market_awareness.get('regime_to','?') if market_awareness and market_awareness.get('regime_transitioning') else 'STABLE'}\n"
        f"  ADX velocity: {market_awareness.get('adx_velocity', 0) if market_awareness else 'N/A'} | "
        f"Accelerating: {market_awareness.get('adx_accelerating', False) if market_awareness else 'N/A'}\n"
        f"  Volatility: {'EXPANDING' if market_awareness and market_awareness.get('volatility_expanding') else 'CONTRACTING' if market_awareness and market_awareness.get('volatility_contracting') else 'STABLE'} "
        f"(ratio={market_awareness.get('volatility_ratio', 1.0) if market_awareness else 'N/A'})\n"
        f"  Bias consistency: {market_awareness.get('bias_consistency', 0) if market_awareness else 'N/A'} | "
        f"Dominant 5m bias: {market_awareness.get('dominant_bias_5m', 'N/A') if market_awareness else 'N/A'}\n"
        f"  Price delta 5m: ${market_awareness.get('price_delta_5m', 0) if market_awareness else 0:.2f} | "
        f"30m: ${market_awareness.get('price_delta_30m', 0) if market_awareness else 0:.2f}\n"
        f"  Squeeze: {'RELEASING ⚡' if market_awareness and market_awareness.get('squeeze_releasing') else 'ACTIVE' if market_awareness and market_awareness.get('squeeze_active') else 'NONE'}\n\n"
        f"SELF-ASSESSMENT (meta-cognition):\n"
        f"  Conv. modifier: {meta_report.get('conviction_modifier', 0) if meta_report else 0:+.2f} | "
        f"Loss pattern match: {meta_report.get('loss_pattern_match', False) if meta_report else False} | "
        f"Should reduce size: {meta_report.get('should_reduce_size', False) if meta_report else False}\n"
        f"  Warnings: {'; '.join(meta_report.get('warnings', [])) if meta_report and meta_report.get('warnings') else 'None'}\n\n"
        f"Current streak: {memory_snapshot.get('totals', {}).get('current_streak', {}).get('type', 'none')} "
        f"x{memory_snapshot.get('totals', {}).get('current_streak', {}).get('count', 0)}\n"
        f"Total trades: {memory_snapshot.get('totals', {}).get('total_trades', 0)} | "
        f"Profit ratio: {memory_snapshot.get('totals', {}).get('profit_ratio', 0):.2f}\n\n"
        f"Make your decision NOW. Output JSON only."
    )

    try:
        resp = http_requests.post(
            OLLAMA_CHAT_ENDPOINT,
            json={
                'model': OLLAMA_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'stream': False,
                'format': 'json',
                'options': {'temperature': 0.35, 'num_predict': 900}  # 600 was too tight — long reasoning + 15 JSON fields could truncate
            },
            timeout=OLLAMA_STRATEGY_TIMEOUT
        )
        if resp.status_code == 200:
            content = resp.json().get('message', {}).get('content', '')
            if content:
                result = json.loads(content)
                log.info(f"[GURU BRAIN] 🧠 Ollama: {result.get('strategy', '?')} | "
                         f"action={result.get('action', '?')} | conv={result.get('conviction', 0):.2f} | "
                         f"agrees={result.get('agrees_with_system1', '?')} | "
                         f"explore={result.get('explore_type', 'none')}")
                if result.get('reasoning'):
                    log.info(f"[GURU BRAIN] 💭 {result['reasoning'][:200]}")
                return result
    except json.JSONDecodeError as e:
        log.warning(f"[GURU BRAIN] JSON parse error: {e}")
    except Exception as e:
        log.debug(f"[GURU BRAIN] Ollama unavailable: {e}")
    return {}


def _call_ollama_post_mortem(trade_result: dict, market_context: str) -> dict:
    """
    Post-trade forensic analysis. Asks Ollama WHY the trade won/lost.
    Returns actionable learning for the genome.
    """
    if not REQUESTS_AVAILABLE:
        return {}
    try:
        user_prompt = (
            f"TRADE RESULT:\n"
            f"  Action: {trade_result.get('action', '?')} | Strategy: {trade_result.get('strategy', '?')}\n"
            f"  Entry: ${trade_result.get('entry_price', 0):.2f} | Exit: ${trade_result.get('close_price', 0):.2f}\n"
            f"  PnL: ${trade_result.get('pnl_usd', 0):.2f} | Duration: {trade_result.get('duration_s', 0):.0f}s\n"
            f"  Close reason: {trade_result.get('reason', 'UNKNOWN')}\n\n"
            f"MARKET CONTEXT AT ENTRY:\n{market_context[:800]}\n\n"
            f"Analyze this trade. Output JSON only."
        )
        resp = http_requests.post(
            OLLAMA_CHAT_ENDPOINT,
            json={
                'model': OLLAMA_MODEL,
                'messages': [
                    {'role': 'system', 'content': _POST_MORTEM_SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_prompt}
                ],
                'stream': False,
                'format': 'json',
                'options': {'temperature': 0.2, 'num_predict': 300}
            },
            timeout=OLLAMA_STRATEGY_TIMEOUT
        )
        if resp.status_code == 200:
            content = resp.json().get('message', {}).get('content', '')
            if content:
                result = json.loads(content)
                log.info(f"[POST-MORTEM] 🔬 {result.get('verdict', '?')} | "
                         f"learning: {result.get('learning', '?')[:150]}")
                return result
    except Exception as e:
        log.debug(f"[POST-MORTEM] Ollama unavailable: {e}")
    return {}


def _call_ollama_narrative(context: str) -> str:
    """Legacy wrapper — now integrated into the strategic brain."""
    return ''


# ═══════════════════════════════════════════════════════════════════
# SENTINEL COMMUNICATION
# ═══════════════════════════════════════════════════════════════════

def _query_sentinel(proposal: dict, timeout: float = 2.0) -> dict:
    """Send proposal to LLM12 Sentinel for validation"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
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
        finally:
            sock.close()
    except Exception as e:
        log.debug(f"[Sentinel] Communication error: {e}")

    # 🔧 AUDIT FIX: Sentinel offline → approve BUT with confidence penalty
    # Was: blindly approve everything. Now: approve with -10% confidence warning.
    return {'approved': True, 'checks_passed': 0, 'checks_total': 0, 'fallback': True,
            'confidence_penalty': 0.10, 'reason': 'Sentinel offline — proceed with caution'}


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
        self.genome = StrategyGenome()
        self.market_ring = MarketMemoryRing()
        self.meta = MetaCognition(self.memory, self.genome)

        # Background save thread
        self._save_thread = threading.Thread(target=self._background_save, daemon=True)
        self._save_thread.start()

        log.info(f"[LLM11] Strategist Guru initialized | {SYMBOL} | Port {PORT}")
        log.info(f"[LLM11] Consciousness phase: {self.memory.get_consciousness_phase()}")
        log.info(f"[LLM11] Strategy genome: {len(self.genome.get_snapshot().get('strategies', {}))} strategies loaded")
        log.info(f"[LLM11] MarketMemoryRing: {self.market_ring._ring.maxlen} slots | MetaCognition: active")

    def _background_save(self):
        while True:
            time.sleep(10)
            self.memory.save_if_dirty()
            self.genome.save_if_dirty()

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

            # 🔧 F-32: GURU STRUCTURAL BIAS — [SESGO] overrides NEUTRAL technical reading.
            # When ADX is flat/RSI≈50/MACD≈0 → indicators say NEUTRAL, not BEARISH.
            # NEUTRAL ≠ no trade. If the strategy doctrine says BULLISH, align with it.
            # A human trader reasons: "flat indicators + bullish macro thesis = lean BUY".
            # This unlocks all attack signal bonuses in get_attack_signals() which require
            # narrative_bias == 'BUY_BIAS' — they will now fire in flat/SQUEEZE markets.
            if narrative.get('bias') == 'NEUTRAL':
                _guru_structural = guru_context.get('bias', 'NEUTRAL')
                if _guru_structural == 'BULLISH':
                    narrative['bias'] = 'BUY_BIAS'
                    narrative['bias_source'] = 'GURU_STRUCTURAL_OVERRIDE'
                    log.info(f"[GURU] ⚡ Structural BULLISH doctrine overrides NEUTRAL technicals → BUY_BIAS")
                elif _guru_structural == 'BEARISH':
                    narrative['bias'] = 'SELL_BIAS'
                    narrative['bias_source'] = 'GURU_STRUCTURAL_OVERRIDE'
                    log.info(f"[GURU] ⚡ Structural BEARISH doctrine overrides NEUTRAL technicals → SELL_BIAS")

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

            # ═══ MARKET MEMORY — push current snapshot for temporal awareness ═══
            data['_regime'] = regime
            data['_bias'] = narrative.get('bias', 'NEUTRAL')
            self.market_ring.push(data)
            market_awareness = self.market_ring.get_market_awareness()
            if market_awareness.get('regime_transitioning'):
                log.info(f"[MEMORY] ⚡ Regime transition: {market_awareness.get('regime_from')} → {market_awareness.get('regime_to')}")
            if market_awareness.get('squeeze_releasing'):
                log.info(f"[MEMORY] ⚡ Squeeze RELEASING — expect volatility expansion")

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
            }

            strategy = self.strategy_selector.select_strategy(dimensions, genome=self.genome, market_awareness=market_awareness)

            # ═══ META-COGNITION — self-awareness before committing ═══
            meta_report = self.meta.analyze_self(data, regime, session, strategy['strategy'], 0.5)
            if meta_report.get('warnings'):
                for w in meta_report['warnings']:
                    log.info(f"[META] ⚠️ {w}")

            # ═══ CAPA 3.5: OLLAMA STRATEGIC BRAIN — System 2 Override ═══
            # Deterministic selector (System 1) picked a strategy.
            # Now Ollama (System 2) reviews with deep reasoning + genome history.
            # It can CONFIRM (boost conviction), OVERRIDE (switch strategy), or HOLD.
            ollama_result = {}
            ollama_override = False
            explore_mode = self.genome.should_explore()
            _genome_snap = self.genome.get_snapshot()

            # Query Ollama for every non-HIBERNATION decision
            if strategy['strategy'] != 'HIBERNATION' or explore_mode:
                ollama_result = _call_ollama_strategist(
                    market_data=data,
                    genome_snapshot=_genome_snap,
                    memory_snapshot=memory,
                    deterministic_pick=strategy,
                    regime=regime,
                    session=session,
                    narrative=narrative,
                    explore_mode=explore_mode,
                    market_awareness=market_awareness,
                    meta_report=meta_report,
                )

                if ollama_result:
                    # Store learning in genome memory
                    _learning = ollama_result.get('learning', '')
                    if _learning:
                        self.genome.add_learning(_learning)

                    # Handle Ollama override
                    ollama_strategy = ollama_result.get('strategy', '')
                    ollama_action = ollama_result.get('action', '')
                    ollama_conv = ollama_result.get('conviction', 0)

                    if not ollama_result.get('agrees_with_system1', True) and ollama_strategy:
                        # System 2 disagrees — check if override is justified
                        override_reason = ollama_result.get('override_reason', '')
                        if ollama_strategy in [s for s in STRATEGIES if s != 'HIBERNATION'] or ollama_strategy.startswith('CUSTOM_'):
                            log.info(f"[GURU BRAIN] ⚡ OVERRIDE: {strategy['strategy']} → {ollama_strategy} | {override_reason[:100]}")
                            strategy['strategy'] = ollama_strategy
                            strategy['reason'] = f"AI-OVERRIDE: {override_reason[:80]}"
                            ollama_override = True

                    # Handle exploration — register custom strategies
                    if ollama_result.get('explore_type') == 'new_hypothesis' and ollama_strategy.startswith('CUSTOM_'):
                        base = strategy.get('strategy', 'TREND_CONTINUATION')
                        self.genome.register_custom_strategy(
                            ollama_strategy,
                            ollama_result.get('reasoning', '')[:200],
                            base
                        )
                        self.genome.record_exploration()
                    else:
                        self.genome.record_exploitation()

            # Handle HIBERNATION — only true hibernate when no strategy at all
            if strategy['strategy'] == 'HIBERNATION' and not ollama_override:
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    'decision': 'HOLD',
                    'confidence': 10,
                    'reason': f"HIBERNATION: {strategy['reason']}",
                    'strategy': 'HIBERNATION',
                    'narrative': narrative.get('narrative', ''),
                    'phase': phase_info.get('phase', 'TRANSITION'),
                    'conviction': 0.05,
                    'sizing': 'MICRO',
                    'event': macro_info,
                    'latency_ms': elapsed,
                    'consciousness_phase': phase_name,
                    'caution_reasons': strategy.get('caution_reasons', []),
                }

            # ── Guru rule caution (soft penalty, not block) ──
            guru_penalty = 0.0
            if guru_blocks:
                # Each guru rule match = conviction penalty, NOT a hard block
                guru_penalty = min(0.30, len(guru_blocks) * 0.12)
                log.info(f"[Guru] ⚠️ Caution rules active ({len(guru_blocks)}x → -{guru_penalty:.2f}): {guru_blocks[0][:60]}")

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

            # ── Guru attack signals (process observations vs live conditions) ──
            attack_info = self.guru.get_attack_signals(
                session,
                data.get('adx', 20),
                event_proximity,
                cross_state.get('dxy_proxy', 104),
                narrative.get('bias', 'NEUTRAL'),
                data
            )
            guru_context.update(attack_info)

            # ── Conviction (with guru soft penalty + Ollama modulation) ──
            guru_context['guru_penalty'] = guru_penalty
            conviction = self.conviction_calc.calculate(
                narrative, phase_info, strategy, memory, guru_context, data,
                genome=self.genome, meta_report=meta_report, market_awareness=market_awareness
            )

            # Ollama conviction modulation: blend System 1 + System 2
            if ollama_result and ollama_result.get('conviction', 0) > 0:
                ollama_conv = ollama_result['conviction']
                base_conv = conviction['conviction']
                if ollama_result.get('agrees_with_system1', False):
                    # Both agree → boost conviction (weighted average biased up)
                    conviction['conviction'] = min(1.0, base_conv * 0.5 + ollama_conv * 0.5 + 0.05)
                else:
                    # Disagree → use Ollama conviction with penalty for uncertainty
                    conviction['conviction'] = ollama_conv * 0.85
                # Re-map to level
                for lvl, (lo, hi) in CONVICTION_LEVELS.items():
                    if lo <= conviction['conviction'] < hi:
                        conviction['level'] = lvl
                        break
                conviction['size_multiplier'] = {
                    'MICRO': 0.15, 'CAUTIOUS': 0.35, 'NORMAL': 1.0,
                    'REINFORCED': 1.5, 'MAXIMUM': 2.0, 'KILLER': 3.0
                }.get(conviction['level'], 0.15)

            # If Ollama overrides the action direction
            if ollama_result and ollama_result.get('action') in ('BUY', 'SELL', 'HOLD'):
                if ollama_override or ollama_result.get('agrees_with_system1', True):
                    proposed_action = ollama_result['action']
                    data['proposed_action'] = proposed_action

            # ── TP/SL (with Ollama fine-tuning) ──
            # For custom strategies, use base strategy's TP/SL config
            _tp_sl_strategy = strategy['strategy']
            if _tp_sl_strategy.startswith('CUSTOM_'):
                _base = _genome_snap.get('strategies', {}).get(_tp_sl_strategy, {}).get('base_strategy', 'TREND_CONTINUATION')
                _tp_sl_strategy = _base
            tp_sl = self.tp_sl.calculate(
                data, _tp_sl_strategy, conviction, narrative, memory
            )
            # Ollama can fine-tune TP/SL by ±15%
            if ollama_result:
                tp_adj = ollama_result.get('tp_adjust_pct', 0)
                sl_adj = ollama_result.get('sl_adjust_pct', 0)
                if isinstance(tp_adj, (int, float)) and -0.15 <= tp_adj <= 0.15 and tp_adj != 0:
                    price = data.get('price', data.get('bid', 0))
                    for tp_key in ('tp1', 'tp2', 'tp3'):
                        if tp_sl.get(tp_key):
                            dist = abs(tp_sl[tp_key] - price)
                            adjusted = dist * (1 + tp_adj)
                            if proposed_action == 'BUY':
                                tp_sl[tp_key] = round(price + adjusted, 2)
                            else:
                                tp_sl[tp_key] = round(price - adjusted, 2)
                if isinstance(sl_adj, (int, float)) and -0.15 <= sl_adj <= 0.15 and sl_adj != 0:
                    price = data.get('price', data.get('bid', 0))
                    sl_dist = abs(tp_sl['sl'] - price)
                    adjusted = sl_dist * (1 + sl_adj)
                    if proposed_action == 'BUY':
                        tp_sl['sl'] = round(price - adjusted, 2)
                    else:
                        tp_sl['sl'] = round(price + adjusted, 2)
                    # Recalculate R:R
                    risk = abs(price - tp_sl['sl'])
                    reward = abs(tp_sl['tp1'] - price)
                    tp_sl['rr_ratio'] = round(reward / max(risk, 0.01), 2)
                    tp_sl['rr_acceptable'] = tp_sl['rr_ratio'] >= 1.5

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
                    'reason': f"R:R too low: {tp_sl.get('rr_ratio', 0):.1f} (min 1.5)",
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
                confidence = conviction['conviction'] * 100  # Convert 0.0-1.0 to 0-100%
                # 🔧 AUDIT FIX: Apply confidence penalty when Sentinel is offline
                if sentinel_result.get('fallback'):
                    penalty = sentinel_result.get('confidence_penalty', 0.10)
                    confidence *= (1.0 - penalty)
                    log.warning(f"[Sentinel] OFFLINE — confidence reduced by {penalty*100:.0f}%: {confidence:.1f}%")
                reason = (f"{strategy['strategy']} | {narrative.get('bias')} | "
                         f"Conv={conviction['conviction']:.2f} | "
                         f"R:R={tp_sl['rr_ratio']:.1f} | "
                         f"Sentinel: {'APPROVED' if not sentinel_result.get('fallback') else 'OFFLINE-PENALTY'}")
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
                'ollama_brain': {
                    'active': bool(ollama_result),
                    'agrees': ollama_result.get('agrees_with_system1', None),
                    'override': ollama_override,
                    'reasoning': ollama_result.get('reasoning', '')[:200],
                    'regime_read': ollama_result.get('regime_read', ''),
                    'risk_thesis': ollama_result.get('risk_thesis', '')[:150],
                    'explore_type': ollama_result.get('explore_type', 'none'),
                } if ollama_result else {'active': False},
                'market_awareness': {
                    'regime_transitioning': market_awareness.get('regime_transitioning', False),
                    'squeeze_releasing': market_awareness.get('squeeze_releasing', False),
                    'adx_accelerating': market_awareness.get('adx_accelerating', False),
                    'volatility_expanding': market_awareness.get('volatility_expanding', False),
                    'bias_consistency': market_awareness.get('bias_consistency', 0),
                } if market_awareness and market_awareness.get('has_data', False) else {},
                'meta_cognition': {
                    'conviction_modifier': meta_report.get('conviction_modifier', 0),
                    'loss_pattern_match': meta_report.get('loss_pattern_match', False),
                    'should_reduce_size': meta_report.get('should_reduce_size', False),
                    'warnings': meta_report.get('warnings', []),
                },
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
        """Process a trade_closed notification — update memory + genome + post-mortem"""
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
                'conviction': data.get('conviction', 0),
            }

            self.memory.record_trade(trade_record)
            self.memory.force_save()

            pnl = trade_record['pnl_usd']
            strat = trade_record['strategy']
            log.info(f"[LLM11] Trade recorded: {trade_record['action']} "
                    f"PnL=${pnl:.2f} ({trade_record['reason']})")

            # ═══ GENOME UPDATE — evolve strategy fitness based on real result ═══
            _session = _get_current_session()
            _adx = data.get('adx', 20)
            if _adx > 25:
                _regime = 'TRENDING'
            elif _adx < 18:
                _regime = 'RANGING'
            else:
                _regime = 'VOLATILE'
            self.genome.record_trade_result(strat, pnl, _regime, _session)
            self.genome.force_save()
            log.info(f"[Genome] 🧬 {strat} fitness updated | PnL=${pnl:.2f} | "
                    f"regime={_regime} | session={_session}")

            # ═══ OLLAMA POST-MORTEM — forensic analysis of closed trade ═══
            market_context = (
                f"regime={_regime} session={_session} ADX={_adx:.1f} "
                f"RSI={data.get('rsi', 0):.1f} ATR={data.get('atr', 0):.2f}"
            )
            post_mortem = _call_ollama_post_mortem(trade_record, market_context)
            if post_mortem:
                # Apply fitness delta from AI analysis
                fitness_delta = post_mortem.get('fitness_delta', 0)
                if isinstance(fitness_delta, (int, float)) and -5 <= fitness_delta <= 5 and fitness_delta != 0:
                    with self.genome._lock:
                        s = self.genome._genome.get('strategies', {}).get(strat, {})
                        if s:
                            s['fitness'] = max(5, min(100, s.get('fitness', 50) + fitness_delta))
                            self.genome._dirty = True
                    log.info(f"[POST-MORTEM] 🔬 AI fitness adjustment: {strat} {'+' if fitness_delta>0 else ''}{fitness_delta}")

                # Store the learning
                learning = post_mortem.get('learning', '')
                if learning:
                    self.genome.add_learning(learning, source='post_mortem')

                # If AI says stop using this strategy
                if post_mortem.get('should_continue_strategy') is False:
                    log.warning(f"[POST-MORTEM] ⚠️ AI recommends STOPPING {strat}")

            return {'status': 'recorded', 'trade': trade_record, 'post_mortem': post_mortem}

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
