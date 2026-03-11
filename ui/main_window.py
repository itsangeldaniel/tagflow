import os
import json
import platform
import subprocess
import hashlib
import shutil
import time as _time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QMessageBox,
    QSystemTrayIcon, QMenu, QApplication, QDialog, QTextEdit,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QPainterPath, QBrush

SISTEMA = platform.system()

# ── Paleta de colores (neutra, sin saturación exagerada) ───────────────────
P = {
    "bg":       "#FAFAFA",
    "surface":  "#FFFFFF",
    "border":   "#EBEBEB",
    "text":     "#111111",
    "text2":    "#555555",
    "text3":    "#AAAAAA",
    "accent":   "#2563EB",
    "acc_soft": "#EFF4FF",
    "danger":   "#D92B2B",
    "dan_soft": "#FEF2F2",
}

# 24 colores únicos — variedad máxima, sin repetición
FOLDER_PALETTE = [
    "#2563EB", "#16A34A", "#D97706", "#DC2626",
    "#7C3AED", "#0891B2", "#BE185D", "#059669",
    "#9333EA", "#EA580C", "#0284C7", "#65A30D",
    "#0D9488", "#B45309", "#7E22CE", "#0369A1",
    "#15803D", "#C2410C", "#6D28D9", "#0F766E",
    "#B91C1C", "#1D4ED8", "#A21CAF", "#047857",
]

FOLDER_COLORS_CUSTOM: dict = {}

# Anchos de columna (px)
W_NUM   = 36
W_ARCH  = 106
W_DATE  = 118


def _color(nombre: str) -> str:
    if nombre in FOLDER_COLORS_CUSTOM:
        return FOLDER_COLORS_CUSTOM[nombre]
    return FOLDER_PALETTE[int(hashlib.md5(nombre.encode()).hexdigest(), 16) % len(FOLDER_PALETTE)]


def _open(ruta: str):
    """Abre una carpeta en el explorador nativo."""
    try:
        if SISTEMA == "Windows":
            os.startfile(ruta)
        elif SISTEMA == "Darwin":
            subprocess.Popen(["open", ruta])
        else:
            for cmd in ["xdg-open", "nautilus", "dolphin", "thunar", "nemo"]:
                try:
                    subprocess.Popen([cmd, ruta],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
                    return
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"[open] {e}")


def _tray_icon() -> QIcon:
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(P["accent"]))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 10, 10)
    p.setPen(QColor("white"))
    p.setFont(QFont("Arial", 30, QFont.Weight.Bold))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "@")
    p.end()
    return QIcon(px)


# ── ColorDot ────────────────────────────────────────────────────────────────

class _Dot(QFrame):
    def __init__(self, hex_c: str, selected: bool, dlg, parent=None):
        super().__init__(parent)
        self.hex_c = hex_c
        self._sel  = selected
        self._dlg  = dlg
        self.setFixedSize(26, 26)
        self._paint()

    def _paint(self):
        b = f"2px solid {P['accent']}" if self._sel else "2px solid transparent"
        self.setStyleSheet(f"QFrame{{background:{self.hex_c};border-radius:13px;border:{b};}}")

    def mark(self, v):
        self._sel = v
        self._paint()

    def mousePressEvent(self, e):
        self._dlg._pick(self)


# ── Diálogo de configuración de carpeta ─────────────────────────────────────

class CarpetaConfig(QDialog):
    PALETA = [
        "#2563EB",  # azul
        "#0891B2",  # cian
        "#0D9488",  # teal
        "#16A34A",  # verde
        "#84CC16",  # lima
        "#EAB308",  # amarillo
        "#F97316",  # naranja
        "#EF4444",  # rojo
        "#EC4899",  # rosa
        "#A855F7",  # violeta
        "#6366F1",  # índigo
        "#14B8A6",  # turquesa
        "#22C55E",  # verde claro
        "#FB923C",  # melocotón
        "#F43F5E",  # rojo-rosa
        "#8B5CF6",  # púrpura
        "#64748B",  # pizarra
        "#0EA5E9",  # celeste
    ]

    def __init__(self, nombre, color_actual, nota_actual, parent=None):
        super().__init__(parent)
        self._orig  = nombre
        self._color = color_actual
        self._dots  = []
        self.setWindowTitle(f"Configurar — {nombre}")
        self.setFixedWidth(360)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{background:{P['surface']};font-family:'Segoe UI',sans-serif;}}
            QLineEdit,QTextEdit {{
                background:{P['bg']};border:1px solid {P['border']};
                border-radius:5px;padding:7px 11px;
                color:{P['text']};font-size:13px;
            }}
            QLineEdit:focus,QTextEdit:focus {{border-color:{P['accent']};}}
        """)
        self._build(nombre, color_actual, nota_actual)

    def _lbl(self, t):
        l = QLabel(t)
        l.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        l.setStyleSheet(f"color:{P['text3']};letter-spacing:0.7px;background:transparent;")
        return l

    def _build(self, nombre, color_actual, nota_actual):
        v = QVBoxLayout(self)
        v.setContentsMargins(22, 22, 22, 18)
        v.setSpacing(14)

        title = QLabel("Configurar carpeta")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{P['text']};")
        v.addWidget(title)

        v.addWidget(self._lbl("NOMBRE"))
        self.inp_n = QLineEdit(nombre)
        self.inp_n.setFixedHeight(36)
        v.addWidget(self.inp_n)

        v.addWidget(self._lbl("COLOR"))
        grid = QFrame()
        grid.setStyleSheet(f"QFrame{{background:{P['bg']};border-radius:6px;border:1px solid {P['border']}}}")
        gl = QVBoxLayout(grid)
        gl.setContentsMargins(10, 10, 10, 10)
        gl.setSpacing(8)
        for i in range(0, len(self.PALETA), 6):
            row = QHBoxLayout()
            row.setSpacing(8)
            for c in self.PALETA[i:i+6]:
                dot = _Dot(c, c == color_actual, self, grid)
                self._dots.append(dot)
                row.addWidget(dot)
            row.addStretch()
            gl.addLayout(row)
        v.addWidget(grid)

        v.addWidget(self._lbl("NOTA  (opcional)"))
        self.inp_nota = QTextEdit()
        self.inp_nota.setPlainText(nota_actual[:100])
        self.inp_nota.setFixedHeight(68)
        self.inp_nota.setPlaceholderText("Máx. 100 caracteres…")
        self.inp_nota.textChanged.connect(self._limit_nota)
        v.addWidget(self.inp_nota)

        btns = QHBoxLayout(); btns.setSpacing(8)
        cancel = QPushButton("Cancelar")
        cancel.setFixedHeight(36)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""QPushButton{{background:{P['bg']};color:{P['text2']};
            border:1px solid {P['border']};border-radius:5px;font-size:12px;}}
            QPushButton:hover{{background:{P['border']};}}""")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Guardar")
        save.setFixedHeight(36)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setStyleSheet(f"""QPushButton{{background:{P['accent']};color:white;
            border:none;border-radius:5px;font-size:12px;font-weight:bold;}}
            QPushButton:hover{{background:#1D4ED8;}}""")
        save.clicked.connect(self.accept)

        btns.addWidget(cancel)
        btns.addWidget(save)
        v.addLayout(btns)

    def _limit_nota(self):
        txt = self.inp_nota.toPlainText()
        if len(txt) > 100:
            cursor = self.inp_nota.textCursor()
            self.inp_nota.blockSignals(True)
            self.inp_nota.setPlainText(txt[:100])
            self.inp_nota.blockSignals(False)
            cursor.setPosition(100)
            self.inp_nota.setTextCursor(cursor)

    def _pick(self, dot):
        for d in self._dots:
            d.mark(d is dot)
        self._color = dot.hex_c

    def result_data(self):
        n = self.inp_n.text().strip().replace(" ", "_") or self._orig
        return n, self._color, self.inp_nota.toPlainText().strip()


# ── Cabecera de tabla ────────────────────────────────────────────────────────

class TableHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"background:transparent;")
        lay = QHBoxLayout(self)
        # Márgenes: izq=24 (12 del contenedor + 12 padding tarjeta) + num_w=W_NUM+8
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(0)

        def th(txt, w=None, center=False):
            l = QLabel(txt)
            l.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            l.setStyleSheet(f"color:{P['text3']};letter-spacing:0.8px;background:transparent;")
            if w:
                l.setFixedWidth(w)
            if center:
                l.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            else:
                l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            return l

        # Mismo layout que FolderRow._build → main_row
        lay.addWidget(th("#", W_NUM + 8, center=True))  # num_w
        lay.addSpacing(4)                                  # spacing(4)
        lay.addWidget(th("CARPETA"))                      # nombre
        lay.addStretch()
        lay.addWidget(th("ARCHIVOS", W_ARCH, center=True))
        lay.addWidget(th("MODIFICADO", W_DATE, center=True))
        lay.addSpacing(52)    # hueco botón ▶
        lay.addSpacing(4+4)   # espaciados internos



class _ChipSub(QWidget):
    """Chip de subcarpeta con sombra coloreada igual que la tarjeta padre."""
    def __init__(self, nombre, ruta, parent=None):
        super().__init__(parent)
        self._nombre = nombre
        self._ruta   = ruta
        self._color  = _color(nombre)
        self._alpha  = 0.0
        self._va     = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background:transparent;")
        # Contenido
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 5, 14, 5)
        lbl = QLabel(nombre)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        c = QColor(self._color)
        lbl.setStyleSheet(f"color:rgb({c.red()},{c.green()},{c.blue()});background:transparent;")
        lay.addWidget(lbl)
        self.setFixedHeight(28)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        c = QColor(self._color)
        cr, cg, cb = c.red(), c.green(), c.blue()
        m = self.contentsMargins()
        W, H = self.width(), self.height()
        PAD2 = 3
        cx, cy = PAD2, PAD2
        cw, ch = W - PAD2*2, H - PAD2*2
        R = 10
        base = int(90 + self._alpha * 100)
        for dx, dy, ex, af in [(0,2,5,0.40),(0,6,14,0.18)]:
            a = max(0, min(255, int(base * af)))
            path = QPainterPath()
            path.addRoundedRect(cx-ex//2+dx, cy-ex//2+dy, cw+ex, ch+ex, R+ex//3, R+ex//3)
            p.fillPath(path, QColor(cr, cg, cb, a))
        card = QPainterPath()
        card.addRoundedRect(cx, cy, cw, ch, R, R)
        p.fillPath(card, QColor(255, 255, 255, 240))
        p.setPen(QColor(cr, cg, cb, 110))
        p.drawPath(card)
        p.end()

    def _anim(self, enter):
        if self._va: self._va.stop()
        va = QVariantAnimation(self)
        va.setStartValue(self._alpha)
        va.setEndValue(1.0 if enter else 0.0)
        va.setDuration(140); va.setEasingCurve(QEasingCurve.Type.OutCubic)
        va.valueChanged.connect(lambda v: self._tick(v))
        self._va = va; va.start()

    def _tick(self, v):
        self._alpha = v; self.update()

    def enterEvent(self, e): self._anim(True)
    def leaveEvent(self, e): self._anim(False)
    def mousePressEvent(self, e): _open(self._ruta)

# ── Fila de carpeta ──────────────────────────────────────────────────────────

class FolderRow(QWidget):
    """
    Fila de una carpeta. Diseño lineal, sin sombras ni bordes redondeados.
    Hover: fondo tintado suave animado.
    Subcarpetas expandibles en chips pequeños.
    """

    def __init__(self, numero, nombre, ruta,
                 on_click=None, modo_elim=False, on_elim=None,
                 modo_cfg=False, on_cfg=None, nota="", parent=None):
        super().__init__(parent)
        self._num       = numero
        self._nombre    = nombre
        self._ruta      = ruta
        self._on_click  = on_click
        self._on_elim   = on_elim
        self._on_cfg    = on_cfg
        self._modo_elim = modo_elim
        self._modo_cfg  = modo_cfg
        self._nota      = nota
        self._expanded  = False
        self._color     = _color(nombre)
        self._subs      = self._subs_list()
        self._alpha     = 0.0
        self._va        = None
        self.setContentsMargins(20, 0, 20, 0)
        self.setStyleSheet("background:transparent;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    # ── helpers ─────────────────────────────────────────────

    def _subs_list(self):
        try:
            return sorted(
                [d for d in os.listdir(self._ruta)
                 if os.path.isdir(os.path.join(self._ruta, d))],
                key=str.casefold)
        except:
            return []

    def _count_files(self):
        try:
            return len([f for f in os.listdir(self._ruta)
                        if os.path.isfile(os.path.join(self._ruta, f))])
        except:
            return 0

    def _date_str(self):
        try:
            return _time.strftime("%d/%m/%Y",
                                  _time.localtime(os.path.getmtime(self._ruta)))
        except:
            return "—"

    # ── construcción ────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── fila principal ───────────────────────────────────
        main_row = QHBoxLayout()
        main_row.setContentsMargins(6, 10, 18, 10)
        main_row.setSpacing(0)

        # Número — widget propio para colorear en hover
        c = QColor(self._color)
        r, g, b = c.red(), c.green(), c.blue()
        self._num_w = QWidget()
        self._num_w.setFixedWidth(W_NUM + 8)
        self._num_w.setStyleSheet("background:transparent;")
        nl = QHBoxLayout(self._num_w)
        nl.setContentsMargins(0, 0, 0, 0)
        num_lbl = QLabel(str(self._num))
        num_lbl.setFont(QFont("DM Sans", 10) if True else QFont("Segoe UI", 10))
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        num_lbl.setStyleSheet(f"color:{P['text3']};background:transparent;")
        self._num_lbl = num_lbl
        nl.addWidget(num_lbl)
        main_row.addWidget(self._num_w)

        # Nombre
        self._name_lbl = QLabel(self._nombre)
        self._name_lbl.setFont(QFont("DM Sans", 13) if True else QFont("Segoe UI", 13))
        self._name_lbl.setStyleSheet(f"color:{P['text']};background:transparent;")
        main_row.addSpacing(4)
        main_row.addWidget(self._name_lbl)
        main_row.addStretch()

        # Archivos
        n = self._count_files()
        arc_lbl = QLabel(f"{n} archivo{'s' if n != 1 else ''}")
        arc_lbl.setFixedWidth(W_ARCH)
        arc_lbl.setFont(QFont("Segoe UI", 10))
        arc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        arc_lbl.setStyleSheet(f"color:{P['text2']};background:transparent;")
        main_row.addWidget(arc_lbl)

        # Fecha
        date_lbl = QLabel(self._date_str())
        date_lbl.setFixedWidth(W_DATE)
        date_lbl.setFont(QFont("Segoe UI", 10))
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        date_lbl.setStyleSheet(f"color:{P['text2']};background:transparent;")
        main_row.addWidget(date_lbl)

        # ── botón subcarpetas — SIEMPRE reserva espacio ─────
        c2 = QColor(self._color)
        r2, g2, b2 = c2.red(), c2.green(), c2.blue()
        self._btn_sub = QPushButton()
        self._btn_sub.setFixedSize(58, 26)
        self._btn_sub.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if self._subs:
            self._btn_sub.setText(f"▶  {len(self._subs)}")
            self._btn_sub.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_sub.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self._btn_sub.setStyleSheet(
                f"QPushButton{{background:rgba({r2},{g2},{b2},30);"
                f"color:{self._color};border:none;border-radius:6px;letter-spacing:1px;}}"
                f"QPushButton:hover{{background:rgba({r2},{g2},{b2},60);}}"
            )
            self._btn_sub.clicked.connect(self._toggle)
        else:
            self._btn_sub.setEnabled(False)
            self._btn_sub.setStyleSheet("QPushButton{background:transparent;border:none;}")
        main_row.addSpacing(4)
        main_row.addWidget(self._btn_sub)

        # ── config ───────────────────────────────────────
        if self._modo_cfg:
            btn = QPushButton("⚙")
            btn.setFixedSize(26, 22)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 12))
            btn.setStyleSheet(
                f"QPushButton{{background:{P['acc_soft']};color:{P['accent']};"
                f"border:none;border-radius:3px;}}"
                f"QPushButton:hover{{background:{P['accent']};color:white;}}"
            )
            n_ = self._nombre
            btn.clicked.connect(lambda _, n=n_: self._on_cfg(n) if self._on_cfg else None)
            main_row.addSpacing(4)
            main_row.addWidget(btn)

        # ── eliminar ─────────────────────────────────────
        if self._modo_elim:
            btn = QPushButton("✕")
            btn.setFixedSize(26, 22)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet(
                f"QPushButton{{background:{P['dan_soft']};color:{P['danger']};"
                f"border:none;border-radius:3px;}}"
                f"QPushButton:hover{{background:{P['danger']};color:white;}}"
            )
            n_ = self._nombre
            btn.clicked.connect(lambda _, n=n_: self._on_elim(n) if self._on_elim else None)
            main_row.addSpacing(4)
            main_row.addWidget(btn)

        root.addLayout(main_row)

        # ── nota (multi-línea, no expande horizontal) ─────
        if self._nota:
            nw = QWidget()
            nw.setStyleSheet("background:transparent;")
            nl = QHBoxLayout(nw)
            nl.setContentsMargins(W_NUM + 16, 0, 12, 8)
            nl.setSpacing(6)
            pfx = QLabel("Nota:")
            pfx.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            pfx.setStyleSheet(f"color:{P['text3']};background:transparent;")
            pfx.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            pfx.setAlignment(Qt.AlignmentFlag.AlignTop)
            nl.addWidget(pfx)
            nota_txt = self._nota[:100]
            ntxt = QLabel(nota_txt)
            ntxt.setFont(QFont("Segoe UI", 9))
            ntxt.setStyleSheet(f"color:{P['text2']};background:transparent;")
            ntxt.setWordWrap(True)
            ntxt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            nl.addWidget(ntxt, stretch=1)
            root.addWidget(nw)

        # ── zona subcarpetas ──────────────────────────────
        self._sub_zone = QWidget()
        self._sub_zone.setStyleSheet("background:transparent;")
        self._sub_lay = QVBoxLayout(self._sub_zone)
        self._sub_lay.setContentsMargins(0, 0, 0, 6)
        self._sub_lay.setSpacing(2)
        self._sub_zone.hide()
        root.addWidget(self._sub_zone)

        # sin separador — el gap entre tarjetas es suficiente

    # ── subcarpetas por nivel ────────────────────────────

    def _toggle(self):
        self._expanded = not self._expanded
        sym = "▼" if self._expanded else "▶"
        if self._btn_sub:
            self._btn_sub.setText(f"{sym}  {len(self._subs)}")
        if self._expanded:
            # limpiar y reconstruir
            while self._sub_lay.count():
                it = self._sub_lay.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            self._add_level(self._ruta, 0)
            self._sub_zone.show()
        else:
            while self._sub_lay.count():
                it = self._sub_lay.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            self._sub_zone.hide()

    def _add_level(self, parent_path, indent):
        try:
            children = sorted(
                [d for d in os.listdir(parent_path)
                 if os.path.isdir(os.path.join(parent_path, d))],
                key=str.casefold)
        except:
            return
        if not children:
            return

        row_w = QWidget()
        row_w.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row_w)
        rl.setContentsMargins(W_NUM + 14 + indent * 16, 2, 16, 2)
        rl.setSpacing(6)

        for child in children:
            child_path = os.path.join(parent_path, child)
            chip = _ChipSub(child, child_path)
            rl.addWidget(chip)

        rl.addStretch()
        self._sub_lay.addWidget(row_w)

        for child in children:
            self._add_level(os.path.join(parent_path, child), indent + 1)

    # ── paint: sombra coloreada + tarjeta blanca ────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        c  = QColor(self._color)
        cr, cg, cb = c.red(), c.green(), c.blue()
        m  = self.contentsMargins()
        W, H = self.width(), self.height()
        # Tarjeta: ocupa todo el alto, márgenes laterales del widget
        PAD = 6      # espacio para sombra alrededor
        cx = m.left() + PAD
        cy = PAD
        cw = W - m.left() - m.right() - PAD * 2
        ch = H - PAD * 2
        R  = 22

        # Una sola sombra difusa hacia abajo — no se corta
        shadow_a = int(55 + self._alpha * 50)   # 55..105
        sh = QPainterPath()
        sh.addRoundedRect(cx, cy + 4, cw, ch, R, R)
        p.fillPath(sh, QColor(cr, cg, cb, shadow_a))

        # Tarjeta blanca encima
        card = QPainterPath()
        card.addRoundedRect(cx, cy, cw, ch, R, R)
        p.fillPath(card, QColor(255, 255, 255, 255))

        # Borde coloreado 1px
        p.setPen(QColor(cr, cg, cb, int(100 + self._alpha * 60)))
        p.drawPath(card)

        p.end()

    def _hover_anim(self, enter):
        if self._va:
            self._va.stop()
        va = QVariantAnimation(self)
        va.setStartValue(self._alpha)
        va.setEndValue(1.0 if enter else 0.0)
        va.setDuration(180)
        va.setEasingCurve(QEasingCurve.Type.OutCubic)
        va.valueChanged.connect(lambda v: self._set_a(v))
        self._va = va
        va.start()

    def _set_a(self, v):
        self._alpha = v
        self.update()

    def enterEvent(self, e):
        self._hover_anim(True)

    def leaveEvent(self, e):
        self._hover_anim(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click(self._nombre)


# ── Ventana principal ────────────────────────────────────────────────────────

class MainWindow(QWidget):
    _sig = pyqtSignal(str, str)

    def __init__(self, carpeta_raiz, watcher, usuario=None, parent=None):
        super().__init__(parent)
        self.carpeta_raiz = carpeta_raiz
        self.watcher      = watcher
        self._email       = (usuario or {}).get("email", "")
        self._modo_elim   = False
        self._modo_cfg    = False
        self._notas: dict = {}
        self._expanded: set = set()
        self._cargar_db()
        self.setWindowTitle("TagFlow")
        self.setMinimumSize(500, 380)
        self.resize(780, 600)
        self._build_style()
        self._build_ui()
        self._build_tray()
        self._sig.connect(self._on_moved)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    # ── DB ─────────────────────────────────────────────────

    def _cargar_db(self):
        if not self._email:
            return
        # Cargar desde archivo local JSON
        cfg_path = os.path.join(self.carpeta_raiz, ".tagflow_config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            self._notas = d.get("notas", {})
            for n, c in d.get("colores", {}).items():
                FOLDER_COLORS_CUSTOM[n] = c
        except:
            pass

    # ── Estilo global ───────────────────────────────────────

    def _build_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background:{P['bg']};
                font-family:'Segoe UI','Helvetica Neue',sans-serif;
                color:{P['text']};
            }}
            QScrollBar:vertical {{
                background:transparent; width:5px;
            }}
            QScrollBar::handle:vertical {{
                background:{P['border']}; border-radius:2px; min-height:24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QLineEdit {{
                background:{P['surface']};
                border:1px solid {P['border']};
                border-radius:5px;
                padding:7px 13px;
                color:{P['text']};
                font-size:13px;
            }}
            QLineEdit:focus {{ border-color:{P['accent']}; }}
            QComboBox {{
                background:{P['surface']};
                border:1px solid {P['border']};
                border-radius:5px;
                padding:4px 26px 4px 10px;
                color:{P['text']};
                font-size:12px;
            }}
            QComboBox::drop-down {{ border:none; width:0px; }}
            QComboBox::down-arrow {{ width:0; height:0; image:none; }}
            QComboBox QAbstractItemView {{
                background:{P['surface']};
                border:1px solid {P['border']};
                border-radius:5px;
                selection-background-color:{P['acc_soft']};
                selection-color:{P['accent']};
                padding:3px;
                outline:none;
            }}
            QMenu {{
                background:{P['surface']};
                border:1px solid {P['border']};
                border-radius:7px;
                padding:4px;
                color:{P['text']};
            }}
            QMenu::item {{ padding:7px 14px; border-radius:4px; font-size:12px; }}
            QMenu::item:selected {{ background:{P['acc_soft']}; color:{P['accent']}; }}
        """)

    # ── UI ─────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─ Topbar ─────────────────────────────────────────
        top = QWidget()
        top.setFixedHeight(50)
        top.setStyleSheet(
            f"background:{P['surface']};"
            f"border-bottom:1px solid {P['border']};"
        )
        tl = QHBoxLayout(top)
        tl.setContentsMargins(16, 0, 12, 0)
        tl.setSpacing(8)

        logo = QLabel()
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setText(
            f"<span style='color:{P['accent']};font-weight:800;font-size:17px;'>@</span>"
            f"<span style='font-weight:700;font-size:17px;'>TagFlow</span>"
        )
        logo.setStyleSheet("background:transparent;")
        tl.addWidget(logo)
        tl.addStretch()

        def _tbtn(label, checkable=False, danger=False):
            b = QPushButton(label)
            b.setFixedHeight(30)
            b.setFont(QFont("Segoe UI", 11))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setCheckable(checkable)
            if danger:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background:{P['surface']}; color:{P['text2']};
                        border:1px solid {P['border']};
                        border-bottom:2px solid #D0D0D0;
                        border-radius:5px; padding:0 13px;
                    }}
                    QPushButton:hover {{
                        background:{P['dan_soft']}; color:{P['danger']};
                        border-color:{P['danger']}; border-bottom-color:#B00000;
                    }}
                    QPushButton:checked {{
                        background:{P['danger']}; color:white;
                        border-color:{P['danger']}; border-bottom-color:#900000;
                    }}
                    QPushButton:pressed {{
                        border-bottom-width:1px; padding-top:1px;
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background:{P['surface']}; color:{P['text2']};
                        border:1px solid {P['border']};
                        border-bottom:2px solid #C8C8C8;
                        border-radius:5px; padding:0 13px;
                    }}
                    QPushButton:hover {{
                        background:{P['acc_soft']}; color:{P['accent']};
                        border-color:{P['accent']}; border-bottom-color:#1040B0;
                    }}
                    QPushButton:checked {{
                        background:{P['accent']}; color:white;
                        border-color:{P['accent']}; border-bottom-color:#1030A0;
                    }}
                    QPushButton:pressed {{
                        border-bottom-width:1px; padding-top:1px;
                    }}
                """)
            return b

        self.btn_cfg  = _tbtn("⚙  Config", checkable=True)
        self.btn_elim = _tbtn("✕  Eliminar", checkable=True, danger=True)
        self.btn_cfg.clicked.connect(self._toggle_cfg)
        self.btn_elim.clicked.connect(self._toggle_elim)
        tl.addWidget(self.btn_cfg)
        tl.addWidget(self.btn_elim)

        self.combo = QComboBox()
        self.combo.addItems(["Recientes  ▾", "A → Z  ▾", "Z → A  ▾"])
        self.combo.setFixedSize(130, 30)
        self.combo.currentIndexChanged.connect(self._refresh)
        tl.addWidget(self.combo)

        btn_q = QPushButton("?")
        btn_q.setFixedSize(26, 26)
        btn_q.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_q.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_q.setStyleSheet(f"""
            QPushButton {{
                background:{P['acc_soft']}; color:{P['accent']};
                border-radius:15px; border:none;
            }}
            QPushButton:hover {{ background:{P['accent']}; color:white; }}
        """)
        btn_q.clicked.connect(self._ayuda)
        tl.addWidget(btn_q)

        root.addWidget(top)

        # ─ Header tabla ────────────────────────────────────
        self._hdr = TableHeader()
        root.addWidget(self._hdr)

        # ─ Lista ───────────────────────────────────────────
        self._cont = QWidget()
        self._cont.setStyleSheet(f"background:{P['bg']};")
        self._lay = QVBoxLayout(self._cont)
        self._lay.setContentsMargins(4, 10, 4, 10)
        self._lay.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidget(self._cont)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background:{P['bg']};")
        root.addWidget(scroll, stretch=1)

        # ─ Barra inferior ──────────────────────────────────
        bot = QWidget()
        bot.setFixedHeight(54)
        bot.setStyleSheet(
            f"background:{P['surface']};"
            f"border-top:1px solid {P['border']};"
        )
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(12, 0, 12, 0)
        bl.setSpacing(8)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Ej: MiCarpeta  o  sub@MiCarpeta para subcarpeta")
        self.inp.setFixedHeight(34)
        self.inp.returnPressed.connect(self._crear)
        bl.addWidget(self.inp)

        btn_add = QPushButton("Crear")
        btn_add.setFixedSize(72, 34)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_add.setStyleSheet(f"""
            QPushButton {{ background:{P['accent']};color:white;
                border-radius:5px;border:none;
                border-bottom: 2px solid #1A3FA8;}}
            QPushButton:hover {{ background:#1D4ED8; }}
            QPushButton:pressed {{ border-bottom:0px; padding-top:2px; }}
        """)
        btn_add.clicked.connect(self._crear)
        bl.addWidget(btn_add)
        root.addWidget(bot)

        self._refresh()

    # ── Tray ───────────────────────────────────────────────

    def _build_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return
        self.tray = QSystemTrayIcon(_tray_icon(), self)
        m = QMenu()
        m.addAction("Mostrar", self.show)
        m.addSeparator()
        m.addAction("Salir", self._quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(
            lambda r: self.show()
            if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    # ── Refresh ─────────────────────────────────────────────

    def _fs_snapshot(self):
        """Snapshot: nombres y mtime de todos los dirs para detectar renombres."""
        snap = []
        try:
            for root_dir, dirs, files in os.walk(self.carpeta_raiz):
                dirs[:] = sorted([d for d in dirs if not d.startswith(".")])
                rel = os.path.relpath(root_dir, self.carpeta_raiz)
                try:
                    mtime = round(os.path.getmtime(root_dir), 2)
                except:
                    mtime = 0
                # Incluir nombre + mtime + lista de hijos (detecta renombres)
                snap.append((rel, mtime, tuple(dirs)))
        except:
            pass
        return tuple(snap)

    def _refresh(self):
        # Solo reconstruir si algo cambió (filesystem O modo UI)
        snap = self._fs_snapshot()
        ui_state = (self._modo_cfg, self._modo_elim, self.combo.currentIndex())
        full_state = (snap, ui_state)
        if hasattr(self, "_last_snap") and full_state == self._last_snap:
            return
        self._last_snap = full_state

        # Guardar estado expandido
        self._expanded = set()
        for i in range(self._lay.count()):
            it = self._lay.itemAt(i)
            if it and it.widget() and isinstance(it.widget(), FolderRow):
                if it.widget()._expanded:
                    self._expanded.add(it.widget()._nombre)

        # Limpiar lista
        while self._lay.count():
            it = self._lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        # Carpetas
        try:
            carpetas = [d for d in os.listdir(self.carpeta_raiz)
                        if os.path.isdir(os.path.join(self.carpeta_raiz, d))
                        and d.lower() != "inbox"]
        except:
            carpetas = []

        orden = self.combo.currentIndex()
        if orden == 0:
            carpetas.sort(
                key=lambda d: os.path.getmtime(os.path.join(self.carpeta_raiz, d)),
                reverse=True)
        elif orden == 1:
            carpetas.sort(key=str.casefold)
        else:
            carpetas.sort(key=str.casefold, reverse=True)
        # (currentIndex es 0/1/2 independiente del texto)

        if not carpetas:
            empty = QLabel(
                "Sin carpetas todavía.\n"
                "Renombra cualquier archivo con  @etiqueta  para empezar."
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{P['text3']};font-size:13px;"
                f"background:transparent;padding:50px;")
            self._lay.addWidget(empty)
        else:
            for i, nombre in enumerate(carpetas, 1):
                ruta = os.path.join(self.carpeta_raiz, nombre)
                row = FolderRow(
                    i, nombre, ruta,
                    on_click=lambda n=nombre: _open(os.path.join(self.carpeta_raiz, n)),
                    modo_elim=self._modo_elim,
                    on_elim=lambda n=nombre: self._confirmar_elim(n),
                    modo_cfg=self._modo_cfg,
                    on_cfg=lambda n=nombre: self._cfg(n),
                    nota=self._notas.get(nombre, ""),
                )
                # Restaurar expandido
                if nombre in self._expanded:
                    row._expanded = True
                    row._add_level(row._ruta, 0)
                    row._sub_zone.show()
                    if row._btn_sub:
                        row._btn_sub.setText(f"▼  {len(row._subs)}")
                self._lay.addWidget(row)

        self._lay.addStretch()

    # ── Acciones ────────────────────────────────────────────

    def _toggle_cfg(self):
        self._modo_cfg = self.btn_cfg.isChecked()
        if self._modo_cfg:
            self._modo_elim = False
            self.btn_elim.setChecked(False)
        self._refresh()

    def _toggle_elim(self):
        self._modo_elim = self.btn_elim.isChecked()
        if self._modo_elim:
            self._modo_cfg = False
            self.btn_cfg.setChecked(False)
        self._refresh()

    def _confirmar_elim(self, nombre):
        ruta = os.path.join(self.carpeta_raiz, nombre)
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar carpeta")
        msg.setText(f"¿Eliminar <b>{nombre}</b> y todo su contenido?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Yes).setText("Sí")
        msg.button(QMessageBox.StandardButton.Cancel).setText("No")
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                # Intentar enviar a papelera, si falla borrar permanente
                try:
                    import send2trash
                    send2trash.send2trash(ruta)
                except ImportError:
                    # send2trash no instalado — mover a ~/.Trash manualmente
                    import platform as _pl
                    if _pl.system() == 'Darwin':
                        trash = os.path.expanduser('~/.Trash')
                        shutil.move(ruta, os.path.join(trash, nombre))
                    elif _pl.system() == 'Linux':
                        trash = os.path.expanduser('~/.local/share/Trash/files')
                        os.makedirs(trash, exist_ok=True)
                        shutil.move(ruta, os.path.join(trash, nombre))
                    else:
                        shutil.rmtree(ruta)  # Windows sin send2trash
                self._notas.pop(nombre, None)
                FOLDER_COLORS_CUSTOM.pop(nombre, None)
                if hasattr(self, '_last_snap'): del self._last_snap
                self._refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _cfg(self, nombre):
        color_actual = FOLDER_COLORS_CUSTOM.get(nombre, _color(nombre))
        nota_actual  = self._notas.get(nombre, "")
        dlg = CarpetaConfig(nombre, color_actual, nota_actual, self)
        if dlg.exec():
            _, color, nota = dlg.result_data()
            if color:
                FOLDER_COLORS_CUSTOM[nombre] = color
                if self._email:
                    try:
                        import auth as _a
                        _a.guardar_config_carpeta(self._email, nombre, color=color)
                    except:
                        pass
            if nota is not None:
                self._notas[nombre] = nota
                if self._email:
                    try:
                        import auth as _a
                        _a.guardar_config_carpeta(self._email, nombre, nota=nota)
                    except:
                        pass
            self._guardar_config()
            if hasattr(self, '_last_snap'):
                del self._last_snap
            self._refresh()

    def _guardar_config(self):
        cfg_path = os.path.join(self.carpeta_raiz, ".tagflow_config.json")
        try:
            data = {
                "notas":   self._notas,
                "colores": {k: v for k, v in FOLDER_COLORS_CUSTOM.items()},
            }
            with open(cfg_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CONFIG] Error guardando: {e}")

    def _crear(self):
        nombre = self.inp.text().strip()
        if not nombre:
            return
        # Parsear @ para subcarpetas: "sub@padre" → padre/sub
        import re as _re
        partes = _re.split(r'@', nombre)
        if len(partes) == 1:
            # Carpeta principal simple
            ruta = os.path.join(self.carpeta_raiz, partes[0].strip())
        else:
            # sub@padre  o  sub@padre@abuelo → carpeta_raiz/padre/sub
            # La jerarquía va de derecha a izquierda: partes[-1] es la raíz
            partes = [p.strip() for p in partes if p.strip()]
            # Formato: nombre@carpeta  o  nombre@carpeta@subcarpeta
            # → construir ruta: raiz/carpeta[/subcarpeta...]/nombre
            carpetas = partes[1:]   # todo lo que va después del @
            sub_nombre = partes[0]  # lo que va antes del primer @
            ruta = os.path.join(self.carpeta_raiz, *carpetas, sub_nombre)
        if not os.path.exists(ruta):
            os.makedirs(ruta, exist_ok=True)
        self.inp.clear()
        if hasattr(self, '_last_snap'):
            del self._last_snap
        self._refresh()

    def _feedback(self):
        import subprocess, platform as _pl
        url = "https://forms.gle/q8q8KTxFmwkfa2nPA"
        try:
            if _pl.system() == 'Linux':
                subprocess.Popen(['xdg-open', url])
            elif _pl.system() == 'Darwin':
                subprocess.Popen(['open', url])
            else:
                import webbrowser; webbrowser.open(url)
        except:
            import webbrowser; webbrowser.open(url)

    def _ayuda(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Cómo usar TagFlow")
        dlg.setFixedWidth(640)
        dlg.setStyleSheet(f"""
            QDialog {{ background:{P['surface']}; }}
            QLabel  {{ background:transparent; }}
        """)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header con gradiente ──────────────────────────────
        header = QWidget()
        header.setFixedHeight(90)
        header.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {P['accent']}, stop:1 #7C3AED);"
        )
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 18, 28, 18)
        hl.setSpacing(2)
        h1 = QLabel("@TagFlow")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setStyleSheet("color:white;")
        h2 = QLabel("Guía de uso rápido")
        h2.setFont(QFont("Segoe UI", 10))
        h2.setStyleSheet("color:rgba(255,255,255,180);")
        hl.addWidget(h1)
        hl.addWidget(h2)
        root.addWidget(header)

        # ── Cuerpo con scroll ─────────────────────────────────
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background:{P['surface']};")
        body = QWidget()
        body.setStyleSheet(f"background:{P['surface']};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 8)
        bl.setSpacing(8)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # Número de acento con línea izquierda coloreada
        secciones = [
            ("01", P["accent"],  "Crear carpetas",
             "Agrega (@) y luego el nombre que le quieras poner a la carpeta. "
             "TagFlow automáticamente creará o moverá los archivos a esa carpeta en segundos.",
             "ensayo @historia.pdf",
             "Se guarda ensayo.pdf en la carpeta historia"),
            ("02", "#0891B2",    "Renombrar archivos",
             "Agrega @carpeta al nombre de cualquier archivo y TagFlow lo moverá "
             "automáticamente a esa carpeta en segundos.",
             None, None),
            ("03", "#16A34A",    "Configurar color y nota",
             "Activa el botón Config en la barra superior, "
             "luego haz clic en el icono de engranaje de la carpeta que "
             "quieras cambiar y podrás modificar su color y agregar una nota.",
             None, None),
            ("04", "#7C3AED",    "Ver subcarpetas",
             "Haz clic en el indicador de subcarpetas (número en la esquina derecha) "
             "para expandir y ver todos los niveles anidados de una carpeta.",
             None, None),
            ("05", "#DC2626",    "Eliminar carpetas",
             "Activa el botón Eliminar en la barra superior, "
             "luego haz clic en la X de la carpeta que quieras borrar. "
             "Los archivos se envían a la papelera del sistema.",
             None, None),
        ]

        for num, color, titulo, desc, ejemplo_in, ejemplo_out in secciones:
            card = QWidget()
            card.setStyleSheet(
                f"QWidget#card{{background:{P['bg']};border-radius:10px;"
                f"border-left:3px solid {color};}}"
            )
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(4)

            # Número + título
            th = QHBoxLayout()
            th.setSpacing(8)
            num_lbl = QLabel(num)
            num_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            num_lbl.setFixedSize(24, 18)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setStyleSheet(
                f"background:{color};color:white;border-radius:4px;"
                f"font-size:8px;font-weight:bold;"
            )
            title_lbl = QLabel(titulo)
            title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            title_lbl.setStyleSheet(f"color:{P['text']};")
            th.addWidget(num_lbl)
            th.addWidget(title_lbl)
            th.addStretch()
            cl.addLayout(th)

            # Descripción
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Segoe UI", 10))
            desc_lbl.setStyleSheet(f"color:{P['text2']};")
            desc_lbl.setWordWrap(True)
            cl.addWidget(desc_lbl)

            # Ejemplo de entrada/salida
            if ejemplo_in:
                ex_w = QWidget()
                ex_w.setStyleSheet(
                    f"background:rgba(0,0,0,0);border-radius:6px;"
                )
                ex_l = QHBoxLayout(ex_w)
                ex_l.setContentsMargins(0, 4, 0, 0)
                ex_l.setSpacing(6)

                def code_lbl(txt, bg, fg):
                    l = QLabel(txt)
                    l.setFont(QFont("Courier New", 9))
                    l.setStyleSheet(
                        f"background:{bg};color:{fg};"
                        f"border-radius:4px;padding:3px 8px;"
                    )
                    return l

                ex_l.addWidget(code_lbl(ejemplo_in,  "#FEF9C3", "#92400E"))
                arr = QLabel("→")
                arr.setStyleSheet(f"color:{P['text3']};font-size:12px;")
                ex_l.addWidget(arr)
                ex_l.addWidget(code_lbl(ejemplo_out, "#F0FDF4", "#166534"))
                ex_l.addStretch()
                cl.addWidget(ex_w)

            bl.addWidget(card)

        bl.addStretch()

        # ── Botón cerrar ──────────────────────────────────────
        foot = QWidget()
        foot.setStyleSheet(
            f"background:{P['surface']};"
            f"border-top:1px solid {P['border']};"
        )
        fl = QVBoxLayout(foot)
        fl.setContentsMargins(24, 12, 24, 16)
        fl.setSpacing(10)

        # Sección de feedback
        feedback_w = QWidget()
        feedback_w.setStyleSheet(
            f"background:{P['acc_soft']};border-radius:8px;"
        )
        fb_l = QVBoxLayout(feedback_w)
        fb_l.setContentsMargins(14, 10, 14, 10)
        fb_l.setSpacing(4)
        fb_title = QLabel("Sugerencias y problemas")
        fb_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        fb_title.setStyleSheet(f"color:{P['accent']};background:transparent;")
        fb_desc = QLabel("Para reportar un problema o enviarnos una sugerencia, copia y pega este enlace en tu navegador:")
        fb_desc.setFont(QFont("Segoe UI", 9))
        fb_desc.setStyleSheet(f"color:{P['text2']};background:transparent;")
        fb_desc.setWordWrap(True)
        # Link copiable
        link_row = QHBoxLayout()
        link_row.setSpacing(6)
        link_lbl = QLabel("https://forms.gle/q8q8KTxFmwkfa2nPA")
        link_lbl.setFont(QFont("Courier New", 9))
        link_lbl.setStyleSheet(
            f"background:white;color:{P['accent']};"
            f"border-radius:4px;padding:4px 8px;"
            f"border:1px solid {P['border']};"
        )
        link_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        link_lbl.setCursor(Qt.CursorShape.IBeamCursor)
        btn_copy = QPushButton("Copiar")
        btn_copy.setFixedSize(64, 28)
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn_copy.setStyleSheet(
            f"QPushButton{{background:{P['accent']};color:white;"
            f"border:none;border-radius:4px;}}"
            f"QPushButton:hover{{background:#1D4ED8;}}"
        )
        def _copiar():
            QApplication.clipboard().setText("https://forms.gle/q8q8KTxFmwkfa2nPA")
            btn_copy.setText("Copiado")
            QTimer.singleShot(2000, lambda: btn_copy.setText("Copiar"))
        btn_copy.clicked.connect(_copiar)
        link_row.addWidget(link_lbl, stretch=1)
        link_row.addWidget(btn_copy)
        fb_l.addWidget(fb_title)
        fb_l.addWidget(fb_desc)
        fb_l.addLayout(link_row)
        fl.addWidget(feedback_w)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(0)
        btn_row.addStretch()
        ok = QPushButton("Entendido")
        ok.setFixedHeight(40)
        ok.setMinimumWidth(160)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ok.setStyleSheet(f"""
            QPushButton {{
                background:{P['accent']};color:white;
                border-radius:8px;border:none;
                border-bottom:2px solid #1A3FA8;
            }}
            QPushButton:hover {{ background:#1D4ED8; }}
            QPushButton:pressed {{ border-bottom:1px solid #1A3FA8; padding-top:1px; }}
        """)
        ok.clicked.connect(dlg.accept)
        btn_row.addWidget(ok)
        fl.addLayout(btn_row)
        root.addWidget(foot)

        dlg.setMinimumHeight(560)
        dlg.exec()

    # ── Watcher ─────────────────────────────────────────────

    def on_archivo_movido(self, etiqueta, nombre):
        self._sig.emit(etiqueta, nombre)

    def _on_moved(self, etiqueta, nombre):
        # Borrar cache para forzar rebuild
        if hasattr(self, '_last_snap'):
            del self._last_snap
        self._refresh()

    # ── Ventana ─────────────────────────────────────────────

    def closeEvent(self, e):
        if self.tray and self.tray.isVisible():
            self.hide()
            e.ignore()
        else:
            self._quit()

    def _quit(self):
        if self.watcher:
            try:
                self.watcher.detener()
            except:
                pass
        QApplication.quit()