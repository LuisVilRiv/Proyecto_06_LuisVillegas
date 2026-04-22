"""
ScienceWorld Park — gui/toast.py
Sistema de notificaciones Toast flotantes auto-dismissables.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore    import Qt, QTimer

# Paleta de colores por nivel
_PALETTE = {
    "info":    ("#00d1ff", "#081828"),
    "success": ("#10b981", "#081f15"),
    "warning": ("#f59e0b", "#1f170a"),
    "error":   ("#ef4444", "#1f0c0c"),
    "event":   ("#a78bfa", "#13101f"),
}


class Toast(QFrame):
    """Widget hijo que flota sobre el contenido de la ventana principal."""

    def __init__(
        self,
        parent,
        titulo: str,
        mensaje: str = "",
        nivel: str = "info",
    ) -> None:
        super().__init__(parent)

        color_text, color_bg = _PALETTE.get(nivel, _PALETTE["info"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_bg};
                border: 1px solid {color_text};
                border-left: 4px solid {color_text};
                border-radius: 8px;
            }}
        """)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(
            f"color: {color_text}; font-size: 12px; font-weight: bold;"
            "border: none; background: transparent;"
        )
        layout.addWidget(lbl_t)

        if mensaje:
            lbl_m = QLabel(mensaje)
            lbl_m.setWordWrap(True)
            lbl_m.setStyleSheet(
                "color: #9ca3af; font-size: 11px;"
                "border: none; background: transparent;"
            )
            layout.addWidget(lbl_m)

        self.adjustSize()
        self.raise_()
        self.show()


class ToastManager:
    """
    Gestiona una cola de Toasts apilados en la esquina superior derecha
    de la ventana padre.
    """

    _MARGIN_RIGHT = 24
    _MARGIN_TOP   = 120   # espacio para la Topbar
    _GAP          = 8

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
        """Reposiciona todos los Toasts activos de abajo a arriba."""
        if not self._parent:
            return
        pw = self._parent.width()
        y  = self._MARGIN_TOP
        for toast in reversed(self._queue):
            x = pw - toast.width() - self._MARGIN_RIGHT
            toast.move(x, y)
            toast.raise_()
            y += toast.height() + self._GAP
