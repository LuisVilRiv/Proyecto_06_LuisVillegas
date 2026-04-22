"""
ScienceWorld Park — gui/main_window.py
Ventana principal con tema Cyber-Science, Toast notifications y Crisis Dialogs.
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QStackedWidget, QMessageBox, QButtonGroup, QLabel,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui  import QKeyEvent

from core.motor   import MotorSimulacion
from core.logger  import log
from models.parque import ParqueModel

from gui.widgets import InfoCard
from gui.toast   import ToastManager

from gui.vistas.dashboard  import DashboardView
from gui.vistas.atracciones import AtraccionesView
from gui.vistas.personal   import PersonalView
from gui.vistas.logistica  import LogisticaView
from gui.vistas.visitantes import VisitantesView
from gui.vistas.finanzas   import FinanzasView


# ── Hoja de estilos QSS — Tema Cyber-Science ────────────────────────────────
QSS = """
/* ======== GLOBAL ======== */
* { font-family: 'Segoe UI', 'Inter', sans-serif; color: #e2e8f0; }
QMainWindow, QWidget   { background-color: #080b14; }
QScrollBar:vertical    { background: #111827; width: 7px; border-radius: 3px; }
QScrollBar::handle:vertical {
    background: #2d3748; border-radius: 3px; min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #00d1ff; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical     { height: 0px; }

/* ======== SIDEBAR ======== */
QFrame#Sidebar {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #0a0d18, stop:1 #0d1020);
    border-right: 1px solid #1a1f2e;
}
QLabel#Logo {
    color: #00d1ff;
    font-size: 15px;
    font-weight: 900;
    padding: 22px 26px;
    letter-spacing: 4px;
    border-bottom: 1px solid #1a1f2e;
    background: transparent;
}
QLabel#LogoSub {
    color: #374151;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 0 26px 14px;
    background: transparent;
}

/* ======== BOTONES DEL MENÚ ======== */
QPushButton#MenuBtn {
    background: transparent;
    color: #4b5563;
    border: none;
    border-left: 3px solid transparent;
    padding: 14px 20px;
    text-align: left;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
}
QPushButton#MenuBtn:hover {
    background: rgba(0,209,255,0.05);
    color: #9ca3af;
    border-left-color: rgba(0,209,255,0.3);
}
QPushButton#MenuBtn:checked {
    background: rgba(0,209,255,0.08);
    color: #00d1ff;
    border-left: 3px solid #00d1ff;
}

/* ======== TOPBAR ======== */
QFrame#Topbar { background: #080b14; border-bottom: 1px solid #1a1f2e; }

/* ======== TARJETAS KPI ======== */
QFrame#InfoCard {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #0f1423, stop:1 #0a0e1a);
    border: 1px solid #1a1f2e;
    border-radius: 8px;
}
QFrame#InfoCard:hover { border-color: rgba(0,209,255,0.25); }

/* ======== TABLAS ======== */
QTableWidget {
    background-color: #0f1423;
    color: #e2e8f0;
    gridline-color: #1a1f2e;
    border: 1px solid #1a1f2e;
    border-radius: 6px;
    selection-background-color: rgba(0,209,255,0.12);
}
QTableWidget::item         { padding: 8px 12px; border-bottom: 1px solid #1a1f2e; }
QTableWidget::item:selected { background: rgba(0,209,255,0.12); color: #00d1ff; }
QHeaderView::section {
    background-color: #080b14;
    color: #4b5563;
    padding: 10px 12px;
    font-weight: 800;
    font-size: 9px;
    letter-spacing: 1.5px;
    border: none;
    border-bottom: 1px solid #1a1f2e;
    border-right: 1px solid #1a1f2e;
}

/* ======== BOTONES GENÉRICOS ======== */
QPushButton {
    background-color: rgba(0,209,255,0.08);
    color: #00d1ff;
    border: 1px solid rgba(0,209,255,0.25);
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 10px;
    letter-spacing: 1.5px;
}
QPushButton:hover  {
    background-color: rgba(0,209,255,0.16);
    border-color: #00d1ff;
}
QPushButton:pressed { background-color: rgba(0,209,255,0.28); }
QPushButton:disabled {
    background-color: rgba(75,85,99,0.08);
    color: #374151;
    border-color: #1a1f2e;
}

/* ======== INPUTS ======== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #0f1423;
    color: #e2e8f0;
    border: 1px solid #2d3748;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #00d1ff;
    background-color: #0a0e1a;
}
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background-color: #0f1423; color: #e2e8f0;
    border: 1px solid #2d3748;
    selection-background-color: rgba(0,209,255,0.15);
}

/* ======== LISTAS ======== */
QListWidget {
    background-color: #0f1423;
    border: 1px solid #1a1f2e;
    border-radius: 6px;
    color: #e2e8f0;
}
QListWidget::item { padding: 9px 14px; border-bottom: 1px solid #1a1f2e; }
QListWidget::item:hover    { background: rgba(0,209,255,0.05); }
QListWidget::item:selected { background: rgba(0,209,255,0.12); color: #00d1ff; }

/* ======== SCROLL AREA ======== */
QScrollArea { background: transparent; border: none; }

/* ======== PROGRESS BAR ======== */
QProgressBar {
    background-color: #1a1f2e;
    border-radius: 4px;
    text-align: center;
    color: #9ca3af;
    font-size: 10px;
    min-height: 14px;
    max-height: 14px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00d1ff, stop:1 #7c3aed);
    border-radius: 4px;
}

/* ======== DIÁLOGOS ======== */
QDialog { background-color: #0a0d18; }
QDialog QLabel { color: #e2e8f0; }
QMessageBox { background-color: #0a0d18; }

/* ======== FRAMES ESPECIALES ======== */
QFrame#SectionCard {
    background: #0f1423;
    border: 1px solid #1a1f2e;
    border-radius: 8px;
}

/* ======== STATUS BAR ======== */
QStatusBar {
    background: #080b14;
    color: #374151;
    border-top: 1px solid #1a1f2e;
    font-size: 10px;
}
"""


# ────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.motor = MotorSimulacion()

        self.setWindowTitle("ScienceWorld Park  ·  Panel de Gestión  v1.0")
        self.resize(1380, 870)
        self.setMinimumSize(1200, 750)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(QSS)

        # Sistema de Toasts
        self.toast = ToastManager(self)

        # Layout raíz
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content_area())

        # Señales del motor
        self.motor.signals.tick_completado.connect(self._on_tick)
        self.motor.signals.evento_critico.connect(self._on_evento_critico)
        self.motor.signals.crisis_detectada.connect(self._on_crisis)
        self.motor.signals.nominas_pagadas.connect(
            lambda amt: self.toast.show(
                "Nóminas Pagadas",
                f"Descontados ${amt:,.0f} por nóminas diarias.",
                "warning",
            )
        )

        # Botón inicial activo
        self._btn_group.button(0).setChecked(True)
        self.actualizar_interfaz()
        log.info("MainWindow inicializada correctamente.")

    # ── Construcción del layout ───────────────────────────────────────────

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(215)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo
        lbl_logo = QLabel("SCIENCEWORLD")
        lbl_logo.setObjectName("Logo")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_logo)

        lbl_sub = QLabel("PARQUE TEMÁTICO · GESTIÓN")
        lbl_sub.setObjectName("LogoSub")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_sub)

        self._btn_group = QButtonGroup(self)
        secciones = [
            ("📊", "Dashboard",   0),
            ("🎢", "Atracciones", 1),
            ("👥", "Personal",    2),
            ("📦", "Logística",   3),
            ("🎟️", "Visitantes", 4),
            ("💹", "Finanzas",    5),
        ]
        for ico, texto, idx in secciones:
            btn = QPushButton(f"  {ico}   {texto.upper()}")
            btn.setObjectName("MenuBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(56)
            btn.clicked.connect(lambda _, i=idx: self._cambiar_vista(i))
            self._btn_group.addButton(btn, idx)
            lay.addWidget(btn)

        lay.addStretch()

        # Indicador de tick
        self._lbl_tick = QLabel("  [ESPACIO] → Avanzar 1h")
        self._lbl_tick.setStyleSheet(
            "color: #1f2937; font-size: 9px; padding: 12px;"
            "border-top: 1px solid #1a1f2e;"
        )
        lay.addWidget(self._lbl_tick)
        return sidebar

    def _build_content_area(self) -> QWidget:
        container = QWidget()
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # Topbar con KPIs
        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(105)
        tlay = QHBoxLayout(topbar)
        tlay.setContentsMargins(20, 12, 20, 12)
        tlay.setSpacing(12)

        self.card_dinero = InfoCard("Fondos",    "$0",    "💰")
        self.card_rep    = InfoCard("Prestigio", "0.0%",  "⭐")
        self.card_time   = InfoCard("Tiempo",    "Día 1", "🕒")
        self.card_visi   = InfoCard("Público",   "0",     "👥")
        self.card_stock  = InfoCard("Logística", "OK",    "🧪")

        for card in (self.card_dinero, self.card_rep, self.card_time,
                     self.card_visi, self.card_stock):
            tlay.addWidget(card)

        vlay.addWidget(topbar)

        # Vistas
        self._views = QStackedWidget()
        self._view_dash  = DashboardView()
        self._view_atrac = AtraccionesView(main_window=self)
        self._view_pers  = PersonalView(main_window=self)
        self._view_log   = LogisticaView(main_window=self)
        self._view_visi  = VisitantesView()
        self._view_fin   = FinanzasView()

        for v in (self._view_dash, self._view_atrac, self._view_pers,
                  self._view_log, self._view_visi, self._view_fin):
            self._views.addWidget(v)

        vlay.addWidget(self._views)
        return container

    # ── Navegación ────────────────────────────────────────────────────────

    def _cambiar_vista(self, index: int) -> None:
        self._views.setCurrentIndex(index)
        widget = self._views.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()
        log.info(f"Navegación: Cambiando a vista {index}.")

    # ── Actualización de la UI ────────────────────────────────────────────

    @Slot()
    def actualizar_interfaz(self) -> None:
        """Sincroniza la Topbar con la BD. Seguro ante errores."""
        try:
            p = ParqueModel.get_by_id(self.motor._parque_id)

            self.card_dinero.update_value(f"${p.dinero:,.0f}")
            self.card_rep.update_value(f"{p.reputacion:.1f}")
            self.card_time.update_value(f"Día {p.dia_actual}  {p.hora_actual:02d}:00")

            # Visitantes en cola: suma desde objetos de dominio
            from models.atracciones import AtraccionModel
            visitantes = sum(
                atr.to_domain().visitantes_en_cola
                for atr in AtraccionModel.select()
            ) + int(p.reputacion * 1.5)
            self.card_visi.update_value(str(max(0, visitantes)))

            # Estado del inventario
            from models.inventario import InventarioModel
            bajo = InventarioModel.select().where(
                InventarioModel.stock_actual <= InventarioModel.stock_minimo
            ).exists()
            estado = "BAJO" if bajo else "ÓPTIMO"
            color  = "#ef4444" if bajo else "#10b981"
            self.card_stock.update_value(estado)
            self.card_stock.set_color(color)

            # Alarma de saldo negativo
            if p.dinero < 0:
                self.card_dinero.set_color("#ef4444")
            else:
                self.card_dinero.set_color("#00d1ff")

            # Refrescar vista activa
            widget = self._views.currentWidget()
            if hasattr(widget, "refresh"):
                widget.refresh()

            self.setFocus()

        except Exception as exc:
            log.error(f"Error UI: {exc}")

    # ── Señales del motor ────────────────────────────────────────────────

    @Slot()
    def _on_tick(self) -> None:
        self.actualizar_interfaz()

    @Slot(str, str)
    def _on_evento_critico(self, titulo: str, mensaje: str) -> None:
        nivel = "error" if any(w in titulo.lower() for w in ("avería", "accidente", "quiebra")) \
               else "warning" if "fallo" in titulo.lower() or "inclemencias" in titulo.lower() \
               else "event"
        self.toast.show(titulo, mensaje, nivel)

    @Slot(str, str)
    def _on_crisis(self, titulo: str, descripcion: str) -> None:
        """Lanza el diálogo de decisión crítica apropiado."""
        from gui.dialogs.crisis_dialog import crisis_accidente, crisis_huelga, CrisisDialog, Opcion

        titulo_lower = titulo.lower()
        if "accidente" in titulo_lower:
            dlg = crisis_accidente(self, self.toast)
        elif "huelga" in titulo_lower:
            dlg = crisis_huelga(self, self.toast)
        else:
            # Crisis genérica
            def ack():
                self.toast.show("Crisis Gestionada", descripcion, "warning")

            dlg = CrisisDialog(
                self, titulo, descripcion,
                [Opcion("Gestionar la situación", "Continuar operaciones", ack)],
                "⚠️",
            )
        dlg.exec()
        self.actualizar_interfaz()

    # ── Teclado ───────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Space:
            try:
                self.motor.ejecutar_tick()
            except Exception as exc:
                QMessageBox.critical(self, "Error del Motor", str(exc))
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        log.info("Cerrando ScienceWorld Park. Guardando estado final...")
        event.accept()
