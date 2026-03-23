from __future__ import annotations

import ctypes
import ctypes.wintypes
from dataclasses import asdict, dataclass, field
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from .path_service import PathService
from .runtime_models import RuntimeActionResult


@dataclass(frozen=True)
class RuntimeState:
    sym: str
    supported: bool
    pair_dir_exists: bool
    start_script_exists: bool
    executor_alive: bool
    stats_fresh: bool
    running: bool
    live_pid: int | None
    process_alive: bool
    process_count: int
    stats_age: float | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeSnapshot:
    sym: str
    ts: float
    stats: dict = field(default_factory=dict)
    stats_age: float | None = None
    live_pid: int | None = None
    memoria: dict = field(default_factory=dict)
    tcp: dict = field(default_factory=dict)
    tcp_llm: list = field(default_factory=list)
    runtime_state: RuntimeState | None = None
    processes: list[dict] = field(default_factory=list)
    pair_dir: str | None = None

    def to_payload(self) -> dict:
        payload = asdict(self)
        if self.runtime_state is not None:
            payload["runtime_state"] = self.runtime_state.to_dict()
        return payload


class RuntimeManager:
    def __init__(self, paths: PathService, port_map: dict, folder_to_symbol: dict, pair_runtime_hints: dict):
        self.paths = paths
        self.port_map = port_map
        self.folder_to_symbol = folder_to_symbol
        self.pair_runtime_hints = pair_runtime_hints
        self._proc_cache_lock = threading.Lock()
        self._proc_cache_ts = 0.0
        self._proc_cache_data: list[dict] = []

    @staticmethod
    def _hidden_subprocess_kwargs() -> dict:
        if sys.platform != "win32":
            return {}
        kwargs = {
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        }
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            kwargs["startupinfo"] = startupinfo
        except Exception:
            pass
        return kwargs

    def discover_pair_runtime(self) -> dict:
        pairs_dir = self.paths.pairs_dir
        if not pairs_dir.exists():
            return {}
        discovered = {}
        for child in sorted(pairs_dir.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            name = child.name.lower()
            if name.startswith("__") or "backup" in name or "snake edition" in name:
                continue
            quantum_files = [p for p in child.glob("*quantum_core.py") if ".bak" not in p.name.lower()]
            if not quantum_files:
                continue
            start_files = [p for p in child.glob("*start.bat") if p.name.upper() != "START_SYSTEM.BAT"]
            if not start_files:
                continue
            quantum_files.sort(key=lambda p: (len(p.name), p.name.lower()))
            start_files.sort(key=lambda p: (len(p.name), p.name.lower()))
            qc = quantum_files[0]
            start = start_files[0]
            prefix = qc.stem[:-len("quantum_core")] if qc.stem.endswith("quantum_core") else qc.stem
            sym = self.folder_to_symbol.get(child.name.lower())
            hint = self.pair_runtime_hints.get(sym, {}) if sym else {}
            if not sym:
                stats_path = child / "quantum_stats.json"
                if stats_path.exists():
                    try:
                        stats_raw = json.loads(stats_path.read_text(encoding="utf-8", errors="ignore") or "{}")
                        guessed = str(stats_raw.get("symbol") or stats_raw.get("sym") or "").upper().strip()
                        if guessed:
                            sym = guessed
                    except Exception:
                        pass
            if not sym:
                sym = child.name.upper()
            runtime = {
                "folder": child.name.lower(),
                "start": hint.get("start", start.name),
                "prefix": hint.get("prefix", prefix),
                "pid": hint.get("pid", f"{prefix}quantum_core.pid"),
            }
            if hint.get("pid_candidates"):
                runtime["pid_candidates"] = list(hint["pid_candidates"])
            discovered[sym] = runtime
        return discovered

    def pair_runtime_status(self, sym: str, runtime: dict) -> bool:
        return self.runtime_state(sym, runtime).running

    def live_symbols(self, pairs: list[dict], runtime_map: dict) -> list[str]:
        live_syms = []
        for pair in pairs:
            sym = pair.get("sym")
            if sym and self.pair_runtime_status(sym, runtime_map.get(sym, {})):
                live_syms.append(sym)
        return sorted(live_syms)

    def collect_pair_snapshot(self, sym: str, runtime: dict) -> dict:
        pair_dir = self.paths.pair_dir(runtime)
        stats, stats_age = self.read_stats(runtime)
        memoria = self.read_memoria(sym, runtime)
        processes = self.find_matching_processes(runtime)
        process_pid = self.primary_process_pid(runtime)
        live_pid = process_pid or self.find_live_pid(runtime)
        pm = self.port_map.get(sym, {})
        tcp = {
            key: (self.probe(port) if port else None)
            for key in ("trinity", "kraken", "sound", "executor")
            for port in [pm.get(key)]
        }
        tcp_llm = [self.probe(port) if port else None for port in pm.get("llm", [])]
        runtime_state = self.runtime_state(
            sym,
            runtime,
            stats_age=stats_age,
            live_pid=live_pid,
            tcp=tcp,
            process_count=len(processes),
            process_alive=bool(processes),
        )
        snapshot = RuntimeSnapshot(
            sym=sym,
            ts=time.time(),
            stats=stats,
            stats_age=stats_age,
            live_pid=live_pid,
            memoria=memoria,
            tcp=tcp,
            tcp_llm=tcp_llm,
            runtime_state=runtime_state,
            processes=processes,
            pair_dir=str(pair_dir) if pair_dir else None,
        )
        return snapshot.to_payload()

    def runtime_state(
        self,
        sym: str,
        runtime: dict,
        *,
        stats_age: float | None = None,
        live_pid: int | None = None,
        tcp: dict | None = None,
        process_count: int | None = None,
        process_alive: bool | None = None,
    ) -> RuntimeState:
        pair_dir = self.paths.pair_dir(runtime)
        start_script = self.paths.start_script(runtime)
        supported = bool(pair_dir and start_script and start_script.exists())
        executor_alive = bool((tcp or {}).get("executor", False)) if isinstance(tcp, dict) else False
        stats_fresh = stats_age is not None and stats_age <= 20
        if process_alive is None:
            process_pid = self.primary_process_pid(runtime)
            process_alive = process_pid is not None
            if live_pid is None:
                live_pid = process_pid or self.find_live_pid(runtime)
        running = bool(process_alive or live_pid is not None or stats_fresh or executor_alive)
        return RuntimeState(
            sym=sym,
            supported=supported,
            pair_dir_exists=bool(pair_dir and pair_dir.exists()),
            start_script_exists=bool(start_script and start_script.exists()),
            executor_alive=executor_alive,
            stats_fresh=stats_fresh,
            running=running,
            live_pid=live_pid,
            process_alive=bool(process_alive),
            process_count=int(process_count or 0),
            stats_age=stats_age,
        )

    def read_stats(self, runtime: dict) -> tuple[dict, float | None]:
        stats_path = self.paths.stats_path(runtime)
        if not stats_path or not stats_path.exists():
            return {}, None
        try:
            raw = stats_path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw) if raw.strip() else {}
            age = max(0.0, time.time() - stats_path.stat().st_mtime)
            return data if isinstance(data, dict) else {}, age
        except Exception:
            return {}, None

    def read_memoria(self, sym: str, runtime: dict) -> dict:
        pair_dir = self.paths.pair_dir(runtime)
        if not pair_dir:
            return {}
        mp = pair_dir / f"memoria_{sym}.json"
        if mp.exists():
            try:
                raw = mp.read_text(encoding="utf-8", errors="ignore")
                data = json.loads(raw) if raw.strip() else {}
                return data if isinstance(data, dict) else {}
            except Exception:
                pass
        return {}

    def find_live_pid(self, runtime: dict) -> int | None:
        proc_pid = self.primary_process_pid(runtime)
        if proc_pid:
            return proc_pid
        for pid_path in self.paths.pid_paths(runtime):
            try:
                if not pid_path.exists():
                    continue
                pid = int(pid_path.read_text(encoding="utf-8", errors="ignore").strip())
                if self.pid_ok(pid):
                    return pid
            except Exception:
                continue
        return None

    def launch_pair(self, runtime: dict) -> RuntimeActionResult:
        start_script = self.paths.start_script(runtime)
        pair_dir = self.paths.pair_dir(runtime)
        if not start_script or not pair_dir or not start_script.exists():
            return RuntimeActionResult(False, "⚠ Launcher no disponible", pair_dir=str(pair_dir) if pair_dir else "")
        self.cleanup_stale_pid_files(runtime)
        popen_kwargs = self._hidden_subprocess_kwargs()
        subprocess.Popen(
            ["cmd.exe", "/c", "start", "", start_script.name],
            cwd=str(pair_dir),
            **popen_kwargs,
        )
        self.invalidate_process_cache()
        return RuntimeActionResult(True, f"⚡ Lanzando {start_script.name}...", pair_dir=str(pair_dir))

    def stop_pair(self, sym: str, runtime: dict) -> RuntimeActionResult:
        pair_dir = self.paths.pair_dir(runtime)
        prefix = (runtime or {}).get("prefix")
        if not pair_dir or not prefix:
            return RuntimeActionResult(False, f"⚠ No stop routine for {sym}", pair_dir=str(pair_dir) if pair_dir else "")
        processes = self.find_matching_processes(runtime, use_cache=False)
        pids = sorted({int(p["pid"]) for p in processes if p.get("pid")})
        killed = 0
        if pids:
            # Kill all matching processes in a single PowerShell call — avoids
            # spawning one taskkill per PID which serialises 30+ subprocesses and
            # blocks the UI thread for 8-10 s.
            pid_list = ",".join(str(p) for p in pids)
            ps_kill = (
                f"$ids = @({pid_list}); "
                "$k = 0; "
                "foreach ($id in $ids) { "
                "  try { Stop-Process -Id $id -Force -ErrorAction Stop; $k++ } "
                "  catch {} "
                "}; "
                "Write-Output $k"
            )
            try:
                res = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_kill],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    **self._hidden_subprocess_kwargs(),
                )
                killed = int((res.stdout or "0").strip()) if res.returncode == 0 else 0
            except Exception:
                pass
        for pid_path in self.paths.pid_paths(runtime):
            try:
                if pid_path.exists():
                    pid_path.unlink()
            except Exception:
                pass
        self.invalidate_process_cache()
        return RuntimeActionResult(
            True,
            f"■ Deteniendo {sym}...",
            detected_processes=len(processes),
            affected_processes=killed,
            pair_dir=str(pair_dir),
        )

    @staticmethod
    def pid_ok(pid: int) -> bool:
        try:
            if sys.platform == "win32":
                handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
                if not handle:
                    return False
                code = ctypes.wintypes.DWORD()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
                ctypes.windll.kernel32.CloseHandle(handle)
                return bool(ok) and code.value == 259
            os.kill(pid, 0)
            return True
        except Exception:
            return False

    @staticmethod
    def probe(port: int) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.15)
            ok = s.connect_ex(("127.0.0.1", port)) == 0
            s.close()
            return ok
        except Exception:
            return False

    def invalidate_process_cache(self) -> None:
        with self._proc_cache_lock:
            self._proc_cache_ts = 0.0
            self._proc_cache_data = []

    def process_snapshot(self, ttl_seconds: float = 1.0, use_cache: bool = True) -> list[dict]:
        now = time.monotonic()
        with self._proc_cache_lock:
            if use_cache and self._proc_cache_data and (now - self._proc_cache_ts) <= ttl_seconds:
                return [dict(p) for p in self._proc_cache_data]
        ps_cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object {$_.CommandLine -and $_.Name -in @('python.exe','cmd.exe','powershell.exe')} | "
            "Select-Object ProcessId, Name, CommandLine | ConvertTo-Json -Compress"
        )
        processes: list[dict] = []
        try:
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5,
                **self._hidden_subprocess_kwargs(),
            )
            raw = (res.stdout or "").strip()
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                if isinstance(parsed, list):
                    for proc in parsed:
                        if not isinstance(proc, dict):
                            continue
                        processes.append({
                            "pid": int(proc.get("ProcessId") or 0),
                            "name": str(proc.get("Name") or ""),
                            "commandline": str(proc.get("CommandLine") or ""),
                        })
        except Exception:
            processes = []
        with self._proc_cache_lock:
            self._proc_cache_ts = now
            self._proc_cache_data = [dict(p) for p in processes]
        return processes

    def runtime_patterns(self, runtime: dict) -> list[str]:
        prefix = str((runtime or {}).get("prefix") or "").lower().strip()
        if not prefix:
            return []
        return [
            f"{prefix}quantum_core", f"{prefix}llm", f"{prefix}trinity", f"{prefix}kraken",
            f"{prefix}sound", f"{prefix}news", f"{prefix}ollama_start", f"{prefix}start",
        ]

    def find_matching_processes(self, runtime: dict, use_cache: bool = True) -> list[dict]:
        pair_dir = self.paths.pair_dir(runtime)
        pair_dir_l = str(pair_dir).lower().replace("/", "\\") if pair_dir else ""
        patterns = self.runtime_patterns(runtime)
        matches: list[dict] = []
        for proc in self.process_snapshot(use_cache=use_cache):
            cmd = str(proc.get("commandline") or "").lower().replace("/", "\\")
            if not cmd:
                continue
            path_match = bool(pair_dir_l and pair_dir_l in cmd)
            pattern_match = any(pat in cmd for pat in patterns)
            news_match = "news_intelligence" in cmd and path_match
            generic_pair_match = path_match and any(token in cmd for token in ("quantum_core", "llm", "trinity", "kraken", "sound"))
            if pattern_match or news_match or generic_pair_match:
                matches.append(proc)
        return matches

    def primary_process_pid(self, runtime: dict) -> int | None:
        matches = self.find_matching_processes(runtime)
        if not matches:
            return None
        matches.sort(key=lambda p: (0 if str(p.get("name", "")).lower() == "python.exe" else 1, int(p.get("pid") or 0)))
        pid = int(matches[0].get("pid") or 0)
        return pid or None

    def cleanup_stale_pid_files(self, runtime: dict) -> None:
        if self.find_matching_processes(runtime):
            return
        for pid_path in self.paths.pid_paths(runtime):
            try:
                if pid_path.exists():
                    pid_path.unlink()
            except Exception:
                pass
