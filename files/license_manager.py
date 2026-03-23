"""
license_manager.py — NOVA Trading AI | Gestor de Licencias (Capa de Distribución)
Polarice Labs © 2026

Capa de licencias para el instalador y lanzador de NOVA.
INDEPENDIENTE del sistema de pares (core/license_system.py).

Decisiones arquitectónicas implementadas:
    HWID:        Importa HWIDProtection de core — nunca duplica
    GRACE:       72 horas (installer puede correr sin Railway un fin de semana)
    SECRET_KEY:  No se usa aquí — es responsabilidad del servidor (server/main.py)
    Cifrado:     AES-256 via Fernet (cryptography) para el archivo local de licencia

Separación de responsabilidades:
    ┌─────────────────────────────────────────────────────┐
    │  core/license_system.py                             │
    │  → Runtime de pares (XAUUSD, EUR, etc.)             │
    │  → Grace 24h, revalida cada 4h                      │
    │  → Corre semanas sin parar dentro del .exe del bot  │
    └─────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────┐
    │  distribucion/license_manager.py  (este archivo)   │
    │  → Installer + Lanzador de NOVA                     │
    │  → Grace 72h, heartbeat cada 24h                    │
    │  → Se ejecuta cuando el usuario abre el installer   │
    └─────────────────────────────────────────────────────┘

Tarea pendiente para Fase 2 (documentada en decisiones):
    Eliminar la copia duplicada de get_machine_hwid() que existe inline
    dentro de core/online_license_client.py.
    Una vez eliminada, ese archivo también deberá importar HWIDProtection.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# ─── HWID: fuente única de verdad ─────────────────────────────────────────────
# Importar de core, no reimplementar — decisión confirmada.
# NUNCA duplicar la lógica de HWID.
try:
    # Ajustar path si license_manager.py se ejecuta desde distribucion/
    # o desde la raíz del proyecto
    import sys as _sys
    _root = Path(__file__).parent.parent   # raíz: proyecto_quimera/
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))

    from core.hwid_protection import HWIDProtection
    _HWID_AVAILABLE = True
except ImportError:
    _HWID_AVAILABLE = False
    # Solo en desarrollo sin core/ disponible (ej: test en otro equipo)
    # En producción (exe PyInstaller) el .spec incluye core/ en pathex

# ─── Dependencia de cifrado ───────────────────────────────────────────────────
try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    # Sin cryptography: save_license/load_license usan JSON sin cifrar
    # FASE 2: agregar cryptography a requirements.txt y al .spec


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Grace period para modo offline — 72h (installer puede correr sin Railway)
# Diferente a core/license_system.py que usa 24h (runtime continuo del bot)
GRACE_HOURS = 72

# Intervalo de heartbeat — cada 24h (no cada 5min como online_license_client.py)
HEARTBEAT_INTERVAL_HOURS = 24

# URL del servidor de licencias Railway
# TODO Fase 2: mover a variable de entorno o archivo de configuración
LICENSE_SERVER_URL = os.environ.get(
    "NOVA_LICENSE_SERVER",
    "https://pacific-upliftment-production.up.railway.app",  # [NOVA FIX] URL Railway real — Polarice Labs © 2026
)

# Timeout para requests al servidor (en segundos)
REQUEST_TIMEOUT = 10

# Ruta del archivo de licencia cifrado en AppData del usuario
_APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
LICENSE_FILE_PATH = Path(_APPDATA) / "NOVA" / "license.dat"

# Clave de cifrado derivada del HWID + salt fijo
# Así el archivo .dat solo puede descifrarse en la misma máquina
_FERNET_SALT = b"NOVA_POLARICE_2026_DIST_v2"

logger = logging.getLogger("nova.license_manager")


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

def get_hwid() -> str:
    """
    Genera el ID único de esta máquina.

    Delega completamente a core/hwid_protection.HWIDProtection.
    Combina: UUID de máquina + MAC address + ProcessorId + Motherboard Serial.
    El resultado es un SHA256 de 64 chars hexadecimales.

    Returns:
        str: HWID en formato SHA256 hex (64 chars).
             Fallback: SHA256 del hostname si core no está disponible.

    NUNCA reimplementar esta lógica aquí — usar siempre HWIDProtection.
    (Ver: core/hwid_protection.py — fuente única de verdad de HWID)
    """
    if _HWID_AVAILABLE:
        return HWIDProtection().get_machine_hwid()

    # Fallback de desarrollo (no usar en producción)
    import socket
    logger.warning(
        "[license_manager] core/hwid_protection no disponible. "
        "Usando fallback de hostname. Instalar en máquina con core/ presente."
    )
    hostname_bytes = socket.gethostname().encode("utf-8")
    return hashlib.sha256(hostname_bytes).hexdigest()


def validate_key(key: str, hwid: str) -> dict:
    """
    Valida una license key contra el servidor Railway.

    Envía key + hwid al endpoint POST /validate.
    En la primera activación: el servidor registra el hwid.
    En activaciones posteriores: el servidor verifica que el hwid coincida.

    Args:
        key:  License key en formato "NOVA-XXXX-XXXX-XXXX-XXXX"
        hwid: Hash SHA256 generado por get_hwid() / HWIDProtection

    Returns:
        dict con estructura:
        {
            "valid":          bool,
            "pares":          list[str],   # pares habilitados (vacío si invalid)
            "expiry":         str,          # "YYYY-MM-DD" (None si invalid)
            "tier":           str,          # "Basic"|"Pro"|"Premium"|"Institutional"
            "client":         str,          # nombre del cliente
            "version_actual": str,          # versión actual del server
            "error":          str | None,   # mensaje de error si not valid
        }

    Manejo de errores:
        - Timeout / servidor caído → retorna valid=False, error="Servidor no disponible"
        - Key inválida → retorna valid=False, error=mensaje del servidor
        - HWID no coincide → retorna valid=False, error="HWID no coincide..."
    """
    try:
        response = requests.post(
            f"{LICENSE_SERVER_URL}/validate",
            json={"key": key, "hwid": hwid},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        logger.warning("[validate_key] No se pudo conectar al servidor de licencias")
        return {
            "valid": False,
            "pares": [],
            "error": "No se pudo conectar al servidor. Verifica tu conexión a internet.",
        }
    except requests.exceptions.Timeout:
        logger.warning("[validate_key] Timeout conectando al servidor de licencias")
        return {
            "valid": False,
            "pares": [],
            "error": "El servidor tardó demasiado en responder. Intenta de nuevo.",
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"[validate_key] HTTP error: {e}")
        return {
            "valid": False,
            "pares": [],
            "error": f"Error del servidor: {e.response.status_code}",
        }
    except Exception as e:
        logger.error(f"[validate_key] Error inesperado: {e}")
        return {
            "valid": False,
            "pares": [],
            "error": "Error inesperado al validar licencia.",
        }


def save_license(data: dict) -> None:
    """
    Guarda la licencia validada en disco (AppData/NOVA/license.dat).

    El archivo se cifra con Fernet (AES-128-CBC) usando una clave derivada
    del HWID de la máquina. Solo puede descifrarse en el mismo equipo.

    El archivo incluye un timestamp de cuándo se guardó, para calcular
    si el grace period de 72h ha expirado en modo offline.

    Args:
        data: Dict retornado por validate_key() con valid=True.
              Se añaden automáticamente:
                - "saved_at": timestamp ISO de cuando se guardó
                - "hwid":     HWID actual de la máquina

    Side effects:
        Crea el directorio AppData/NOVA/ si no existe.
        Si cryptography no está disponible, guarda en JSON sin cifrar
        con una advertencia en el log.
    """
    LICENSE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        **data,
        "saved_at": datetime.utcnow().isoformat(),
        "hwid":     get_hwid(),
    }

    raw = json.dumps(record, ensure_ascii=False).encode("utf-8")

    if _CRYPTO_AVAILABLE:
        key_bytes = _derive_fernet_key(record["hwid"])
        fernet    = Fernet(key_bytes)
        payload   = fernet.encrypt(raw)
    else:
        logger.warning(
            "[save_license] cryptography no disponible — guardando sin cifrar. "
            "Instalar: pip install cryptography"
        )
        payload = raw

    LICENSE_FILE_PATH.write_bytes(payload)
    logger.info(f"[save_license] Licencia guardada en {LICENSE_FILE_PATH}")


def load_license() -> Optional[dict]:
    """
    Carga la licencia guardada para modo offline.

    El modo offline tiene un grace period de GRACE_HOURS (72h).
    Si el archivo no existe o la licencia tiene más de 72h sin validarse
    contra el servidor, retorna None.

    Returns:
        dict con los datos de la licencia si es válida y dentro del grace period.
        None si:
            - El archivo no existe (primera vez)
            - El archivo está corrupto o cifrado con HWID diferente
            - Han pasado más de 72h desde la última validación online
            - La licencia expiró (expiry_date < hoy)

    GRACE_HOURS = 72:
        Diferente a core/license_system.py (24h) porque el installer
        puede ejecutarse cuando Railway está caído un fin de semana.
        El runtime del bot usa 24h porque verifica cada 4h.
    """
    if not LICENSE_FILE_PATH.exists():
        logger.info("[load_license] Archivo de licencia no encontrado")
        return None

    try:
        raw_bytes = LICENSE_FILE_PATH.read_bytes()

        if _CRYPTO_AVAILABLE:
            hwid      = get_hwid()
            key_bytes = _derive_fernet_key(hwid)
            fernet    = Fernet(key_bytes)
            try:
                decrypted = fernet.decrypt(raw_bytes)
            except InvalidToken:
                logger.warning(
                    "[load_license] No se pudo descifrar — HWID diferente o archivo corrupto"
                )
                return None
        else:
            decrypted = raw_bytes

        record = json.loads(decrypted.decode("utf-8"))

    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"[load_license] Error leyendo licencia: {e}")
        return None

    # ── Verificar grace period ────────────────────────────────────────────────
    saved_at_str = record.get("saved_at")
    if not saved_at_str:
        logger.warning("[load_license] Campo saved_at ausente — rechazando licencia")
        return None

    try:
        saved_at = datetime.fromisoformat(saved_at_str)
    except ValueError:
        logger.warning("[load_license] Campo saved_at con formato inválido")
        return None

    age_hours = (datetime.utcnow() - saved_at).total_seconds() / 3600
    if age_hours > GRACE_HOURS:
        logger.info(
            f"[load_license] Grace period expirado: "
            f"{age_hours:.1f}h > {GRACE_HOURS}h"
        )
        return None

    # ── Verificar que la licencia no expiró ───────────────────────────────────
    expiry_str = record.get("expiry")
    if expiry_str:
        try:
            expiry = datetime.fromisoformat(expiry_str).date()
            if expiry < datetime.utcnow().date():
                logger.info(f"[load_license] Licencia expirada: {expiry_str}")
                return None
        except ValueError:
            pass   # Si no podemos parsear, seguimos — el servidor lo verificará

    logger.info(
        f"[load_license] Licencia cargada offline "
        f"(age: {age_hours:.1f}h / grace: {GRACE_HOURS}h)"
    )
    return record


def heartbeat() -> bool:
    """
    Verifica que la licencia sigue activa contra el servidor.

    Llamar cada HEARTBEAT_INTERVAL_HOURS (24h) desde el lanzador de NOVA.
    Si retorna False: la licencia fue desactivada o expiró — detener acceso.

    Diferente a core/online_license_client.py que hace heartbeat cada 5min
    porque ese sistema corre continuamente dentro del bot de trading.
    Este heartbeat es para el installer/lanzador que el usuario abre ocasionalmente.

    Returns:
        True si la licencia está activa y puede continuar.
        False si:
            - La licencia fue desactivada (chargeback, fraude)
            - La licencia expiró
            - No hay licencia guardada localmente
            - El servidor no responde (falla silenciosamente → True conservador)

    Nota de comportamiento offline:
        Si el servidor no responde, retorna True (conservador).
        El grace period de load_license() se encarga del límite offline.
        No queremos bloquear al cliente por un problema temporal del servidor.
    """
    license_data = load_license()

    if not license_data:
        logger.info("[heartbeat] No hay licencia local válida")
        return False

    key  = license_data.get("key", "")
    hwid = get_hwid()

    if not key:
        logger.warning("[heartbeat] Licencia local sin campo 'key'")
        return False

    try:
        response = requests.post(
            f"{LICENSE_SERVER_URL}/heartbeat",
            json={
                "key":     key,
                "hwid":    hwid,
                "version": "2.0.0",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("active"):
            # Actualizar timestamp del archivo local para reiniciar grace period
            save_license(license_data)
            logger.info(
                f"[heartbeat] ✓ Activa — "
                f"{result.get('days_remaining', '?')} días restantes"
            )
            return True
        else:
            logger.warning(
                f"[heartbeat] Licencia inactiva: {result.get('error', 'unknown')}"
            )
            return False

    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout):
        # Servidor no disponible → comportamiento conservador: True
        logger.info("[heartbeat] Servidor no disponible — modo offline conservador")
        return True

    except Exception as e:
        logger.error(f"[heartbeat] Error inesperado: {e}")
        return True   # Conservador


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════════════════════

def _derive_fernet_key(hwid: str) -> bytes:
    """
    Deriva una clave Fernet de 32 bytes a partir del HWID.

    Fernet requiere exactamente 32 bytes codificados en base64 URL-safe.
    Derivamos usando SHA256(HWID + salt) para que la clave sea:
        - Determinista (misma máquina → misma clave)
        - Única por máquina (HWID diferente → clave diferente)
        - Sin hardcodear la clave en el código fuente

    Args:
        hwid: SHA256 hex del hardware de la máquina

    Returns:
        32 bytes codificados en base64 URL-safe (formato Fernet)
    """
    import base64
    raw = hashlib.sha256(
        (hwid + _FERNET_SALT.decode()).encode("utf-8")
    ).digest()                          # 32 bytes
    return base64.urlsafe_b64encode(raw)  # Fernet espera base64


def _probe_local_license_file() -> dict:
    """
    Inspecciona `license.dat` para distinguir entre archivo ausente,
    corrupción/HWID distinto y licencias viejas que solo requieren revalidación.

    Returns:
        {
            "file_present": bool,
            "status": "missing"|"ok"|"hwid_mismatch_or_corrupt"|"invalid_json"|"missing_saved_at"|"invalid_saved_at"|"grace_expired"|"expired",
            "record": dict | None,
        }
    """
    if not LICENSE_FILE_PATH.exists():
        return {
            "file_present": False,
            "status": "missing",
            "record": None,
        }

    try:
        raw_bytes = LICENSE_FILE_PATH.read_bytes()

        if _CRYPTO_AVAILABLE:
            hwid = get_hwid()
            key_bytes = _derive_fernet_key(hwid)
            fernet = Fernet(key_bytes)
            try:
                decrypted = fernet.decrypt(raw_bytes)
            except InvalidToken:
                return {
                    "file_present": True,
                    "status": "hwid_mismatch_or_corrupt",
                    "record": None,
                }
        else:
            decrypted = raw_bytes

        record = json.loads(decrypted.decode("utf-8"))

    except json.JSONDecodeError:
        return {
            "file_present": True,
            "status": "invalid_json",
            "record": None,
        }
    except OSError:
        return {
            "file_present": True,
            "status": "invalid_json",
            "record": None,
        }

    saved_at_str = record.get("saved_at")
    if not saved_at_str:
        return {
            "file_present": True,
            "status": "missing_saved_at",
            "record": record,
        }

    try:
        saved_at = datetime.fromisoformat(saved_at_str)
    except ValueError:
        return {
            "file_present": True,
            "status": "invalid_saved_at",
            "record": record,
        }

    age_hours = (datetime.utcnow() - saved_at).total_seconds() / 3600
    if age_hours > GRACE_HOURS:
        return {
            "file_present": True,
            "status": "grace_expired",
            "record": record,
        }

    expiry_str = record.get("expiry")
    if expiry_str:
        try:
            expiry = datetime.fromisoformat(expiry_str).date()
            if expiry < datetime.utcnow().date():
                return {
                    "file_present": True,
                    "status": "expired",
                    "record": record,
                }
        except ValueError:
            pass

    return {
        "file_present": True,
        "status": "ok",
        "record": record,
    }


def get_license_status() -> dict:
    """
    Retorna el estado actual de la licencia sin contactar el servidor.

    Útil para mostrar información en la UI antes de hacer requests.

    Returns:
        {
            "has_license": bool,
            "is_expired":  bool,
            "days_remaining": int | None,
            "tier":        str | None,
            "pares":       list[str],
            "client":      str | None,
            "grace_hours_remaining": float | None,
            "needs_online_check": bool,
        }
    """
    probe = _probe_local_license_file()
    record = probe.get("record") if probe.get("status") == "ok" else None

    if not record:
        if probe.get("file_present"):
            return {
                "has_license": False,
                "is_expired":  False,
                "days_remaining": None,
                "tier":        None,
                "pares":       [],
                "client":      None,
                "grace_hours_remaining": 0.0,
                "needs_online_check": True,
                "local_status": probe.get("status"),
                "local_file_present": True,
            }
        return {
            "has_license": False,
            "is_expired":  False,
            "days_remaining": None,
            "tier":        None,
            "pares":       [],
            "client":      None,
            "grace_hours_remaining": None,
            "needs_online_check": True,
            "local_status": "missing",
            "local_file_present": False,
        }

    expiry_str = record.get("expiry")
    days_remaining = None
    is_expired = False
    if expiry_str:
        try:
            expiry = datetime.fromisoformat(expiry_str).date()
            days_remaining = (expiry - datetime.utcnow().date()).days
            is_expired = days_remaining < 0
        except ValueError:
            pass

    saved_at_str = record.get("saved_at")
    grace_remaining = None
    needs_check = True
    if saved_at_str:
        try:
            saved_at    = datetime.fromisoformat(saved_at_str)
            age_hours   = (datetime.utcnow() - saved_at).total_seconds() / 3600
            grace_remaining = max(0.0, GRACE_HOURS - age_hours)
            needs_check = age_hours > HEARTBEAT_INTERVAL_HOURS
        except ValueError:
            pass

    return {
        "has_license":           True,
        "is_expired":            is_expired,
        "days_remaining":        days_remaining,
        "tier":                  record.get("tier"),
        "pares":                 record.get("pares", []),
        "client":                record.get("client"),
        "grace_hours_remaining": grace_remaining,
        "needs_online_check":    needs_check,
        "local_status":          "ok",
        "local_file_present":    True,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SELF-TEST (solo desarrollo)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

    print("=== NOVA License Manager — Self Test ===\n")

    # Test 1: HWID
    hwid = get_hwid()
    print(f"HWID ({len(hwid)} chars): {hwid[:16]}...{hwid[-8:]}")
    print(f"HWIDProtection disponible: {_HWID_AVAILABLE}")
    print(f"cryptography disponible:   {_CRYPTO_AVAILABLE}")
    print()

    # Test 2: Estado actual
    status = get_license_status()
    print("Estado de licencia:")
    for k, v in status.items():
        print(f"  {k}: {v}")
    print()

    # Test 3: Guardar y cargar licencia simulada
    mock_license = {
        "valid":   True,
        "key":     "NOVA-TEST-SELF-TEST-0001",
        "pares":   ["XAUUSD", "EURUSD"],
        "expiry":  "2027-12-31",
        "tier":    "Premium",
        "client":  "Self Test",
        "version_actual": "2.0.0",
    }

    print("Guardando licencia simulada...")
    save_license(mock_license)

    loaded = load_license()
    if loaded:
        print(f"✅ Licencia cargada correctamente — client: {loaded.get('client')}")
    else:
        print("❌ No se pudo cargar la licencia guardada")
    print()
    print(f"Archivo: {LICENSE_FILE_PATH}")
    print("=== Test completado ===")
