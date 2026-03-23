from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import threading
import time


@dataclass(frozen=True)
class MT5ActionResult:
    ok: bool
    message: str
    closed: int = 0
    errors: int = 0
    symbol: str = ""
    last_error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class MT5DayMetrics:
    ok: bool
    symbol: str = ""
    trades: int = 0
    wins: int = 0
    losses: int = 0
    winrate: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    roi_pct: float = 0.0
    algo_enabled: bool = False
    balance: float = 0.0
    last_error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class MT5Service:
    def __init__(self, mt5_module=None):
        self._mt5 = mt5_module
        self._available = mt5_module is not None
        self._lock = threading.Lock()
        self._metrics_cache: dict[str, tuple[float, MT5DayMetrics]] = {}

    @staticmethod
    def _normalize_symbol_alias(raw_symbol: str) -> str:
        sym = str(raw_symbol or "").upper().strip()
        aliases = {
            "NAS100": "US30",
            "US30USD": "US30",
        }
        return aliases.get(sym, sym)

    @property
    def available(self) -> bool:
        return self._available and self._mt5 is not None

    def _resolve_symbol(self, mt5, raw_symbol: str) -> tuple[str, object | None]:
        sym = self._normalize_symbol_alias(raw_symbol)
        si = mt5.symbol_info(sym)
        if si is None:
            for suffix in ("m", ".a", ".e", ".i", ".raw", "_", ".pro", ".std"):
                candidate = f"{sym}{suffix}"
                si = mt5.symbol_info(candidate)
                if si is not None:
                    sym = candidate
                    break
        if si is None:
            matches = mt5.symbols_get(group=f"*{raw_symbol}*")
            if matches:
                sym = matches[0].name
                si = mt5.symbol_info(sym)
        return sym, si

    def _with_initialized_terminal(self):
        mt5 = self._mt5
        if not self.available:
            return None, "MetaTrader5 not available"
        if not mt5.initialize():
            return None, f"MT5 init error: {mt5.last_error()}"
        return mt5, ""

    def _terminal_trade_allowed(self, mt5) -> bool:
        info = mt5.terminal_info()
        return bool(getattr(info, "trade_allowed", False)) if info else False

    def _send_ctrl_e(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            handles: list[int] = []

            def _enum(hwnd, _lparam):
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length <= 0:
                    return True
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value or ""
                if "MetaTrader 5" in title or title.endswith(" - Demo") or title.endswith(" - Real"):
                    handles.append(hwnd)
                return True

            user32.EnumWindows(EnumWindowsProc(_enum), 0)
            if not handles:
                return False
            hwnd = handles[0]
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.15)

            VK_CONTROL = 0x11
            VK_E = 0x45
            KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_E, 0, 0, 0)
            user32.keybd_event(VK_E, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    def get_day_metrics(self, raw_symbol: str, *, refresh: bool = False) -> MT5DayMetrics:
        cache_key = self._normalize_symbol_alias(raw_symbol)
        with self._lock:
            cached = self._metrics_cache.get(cache_key)
            if cached and not refresh and (time.time() - cached[0]) < 2.5:
                return cached[1]

            mt5, error = self._with_initialized_terminal()
            if mt5 is None:
                metrics = MT5DayMetrics(ok=False, symbol=cache_key, last_error=error)
                self._metrics_cache[cache_key] = (time.time(), metrics)
                return metrics

            try:
                sym, si = self._resolve_symbol(mt5, raw_symbol)
                if si is None:
                    metrics = MT5DayMetrics(ok=False, symbol=cache_key, last_error=f"symbol not found: {raw_symbol}")
                    self._metrics_cache[cache_key] = (time.time(), metrics)
                    return metrics

                if not si.visible:
                    mt5.symbol_select(sym, True)

                now_local = datetime.now().astimezone()
                start_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
                deals = mt5.history_deals_get(start_day, now_local, group=f"*{sym}*")
                deals = list(deals or [])

                out_entries = {
                    getattr(mt5, "DEAL_ENTRY_OUT", 1),
                    getattr(mt5, "DEAL_ENTRY_OUT_BY", 3),
                }
                gross_profit = 0.0
                gross_loss = 0.0
                wins = 0
                losses = 0
                trades = 0
                for deal in deals:
                    if str(getattr(deal, "symbol", "") or "").upper() != sym.upper():
                        continue
                    pnl = (
                        float(getattr(deal, "profit", 0.0) or 0.0)
                        + float(getattr(deal, "swap", 0.0) or 0.0)
                        + float(getattr(deal, "commission", 0.0) or 0.0)
                        + float(getattr(deal, "fee", 0.0) or 0.0)
                    )
                    entry = getattr(deal, "entry", None)
                    if entry not in out_entries and abs(pnl) < 1e-9:
                        continue
                    trades += 1
                    if pnl > 0:
                        wins += 1
                        gross_profit += pnl
                    elif pnl < 0:
                        losses += 1
                        gross_loss += abs(pnl)

                net_profit = gross_profit - gross_loss
                winrate = (wins / trades * 100.0) if trades else 0.0
                account_info = mt5.account_info()
                balance = float(getattr(account_info, "balance", 0.0) or 0.0) if account_info else 0.0
                base_balance = balance - net_profit if balance else 0.0
                roi_pct = (net_profit / base_balance * 100.0) if base_balance not in (0.0, -0.0) else 0.0
                metrics = MT5DayMetrics(
                    ok=True,
                    symbol=sym,
                    trades=trades,
                    wins=wins,
                    losses=losses,
                    winrate=winrate,
                    gross_profit=gross_profit,
                    gross_loss=gross_loss,
                    net_profit=net_profit,
                    roi_pct=roi_pct,
                    algo_enabled=self._terminal_trade_allowed(mt5),
                    balance=balance,
                )
                self._metrics_cache[cache_key] = (time.time(), metrics)
                return metrics
            except Exception as ex:
                metrics = MT5DayMetrics(ok=False, symbol=cache_key, last_error=str(ex))
                self._metrics_cache[cache_key] = (time.time(), metrics)
                return metrics
            finally:
                try:
                    mt5.shutdown()
                except Exception:
                    pass

    def toggle_algo_trading(self, texts: dict, *, enable: bool | None = None) -> MT5ActionResult:
        if not self.available:
            return MT5ActionResult(False, texts["no_mt5"])

        with self._lock:
            mt5, error = self._with_initialized_terminal()
            if mt5 is None:
                return MT5ActionResult(False, f"⚠ {error}")
            try:
                before = self._terminal_trade_allowed(mt5)
            finally:
                try:
                    mt5.shutdown()
                except Exception:
                    pass

            if enable is not None and before == enable:
                msg = texts["algo_already_on"] if enable else texts["algo_already_off"]
                return MT5ActionResult(True, msg)

            if not self._send_ctrl_e():
                return MT5ActionResult(False, texts["algo_toggle_failed"])

            after = before
            for _ in range(8):
                time.sleep(0.35)
                mt5, _ = self._with_initialized_terminal()
                if mt5 is None:
                    continue
                try:
                    after = self._terminal_trade_allowed(mt5)
                finally:
                    try:
                        mt5.shutdown()
                    except Exception:
                        pass
                if after != before:
                    break

            if after == before:
                return MT5ActionResult(False, texts["algo_toggle_failed"])
            return MT5ActionResult(True, texts["algo_enabled"] if after else texts["algo_disabled"])

    def prepare_ea_injection(self, raw_symbol: str, bridge_path: str | Path | None, texts: dict) -> MT5ActionResult:
        bridge = Path(bridge_path) if bridge_path else None
        bridge_msg = str(bridge) if bridge else str(raw_symbol)
        if bridge and sys.platform == "win32":
            try:
                subprocess.Popen(["explorer", f"/select,{bridge}"])
            except Exception:
                pass

        if self.available:
            with self._lock:
                mt5, _ = self._with_initialized_terminal()
                if mt5 is not None:
                    try:
                        sym, si = self._resolve_symbol(mt5, raw_symbol)
                        if si is not None and not si.visible:
                            mt5.symbol_select(sym, True)
                    finally:
                        try:
                            mt5.shutdown()
                        except Exception:
                            pass

        return MT5ActionResult(False, texts["ea_manual_required"].format(sym=raw_symbol, bridge=bridge_msg))

    def close_profitable(self, raw_symbol: str, texts: dict) -> MT5ActionResult:
        if not self.available:
            return MT5ActionResult(False, texts["no_mt5"])

        sym = str(raw_symbol or "").upper()
        mt5 = self._mt5
        try:
            if not mt5.initialize():
                return MT5ActionResult(False, f"⚠ MT5 init error: {mt5.last_error()}")

            sym, si = self._resolve_symbol(mt5, raw_symbol)
            if si is None:
                return MT5ActionResult(False, texts["symbol_not_found"].format(sym=raw_symbol), symbol=str(raw_symbol))

            if not si.visible:
                mt5.symbol_select(sym, True)

            filling_candidates = []
            try:
                fm = getattr(si, "filling_mode", None)
                for mode in (
                    fm,
                    getattr(mt5, "ORDER_FILLING_RETURN", None),
                    getattr(mt5, "ORDER_FILLING_IOC", None),
                    getattr(mt5, "ORDER_FILLING_FOK", None),
                ):
                    if mode is not None and mode not in filling_candidates:
                        filling_candidates.append(mode)
            except Exception:
                filling_candidates = []
            if not filling_candidates:
                filling_candidates = [
                    mode for mode in (
                        getattr(mt5, "ORDER_FILLING_RETURN", None),
                        getattr(mt5, "ORDER_FILLING_IOC", None),
                        getattr(mt5, "ORDER_FILLING_FOK", None),
                    ) if mode is not None
                ]

            positions = mt5.positions_get(symbol=sym)
            if positions is None or len(positions) == 0:
                return MT5ActionResult(False, texts["no_positions"].format(sym=sym), symbol=sym)

            info = mt5.symbol_info_tick(sym)
            if info is None:
                return MT5ActionResult(False, texts["mt5_no_tick"].format(sym=sym), symbol=sym)

            profitable = [p for p in positions if p.profit > 0]
            if not profitable:
                return MT5ActionResult(False, texts["no_profit"].format(sym=sym), symbol=sym)

            closed = 0
            errors = 0
            last_err = ""
            for pos in profitable:
                close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                tick = mt5.symbol_info_tick(sym) or info
                price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
                res = None
                for filling in filling_candidates:
                    req = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": sym,
                        "volume": pos.volume,
                        "type": close_type,
                        "position": pos.ticket,
                        "price": price,
                        "deviation": 30,
                        "magic": pos.magic,
                        "comment": "NOVA_CLOSE_PROFIT",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": filling,
                    }
                    res = mt5.order_send(req)
                    if res and res.retcode in {
                        mt5.TRADE_RETCODE_DONE,
                        getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -1),
                    }:
                        closed += 1
                        break
                else:
                    errors += 1
                    rc = res.retcode if res else -1
                    cm = getattr(res, "comment", "") if res else "null"
                    last_err = f"[{rc}:{cm}]"

            message = texts["closed_result"].format(closed=closed, errors=errors, sym=sym)
            if errors > 0 and last_err:
                message += f" {last_err}"
            return MT5ActionResult(errors == 0, message, closed=closed, errors=errors, symbol=sym, last_error=last_err)
        except Exception as ex:
            return MT5ActionResult(False, f"❌ {ex}", symbol=sym)
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
