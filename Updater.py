"""
TagFlow Auto-Updater
Consulta GitHub Releases y se actualiza solo si hay versión nueva.
"""

import os
import sys
import json
import shutil
import tempfile
import threading
import platform
import subprocess

# ── Configura esto con tu repo ────────────────────────────────
GITHUB_OWNER   = "TU_USUARIO"          # ← cambia esto
GITHUB_REPO    = "tagflow"             # ← cambia esto
CURRENT_VERSION = "1.0.0"             # ← se actualiza automáticamente
API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

SISTEMA = platform.system()  # Windows / Darwin / Linux


def get_version_file() -> str:
    """Ruta al archivo version.txt junto al ejecutable."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "version.txt")


def leer_version_local() -> str:
    try:
        with open(get_version_file(), "r") as f:
            return f.read().strip()
    except:
        return CURRENT_VERSION


def _comparar_versiones(local: str, remota: str) -> bool:
    """Retorna True si la versión remota es más nueva."""
    try:
        def parse(v):
            return tuple(int(x) for x in v.lstrip("v").split("."))
        return parse(remota) > parse(local)
    except:
        return False


def _asset_para_sistema(assets: list) -> dict | None:
    """Elige el asset correcto según el sistema operativo."""
    keywords = {
        "Windows": [".exe", "windows", "win"],
        "Darwin":  [".dmg", ".app", "macos", "darwin", "mac"],
        "Linux":   ["linux", ".AppImage", ".tar.gz"],
    }.get(SISTEMA, [])

    for asset in assets:
        name = asset["name"].lower()
        if any(kw.lower() in name for kw in keywords):
            return asset
    return None


def verificar_actualizacion() -> dict | None:
    """
    Consulta GitHub y retorna info de la nueva versión si existe.
    Retorna None si no hay actualización o hay error.
    """
    try:
        import urllib.request
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "TagFlow-Updater/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        version_remota = data.get("tag_name", "").lstrip("v")
        version_local  = leer_version_local()

        if not _comparar_versiones(version_local, version_remota):
            return None  # Ya está actualizado

        asset = _asset_para_sistema(data.get("assets", []))
        if not asset:
            return None

        return {
            "version":     version_remota,
            "url":         asset["browser_download_url"],
            "nombre":      asset["name"],
            "notas":       data.get("body", ""),
            "tamaño_mb":   round(asset["size"] / (1024 * 1024), 1),
        }
    except Exception as e:
        print(f"[UPDATER] Error consultando: {e}")
        return None


def descargar_y_aplicar(info: dict, progreso_cb=None) -> bool:
    """
    Descarga el nuevo ejecutable y lo aplica.
    progreso_cb(porcentaje: int) — callback opcional de progreso.
    """
    try:
        import urllib.request

        url      = info["url"]
        tmp_dir  = tempfile.mkdtemp(prefix="tagflow_update_")
        tmp_file = os.path.join(tmp_dir, info["nombre"])

        # ── Descargar con progreso ────────────────────────
        def _reporthook(count, block_size, total_size):
            if total_size > 0 and progreso_cb:
                pct = min(100, int(count * block_size * 100 / total_size))
                progreso_cb(pct)

        urllib.request.urlretrieve(url, tmp_file, reporthook=_reporthook)
        if progreso_cb:
            progreso_cb(100)

        # ── Aplicar según sistema ─────────────────────────
        if SISTEMA == "Windows":
            _aplicar_windows(tmp_file)
        elif SISTEMA == "Darwin":
            _aplicar_macos(tmp_file)
        else:
            _aplicar_linux(tmp_file)

        return True

    except Exception as e:
        print(f"[UPDATER] Error descargando: {e}")
        return False


def _aplicar_windows(tmp_exe: str):
    """
    Windows: crea un .bat que espera a que TagFlow cierre,
    reemplaza el .exe y relanza.
    """
    exe_actual = sys.executable if getattr(sys, "frozen", False) else __file__
    bat = tempfile.NamedTemporaryFile(suffix=".bat", delete=False, mode="w")
    bat.write(f"""@echo off
timeout /t 2 /nobreak > nul
copy /Y "{tmp_exe}" "{exe_actual}"
start "" "{exe_actual}"
del "%~f0"
""")
    bat.close()
    subprocess.Popen(["cmd", "/c", bat.name], creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit(0)


def _aplicar_macos(tmp_dmg: str):
    """macOS: abre el .dmg para que el usuario arrastre."""
    subprocess.Popen(["open", tmp_dmg])
    sys.exit(0)


def _aplicar_linux(tmp_file: str):
    """Linux: reemplaza el AppImage/binario y relanza."""
    exe_actual = sys.executable if getattr(sys, "frozen", False) \
                 else os.path.join(os.path.dirname(__file__), "TagFlow")

    os.chmod(tmp_file, 0o755)
    # Crear script que reemplaza el binario y relanza
    sh = tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w")
    sh.write(f"""#!/bin/bash
sleep 1
cp -f "{tmp_file}" "{exe_actual}"
chmod +x "{exe_actual}"
"{exe_actual}" &
rm -- "$0"
""")
    sh.close()
    os.chmod(sh.name, 0o755)
    subprocess.Popen(["/bin/bash", sh.name])
    sys.exit(0)


# ── Check en background (no bloquea la app) ───────────────────

def check_en_background(on_update_disponible):
    """
    Llama a on_update_disponible(info_dict) en el hilo principal
    si hay una actualización disponible.
    No bloquea el arranque.
    """
    def _worker():
        info = verificar_actualizacion()
        if info:
            on_update_disponible(info)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()