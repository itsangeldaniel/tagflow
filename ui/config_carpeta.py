import os
import platform
import subprocess
import hashlib

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QMessageBox,
    QSystemTrayIcon, QMenu, QApplication, QGraphicsDropShadowEffect,
    QSizePolicy, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QCloseEvent, QBrush, QLinearGradient, QPen, QPainterPath

SISTEMA = platform.system()

COLORS = {
    "bg":           "#EAEAEA",
    "surface":      "#FFFFFF",
    "border":       "#DEDEDE",
    "text":         "#0D0D0D",
    "text2":        "#555555",
    "text3":        "#999999",
    "accent":       "#0071E3",
    "accent_hover": "#0077ED",
    "accent_light": "#E5F0FC",
    "header":       "#F8F8F8",
    "table_header": "#F2F2F2",
}

FOLDER_COLORS = [
    "#E8524A", "#0071E3", "#34C759", "#FF9500",
    "#AF52DE", "#FF2D55", "#5AC8FA", "#FFCC00",
    "#FF6B35", "#30B0C7", "#4CD964", "#A78BFA",
]

PALETA_CONFIG = [
    "#E8524A","#FF6B35","#FF9500","#FFCC00",
    "#34C759","#30B0C7","#0071E3","#5856D6",
    "#AF52DE","#FF2D55","#A2845E","#8E8E93",
    "#5AC8FA","#4CD964","#007AFF","#30D158",
    "#FF9F0A","#FF3B30",
]

# Colores personalizados por usuario {nombre: hex}
FOLDER_COLORS_CUSTOM: dict = {}

COL_NUM   = 36
COL_ARCH  = 95
COL_FECHA = 138
COL_ARROW = 22


def color_para_carpeta(nombre: str) -> str:
    if nombre in FOLDER_COLORS_CUSTOM:
        return FOLDER_COLORS_CUSTOM[nombre]
    idx = int(hashlib.md5(nombre.encode()).hexdigest(), 16) % len(FOLDER_COLORS)
    return FOLDER_COLORS[idx]


def abrir_en_explorador(ruta: str):
    try:
        if SISTEMA == "Windows":
            os.startfile(ruta)
        elif SISTEMA == "Darwin":
            subprocess.Popen(["open", ruta])
        else:
            for cmd in ["xdg-open","nautilus","dolphin","thunar","nemo"]:
                try:
                    subprocess.Popen([cmd, ruta]); return
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"[UI] {e}")


def sombra(radio=14, opacidad=45, dy=3) -> QGraphicsDropShadowEffect:
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(radio)
    s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, opacidad))
    return s


def _crear_icono_tray() -> QIcon:
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(COLORS["accent"]))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    p.setPen(QColor("white"))
    p.setFont(QFont("Arial", 26, QFont.Weight.Bold))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    p.end()
    return QIcon(px)


def _icono_carpeta_2d(size=20) -> QLabel:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#AAAAAA")))
    p.setPen(Qt.PenStyle.NoPen)
    body = QPainterPath()
    body.addRoundedRect(0, size*0.30, size, size*0.68, 2, 2)
    p.fillPath(body, QBrush(QColor("#AAAAAA")))
    tab = QPainterPath()
    tab.addRoundedRect(0, size*0.18, size*0.45, size*0.18, 2, 2)
    p.fillPath(tab, QBrush(QColor("#AAAAAA")))
    p.end()
    lbl = QLabel()
    lbl.setPixmap(px)
    lbl.setFixedSize(size, size)
    lbl.setStyleSheet("background: transparent;")
    return lbl


# ── Diálogo config carpeta ─────────────────────────────────────

class ColorDot(QFrame):
    def __init__(self, color_hex: str, seleccionado: bool, dialogo, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self._sel = seleccionado
        self._dialogo = dialogo
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update()

    def _update(self):
        borde = f"2.5px solid {COLORS['accent']}" if self._sel else "2px solid transparent"
        self.setStyleSheet(f"QFrame {{ background-color: {self.color_hex}; border-radius: 15px; border: {borde}; }}")

    def marcar(self, v: bool):
        self._sel = v; self._update()

    def mousePressEvent(self, e):
        self._dialogo._on_color(self)


class ConfigCarpetaDialog(QDialog):
    def __init__(self, nombre: str, color_actual: str, nota_actual: str, parent=None):
        super().__init__(parent)
        self._nombre_orig = nombre
        self._color = color_actual
        self._dots = []
        self.setWindowTitle(f"Configurar — {nombre}")
        self.setFixedWidth(400)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLORS['bg']}; font-family: 'Segoe UI', sans-serif; }}")
        self._build(nombre, color_actual, nota_actual)

    def _lbl_sec(self, txt):
        l = QLabel(txt)
        l.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        l.setStyleSheet(f"color: {COLORS['text2']}; letter-spacing: 0.5px;")
        return l

    def _build(self, nombre, color_actual, nota_actual):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 26, 26, 22)
        lay.setSpacing(16)

        # Título
        t = QLabel("Configurar carpeta")
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {COLORS['text']};")
        lay.addWidget(t)
        s = QLabel(nombre)
        s.setFont(QFont("Segoe UI", 11))
        s.setStyleSheet(f"color: {COLORS['text2']};")
        lay.addWidget(s)

        # Nombre
        lay.addWidget(self._lbl_sec("NOMBRE"))
        self.inp_nombre = QLineEdit(nombre)
        self.inp_nombre.setFixedHeight(40)
        self.inp_nombre.setFont(QFont("Segoe UI", 12))
        self.inp_nombre.setStyleSheet(f"""
            QLineEdit {{ background: {COLORS['surface']}; border: 1.5px solid {COLORS['border']};
                border-radius: 10px; padding: 0 14px; color: {COLORS['text']}; }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        self.inp_nombre.setGraphicsEffect(sombra(8, 20, 2))
        lay.addWidget(self.inp_nombre)

        # Color
        lay.addWidget(self._lbl_sec("COLOR"))
        pf = QFrame()
        pf.setStyleSheet(f"QFrame {{ background: {COLORS['surface']}; border-radius: 12px; border: 1px solid {COLORS['border']}; }}")
        pf.setGraphicsEffect(sombra(8, 18, 2))
        pl = QVBoxLayout(pf)
        pl.setContentsMargins(12, 12, 12, 12)
        pl.setSpacing(8)
        for i in range(0, len(PALETA_CONFIG), 9):
            row = QHBoxLayout()
            row.setSpacing(8)
            for c in PALETA_CONFIG[i:i+9]:
                dot = ColorDot(c, c == color_actual, self, pf)
                self._dots.append(dot)
                row.addWidget(dot)
            row.addStretch()
            pl.addLayout(row)
        lay.addWidget(pf)

        # Nota
        lay.addWidget(self._lbl_sec("NOTA  (opcional)"))
        self.inp_nota = QTextEdit()
        self.inp_nota.setPlainText(nota_actual)
        self.inp_nota.setFixedHeight(72)
        self.inp_nota.setFont(QFont("Segoe UI", 12))
        self.inp_nota.setStyleSheet(f"""
            QTextEdit {{ background: {COLORS['surface']}; border: 1.5px solid {COLORS['border']};
                border-radius: 10px; padding: 8px 14px; color: {COLORS['text']}; }}
            QTextEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        self.inp_nota.setGraphicsEffect(sombra(8, 18, 2))
        lay.addWidget(self.inp_nota)

        # Botones
        br = QHBoxLayout(); br.setSpacing(10)
        bc = QPushButton("Cancelar")
        bc.setFixedHeight(40)
        bc.setFont(QFont("Segoe UI", 12))
        bc.setCursor(Qt.CursorShape.PointingHandCursor)
        bc.setStyleSheet(f"QPushButton {{ background: {COLORS['surface']}; color: {COLORS['text2']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 0 18px; }} QPushButton:hover {{ background: #F0F0F0; }}")
        bc.setGraphicsEffect(sombra(8, 18, 2))
        bc.clicked.connect(self.reject)
        br.addWidget(bc)
        bg = QPushButton("Guardar")
        bg.setFixedHeight(40)
        bg.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        bg.setCursor(Qt.CursorShape.PointingHandCursor)
        bg.setStyleSheet(f"QPushButton {{ background: {COLORS['accent']}; color: white; border: none; border-radius: 10px; padding: 0 22px; }} QPushButton:hover {{ background: {COLORS['accent_hover']}; }}")
        bg.setGraphicsEffect(sombra(10, 55, 3))
        bg.clicked.connect(self.accept)
        br.addWidget(bg)
        lay.addLayout(br)

    def _on_color(self, dot):
        for d in self._dots: d.marcar(d == dot)
        self._color = dot.color_hex

    def resultado(self):
        n = self.inp_nombre.text().strip().replace(" ", "_") or self._nombre_orig
        return n, self._color, self.inp_nota.toPlainText().strip()


# ── Fila de carpeta ────────────────────────────────────────────

class FilaCarpeta(QFrame):
    HEIGHT_BASE = 58
    HEIGHT_NOTA = 78

    def __init__(self, numero, nombre, ruta,
                 on_click=None, modo_eliminar=False, on_eliminar=None,
                 modo_config=False, on_config=None, nota="",
                 nota_global="", autor_global="", es_empresarial=False,
                 parent=None):
        super().__init__(parent)
        self.ruta = ruta
        self._nombre = nombre
        self._color_hex = color_para_carpeta(nombre)
        self._hover = False
        self._on_click = on_click
        self._modo_eliminar = modo_eliminar
        self._on_eliminar = on_eliminar
        self._modo_config = modo_config
        self._on_config = on_config
        self._nota = nota
        self._nota_global = nota_global
        self._autor_global = autor_global
        self._es_empresarial = es_empresarial

        tiene_nota = bool(nota or nota_global)
        extra = 20 if (nota and nota_global) else 0
        h = (self.HEIGHT_NOTA + extra) if tiene_nota else self.HEIGHT_BASE
        self.setFixedHeight(h)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(ruta)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._build(numero, nombre, ruta)

    def _div(self):
        d = QFrame()
        d.setFixedSize(1, 28)
        d.setStyleSheet(f"background: {COLORS['border']};")
        return d

    def _build(self, numero, nombre, ruta):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Fila principal
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 12, 0)
        row.setSpacing(0)

        # #
        num = QLabel(str(numero))
        num.setFixedWidth(COL_NUM)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setFont(QFont("Segoe UI", 11))
        num.setStyleSheet(f"color: {COLORS['text3']}; background: transparent;")
        row.addWidget(num)
        row.addWidget(self._div())

        # Nombre
        nr = QHBoxLayout()
        nr.setContentsMargins(14, 0, 14, 0)
        nr.setSpacing(10)
        nr.addWidget(_icono_carpeta_2d(20))
        nl = QLabel(nombre)
        nl.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        nl.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        nl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nr.addWidget(nl)
        nr.addStretch()
        nw = QWidget()
        nw.setStyleSheet("background: transparent;")
        nw.setLayout(nr)
        nw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(nw, stretch=1)
        row.addWidget(self._div())

        # Archivos
        try:
            n = len([f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))])
            at = f"{n} archivo{'s' if n!=1 else ''}"
        except:
            at = "-"
        al = QLabel(at)
        al.setFixedWidth(COL_ARCH)
        al.setAlignment(Qt.AlignmentFlag.AlignCenter)
        al.setFont(QFont("Segoe UI", 11))
        al.setStyleSheet(f"color: {COLORS['text2']}; background: transparent;")
        row.addWidget(al)
        row.addWidget(self._div())

        # Fecha
        try:
            from datetime import datetime
            ts = os.path.getmtime(ruta)
            fs = datetime.fromtimestamp(ts).strftime("%H:%M  %d/%m/%Y")
        except:
            fs = "-"
        fl = QLabel(fs)
        fl.setFixedWidth(COL_FECHA)
        fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.setFont(QFont("Segoe UI", 11))
        fl.setStyleSheet(f"color: {COLORS['text2']}; background: transparent;")
        row.addWidget(fl)

        # Flecha
        arr = QLabel("›")
        arr.setFixedWidth(COL_ARROW)
        arr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arr.setFont(QFont("Segoe UI", 17))
        arr.setStyleSheet(f"color: {COLORS['text3']}; background: transparent;")
        row.addWidget(arr)

        # Botón config o eliminar
        if self._modo_config:
            btn = QPushButton("·")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 13))
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {COLORS['accent_light']}; color: {COLORS['accent']};
                    border-radius: 8px; border: 1px solid {COLORS['accent']}; }}
                QPushButton:hover {{ background: {COLORS['accent']}; color: white; }}
            """)
            btn.setGraphicsEffect(sombra(6, 35, 2))
            if self._on_config:
                fn = self._on_config
                btn.clicked.connect(lambda _, f=fn: f())
            row.addSpacing(6)
            row.addWidget(btn)
            row.addSpacing(4)

        elif self._modo_eliminar:
            btn = QPushButton("✕")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setStyleSheet("""
                QPushButton { background: #FF3B30; color: white; border-radius: 8px; border: none; }
                QPushButton:hover { background: #E0352A; }
                QPushButton:pressed { background: #C42D23; }
            """)
            btn.setGraphicsEffect(sombra(8, 55, 2))
            if self._on_eliminar:
                fn = self._on_eliminar
                btn.clicked.connect(lambda _, f=fn: f())
            row.addSpacing(6)
            row.addWidget(btn)
            row.addSpacing(4)

        root.addLayout(row)

        # Nota personal
        if self._nota:
            nota_lbl = QLabel(self._nota)
            nota_lbl.setFont(QFont("Segoe UI", 9))
            nota_lbl.setStyleSheet("color: " + COLORS['text2'] + "; background: transparent;")
            nota_lbl.setContentsMargins(COL_NUM + 14 + 28, 0, 12, 4)
            nota_lbl.setWordWrap(True)
            root.addWidget(nota_lbl)

        # Nota global (solo modo empresarial)
        if self._nota_global and self._es_empresarial:
            row_g_w = QWidget()
            row_g_w.setStyleSheet("background: transparent;")
            row_g = QHBoxLayout(row_g_w)
            row_g.setContentsMargins(COL_NUM + 14 + 28, 0, 12, 6)
            row_g.setSpacing(6)
            badge_g = QLabel("Global")
            badge_g.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            _ac = COLORS['accent']; _al = COLORS['accent_light']
            badge_g.setStyleSheet(
                "QLabel { color: " + _ac + "; background: " + _al + ";"
                " border-radius: 5px; padding: 1px 6px; }"
            )
            row_g.addWidget(badge_g)
            nota_g_lbl = QLabel(self._nota_global)
            nota_g_lbl.setFont(QFont("Segoe UI", 9))
            nota_g_lbl.setStyleSheet("color: " + _ac + "; background: transparent;")
            nota_g_lbl.setWordWrap(True)
            row_g.addWidget(nota_g_lbl)
            row_g.addStretch()
            root.addWidget(row_g_w)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color_hex)
        grad = QLinearGradient(0, 0, 0, self.height())
        if self._hover:
            grad.setColorAt(0.0, QColor(c.red(),c.green(),c.blue(),30))
            grad.setColorAt(0.4, QColor(c.red(),c.green(),c.blue(),70))
            grad.setColorAt(1.0, QColor(c.red(),c.green(),c.blue(),120))
        else:
            grad.setColorAt(0.0, QColor(255,255,255,255))
            grad.setColorAt(0.5, QColor(c.red(),c.green(),c.blue(),40))
            grad.setColorAt(1.0, QColor(c.red(),c.green(),c.blue(),90))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.fillPath(path, QBrush(grad))
        bc = QColor(self._color_hex) if self._hover else QColor(COLORS["border"])
        bc.setAlpha(180 if self._hover else 255)
        p.setPen(QPen(bc, 1.2))
        p.drawPath(path)
        p.end()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        # Animación: subir 3px y agrandar levemente
        self._anim_pos = QPropertyAnimation(self, b"pos")
        self._anim_pos.setDuration(130)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_pos.setEndValue(self.pos() - QPoint(0, 3))
        self._anim_pos.start()

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        self._anim_pos = QPropertyAnimation(self, b"pos")
        self._anim_pos.setDuration(130)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_pos.setEndValue(self.pos() + QPoint(0, 3))
        self._anim_pos.start()

    def mousePressEvent(self, e):
        # No propagar si el click fue en un botón hijo
        child = self.childAt(e.pos())
        if child and isinstance(child, QPushButton):
            return
        if self._on_click:
            self._on_click()
        abrir_en_explorador(self.ruta)


# ── Header de tabla ────────────────────────────────────────────

class HeaderTabla(QFrame):
    def __init__(self, modo_eliminar=False, modo_config=False, parent=None):
        super().__init__(parent)
        self._modo_eliminar = modo_eliminar
        self._modo_config = modo_config
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"QFrame {{ background: {COLORS['table_header']}; border-radius: 10px; border: none; }}")
        self.setGraphicsEffect(sombra(6, 12, 1))
        self._build()

    def _div(self):
        d = QFrame(); d.setFixedSize(1, 22)
        d.setStyleSheet(f"background: {COLORS['border']};")
        return d

    def _th(self, txt, w=None, align=Qt.AlignmentFlag.AlignCenter):
        l = QLabel(txt)
        l.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        l.setStyleSheet(f"color: {COLORS['text2']}; background: transparent;")
        l.setAlignment(align)
        if w: l.setFixedWidth(w)
        return l

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(0)
        lay.addWidget(self._th("#", COL_NUM))
        lay.addWidget(self._div())
        mn = self._th("  Mis Carpetas", align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        mn.setContentsMargins(14,0,0,0)
        mn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay.addWidget(mn, stretch=1)
        lay.addWidget(self._div())
        lay.addWidget(self._th("Archivos", COL_ARCH))
        lay.addWidget(self._div())
        lay.addWidget(self._th("Modificado", COL_FECHA))
        lay.addSpacing(COL_ARROW)
        if self._modo_config or self._modo_eliminar:
            lay.addSpacing(46)


# ── Banner notificación ────────────────────────────────────────

class NotificacionBanner(QFrame):
    def __init__(self, etiqueta, nombre, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet("QFrame { background: #F0FFF4; border: 1.5px solid #28A745; border-radius: 16px; }")
        self.setGraphicsEffect(sombra(10, 20, 2))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16,0,16,0); lay.setSpacing(10)
        ck = QLabel("+")
        ck.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        ck.setStyleSheet("color: #28A745; background: transparent;")
        lay.addWidget(ck)
        nc = nombre if len(nombre)<=38 else nombre[:35]+"..."
        txt = QLabel(f"<span style='color:#0D0D0D'><b>{nc}</b></span><span style='color:#555'> movido a </span><span style='color:{COLORS['accent']}'><b>{etiqueta}/</b></span>")
        txt.setFont(QFont("Segoe UI", 12))
        txt.setStyleSheet("background: transparent;")
        txt.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(txt); lay.addStretch()



# ── Fila de árbol con subcarpetas colapsables ─────────────────

class FilaArbol(QFrame):
    """Tarjeta de carpeta con degradado, animación hover y chips de subcarpetas."""

    def __init__(self, numero, nombre, ruta,
                 on_click=None, modo_eliminar=False, on_eliminar=None,
                 modo_config=False, on_config=None, nota="", parent=None):
        super().__init__(parent)
        self._nombre        = nombre
        self._ruta          = ruta
        self._numero        = numero
        self._on_click      = on_click
        self._on_eliminar   = on_eliminar
        self._on_config     = on_config
        self._modo_eliminar = modo_eliminar
        self._modo_config   = modo_config
        self._nota          = nota
        self._hover         = False
        self._subs          = self._get_subs()
        self._color_hex     = color_para_carpeta(nombre)
        self._build()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def _get_subs(self):
        try:
            return sorted([d for d in os.listdir(self._ruta)
                           if os.path.isdir(os.path.join(self._ruta, d))],
                          key=str.casefold)
        except:
            return []

    def _count_archivos(self):
        try:
            return len([f for f in os.listdir(self._ruta)
                        if os.path.isfile(os.path.join(self._ruta, f))])
        except:
            return 0

    def _build(self):
        tiene_subs = bool(self._subs)
        tiene_nota = bool(self._nota)
        h = 54
        if tiene_nota: h += 18
        if tiene_subs: h += 30
        self.setFixedHeight(h)
        self.setStyleSheet("QFrame { border: none; border-radius: 14px; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 6)
        root.setSpacing(4)

        # ── Fila principal ─────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(0)
        top.setContentsMargins(8, 0, 10, 0)

        # Número
        num_lbl = QLabel(str(self._numero))
        num_lbl.setFixedWidth(COL_NUM)
        num_lbl.setFont(QFont("Segoe UI", 10))
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setStyleSheet("color: " + COLORS["text3"] + "; background: transparent;")
        top.addWidget(num_lbl)

        # Nombre + nota
        info = QVBoxLayout()
        info.setSpacing(1); info.setContentsMargins(8, 0, 0, 0)
        nombre_lbl = QLabel(self._nombre)
        nombre_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        nombre_lbl.setStyleSheet("color: " + COLORS["text"] + "; background: transparent;")
        info.addWidget(nombre_lbl)
        if tiene_nota:
            nota_lbl = QLabel(self._nota)
            nota_lbl.setFont(QFont("Segoe UI", 9))
            nota_lbl.setStyleSheet("color: " + COLORS["text2"] + "; background: transparent;")
            info.addWidget(nota_lbl)
        top.addLayout(info)
        top.addStretch()

        # Archivos
        n = self._count_archivos()
        arch_lbl = QLabel(str(n) + " archivo" + ("s" if n != 1 else ""))
        arch_lbl.setFixedWidth(COL_ARCH)
        arch_lbl.setFont(QFont("Segoe UI", 10))
        arch_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arch_lbl.setStyleSheet("color: " + COLORS["text2"] + "; background: transparent;")
        top.addWidget(arch_lbl)

        # Modificado
        try:
            import time as _t
            mod_str = _t.strftime("%d/%m/%Y", _t.localtime(os.path.getmtime(self._ruta)))
        except:
            mod_str = "--"
        mod_lbl = QLabel(mod_str)
        mod_lbl.setFixedWidth(COL_FECHA)
        mod_lbl.setFont(QFont("Segoe UI", 9))
        mod_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mod_lbl.setStyleSheet("color: " + COLORS["text2"] + "; background: transparent;")
        top.addWidget(mod_lbl)

        # Botón config
        if self._modo_config:
            btn_cfg = QPushButton("·")
            btn_cfg.setFixedSize(26, 26)
            btn_cfg.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_cfg.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cfg.setStyleSheet(
                "QPushButton { background:" + COLORS["accent_light"] + "; color:" + COLORS["accent"] + ";"
                " border-radius:7px; border:none; font-weight:bold; font-size:16px; }"
                "QPushButton:hover { background:" + COLORS["accent"] + "; color:white; }"
            )
            _n = self._nombre
            btn_cfg.clicked.connect(lambda checked=False, n=_n:
                self._on_config(n) if self._on_config else None)
            top.addWidget(btn_cfg)

        # Botón eliminar
        if self._modo_eliminar:
            btn_del = QPushButton("x")
            btn_del.setFixedSize(26, 26)
            btn_del.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                "QPushButton { background:#FFF0F0; color:#FF3B30;"
                " border-radius:7px; border:none; font-weight:bold; }"
                "QPushButton:hover { background:#FF3B30; color:white; }"
            )
            _n = self._nombre
            btn_del.clicked.connect(lambda checked=False, n=_n:
                self._on_eliminar(n) if self._on_eliminar else None)
            top.addWidget(btn_del)

        root.addLayout(top)

        # ── Chips subcarpetas ──────────────────────────────
        if tiene_subs:
            chips = QHBoxLayout()
            chips.setSpacing(5)
            chips.setContentsMargins(COL_NUM + 16, 0, 10, 0)
            for sub in self._subs[:8]:
                cs = QColor(color_para_carpeta(sub))
                r2, g2, b2 = cs.red(), cs.green(), cs.blue()
                chip = QPushButton(sub)
                chip.setFixedHeight(20)
                chip.setCursor(Qt.CursorShape.PointingHandCursor)
                chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                chip.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
                chip.setStyleSheet(
                    "QPushButton { background: rgba(" + str(r2) + "," + str(g2) + "," + str(b2) + ",60);"
                    " color:" + COLORS["text"] + "; border-radius:7px;"
                    " border:1px solid rgba(" + str(r2) + "," + str(g2) + "," + str(b2) + ",130);"
                    " padding:0 8px; }"
                    "QPushButton:hover { background: rgba(" + str(r2) + "," + str(g2) + "," + str(b2) + ",130); }"
                )
                ruta_sub = os.path.join(self._ruta, sub)
                chip.clicked.connect(lambda chk=False, r=ruta_sub:
                    __import__("subprocess").Popen(["xdg-open", r]))
                chips.addWidget(chip)
            if len(self._subs) > 8:
                mas = QLabel("+" + str(len(self._subs) - 8))
                mas.setFont(QFont("Segoe UI", 8))
                mas.setStyleSheet("color:" + COLORS["text3"] + "; background:transparent;")
                chips.addWidget(mas)
            chips.addStretch()
            root.addLayout(chips)

    # ── Pintar degradado blanco→color ──────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color_hex)
        alpha_end = 160 if self._hover else 80
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), alpha_end))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        p.fillPath(path, QBrush(grad))
        p.end()

    # ── Animación hover: sube 3px ──────────────────────────
    def enterEvent(self, e):
        self._hover = True
        self.update()
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setEndValue(self.pos() - QPoint(0, 3))
        self._anim.start()

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setEndValue(self.pos() + QPoint(0, 3))
        self._anim.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click(self._nombre)


class MainWindow(QWidget):
    _archivo_movido_signal = pyqtSignal(str, str)  # thread-safe

    def __init__(self, carpeta_raiz, watcher, usuario=None, parent=None):
        super().__init__(parent)
        self.carpeta_raiz = carpeta_raiz
        self.watcher = watcher
        self._usuario = usuario or {}
        self._cerrando = False
        self._modo_eliminar = False
        self._modo_config = False
        self._carpeta_sel = None
        self._notas: dict = {}
        self._notas_globales: dict = {}
        self._email = self._usuario.get("email", "")
        self._modo  = self._usuario.get("modo", "personal")
        self._cargar_configs_db()

        self.setWindowTitle("TagFlow")
        self.setMinimumSize(480, 400)
        self.resize(740, 660)
        # Ícono de la app
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "tagflow_icon.png")
        if os.path.exists(_icon_path):
            from PyQt6.QtGui import QIcon
            _icon = QIcon(_icon_path)
            self.setWindowIcon(_icon)
            QApplication.instance().setWindowIcon(_icon)
        self._aplicar_estilo()
        self._build_ui()
        self._build_tray()
        # Conectar señal thread-safe para actualizaciones del watcher
        self._archivo_movido_signal.connect(self._on_archivo_movido_ui)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)

    def _cargar_configs_db(self):
        """Carga notas personales, colores y notas globales desde SQLite."""
        if not self._email:
            return
        try:
            import auth as _auth
            data = _auth.cargar_configs_carpetas(self._email)
            self._notas          = data.get("notas", {})
            self._notas_globales = data.get("notas_globales", {})
            for nombre, color in data.get("colores", {}).items():
                FOLDER_COLORS_CUSTOM[nombre] = color
        except Exception as e:
            print(f"[DB] No se pudieron cargar configs: {e}")

    def _aplicar_estilo(self):
        self.setStyleSheet(f"""
            QWidget {{ background: {COLORS['bg']}; font-family: 'Segoe UI','Helvetica Neue',sans-serif; color: {COLORS['text']}; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background: #C8C8C8; border-radius: 3px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QComboBox {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 10px;
                padding: 5px 32px 5px 12px; color: {COLORS['text']}; font-size: 13px; font-weight: 500; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox::down-arrow {{ width:0; height:0; border-left:4px solid transparent;
                border-right:4px solid transparent; border-top:5px solid {COLORS['text2']}; margin-right:10px; }}
            QComboBox QAbstractItemView {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']};
                border-radius: 10px; selection-background-color: {COLORS['accent_light']};
                selection-color: {COLORS['accent']}; color: {COLORS['text']}; padding: 4px; outline: none; font-size: 13px; }}
            QComboBox QAbstractItemView::item {{ padding: 8px 12px; border-radius: 6px; min-height: 28px; }}
            QLineEdit {{ background: {COLORS['surface']}; border: 1.5px solid {COLORS['border']};
                border-radius: 16px; padding: 9px 16px; color: {COLORS['text']}; font-size: 13px; }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
            QMenu {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']};
                border-radius: 12px; padding: 6px; color: {COLORS['text']}; }}
            QMenu::item {{ padding: 8px 16px; border-radius: 8px; font-size: 13px; }}
            QMenu::item:selected {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; }}
            QMenu::separator {{ height:1px; background:{COLORS['border']}; margin:4px 8px; }}
        """)

    # ── Tray ──────────────────────────────────────────────────

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "tagflow_icon.png")
        if os.path.exists(_icon_path):
            from PyQt6.QtGui import QIcon
            self.tray.setIcon(QIcon(_icon_path))
        self.tray.setIcon(_crear_icono_tray())
        self.tray.setToolTip("TagFlow")
        m = QMenu()
        m.addAction("Abrir TagFlow").triggered.connect(self._show)
        m.addAction("Abrir Inbox").triggered.connect(
            lambda: abrir_en_explorador(os.path.join(self.carpeta_raiz,"inbox")))
        m.addSeparator()
        m.addAction("Salir").triggered.connect(self._quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(
            lambda r: self._show() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()
        self.tray.showMessage("TagFlow activo","Organizando tus archivos.",
                              QSystemTrayIcon.MessageIcon.Information, 2500)

    def _show(self): self.show(); self.raise_(); self.activateWindow()
    def _quit(self):
        self._cerrando = True
        if self.watcher: self.watcher.detener()
        self.tray.hide(); QApplication.quit()

    def _abrir_empresarial(self):
        from ui.empresarial_window import EmpresarialWindow
        usuario = getattr(self, "_usuario_sesion", {})
        self._emp_win = EmpresarialWindow(usuario)
        self._emp_win.show()


    def _cerrar_sesion(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Cerrar sesion")
        msg.setText("Deseas cerrar sesion de TagFlow?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("Si, salir")
        msg.button(QMessageBox.StandardButton.No).setText("No")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                import auth as _auth
                _auth.cerrar_sesion()
            except: pass
            self._cerrando = True
            if self.watcher: self.watcher.detener()
            self.tray.hide()
            import subprocess, sys
            subprocess.Popen([sys.executable] + sys.argv)
            QApplication.quit()

    def closeEvent(self, e: QCloseEvent):
        if not self._cerrando and self.tray.isSystemTrayAvailable():
            e.ignore(); self.hide()
            self.tray.showMessage("TagFlow sigue activo","Corriendo en segundo plano.",
                                  QSystemTrayIcon.MessageIcon.Information, 2000)
        else: e.accept()

    # ── UI ────────────────────────────────────────────────────

    def _btn_toggle(self, texto, color_on, color_hover_off):
        """Crea un QPushButton con estilo de toggle."""
        b = QPushButton(texto)
        b.setFixedHeight(34)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        b.setGraphicsEffect(sombra(8, 28, 2))
        b._color_on = color_on
        b._color_hover_off = color_hover_off
        self._set_toggle_off(b)
        return b

    def _set_toggle_on(self, btn):
        btn.setStyleSheet(f"""
            QPushButton {{ background: {btn._color_on}; color: white;
                border-radius: 10px; border: none; padding: 0 14px; }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)

    def _set_toggle_off(self, btn):
        btn.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['surface']}; color: {COLORS['text2']};
                border-radius: 10px; border: 1px solid {COLORS['border']}; padding: 0 14px; }}
            QPushButton:hover {{ background: {btn._color_hover_off}; color: {btn._color_on}; border-color: {btn._color_on}; }}
        """)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Header ──────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(62)
        header.setStyleSheet(f"QFrame {{ background: {COLORS['header']}; border-bottom: 1px solid {COLORS['border']}; }}")
        header.setGraphicsEffect(sombra(20, 24, 4))
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20,0,20,0); hl.setSpacing(8)

        logo = QLabel()
        logo.setTextFormat(Qt.TextFormat.RichText)
        _ac = COLORS["accent"]
        _tx = COLORS["text"]
        logo.setText(
            f"<span style='color:{_ac};font-weight:800;'>@</span>"
            f"<span style='color:{_tx};font-weight:800;'>TagFlow</span>"
        )
        logo.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        logo.setStyleSheet("background: transparent;")
        hl.addWidget(logo)

        _s     = self._usuario
        _modo  = _s.get("modo", "personal")
        _admin = _s.get("admin", False)



        if _admin:
            _ab = QLabel("Admin")
            _ab.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            _ab.setStyleSheet("QLabel { color:#B45309; background:#FEF3C7; border-radius:8px; padding:2px 10px; }")
            hl.addSpacing(4); hl.addWidget(_ab)

        hl.addStretch()

        # Orden: Config | Eliminar | Recientes | Cerrar sesión

        # Toggle Config
        self.btn_config = self._btn_toggle("Config", COLORS['accent'], COLORS['accent_light'])
        self.btn_config.clicked.connect(self._toggle_config)
        hl.addWidget(self.btn_config)
        hl.addSpacing(6)

        # Toggle Eliminar
        self.btn_elim = self._btn_toggle("Eliminar", "#FF3B30", "#FFF0F0")
        self.btn_elim.clicked.connect(self._toggle_eliminar)
        hl.addWidget(self.btn_elim)
        hl.addSpacing(6)

        # Combo orden
        self.combo = QComboBox()
        self.combo.addItems(["Recientes", "A - Z", "Z - A"])
        self.combo.setMinimumWidth(120); self.combo.setMaximumWidth(180)
        self.combo.setFixedHeight(34)
        self.combo.setGraphicsEffect(sombra(10, 32, 3))
        self.combo.currentIndexChanged.connect(self._refresh)
        hl.addWidget(self.combo)
        root.addWidget(header)

        # ── Body ────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"background: {COLORS['bg']};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20,16,20,16); bl.setSpacing(10)

        self._zona_notif = QVBoxLayout(); self._zona_notif.setSpacing(8)
        bl.addLayout(self._zona_notif)

        self._header_tabla = HeaderTabla()
        bl.addWidget(self._header_tabla)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        self._cont = QWidget(); self._cont.setStyleSheet("background: transparent;")
        self._cont.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._list_lay = QVBoxLayout(self._cont)
        self._list_lay.setSpacing(7)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._cont)
        bl.addWidget(scroll, stretch=1)

        # Nueva carpeta
        nr = QHBoxLayout(); nr.setSpacing(10)
        self.inp_nueva = QLineEdit()
        self.inp_nueva.setPlaceholderText("Nueva carpeta...  (o renombra un archivo con @etiqueta)")
        self.inp_nueva.setFixedHeight(44)
        self.inp_nueva.setGraphicsEffect(sombra(16, 28, 4))
        self.inp_nueva.returnPressed.connect(self._crear_carpeta)
        nr.addWidget(self.inp_nueva)
        btn_crear = QPushButton("+ Crear")
        btn_crear.setFixedHeight(44)
        btn_crear.setMinimumWidth(80); btn_crear.setMaximumWidth(110)
        btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_crear.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        btn_crear.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['accent']}; color: white; border-radius: 16px; border: none; }}
            QPushButton:hover {{ background: {COLORS['accent_hover']}; }}
            QPushButton:pressed {{ background: #005BBB; }}
        """)
        btn_crear.setGraphicsEffect(sombra(16, 90, 5))
        btn_crear.clicked.connect(self._crear_carpeta)
        nr.addWidget(btn_crear)
        bl.addLayout(nr)

        self._bl_body = bl
        root.addWidget(body)
        self._refresh()

    # ── Toggles ───────────────────────────────────────────────

    def _toggle_config(self):
        self._modo_config = not self._modo_config
        if self._modo_config:
            self._modo_eliminar = False
            self._set_toggle_off(self.btn_elim)
            self._set_toggle_on(self.btn_config)
        else:
            self._set_toggle_off(self.btn_config)
        self._refresh()

    def _toggle_eliminar(self):
        self._modo_eliminar = not self._modo_eliminar
        if self._modo_eliminar:
            self._modo_config = False
            self._set_toggle_off(self.btn_config)
            self._set_toggle_on(self.btn_elim)
        else:
            self._set_toggle_off(self.btn_elim)
        self._refresh()

    # ── Refresh ───────────────────────────────────────────────

    def _refresh(self):
        # Actualizar header
        nuevo_h = HeaderTabla(self._modo_eliminar, self._modo_config)
        idx = self._bl_body.indexOf(self._header_tabla)
        if idx >= 0:
            self._bl_body.takeAt(idx)
            self._header_tabla.deleteLater()
            self._header_tabla = nuevo_h
            self._bl_body.insertWidget(idx, nuevo_h)

        # Limpiar lista
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        try:
            carpetas = [d for d in os.listdir(self.carpeta_raiz)
                        if os.path.isdir(os.path.join(self.carpeta_raiz, d))
                        and d.lower() != "inbox"
                        and "@" not in d]   # ignorar carpetas mal creadas con @ en nombre
        except:
            carpetas = []

        orden = self.combo.currentIndex()
        if orden == 0:
            carpetas.sort(key=lambda d: os.path.getmtime(os.path.join(self.carpeta_raiz, d)), reverse=True)
        elif orden == 1:
            carpetas.sort(key=str.casefold)
        else:
            carpetas.sort(key=str.casefold, reverse=True)

        if not carpetas:
            v = QLabel("Sin carpetas aún.\nRenombra cualquier archivo con  @etiqueta  para empezar.")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.setStyleSheet(f"color: {COLORS['text3']}; font-size: 13px; background: transparent;")
            self._list_lay.addWidget(v)
        else:
            for i, nombre in enumerate(carpetas, 1):
                ruta = os.path.join(self.carpeta_raiz, nombre)
                fila = FilaArbol(
                    i, nombre, ruta,
                    on_click=lambda n=nombre: self._sel_carpeta(n),
                    modo_eliminar=self._modo_eliminar,
                    on_eliminar=lambda n=nombre: self._confirmar_eliminar(n),
                    modo_config=self._modo_config,
                    on_config=lambda n=nombre: self._abrir_config(n),
                    nota=self._notas.get(nombre, ""),
                )
                self._list_lay.addWidget(fila)

    # ── Acciones ──────────────────────────────────────────────

    def _sel_carpeta(self, nombre):
        self._carpeta_sel = nombre

    def _confirmar_eliminar(self, nombre):
        ruta = os.path.join(self.carpeta_raiz, nombre)
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar carpeta")
        msg.setText(f'¿Seguro que quieres eliminar <b>"{nombre}"</b>?')
        msg.setInformativeText("Se eliminará la carpeta y todos sus archivos.\nEsta acción no se puede deshacer.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("Sí, eliminar")
        msg.button(QMessageBox.StandardButton.No).setText("No")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                shutil.rmtree(ruta)
                if nombre in self._notas: del self._notas[nombre]
                if nombre in FOLDER_COLORS_CUSTOM: del FOLDER_COLORS_CUSTOM[nombre]
                # Limpiar en BD
                if self._email:
                    try:
                        import auth as _auth
                        _auth.guardar_config_carpeta(self._email, nombre, "", "")
                    except: pass
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def _abrir_config(self, nombre):
        ruta = os.path.join(self.carpeta_raiz, nombre)
        dlg = ConfigCarpetaDialog(
            nombre, color_para_carpeta(nombre),
            self._notas.get(nombre, ""),
            self
        )
        if dlg.exec():
            nuevo_nombre, nuevo_color, nueva_nota, nueva_nota_global = dlg.resultado()
            # Renombrar si cambió
            if nuevo_nombre != nombre:
                nueva_ruta = os.path.join(self.carpeta_raiz, nuevo_nombre)
                try:
                    os.rename(ruta, nueva_ruta)
                    if nombre in self._notas:
                        self._notas[nuevo_nombre] = self._notas.pop(nombre)
                    if nombre in FOLDER_COLORS_CUSTOM:
                        FOLDER_COLORS_CUSTOM[nuevo_nombre] = FOLDER_COLORS_CUSTOM.pop(nombre)
                    # Migrar en BD
                    if self._email:
                        import auth as _auth
                        _auth.renombrar_config_carpeta(self._email, nombre, nuevo_nombre)
                    nombre = nuevo_nombre
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo renombrar:\n{e}"); return
            self._notas[nombre] = nueva_nota
            FOLDER_COLORS_CUSTOM[nombre] = nuevo_color
            # Guardar en SQLite
            if self._email:
                try:
                    import auth as _auth
                    _auth.guardar_config_carpeta(self._email, nombre, nueva_nota, nuevo_color)
                except Exception as e:
                    print(f"[DB] Error guardando config: {e}")
            self._refresh()

    def _crear_carpeta(self):
        nombre = self.inp_nueva.text().strip().lstrip("@").replace(" ","_")
        if not nombre: return
        ruta = os.path.join(self.carpeta_raiz, nombre)
        if os.path.exists(ruta):
            QMessageBox.information(self, "TagFlow", f"'{nombre}' ya existe."); return
        try:
            os.makedirs(ruta); self.inp_nueva.clear(); self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_archivo_movido(self, etiqueta, nombre):
        # Llamado desde hilo del watcher — solo emitir señal, nunca tocar widgets
        self._archivo_movido_signal.emit(etiqueta, nombre)

    def _on_archivo_movido_ui(self, etiqueta, nombre):
        # Llamado en el hilo principal — seguro tocar widgets
        banner = NotificacionBanner(etiqueta, nombre)
        self._zona_notif.addWidget(banner)
        self._refresh()
        QTimer.singleShot(4500, lambda: self._quitar_banner(banner))
        nc = nombre if len(nombre)<=35 else nombre[:32]+"..."
        self.tray.showMessage("TagFlow", f"{nc} -> /{etiqueta}/",
                              QSystemTrayIcon.MessageIcon.NoIcon, 3000)

    def _quitar_banner(self, banner):
        self._zona_notif.removeWidget(banner); banner.deleteLater()