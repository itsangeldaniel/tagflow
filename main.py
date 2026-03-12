import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
app.setApplicationName("TagFlow")
app.setStyle("Fusion")
app.setQuitOnLastWindowClosed(False)

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
    try:
        from updater import check_en_background
        check_en_background(_mostrar_update)
    except Exception as e:
        print(f"[UPDATER] Error iniciando check: {e}")


def _mostrar_update(info: dict):
    """Se llama desde el hilo de background si hay update disponible."""
    if ventana:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: _abrir_dialog(info))


def _abrir_dialog(info: dict):
    try:
        from ui.update_dialog import UpdateDialog
        dlg = UpdateDialog(info, parent=ventana)
        dlg.exec()
    except Exception as e:
        print(f"[UPDATER] Error mostrando dialog: {e}")


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