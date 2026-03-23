#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nova_dashboard.py — NOVA Trading AI | Dashboard v5.0
Polarice Labs © 2026

Reescritura completa con QPainter puro — misma arquitectura que
nova_installer_pyside6.py y nova_keygen_pyside6.py.

- Sub-ventanas custom (sin QMdiArea) con title bar QPainter
- Partículas doradas idénticas al keygen
- Botones estilo keygen con gradiente dorado
- Sidebar resizable con QSplitter
- Session bar con todas las sesiones identificadas
"""
from __future__ import annotations
import json, logging, math, os, random, re, socket, subprocess, sys, threading, time
try:
    import MetaTrader5 as _mt5
    _MT5_OK = True
except ImportError:
    _mt5 = None
    _MT5_OK = False
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
if sys.platform == "win32":
    import ctypes, ctypes.wintypes

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QSplitter, QFrame, QSizePolicy, QTextEdit,
    QProgressBar, QPushButton,
)
from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QPoint, Signal, Slot, QThread, QSize, QRect,
    Property, QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import (
    QFont, QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPainterPath, QCursor, QRadialGradient, QPalette, QPixmap, QImage, QFontDatabase, QIcon,
)
from services.license_service import LicenseService, LicenseSnapshot
from services.dashboard_action_controller import DashboardActionController
from services.dashboard_body_builder import DashboardBodyBuilder
from services.dashboard_presenter import DashboardPresenter
from services.mt5_service import MT5Service
from services.path_service import PathService
from services.telemetry_service import TelemetryService
from services.runtime_manager import RuntimeManager

# ── Updater automático ────────────────────────────────────────────────────────
try:
    from nova_updater import NovaUpdater
    _UPDATER_AVAILABLE = True
except ImportError:
    _UPDATER_AVAILABLE = False

PATHS = PathService.from_entry(__file__)
PATHS.extend_sys_path()
_ROOT = PATHS.root
_BUNDLE = PATHS.bundle
ORBITRON_DIR = PATHS.orbitron_dir
try:
    from license_manager import get_license_status
    _LM_OK = True
except ImportError:
    _LM_OK = False

logger = logging.getLogger("nova.dashboard")
CORE_DIR = PATHS.core_dir

FONT_FALLBACK = "Segoe UI"
FONT_FAMILIES = {"display": FONT_FALLBACK}
FONT_DISPLAY = FONT_FAMILIES["display"]


def _ui_font(size: int, weight: int = QFont.Medium) -> QFont:
    return QFont(FONT_DISPLAY, size, weight)


def _font_css_family() -> str:
    return f"'{FONT_DISPLAY}',Arial"
def _pair_short_code(sym: str) -> str:
    sym = str(sym or "").upper().strip()
    special = {
        "NAS100": "US30",
        "US30": "US30",
        "US30USD": "US30",
        "BTCUSD": "BTC",
        "ETHUSD": "ETH",
    }
    if sym in special:
        return special[sym]
    if len(sym) >= 6 and sym[:3].isalpha() and sym[3:6].isalpha():
        base, quote = sym[:3], sym[3:6]
        return base if quote == "USD" else quote
    return sym[:3] if len(sym) >= 3 else sym

def _ensure_dashboard_fonts_loaded() -> None:
    global FONT_DISPLAY
    if FONT_DISPLAY != FONT_FALLBACK:
        return
    for fp in (
        ORBITRON_DIR / "static" / "Orbitron-Bold.ttf",
        ORBITRON_DIR / "static" / "Orbitron-SemiBold.ttf",
        ORBITRON_DIR / "Orbitron-VariableFont_wght.ttf",
    ):
        if not fp.exists():
            continue
        try:
            fid = QFontDatabase.addApplicationFont(str(fp))
            fams = QFontDatabase.applicationFontFamilies(fid)
            if fams:
                FONT_FAMILIES["display"] = fams[0]
                FONT_DISPLAY = fams[0]
                break
        except Exception:
            pass

try:
    from nova_diagnostics import DiagnosticsEngine, DiagnosticsPanel
    _DIAG_OK = True
except ImportError:
    _DIAG_OK = False

C = {
    "bg":      "#040402", "card":    "#121008", "card2":   "#181510",
    "input":   "#1E1A10", "border":  "#302808", "border2": "#483C15",
    "accent":  "#FFB829", "gold":    "#FFD700",
    "success": "#00FF88", "error":   "#FF4444", "warn":    "#FFA500",
    "info":    "#49B8FF", "violet":  "#B04DFF",
    "text":    "#FFFFFF", "text2":   "#E8D8B0",
    "dim":     "#A08C5A", "dim2":    "#C8B478",
    "buy":     "#00FF88", "sell":    "#FF4444", "hold":    "#A08C5A",
}

PAIR_CATALOG = {
    "XAUUSD": {"sym":"XAUUSD","short":"XAU","name":"Gold",   "icon":"XAU","color":"#FFD700","port_base":5500,"strategy":"Golden Bullet v3.2"},
    "EURUSD": {"sym":"EURUSD","short":"EUR","name":"Euro",   "icon":"EUR","color":"#4A90D9","port_base":6500,"strategy":"Ares War v1.2"},
    "USDJPY": {"sym":"USDJPY","short":"JPY","name":"Samurai","icon":"JPY","color":"#FF6B6B","port_base":7500,"strategy":"Samurai Predator"},
    "GBPUSD": {"sym":"GBPUSD","short":"GBP","name":"Beast",  "icon":"GBP","color":"#9B59B6","port_base":9500,"strategy":"Excalibur Knight"},
    "AUDUSD": {"sym":"AUDUSD","short":"AUD","name":"Miner",  "icon":"AUD","color":"#E67E22","port_base":8500,"strategy":"Lance Forger"},
    "USDCAD": {"sym":"USDCAD","short":"CAD","name":"Petro",  "icon":"CAD","color":"#1ABC9C","port_base":11500,"strategy":"Petro Engine"},
    "USDCHF": {"sym":"USDCHF","short":"CHF","name":"Refuge", "icon":"CHF","color":"#95A5A6","port_base":10500,"strategy":"Sniper v17.03"},
    "NZDUSD": {"sym":"NZDUSD","short":"NZD","name":"Kiwi",   "icon":"NZD","color":"#2ECC71","port_base":12500,"strategy":"Maui Storm v2.2"},
    "BTCUSD": {"sym":"BTCUSD","short":"BTC","name":"Crypto", "icon":"BTC","color":"#F39C12","port_base":15500,"strategy":"Crypto Pulse"},
    "USDCNH": {"sym":"USDCNH","short":"CNH","name":"Dragon", "icon":"CNH","color":"#E74C3C","port_base":14500,"strategy":"Red Dragon v1.1"},
    "US30":   {"sym":"US30","short":"US30","name":"US30",   "icon":"US30","color":"#3498DB","port_base":17500,"strategy":"Index Hunter"},
    "USDSEK": {"sym":"USDSEK","short":"SEK","name":"Nordic", "icon":"SEK","color":"#5DADE2","port_base":8650,"strategy":"Excalibur Knight"},
}

PAIR_RUNTIME_HINTS = {
    "XAUUSD": {"folder": "xauusd", "start": "xaustart.bat", "prefix": "xau", "pid": "xauquantum_core.pid"},
    "EURUSD": {"folder": "eurusd", "start": "eustart.bat", "prefix": "eu", "pid": "euquantum_core.pid"},
    "USDJPY": {"folder": "usdjpy", "start": "jpystart.bat", "prefix": "jpy", "pid": "jpyquantum_core.pid"},
    "GBPUSD": {"folder": "gbpusd", "start": "gbpstart.bat", "prefix": "gbp", "pid": "gbpquantum_core.pid"},
    "AUDUSD": {"folder": "audusd", "start": "audstart.bat", "prefix": "aud", "pid": "audquantum_core.pid"},
    "USDCAD": {"folder": "cadusd", "start": "cadstart.bat", "prefix": "cad", "pid": "cadquantum_core.pid"},
    "USDCHF": {"folder": "chfusd", "start": "chfstart.bat", "prefix": "chf", "pid": "chfquantum_core.pid"},
    "NZDUSD": {"folder": "nzdusd", "start": "nzdstart.bat", "prefix": "nzd", "pid": "nzdquantum_core.pid"},
    "BTCUSD": {"folder": "btcusd", "start": "btcstart.bat", "prefix": "btc", "pid": "btcquantum_core.pid"},
    "USDCNH": {"folder": "cnhusd", "start": "cnhstart.bat", "prefix": "cnh", "pid": "cnhquantum_core.pid"},
    "US30":   {"folder": "us30usd", "start": "us30start.bat", "prefix": "us30", "pid": "us30quantum_core.pid"},
    "USDSEK": {"folder": "sekusd", "start": "sekstart.bat", "prefix": "sek", "pid": "sekquantum_core.pid"},
}

FOLDER_TO_SYMBOL = {rt["folder"]: sym for sym, rt in PAIR_RUNTIME_HINTS.items()}

def _fallback_pair_meta(sym: str, folder: str, prefix: str) -> dict:
    pretty = sym if sym else folder.upper()
    short = _pair_short_code(pretty)
    icon = short
    color_seed = sum(ord(c) for c in pretty) % 6
    palette = ["#5DADE2", "#AF7AC5", "#48C9B0", "#F5B041", "#EC7063", "#58D68D"]
    return {
        "sym": pretty,
        "short": short,
        "name": folder.upper(),
        "icon": icon,
        "color": palette[color_seed],
        "port_base": 0,
        "strategy": f"{prefix.upper()} Quantum Core" if prefix else "Quantum Core",
    }

def _discover_pair_runtime() -> dict:
    return RUNTIME_MANAGER.discover_pair_runtime()

def _build_available_pairs(runtime_map: dict) -> list[dict]:
    ordered_syms = [sym for sym in PAIR_CATALOG if sym in runtime_map]
    ordered_syms.extend(sorted(sym for sym in runtime_map if sym not in PAIR_CATALOG))
    pairs = []
    for sym in ordered_syms:
        rt = runtime_map[sym]
        meta = dict(PAIR_CATALOG.get(sym) or _fallback_pair_meta(sym, rt.get("folder", sym.lower()), rt.get("prefix", "")))
        meta["sym"] = sym
        meta.setdefault("short", _pair_short_code(sym))
        meta["icon"] = meta.get("short", _pair_short_code(sym))
        pairs.append(meta)
    return pairs

PORT_MAP = {
    "XAUUSD": {"trinity":6666,"kraken":5552,"sound":5560,"quantum":5554,"executor":5556,
               "llm":[5555,5557,5558,5559,5561,5004,5562,5563,5564,5565,5568,5569]},
    "EURUSD": {"trinity":7666,"kraken":6552,"sound":6570,"quantum":6554,"executor":6556,
               "llm":[6555,6557,6558,6559,6561,6562,None,None,None,None,6566,6567]},
    "USDJPY": {"trinity":7866,"kraken":7852,"sound":7870,"quantum":7854,"executor":7856,
               "llm":[7855,7857,7858,7859,7861,7862,None,None,None,None,7867,7868]},
    "GBPUSD": {"trinity":7566,"kraken":7552,"sound":7570,"quantum":7554,"executor":7556,
               "llm":[7555,7557,7558,7559,7561,7562,7563,7564,7565,7560,7567,7568]},
    "AUDUSD": {"trinity":8566,"kraken":8552,"sound":8570,"quantum":8554,"executor":8556,
               "llm":[8555,8557,8558,8559,8561,8562,8563,8564,8565,8560,8567,8568]},
    "USDCAD": {"trinity":9166,"kraken":9152,"sound":9170,"quantum":9154,"executor":9156,
               "llm":[9155,9157,9158,9159,9161,9162,9163,9164,9165,9160,9167,9168]},
    "USDCHF": {"trinity":8620,"kraken":9901,"sound":8611,"quantum":9054,"executor":9056,
               "llm":[8601,8602,8603,8604,8606,8607,None,None,None,None,8611,8612]},
    "NZDUSD": {"trinity":9266,"kraken":9252,"sound":9270,"quantum":9254,"executor":9256,
               "llm":[9255,9257,9258,9259,9261,9262,9263,9264,9265,9260,9267,9268]},
    "BTCUSD": {"trinity":8866,"kraken":8852,"sound":8870,"quantum":8854,"executor":8856,
               "llm":[8855,8857,8858,8859,8861,5004,None,None,None,None,8867,8868]},
    "USDCNH": {"trinity":8766,"kraken":8752,"sound":8770,"quantum":8754,"executor":8756,
               "llm":[8755,8757,8758,8759,8761,8762,8763,8764,8765,8760,8767,8768]},
    "USDSEK": {"trinity":8666,"kraken":8652,"sound":8670,"quantum":8654,"executor":8656,
               "llm":[8655,8657,8658,8659,8661,8662,8663,8664,8665,8660,8667,8668]},
    "US30":   {"trinity":8966,"kraken":8952,"sound":8970,"quantum":8954,"executor":8956,
               "llm":[8955,8957,8958,8959,8961,8962,8963,8964,8965,8960,8967,8968]},
}

RUNTIME_MANAGER = RuntimeManager(PATHS, PORT_MAP, FOLDER_TO_SYMBOL, PAIR_RUNTIME_HINTS)
MT5_SERVICE = MT5Service(_mt5)
TELEMETRY_SERVICE = TelemetryService(RUNTIME_MANAGER, MT5_SERVICE)
LICENSE_SERVICE = LicenseService(get_license_status if _LM_OK else None)

def _pair_runtime_status(sym: str, runtime: dict) -> bool:
    return bool(RUNTIME_MANAGER.pair_runtime_status(sym, runtime))

PAIR_RUNTIME = _discover_pair_runtime()
ALL_PARES = _build_available_pairs(PAIR_RUNTIME)

def _build_qss() -> str:
    return f"""
QLabel      {{ background:transparent; color:{C['text']}; border:none; font-family:{_font_css_family()}; }}
QScrollBar:vertical {{
    background-color: #0A0802; width:10px; border:none; border-radius:5px; margin:2px 0;
}}
QScrollBar::groove:vertical {{
    background: #0A0802; border-radius:5px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar::handle:vertical {{
    background: qlineargradient(y1:0, y2:1,
        stop:0 rgba(160,110,15,200), stop:0.35 rgba(220,160,25,220),
        stop:0.5 rgba(255,215,0,235), stop:0.65 rgba(220,160,25,220),
        stop:1 rgba(160,110,15,200));
    border: 1px solid rgba(255,215,0,70);
    border-radius:5px; min-height:30px;
}}
QScrollBar::handle:vertical:hover {{
    background: qlineargradient(y1:0, y2:1,
        stop:0 rgba(200,140,20,230), stop:0.35 rgba(245,190,40,245),
        stop:0.5 rgba(255,230,80,255), stop:0.65 rgba(245,190,40,245),
        stop:1 rgba(200,140,20,230));
    border: 1px solid rgba(255,230,80,130);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{
    background-color: #0A0802; height:10px; border:none; border-radius:5px; margin:0 2px;
}}
QScrollBar::groove:horizontal {{
    background: #0A0802; border-radius:5px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, x2:1,
        stop:0 rgba(160,110,15,200), stop:0.35 rgba(220,160,25,220),
        stop:0.5 rgba(255,215,0,235), stop:0.65 rgba(220,160,25,220),
        stop:1 rgba(160,110,15,200));
    border: 1px solid rgba(255,215,0,70);
    border-radius:5px; min-width:30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: qlineargradient(x1:0, x2:1,
        stop:0 rgba(200,140,20,230), stop:0.35 rgba(245,190,40,245),
        stop:0.5 rgba(255,230,80,255), stop:0.65 rgba(245,190,40,245),
        stop:1 rgba(200,140,20,230));
    border: 1px solid rgba(255,230,80,130);
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
QToolTip {{ background:{C['card']}; color:{C['text2']}; border:1px solid {C['accent']}60;
           padding:8px 12px; border-radius:8px; font-size:11px; font-family:{_font_css_family()}; }}
"""

LLM_NAMES = ["BAY","TEC","CHT","RSK","SUP","SMI","OCS","TMR","PRD","MSDA","GURU","SNTL"]
LLM_FULL  = {
    "BAY":  ("Bayesian",     "Análisis probabilístico bayesiano"),
    "TEC":  ("Technical",    "Indicadores técnicos RSI/ADX/MACD"),
    "CHT":  ("Chart",        "Patrones de velas y formaciones"),
    "RSK":  ("Risk Mgmt",    "Gestión de riesgo y exposición"),
    "SUP":  ("Supply/Dem",   "Soporte, resistencia y zonas S/D"),
    "SMI":  ("Smart Money",  "Detección de ballenas y barridos"),
    "OCS":  ("Quantum",      "Conciencia cuántica — integrador"),
    "TMR":  ("Timer",        "Optimizador de timing de entrada"),
    "PRD":  ("Predator",     "Cazador de liquidez e imbalances"),
    "MSDA": ("MSDA Meta",    "Meta-análisis de sentimiento"),
    "GURU": ("Mkt Guru",     "Supervisor experto del mercado"),
    "SNTL": ("Sentinel",     "Vigilante 24/7 — riesgo global"),
}
LLM_GROUPS = {
    "BAY":"VOTERS","TEC":"VOTERS","CHT":"VOTERS","RSK":"VOTERS","SUP":"VOTERS","SMI":"VOTERS",
    "OCS":"VOTERS","TMR":"VOTERS","PRD":"VOTERS",
    "MSDA":"META","GURU":"META","SNTL":"META",
}

TEXTS = {
    "ES": {
        "start":       "⚡  INICIAR QUANTUM",
        "launching":   "⚡  Iniciando",
        "waiting_ea":  "🟡  Esperando Inyección EA",
        "injected":    "🟢  SISTEMA INYECTADO",
        "stop":        "■  DETENER",
        "stopped":     "⬛  SISTEMA DETENIDO",
        "stopping":    "⏳  Deteniendo…",
        "close_profit":"💰  CERRAR LUCRATIVAS",
        "close_profit_short":"💰  CERRAR +",
        "close_profit_mini":"💰 +",
        "sub_btn":     "◇  Suscripción",
        "refresh_pairs":"↻  REFRESCAR PARES",
        "refresh_pairs_short":"↻  REFRESCAR",
        "hint":        "Selecciona un par para abrir su dashboard",
        "sessions":    "SESIONES",
        "pairs_active": "✦ {count} pares activos ✦",
        "days_remaining": "{days} días",
        "no_license": "Sin licencia",
        "diagnostics_collapsed": "► DIAGNÓSTICOS",
        "diagnostics_expanded": "▼ DIAGNÓSTICOS",
        "layout": "LAYOUT",
        "tile_h": "▤ Tile H",
        "tile_v": "▥ Tile V",
        "cascade": "⧉ Cascada",
        "close_all": "✕ Cerrar",
        "license_title": "◇  Suscripción y Licencia",
        "license_client_sub": "Cliente NOVA Trading AI",
        "license_key": "Licencia",
        "license_expiry": "Expira",
        "license_days": "Días",
        "license_pairs": "Pares",
        "license_server": "Servidor",
        "license_status": "Estado",
        "license_active": "● ACTIVO",
        "license_demo": "● DEMO",
        "pairs_in_license": "PARES EN TU LICENCIA",
        "sec_market":    "MERCADO",
        "sec_indicators":"INDICADORES",
        "sec_ml":        "SISTEMAS ML",
        "sec_brain":     "IA CEREBRO — 12 MODELOS ACTIVOS",
        "sec_patterns":  "PATRONES",
        "sec_attack":    "SISTEMA DE ATAQUE",
        "sec_orderflow": "FLUJO DE ÓRDENES",
        "sec_network":   "RED",
        "sec_perf":      "RENDIMIENTO",
        "sec_sound":     "CC / SOUND",
        "connecting":  "Conectando…",
        "no_launcher": "⚠ Launcher no disponible para este par",
        "live":        "LIVE",
        "offline":     "OFFLINE",
        "offline_last": "OFFLINE • Última telemetría hace {age}s",
        "offline_none": "OFFLINE • Sin telemetría disponible",
        "legend_on":    "Online",
        "legend_wait":  "Esperando",
        "legend_off":   "Offline",
        "scanning":     "Escaneando…",
        "no_mt5":       "⚠ MetaTrader5 no disponible en este entorno",
        "no_positions": "💰 Sin posiciones abiertas en {sym}",
        "no_profit":    "💰 Ninguna posición con ganancia en {sym}",
        "closed_result":"💰 Cerradas: {closed}  |  Errores: {errors}  ({sym})",
        "symbol_not_found": "⚠ Símbolo {sym} no encontrado en MT5",
        "launch_error": "❌ Error al lanzar: {error}",
        "no_stop_routine": "⚠ No existe rutina de apagado para este par",
        "stopping_pair": "■ Deteniendo {sym}...",
        "mt5_no_tick": "⚠ Sin tick para {sym}",
        "algo_off": "◌ ALGO OFF",
        "algo_on": "◉ ALGO ON",
        "algo_enabled": "🟢 Algo Trading activado",
        "algo_disabled": "🔴 Algo Trading desactivado",
        "algo_already_on": "🟢 Algo Trading ya estaba activo",
        "algo_already_off": "🔴 Algo Trading ya estaba desactivado",
        "algo_toggle_failed": "⚠ No pude conmutar Algo Trading desde MT5. Revisa foco del terminal o usa Ctrl+E.",
        "algo_toggle_hint_on": "Click para desactivar Algo Trading en MT5",
        "algo_toggle_hint_off": "Click para activar Algo Trading en MT5",
        "ea_manual_required": "🟡 Bridge preparado para {sym}. MT5 no expone attach automático del EA; abrí el chart correcto y adjunta este archivo: {bridge}",
    },
    "EN": {
        "start":       "⚡  START QUANTUM",
        "launching":   "⚡  Starting",
        "waiting_ea":  "🟡  Waiting for EA Injection",
        "injected":    "🟢  SYSTEM INJECTED",
        "stop":        "■  STOP",
        "stopped":     "⬛  SYSTEM STOPPED",
        "stopping":    "⏳  Stopping…",
        "close_profit":"💰  CLOSE PROFITABLE",
        "close_profit_short":"💰  CLOSE +",
        "close_profit_mini":"💰 +",
        "sub_btn":     "◇  Subscription",
        "refresh_pairs":"↻  REFRESH PAIRS",
        "refresh_pairs_short":"↻  REFRESH",
        "hint":        "Select a pair to open its dashboard",
        "sessions":    "SESSIONS",
        "pairs_active": "✦ {count} active pairs ✦",
        "days_remaining": "{days} days",
        "no_license": "No license",
        "diagnostics_collapsed": "► DIAGNOSTICS",
        "diagnostics_expanded": "▼ DIAGNOSTICS",
        "layout": "LAYOUT",
        "tile_h": "▤ Tile H",
        "tile_v": "▥ Tile V",
        "cascade": "⧉ Cascade",
        "close_all": "✕ Close",
        "license_title": "◇  Subscription & License",
        "license_client_sub": "NOVA Trading AI Client",
        "license_key": "License",
        "license_expiry": "Expires",
        "license_days": "Days",
        "license_pairs": "Pairs",
        "license_server": "Server",
        "license_status": "Status",
        "license_active": "● ACTIVE",
        "license_demo": "● DEMO",
        "pairs_in_license": "PAIRS IN YOUR LICENSE",
        "sec_market":    "MARKET",
        "sec_indicators":"INDICATORS",
        "sec_ml":        "ML SYSTEMS",
        "sec_brain":     "AI BRAIN — 12 ACTIVE MODELS",
        "sec_patterns":  "PATTERNS",
        "sec_attack":    "ATTACK SYSTEM",
        "sec_orderflow": "ORDER FLOW",
        "sec_network":   "NETWORK",
        "sec_perf":      "PERFORMANCE",
        "sec_sound":     "CC / SOUND",
        "connecting":  "Connecting…",
        "no_launcher": "⚠ No launcher available for this pair",
        "live":        "LIVE",
        "offline":     "OFFLINE",
        "offline_last": "OFFLINE • Last telemetry {age}s ago",
        "offline_none": "OFFLINE • No telemetry available",
        "legend_on":    "Online",
        "legend_wait":  "Waiting",
        "legend_off":   "Offline",
        "scanning":     "Scanning…",
        "no_mt5":       "⚠ MetaTrader5 not available",
        "no_positions": "💰 No open positions on {sym}",
        "no_profit":    "💰 No profitable positions on {sym}",
        "closed_result":"💰 Closed: {closed}  |  Errors: {errors}  ({sym})",
        "symbol_not_found": "⚠ Symbol {sym} not found in MT5",
        "launch_error": "❌ Launch error: {error}",
        "no_stop_routine": "⚠ No shutdown routine available for this pair",
        "stopping_pair": "■ Stopping {sym}...",
        "mt5_no_tick": "⚠ No tick for {sym}",
        "algo_off": "◌ ALGO OFF",
        "algo_on": "◉ ALGO ON",
        "algo_enabled": "🟢 Algo Trading enabled",
        "algo_disabled": "🔴 Algo Trading disabled",
        "algo_already_on": "🟢 Algo Trading already enabled",
        "algo_already_off": "🔴 Algo Trading already disabled",
        "algo_toggle_failed": "⚠ I could not toggle Algo Trading from MT5. Check terminal focus or use Ctrl+E.",
        "algo_toggle_hint_on": "Click to disable Algo Trading in MT5",
        "algo_toggle_hint_off": "Click to enable Algo Trading in MT5",
        "ea_manual_required": "🟡 Bridge prepared for {sym}. MT5 does not expose automatic EA attach; open the correct chart and attach this file: {bridge}",
    },
}

# ═══════════════════════════════════════════════════════════════════════
#  BACKGROUND CANVAS — idéntico al keygen v8 GOLDEN
# ═══════════════════════════════════════════════════════════════════════
class BackgroundCanvas(QWidget):
    def __init__(self, parent=None, draw_particles=True, draw_vignette=True):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._draw_particles = draw_particles
        self._draw_vignette = draw_vignette
        self._vignette_cache = None
        self._vignette_size = QSize()
        self.particles = []
        for _ in range(80):
            self.particles.append({
                "x": random.uniform(0,1), "y": random.uniform(0,1),
                "vx": random.uniform(-0.0003,0.0003),
                "vy": random.uniform(-0.0003,0.0003),
                "r": random.uniform(1.2,3.2),
                "alpha": random.uniform(0.45,0.95),
                "pulse": random.uniform(0,math.pi*2),
                "pulse_speed": random.uniform(0.02,0.05),
            })
        t = QTimer(self); t.timeout.connect(self._tick); t.start(33)
    def _tick(self):
        for p in self.particles:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["pulse"]+=p["pulse_speed"]
            if p["x"]<0: p["x"]=1.0
            if p["x"]>1: p["x"]=0.0
            if p["y"]<0: p["y"]=1.0
            if p["y"]>1: p["y"]=0.0
        self.update()
    def paintEvent(self, _):
        if not self.isVisible(): return
        qp = QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        if self._draw_particles:
            pen = QPen()
            max_dist = 120.0
            max_dist2 = max_dist * max_dist
            for i, p1 in enumerate(self.particles):
                x1 = p1["x"] * w; y1 = p1["y"] * h
                for p2 in self.particles[i+1:]:
                    dx = x1 - (p2["x"] * w)
                    dy = y1 - (p2["y"] * h)
                    d2 = dx*dx + dy*dy
                    if d2 < max_dist2:
                        d = math.sqrt(d2)
                        a=int((1-d/max_dist)*55)
                        pen.setColor(QColor(255,190,50,a)); pen.setWidthF(0.6)
                        qp.setPen(pen)
                        qp.drawLine(int(x1), int(y1), int(p2["x"]*w), int(p2["y"]*h))
            for p in self.particles:
                a=p["alpha"]*(0.65+0.35*math.sin(p["pulse"]))
                px,py,r = p["x"]*w, p["y"]*h, p["r"]
                qp.setPen(Qt.NoPen)
                qp.setBrush(QBrush(QColor(255,190,50,int(a*40))))
                qp.drawEllipse(QRectF(px-r*3,py-r*3,r*6,r*6))
                qp.setBrush(QBrush(QColor(255,215,80,int(a*240))))
                qp.drawEllipse(QRectF(px-r,py-r,r*2,r*2))
        if self._draw_vignette:
            size = self.size()
            if self._vignette_cache is None or self._vignette_size != size:
                pm = QPixmap(size)
                pm.fill(Qt.transparent)
                vqp = QPainter(pm)
                vqp.setRenderHint(QPainter.Antialiasing)
                vg = QRadialGradient(w/2,h/2,max(w,h)*0.68)
                vg.setColorAt(0,QColor(0,0,0,0)); vg.setColorAt(0.55,QColor(0,0,0,0)); vg.setColorAt(1,QColor(0,0,0,130))
                vqp.fillRect(QRectF(0, 0, w, h), QBrush(vg))
                vqp.end()
                self._vignette_cache = pm
                self._vignette_size = QSize(size)
            qp.drawPixmap(0, 0, self._vignette_cache)
        qp.end()


class RuntimeActivityWorker(QThread):
    live_ready = Signal(list)

    def __init__(self, interval_ms: int = 5000, parent=None):
        super().__init__(parent)
        self._interval_ms = max(1000, int(interval_ms))
        self._active = True
        self._pairs: list[dict] = []
        self._runtime_map: dict = {}
        self._lock = threading.Lock()
        self._last_live: tuple[str, ...] = tuple()

    def set_inputs(self, pairs: list[dict], runtime_map: dict):
        with self._lock:
            self._pairs = [dict(p) for p in pairs]
            self._runtime_map = dict(runtime_map)

    def stop(self):
        self._active = False
        self.wait(3000)

    def run(self):
        while self._active:
            with self._lock:
                pairs = list(self._pairs)
                runtime_map = dict(self._runtime_map)
            live_tuple = tuple(RUNTIME_MANAGER.live_symbols(pairs, runtime_map))
            if live_tuple != self._last_live:
                self._last_live = live_tuple
                self.live_ready.emit(list(live_tuple))
            for _ in range(max(1, self._interval_ms // 100)):
                if not self._active:
                    return
                self.msleep(100)

# ═══════════════════════════════════════════════════════════════════════
#  TITLE BAR — idéntica al keygen
# ═══════════════════════════════════════════════════════════════════════
class TitleBar(QWidget):
    lang_toggled = Signal(str)
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self._win = win
        self._drag_pos = None
        self._hover_btn = -1  # -1=none, 0=min, 1=max, 2=close, 3=lang
        self._lang = "EN"
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setMouseTracking(True)
    def set_lang(self, lang: str):
        self._lang = lang
        self.update()
    def _btn_rect(self, i):
        bw=52; return QRectF(self.width()-bw*(3-i), 0, bw, self.height())
    def _lang_rect(self):
        h=self.height(); pw=52
        return QRectF(self.width()-pw*3-58, (h-22)//2, 48, 22)
    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons()==Qt.LeftButton:
            self._win.move(e.globalPosition().toPoint()-self._drag_pos); return
        old=self._hover_btn; self._hover_btn=-1
        if self._lang_rect().contains(e.position()):
            self._hover_btn=3
        else:
            for i in range(3):
                if self._btn_rect(i).contains(e.position()):
                    self._hover_btn=i; break
        if old!=self._hover_btn: self.update()
    def leaveEvent(self,_):
        if self._hover_btn>=0: self._hover_btn=-1; self.update()
    def mouseReleaseEvent(self,_): self._drag_pos=None
    def paintEvent(self, _):
        qp = QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        qp.fillRect(self.rect(), QColor(C["bg"]))
        # NOVA logo
        fn = _ui_font(14, QFont.Black)
        qp.setFont(fn); fm=qp.fontMetrics()
        nw=fm.horizontalAdvance("N"); ow=fm.horizontalAdvance("OVA")
        x0=20
        qp.setPen(QPen(QColor("#FFFFFF"))); qp.drawText(x0,0,nw+2,h,Qt.AlignVCenter,"N")
        gova=QLinearGradient(x0+nw,0,x0+nw+ow,0)
        gova.setColorAt(0,QColor("#E06010")); gova.setColorAt(0.5,QColor("#F5A623")); gova.setColorAt(1,QColor("#FFD700"))
        qp.setPen(QPen(QBrush(gova),0)); qp.drawText(x0+nw,0,ow+2,h,Qt.AlignVCenter,"OVA")
        f2=_ui_font(7); f2.setLetterSpacing(QFont.AbsoluteSpacing,3)
        qp.setFont(f2); qp.setPen(QPen(QColor(C["dim"])))
        qp.drawText(x0+nw+ow+12,0,130,h,Qt.AlignVCenter,"TRADING AI")
        # Version
        qp.setFont(_ui_font(8)); qp.setPen(QPen(QColor(C["dim"])))
        qp.drawText(0,0,w-230,h,Qt.AlignVCenter|Qt.AlignRight,"v5.0.0")
        # EN/ES language pill
        lr = self._lang_rect()
        hov_lang = self._hover_btn == 3
        pill = QPainterPath(); pill.addRoundedRect(lr, 5, 5)
        if hov_lang:
            qp.fillPath(pill, QBrush(QColor(70,55,10,220)))
        else:
            qp.fillPath(pill, QBrush(QColor(28,22,4,180)))
        rim_g = QLinearGradient(lr.x(),0,lr.right(),0)
        rim_g.setColorAt(0, QColor(245,166,35,160)); rim_g.setColorAt(0.5, QColor(255,215,0,210)); rim_g.setColorAt(1, QColor(245,166,35,160))
        qp.strokePath(pill, QPen(QBrush(rim_g), 1.0))
        qp.setPen(QPen(QColor(C["gold"]) if not hov_lang else QColor("#FFFFFF")))
        qp.setFont(_ui_font(8, QFont.Bold))
        qp.drawText(lr, Qt.AlignCenter, self._lang)
        # Buttons ─ □ ✕ — with hover highlight
        for i,(sym,hbg) in enumerate([("─","#2A2200"),("□","#2A2200"),("✕","#CC2222")]):
            br=self._btn_rect(i)
            if self._hover_btn==i:
                qp.fillRect(br,QColor(hbg))
                qp.setPen(QPen(QColor("#FFFFFF"))); qp.setFont(_ui_font(11))
            else:
                qp.setPen(QPen(QColor(C["dim2"]))); qp.setFont(_ui_font(11))
            qp.drawText(br,Qt.AlignCenter,sym)
        # Bottom glow line
        g=QLinearGradient(0,h-1,w,h-1)
        g.setColorAt(0,QColor(0,0,0,0)); g.setColorAt(0.2,QColor(245,166,35,50))
        g.setColorAt(0.5,QColor(255,215,0,100)); g.setColorAt(0.8,QColor(245,166,35,50))
        g.setColorAt(1,QColor(0,0,0,0))
        qp.fillRect(0,h-2,w,2,QBrush(g))
        qp.end()
    def mouseDoubleClickEvent(self,e):
        # Suppress double-click on the lang pill (prevents resize)
        if self._lang_rect().contains(e.position()):
            return
        if self._win.isMaximized(): self._win.showNormal()
        else: self._win.showMaximized()
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            if self._lang_rect().contains(e.position()):
                self._lang = "EN" if self._lang=="ES" else "ES"
                self.lang_toggled.emit(self._lang)
                self.update()
                self._lang_click_ts = time.time()  # debounce double-click
                return
            for i in range(3):
                if self._btn_rect(i).contains(e.position()):
                    if i==0: self._win.showMinimized()
                    elif i==1: self.mouseDoubleClickEvent(e)
                    else: self._win.close()
                    return
            self._drag_pos=e.globalPosition().toPoint()-self._win.frameGeometry().topLeft()

# ═══════════════════════════════════════════════════════════════════════
#  SESSION BAR — Todas las sesiones identificadas con texto grande
# ═══════════════════════════════════════════════════════════════════════
class SessionBar(QWidget):
    # 2 lanes: Lane 0 = Sydney + London, Lane 1 = Tokyo + NY (no overlap within lanes)
    SESSIONS = [
        {"name":"SYDNEY",  "start":22,"end":7, "color":"#008FCF","lane":0},
        {"name":"TOKYO",   "start":0, "end":9, "color":"#FF1744","lane":1},
        {"name":"LONDON",  "start":8,"end":17,"color":"#00FF9C","lane":0},
        {"name":"NEW YORK","start":13,"end":22,"color":"#FFE600","lane":1},
    ]
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lang = "EN"
        self.setFixedHeight(68)
        self.setAttribute(Qt.WA_NoSystemBackground)
        t=QTimer(self); t.timeout.connect(self.update); t.start(1000)  # 1s for blinking colon
    def set_lang(self, lang: str):
        self._lang = lang
        self.update()
    def paintEvent(self, _):
        qp=QPainter(self); 
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        qp.fillRect(self.rect(),QColor(C["bg"]))
        now=datetime.now(timezone.utc); now_h=now.hour+now.minute/60.0
        bL,bR=90,130; bW=w-bL-bR
        lane_h=18; lane_gap=4; lanes_top=8
        # Label — premium gold
        qp.setPen(QColor(C["gold"])); qp.setFont(_ui_font(8, QFont.Bold))
        qp.drawText(QRectF(10,0,72,h-10),Qt.AlignVCenter,TEXTS[self._lang]["sessions"])
        # Hour ticks — brighter
        qp.setFont(_ui_font(8)); qp.setPen(QColor(C["dim2"]))
        for hr in range(0,25,3):
            x=bL+int(bW*hr/24)
            qp.drawText(QRectF(x-10,h-14,20,14),Qt.AlignCenter,f"{hr:02d}")
        # Draw sessions in 2 lanes
        for s in self.SESSIONS:
            s0,s1=s["start"],s["end"]
            active=(s0<=now_h<s1) if s0<s1 else (now_h>=s0 or now_h<s1)
            col=QColor(s["color"]); lane=s["lane"]
            y_top=lanes_top+lane*(lane_h+lane_gap)
            def draw_seg(x1,x2,show_label):
                bw=max(x2-x1,3)
                c=QColor(col)
                if active:
                    # Gradient fill for depth
                    gf=QLinearGradient(x1,y_top,x1,y_top+lane_h)
                    gf.setColorAt(0,QColor(c.red(),c.green(),c.blue(),255))
                    gf.setColorAt(0.5,QColor(c.red(),c.green(),c.blue(),200))
                    gf.setColorAt(1,QColor(c.red(),c.green(),c.blue(),240))
                    qp.setPen(Qt.NoPen); qp.setBrush(QBrush(gf))
                    qp.drawRoundedRect(int(x1),y_top,int(bw),lane_h,4,4)
                    # Glow border
                    bp=QPainterPath(); bp.addRoundedRect(QRectF(x1,y_top,bw,lane_h),4,4)
                    qp.strokePath(bp,QPen(QColor(c.red(),c.green(),c.blue(),120),1))
                else:
                    c.setAlpha(55)
                    qp.setPen(Qt.NoPen); qp.setBrush(c)
                    qp.drawRoundedRect(int(x1),y_top,int(bw),lane_h,4,4)
                if show_label and bw>30:
                    dark_bg=s["color"] in ["#FFD740","#60E890"]
                    if active:
                        qp.setPen(QColor("#0A0A00") if dark_bg else QColor("#FFFFFF"))
                        qp.setFont(_ui_font(9, QFont.Bold))
                    else:
                        tc=QColor(col); tc.setAlpha(200)
                        qp.setPen(tc); qp.setFont(_ui_font(8))
                    qp.drawText(QRectF(x1,y_top,bw,lane_h),Qt.AlignCenter,s["name"])
            if s0<s1:
                draw_seg(bL+int(bW*s0/24),bL+int(bW*s1/24),True)
            else:
                xa=bL+int(bW*s0/24); xb=bL+int(bW*s1/24)
                wa2=bL+bW-xa; wb2=xb-bL
                draw_seg(xa,bL+bW,wa2>=wb2)
                draw_seg(bL,xb,wb2>wa2)
        # Now marker — spans both lanes
        nx=bL+int(bW*now_h/24)
        qp.setPen(QPen(QColor(C["accent"]),2.5)); qp.drawLine(int(nx),2,int(nx),h-14)
        qp.setPen(Qt.NoPen); qp.setBrush(QColor(C["accent"]))
        qp.drawEllipse(QPointF(nx,3),3.5,3.5)
        # UTC — centered in right zone, futuristic font
        utc_h=now.strftime("%H"); utc_m=now.strftime("%M")
        colon=":" if now.second%2==0 else " "
        clk_x = w - bR; clk_w = bR
        # Time digits — large display font
        qp.setPen(QColor(C["gold"]))
        qp.setFont(_ui_font(16, QFont.Bold))
        qp.drawText(QRectF(clk_x, 0, clk_w, h-10), Qt.AlignVCenter|Qt.AlignHCenter, f"{utc_h}{colon}{utc_m}")
        # UTC label — small below
        qp.setFont(_ui_font(7))
        qp.setPen(QColor(C["dim2"]))
        qp.drawText(QRectF(clk_x, 0, clk_w, h+10), Qt.AlignVCenter|Qt.AlignHCenter, "\n\nUTC")
        # Bottom glow
        g=QLinearGradient(0,h-1,w,h-1)
        g.setColorAt(0,QColor(C["border"])); g.setColorAt(0.3,QColor(245,166,35,25))
        g.setColorAt(0.7,QColor(245,166,35,25)); g.setColorAt(1,QColor(C["border"]))
        qp.setPen(QPen(QBrush(g),1)); qp.drawLine(0,h-1,w,h-1)
        qp.end()

# ═══════════════════════════════════════════════════════════════════════
#  PREMIUM BUTTON — idéntico al keygen (QPainter puro)
# ═══════════════════════════════════════════════════════════════════════
class PremiumButton(QWidget):
    clicked=Signal()
    def __init__(self, text, mode="primary", parent=None):
        super().__init__(parent)
        self._text=text; self.mode=mode; self._hov=self._press=False
        self.setFixedHeight(34); self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        self._scale_val=1.0
        self._anim=QPropertyAnimation(self, b"_zoom")
        self._anim.setDuration(150); self._anim.setEasingCurve(QEasingCurve.OutCubic)
        # ─── Shimmer-sweep state (for "INYECTADO" running mode) ───
        self._running   = False
        self._stopping  = False
        self._waiting_ea = False
        self._lang_texts = {}
        self._shimmer_x = 0.0          # 0.0 → 1.0 across width
        self._shimmer_phase = 0        # 0=sweeping, 1=pause
        self._shimmer_pause = 0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)
        # ─── Stop flash timer ───
        self._stop_timer = QTimer(self); self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self._stop_flash_done)
        self._stopped = False   # persistent "DETENIDO" state
        # ─── Launching animation ───
        self._launching  = False
        self._launch_dot = 0        # cycles 0→1→2 → dots "."".."→"..."
        self._launch_pulse = 0      # brightness pulse counter
        self._launch_timer = QTimer(self)
        self._launch_timer.setInterval(380)
        self._launch_timer.timeout.connect(self._tick_launch)
        self._orig_text = text

    def _get_zoom(self): return self._scale_val
    def _set_zoom(self, v): self._scale_val=v; self.update()
    _zoom=Property(float, _get_zoom, _set_zoom)

    def setText(self, t): self._text=t; self.update()

    def set_lang_texts(self, texts: dict):
        """Receive lang dict so button labels update on toggle."""
        self._lang_texts = texts

    def set_launching(self):
        """Phase 1: 'Iniciando...' animation while bot warms up."""
        if self._launching or self._running: return
        self._launching = True; self._waiting_ea = False
        self._launch_dot = 0; self._launch_pulse = 0
        self._launch_timer.start()
        base = self._lang_texts.get("launching", "⚡  Iniciando") if hasattr(self, '_lang_texts') else "⚡  Iniciando"
        self._text = f"{base}."
        self.update()

    def set_waiting_ea(self):
        """Phase 2: 'Esperando Inyección EA' — system started but no EA yet."""
        self._launching = False; self._launch_timer.stop()
        self._waiting_ea = True; self._running = False
        self._shimmer_timer.stop()
        self._shimmer_x = 0.0; self._shimmer_phase = 0; self._shimmer_pause = 0
        self._shimmer_timer.start(35)  # amber pulse
        t = self._lang_texts.get("waiting_ea", "🟡  Esperando Inyección EA") if hasattr(self, '_lang_texts') else "🟡  Esperando Inyección EA"
        self._text = t
        self.update()

    def _tick_launch(self):
        self._launch_dot = (self._launch_dot + 1) % 3
        self._launch_pulse = (self._launch_pulse + 1) % 20
        dots = "." * (self._launch_dot + 1)
        base = self._lang_texts.get("launching", "⚡  Iniciando") if hasattr(self, '_lang_texts') else "⚡  Iniciando"
        self._text = f"{base}{dots}"
        self.update()

    def set_running(self, val: bool):
        """Phase 3 (val=True): 'SISTEMA INYECTADO' — EA detected."""
        if val == self._running and not self._launching and not self._waiting_ea: return
        self._launching = False; self._launch_timer.stop()
        self._waiting_ea = False
        self._running = val
        if val:
            t = self._lang_texts.get("injected", "🟢  SISTEMA INYECTADO") if hasattr(self, '_lang_texts') else "🟢  SISTEMA INYECTADO"
            self._text = t
            self._shimmer_x = 0.0; self._shimmer_phase = 0; self._shimmer_pause = 0
            self._shimmer_timer.start(35)
        else:
            self._text = self._orig_text
            self._shimmer_timer.stop()
        self.update()

    def set_stopping(self):
        """Flash 'Deteniendo…' for 2.5s on stop button."""
        if self._stopping: return
        self._stopping = True
        t = self._lang_texts.get("stopping", "⏳  Deteniendo…") if hasattr(self, '_lang_texts') else "⏳  Deteniendo…"
        self._text = t
        self._stop_timer.start(2500)
        self.update()

    def _stop_flash_done(self):
        self._stopping = False
        self._stopped = True
        t = self._lang_texts.get("stopped", "⬛  SISTEMA DETENIDO") if hasattr(self, '_lang_texts') else "⬛  SISTEMA DETENIDO"
        self._text = t
        self.update()

    def reset_to_danger(self):
        """Call when bot is detected running again so DETENER returns to red."""
        self._stopping = False
        self._stopped = False
        self._text = self._orig_text
        self._stop_timer.stop()
        self.update()

    def _tick_shimmer(self):
        if self._shimmer_phase == 0:
            self._shimmer_x += 0.035
            if self._shimmer_x >= 1.4:
                self._shimmer_phase = 1
                self._shimmer_pause = 0
        else:
            self._shimmer_pause += 1
            if self._shimmer_pause >= 55:          # ~2s pause between sweeps
                self._shimmer_x = -0.2
                self._shimmer_phase = 0
        self.update()

    def enterEvent(self,_):
        self._hov=True
        if not self._running:
            self._anim.stop(); self._anim.setStartValue(self._scale_val); self._anim.setEndValue(1.04); self._anim.start()
    def leaveEvent(self,_):
        self._hov=False; self._press=False
        self._anim.stop(); self._anim.setStartValue(self._scale_val); self._anim.setEndValue(1.0); self._anim.start()
    def mousePressEvent(self,_): self._press=True; self.update()
    def mouseReleaseEvent(self,e):
        self._press=False; self.update()
        if self.rect().contains(e.position().toPoint()): self.clicked.emit()

    def _glass(self, qp, path, w, h, tr, tg, tb, alpha=60):
        sp=QPainterPath(); sp.addRoundedRect(QRectF(1.5,1.5,w-3,h*0.48),6,6)
        sp=sp.intersected(path); sg=QLinearGradient(0,0,0,h*0.48)
        sg.setColorAt(0,QColor(255,255,255,alpha)); sg.setColorAt(1,QColor(tr,tg,tb,0))
        qp.fillPath(sp,QBrush(sg))

    def _halo(self, qp, w, h, cr, cg, cb):
        if not self._hov: return
        halo=QPainterPath(); halo.addRoundedRect(QRectF(-2,-2,w+4,h+4),9,9)
        hg=QRadialGradient(w/2,h/2,max(w,h)*0.65)
        hg.setColorAt(0,QColor(cr,cg,cb,55)); hg.setColorAt(0.5,QColor(cr,cg,cb,20)); hg.setColorAt(1,QColor(cr,cg,cb,0))
        qp.fillPath(halo,QBrush(hg))

    def paintEvent(self, _):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w=self.width(); h=self.height()
        m = max(0.0, (1.04 - self._scale_val) / 0.04 * 4.5)
        qp.translate(m, m)
        bw = w - 2*m; bh = h - 2*m
        r = QRectF(0, 0, bw, bh)
        rad = max(3.0, 7.0 - m)
        path=QPainterPath(); path.addRoundedRect(r, rad, rad)

        # ── WAITING EA mode — amber/gold pulse ──
        if getattr(self, '_waiting_ea', False) and not self._running and not self._launching:
            pulse = abs(math.sin(self._shimmer_x * math.pi * 2))
            base_a = int(190 + pulse * 50)
            fg = QLinearGradient(0, 0, bw, 0)
            fg.setColorAt(0,   QColor(180, 120, 0,  base_a))
            fg.setColorAt(0.5, QColor(240, 180, 20, base_a))
            fg.setColorAt(1,   QColor(190, 130, 0,  base_a))
            qp.fillPath(path, QBrush(fg))
            # Shimmer band
            sx = self._shimmer_x * bw
            sg = QLinearGradient(sx - 30, 0, sx + 30, 0)
            sg.setColorAt(0,   QColor(255,255,255, 0))
            sg.setColorAt(0.5, QColor(255,255,200, int(50 + pulse * 50)))
            sg.setColorAt(1,   QColor(255,255,255, 0))
            qp.fillPath(path, QBrush(sg))
            rim = QLinearGradient(0, 0, bw, bh)
            rim.setColorAt(0,   QColor(255, 200, 60,  180))
            rim.setColorAt(0.5, QColor(255, 240, 120, 240))
            rim.setColorAt(1,   QColor(255, 180, 40,  160))
            qp.strokePath(path, QPen(QBrush(rim), 1.5))
            self._glass(qp, path, bw, bh, 255, 220, 80, 45)
            qp.setPen(QPen(QColor("#1A1000")))
        # ── LAUNCHING (Iniciando...) mode — electric blue pulse ──
        elif self._launching:
            pulse = abs(math.sin(self._launch_pulse * math.pi / 10.0))
            base_a = int(190 + pulse * 45)
            fg = QLinearGradient(0, 0, bw, 0)
            fg.setColorAt(0,   QColor(0,  80,  200, base_a))
            fg.setColorAt(0.4, QColor(20, 140, 255, base_a))
            fg.setColorAt(0.7, QColor(0,  180, 240, base_a))
            fg.setColorAt(1,   QColor(0,  100, 210, base_a))
            qp.fillPath(path, QBrush(fg))
            # Sweeping scan line
            sx = (self._launch_dot / 2.0) * bw
            sg = QLinearGradient(sx - 40, 0, sx + 40, 0)
            sg.setColorAt(0,   QColor(100, 200, 255, 0))
            sg.setColorAt(0.5, QColor(180, 230, 255, int(60 + pulse * 60)))
            sg.setColorAt(1,   QColor(100, 200, 255, 0))
            qp.fillPath(path, QBrush(sg))
            rim = QLinearGradient(0, 0, bw, bh)
            rim.setColorAt(0,   QColor(80,  180, 255, 200))
            rim.setColorAt(0.5, QColor(150, 220, 255, 255))
            rim.setColorAt(1,   QColor(60,  160, 240, 180))
            qp.strokePath(path, QPen(QBrush(rim), 1.5))
            self._glass(qp, path, bw, bh, 100, 200, 255, 50)
            qp.setPen(QPen(QColor("#001830")))
        # ── RUNNING (INYECTADO) mode — emerald green + shimmer ──
        elif self._running:
            a = 235 if self._press else (230 if self._hov else 215)
            fg = QLinearGradient(0, 0, bw, 0)
            fg.setColorAt(0,  QColor(0,  140, 60,  a))
            fg.setColorAt(0.5,QColor(20, 200, 90,  a))
            fg.setColorAt(1,  QColor(0,  160, 70,  a))
            qp.fillPath(path, QBrush(fg))
            # Shimmer band
            sx = self._shimmer_x * bw
            sg = QLinearGradient(sx - 30, 0, sx + 30, 0)
            sg.setColorAt(0,   QColor(255,255,255, 0))
            sg.setColorAt(0.4, QColor(255,255,255, 55))
            sg.setColorAt(0.5, QColor(255,255,255, 90))
            sg.setColorAt(0.6, QColor(255,255,255, 55))
            sg.setColorAt(1,   QColor(255,255,255, 0))
            qp.fillPath(path, QBrush(sg))
            rim = QLinearGradient(0,0,bw,bh)
            rim.setColorAt(0,  QColor(80,255,140,200)); rim.setColorAt(0.5,QColor(150,255,180,255)); rim.setColorAt(1,QColor(60,220,110,180))
            qp.strokePath(path, QPen(QBrush(rim), 1.5))
            self._glass(qp, path, bw, bh, 100, 255, 150, 55)
            if self._hov: self._halo(qp, bw, bh, 30, 230, 100)
            qp.setPen(QPen(QColor("#002810")))
        # ── STOPPED (DETENIDO) mode — persistent grey ──
        elif self._stopped:
            fg = QLinearGradient(0, 0, 0, bh)
            fg.setColorAt(0,   QColor(38, 38, 38, 220))
            fg.setColorAt(0.5, QColor(55, 55, 55, 220))
            fg.setColorAt(1,   QColor(38, 38, 38, 220))
            qp.fillPath(path, QBrush(fg))
            rim = QLinearGradient(0, 0, bw, bh)
            rim.setColorAt(0, QColor(110, 110, 110, 120))
            rim.setColorAt(1, QColor(80,  80,  80,  90))
            qp.strokePath(path, QPen(QBrush(rim), 1.0))
            qp.setPen(QPen(QColor("#666666")))
        # ── STOPPING mode ──
        elif self._stopping:
            fg = QLinearGradient(0, 0, bw, 0)
            fg.setColorAt(0, QColor(180,80,0,220)); fg.setColorAt(1, QColor(220,130,0,220))
            qp.fillPath(path, QBrush(fg))
            rim = QLinearGradient(0,0,bw,bh)
            rim.setColorAt(0,QColor(255,160,60,200)); rim.setColorAt(1,QColor(255,220,100,200))
            qp.strokePath(path, QPen(QBrush(rim), 1.3))
            qp.setPen(QPen(QColor("#1A0800")))
        # ── DANGER (DETENER) mode ──
        elif self.mode=="danger":
            a=235 if self._press else (225 if self._hov else 205)
            fg=QLinearGradient(0,0,0,bh)
            fg.setColorAt(0,QColor(160,20,20,a)); fg.setColorAt(0.5,QColor(220,45,45,a)); fg.setColorAt(1,QColor(170,25,25,a))
            qp.fillPath(path,QBrush(fg))
            rim=QLinearGradient(0,0,bw,bh)
            rim.setColorAt(0,QColor(255,90,90,200)); rim.setColorAt(0.5,QColor(255,140,140,255)); rim.setColorAt(1,QColor(220,60,60,170))
            qp.strokePath(path,QPen(QBrush(rim),1.3))
            self._glass(qp,path,bw,bh,255,100,100,55)
            self._halo(qp,bw,bh,255,70,70)
            qp.setPen(QPen(QColor("#FFFFFF")))
        elif self.mode=="secondary":
            fg=QLinearGradient(0,0,0,bh)
            if self._press:
                fg.setColorAt(0,QColor(80,60,10,230)); fg.setColorAt(0.5,QColor(120,90,15,230)); fg.setColorAt(1,QColor(85,65,10,230))
            elif self._hov:
                fg.setColorAt(0,QColor(110,80,12,225)); fg.setColorAt(0.5,QColor(160,120,20,225)); fg.setColorAt(1,QColor(115,85,12,225))
            else:
                fg.setColorAt(0,QColor(50,38,5,210)); fg.setColorAt(0.5,QColor(75,55,8,210)); fg.setColorAt(1,QColor(52,40,5,210))
            qp.fillPath(path,QBrush(fg))
            rim=QLinearGradient(0,0,bw,bh)
            rim.setColorAt(0,QColor(255,184,40,180)); rim.setColorAt(0.5,QColor(255,220,80,240)); rim.setColorAt(1,QColor(255,170,30,160))
            qp.strokePath(path,QPen(QBrush(rim),1.3))
            self._glass(qp,path,bw,bh,255,215,60,40)
            self._halo(qp,bw,bh,255,200,50)
            qp.setPen(QPen(QColor(C["gold"])))
        else:
            if self._press:
                fg=QLinearGradient(0,0,bw,0)
                fg.setColorAt(0,QColor(200,100,0,220)); fg.setColorAt(1,QColor(180,130,0,220))
            elif self._hov:
                fg=QLinearGradient(0,0,bw,0)
                fg.setColorAt(0,QColor(240,120,0,235)); fg.setColorAt(0.5,QColor(255,190,20,235)); fg.setColorAt(1,QColor(255,215,0,235))
            else:
                fg=QLinearGradient(0,0,bw,0)
                fg.setColorAt(0,QColor(220,100,0,215)); fg.setColorAt(0.35,QColor(255,155,15,215))
                fg.setColorAt(0.7,QColor(255,200,0,215)); fg.setColorAt(1,QColor(245,175,10,215))
            qp.fillPath(path,QBrush(fg))
            rim=QLinearGradient(0,0,bw,bh)
            rim.setColorAt(0,QColor(255,180,40,230)); rim.setColorAt(0.5,QColor(255,225,70,255)); rim.setColorAt(1,QColor(255,160,20,180))
            qp.strokePath(path,QPen(QBrush(rim),1.5))
            self._glass(qp,path,bw,bh,255,220,80,65)
            self._halo(qp,bw,bh,255,200,50)
            qp.setPen(QPen(QColor("#1A0800")))
        f=_ui_font(9,QFont.Bold); f.setLetterSpacing(QFont.AbsoluteSpacing,1)
        qp.setFont(f); qp.drawText(r,Qt.AlignCenter,self._text)
        qp.end()

# ═══════════════════════════════════════════════════════════════════════
#  TELEMETRY WORKER — Background I/O thread for a single pair
# ═══════════════════════════════════════════════════════════════════════
class TelemetryWorker(QThread):
    """Collects quantum_stats, memoria, PID status and TCP health off-thread."""
    data_ready = Signal(dict)

    def __init__(self, sym: str, runtime: dict, parent=None):
        super().__init__(parent)
        self._sym = sym
        self._rt = runtime
        self._active = True

    def stop(self):
        self._active = False
        self.wait(4000)

    def run(self):
        while self._active:
            try:
                self.data_ready.emit(self._collect())
            except Exception:
                pass
            # 2 s in small increments so stop() responds quickly
            for _ in range(20):
                if not self._active:
                    return
                self.msleep(100)

    # ── data collection ──────────────────────────────────────────────
    def _collect(self) -> dict:
        return TELEMETRY_SERVICE.collect_snapshot(self._sym, self._rt)

# ═══════════════════════════════════════════════════════════════════════
#  MINI SPARKLINE — live price history (pure QPainter)
# ═══════════════════════════════════════════════════════════════════════
class MiniChartWidget(QWidget):
    def __init__(self, color="#FFB829", parent=None):
        super().__init__(parent)
        self._col = color; self._data: list[float] = []
        self.setFixedHeight(82); self.setAttribute(Qt.WA_NoSystemBackground)

    def add_price(self, p: float):
        if p <= 0: return
        self._data.append(p)
        if len(self._data) > 130: self._data = self._data[-130:]
        self.update()

    def paintEvent(self, _):
        qp = QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # card bg
        path = QPainterPath(); path.addRoundedRect(QRectF(0, 0, w, h), 4, 4)
        qp.fillPath(path, QBrush(QColor(C["card"])))
        if len(self._data) < 3:
            qp.setFont(_ui_font(8)); qp.setPen(QColor(C["dim"]))
            qp.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "Connecting to price feed…")
            qp.end(); return
        mn = min(self._data); mx = max(self._data); rng = mx - mn or 1e-9
        PAD = 10
        pts = [QPointF(PAD + (w - 2*PAD) * i / (len(self._data)-1),
                       (h-PAD) - (v-mn)/rng*(h-2*PAD))
               for i, v in enumerate(self._data)]
        up = self._data[-1] >= self._data[0]
        line_col = QColor(C["buy"] if up else C["sell"])
        # gradient fill under line
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(line_col.red(), line_col.green(), line_col.blue(), 55))
        grad.setColorAt(1, QColor(line_col.red(), line_col.green(), line_col.blue(), 0))
        fill = QPainterPath(); fill.moveTo(pts[0].x(), h)
        for p in pts: fill.lineTo(p)
        fill.lineTo(pts[-1].x(), h); fill.closeSubpath()
        qp.setPen(Qt.NoPen); qp.fillPath(fill, QBrush(grad))
        # price line
        lpath = QPainterPath(); lpath.moveTo(pts[0])
        for p in pts[1:]: lpath.lineTo(p)
        qp.setPen(QPen(line_col, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        qp.drawPath(lpath)
        # end dot
        lx, ly = pts[-1].x(), pts[-1].y()
        qp.setPen(Qt.NoPen); qp.setBrush(line_col)
        qp.drawEllipse(QRectF(lx-4, ly-4, 8, 8))
        # high/low labels
        qp.setFont(_ui_font(7)); qp.setPen(QColor(C["dim"]))
        qp.drawText(QRectF(PAD, 2, 80, 12), Qt.AlignLeft, f"H {mx:.5f}")
        qp.drawText(QRectF(PAD, h-12, 80, 12), Qt.AlignLeft, f"L {mn:.5f}")
        # last price label (right)
        qp.setPen(QColor(C["text"])); qp.setFont(_ui_font(9, QFont.Bold))
        qp.drawText(QRectF(w-90, 2, 86, 14), Qt.AlignRight, f"{self._data[-1]:.5f}")
        qp.end()


# ═══════════════════════════════════════════════════════════════════════
#  ATTACK GAUGE — circular arc QPainter widget
# ═══════════════════════════════════════════════════════════════════════
class AttackGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._prob = 0.0; self._dir = "NONE"
        self.setFixedSize(104, 86); self.setAttribute(Qt.WA_NoSystemBackground)

    def set_value(self, prob: float, direction: str = "NONE"):
        self._prob = max(0.0, min(100.0, float(prob or 0)))
        self._dir = str(direction or "NONE").upper()[:4]
        self.update()

    def paintEvent(self, _):
        qp = QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 4
        r = min(w, h) * 0.42
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        START = 225 * 16; SPAN = 270 * 16  # 270° arc
        # Background track
        qp.setPen(QPen(QColor(C["border2"]), 8, Qt.SolidLine, Qt.RoundCap))
        qp.drawArc(rect, START, -SPAN)
        # Filled arc
        if self._prob > 0:
            col = QColor(C["buy"] if self._prob >= 80 else
                         C["success"] if self._prob >= 60 else
                         C["warn"] if self._prob >= 40 else C["dim"])
            fill_span = int(self._prob / 100.0 * SPAN)
            qp.setPen(QPen(col, 8, Qt.SolidLine, Qt.RoundCap))
            qp.drawArc(rect, START, -fill_span)
            # outer glow
            glow_pen = QPen(QColor(col.red(), col.green(), col.blue(), 40), 14, Qt.SolidLine, Qt.RoundCap)
            qp.setPen(glow_pen)
            qp.drawArc(rect, START, -fill_span)
        # Centre percentage
        pct_col = (C["buy"] if self._prob >= 80 else C["success"] if self._prob >= 60
                   else C["warn"] if self._prob >= 40 else C["dim"])
        qp.setPen(QColor(pct_col))
        qp.setFont(_ui_font(15, QFont.Black))
        qp.drawText(QRectF(cx-r, cy-18, r*2, 22), Qt.AlignCenter, f"{int(self._prob)}")
        qp.setFont(_ui_font(7))
        qp.setPen(QColor(C["dim2"]))
        qp.drawText(QRectF(cx-r, cy+5, r*2, 12), Qt.AlignCenter, f"DIR {self._dir}")
        qp.end()


class RoiGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._roi = 0.0
        self._winrate = "—"
        self._trades = "0"
        self.setFixedSize(122, 98)
        self.setAttribute(Qt.WA_NoSystemBackground)

    def set_metrics(self, roi_pct: float, winrate_text: str, trades_text: str):
        self._roi = float(roi_pct or 0.0)
        self._winrate = str(winrate_text or "—")
        self._trades = str(trades_text or "0")
        self.update()

    def _color(self) -> QColor:
        if self._roi < -0.75:
            return QColor(C["error"])
        if self._roi < 0:
            return QColor(C["warn"])
        if self._roi < 1.0:
            return QColor(C["buy"])
        return QColor(C["violet"])

    def paintEvent(self, _):
        qp = QPainter(self)
        if not qp.isActive():
            return
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 4
        r = min(w, h) * 0.38
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        start = 225 * 16
        span = 270 * 16
        qp.setPen(QPen(QColor(C["border2"]), 9, Qt.SolidLine, Qt.RoundCap))
        qp.drawArc(rect, start, -span)
        color = self._color()
        roi_clamped = max(-2.0, min(2.0, self._roi))
        ratio = (roi_clamped + 2.0) / 4.0
        fill = int(span * ratio)
        qp.setPen(QPen(color, 9, Qt.SolidLine, Qt.RoundCap))
        qp.drawArc(rect, start, -fill)
        qp.setPen(QColor(color))
        qp.setFont(_ui_font(13, QFont.Black))
        qp.drawText(QRectF(cx - r, cy - 16, r * 2, 20), Qt.AlignCenter, f"{self._roi:+.2f}%")
        qp.setPen(QColor(C["dim2"]))
        qp.setFont(_ui_font(7, QFont.Bold))
        qp.drawText(QRectF(cx - r, cy + 4, r * 2, 12), Qt.AlignCenter, f"WR {self._winrate}")
        qp.drawText(QRectF(cx - r, cy + 16, r * 2, 12), Qt.AlignCenter, f"TRD {self._trades}")
        qp.end()


class RoiBandBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._roi = 0.0
        self._band = "Flat"
        self._color_key = "dim"
        self.setFixedHeight(24)
        self.setAttribute(Qt.WA_NoSystemBackground)

    def set_metrics(self, roi_pct: float, band_text: str, color_key: str):
        self._roi = float(roi_pct or 0.0)
        self._band = str(band_text or "Flat")
        self._color_key = str(color_key or "dim")
        self.update()

    def paintEvent(self, _):
        qp = QPainter(self)
        if not qp.isActive():
            return
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rect = QRectF(0, 2, w, h - 4)
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        qp.fillPath(path, QColor(C["card2"]))
        mid = rect.center().x()
        qp.setPen(QPen(QColor(C["border2"]), 1))
        qp.drawLine(int(mid), int(rect.top()), int(mid), int(rect.bottom()))

        color = QColor(C.get(self._color_key, C["dim"]))
        roi_clamped = max(-2.0, min(2.0, self._roi))
        ratio = abs(roi_clamped) / 2.0
        if roi_clamped >= 0:
            fill_rect = QRectF(mid, rect.top(), (rect.width() / 2.0) * ratio, rect.height())
        else:
            fill_rect = QRectF(mid - (rect.width() / 2.0) * ratio, rect.top(), (rect.width() / 2.0) * ratio, rect.height())
        fill_path = QPainterPath()
        fill_path.addRoundedRect(fill_rect, 8, 8)
        grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
        grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 90))
        grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 230))
        qp.fillPath(fill_path, grad)
        qp.setPen(QColor(C["text2"]))
        qp.setFont(_ui_font(8, QFont.Bold))
        qp.drawText(rect, Qt.AlignCenter, f"ROI BAND // {self._band.upper()} // {self._roi:+.2f}%")
        qp.end()


# ═══════════════════════════════════════════════════════════════════════
#  PAR DASHBOARD — Dashboard completo de un par (custom sub-window)
# ═══════════════════════════════════════════════════════════════════════
class ParDashboard(QWidget):
    close_requested=Signal(str)
    _EDGE = 6  # resize handle width in pixels
    _MIN_W = 300; _MIN_H = 250  # minimum panel size

    def __init__(self, par, parent=None):
        super().__init__(parent)
        self._par=par; self._color=par["color"]
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._drag_pos=None; self._data={}; self._hover_x=False; self._hover_min=False; self._hover_max=False
        self._maximized=False; self._restore_geom=None
        self._runtime=PAIR_RUNTIME.get(self._par["sym"], {})
        self.setMouseTracking(True)
        self.setMinimumSize(self._MIN_W, self._MIN_H)
        # ── resize state ──
        self._resize_edge = None   # None or "l","r","t","b","tl","tr","bl","br"
        self._resize_origin = None
        self._resize_geom = None
        self._minimized = False
        self._restore_h = 720
        self._lang = "EN"
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        # Custom title bar
        self._titlebar=QWidget(); self._titlebar.setFixedHeight(28)
        self._titlebar.setMouseTracking(True)
        self._titlebar.mouseMoveEvent = self.mouseMoveEvent
        self._titlebar.leaveEvent = self.leaveEvent
        lay.addWidget(self._titlebar)
        # Scrollable body
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                             "QScrollBar:vertical{width:4px;background:transparent;}"
                             f"QScrollBar::handle:vertical{{background:{C['border2']};border-radius:2px;}}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        scroll.viewport().setAutoFillBackground(False)
        body=QWidget(); body.setAttribute(Qt.WA_NoSystemBackground)
        body.setStyleSheet("background:transparent;")
        body.setMinimumWidth(0)  # allow shrink to viewport width — prevents horizontal overflow
        self._body=QVBoxLayout(body); self._body.setContentsMargins(8,8,8,8); self._body.setSpacing(4)
        self._build_body()
        scroll.setWidget(body)
        self._scroll = scroll  # keep ref for minimize/responsive
        lay.addWidget(scroll,1)
        # Start button
        btn_row=QHBoxLayout(); btn_row.setContentsMargins(10,4,10,8); btn_row.setSpacing(6)
        self._btn_start=PremiumButton(TEXTS[self._lang]["start"])
        self._btn_start.set_lang_texts(TEXTS[self._lang])
        self._btn_start.clicked.connect(self._launch)
        self._btn_stop=PremiumButton(TEXTS[self._lang]["stop"],"danger")
        self._btn_stop.set_lang_texts(TEXTS[self._lang])
        self._btn_stop.setMinimumWidth(50); self._btn_stop.setMaximumWidth(140)
        self._btn_stop.clicked.connect(self._stop)
        self._btn_profit=PremiumButton(TEXTS[self._lang]["close_profit"],"secondary")
        self._btn_profit.set_lang_texts(TEXTS[self._lang])
        self._btn_profit.setMinimumWidth(70); self._btn_profit.setMaximumWidth(200)
        self._btn_profit.clicked.connect(self._close_profitable)
        self._btn_algo=PremiumButton(TEXTS[self._lang]["algo_off"],"secondary")
        self._btn_algo.set_lang_texts(TEXTS[self._lang])
        self._btn_algo.setMinimumWidth(78); self._btn_algo.setMaximumWidth(138)
        self._btn_algo.clicked.connect(self._toggle_algo)
        btn_row.addWidget(self._btn_start); btn_row.addWidget(self._btn_profit); btn_row.addWidget(self._btn_algo); btn_row.addWidget(self._btn_stop)
        lay.addLayout(btn_row)
        self._action_controller = DashboardActionController(
            paths=PATHS,
            runtime_manager=RUNTIME_MANAGER,
            mt5_service=MT5_SERVICE,
            logger=logger,
        )
        self._dashboard_presenter = DashboardPresenter(
            theme=C,
            font_family=_font_css_family(),
            status_label=self._sub_lbl,
            sentiment_label=self._sent_lbl,
            fields=self._f,
            llm_widgets=self._llm,
            network_labels=self._net,
            network_dots=self._net_dots,
            llm_network_dots=self._llm_net_dots,
            sections=self._dashboard_sections,
            groups=self._dashboard_groups,
            chart=self._chart,
            gauge=self._gauge,
            start_button=self._btn_start,
            profit_button=self._btn_profit,
            algo_button=self._btn_algo,
            stop_button=self._btn_stop,
        )
        # Telemetry worker (background thread — all I/O off main thread)
        self._worker = TelemetryWorker(self._par["sym"], self._runtime)
        self._worker.data_ready.connect(self._on_telemetry)
        self._worker.start()

    def _lbl(self, text, color=None, size=13, bold=False, mono=True):
        l=QLabel(text); fam=f"font-family:{_font_css_family()};"
        w="font-weight:700;" if bold else "font-weight:500;"
        l.setStyleSheet(f"color:{color or C['text2']};font-size:{size}px;{fam}{w}background:transparent;")
        l.setMinimumWidth(0)  # allow shrink so body never overflows viewport
        return l

    def _sec(self, text):
        w = QWidget(); row = QHBoxLayout(w); row.setContentsMargins(0,6,0,2); row.setSpacing(6)
        pc = QColor(self._color)
        accent = QFrame(); accent.setFixedSize(3, 14)
        accent.setStyleSheet(f"background:{self._color};border-radius:1px;")
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{C['gold']};font-size:10px;font-weight:700;letter-spacing:2px;font-family:{_font_css_family()};background:transparent;")
        row.addWidget(accent); row.addWidget(lbl); row.addStretch()
        w.setStyleSheet("background:transparent;")
        return w

    def _sep(self):
        f=QFrame(); f.setFixedHeight(1)
        f.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        f"stop:0 transparent,stop:0.1 {C['accent']}20,stop:0.5 {C['accent']}40,stop:0.9 {C['accent']}20,stop:1 transparent);")
        return f

    def _bar(self, color=None, h=5):
        pb = QProgressBar(); pb.setFixedHeight(h); pb.setTextVisible(False)
        pb.setRange(0, 100); pb.setValue(0)
        c = color or C["buy"]
        pb.setStyleSheet(
            f"QProgressBar{{background:{C['card2']};border:none;border-radius:{h//2}px;}}"
            f"QProgressBar::chunk{{background:{c};border-radius:{h//2}px;}}"
        )
        return pb

    def _badge(self, text, fg, bg_alpha=25):
        """Colored mini chip/badge label."""
        l = QLabel(text)
        col = QColor(fg); col.setAlpha(bg_alpha)
        l.setStyleSheet(
            f"color:{fg};font-size:10px;font-family:{_font_css_family()};font-weight:600;"
            f"background:rgba({col.red()},{col.green()},{col.blue()},{bg_alpha});"
            f"border:1px solid {fg}40;border-radius:3px;padding:0px 4px;"
        )
        return l

    def _build_body(self):
        builder = DashboardBodyBuilder(
            theme=C,
            llm_names=LLM_NAMES,
            llm_full=LLM_FULL,
            label_factory=self._lbl,
            section_factory=self._sec,
            separator_factory=self._sep,
            progress_factory=self._bar,
            chart_factory=MiniChartWidget,
            gauge_factory=AttackGaugeWidget,
            roi_gauge_factory=RoiGaugeWidget,
            roi_bar_factory=RoiBandBarWidget,
        )
        refs = builder.build(
            body_layout=self._body,
            texts=TEXTS[self._lang],
            accent_color=self._color,
            footer_text=f"NOVA {self._par['strategy']}  ✦  Polarice Labs  ✦  © 2026",
        )

        self._sub_lbl = refs.status_label
        self._sent_lbl = refs.sentiment_label
        self._sym_lbl = refs.symbol_label
        self._chart = refs.chart
        self._gauge = refs.gauge
        self._f = refs.fields
        self._llm = refs.llm_widgets
        self._net = refs.network_labels
        self._net_dots = refs.network_dots
        self._llm_net_dots = refs.llm_network_dots
        self._dashboard_sections = refs.sections
        self._dashboard_groups = refs.groups

    @Slot(dict)
    def _on_telemetry(self, data: dict):
        """Process pre-collected telemetry from the background worker thread."""
        t = TEXTS.get(getattr(self, '_lang', 'ES'), TEXTS['ES'])
        vm = TELEMETRY_SERVICE.build_dashboard_vm(
            data=data,
            texts=t,
            llm_names=LLM_NAMES,
            launcher_available=self._action_controller.launcher_available(self._runtime),
            button_state={
                "launching": self._btn_start._launching,
                "waiting_ea": self._btn_start._waiting_ea,
                "running": self._btn_start._running,
            },
        )
        self._dashboard_presenter.apply_dashboard_vm(vm)

    def _launch(self):
        if self._btn_start._waiting_ea:
            outcome = self._action_controller.prepare_ea_injection(
                sym=self._par["sym"],
                runtime=self._runtime,
                texts=TEXTS.get(self._lang, TEXTS["EN"]),
            )
            self._sub_lbl.setText(outcome.message)
            return
        outcome = self._action_controller.launch(
            sym=self._par["sym"],
            runtime=self._runtime,
            texts=TEXTS.get(self._lang, TEXTS["EN"]),
        )
        self._sub_lbl.setText(outcome.message)
        if outcome.start_launching:
            self._btn_start.set_launching()

    def _close_profitable(self):
        outcome = self._action_controller.close_profitable(
            sym=self._par["sym"],
            texts=TEXTS.get(getattr(self, '_lang', 'ES'), TEXTS['ES']),
        )
        self._sub_lbl.setText(outcome.message)

    def _toggle_algo(self):
        outcome = self._action_controller.toggle_algo_trading(
            texts=TEXTS.get(getattr(self, '_lang', 'ES'), TEXTS['ES']),
        )
        self._sub_lbl.setText(outcome.message)

    def _stop(self):
        self._btn_stop.set_stopping()  # visual feedback immediately
        self._btn_start.set_running(False)  # reset start button
        # Run stop in background thread so the Qt UI thread never freezes.
        # stop_pair can spend 5-15 s spawning PowerShell + kill subprocesses.
        import threading
        sym     = self._par["sym"]
        runtime = self._runtime
        texts   = TEXTS.get(self._lang, TEXTS["EN"])
        lbl     = self._sub_lbl

        def _do_stop():
            outcome = self._action_controller.stop(sym=sym, runtime=runtime, texts=texts)
            # Qt widgets must be updated from the UI thread; use a single-shot timer
            QTimer.singleShot(0, lambda: lbl.setText(outcome.message))

        threading.Thread(target=_do_stop, daemon=True).start()

    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        # Card background
        path=QPainterPath(); path.addRoundedRect(QRectF(0.5,0.5,w-1,h-1),8,8)
        qp.fillPath(path,QBrush(QColor(16,14,6,240)))
        # Border with par color accent — brighter
        pc=QColor(self._color)
        bg=QLinearGradient(0,0,w,0)
        bg.setColorAt(0,QColor(pc.red(),pc.green(),pc.blue(),100))
        bg.setColorAt(0.5,QColor(pc.red(),pc.green(),pc.blue(),50))
        bg.setColorAt(1,QColor(pc.red(),pc.green(),pc.blue(),100))
        qp.strokePath(path,QPen(QBrush(bg),1.3))
        # Title bar background
        qp.setPen(Qt.NoPen); qp.setBrush(QColor(C["bg"]))
        tp=QPainterPath(); tp.addRoundedRect(QRectF(1,1,w-2,27),7,7)
        qp.drawPath(tp)
        # Top accent line
        qp.setPen(QPen(QColor(pc.red(),pc.green(),pc.blue(),120),2))
        qp.drawLine(8,1,w-8,1)
        # Title text — leave room for 3 buttons (3×38=114px)
        qp.setPen(QColor(C["accent"])); qp.setFont(_ui_font(9,QFont.Bold))
        qp.drawText(QRectF(10,0,w-124,28),Qt.AlignVCenter,
                     f"{self._par.get('short', self._par['icon'])}  {self._par['sym']} — {self._par['strategy']}")
        bw = 38  # button width for title bar buttons
        # ── Minimize button ── (leftmost of 3)
        mr = QRectF(w - bw*3, 0, bw, 28)
        if self._hover_min:
            qp.fillRect(mr, QColor("#2A2200"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        qp.drawLine(int(w - bw*3 + 12), 14, int(w - bw*2 - 12), 14)
        # ── Maximize/Restore button ── (middle)
        maxr = QRectF(w - bw*2, 0, bw, 28)
        if self._hover_max:
            qp.fillRect(maxr, QColor("#2A2200"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        mcx = int(w - bw*1.5); mcy = 14
        if self._maximized:
            # Restore icon: two overlapping rectangles
            qp.drawRect(mcx - 4, mcy - 5, 8, 8)
            qp.drawRect(mcx - 2, mcy - 3, 8, 8)
        else:
            # Maximize icon: □
            qp.drawRect(mcx - 5, mcy - 5, 10, 10)
        # ── Close button ── (rightmost)
        xr = QRectF(w - bw, 0, bw, 28)
        if self._hover_x:
            qp.fillRect(xr, QColor("#CC2222"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        cx = w - bw/2; cy = 14
        xsz = 6 if self._hover_x else 4
        qp.drawLine(int(cx-xsz), int(cy-xsz), int(cx+xsz), int(cy+xsz))
        qp.drawLine(int(cx+xsz), int(cy-xsz), int(cx-xsz), int(cy+xsz))
        # ── Resize grip (bottom-right corner) ──
        if not self._minimized:
            for i in range(3):
                x0 = w - 5 - i*4; y0 = h - 5
                qp.setPen(Qt.NoPen)
                qp.setBrush(QColor(pc.red(), pc.green(), pc.blue(), 60 + i*25))
                qp.drawEllipse(QPointF(x0, y0), 1.5, 1.5)
        qp.end()

    def _hit_edge(self, pos):
        """Return resize edge string or None for interior."""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        e = self._EDGE
        if self._minimized:
            return None
        on_l = x < e; on_r = x > w - e; on_t = y < e; on_b = y > h - e
        if on_t and on_l: return "tl"
        if on_t and on_r: return "tr"
        if on_b and on_l: return "bl"
        if on_b and on_r: return "br"
        if on_l: return "l"
        if on_r: return "r"
        if on_t: return "t"
        if on_b: return "b"
        return None

    def _edge_cursor(self, edge):
        m = {"l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor,
             "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
             "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
             "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor}
        return QCursor(m.get(edge, Qt.ArrowCursor))

    def _toggle_minimize(self):
        if self._minimized:
            self._minimized = False
            self.setFixedHeight(16777215)  # QWIDGETSIZE_MAX — remove constraint
            self.resize(self.width(), self._restore_h)
            self._scroll.show()
        else:
            self._restore_h = self.height()
            self._minimized = True
            self._scroll.hide()
            self.setFixedHeight(68)  # title bar + button row only
        self.update()

    def _toggle_maximize(self):
        """Toggle between maximized (fill parent workspace) and restored size."""
        p = self.parentWidget()
        if not p:
            return
        if self._maximized:
            # Restore to previous geometry
            if self._restore_geom:
                self.setGeometry(self._restore_geom)
            self._maximized = False
        else:
            self._restore_geom = self.geometry()
            self.setGeometry(0, 0, p.width(), p.height())
            self._maximized = True
        self._apply_responsive()
        self.update()

    def mousePressEvent(self, e):
        self.raise_()
        x, y = e.position().x(), e.position().y()
        w = self.width()
        bw = 38
        # Close button (rightmost)
        if x > w - bw and y < 28:
            self.close_requested.emit(self._par["sym"]); return
        # Maximize/restore button (middle)
        if x > w - bw*2 and x <= w - bw and y < 28:
            self._toggle_maximize(); return
        # Minimize button (leftmost of 3)
        if x > w - bw*3 and x <= w - bw*2 and y < 28:
            self._toggle_minimize(); return
        # Edge resize (disabled when maximized)
        if not self._maximized:
            edge = self._hit_edge(e.position())
            if edge:
                self._resize_edge = edge
                self._resize_origin = e.globalPosition().toPoint()
                self._resize_geom = self.geometry()
                return
        # Title bar drag (disabled when maximized)
        if y < 28 and not self._maximized:
            self._drag_pos = e.position().toPoint()

    def mouseMoveEvent(self, e):
        # Active resize
        if self._resize_edge and e.buttons() == Qt.LeftButton:
            delta = e.globalPosition().toPoint() - self._resize_origin
            g = QRect(self._resize_geom)
            edge = self._resize_edge
            if "r" in edge: g.setRight(max(g.left() + self._MIN_W, g.right() + delta.x()))
            if "b" in edge: g.setBottom(max(g.top() + self._MIN_H, g.bottom() + delta.y()))
            if "l" in edge: g.setLeft(min(g.right() - self._MIN_W, g.left() + delta.x()))
            if "t" in edge: g.setTop(min(g.bottom() - self._MIN_H, g.top() + delta.y()))
            self.setGeometry(g)
            self._apply_responsive()
            return
        # Active drag
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            delta = e.position().toPoint() - self._drag_pos
            self.move(self.pos() + delta); return
        # Hover state updates — 3 buttons on title bar
        bw = 38
        old_x, old_m, old_mx = self._hover_x, self._hover_min, self._hover_max
        px, py = e.position().x(), e.position().y()
        in_tb = py < 28
        self._hover_x   = in_tb and px > self.width() - bw
        self._hover_max  = in_tb and px > self.width() - bw*2 and px <= self.width() - bw
        self._hover_min  = in_tb and px > self.width() - bw*3 and px <= self.width() - bw*2
        if old_x != self._hover_x or old_m != self._hover_min or old_mx != self._hover_max:
            self.update()
        # Cursor shape
        if not self._maximized:
            edge = self._hit_edge(e.position())
            if edge:
                self.setCursor(self._edge_cursor(edge))
                return
        if self._hover_x or self._hover_min or self._hover_max:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif in_tb and not self._maximized:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

    def leaveEvent(self, _):
        if self._hover_x or self._hover_min or self._hover_max:
            self._hover_x = False; self._hover_min = False; self._hover_max = False; self.update()
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseReleaseEvent(self, _):
        self._drag_pos = None
        self._resize_edge = None
        self._resize_origin = None
        self._resize_geom = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # Trigger responsive layout on resize
        if not self._minimized:
            self._apply_responsive()

    def _apply_responsive(self):
        """Adapt buttons based on panel size. Scroll area handles vertical overflow."""
        w, h = self.width(), self.height()
        self._dashboard_presenter.apply_responsive(w, h, TEXTS.get(self._lang, TEXTS["EN"]))
        # Maximized state clears the flag if parent was resized
        if self._maximized:
            p = self.parentWidget()
            if p and (self.width() != p.width() or self.height() != p.height()):
                self._maximized = False
    def _update_profit_button_text(self, width: int):
        self._dashboard_presenter.update_profit_button_text(width, TEXTS.get(self._lang, TEXTS["EN"]))
    def set_lang(self, lang):
        """Full EN/ES language switch for all dynamic elements."""
        self._lang = lang
        self._dashboard_presenter.apply_language(lang, TEXTS[lang], self.width())

# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR — Panel izquierdo con pares
# ═══════════════════════════════════════════════════════════════════════
class Sidebar(QWidget):
    par_clicked=Signal(dict)
    sub_clicked=Signal()
    refresh_requested=Signal()
    def __init__(self, pares, license_info, parent=None):
        super().__init__(parent)
        self._lang = "EN"
        self._pares = list(pares)
        self._active_syms = set()
        self._live_syms = set()
        self._license_info = dict(license_info or {})
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setMinimumWidth(180); self.setMaximumWidth(320)
        lay=QVBoxLayout(self); lay.setContentsMargins(8,10,8,10); lay.setSpacing(0)
        # Pares scroll
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        scroll.viewport().setAutoFillBackground(False)
        container=QWidget(); container.setAttribute(Qt.WA_NoSystemBackground)
        container.setStyleSheet("background:transparent;")
        cl=QVBoxLayout(container); cl.setContentsMargins(4,2,4,2); cl.setSpacing(4)
        self._pairs_layout = cl
        self.set_pairs(pares)
        scroll.setWidget(container)
        lay.addWidget(scroll,1)
        # Bottom section
        lay.addSpacing(6)
        self._refresh_btn=PremiumButton(TEXTS[self._lang]["refresh_pairs"],"primary")
        self._refresh_btn.setFixedHeight(30)
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        lay.addWidget(self._refresh_btn)
        lay.addSpacing(6)
        # Subscription button
        self._sub_btn=PremiumButton(TEXTS[self._lang]["sub_btn"],"primary")
        self._sub_btn.setFixedHeight(32)
        self._sub_btn.clicked.connect(self.sub_clicked.emit)
        lay.addWidget(self._sub_btn)
        lay.addSpacing(6)
        # License card
        lc=QWidget(); lc.setFixedHeight(100)
        lcl=QVBoxLayout(lc); lcl.setContentsMargins(12,10,12,10); lcl.setSpacing(4)
        tier=self._license_info.get("tier","DEMO") or "DEMO"
        tl=QLabel(tier); tl.setAlignment(Qt.AlignCenter)
        tl.setStyleSheet(f"color:{C['accent']};font-size:16px;font-weight:700;letter-spacing:3px;background:transparent;")
        lcl.addWidget(tl)
        days=self._license_info.get("days_remaining")
        dl=QLabel(""); dl.setAlignment(Qt.AlignCenter)
        dl.setStyleSheet(f"color:{C['dim2']};font-size:11px;background:transparent;")
        self._license_days_lbl = dl
        lcl.addWidget(dl)
        pl=QLabel(""); pl.setAlignment(Qt.AlignCenter)
        pl.setStyleSheet(f"color:{C['gold']};font-size:11px;background:transparent;")
        self._pairs_count_lbl = pl
        lcl.addWidget(pl)
        lay.addWidget(lc)
        lay.addSpacing(4)
        # Diagnostics panel placeholder — injected later via set_diagnostics_panel
        self._diag_slot = lay  # keep ref to insert panel
        self._apply_license_texts()

    def _pairs_count_text(self, count: int) -> str:
        return LICENSE_SERVICE.pairs_count_text(count, TEXTS[self._lang])

    def _days_text(self) -> str:
        return LICENSE_SERVICE.days_text(LicenseSnapshot(self._license_info), TEXTS[self._lang])

    def _diag_toggle_text(self, expanded: bool) -> str:
        return TEXTS[self._lang]["diagnostics_expanded" if expanded else "diagnostics_collapsed"]

    def _apply_license_texts(self):
        if hasattr(self, '_license_days_lbl'):
            self._license_days_lbl.setText(self._days_text())
        if hasattr(self, '_pairs_count_lbl'):
            self._pairs_count_lbl.setText(self._pairs_count_text(len(self._pares)))

    def set_pairs(self, pares):
        self._pares = list(pares)
        if not hasattr(self, '_pairs_layout'):
            return
        while self._pairs_layout.count():
            item = self._pairs_layout.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w:
                w.deleteLater()
        for p in self._pares:
            item=_ParItem(p)
            item.set_active(p["sym"] in self._active_syms)
            item.set_live(p["sym"] in self._live_syms)
            item.clicked.connect(lambda par=p: self.par_clicked.emit(par))
            self._pairs_layout.addWidget(item)
        self._pairs_layout.addStretch()
        self._apply_license_texts()
        self.update()

    def set_active_symbols(self, syms):
        new_syms = set(syms)
        if new_syms == self._active_syms:
            return
        self._active_syms = new_syms
        if not hasattr(self, '_pairs_layout'):
            return
        for i in range(self._pairs_layout.count()):
            item = self._pairs_layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, _ParItem):
                w.set_active(w._par.get("sym") in self._active_syms)

    def set_live_symbols(self, syms):
        new_syms = set(syms)
        if new_syms == self._live_syms:
            return
        self._live_syms = new_syms
        if not hasattr(self, '_pairs_layout'):
            return
        for i in range(self._pairs_layout.count()):
            item = self._pairs_layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, _ParItem):
                w.set_live(w._par.get("sym") in self._live_syms)

    def set_diagnostics_panel(self, panel):
        """Inject the diagnostics panel at the bottom of the sidebar, collapsed by default."""
        self._diag_panel_widget = panel
        panel.hide()
        # Small toggle button — collapsed by default
        self._diag_btn = QPushButton(self._diag_toggle_text(False))
        self._diag_btn.setFixedHeight(22)
        self._diag_btn.setStyleSheet(
            f"QPushButton{{background:{C['card']};color:{C['dim2']};border:1px solid {C['border']};"
            f"border-radius:3px;font-size:10px;font-family:{_font_css_family()};font-weight:700;padding:0 6px;}}"
            f"QPushButton:hover{{background:{C['border2']};color:{C['text']};}}"
        )
        self._diag_btn.clicked.connect(self._toggle_diag)
        self._diag_slot.addSpacing(4)
        self._diag_slot.addWidget(self._diag_btn)
        self._diag_slot.addWidget(panel)

    def _toggle_diag(self):
        visible = self._diag_panel_widget.isVisible()
        self._diag_panel_widget.setVisible(not visible)
        self._diag_btn.setText(self._diag_toggle_text(not visible))

    def set_lang(self, lang):
        self._lang = lang
        self._sub_btn.setText(TEXTS[lang]["sub_btn"])
        self._refresh_btn.setText(TEXTS[lang]["refresh_pairs"])
        self._apply_license_texts()
        if hasattr(self, '_diag_btn'):
            self._diag_btn.setText(self._diag_toggle_text(self._diag_panel_widget.isVisible()))

    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        w,h=self.width(),self.height()
        # Semi-transparent background — particles peek through
        qp.fillRect(self.rect(),QColor(3,3,0,220))
        # Right border
        qp.setPen(QPen(QColor(C["border"]),1))
        qp.drawLine(w-1,0,w-1,h)
        # License card bg
        qp.setPen(Qt.NoPen)
        cr=QRectF(8,h-102,w-16,94)
        path=QPainterPath(); path.addRoundedRect(cr,8,8)
        qp.fillPath(path,QBrush(QColor(C["card"])))
        bg=QLinearGradient(cr.x(),cr.y(),cr.right(),cr.bottom())
        bg.setColorAt(0,QColor(245,166,35,30)); bg.setColorAt(1,QColor(255,215,0,15))
        qp.strokePath(path,QPen(QBrush(bg),1))
        qp.end()

class _ParItem(QWidget):
    clicked=Signal()
    def __init__(self, par, parent=None):
        super().__init__(parent)
        self._par=par; self._hov=False; self._active=False; self._live=False
        self.setFixedHeight(58); self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._scale_val=1.0
        self._anim=QPropertyAnimation(self, b"_zoom")
        self._anim.setDuration(150); self._anim.setEasingCurve(QEasingCurve.OutCubic)
    def set_active(self, active: bool):
        active = bool(active)
        if self._active == active:
            return
        self._active = active
        self.update()
    def set_live(self, live: bool):
        live = bool(live)
        if self._live == live:
            return
        self._live = live
        self.update()
    def _get_zoom(self): return self._scale_val
    def _set_zoom(self, v): self._scale_val=v; self.update()
    _zoom=Property(float, _get_zoom, _set_zoom)
    def enterEvent(self,_):
        self._hov=True
        self._anim.stop(); self._anim.setStartValue(self._scale_val); self._anim.setEndValue(1.05); self._anim.start()
    def leaveEvent(self,_):
        self._hov=False
        self._anim.stop(); self._anim.setStartValue(self._scale_val); self._anim.setEndValue(1.0); self._anim.start()
    def mousePressEvent(self,_): self.clicked.emit()
    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        # Inset-expand zoom: rest=5px inset, hover=fill — fully rounded, no overflow
        m = max(0.0, (1.05 - self._scale_val) / 0.05 * 5.0)
        qp.translate(m, m)
        bw = w - 2*m; bh = h - 2*m
        active_or_hover = self._hov or self._active
        live_col = QColor("#29F0FF")
        if active_or_hover:
            hp=QPainterPath(); hp.addRoundedRect(QRectF(0,0,bw,bh),6,6)
            if self._active:
                ag = QLinearGradient(0, 0, bw, bh)
                ag.setColorAt(0, QColor(35, 26, 6, 240))
                ag.setColorAt(0.45, QColor(28, 22, 6, 232))
                ag.setColorAt(1, QColor(18, 14, 4, 225))
                qp.fillPath(hp, QBrush(ag))
                gp = QRadialGradient(bw * 0.15, bh * 0.5, bw * 0.75)
                gp.setColorAt(0, QColor(255, 210, 70, 36))
                gp.setColorAt(1, QColor(255, 184, 40, 0))
                qp.fillPath(hp, QBrush(gp))
                qp.strokePath(hp, QPen(QColor(255,215,0,90),1.2))
            else:
                qp.fillPath(hp, QBrush(QColor(C["card"])))
            # Vibrant gold accent bar — gradient + outer glow, matches PremiumButton style
            bar_y = max(0, int(10-m)); bar_h = int(bh - max(0, 20-2*m))
            bg_g = QLinearGradient(0, bar_y, 0, bar_y+bar_h)
            bg_g.setColorAt(0, QColor(255,225,85,210))
            bg_g.setColorAt(0.45, QColor(255,184,40,255))
            bg_g.setColorAt(1, QColor(195,105,0,195))
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(bg_g))
            qp.drawRoundedRect(0, bar_y, 3, bar_h, 2, 2)
            # Outer glow
            gw = QRadialGradient(1.5, bar_y + bar_h*0.5, 22)
            gw.setColorAt(0, QColor(255,195,50,80)); gw.setColorAt(0.4, QColor(255,184,40,32)); gw.setColorAt(1, QColor(255,184,40,0))
            qp.setBrush(QBrush(gw))
            qp.drawEllipse(QRectF(-20, bar_y-15, 44, bar_h+30))
        if self._live:
            lp = QPainterPath(); lp.addRoundedRect(QRectF(0.6,0.6,bw-1.2,bh-1.2),6,6)
            qp.strokePath(lp, QPen(QColor(41,240,255,80 if self._active else 110), 1.0))
            glow = QRadialGradient(bw - 12, 12, 15)
            glow.setColorAt(0, QColor(41,240,255,160))
            glow.setColorAt(0.35, QColor(41,240,255,70))
            glow.setColorAt(1, QColor(41,240,255,0))
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(glow))
            qp.drawEllipse(QRectF(bw - 27, -2, 30, 30))
            qp.setBrush(QColor(41,240,255,230))
            qp.drawEllipse(QRectF(bw - 15.5, 8.5, 7, 7))
        # Icon
        pc=QColor(self._par["color"])
        ir=QRectF(12,max(2,9-m),40,40)
        ip=QPainterPath(); ip.addRoundedRect(ir,8,8)
        fill_alpha = 40 if self._active else 25
        stroke_col = QColor(255,215,0,120) if self._active else QColor(pc.red(),pc.green(),pc.blue(),60)
        icon_col = QColor("#FFF3C1") if self._active else (live_col if self._live else pc)
        qp.fillPath(ip,QBrush(QColor(pc.red(),pc.green(),pc.blue(),fill_alpha)))
        qp.strokePath(ip,QPen(stroke_col,1))
        qp.setPen(icon_col); qp.setFont(QFont(FONT_DISPLAY,11,QFont.Bold))
        qp.drawText(ir,Qt.AlignCenter,self._par["icon"])
        # Text
        sym_col = QColor(C["gold"]) if self._active else QColor(C["text"])
        qp.setPen(sym_col); qp.setFont(QFont(FONT_DISPLAY,12,QFont.Bold))
        qp.drawText(QRectF(60,max(2,8-m),bw-70,20),Qt.AlignVCenter,self._par["sym"])
        strat_col = QColor(C["text2"] if self._active else C["dim"])
        qp.setPen(strat_col); qp.setFont(QFont(FONT_DISPLAY,8,QFont.Medium))
        qp.drawText(QRectF(60,min(bh-20,28-m),bw-70,18),Qt.AlignVCenter,self._par["strategy"])
        qp.end()

# ═══════════════════════════════════════════════════════════════════════
#  WORKSPACE — Zona central donde viven los dashboards
# ═══════════════════════════════════════════════════════════════════════
class Workspace(QWidget):
    dashboard_opened=Signal(str)
    dashboard_closed=Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._subs: dict[str,ParDashboard] = {}
        self._lang = "EN"
    def set_lang(self, lang):
        self._lang = lang
        for d in self._subs.values():
            if hasattr(d, "set_lang"): d.set_lang(lang)
        self.update()
    def add_dashboard(self, par):
        sym=par["sym"]
        if sym in self._subs:
            self._subs[sym].raise_(); return
        d=ParDashboard(par,self)
        d.set_lang(self._lang)
        d.close_requested.connect(self._close_sub)
        # Position
        n=len(self._subs)
        d.setGeometry(20+n*30, 10+n*30, 550, 720)
        d.show()
        self._subs[sym]=d
        self.dashboard_opened.emit(sym)
    def _close_sub(self, sym):
        if sym in self._subs:
            w = self._subs[sym]
            if hasattr(w, '_worker') and w._worker.isRunning():
                w._worker.stop()
            w.deleteLater()
            del self._subs[sym]
            self.dashboard_closed.emit(sym)
    def sync_pairs(self, pares):
        by_sym = {p["sym"]: p for p in pares}
        for sym in list(self._subs.keys()):
            if sym == "__sub__":
                continue
            if sym not in by_sym:
                self._close_sub(sym)
                continue
            w = self._subs[sym]
            w._par = by_sym[sym]
            w._color = by_sym[sym]["color"]
            w._runtime = PAIR_RUNTIME.get(sym, {})
            if hasattr(w, '_worker'):
                w._worker._rt = w._runtime
                w._worker._sym = sym
            w.update()
        self.update()
    def active_symbols(self):
        return [sym for sym in self._subs.keys() if sym != "__sub__"]
    def tile_h(self):
        subs=list(self._subs.values())
        if not subs: return
        w,h=self.width(),self.height()
        # Calculate grid that respects minimum panel sizes
        min_w, min_h = ParDashboard._MIN_W, ParDashboard._MIN_H
        max_cols = max(1, w // min_w)
        cols = min(len(subs), max_cols, 4)
        rows = math.ceil(len(subs) / cols)
        sw = w // cols
        sh = max(min_h, h // rows)  # enforce minimum height
        for i, s in enumerate(subs):
            # Clear maximized state when tiling
            s._maximized = False
            s.setGeometry((i % cols) * sw, (i // cols) * sh, sw - 2, sh - 2)
            s._apply_responsive()
    def tile_v(self):
        subs=list(self._subs.values())
        if not subs: return
        w,h=self.width(),self.height()
        min_h = ParDashboard._MIN_H
        sh = max(min_h, h // len(subs))
        for i, s in enumerate(subs):
            s._maximized = False
            s.setGeometry(0, i * sh, w, sh - 2)
            s._apply_responsive()
    def cascade(self):
        for i,s in enumerate(self._subs.values()):
            s._maximized = False
            s.setGeometry(20+i*30,10+i*30,min(550,self.width()-60),min(720,self.height()-40))
            s._apply_responsive()
    def open_subscription(self, lic, pares):
        key="__sub__"
        if key in self._subs: self._subs[key].raise_(); return
        d=SubscriptionPanel(lic,pares,self)
        if hasattr(d, "set_lang"):
            d.set_lang(self._lang)
        d.close_requested.connect(self._close_sub)
        d.setGeometry(max(20,self.width()//2-220),30,440,520)
        d.show(); self._subs[key]=d; self.update()
    def close_all(self):
        for s in list(self._subs.values()):
            if hasattr(s, '_worker') and s._worker.isRunning():
                s._worker.stop()
            s.deleteLater()
        self._subs.clear(); self.update()
    def paintEvent(self, _):
        if self._subs: return
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        cx,cy=w//2,h//2-40
        fn=_ui_font(42,QFont.Black)
        qp.setFont(fn); fm=qp.fontMetrics()
        nw=fm.horizontalAdvance("N"); ow=fm.horizontalAdvance("OVA"); lx=cx-(nw+ow)//2
        for r2,a2 in [(40,4),(25,8),(15,14)]:
            rg=QRadialGradient(lx+nw//2,cy,r2)
            rg.setColorAt(0,QColor(255,255,255,a2)); rg.setColorAt(1,QColor(255,255,255,0))
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(rg))
            qp.drawEllipse(QRectF(lx+nw//2-r2,cy-r2,r2*2,r2*2))
        ocx=lx+nw+ow//2
        for r2,a2 in [(70,3),(45,6),(25,12)]:
            rg=QRadialGradient(ocx,cy,r2)
            rg.setColorAt(0,QColor(245,166,35,a2)); rg.setColorAt(1,QColor(245,166,35,0))
            qp.setPen(Qt.NoPen); qp.setBrush(QBrush(rg))
            qp.drawEllipse(QRectF(ocx-r2,cy-r2,r2*2,r2*2))
        qp.setPen(QPen(QColor("#FFFFFF"))); qp.setFont(fn)
        qp.drawText(QRectF(lx,cy-30,nw+2,60),Qt.AlignCenter,"N")
        gova=QLinearGradient(lx+nw,0,lx+nw+ow,0)
        gova.setColorAt(0,QColor("#E06010")); gova.setColorAt(0.5,QColor("#F5A623")); gova.setColorAt(1,QColor("#FFD700"))
        qp.setPen(QPen(QBrush(gova),0)); qp.setFont(fn)
        qp.drawText(QRectF(lx+nw,cy-30,ow+2,60),Qt.AlignCenter,"OVA")
        g=QLinearGradient(cx-140,0,cx+140,0)
        g.setColorAt(0,QColor(0,0,0,0)); g.setColorAt(0.2,QColor(245,166,35,60))
        g.setColorAt(0.5,QColor(255,215,0,120)); g.setColorAt(0.8,QColor(245,166,35,60)); g.setColorAt(1,QColor(0,0,0,0))
        qp.fillRect(QRectF(cx-140,cy+30,280,2),QBrush(g))
        f2=_ui_font(9); f2.setLetterSpacing(QFont.AbsoluteSpacing,5)
        qp.setFont(f2); qp.setPen(QPen(QColor(C["dim"])))
        qp.drawText(QRectF(0,cy+40,w,25),Qt.AlignCenter,"T R A D I N G   A I")
        qp.setFont(_ui_font(11)); qp.setPen(QPen(QColor(C["dim2"])))
        qp.drawText(QRectF(0,cy+90,w,25),Qt.AlignCenter,TEXTS[self._lang]["hint"])
        qp.setFont(_ui_font(8)); qp.setPen(QPen(QColor(C["dim"])))
        qp.drawText(QRectF(0,cy+130,w,20),Qt.AlignCenter,"v5.0.0  ✦  Polarice Labs  ✦  © 2026")
        qp.end()

class SubscriptionPanel(QWidget):
    close_requested=Signal(str)
    def __init__(self, lic, pares, parent=None):
        super().__init__(parent); self._lic=lic; self._pares=pares; self._lang="EN"
        self.setAttribute(Qt.WA_NoSystemBackground); self._drag_pos=None
        self._hover_x=False; self._hover_min=False; self._hover_max=False
        self._maximized=False; self._restore_geom=None; self._minimized=False; self._restore_h=520
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        tb=QWidget(); tb.setFixedHeight(28); tb.setCursor(QCursor(Qt.OpenHandCursor)); lay.addWidget(tb)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        scroll.viewport().setAutoFillBackground(False)
        self._scroll = scroll
        body=QWidget(); body.setAttribute(Qt.WA_NoSystemBackground); body.setStyleSheet("background:transparent;")
        bl=QVBoxLayout(body); bl.setContentsMargins(20,12,20,20); bl.setSpacing(8)
        tier=lic.get("tier","DEMO") or "DEMO"
        self._tier_lbl=QLabel(tier); self._tier_lbl.setAlignment(Qt.AlignCenter)
        self._tier_lbl.setStyleSheet(f"color:{C['accent']};font-size:32px;font-weight:900;letter-spacing:5px;background:transparent;")
        bl.addWidget(self._tier_lbl)
        self._client_lbl=QLabel(f"{lic.get('client','Demo User')}"); self._client_lbl.setAlignment(Qt.AlignCenter)
        self._client_lbl.setStyleSheet(f"color:{C['text']};font-size:16px;font-weight:600;background:transparent;"); bl.addWidget(self._client_lbl)
        self._client_sub_lbl=QLabel(); self._client_sub_lbl.setAlignment(Qt.AlignCenter)
        self._client_sub_lbl.setStyleSheet(f"color:{C['dim2']};font-size:11px;background:transparent;letter-spacing:2px;"); bl.addWidget(self._client_sub_lbl)
        bl.addSpacing(12)
        self._info_rows = {}
        for key in ("license_key","license_expiry","license_days","license_pairs","license_server","license_status"):
            r=QHBoxLayout()
            l=QLabel(); l.setStyleSheet(f"color:{C['dim2']};font-size:13px;background:transparent;")
            v=QLabel(); v.setStyleSheet(f"color:{C['text']};font-size:13px;font-family:{_font_css_family()};font-weight:500;background:transparent;")
            v.setAlignment(Qt.AlignRight); r.addWidget(l); r.addStretch(); r.addWidget(v); bl.addLayout(r)
            self._info_rows[key] = (l, v)
        bl.addSpacing(12)
        self._pairs_title_lbl=QLabel()
        self._pairs_title_lbl.setStyleSheet(f"color:{C['gold']};font-size:10px;font-weight:700;letter-spacing:3px;background:transparent;"); bl.addWidget(self._pairs_title_lbl)
        bl.addSpacing(4)
        self._pair_labels=[]
        for p in pares:
            pr=QLabel(f"  {p.get('short', p['icon'])}   {p['sym']}  —  {p['strategy']}")
            pr.setStyleSheet(f"color:{C['text2']};font-size:13px;font-family:{_font_css_family()};font-weight:500;background:transparent;"); bl.addWidget(pr)
            self._pair_labels.append((pr, p))
        bl.addStretch(); scroll.setWidget(body); lay.addWidget(scroll,1)
        self.setMouseTracking(True)
        self.set_lang(self._lang)

    def _btn_rect(self, i):
        bw = 38
        return QRectF(self.width() - bw*(3-i), 0, bw, 28)

    def set_lang(self, lang):
        self._lang = lang
        t = TEXTS[lang]
        self._client_sub_lbl.setText(t["license_client_sub"])
        rows = LICENSE_SERVICE.subscription_rows(LicenseSnapshot(self._lic), self._pares, t)
        for key, (lbl, val) in self._info_rows.items():
            lbl.setText(t[key])
            val.setText(rows[key])
        self._pairs_title_lbl.setText(t["pairs_in_license"])
        for lbl, p in self._pair_labels:
            lbl.setText(f"  {p.get('short', p['icon'])}   {p['sym']}  —  {p['strategy']}")
        self.update()

    def _toggle_minimize(self):
        if self._minimized:
            self._minimized = False
            self.setFixedHeight(16777215)
            self.resize(self.width(), self._restore_h)
            self._scroll.show()
        else:
            self._restore_h = self.height()
            self._minimized = True
            self._scroll.hide()
            self.setFixedHeight(68)
        self.update()

    def _toggle_maximize(self):
        p = self.parentWidget()
        if not p:
            return
        if self._maximized:
            if self._restore_geom:
                self.setGeometry(self._restore_geom)
            self._maximized = False
        else:
            self._restore_geom = self.geometry()
            self.setGeometry(0, 0, p.width(), p.height())
            self._maximized = True
        self.update()

    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        # Outer glow rings
        for i,a in [(5,6),(3,14),(1,25)]:
            gp=QPainterPath(); gp.addRoundedRect(QRectF(-i,-i,w+2*i,h+2*i),12+i,12+i)
            qp.strokePath(gp,QPen(QColor(255,184,40,a),1))
        # Card with rich gradient fill
        path=QPainterPath(); path.addRoundedRect(QRectF(0.5,0.5,w-1,h-1),12,12)
        bg_fill=QLinearGradient(0,0,0,h)
        bg_fill.setColorAt(0,QColor(22,18,8,252)); bg_fill.setColorAt(0.15,QColor(16,13,5,252)); bg_fill.setColorAt(1,QColor(10,8,3,252))
        qp.fillPath(path,QBrush(bg_fill))
        # Shimmer at top
        shimmer=QRadialGradient(w/2,0,w*0.6)
        shimmer.setColorAt(0,QColor(255,215,0,18)); shimmer.setColorAt(1,QColor(0,0,0,0))
        sp=QPainterPath(); sp.addRoundedRect(QRectF(1,1,w-2,100),11,11)
        qp.fillPath(sp.intersected(path),QBrush(shimmer))
        # Gold border — premium glow
        border_g=QLinearGradient(0,0,w,h)
        border_g.setColorAt(0,QColor(245,166,35,160)); border_g.setColorAt(0.25,QColor(255,215,0,120))
        border_g.setColorAt(0.5,QColor(255,230,100,200)); border_g.setColorAt(0.75,QColor(255,215,0,120))
        border_g.setColorAt(1,QColor(245,166,35,160))
        qp.strokePath(path,QPen(QBrush(border_g),1.8))
        # Red accent lines (left & right) — signature premium
        rp=QPen(QColor(200,35,35,160),2.5)
        qp.setPen(rp); qp.drawLine(3,35,3,h-15); qp.drawLine(w-3,35,w-3,h-15)
        # Title bar
        qp.setPen(Qt.NoPen); qp.setBrush(QColor(8,6,2,250))
        tp=QPainterPath(); tp.addRoundedRect(QRectF(1,1,w-2,28),11,11); qp.drawPath(tp)
        # Top gold accent
        g_top=QLinearGradient(0,0,w,0)
        g_top.setColorAt(0,QColor(0,0,0,0)); g_top.setColorAt(0.15,QColor(245,166,35,180))
        g_top.setColorAt(0.5,QColor(255,215,0,255)); g_top.setColorAt(0.85,QColor(245,166,35,180))
        g_top.setColorAt(1,QColor(0,0,0,0))
        qp.setPen(QPen(QBrush(g_top),2.5)); qp.drawLine(15,1,w-15,1)
        # Title text
        qp.setPen(QColor(C["accent"])); qp.setFont(_ui_font(9,QFont.Bold))
        qp.drawText(QRectF(12,0,w-124,28),Qt.AlignVCenter,TEXTS[self._lang]["license_title"])
        bw = 38
        mr = QRectF(w - bw*3, 0, bw, 28)
        if self._hover_min:
            qp.fillRect(mr, QColor("#2A2200"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        qp.drawLine(int(w - bw*3 + 12), 14, int(w - bw*2 - 12), 14)
        maxr = QRectF(w - bw*2, 0, bw, 28)
        if self._hover_max:
            qp.fillRect(maxr, QColor("#2A2200"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        mcx = int(w - bw*1.5); mcy = 14
        if self._maximized:
            qp.drawRect(mcx - 4, mcy - 5, 8, 8)
            qp.drawRect(mcx - 2, mcy - 3, 8, 8)
        else:
            qp.drawRect(mcx - 5, mcy - 5, 10, 10)
        xr = QRectF(w - bw, 0, bw, 28)
        if self._hover_x:
            qp.fillRect(xr, QColor("#CC2222"))
            qp.setPen(QPen(QColor("#FFFFFF"), 1.5))
        else:
            qp.setPen(QPen(QColor(C["dim2"]), 1.3))
        cx = w - bw/2; cy = 14
        xsz = 6 if self._hover_x else 4
        qp.drawLine(int(cx-xsz), int(cy-xsz), int(cx+xsz), int(cy+xsz))
        qp.drawLine(int(cx+xsz), int(cy-xsz), int(cx-xsz), int(cy+xsz))
        qp.end()
    def mousePressEvent(self, e):
        self.raise_()
        x, y = e.position().x(), e.position().y()
        w = self.width(); bw = 38
        if x > w - bw and y < 28:
            self.close_requested.emit("__sub__"); return
        if x > w - bw*2 and x <= w - bw and y < 28:
            self._toggle_maximize(); return
        if x > w - bw*3 and x <= w - bw*2 and y < 28:
            self._toggle_minimize(); return
        if y < 28 and not self._maximized:
            self._drag_pos=e.position().toPoint()
    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons()==Qt.LeftButton:
            self.move(self.pos()+(e.position().toPoint()-self._drag_pos)); return
        bw = 38
        old = (self._hover_x, self._hover_min, self._hover_max)
        px, py = e.position().x(), e.position().y()
        in_tb = py < 28
        self._hover_x = in_tb and px > self.width() - bw
        self._hover_max = in_tb and px > self.width() - bw*2 and px <= self.width() - bw
        self._hover_min = in_tb and px > self.width() - bw*3 and px <= self.width() - bw*2
        if old != (self._hover_x, self._hover_min, self._hover_max):
            self.update()
        if self._hover_x or self._hover_min or self._hover_max:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif in_tb and not self._maximized:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
    def leaveEvent(self, _):
        if self._hover_x or self._hover_min or self._hover_max:
            self._hover_x = False; self._hover_min = False; self._hover_max = False; self.update()
        self.setCursor(QCursor(Qt.ArrowCursor))
    def mouseReleaseEvent(self,_): self._drag_pos=None

# ═══════════════════════════════════════════════════════════════════════
#  TOOLBAR — Botones de layout keygen-style
# ═══════════════════════════════════════════════════════════════════════
class LayoutToolbar(QWidget):
    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self._ws=workspace
        self._lang = "EN"
        self.setFixedHeight(44)
        self.setAttribute(Qt.WA_NoSystemBackground)
        lay=QHBoxLayout(self); lay.setContentsMargins(14,5,14,5); lay.setSpacing(8)
        self._label=QLabel(TEXTS[self._lang]["layout"]); self._label.setStyleSheet(f"color:{C['dim']};font-size:8px;font-weight:600;letter-spacing:2px;background:transparent;")
        lay.addWidget(self._label); lay.addSpacing(6)
        self._buttons = []
        for key,fn in [("tile_h",workspace.tile_h),("tile_v",workspace.tile_v),
                       ("cascade",workspace.cascade),("close_all",workspace.close_all)]:
            b=PremiumButton(TEXTS[self._lang][key],"primary"); b.setFixedHeight(30); b.setFixedWidth(100)
            b.clicked.connect(fn); lay.addWidget(b); self._buttons.append((key, b))
        lay.addStretch()
    def set_lang(self, lang):
        self._lang = lang
        self._label.setText(TEXTS[lang]["layout"])
        for key, btn in self._buttons:
            btn.setText(TEXTS[lang][key])
    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.fillRect(self.rect(),QColor(C["bg"]))
        w,h=self.width(),self.height()
        qp.setPen(QPen(QColor(C["border"]),1)); qp.drawLine(0,h-1,w,h-1)
        qp.end()

# ═══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════
# ──────────────────────────────────────────────────────────────────────────────
class UpdateBanner(QWidget):
    """Barra dorada que aparece en la parte superior cuando hay actualización."""

    download_clicked = Signal()
    dismiss_clicked  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(0)   # oculto por defecto
        self._anim = QPropertyAnimation(self, b"maximumHeight", self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._restart_mode = False
        self._build_ui()

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 5, 14, 5)
        lay.setSpacing(10)

        self._icon = QLabel("🚀")
        self._icon.setStyleSheet("font-size:15px;")

        self._lbl = QLabel("Nueva versión disponible")
        self._lbl.setStyleSheet(
            "color:#1a1000; font-weight:700; font-size:12px;"
        )

        self._btn_dl = QPushButton("Actualizar ahora")
        self._btn_dl.setFixedSize(140, 26)
        self._btn_dl.setStyleSheet("""
            QPushButton {
                background:#1a1000; color:#F5A623;
                border:1px solid #F5A623; border-radius:5px;
                font-weight:700; font-size:11px;
            }
            QPushButton:hover { background:#2a2000; }
            QPushButton:disabled { opacity:0.5; }
        """)
        self._btn_dl.clicked.connect(self._on_btn_clicked)

        self._btn_x = QPushButton("✕")
        self._btn_x.setFixedSize(24, 24)
        self._btn_x.setStyleSheet(
            "QPushButton{background:transparent;color:#1a1000;border:none;font-size:14px;}"
            "QPushButton:hover{color:#000;}"
        )
        self._btn_x.clicked.connect(self._hide)

        self._prog = QProgressBar()
        self._prog.setFixedSize(160, 10)
        self._prog.setVisible(False)
        self._prog.setTextVisible(False)
        self._prog.setStyleSheet("""
            QProgressBar{background:#2a2000;border:none;border-radius:5px;}
            QProgressBar::chunk{background:#1a1000;border-radius:5px;}
        """)

        lay.addWidget(self._icon)
        lay.addWidget(self._lbl, 1)
        lay.addWidget(self._prog)
        lay.addWidget(self._btn_dl)
        lay.addWidget(self._btn_x)
        self.setStyleSheet("background:#F5A623;")

    def _on_btn_clicked(self):
        if self._restart_mode:
            self.dismiss_clicked.emit()   # el MainWindow maneja el restart
        else:
            self.download_clicked.emit()

    def _hide(self):
        self._anim.setStartValue(self.maximumHeight())
        self._anim.setEndValue(0)
        self._anim.start()

    def _show(self):
        self._anim.setStartValue(0)
        self._anim.setEndValue(38)
        self._anim.start()

    # ── API pública ─────────────────────────────────────────────────────
    def show_update(self, version: str, files: list):
        n = len(files)
        names = ", ".join(f.split("/")[-1] for f in files[:3])
        extra = "..." if n > 3 else ""
        self._lbl.setText(
            f"NOVA v{version} disponible — {n} archivo{'s' if n!=1 else ''}: {names}{extra}"
        )
        self._icon.setText("🚀")
        self._btn_dl.setText("Actualizar ahora")
        self._btn_dl.setEnabled(True)
        self._restart_mode = False
        self._show()

    def show_progress(self, file: str, index: int, total: int):
        self._prog.setVisible(True)
        self._prog.setMaximum(total)
        self._prog.setValue(index)
        short = file.split("/")[-1]
        self._lbl.setText(f"⬇ Descargando {short}  [{index}/{total}]")
        self._btn_dl.setEnabled(False)

    def show_complete(self, updated: list):
        self._prog.setVisible(False)
        n = len(updated)
        self._icon.setText("✅")
        self._lbl.setText(
            f"{n} archivo{'s' if n!=1 else ''} actualizado{'s' if n!=1 else ''} — "
            f"Reinicia NOVA para aplicar los cambios."
        )
        self._btn_dl.setText("Reiniciar")
        self._btn_dl.setEnabled(True)
        self._restart_mode = True


class NOVADashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self._lang = "EN"
        self.setWindowTitle("NOVA Trading AI — Dashboard v5.0")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1000, 650)
        self.resize(1400, 850)
        self.setStyleSheet(_build_qss())
        self._center()

        # License
        self._license = LICENSE_SERVICE.load().raw
        self._pares=list(ALL_PARES)
        self._pair_runtime_sig = json.dumps(PAIR_RUNTIME, sort_keys=True)

        # Root — dark bg base
        self.root=QWidget(self); self.setCentralWidget(self.root)
        self.root.setStyleSheet(f"background:{C['bg']};")
        # Layout first
        main=QVBoxLayout(self.root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)
        self._titlebar=TitleBar(self)
        self._titlebar.set_lang(self._lang)
        main.addWidget(self._titlebar)
        self._session=SessionBar()
        self._session.set_lang(self._lang)
        main.addWidget(self._session)
        # ── Update banner (oculto hasta que haya actualización)
        self._update_banner = UpdateBanner(self)
        self._update_banner.download_clicked.connect(self._start_download)
        self._update_banner.dismiss_clicked.connect(self._restart_nova)
        main.addWidget(self._update_banner)
        # Splitter: sidebar | workspace
        self._splitter=QSplitter(Qt.Horizontal)
        self._splitter.setAttribute(Qt.WA_NoSystemBackground)
        self._splitter.setStyleSheet("QSplitter{background:transparent;}"
                               f"QSplitter::handle{{background:{C['border']};width:3px;}}")
        self._sidebar=Sidebar(self._pares,self._license)
        self._workspace=Workspace()
        self._workspace.set_lang(self._lang)
        # Diagnostics engine — auto-detect bugs in real-time
        self._diag=None; self._diag_panel=None
        if _DIAG_OK:
            self._diag=DiagnosticsEngine(self)
            self._diag_panel=DiagnosticsPanel(self._diag)
            self._sidebar.set_diagnostics_panel(self._diag_panel)
            self._diag.start()
        self._toolbar=LayoutToolbar(self._workspace)
        self._toolbar.set_lang(self._lang)
        # Add hamburger toggle to toolbar
        self._sidebar_visible=True
        hb=PremiumButton("☰","primary"); hb.setFixedHeight(26); hb.setFixedWidth(36)
        hb.clicked.connect(self._toggle_sidebar)
        self._toolbar.layout().insertWidget(0,hb)
        right=QWidget(); right.setAttribute(Qt.WA_NoSystemBackground)
        right.setStyleSheet("background:transparent;")
        rl=QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        rl.addWidget(self._toolbar); rl.addWidget(self._workspace,1)
        self._splitter.addWidget(self._sidebar); self._splitter.addWidget(right)
        self._splitter.setSizes([230,self.width()-230])
        self._splitter.setStretchFactor(0,0); self._splitter.setStretchFactor(1,1)
        main.addWidget(self._splitter,1)
        # Connections
        self._sidebar.par_clicked.connect(self._workspace.add_dashboard)
        self._sidebar.refresh_requested.connect(self._refresh_detected_pairs)
        self._sidebar.sub_clicked.connect(
            lambda: self._workspace.open_subscription(self._license, self._pares)
        )
        self._workspace.dashboard_opened.connect(lambda _sym: self._sidebar.set_active_symbols(self._workspace.active_symbols()))
        self._workspace.dashboard_closed.connect(lambda _sym: self._sidebar.set_active_symbols(self._workspace.active_symbols()))
        self._titlebar.lang_toggled.connect(self._set_lang)
        self._sidebar.set_lang(self._lang)
        self._pair_refresh_timer = QTimer(self)
        self._pair_refresh_timer.setInterval(12000)
        self._pair_refresh_timer.timeout.connect(self._refresh_detected_pairs)
        self._pair_refresh_timer.start()
        self._runtime_status_worker = RuntimeActivityWorker(5000, self)
        self._runtime_status_worker.live_ready.connect(self._sidebar.set_live_symbols)
        self._runtime_status_worker.set_inputs(self._pares, PAIR_RUNTIME)
        self._runtime_status_worker.start()
        # ── Verificar actualizaciones 3s después de arrancar
        self._pending_update_version = ""
        self._pending_update_files   = []
        self._nova_updater = None
        if _UPDATER_AVAILABLE:
            self._nova_updater = NovaUpdater(
                on_update_available = self._on_update_available,
                on_progress         = self._on_update_progress,
                on_complete         = self._on_update_complete,
                on_error            = lambda msg: log.warning(f"[Updater] {msg}"),
                on_no_update        = lambda: log.info("NOVA está al día."),
            )
            QTimer.singleShot(3000, self._nova_updater.check_async)
        # Vignette underlay — keeps the cinematic dark falloff below the logo
        self.bg_vignette=BackgroundCanvas(self.root, draw_particles=False, draw_vignette=True)
        self.bg_vignette.setGeometry(0,0,self.width(),self.height())
        self.bg_vignette.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.bg_vignette.lower()
        # Particles overlay — kept above UI for the brighter original look
        self.bg=BackgroundCanvas(self.root, draw_particles=True, draw_vignette=False)
        self.bg.setGeometry(0,0,self.width(),self.height())
        self.bg.raise_()  # On top of all widgets
        self.bg.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Clicks pass through

    # ── Métodos del sistema de actualización ─────────────────────────────────

    def _on_update_available(self, version: str, files: list):
        """Llamado desde thread del updater → despacha a hilo principal."""
        self._pending_update_version = version
        self._pending_update_files   = files
        # QTimer.singleShot es thread-safe en PySide6
        QTimer.singleShot(0, self._show_update_banner)

    def _show_update_banner(self):
        self._update_banner.show_update(
            self._pending_update_version,
            self._pending_update_files,
        )

    def _start_download(self):
        if self._nova_updater:
            self._nova_updater.download_updates()

    def _on_update_progress(self, file: str, index: int, total: int):
        """Thread del updater → hilo principal."""
        QTimer.singleShot(0, lambda: self._update_banner.show_progress(file, index, total))

    def _on_update_complete(self, updated: list):
        """Thread del updater → hilo principal."""
        QTimer.singleShot(0, lambda: self._update_banner.show_complete(updated))

    def _restart_nova(self):
        """Reinicia el ejecutable para aplicar los archivos descargados."""
        import subprocess
        exe  = sys.executable
        args = sys.argv[:]
        subprocess.Popen([exe] + args)
        QApplication.quit()

    # ──────────────────────────────────────────────────────────────────

    def _refresh_detected_pairs(self):
        global PAIR_RUNTIME
        runtime = _discover_pair_runtime()
        runtime_sig = json.dumps(runtime, sort_keys=True)
        if runtime_sig == getattr(self, '_pair_runtime_sig', ''):
            return
        PAIR_RUNTIME.clear()
        PAIR_RUNTIME.update(runtime)
        self._pares = _build_available_pairs(PAIR_RUNTIME)
        self._pair_runtime_sig = runtime_sig
        if hasattr(self, '_sidebar'):
            self._sidebar.set_pairs(self._pares)
        if hasattr(self, '_workspace'):
            self._workspace.sync_pairs(self._pares)
        if hasattr(self, '_sidebar') and hasattr(self, '_workspace'):
            self._sidebar.set_active_symbols(self._workspace.active_symbols())
        if hasattr(self, '_runtime_status_worker'):
            self._runtime_status_worker.set_inputs(self._pares, PAIR_RUNTIME)

    def _set_lang(self, lang: str):
        """Propagate EN/ES language change to all live sub-widgets."""
        self._lang = lang
        self._workspace.set_lang(lang)
        self._sidebar.set_lang(lang)
        self._titlebar.set_lang(lang)
        self._session.set_lang(lang)
        self._toolbar.set_lang(lang)
    def closeEvent(self, e):
        if hasattr(self, '_runtime_status_worker') and self._runtime_status_worker.isRunning():
            self._runtime_status_worker.stop()
        if hasattr(self, '_workspace'):
            self._workspace.close_all()
        super().closeEvent(e)
    def _center(self):
        s=QApplication.primaryScreen().geometry()
        fg=self.frameGeometry(); fg.moveCenter(s.center()); self.move(fg.topLeft())
    def _toggle_sidebar(self):
        self._sidebar_visible=not self._sidebar_visible
        if self._sidebar_visible:
            self._sidebar.show()
            self._splitter.setSizes([230,self.width()-230])
        else:
            self._sidebar.hide()
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self,'root'): self.root.setGeometry(0,0,self.width(),self.height())
        if hasattr(self,'bg_vignette'):
            self.bg_vignette.setGeometry(0,0,self.width(),self.height())
            self.bg_vignette.lower()
        if hasattr(self,'bg'):
            self.bg.setGeometry(0,0,self.width(),self.height())
            self.bg.raise_()
    def paintEvent(self, _):
        qp=QPainter(self)
        if not qp.isActive(): return
        qp.setRenderHint(QPainter.Antialiasing)
        r = 0 if self.isMaximized() else 12
        path=QPainterPath(); path.addRoundedRect(QRectF(0.5,0.5,self.width()-1,self.height()-1),r,r)
        qp.fillPath(path, QBrush(QColor(C["bg"])))
        if r > 0:
            qp.strokePath(path, QPen(QColor(C["border2"]), 1))
        qp.end()

    # ── Windows snap, edge-resize, DWM corners ──────────────────────
    _BORDER = 7

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))
                # WM_NCCALCSIZE — return 0 so WS_THICKFRAME doesn't add a visible frame
                if msg.message == 0x0083:                       # WM_NCCALCSIZE
                    if msg.wParam:
                        return True, 0
                if msg.message == 0x0084:                       # WM_NCHITTEST
                    xs = ctypes.c_short(msg.lParam & 0xFFFF).value
                    ys = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    pos = self.mapFromGlobal(QPoint(xs, ys))
                    x, y = pos.x(), pos.y()
                    w, h = self.width(), self.height()
                    bw = self._BORDER
                    if not self.isMaximized():
                        if x < bw  and y < bw:  return True, 13   # HTTOPLEFT
                        if x > w-bw and y < bw:  return True, 14   # HTTOPRIGHT
                        if x < bw  and y > h-bw: return True, 16   # HTBOTTOMLEFT
                        if x > w-bw and y > h-bw: return True, 17  # HTBOTTOMRIGHT
                        if x < bw:  return True, 10                 # HTLEFT
                        if x > w-bw: return True, 11                # HTRIGHT
                        if y < bw:  return True, 12                 # HTTOP
                        if y > h-bw: return True, 15                # HTBOTTOM
                    if y < 46 and x < w - 216:
                        return True, 2                              # HTCAPTION
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def _apply_win11_corners(self):
        """DWM round corners + WS_THICKFRAME for Windows 11 snap."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            # ── Inject WS_THICKFRAME so Win11 snap layouts work ──
            GWL_STYLE = -16
            WS_THICKFRAME = 0x00040000
            WS_MAXIMIZEBOX = 0x00010000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style |= WS_THICKFRAME | WS_MAXIMIZEBOX
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
            # Force the frame change to take effect
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER,
            )
            # ── DWM rounded corners (Win11+) ──
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33,                                   # DWMWA_WINDOW_CORNER_PREFERENCE
                ctypes.byref(ctypes.c_int(2)),              # DWMWCP_ROUND
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass


def _apply_win_taskbar_icon(hwnd: int, ico_path: str) -> None:
    try:
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x10
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        user32 = ctypes.windll.user32
        hbig = user32.LoadImageW(None, ico_path, IMAGE_ICON, 256, 256, LR_LOADFROMFILE)
        hsml = user32.LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        if hbig:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hbig)
        if hsml:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hsml)
    except Exception:
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PolariceLabs.NOVATradingAI.Dashboard.1"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    _ensure_dashboard_fonts_loaded()
    app.setApplicationName("NOVA Trading AI")
    app.setFont(_ui_font(10))

    _ico_path = str(_BUNDLE / "nova_icon.ico")
    _icon = QIcon(_ico_path) if os.path.isfile(_ico_path) else QIcon()
    if not _icon.isNull():
        app.setWindowIcon(_icon)

    w = NOVADashboard()
    w.setWindowIcon(_icon)
    w.show()
    w._apply_win11_corners()
    if os.path.isfile(_ico_path):
        _apply_win_taskbar_icon(int(w.winId()), _ico_path)
    sys.exit(app.exec())
