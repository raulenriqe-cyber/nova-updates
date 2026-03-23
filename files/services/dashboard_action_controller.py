from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .mt5_service import MT5Service
from .path_service import PathService
from .runtime_manager import RuntimeManager


@dataclass(frozen=True)
class DashboardActionOutcome:
    ok: bool
    message: str
    start_launching: bool = False


class DashboardActionController:
    def __init__(
        self,
        *,
        paths: PathService,
        runtime_manager: RuntimeManager,
        mt5_service: MT5Service,
        logger: Any = None,
    ):
        self.paths = paths
        self.runtime_manager = runtime_manager
        self.mt5_service = mt5_service
        self.logger = logger

    def launcher_available(self, runtime: dict) -> bool:
        pair_dir = self.paths.pair_dir(runtime)
        start_script = self.paths.start_script(runtime)
        return bool(pair_dir and start_script and start_script.exists())

    def launch(self, *, sym: str, runtime: dict, texts: dict) -> DashboardActionOutcome:
        start_script = self.paths.start_script(runtime)
        pair_dir = self.paths.pair_dir(runtime)
        if not start_script or not pair_dir or not start_script.exists():
            return DashboardActionOutcome(False, "⚠ No existe launcher para este par")
        try:
            result = self.runtime_manager.launch_pair(runtime)
            return DashboardActionOutcome(result.ok, result.message, start_launching=result.ok)
        except Exception as exc:
            if self.logger is not None:
                self.logger.exception("Launch error for %s", sym)
            return DashboardActionOutcome(False, texts["launch_error"].format(error=exc))

    def close_profitable(self, *, sym: str, texts: dict) -> DashboardActionOutcome:
        result = self.mt5_service.close_profitable(sym, texts)
        return DashboardActionOutcome(result.ok, result.message)

    def toggle_algo_trading(self, *, texts: dict) -> DashboardActionOutcome:
        result = self.mt5_service.toggle_algo_trading(texts)
        return DashboardActionOutcome(result.ok, result.message)

    def prepare_ea_injection(self, *, sym: str, runtime: dict, texts: dict) -> DashboardActionOutcome:
        bridge_paths = self.paths.bridge_paths(runtime)
        bridge = bridge_paths[0] if bridge_paths else None
        result = self.mt5_service.prepare_ea_injection(sym, bridge, texts)
        return DashboardActionOutcome(result.ok, result.message)

    def stop(self, *, sym: str, runtime: dict, texts: dict) -> DashboardActionOutcome:
        pair_dir = self.paths.pair_dir(runtime)
        prefix = runtime.get("prefix")
        if not pair_dir or not prefix:
            return DashboardActionOutcome(False, texts["no_stop_routine"])
        try:
            result = self.runtime_manager.stop_pair(sym, runtime)
            return DashboardActionOutcome(result.ok, result.message)
        except Exception as exc:
            if self.logger is not None:
                self.logger.exception("Stop error for %s", sym)
            return DashboardActionOutcome(False, f"❌ Error al detener: {exc}")