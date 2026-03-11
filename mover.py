import os
import shutil
import platform
import time
import re

SISTEMA = platform.system()
_TAG = r'[a-zA-Z0-9_\-áéíóúüñÁÉÍÓÚÜÑ]+'


def _nombre_limpio(nombre_archivo: str) -> str:
    """Quita todas las etiquetas @xxx del nombre."""
    nombre, ext = os.path.splitext(nombre_archivo)
    nombre_sin = re.sub(r'(@' + _TAG + r')+', '', nombre).strip()
    # Limpiar espacios/guiones residuales al final
    nombre_sin = nombre_sin.rstrip(' _-').strip()
    return (nombre_sin or "archivo") + ext


def mover_archivo(ruta_archivo: str, carpeta_raiz: str, etiqueta: str) -> bool:
    """Compatibilidad — mueve a una sola carpeta."""
    return mover_archivo_ruta(ruta_archivo, carpeta_raiz, [etiqueta])


def mover_archivo_ruta(ruta_archivo: str, carpeta_raiz: str,
                        ruta_etiquetas: list[str]) -> bool:
    """
    Mueve el archivo a carpeta_raiz/etiqueta1/.../etiquetaN/
    El archivo destino usa nombre LIMPIO (sin @etiquetas).
    """
    if not os.path.exists(ruta_archivo):
        return False

    nombre_sucio = os.path.basename(ruta_archivo)
    nombre_dest  = _nombre_limpio(nombre_sucio)

    # Construir ruta destino
    carpeta_destino = os.path.join(carpeta_raiz, *ruta_etiquetas)

    try:
        os.makedirs(carpeta_destino, exist_ok=True)
    except PermissionError:
        print(f"[MOVER] Sin permisos: {carpeta_destino}")
        return False

    ruta_destino = _resolver_nombre(os.path.join(carpeta_destino, nombre_dest))

    reintentos = 3 if SISTEMA == "Windows" else 1
    for intento in range(reintentos):
        try:
            shutil.move(ruta_archivo, ruta_destino)
            return True
        except PermissionError:
            if intento < reintentos - 1:
                time.sleep(0.5)
            else:
                print(f"[MOVER] Sin permisos: {ruta_archivo}")
                return False
        except Exception as e:
            print(f"[MOVER] Error: {e}")
            return False
    return False


def _resolver_nombre(ruta: str) -> str:
    """Evita sobreescribir — agrega (1), (2)..."""
    if not os.path.exists(ruta):
        return ruta
    base, ext = os.path.splitext(ruta)
    # Limpiar (N) previos para no acumular
    base = re.sub(r'\s*\(\d+\)$', '', base)
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"