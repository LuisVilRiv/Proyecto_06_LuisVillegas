"""
ScienceWorld Park — gui/main_window.py
Ventana principal con tema Cyber-Science, Toast notifications y control del tiempo.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QStackedWidget, QButtonGroup,
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QKeyEvent

from core.motor import MotorSimulacion
from models.parque import ParqueModel

from gui.widgets import InfoCard
from gui.toast import ToastManager

from gui.vistas.dashboard import DashboardView
from gui.vistas.atracciones import AtraccionesView
from gui.vistas.visitantes import VisitantesView
from gui.vistas.personal import PersonalView
from gui.vistas.logistica import LogisticaView
from gui.vistas.finanzas import FinanzasView


VELOCIDADES = [
    ("⏸  PAUSA", 0),
    ("🐢  LENTO", 3000),
    ("▶  NORMAL", 1000),
    ("⚡  RÁPIDO", 400),
    ("🚀  TURBO", 120),
]

_CLOCK_REFRESH_MS = 80


# ─────────────────────────────────────────────
QSS = """
* { font-family: 'Courier New', monospace; color: #d7ffe9; }
QMainWindow, QWidget { background-color: #070b12; }

/* BOTONES RETRO */
QPushButton {
    background-color: #0f1b2b;
    border: 1px solid #00ff9f;
    color: #00ff9f;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 900;
    border-radius: 2px;
    min-width: 110px;
    letter-spacing: 1px;
}

QPushButton:hover {
    background-color: #16334f;
    color: #7fffd4;
}

QPushButton:pressed {
    background-color: #00ff9f;
    color: #04120c;
}

QPushButton:checked {
    background-color: #123323;
    color: #a8ffd9;
    border-color: #7fffd4;
}

QPushButton:disabled {
    background-color: #0e141d;
    color: #4a6b5d;
    border-color: #28453a;
}

/* TARJETAS */
QFrame#SectionCard {
    background: #0d1522;
    border: 1px solid #1f3550;
    border-radius: 3px;
    margin: 4px;
}

QFrame#InfoCard {
    background: #0d1522;
    border: 1px solid #1f3550;
    border-radius: 3px;
}

/* SIDEBAR */
QFrame#Sidebar {
    background: #09111c;
    border-right: 1px solid #1f3550;
}

QProgressBar {
    border: 1px solid #27435f;
    border-radius: 2px;
    text-align: center;
    background: #09121e;
    color: #9dddc0;
}
QProgressBar::chunk {
    background: #00ff9f;
}

QListWidget, QTableWidget, QComboBox, QLineEdit, QSpinBox {
    background-color: #0c1522;
    border: 1px solid #1f3550;
    color: #d7ffe9;
    selection-background-color: #173451;
    selection-color: #a8ffd9;
}

QHeaderView::section {
    background-color: #102133;
    color: #7fffd4;
    border: 1px solid #1f3550;
    padding: 6px;
    font-weight: 900;
}

QTabWidget::pane {
    border: 1px solid #1f3550;
    background: #0b1320;
}
QTabBar::tab {
    background: #0f1b2b;
    border: 1px solid #1f3550;
    color: #79d2b5;
    padding: 6px 10px;
}
QTabBar::tab:selected {
    background: #173451;
    color: #a8ffd9;
    border-color: #00ff9f;
}
"""

QSS_COMPACT = """
QPushButton { padding: 5px 8px; font-size: 10px; min-width: 90px; }
QHeaderView::section { padding: 3px; }
QTabBar::tab { padding: 4px 7px; }
QListWidget, QTableWidget, QComboBox, QLineEdit, QSpinBox { font-size: 10px; }
"""


# ─────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.motor = MotorSimulacion()
        self._settings = QSettings("ScienceWorld", "ScienceWorldPark")

        self.setWindowTitle("ScienceWorld Park")
        self.resize(1380, 870)
        self._density_mode = self._settings.value("ui/density_mode", "normal")
        if self._density_mode not in ("normal", "compacta"):
            self._density_mode = "normal"
        self._apply_density_style()

        self.toast = ToastManager(self)

        # ── timers
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_automatico)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(_CLOCK_REFRESH_MS)
        self._clock_timer.timeout.connect(self._actualizar_reloj)
        self._clock_timer.start()

        self._clock_hora = 8
        self._clock_dia = 1

        # ── UI
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content())

        self.motor.signals.tick_completado.connect(self._on_tick)

        self.actualizar_interfaz()

    # ─────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")

        lay = QVBoxLayout(sidebar)

        self._btn_group = QButtonGroup(self)

        for i, txt in enumerate([
            "Dashboard",
            "Atracciones",
            "Visitantes",
            "Personal",
            "Logística",
            "Finanzas",
        ]):
            btn = QPushButton(txt)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, x=i: self._cambiar_vista(x))
            self._btn_group.addButton(btn, i)
            lay.addWidget(btn)

        # 🔥 BOTÓN NUEVO: PRECIO ENTRADA
        btn_precio = QPushButton("🎟 PRECIO ENTRADA")
        btn_precio.clicked.connect(self.cambiar_precio_entrada)
        lay.addWidget(btn_precio)

        btn_density = QPushButton("[UI] DENSIDAD")
        btn_density.clicked.connect(self._toggle_density)
        lay.addWidget(btn_density)

        for txt, interval in VELOCIDADES:
            btn_vel = QPushButton(txt)
            btn_vel.clicked.connect(
                lambda _, ms=interval: self._set_velocidad(ms)
            )
            lay.addWidget(btn_vel)

        lay.addStretch()
        first = self._btn_group.button(0)
        if first:
            first.setChecked(True)

        return sidebar

    # ─────────────────────────────────────────
    def _build_content(self):
        container = QWidget()
        vlay = QVBoxLayout(container)

        self.card_time = InfoCard("Tiempo", "D1 08:00:00", "🕒")
        vlay.addWidget(self.card_time)

        self._views = QStackedWidget()
        self._views.addWidget(DashboardView())
        self._views.addWidget(AtraccionesView(self))
        self._views.addWidget(VisitantesView())
        self._views.addWidget(PersonalView(self))
        self._views.addWidget(LogisticaView(self))
        self._views.addWidget(FinanzasView())

        vlay.addWidget(self._views)

        return container

    # ─────────────────────────────────────────
    def _cambiar_vista(self, i):
        self._views.setCurrentIndex(i)
        self._refresh_current_view()

    def _set_velocidad(self, ms: int):
        if ms <= 0:
            self._timer.stop()
            self.toast.show("Tiempo", "Simulación en pausa", "info")
            return
        self._timer.setInterval(ms)
        self._timer.start()
        self.toast.show("Tiempo", f"Velocidad ajustada ({ms} ms/tick)", "success")

    def _toggle_density(self):
        self._density_mode = "compacta" if self._density_mode == "normal" else "normal"
        self._apply_density_style()
        self._settings.setValue("ui/density_mode", self._density_mode)
        self.toast.show("UI", f"Densidad {self._density_mode.upper()}", "info")

    def _apply_density_style(self):
        if self._density_mode == "compacta":
            self.setStyleSheet(QSS + QSS_COMPACT)
            return
        self.setStyleSheet(QSS)

    # ─────────────────────────────────────────
    def cambiar_precio_entrada(self):
        parque = ParqueModel.get_by_id(self.motor._parque_id)

        nuevo, ok = QInputDialog.getDouble(
            self,
            "Taquilla",
            "Precio entrada al parque:",
            value=parque.precio_entrada_adulto,
            minValue=5,
            maxValue=200
        )

        if ok:
            parque.precio_entrada_adulto = nuevo
            parque.save()
            self.actualizar_interfaz()

            self.toast.show(
                "Taquilla",
                f"Precio actualizado a {nuevo}€",
                "success"
            )

    # ─────────────────────────────────────────
    def _actualizar_reloj(self):
        self.card_time.update_value(
            f"D{self._clock_dia} {self._clock_hora:02d}:00:00"
        )

    def _tick_automatico(self):
        self.motor.ejecutar_tick()

    def _on_tick(self):
        self.actualizar_interfaz()

    def actualizar_interfaz(self):
        p = ParqueModel.get_by_id(self.motor._parque_id)
        self._clock_hora = p.hora_actual
        self._clock_dia = p.dia_actual
        self._refresh_current_view()

    def _refresh_current_view(self):
        vista = self._views.currentWidget()
        if vista and hasattr(vista, "refresh"):
            vista.refresh()

    # ─────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.motor.ejecutar_tick()

    def closeEvent(self, event):
        self._timer.stop()
        self._clock_timer.stop()
        event.accept()