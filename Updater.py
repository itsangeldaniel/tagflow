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
GITHUB_OWNER    = "itsangeld67"
GITHUB_REPO     = "tagflow"
CURRENT_VERSION = "1.0.0"
API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

SISTEMA = platform.system()  # Windows / Darwin / Linux


def get_version_file() -> str:
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
    try:
        def parse(v):
            return tuple(int(x) for x in v.lstrip("v").split("."))
        return parse(remota) > parse(local)
    except:
        return False


def _asset_para_sistema(assets: list) -> dict | None:
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
            return None

        asset = _asset_para_sistema(data.get("assets", []))
        if not asset:
            return None

        return {
            "version":   version_remota,
            "url":       asset["browser_download_url"],
            "nombre":    asset["name"],
            "notas":     data.get("body", ""),
            "tamaño_mb": round(asset["size"] / (1024 * 1024), 1),
        }
    except Exception as e:
        print(f"[UPDATER] Error consultando: {e}")
        return None


def descargar_y_aplicar(info: dict, progreso_cb=None) -> bool:
    try:
        import urllib.request

        url      = info["url"]
        tmp_dir  = tempfile.mkdtemp(prefix="tagflow_update_")
        tmp_file = os.path.join(tmp_dir, info["nombre"])

        def _reporthook(count, block_size, total_size):
            if total_size > 0 and progreso_cb:
                pct = min(100, int(count * block_size * 100 / total_size))
                progreso_cb(pct)

        urllib.request.urlretrieve(url, tmp_file, reporthook=_reporthook)
        if progreso_cb:
            progreso_cb(100)

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
    subprocess.Popen(["open", tmp_dmg])
    sys.exit(0)


def _aplicar_linux(tmp_file: str):
    exe_actual = sys.executable if getattr(sys, "frozen", False) \
                 else os.path.join(os.path.dirname(__file__), "TagFlow")

    os.chmod(tmp_file, 0o755)
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


def check_en_background(on_update_disponible):
    """
    Llama a on_update_disponible(info_dict) si hay actualización.
    No bloquea la app — corre en hilo daemon.
    """
    def _worker():
        try:
            info = verificar_actualizacion()
            if info:
                on_update_disponible(info)
        except Exception as e:
            print(f"[UPDATER] Error en worker: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()