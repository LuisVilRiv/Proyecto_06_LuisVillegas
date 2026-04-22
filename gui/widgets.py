"""
ScienceWorld Park — gui/widgets.py
Componentes reutilizables de la interfaz.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel


class InfoCard(QFrame):
    """
    Tarjeta KPI de la Topbar.
    Usa el objectName 'InfoCard' para ser estilizada por el QSS global.
    """

    def __init__(self, titulo: str, valor: str, icono: str = "📊") -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(155)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.lbl_icon = QLabel(icono)
        self.lbl_icon.setStyleSheet(
            "font-size: 26px; background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setStyleSheet(
            "color: #4b5563; font-size: 8px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent; border: none;"
        )

        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(
            "color: #00d1ff; font-size: 20px; font-weight: 900;"
            "background: transparent; border: none;"
        )

        text_col.addWidget(self.lbl_titulo)
        text_col.addWidget(self.lbl_valor)
        layout.addLayout(text_col)
        layout.addStretch()

    def update_value(self, nuevo_valor: str) -> None:
        self.lbl_valor.setText(nuevo_valor)

    def set_color(self, color: str) -> None:
        """Cambia el color del valor (ej. rojo para alertas)."""
        self.lbl_valor.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: 900;"
            "background: transparent; border: none;"
        )


class StatusBadge(QLabel):
    """Indicador circular de estado (verde / amarillo / rojo)."""

    _COLORS = {
        "green":  "#10b981",
        "yellow": "#f59e0b",
        "red":    "#ef4444",
        "grey":   "#4b5563",
    }

    def __init__(self, color: str = "green") -> None:
        super().__init__()
        self.setFixedSize(10, 10)
        self.update_color(color)

    def update_color(self, color: str) -> None:
        hex_c = self._COLORS.get(color, self._COLORS["grey"])
        self.setStyleSheet(
            f"background-color: {hex_c}; border-radius: 5px; border: none;"
        )
