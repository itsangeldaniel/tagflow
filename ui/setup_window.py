import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient

COLORS = {
    "bg":           "#F5F5F7",
    "surface":      "#FFFFFF",
    "surface2":     "#F0F0F2",
    "border":       "#E0E0E5",
    "border_focus": "#0071E3",
    "text":         "#1D1D1F",
    "text2":        "#6E6E73",
    "accent":       "#0071E3",
    "accent_hover": "#0077ED",
    "accent_light": "#E8F1FC",
}

def _sombra(radio=20, opacidad=30, dy=4):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(radio)
    s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, opacidad))
    return s


class DiscoCard(QFrame):
    seleccionado = pyqtSignal(str)

    def __init__(self, disco: dict, parent=None):
        super().__init__(parent)
        self.disco = disco
        self._sel = False
        self._construir_ui()
        self.setGraphicsEffect(_sombra(10, 15, 2))

    def _construir_ui(self):
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._estilo(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(14)

        # Ícono disco
        icono_frame = QFrame()
        icono_frame.setFixedSize(40, 40)
        icono_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['accent_light']};
                border-radius: 10px;
            }}
        """)
        il = QHBoxLayout(icono_frame)
        il.setContentsMargins(0, 0, 0, 0)
        icono = QLabel("💾")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono.setFont(QFont("Segoe UI Emoji", 18))
        icono.setStyleSheet("background: transparent;")
        il.addWidget(icono)
        layout.addWidget(icono_frame)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)

        nombre = QLabel(self.disco["nombre"])
        nombre.setFont(QFont("SF Pro Display", 13, QFont.Weight.Medium))
        nombre.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        info.addWidget(nombre)

        libre = self.disco["espacio_libre_gb"]
        total = self.disco["espacio_total_gb"]
        espacio = QLabel(f"{libre} GB libres  de  {total} GB")
        espacio.setFont(QFont("SF Pro Display", 11))
        espacio.setStyleSheet(f"color: {COLORS['text2']}; background: transparent;")
        info.addWidget(espacio)

        layout.addLayout(info)
        layout.addStretch()

        # Barra de uso
        usado = 1 - (libre / max(total, 1))
        barra_bg = QFrame()
        barra_bg.setFixedSize(72, 6)
        barra_bg.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['border']};
                border-radius: 3px;
            }}
        """)
        barra_fill = QFrame(barra_bg)
        fill_w = max(4, int(72 * usado))
        barra_fill.setGeometry(0, 0, fill_w, 6)
        color_barra = "#FF3B30" if usado > 0.85 else COLORS["accent"]
        barra_fill.setStyleSheet(f"""
            QFrame {{
                background-color: {color_barra};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(barra_bg)

    def _estilo(self, sel: bool):
        if sel:
            self.setStyleSheet(f"""
                DiscoCard {{
                    background-color: {COLORS['accent_light']};
                    border: 2px solid {COLORS['accent']};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                DiscoCard {{
                    background-color: {COLORS['surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 14px;
                }}
            """)

    def marcar_seleccionada(self, estado: bool):
        self._sel = estado
        self._estilo(estado)

    def mousePressEvent(self, e):
        self.seleccionado.emit(self.disco["ruta"])


class SetupWindow(QWidget):
    disco_elegido = pyqtSignal(str)

    def __init__(self, discos: list[dict], parent=None):
        super().__init__(parent)
        self.discos = discos
        self._ruta = None
        self._cards = []

        self.setWindowTitle("TagFlow")
        self.setFixedSize(500, 560)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg']};
                font-family: 'SF Pro Display', 'Helvetica Neue', 'Segoe UI', sans-serif;
                color: {COLORS['text']};
            }}
        """)
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 44, 36, 36)
        layout.setSpacing(0)

        # Logo
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_frame = QFrame()
        logo_frame.setFixedSize(56, 56)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['accent']};
                border-radius: 14px;
            }}
        """)
        logo_frame.setGraphicsEffect(_sombra(16, 60, 4))
        ll = QHBoxLayout(logo_frame)
        ll.setContentsMargins(0, 0, 0, 0)
        logo_t = QLabel("T")
        logo_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_t.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        logo_t.setStyleSheet("color: white; background: transparent;")
        ll.addWidget(logo_t)
        logo_row.addWidget(logo_frame)
        layout.addLayout(logo_row)

        layout.addSpacing(20)

        titulo = QLabel("Bienvenido a TagFlow")
        titulo.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text']};")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        layout.addSpacing(6)

        sub = QLabel("Elige dónde crear tu carpeta TagFlow")
        sub.setFont(QFont("SF Pro Display", 13))
        sub.setStyleSheet(f"color: {COLORS['text2']};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(28)

        # Discos
        for disco in self.discos:
            card = DiscoCard(disco)
            card.seleccionado.connect(self._on_seleccion)
            self._cards.append(card)
            layout.addWidget(card)
            layout.addSpacing(10)

        layout.addStretch()

        # Botón
        self.btn = QPushButton("Continuar")
        self.btn.setEnabled(False)
        self.btn.setFixedHeight(48)
        self.btn.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
            QPushButton:pressed {{ background-color: #005BBB; }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text2']};
            }}
        """)
        self.btn.setGraphicsEffect(_sombra(14, 50, 3))
        self.btn.clicked.connect(self._confirmar)
        layout.addWidget(self.btn)

    def _on_seleccion(self, ruta: str):
        self._ruta = ruta
        for card in self._cards:
            card.marcar_seleccionada(card.disco["ruta"] == ruta)
        self.btn.setEnabled(True)

    def _confirmar(self):
        if self._ruta:
            self.disco_elegido.emit(self._ruta)