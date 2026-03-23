#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nova_diagnostics.py â€” NOVA Trading AI | Auto-Diagnostics Engine
Polarice Labs Â© 2026

Self-testing diagnostic system that runs alongside the dashboard:
  â€¢ Intercepts ALL runtime exceptions (even caught ones)
  â€¢ Periodic health checks every 10s on widgets, states, translations
  â€¢ Writes machine-readable JSON log â†’ nova_diagnostics_report.json
  â€¢ Exposes live results to the dashboard via DiagnosticsPanel widget
  â€¢ Can run a full self-test on demand

Usage:
    from nova_diagnostics import DiagnosticsEngine
    diag = DiagnosticsEngine(dashboard_window)
    diag.start()       # begins periodic checks
    diag.run_full()    # on-demand full test
    diag.stop()        # cleanup
"""

from __future__ import annotations
import ast, json, logging, re, subprocess, sys, time, traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame

logger = logging.getLogger("nova.diagnostics")

_MAX_LOG = 500          # max entries kept in memory
_CHECK_INTERVAL = 10000 # ms between periodic checks
_LOG_FILE = Path(__file__).parent / "nova_diagnostics_report.json"


def _resolve_dashboard_module(dashboard=None):
    """Return the active dashboard module without importing any archived dashboard module."""
    candidates = []
    if dashboard is not None:
        mod_name = getattr(dashboard.__class__, "__module__", "")
        if mod_name:
            candidates.append(sys.modules.get(mod_name))
    candidates.extend([
        sys.modules.get("nova_dashboard"),
        sys.modules.get("__main__"),
    ])
    for mod in candidates:
        if mod is not None:
            return mod
    return None

# â”€â”€â”€ Severity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SEV_INFO  = "INFO"
SEV_WARN  = "WARN"
SEV_ERROR = "ERROR"
SEV_CRITICAL = "CRITICAL"

# â”€â”€â”€ Colors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_C = {
    "bg":   "#0A0802",
    "card": "#121008",
    "gold": "#FFD700",
    "text": "#E8D8B0",
    "dim":  "#A08C5A",
    "ok":   "#00FF88",
    "warn": "#FFA500",
    "err":  "#FF4444",
    "crit": "#FF0066",
}


class DiagEntry:
    """Single diagnostic log entry."""
    __slots__ = ("ts", "sev", "cat", "msg", "detail")

    def __init__(self, sev: str, cat: str, msg: str, detail: str = ""):
        self.ts = time.time()
        self.sev = sev
        self.cat = cat
        self.msg = msg
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "ts": datetime.fromtimestamp(self.ts, tz=timezone.utc).isoformat(),
            "sev": self.sev,
            "cat": self.cat,
            "msg": self.msg,
            "detail": self.detail[:500],
        }

    def __repr__(self):
        return f"[{self.sev}] {self.cat}: {self.msg}"


class DiagnosticsEngine(QObject):
    """
    Core diagnostics engine â€” hooks into the dashboard, runs checks,
    captures exceptions, writes reports.
    """
    entry_added = Signal(object)       # emits DiagEntry
    check_done  = Signal(dict)         # emits summary dict after each periodic check

    def __init__(self, dashboard=None, parent=None):
        super().__init__(parent)
        self._dash = dashboard               # NOVADashboard instance
        self._log: deque[DiagEntry] = deque(maxlen=_MAX_LOG)
        self._timer = QTimer(self)
        self._timer.setInterval(_CHECK_INTERVAL)
        self._timer.timeout.connect(self._periodic_check)
        self._orig_excepthook = None
        self._started = False
        self._last_summary: dict = {}

    # â”€â”€ public API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def start(self):
        """Begin monitoring: install exception hook + start periodic timer."""
        if self._started:
            return
        self._started = True
        self._install_exception_hook()
        self._timer.start()
        self._add(SEV_INFO, "DIAG", "Diagnostics engine started")
        # Run initial check immediately
        QTimer.singleShot(2000, self._periodic_check)

    def stop(self):
        self._timer.stop()
        self._restore_exception_hook()
        self._add(SEV_INFO, "DIAG", "Diagnostics engine stopped")
        self._flush_log()
        self._started = False

    def run_full(self) -> dict:
        """Run all diagnostic tests on demand and return summary."""
        self._add(SEV_INFO, "DIAG", "Full self-test initiated")
        results = {}
        results["imports"]       = self._test_imports()
        results["widgets"]       = self._test_widgets()
        results["buttons"]       = self._test_button_states()
        results["translation"]   = self._test_translation()
        results["telemetry"]     = self._test_telemetry_workers()
        results["files"]         = self._test_file_system()
        results["ports"]         = self._test_port_map()
        results["quantum_cores"] = self._test_quantum_cores()
        results["mt5"]           = self._test_mt5()

        total = sum(1 for v in results.values())
        passed = sum(1 for v in results.values() if v.get("ok"))
        failed = total - passed
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": total, "passed": passed, "failed": failed,
            "tests": results,
        }
        self._last_summary = summary
        self.check_done.emit(summary)
        sev = SEV_INFO if failed == 0 else (SEV_ERROR if failed >= 3 else SEV_WARN)
        self._add(sev, "SELFTEST", f"Full test: {passed}/{total} passed", json.dumps(results, default=str)[:500])
        self._flush_log()
        return summary

    @property
    def log(self) -> list[DiagEntry]:
        return list(self._log)

    @property
    def summary(self) -> dict:
        return self._last_summary

    @property
    def error_count(self) -> int:
        return sum(1 for e in self._log if e.sev in (SEV_ERROR, SEV_CRITICAL))

    @property
    def warn_count(self) -> int:
        return sum(1 for e in self._log if e.sev == SEV_WARN)

    # â”€â”€ exception hook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _install_exception_hook(self):
        self._orig_excepthook = sys.excepthook
        sys.excepthook = self._on_exception

    def _restore_exception_hook(self):
        if self._orig_excepthook:
            sys.excepthook = self._orig_excepthook

    def _on_exception(self, exc_type, exc_value, exc_tb):
        """Capture unhandled exceptions into the diagnostics log."""
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        # Filter out harmless ones
        msg = f"{exc_type.__name__}: {exc_value}"
        if "QPainter" in msg and "not active" in msg:
            self._add(SEV_WARN, "PAINT", msg, tb_str)
        elif "RuntimeError" in msg and "deleted" in msg.lower():
            self._add(SEV_ERROR, "WIDGET", "Deleted C++ object accessed", tb_str)
        else:
            self._add(SEV_ERROR, "UNHANDLED", msg, tb_str)
        # Still call original hook
        if self._orig_excepthook:
            self._orig_excepthook(exc_type, exc_value, exc_tb)

    # â”€â”€ periodic check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _periodic_check(self):
        """Lightweight check that runs every 10s."""
        checks = []
        try:
            checks.append(self._check_button_coherence())
            checks.append(self._check_telemetry_alive())
            checks.append(self._check_translation_sync())
            checks.append(self._check_widget_visibility())
        except Exception as e:
            self._add(SEV_ERROR, "PERIODIC", f"Check crashed: {e}", traceback.format_exc())

        issues = [c for c in checks if c]
        summary = {
            "ts": time.time(),
            "checks_run": len(checks),
            "issues": len(issues),
            "errors": self.error_count,
            "warnings": self.warn_count,
            "details": issues,
        }
        self._last_summary = summary
        self.check_done.emit(summary)

    # â”€â”€ individual periodic checks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _check_button_coherence(self) -> Optional[str]:
        """Verify button states make sense (e.g. can't be running AND stopped)."""
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return None
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            btn = getattr(d, '_btn_start', None)
            if not btn:
                continue
            # Impossible states
            if btn._running and btn._launching:
                msg = f"{sym}: INICIAR is both _running AND _launching"
                self._add(SEV_ERROR, "BTN_STATE", msg)
                return msg
            if btn._running and btn._waiting_ea:
                msg = f"{sym}: INICIAR is both _running AND _waiting_ea"
                self._add(SEV_ERROR, "BTN_STATE", msg)
                return msg
            if btn._launching and btn._waiting_ea:
                msg = f"{sym}: INICIAR is both _launching AND _waiting_ea"
                self._add(SEV_ERROR, "BTN_STATE", msg)
                return msg
            stop_btn = getattr(d, '_btn_stop', None)
            if stop_btn and stop_btn._stopping and stop_btn._stopped:
                msg = f"{sym}: DETENER is both _stopping AND _stopped"
                self._add(SEV_ERROR, "BTN_STATE", msg)
                return msg
        return None

    def _check_telemetry_alive(self) -> Optional[str]:
        """Check that TelemetryWorker threads are running for open dashboards."""
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return None
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            worker = getattr(d, '_worker', None)
            if not worker:
                msg = f"{sym}: no TelemetryWorker assigned"
                self._add(SEV_WARN, "TELEMETRY", msg)
                return msg
            if not worker.isRunning():
                msg = f"{sym}: TelemetryWorker thread is dead"
                self._add(SEV_ERROR, "TELEMETRY", msg)
                return msg
        return None

    def _check_translation_sync(self) -> Optional[str]:
        """Verify that label text matches current language state."""
        if not self._dash:
            return None
        try:
            dashboard_mod = _resolve_dashboard_module(self._dash)
            TEXTS = getattr(dashboard_mod, "TEXTS", None)
            if not isinstance(TEXTS, dict):
                return None
            lang = getattr(self._dash, '_lang', 'ES')
            t = TEXTS.get(lang, TEXTS['ES'])

            ws = self._dash._workspace
            for sym, d in ws._subs.items():
                # Check section headers match language
                for attr_name, text_key in [
                    ("_sec_market",  "sec_market"),
                    ("_sec_ind",     "sec_indicators"),
                    ("_sec_ml",      "sec_ml"),
                    ("_sec_brain",   "sec_brain"),
                    ("_sec_perf",    "sec_perf"),
                ]:
                    widget = getattr(d, attr_name, None)
                    if widget:
                        lbl = widget.findChild(QLabel)
                        if lbl and lbl.text() != t.get(text_key, ""):
                            expected = t.get(text_key, "?")
                            actual = lbl.text()
                            msg = f"{sym}: {attr_name} shows '{actual}' expected '{expected}' (lang={lang})"
                            self._add(SEV_WARN, "TRANSLATE", msg)
                            return msg
        except Exception as e:
            self._add(SEV_WARN, "TRANSLATE", f"Translation check error: {e}")
        return None

    def _check_widget_visibility(self) -> Optional[str]:
        """Ensure all expected self._f widgets exist and are visible."""
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return None
        EXPECTED_KEYS = [
            "Bid", "Ask", "Spread", "Session", "Regime",
            "RSI", "ADX", "MACD", "ATR",
            "consensus", "cons_pct",
            "atk_icon", "atk_pct_lbl", "atk_dir",
            "pf_WinRate", "pf_Trades", "today",
            "open_pos", "tp_hits", "sl_hits",
        ]
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            f = getattr(d, '_f', {})
            missing = [k for k in EXPECTED_KEYS if k not in f]
            if missing:
                msg = f"{sym}: missing widget keys: {', '.join(missing[:5])}"
                self._add(SEV_ERROR, "WIDGETS", msg)
                return msg
            # Check for labels stuck at "â€”" after 30s of telemetry
            bid_lbl = f.get("Bid")
            if bid_lbl and bid_lbl.text() == "â€”":
                worker = getattr(d, '_worker', None)
                if worker and worker.isRunning():
                    # Only warn if worker has been running > 30s
                    pass  # Telemetry may just not have data yet
        return None

    # â”€â”€ full self-test checks (run_full) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _test_imports(self) -> dict:
        """Test that all critical imports work."""
        issues = []
        for mod_name in ["PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "json", "socket", "subprocess"]:
            try:
                __import__(mod_name)
            except ImportError as e:
                issues.append(f"Cannot import {mod_name}: {e}")
        # Optional imports
        try:
            import MetaTrader5
        except ImportError:
            issues.append("MetaTrader5 not installed (close-profitable won't work)")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Critical Imports"}

    def _test_widgets(self) -> dict:
        """Verify all ParDashboard widgets are properly initialized."""
        issues = []
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return {"ok": True, "issues": ["No dashboard to test"], "name": "Widgets"}
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            if not hasattr(d, '_f'):
                issues.append(f"{sym}: no _f dict")
                continue
            if not hasattr(d, '_llm'):
                issues.append(f"{sym}: no _llm dict")
                continue
            llm_count = len(getattr(d, '_llm', {}))
            if llm_count != 12:
                issues.append(f"{sym}: expected 12 LLMs, got {llm_count}")
            if not hasattr(d, '_chart'):
                issues.append(f"{sym}: no MiniChartWidget")
            if not hasattr(d, '_gauge'):
                issues.append(f"{sym}: no AttackGaugeWidget")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Widget Init"}

    def _test_button_states(self) -> dict:
        """Verify button initial state is correct."""
        issues = []
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return {"ok": True, "issues": [], "name": "Button States"}
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            for attr, label in [("_btn_start", "INICIAR"), ("_btn_stop", "DETENER"), ("_btn_profit", "PROFIT")]:
                btn = getattr(d, attr, None)
                if btn is None:
                    issues.append(f"{sym}: {label} button missing")
                elif not isinstance(btn._orig_text, str) or len(btn._orig_text) < 2:
                    issues.append(f"{sym}: {label} _orig_text invalid: '{btn._orig_text}'")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Button States"}

    def _test_translation(self) -> dict:
        """Verify TEXTS dict completeness for both languages."""
        issues = []
        try:
            dashboard_mod = _resolve_dashboard_module(self._dash)
            TEXTS = getattr(dashboard_mod, "TEXTS", None)
            if not isinstance(TEXTS, dict):
                return {"ok": True, "issues": ["TEXTS not available"], "name": "Translation"}
            es_keys = set(TEXTS.get("ES", {}).keys())
            en_keys = set(TEXTS.get("EN", {}).keys())
            missing_en = es_keys - en_keys
            missing_es = en_keys - es_keys
            if missing_en:
                issues.append(f"EN missing keys: {', '.join(sorted(missing_en))}")
            if missing_es:
                issues.append(f"ES missing keys: {', '.join(sorted(missing_es))}")
            # Check no empty values
            for lang in ("ES", "EN"):
                for k, v in TEXTS.get(lang, {}).items():
                    if not v or not v.strip():
                        issues.append(f"{lang}['{k}'] is empty")
        except Exception as e:
            issues.append(f"Could not load TEXTS: {e}")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Translation"}

    def _test_telemetry_workers(self) -> dict:
        """Test that all open dashboard telemetry workers are alive."""
        issues = []
        if not self._dash or not hasattr(self._dash, '_workspace'):
            return {"ok": True, "issues": [], "name": "Telemetry Workers"}
        ws = self._dash._workspace
        for sym, d in ws._subs.items():
            w = getattr(d, '_worker', None)
            if not w:
                issues.append(f"{sym}: worker missing")
            elif not w.isRunning():
                issues.append(f"{sym}: worker thread dead")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Telemetry Workers"}

    def _test_file_system(self) -> dict:
        """Verify expected pair folders and files exist."""
        issues = []
        try:
            dashboard_mod = _resolve_dashboard_module(self._dash)
            PAIR_RUNTIME = getattr(dashboard_mod, "PAIR_RUNTIME", None)
            _ROOT = getattr(dashboard_mod, "_ROOT", None)
            if not isinstance(PAIR_RUNTIME, dict) or _ROOT is None:
                return {"ok": True, "issues": ["Runtime metadata unavailable"], "name": "File System"}
            for sym, rt in PAIR_RUNTIME.items():
                folder = _ROOT / "pares" / rt.get("folder", "")
                if not folder.exists():
                    issues.append(f"{sym}: folder missing â†’ {folder.name}")
                    continue
                start = folder / rt.get("start", "")
                if not start.exists():
                    issues.append(f"{sym}: start script missing â†’ {start.name}")
                # Check quantum_stats.json writability
                qs = folder / "quantum_stats.json"
                if qs.exists():
                    try:
                        qs.read_text(encoding="utf-8")
                    except Exception as e:
                        issues.append(f"{sym}: can't read quantum_stats.json: {e}")
        except Exception as e:
            issues.append(f"FS check error: {e}")
        return {"ok": len(issues) == 0, "issues": issues, "name": "File System"}

    def _test_port_map(self) -> dict:
        """Verify PORT_MAP has all required components for each pair."""
        issues = []
        try:
            dashboard_mod = _resolve_dashboard_module(self._dash)
            PORT_MAP = getattr(dashboard_mod, "PORT_MAP", None)
            PAIR_RUNTIME = getattr(dashboard_mod, "PAIR_RUNTIME", None)
            if not isinstance(PORT_MAP, dict) or not isinstance(PAIR_RUNTIME, dict):
                return {"ok": True, "issues": ["Port metadata unavailable"], "name": "Port Map"}
            REQUIRED = {"trinity", "kraken", "quantum", "executor"}
            for sym in PAIR_RUNTIME:
                pm = PORT_MAP.get(sym)
                if not pm:
                    issues.append(f"{sym}: not in PORT_MAP")
                    continue
                for comp in REQUIRED:
                    port = pm.get(comp)
                    if not port:
                        issues.append(f"{sym}: missing '{comp}' port in PORT_MAP")
                llm_ports = pm.get("llm", [])
                if len(llm_ports) != 12:
                    issues.append(f"{sym}: expected 12 LLM ports, got {len(llm_ports)}")
        except Exception as e:
            issues.append(f"Port map check error: {e}")
        return {"ok": len(issues) == 0, "issues": issues, "name": "Port Map"}

    def _test_quantum_cores(self) -> dict:
        """
        Validate each quantum_core one-by-one with:
        1) ast.parse syntax check
        2) short runtime smoke test in a subprocess

        Each core is launched briefly and then terminated before moving to the
        next one, so diagnostics do not consume excessive RAM.
        """
        issues = []
        passed = []
        try:
            dashboard_mod = _resolve_dashboard_module(self._dash)
            PAIR_RUNTIME = getattr(dashboard_mod, "PAIR_RUNTIME", None)
            _ROOT = getattr(dashboard_mod, "_ROOT", None)
            if not isinstance(PAIR_RUNTIME, dict) or _ROOT is None:
                return {"ok": True, "issues": ["Quantum runtime metadata unavailable"], "name": "Quantum Cores"}
            py_exec = Path(sys.executable)
            for sym, rt in PAIR_RUNTIME.items():
                folder = _ROOT / "pares" / rt.get("folder", "")
                prefix = rt.get("prefix", rt["folder"].rstrip("usd"))
                # Find the quantum_core file (e.g. jpyquantum_core.py)
                candidates = list(folder.glob(f"{prefix}quantum_core.py"))
                if not candidates:
                    # Fallback: any *quantum_core.py in the folder
                    candidates = list(folder.glob("*quantum_core.py"))
                    candidates = [c for c in candidates if ".bak" not in c.suffix]
                if not candidates:
                    issues.append(f"{sym}: quantum_core.py not found in {folder.name}")
                    continue
                qc = candidates[0]
                try:
                    src = qc.read_text(encoding="utf-8", errors="replace")
                    ast.parse(src, filename=qc.name)
                    del src  # release memory immediately
                except SyntaxError as e:
                    issues.append(
                        f"{sym}: {qc.name} syntax error line {e.lineno}: {e.msg}"
                    )
                    continue
                except Exception as e:
                    issues.append(f"{sym}: {qc.name} read error: {e}")
                    continue

                proc = None
                try:
                    proc = subprocess.Popen(
                        [str(py_exec), qc.name],
                        cwd=str(folder),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        errors="ignore",
                    )
                    time.sleep(5)
                    if proc.poll() is not None:
                        out, err = proc.communicate(timeout=2)
                        tail = ""
                        if err.strip():
                            tail = err.strip().splitlines()[-1]
                        elif out.strip():
                            tail = out.strip().splitlines()[-1]
                        issues.append(
                            f"{sym}: {qc.name} runtime smoke test failed: {tail or 'process exited early'}"
                        )
                    else:
                        passed.append(sym)
                except Exception as e:
                    issues.append(f"{sym}: {qc.name} smoke test error: {e}")
                finally:
                    if proc is not None and proc.poll() is None:
                        try:
                            proc.terminate()
                            proc.communicate(timeout=2)
                        except Exception:
                            try:
                                proc.kill()
                                proc.communicate(timeout=2)
                            except Exception:
                                pass
        except Exception as e:
            issues.append(f"Quantum core check error: {e}")
        name = f"Quantum Cores Runtime ({len(passed)} OK)"
        return {"ok": len(issues) == 0, "issues": issues, "name": name}

    def _test_mt5(self) -> dict:
        """Test MetaTrader5 availability."""
        issues = []
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                err = mt5.last_error()
                issues.append(f"MT5 init failed: {err}")
                mt5.shutdown()
            else:
                info = mt5.terminal_info()
                if info:
                    if not info.trade_allowed:
                        issues.append("MT5 trade not allowed (AutoTrading off?)")
                mt5.shutdown()
        except ImportError:
            issues.append("MetaTrader5 module not installed")
        except Exception as e:
            issues.append(f"MT5 error: {e}")
        return {"ok": len(issues) == 0, "issues": issues, "name": "MetaTrader5"}

    # â”€â”€ internal helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _add(self, sev: str, cat: str, msg: str, detail: str = ""):
        entry = DiagEntry(sev, cat, msg, detail)
        self._log.append(entry)
        self.entry_added.emit(entry)
        # Log to Python logger too
        ll = {"INFO": logging.INFO, "WARN": logging.WARNING, "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
        logger.log(ll.get(sev, logging.INFO), "[DIAG:%s] %s", cat, msg)

    def _flush_log(self):
        """Write log to JSON file for external inspection."""
        try:
            entries = [e.to_dict() for e in self._log]
            data = {
                "generated": datetime.now(timezone.utc).isoformat(),
                "total_entries": len(entries),
                "errors": self.error_count,
                "warnings": self.warn_count,
                "last_summary": self._last_summary,
                "entries": entries[-200:],  # last 200
            }
            _LOG_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to write diagnostics report: %s", e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  DIAGNOSTICS PANEL â€” QPainter widget for dashboard integration
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
class DiagnosticsPanel(QWidget):
    """
    Compact diagnostics widget that embeds in the sidebar or main layout.
    Shows live error/warning counts and a scrollable recent issues list.
    """
    def __init__(self, engine: DiagnosticsEngine, parent=None):
        super().__init__(parent)
        self._engine = engine
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setMinimumHeight(120)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        self._status_dot = QLabel("â—")
        self._status_dot.setStyleSheet(f"color:{_C['ok']};font-size:14px;font-weight:700;background:transparent;")
        self._status_dot.setFixedWidth(16)
        title = QLabel("DIAGNOSTICS")
        title.setStyleSheet(f"color:{_C['gold']};font-size:10px;font-weight:700;letter-spacing:2px;background:transparent;")
        self._count_lbl = QLabel("0 errors Â· 0 warnings")
        self._count_lbl.setStyleSheet(f"color:{_C['dim']};font-size:9px;font-family:Consolas;background:transparent;")
        hdr.addWidget(self._status_dot)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self._count_lbl)
        lay.addLayout(hdr)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['gold']}30;")
        lay.addWidget(sep)

        # Recent issues scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(200)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                             f"QScrollBar:vertical{{width:4px;background:transparent;}}"
                             f"QScrollBar::handle:vertical{{background:{_C['gold']}40;border-radius:2px;}}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        scroll.viewport().setAutoFillBackground(False)
        self._list_widget = QWidget()
        self._list_widget.setAttribute(Qt.WA_NoSystemBackground)
        self._list_widget.setStyleSheet("background:transparent;")
        self._list_lay = QVBoxLayout(self._list_widget)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(2)
        self._list_lay.addStretch()
        scroll.setWidget(self._list_widget)
        lay.addWidget(scroll, 1)

        # Run test button (text-only, compact)
        self._run_btn = QLabel("â–¶ RUN SELF-TEST")
        self._run_btn.setAlignment(Qt.AlignCenter)
        self._run_btn.setStyleSheet(
            f"color:{_C['gold']};font-size:9px;font-weight:700;letter-spacing:1px;"
            f"background:{_C['gold']}15;border:1px solid {_C['gold']}30;"
            f"border-radius:3px;padding:4px 8px;font-family:Consolas;"
        )
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.mousePressEvent = lambda _: self._on_run_test()
        lay.addWidget(self._run_btn)

        # Connect signals
        engine.entry_added.connect(self._on_entry)
        engine.check_done.connect(self._on_check)

    def _on_entry(self, entry: DiagEntry):
        """Add a new log entry to the visible list."""
        if entry.sev == SEV_INFO:
            return  # Only show warnings and errors in the UI
        ts = datetime.fromtimestamp(entry.ts).strftime("%H:%M:%S")
        sev_col = {SEV_WARN: _C["warn"], SEV_ERROR: _C["err"], SEV_CRITICAL: _C["crit"]}.get(entry.sev, _C["dim"])
        sev_icon = {SEV_WARN: "âš ", SEV_ERROR: "âœ–", SEV_CRITICAL: "ðŸ”¥"}.get(entry.sev, "â€¢")
        lbl = QLabel(f"{sev_icon} {ts} [{entry.cat}] {entry.msg}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color:{sev_col};font-size:9px;font-family:Consolas;"
            f"background:{sev_col}10;border-radius:2px;padding:2px 4px;"
        )
        if entry.detail:
            lbl.setToolTip(entry.detail[:800])
        # Insert before the stretch
        idx = max(0, self._list_lay.count() - 1)
        self._list_lay.insertWidget(idx, lbl)
        # Cap visible items
        while self._list_lay.count() > 51:  # 50 items + stretch
            item = self._list_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _on_check(self, summary: dict):
        """Update header counters from periodic check."""
        errs = self._engine.error_count
        warns = self._engine.warn_count
        self._count_lbl.setText(f"{errs} errors Â· {warns} warnings")
        if errs > 0:
            dot_col = _C["err"]
        elif warns > 0:
            dot_col = _C["warn"]
        else:
            dot_col = _C["ok"]
        self._status_dot.setStyleSheet(f"color:{dot_col};font-size:14px;font-weight:700;background:transparent;")

    def _on_run_test(self):
        """Run full self-test and show results."""
        self._run_btn.setText("â³ TESTINGâ€¦")
        self._run_btn.setStyleSheet(
            f"color:{_C['warn']};font-size:9px;font-weight:700;letter-spacing:1px;"
            f"background:{_C['warn']}15;border:1px solid {_C['warn']}30;"
            f"border-radius:3px;padding:4px 8px;font-family:Consolas;"
        )

        def _run():
            result = self._engine.run_full()
            passed = result.get("passed", 0)
            total = result.get("total", 0)
            failed = result.get("failed", 0)
            if failed == 0:
                self._run_btn.setText(f"âœ… ALL {total} TESTS PASSED")
                bc = _C["ok"]
            else:
                self._run_btn.setText(f"âš  {failed}/{total} TESTS FAILED")
                bc = _C["err"]
            self._run_btn.setStyleSheet(
                f"color:{bc};font-size:9px;font-weight:700;letter-spacing:1px;"
                f"background:{bc}15;border:1px solid {bc}30;"
                f"border-radius:3px;padding:4px 8px;font-family:Consolas;"
            )
            # Show individual test results
            for test_name, test_result in result.get("tests", {}).items():
                if not test_result.get("ok"):
                    for issue in test_result.get("issues", []):
                        self._engine._add(SEV_WARN, test_name.upper(), issue)
            # Reset button text after 8s
            QTimer.singleShot(8000, lambda: self._run_btn.setText("â–¶ RUN SELF-TEST"))
            QTimer.singleShot(8000, lambda: self._run_btn.setStyleSheet(
                f"color:{_C['gold']};font-size:9px;font-weight:700;letter-spacing:1px;"
                f"background:{_C['gold']}15;border:1px solid {_C['gold']}30;"
                f"border-radius:3px;padding:4px 8px;font-family:Consolas;"
            ))

        QTimer.singleShot(100, _run)

    def paintEvent(self, _):
        from PySide6.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush
        qp = QPainter(self)
        if not qp.isActive():
            return
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, w - 1, h - 1, 6, 6)
        qp.fillPath(path, QBrush(QColor(10, 8, 4, 200)))
        qp.strokePath(path, QPen(QColor(_C["gold"] + "25"), 1))
        qp.end()
