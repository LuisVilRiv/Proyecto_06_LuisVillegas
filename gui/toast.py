"""
ScienceWorld Park — gui/toast.py
PIXEL ART RETRO Toast notifications.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore    import Qt, QTimer

# Paleta retro pixel por nivel
_PALETTE = {
    "info":    ("#00FF41", "#0D1A0F", ">>"),
    "success": ("#39FF14", "#091A0B", "OK"),
    "warning": ("#FFE600", "#1A1500", "!!"),
    "error":   ("#FF2D55", "#1A040A", "XX"),
    "event":   ("#00FFFF", "#051A1A", "**"),
}


class Toast(QFrame):
    """Widget flotante estilo terminal retro."""

    def __init__(
        self,
        parent,
        titulo: str,
        mensaje: str = "",
        nivel: str = "info",
    ) -> None:
        super().__init__(parent)

        color_text, color_bg, prefix = _PALETTE.get(nivel, _PALETTE["info"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_bg};
                border: 2px solid {color_text};
                border-left: 6px solid {color_text};
                border-radius: 0px;
            }}
        """)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        # Cabecera estilo terminal
        lbl_header = QLabel(f"┌─[{prefix}]─ {titulo.upper()}")
        lbl_header.setStyleSheet(
            f"color: {color_text}; font-size: 11px; font-weight: 900;"
            "border: none; background: transparent;"
            "font-family: 'Courier New', monospace; letter-spacing: 1px;"
        )
        layout.addWidget(lbl_header)

        if mensaje:
            lbl_m = QLabel(f"│  {mensaje}")
            lbl_m.setWordWrap(True)
            lbl_m.setStyleSheet(
                "color: #5A8F60; font-size: 10px;"
                "border: none; background: transparent;"
                "font-family: 'Courier New', monospace;"
            )
            layout.addWidget(lbl_m)

        lbl_footer = QLabel("└─────────────────────────")
        lbl_footer.setStyleSheet(
            f"color: {color_text}; font-size: 9px;"
            "border: none; background: transparent;"
            "font-family: 'Courier New', monospace; letter-spacing: 0px;"
            "opacity: 0.5;"
        )
        layout.addWidget(lbl_footer)

        self.adjustSize()
        self.raise_()
        self.show()


class ToastManager:
    """Cola de Toasts apilados en la esquina superior derecha."""

    _MARGIN_RIGHT = 20
    _MARGIN_TOP   = 118
    _GAP          = 6

    def __init__(self, parent) -> None:
        self._parent = parent
        self._queue: list[Toast] = []

    def show(
        self,
        titulo: str,
        mensaje: str = "",
        nivel: str = "info",
        duration: int = 4500,
    ) -> None:
        toast = Toast(self._parent, titulo, mensaje, nivel)
        self._queue.append(toast)
        self._restack()

        def _dismiss():
            if toast in self._queue:
                self._queue.remove(toast)
            toast.deleteLater()
            self._restack()

        QTimer.singleShot(duration, _dismiss)

    def _restack(self) -> None:
        if not self._parent:
            return
        pw = self._parent.width()
        y  = self._MARGIN_TOP
        for toast in reversed(self._queue):
            x = pw - toast.width() - self._MARGIN_RIGHT
            toast.move(x, y)
            toast.raise_()
            y += toast.height() + self._GAP
