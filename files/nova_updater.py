#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nova_updater.py — NOVA Trading AI | Sistema de Actualización Automática
Polarice Labs © 2026

Descarga solo los archivos modificados desde GitHub Releases.
Se integra en nova_dashboard.py como thread de fondo al arrancar.

Flujo:
  1. Descarga version_manifest.json desde GitHub
  2. Compara hashes SHA256 con archivos locales
  3. Descarga solo los archivos que cambiaron
  4. Los guarda en _internal/ junto al exe
  5. Notifica al usuario que reinicie para aplicar

Uso desde nova_dashboard.py:
    from nova_updater import NovaUpdater
    updater = NovaUpdater(on_update_available=callback, on_complete=callback)
    updater.check_async()
"""

from __future__ import annotations
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

log = logging.getLogger("nova_updater")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACION — cambia GITHUB_USER y GITHUB_REPO a los tuyos
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_USER   = "raulenriqe-cyber"
GITHUB_REPO   = "nova-updates"
MANIFEST_URL  = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
    f"/main/releases/version_manifest.json"
)
DOWNLOAD_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
    f"/main/releases/files"
)
CHECK_TIMEOUT = 8    # segundos para conectar con GitHub
DOWNLOAD_TIMEOUT = 30

# Versión actual del dashboard — se actualiza con cada release
CURRENT_VERSION = "5.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

def _get_install_dir() -> Path:
    """
    Devuelve el directorio donde están los archivos actualizables.
    - Si está frozen (exe compilado): directorio _internal/ junto al exe
    - Si está en modo desarrollo: directorio del script
    """
    if getattr(sys, "frozen", False):
        # exe compilado por PyInstaller
        exe_dir = Path(sys.executable).parent
        internal = exe_dir / "_internal"
        return internal if internal.exists() else exe_dir
    else:
        # modo desarrollo
        return Path(__file__).parent


def _sha256(path: Path) -> str:
    """Calcula SHA256 de un archivo local."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def _fetch_json(url: str, timeout: int = CHECK_TIMEOUT) -> dict:
    """Descarga y parsea JSON desde una URL."""
    req = Request(url, headers={"User-Agent": "NOVA-Updater/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_file(url: str, dest: Path, timeout: int = DOWNLOAD_TIMEOUT) -> int:
    """
    Descarga un archivo a dest. Devuelve bytes descargados.
    Usa descarga atómica (archivo temporal → rename).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_suffix(dest.suffix + ".tmp")
    req = Request(url, headers={"User-Agent": "NOVA-Updater/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp, open(tmp_path, "wb") as f:
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        # Backup del original si existe
        if dest.exists():
            backup = dest.with_suffix(dest.suffix + ".bak")
            shutil.copy2(dest, backup)
        # Reemplazo atómico
        shutil.move(str(tmp_path), str(dest))
        return total
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def _version_tuple(v: str):
    """Convierte "5.1.2" en (5, 1, 2) para comparación."""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


# ─────────────────────────────────────────────────────────────────────────────
# CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class NovaUpdater:
    """
    Updater incremental para NOVA Dashboard.

    Callbacks:
        on_update_available(version: str, files: list[str]) → se llama cuando hay actualización
        on_progress(file: str, index: int, total: int)      → progreso de descarga
        on_complete(updated_files: list[str])                → descarga terminada
        on_error(message: str)                               → error de red o parsing
        on_no_update()                                       → ya está al día
    """

    def __init__(
        self,
        on_update_available: Optional[Callable] = None,
        on_progress:         Optional[Callable] = None,
        on_complete:         Optional[Callable] = None,
        on_error:            Optional[Callable] = None,
        on_no_update:        Optional[Callable] = None,
        auto_download:       bool = False,   # True = descarga sin preguntar
    ):
        self.on_update_available = on_update_available
        self.on_progress         = on_progress
        self.on_complete         = on_complete
        self.on_error            = on_error
        self.on_no_update        = on_no_update
        self.auto_download       = auto_download

        self._install_dir   = _get_install_dir()
        self._manifest: dict  = {}
        self._pending_files: list[dict] = []
        self._thread: Optional[threading.Thread] = None

    # ── API PÚBLICA ──────────────────────────────────────────────────────────

    def check_async(self) -> None:
        """Lanza la verificación en un thread de fondo. No bloquea la UI."""
        self._thread = threading.Thread(
            target=self._check_worker, daemon=True, name="nova-updater"
        )
        self._thread.start()

    def download_updates(self) -> None:
        """
        Descarga los archivos pendientes (llamar después de que el usuario confirme).
        Se ejecuta en thread de fondo.
        """
        t = threading.Thread(
            target=self._download_worker, daemon=True, name="nova-downloader"
        )
        t.start()

    def rollback(self) -> list[str]:
        """
        Restaura backups (.bak) si la actualización causó problemas.
        Devuelve lista de archivos restaurados.
        """
        restored = []
        for entry in self._pending_files:
            dest = self._install_dir / entry["local_path"]
            backup = dest.with_suffix(dest.suffix + ".bak")
            if backup.exists():
                shutil.copy2(backup, dest)
                restored.append(entry["local_path"])
                log.info(f"Rollback: {entry['local_path']}")
        return restored

    # ── WORKERS INTERNOS ─────────────────────────────────────────────────────

    def _check_worker(self) -> None:
        """Thread: descarga manifest y compara hashes."""
        try:
            log.info(f"Verificando actualizaciones en {MANIFEST_URL}")
            manifest = _fetch_json(MANIFEST_URL)
            self._manifest = manifest

            remote_version = manifest.get("version", "0.0.0")

            # Comparar versión
            if _version_tuple(remote_version) <= _version_tuple(CURRENT_VERSION):
                log.info(f"NOVA está al día (v{CURRENT_VERSION})")
                if self.on_no_update:
                    self.on_no_update()
                return

            # Encontrar archivos que cambiaron
            pending = []
            for entry in manifest.get("files", []):
                local_path = self._install_dir / entry["local_path"]
                local_hash = _sha256(local_path)
                if local_hash != entry["sha256"]:
                    pending.append(entry)
                    log.info(f"Actualización pendiente: {entry['local_path']} "
                             f"({local_hash[:8]}... → {entry['sha256'][:8]}...)")

            if not pending:
                log.info("Manifest actualizado pero archivos ya coinciden.")
                if self.on_no_update:
                    self.on_no_update()
                return

            self._pending_files = pending
            file_names = [e["local_path"] for e in pending]
            log.info(f"Actualización disponible v{remote_version}: {len(pending)} archivos")

            if self.on_update_available:
                self.on_update_available(remote_version, file_names)

            if self.auto_download:
                self._download_worker()

        except (URLError, HTTPError) as e:
            log.warning(f"No se pudo conectar con el servidor de actualizaciones: {e}")
            if self.on_error:
                self.on_error(f"Sin conexión al servidor de actualizaciones: {e}")
        except Exception as e:
            log.error(f"Error verificando actualización: {e}", exc_info=True)
            if self.on_error:
                self.on_error(str(e))

    def _download_worker(self) -> None:
        """Thread: descarga los archivos pendientes uno por uno."""
        updated = []
        total = len(self._pending_files)

        for i, entry in enumerate(self._pending_files):
            local_path = entry["local_path"]
            dest = self._install_dir / local_path
            url = f"{DOWNLOAD_BASE}/{entry['remote_path']}"

            try:
                if self.on_progress:
                    self.on_progress(local_path, i + 1, total)

                log.info(f"Descargando [{i+1}/{total}]: {local_path}")
                size = _download_file(url, dest)
                log.info(f"  → {size:,} bytes guardados en {dest}")

                # Verificar hash post-descarga
                downloaded_hash = _sha256(dest)
                if downloaded_hash != entry["sha256"]:
                    log.error(f"Hash incorrecto para {local_path}: "
                              f"esperado {entry['sha256']}, obtenido {downloaded_hash}")
                    # Restaurar backup
                    backup = dest.with_suffix(dest.suffix + ".bak")
                    if backup.exists():
                        shutil.copy2(backup, dest)
                    continue

                updated.append(local_path)

            except Exception as e:
                log.error(f"Error descargando {local_path}: {e}")
                if self.on_error:
                    self.on_error(f"Error descargando {local_path}: {e}")

        if self.on_complete:
            self.on_complete(updated)

        log.info(f"Actualización completada: {len(updated)}/{total} archivos actualizados.")
