from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class LicenseSnapshot:
    raw: dict

    @property
    def tier(self) -> str:
        return str(self.raw.get("tier", "DEMO") or "DEMO")

    @property
    def days_remaining(self):
        return self.raw.get("days_remaining")

    @property
    def has_license(self) -> bool:
        return bool(self.raw.get("has_license"))

    @property
    def client(self) -> str:
        return str(self.raw.get("client", "Demo User"))

    @property
    def license_key(self) -> str:
        return str(self.raw.get("license_key", "NOVA-DEMO-0000-0000"))

    @property
    def expiry(self) -> str:
        return str(self.raw.get("expiry", "—"))


class LicenseService:
    def __init__(self, loader: Callable[[], dict] | None = None):
        self._loader = loader

    def load(self) -> LicenseSnapshot:
        if not self._loader:
            return LicenseSnapshot({})
        try:
            data = self._loader() or {}
            return LicenseSnapshot(dict(data))
        except Exception:
            return LicenseSnapshot({})

    def days_text(self, snapshot: LicenseSnapshot, texts: dict) -> str:
        days = snapshot.days_remaining
        return texts["days_remaining"].format(days=days) if days else texts["no_license"]

    def pairs_count_text(self, count: int, texts: dict) -> str:
        return texts["pairs_active"].format(count=count)

    def subscription_rows(self, snapshot: LicenseSnapshot, pares: list, texts: dict) -> dict:
        return {
            "license_key": snapshot.license_key,
            "license_expiry": snapshot.expiry,
            "license_days": texts["days_remaining"].format(days=snapshot.days_remaining) if snapshot.days_remaining not in (None, "") else "—",
            "license_pairs": f"{len(pares)}",
            "license_server": "railway.app",
            "license_status": texts["license_active"] if snapshot.has_license else texts["license_demo"],
        }
