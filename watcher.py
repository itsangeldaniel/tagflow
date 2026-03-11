import os
import time
import threading
import re

from tagger import extraer_ruta, nombre_limpio
from mover import mover_archivo_ruta

_TAG    = r'[a-zA-Z0-9_\-áéíóúüñÁÉÍÓÚÜÑ]+'
_PATRON = re.compile(r'^[^@]+@(' + _TAG + r')+')


class Watcher(threading.Thread):
    def __init__(self, carpeta_raiz: str, callback=None):
        super().__init__(daemon=True)
        self.carpeta_raiz  = carpeta_raiz
        self.callback      = callback
        self._stop_event   = threading.Event()
        # Clave: path original → ya procesado. Evita reprocessar el mismo archivo.
        self._procesados   = set()
        self._home         = os.path.expanduser("~")
        self._tagflow_snap = None
        # Timestamp del último movimiento para evitar loop de refresh
        self._ultimo_move  = 0.0

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._escanear_home(self._home)
                self._escanear_tagflow()
                self._check_cambios()
            except Exception as e:
                print(f"[WATCHER] Error: {e}")
            time.sleep(2)

    def detener(self):
        self._stop_event.set()

    # ── Snapshot ────────────────────────────────────────────────────────────

    def _snapshot(self):
        """Solo nombres de dirs — ignora mtime para no triggear por movimientos."""
        snap = []
        try:
            for root_dir, dirs, files in os.walk(self.carpeta_raiz):
                dirs[:] = sorted([d for d in dirs if not d.startswith(".")])
                rel = os.path.relpath(root_dir, self.carpeta_raiz)
                # Solo estructura (nombres), no mtime ni conteo de archivos
                snap.append((rel, tuple(dirs)))
        except:
            pass
        return tuple(snap)

    def _check_cambios(self):
        """Notifica UI solo si la ESTRUCTURA de carpetas cambió (no archivos)."""
        cur = self._snapshot()
        if self._tagflow_snap is not None and cur != self._tagflow_snap:
            # Esperar un poco para que el move termine antes de refrescar
            time.sleep(0.5)
            if self.callback:
                self.callback("__refresh__", "")
        self._tagflow_snap = cur

    # ── Escanear home ────────────────────────────────────────────────────────

    def _escanear_home(self, directorio: str):
        try:
            entradas = list(os.scandir(directorio))
        except PermissionError:
            return
        for e in entradas:
            if e.path.startswith(self.carpeta_raiz):
                continue
            if e.name.startswith(".") or e.name.startswith("$"):
                continue
            if e.is_file(follow_symlinks=False):
                self._procesar(e.path, e.name)
            elif e.is_dir(follow_symlinks=False):
                if e.name not in {".venv","__pycache__","node_modules",
                                  ".git",".cache",".local","proc","sys","dev"}:
                    self._escanear_home(e.path)

    # ── Escanear dentro de TagFlow (renombres con @) ─────────────────────────

    def _escanear_tagflow(self):
        try:
            for root_dir, dirs, files in os.walk(self.carpeta_raiz):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if fname.startswith("."):
                        continue
                    fpath = os.path.join(root_dir, fname)
                    # Solo procesar si tiene @ Y no está ya procesado
                    if _PATRON.match(fname) and fpath not in self._procesados:
                        self._procesar(fpath, fname)
        except:
            pass

    # ── Procesar archivo ─────────────────────────────────────────────────────

    def _procesar(self, ruta: str, nombre: str):
        if ruta in self._procesados:
            return
        if not _PATRON.match(nombre):
            return

        etiquetas = extraer_ruta(nombre)
        if not etiquetas:
            return
        if any(len(e) < 2 for e in etiquetas):
            return
        if any(e.isdigit() or re.match(r'^\d+x?$', e) for e in etiquetas):
            return
        if not self._listo(ruta):
            return

        # Marcar ANTES de mover para evitar doble proceso
        self._procesados.add(ruta)

        exito = mover_archivo_ruta(ruta, self.carpeta_raiz, etiquetas)
        if exito:
            self._ultimo_move = time.time()
            if self.callback:
                self.callback(etiquetas[0], nombre_limpio(nombre))

    def _listo(self, ruta: str, espera: float = 0.3) -> bool:
        try:
            t1 = os.path.getsize(ruta)
            time.sleep(espera)
            t2 = os.path.getsize(ruta)
            return t1 == t2
        except:
            return False