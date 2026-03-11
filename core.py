import os
import json
import shutil
import platform

# ──────────────────────────────────────────────────────────────
#  CORE – Inicialización del entorno TagFlow
#  Compatible con Windows, macOS y Linux
# ──────────────────────────────────────────────────────────────

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagflow_config.json")
SISTEMA = platform.system()  # "Windows" | "Darwin" | "Linux"


# ── Configuración ─────────────────────────────────────────────

def cargar_config() -> dict | None:
    """Carga la configuración guardada. Retorna None si es la primera vez."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def guardar_config(carpeta_raiz: str):
    """Persiste la ruta raíz elegida por el usuario."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"carpeta_raiz": carpeta_raiz}, f, ensure_ascii=False, indent=2)


# ── Entorno TagFlow ────────────────────────────────────────────

def inicializar_entorno(disco: str) -> str:
    """
    Crea la estructura base en el disco elegido:
        <disco>/TagFlow/
        <disco>/TagFlow/inbox/
    Retorna la ruta absoluta de la carpeta raíz TagFlow.
    """
    carpeta_raiz = os.path.join(disco, "TagFlow")
    inbox = os.path.join(carpeta_raiz, "inbox")
    os.makedirs(inbox, exist_ok=True)
    guardar_config(carpeta_raiz)
    return carpeta_raiz


# ── Detección de discos ────────────────────────────────────────

def obtener_discos_disponibles() -> list[dict]:
    """
    Detecta los discos/volúmenes disponibles según el sistema operativo.
    Retorna lista de dicts con: ruta, nombre, espacio_libre_gb, espacio_total_gb.
    """
    if SISTEMA == "Windows":
        return _discos_windows()
    elif SISTEMA == "Darwin":
        return _discos_macos()
    else:
        return _discos_linux()


def _info_disco(ruta: str, nombre: str) -> dict | None:
    """Obtiene espacio de un punto de montaje. Retorna None si falla."""
    try:
        total, _, libre = shutil.disk_usage(ruta)
        if total == 0:
            return None
        return {
            "ruta": ruta,
            "nombre": nombre,
            "espacio_libre_gb": round(libre / (1024 ** 3), 1),
            "espacio_total_gb": round(total / (1024 ** 3), 1),
        }
    except Exception:
        return None


def _discos_windows() -> list[dict]:
    """Windows: itera letras A-Z y obtiene nombre de volumen via WinAPI."""
    import string
    discos = []

    for letra in string.ascii_uppercase:
        ruta = f"{letra}:\\"
        if not os.path.exists(ruta):
            continue

        nombre_volumen = ""
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(261)
            ctypes.windll.kernel32.GetVolumeInformationW(
                ruta, buf, ctypes.sizeof(buf), None, None, None, None, 0
            )
            nombre_volumen = buf.value.strip()
        except Exception:
            pass

        nombre_legible = f"Disco {letra}:  —  {nombre_volumen}" if nombre_volumen else f"Disco {letra}:"
        info = _info_disco(ruta, nombre_legible)
        if info:
            discos.append(info)

    return discos


def _discos_macos() -> list[dict]:
    """macOS: usa /Volumes/ donde se montan todos los discos."""
    discos = []
    volumes = "/Volumes"

    if not os.path.exists(volumes):
        info = _info_disco(os.path.expanduser("~"), "Disco Principal")
        return [info] if info else []

    vistos = set()
    for volumen in os.listdir(volumes):
        ruta = os.path.join(volumes, volumen)
        if not os.path.isdir(ruta):
            continue
        try:
            dev_id = os.stat(ruta).st_dev
            if dev_id in vistos:
                continue
            vistos.add(dev_id)
        except Exception:
            continue

        if volumen.lower().replace(" ", "_") in ("macintosh_hd", "macintosh hd"):
            nombre = "Macintosh HD  (Disco Principal)"
        else:
            nombre = volumen

        info = _info_disco(ruta, nombre)
        if info:
            discos.append(info)

    if not discos:
        info = _info_disco(os.path.expanduser("~"), "Disco Principal")
        if info:
            discos.append(info)

    return discos


def _discos_linux() -> list[dict]:
    """
    Linux: muestra el home del usuario como opcion principal
    y discos externos montados en /media/ o /mnt/.
    Evita usar / directamente para no tener problemas de permisos.
    """
    FS_VIRTUALES = {
        "tmpfs", "devtmpfs", "sysfs", "proc", "devpts", "cgroup", "cgroup2",
        "pstore", "efivarfs", "bpf", "tracefs", "securityfs", "debugfs",
        "hugetlbfs", "mqueue", "fusectl", "configfs", "overlay", "squashfs",
        "ramfs", "autofs", "rpc_pipefs", "nfsd", "none", "udev",
    }

    discos = []
    vistos = set()

    # 1. Siempre ofrecer home del usuario como opcion principal
    home = os.path.expanduser("~")
    try:
        stat = os.statvfs(home)
        dev_id = (stat.f_fsid, os.stat(home).st_dev)
        vistos.add(dev_id)
        total = stat.f_frsize * stat.f_blocks
        libre = stat.f_frsize * stat.f_bavail
        if total > 0:
            discos.append({
                "ruta": home,
                "nombre": f"Carpeta personal  (/home/{os.path.basename(home)})",
                "espacio_libre_gb": round(libre / (1024 ** 3), 1),
                "espacio_total_gb": round(total / (1024 ** 3), 1),
            })
    except Exception:
        pass

    # 2. Discos externos montados en /media/ o /mnt/
    puntos_externos = []
    try:
        with open("/proc/mounts", "r") as f:
            for linea in f:
                partes = linea.split()
                if len(partes) < 3:
                    continue
                dispositivo, punto, fs_type = partes[0], partes[1], partes[2]
                if fs_type in FS_VIRTUALES:
                    continue
                if not dispositivo.startswith("/dev/"):
                    continue
                if punto.startswith("/media/") or punto.startswith("/mnt/"):
                    if os.path.isdir(punto):
                        puntos_externos.append(punto)
    except Exception:
        pass

    for punto in puntos_externos:
        try:
            stat = os.statvfs(punto)
            dev_id = (stat.f_fsid, os.stat(punto).st_dev)
            if dev_id in vistos:
                continue
            vistos.add(dev_id)

            total = stat.f_frsize * stat.f_blocks
            libre = stat.f_frsize * stat.f_bavail
            if total == 0:
                continue

            nombre = os.path.basename(punto) or punto
            discos.append({
                "ruta": punto,
                "nombre": nombre,
                "espacio_libre_gb": round(libre / (1024 ** 3), 1),
                "espacio_total_gb": round(total / (1024 ** 3), 1),
            })
        except Exception:
            pass

    return discos