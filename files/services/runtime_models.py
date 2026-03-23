from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RuntimeActionResult:
    ok: bool
    message: str
    detected_processes: int = 0
    affected_processes: int = 0
    pair_dir: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
