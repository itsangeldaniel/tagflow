import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

app = QApplication(sys.argv)
app.setApplicationName("TagFlow")
app.setStyle("Fusion")
app.setQuitOnLastWindowClosed(False)

_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagflow_icon.png")
if os.path.exists(_ico):
    app.setWindowIcon(QIcon(_ico))

from core import cargar_config, inicializar_entorno, obtener_discos_disponibles

ventana = None
watcher = None
setup_w = None


def iniciar_panel(carpeta_raiz):
    global ventana, watcher
    from watcher import Watcher
    from ui.main_window import MainWindow
    watcher = Watcher(carpeta_raiz)
    ventana = MainWindow(carpeta_raiz, watcher)
    watcher.callback = ventana.on_archivo_movido
    watcher.start()
    ventana.show()

    # ── Verificar actualizaciones en background (30s de delay) ──
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(30_000, _check_update)


def _check_update():
    """Consulta GitHub en background sin bloquear la UI."""
    from updater import check_en_background
    check_en_background(_mostrar_update)


def _mostrar_update(info: dict):
    """Se llama desde el hilo principal si hay update disponible."""
    from PyQt6.QtCore import QMetaObject, Qt
    # Asegurar que corre en hilo principal
    if ventana:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: _abrir_dialog(info))


def _abrir_dialog(info: dict):
    from ui.update_dialog import UpdateDialog
    dlg = UpdateDialog(info, parent=ventana)
    dlg.exec()


def on_disco(disco):
    global setup_w
    carpeta = inicializar_entorno(disco)
    if setup_w:
        setup_w.close()
    iniciar_panel(carpeta)


config = cargar_config()
if config and os.path.exists(config.get("carpeta_raiz", "")):
    iniciar_panel(config["carpeta_raiz"])
else:
    from ui.setup_window import SetupWindow
    setup_w = SetupWindow(obtener_discos_disponibles())
    setup_w.disco_elegido.connect(on_disco)
    setup_w.show()

sys.exit(app.exec())