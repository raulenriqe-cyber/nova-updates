from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class PathService:
    root: Path
    bundle: Path
    orbitron_dir: Path
    exe_dir: Path | None = None

    @classmethod
    def from_entry(cls, entry_file: str) -> "PathService":
        if getattr(sys, "frozen", False):
            bundle = Path(sys._MEIPASS)
            exe_dir = Path(sys.executable).parent
            override = exe_dir / "nova_root.txt"
            if override.exists():
                try:
                    candidate = Path(override.read_text(encoding="utf-8-sig").strip())
                    root = candidate if candidate.exists() and (candidate / "pares").exists() else exe_dir
                except Exception:
                    root = exe_dir
            else:
                root = exe_dir
            orbitron_dir = bundle / "Orbitron"
            return cls(root=root, bundle=bundle, orbitron_dir=orbitron_dir, exe_dir=exe_dir)

        script_dir = Path(entry_file).resolve().parent
        bundle = script_dir
        root = script_dir.parent
        orbitron_dir = root / "distribucion" / "tipografias" / "Orbitron"
        return cls(root=root, bundle=bundle, orbitron_dir=orbitron_dir)

    @property
    def core_dir(self) -> Path:
        return self.root / "core"

    @property
    def pairs_dir(self) -> Path:
        return self.root / "pares"

    def pair_dir(self, runtime: dict | None) -> Path | None:
        folder = (runtime or {}).get("folder")
        if not folder:
            return None
        return self.pairs_dir / folder

    def start_script(self, runtime: dict | None) -> Path | None:
        pair_dir = self.pair_dir(runtime)
        start_name = (runtime or {}).get("start")
        if not pair_dir or not start_name:
            return None
        return pair_dir / start_name

    def stats_path(self, runtime: dict | None) -> Path | None:
        pair_dir = self.pair_dir(runtime)
        return pair_dir / "quantum_stats.json" if pair_dir else None

    def pid_paths(self, runtime: dict | None) -> list[Path]:
        pair_dir = self.pair_dir(runtime)
        if not pair_dir:
            return []
        names: list[str] = []
        if (runtime or {}).get("pid"):
            names.append(runtime["pid"])
        names.extend((runtime or {}).get("pid_candidates", []))
        return [pair_dir / name for name in dict.fromkeys(names)]

    def bridge_paths(self, runtime: dict | None) -> list[Path]:
        pair_dir = self.pair_dir(runtime)
        prefix = (runtime or {}).get("prefix")
        if not pair_dir or not prefix:
            return []
        candidates = [
            pair_dir / f"{prefix}quimera_bridge.ex5",
            pair_dir / f"{prefix}quimera_bridge.mq5",
            self.root / "bridge" / f"{prefix}quimera_bridge.ex5",
            self.root / "bridge" / f"{prefix}quimera_bridge.mq5",
        ]
        return [path for path in candidates if path.exists()]

    def extend_sys_path(self) -> None:
        candidates = ([str(self.exe_dir)] if self.exe_dir else []) + [str(self.root), str(self.bundle)]
        for path in candidates:
            if path not in sys.path:
                sys.path.insert(0, path)
