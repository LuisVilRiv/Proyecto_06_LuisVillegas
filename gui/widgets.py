"""
ScienceWorld Park — gui/widgets.py
PIXEL ART RETRO widgets.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel


class InfoCard(QFrame):
    """
    Tarjeta KPI de la Topbar — estilo terminal retro.
    Usa objectName 'InfoCard' para el QSS global.
    """

    _COLORS = {
        "green":  "#00FF41",
        "yellow": "#FFE600",
        "red":    "#FF2D55",
        "orange": "#FF6B2B",
        "cyan":   "#00FFFF",
        "grey":   "#1A5C21",
    }

    def __init__(self, titulo: str, valor: str, icono: str = "[?]") -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(168)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(2)

        # Fila superior: icono + título
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_icon = QLabel(icono)
        self.lbl_icon.setStyleSheet(
            "color: #1A5C21; font-size: 11px; font-weight: 900;"
            "background: transparent; border: none;"
            "font-family: 'Courier New', monospace;"
        )

        self.lbl_titulo = QLabel(f">> {titulo}")
        self.lbl_titulo.setStyleSheet(
            "color: #1A5C21; font-size: 8px; font-weight: 900;"
            "letter-spacing: 2px; background: transparent; border: none;"
            "font-family: 'Courier New', monospace;"
            "text-transform: uppercase;"
        )

        top_row.addWidget(self.lbl_icon)
        top_row.addWidget(self.lbl_titulo)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Separador pixelado
        sep = QLabel("─" * 22)
        sep.setStyleSheet(
            "color: #1A3D1E; font-size: 8px; background: transparent;"
            "border: none; letter-spacing: 0px;"
        )
        layout.addWidget(sep)

        # Valor grande
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(
            "color: #00FF41; font-size: 18px; font-weight: 900;"
            "background: transparent; border: none;"
            "font-family: 'Courier New', monospace;"
            "letter-spacing: 1px;"
        )
        layout.addWidget(self.lbl_valor)

    def update_value(self, nuevo_valor: str) -> None:
        self.lbl_valor.setText(nuevo_valor)

    def set_color(self, color: str) -> None:
        """Cambia el color del valor (hex o nombre en _COLORS)."""
        hex_c = self._COLORS.get(color, color)  # soporta tanto hex como nombre
        self.lbl_valor.setStyleSheet(
            f"color: {hex_c}; font-size: 18px; font-weight: 900;"
            "background: transparent; border: none;"
            "font-family: 'Courier New', monospace;"
            "letter-spacing: 1px;"
        )


class StatusBadge(QLabel):
    """Indicador de estado retro con caracteres ASCII."""

    _SYMBOLS = {
        "green":  ("[ OK ]", "#00FF41"),
        "yellow": ("[ !! ]", "#FFE600"),
        "red":    ("[ XX ]", "#FF2D55"),
        "grey":   ("[ -- ]", "#1A5C21"),
    }

    def __init__(self, color: str = "green") -> None:
        super().__init__()
        self.update_color(color)

    def update_color(self, color: str) -> None:
        symbol, hex_c = self._SYMBOLS.get(color, self._SYMBOLS["grey"])
        self.setText(symbol)
        self.setStyleSheet(
            f"color: {hex_c}; font-size: 10px; font-weight: 900;"
            "font-family: 'Courier New', monospace; background: transparent;"
            "border: none; letter-spacing: 1px;"
        )
