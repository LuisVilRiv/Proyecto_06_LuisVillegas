"""
ScienceWorld Park — gui/main_window.py
Ventana principal con tema Cyber-Science, Toast notifications y Crisis Dialogs.
Incluye avance automático del tiempo con velocidades seleccionables.

Cambios v3.1:
 - RELOJ ANIMADO: un QTimer de 80ms actualiza horas/minutos/segundos en tiempo
   real interpolando entre ticks. El reloj in-game avanza a la velocidad de
   simulación activa y se congela en PAUSA.
 - PAUSA POR DEFECTO: al cargar o crear una partida la simulación arranca
   siempre en PAUSA, requiriendo acción explícita del jugador para empezar.
"""

import sys
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton, QStackedWidget, QMessageBox, QButtonGroup, QLabel,
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui  import QKeyEvent

from core.motor   import MotorSimulacion
from core.logger  import log
from models.parque import ParqueModel

from gui.widgets import InfoCard
from gui.toast   import ToastManager

from gui.vistas.dashboard   import DashboardView
from gui.vistas.atracciones import AtraccionesView
from gui.vistas.personal    import PersonalView
from gui.vistas.logistica   import LogisticaView
from gui.vistas.visitantes  import VisitantesView
from gui.vistas.finanzas    import FinanzasView


# ── Velocidades disponibles ──────────────────────────────────────────────────
# Cada entrada: (etiqueta, intervalo en ms entre ticks de 1h in-game, 0 = pausado)
VELOCIDADES = [
    ("⏸  PAUSA",    0),
    ("🐢  LENTO",   3000),
    ("▶  NORMAL",  1000),
    ("⚡  RÁPIDO",   400),
    ("🚀  TURBO",    120),
]

# Intervalo de refresco del reloj visual (ms)
_CLOCK_REFRESH_MS = 80


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

/* ======== BOTONES DE VELOCIDAD ======== */
QPushButton#SpeedBtn {
    background: transparent;
    color: #374151;
    border: none;
    border-left: 3px solid transparent;
    padding: 10px 20px;
    text-align: left;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1px;
}
QPushButton#SpeedBtn:hover {
    background: rgba(167,139,250,0.06);
    color: #9ca3af;
    border-left-color: rgba(167,139,250,0.3);
}
QPushButton#SpeedBtn:checked {
    background: rgba(167,139,250,0.10);
    color: #a78bfa;
    border-left: 3px solid #a78bfa;
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

/* ======== SEPARADOR SIDEBAR ======== */
QFrame#SidebarSep {
    background: #1a1f2e;
    max-height: 1px;
    border: none;
}

/* ======== LABEL VELOCIDAD ======== */
QLabel#SpeedLabel {
    color: #1f2937;
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 2px;
    padding: 10px 20px 4px;
    background: transparent;
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

        # ── Timer de simulación (lógica de ticks) ───────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_automatico)
        self._velocidad_actual = 0      # índice en VELOCIDADES (0 = pausa)
        self._tick_interval_ms = 0      # ms por tick (0 = pausado)

        # ── Reloj animado ────────────────────────────────────────────────
        # Rastrea el momento real del último tick para interpolar MM:SS
        self._last_tick_real_time: float = time.monotonic()
        self._clock_hora: int  = 8      # hora in-game mostrada
        self._clock_min:  int  = 0
        self._clock_sec:  int  = 0

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(_CLOCK_REFRESH_MS)
        self._clock_timer.timeout.connect(self._actualizar_reloj)
        self._clock_timer.start()       # siempre activo; si pausa → tiempo congelado

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

        # Estado inicial: primera opción de navegación activa, velocidad = PAUSA
        self._btn_group.button(0).setChecked(True)
        self._speed_group.button(0).setChecked(True)   # PAUSA por defecto

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

        # ── Menú de navegación ───────────────────────────────────────────
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
            btn.setFixedHeight(52)
            btn.clicked.connect(lambda _, i=idx: self._cambiar_vista(i))
            self._btn_group.addButton(btn, idx)
            lay.addWidget(btn)

        # ── Separador ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("SidebarSep")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        # ── Controles de velocidad ────────────────────────────────────────
        lbl_vel = QLabel("VELOCIDAD DE SIMULACIÓN")
        lbl_vel.setObjectName("SpeedLabel")
        lay.addWidget(lbl_vel)

        self._speed_group = QButtonGroup(self)
        self._speed_group.setExclusive(True)

        for idx, (etiqueta, ms) in enumerate(VELOCIDADES):
            btn = QPushButton(f"  {etiqueta}")
            btn.setObjectName("SpeedBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            btn.clicked.connect(lambda _, i=idx: self._cambiar_velocidad(i))
            self._speed_group.addButton(btn, idx)
            lay.addWidget(btn)

        lay.addStretch()

        # Indicador de ayuda teclado
        self._lbl_tick = QLabel("  [ESPACIO] → Tick manual")
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

        self.card_dinero = InfoCard("Fondos",      "$0",    "💰")
        self.card_rep    = InfoCard("Prestigio",   "0.0%",  "⭐")
        self.card_time   = InfoCard("Tiempo",      "D1 08:00:00", "🕒")
        self.card_visi   = InfoCard("Público",     "0",     "👥")
        self.card_stock  = InfoCard("Logística",   "OK",    "🧪")
        self.card_speed  = InfoCard("Velocidad",   "PAUSA", "⏱️")

        for card in (self.card_dinero, self.card_rep, self.card_time,
                     self.card_visi, self.card_stock, self.card_speed):
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

    # ── Control de velocidad ──────────────────────────────────────────────

    def _cambiar_velocidad(self, idx: int) -> None:
        """Activa/desactiva el timer según la velocidad elegida."""
        self._velocidad_actual = idx
        etiqueta, ms = VELOCIDADES[idx]
        self._tick_interval_ms = ms

        self._timer.stop()
        if ms > 0:
            self._timer.start(ms)
            # Al reanudar, resetear el origen del reloj para que empiece
            # desde donde se quedó sin saltar segundos
            self._last_tick_real_time = time.monotonic()

        # Actualizar card de velocidad en topbar
        nombre_limpio = etiqueta.split("  ", 1)[-1].strip()
        self.card_speed.update_value(nombre_limpio)
        color = "#a78bfa" if ms > 0 else "#4b5563"
        self.card_speed.set_color(color)

        log.info(f"Velocidad de simulación: {etiqueta} ({ms}ms/tick)")

    # ── Reloj animado ─────────────────────────────────────────────────────

    @Slot()
    def _actualizar_reloj(self) -> None:
        """
        Se ejecuta cada 80ms. Interpola minutos y segundos dentro del tick
        actual basándose en el tiempo real transcurrido desde el último tick.
        En PAUSA el reloj queda congelado.
        """
        if self._tick_interval_ms <= 0:
            # Pausa: mostrar la hora congelada sin animación
            self.card_time.update_value(
                f"D{self._clock_dia}  {self._clock_hora:02d}:{self._clock_min:02d}:{self._clock_sec:02d}"
            )
            return

        # Segundos reales transcurridos desde el último tick
        elapsed_real = time.monotonic() - self._last_tick_real_time

        # Fracción del tick completada (0.0 … 1.0)
        tick_seg = self._tick_interval_ms / 1000.0
        fraccion = min(elapsed_real / tick_seg, 1.0)

        # Convertir fracción a segundos in-game dentro de 1 hora (3600s)
        ig_seconds = int(fraccion * 3600)
        min_ig  = (ig_seconds // 60) % 60
        sec_ig  = ig_seconds % 60

        self.card_time.update_value(
            f"D{self._clock_dia}  {self._clock_hora:02d}:{min_ig:02d}:{sec_ig:02d}"
        )

    # ── Tick automático ───────────────────────────────────────────────────

    @Slot()
    def _tick_automatico(self) -> None:
        """Llamado por el QTimer en cada intervalo."""
        try:
            self.motor.ejecutar_tick()
        except Exception as exc:
            self._timer.stop()
            QMessageBox.critical(self, "Error del Motor", str(exc))

    # ── Actualización de la UI ────────────────────────────────────────────

    @Slot()
    def actualizar_interfaz(self) -> None:
        """Sincroniza la Topbar con la BD. Seguro ante errores."""
        try:
            p = ParqueModel.get_by_id(self.motor._parque_id)

            self.card_dinero.update_value(f"${p.dinero:,.0f}")
            self.card_rep.update_value(f"{p.reputacion:.1f}")

            # Actualizar estado interno del reloj
            self._clock_hora = p.hora_actual
            self._clock_dia  = p.dia_actual
            self._clock_min  = 0
            self._clock_sec  = 0

            # Visitantes estimados
            visitantes = int(p.reputacion * 1.5)
            self.card_visi.update_value(str(max(0, visitantes)))

            # Estado del inventario
            from models.inventario import InventarioModel
            bajo = InventarioModel.select().where(
                InventarioModel.stock_actual <= InventarioModel.stock_minimo
            ).exists()
            self.card_stock.update_value("BAJO" if bajo else "ÓPTIMO")
            self.card_stock.set_color("#ef4444" if bajo else "#10b981")

            # Alarma de saldo negativo
            self.card_dinero.set_color("#ef4444" if p.dinero < 0 else "#00d1ff")

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
        """
        Al completar un tick de 1 hora in-game:
        - Registra el instante real para que el reloj arranque desde 00:00.
        - Actualiza la interfaz con los nuevos datos de BD.
        """
        self._last_tick_real_time = time.monotonic()
        self.actualizar_interfaz()

    @Slot(str, str)
    def _on_evento_critico(self, titulo: str, mensaje: str) -> None:
        nivel = (
            "error"   if any(w in titulo.lower() for w in ("avería", "accidente", "quiebra"))
            else "warning" if any(w in titulo.lower() for w in ("fallo", "inclemencias"))
            else "event"
        )
        self.toast.show(titulo, mensaje, nivel)

    @Slot(str, str)
    def _on_crisis(self, titulo: str, descripcion: str) -> None:
        """Pausa el timer, lanza el diálogo y lo reanuda al cerrar."""
        velocidad_previa = self._velocidad_actual
        self._timer.stop()

        from gui.dialogs.crisis_dialog import crisis_accidente, crisis_huelga, CrisisDialog, Opcion

        titulo_lower = titulo.lower()
        if "accidente" in titulo_lower:
            dlg = crisis_accidente(self, self.toast)
        elif "huelga" in titulo_lower:
            dlg = crisis_huelga(self, self.toast)
        else:
            def ack():
                self.toast.show("Crisis Gestionada", descripcion, "warning")
            dlg = CrisisDialog(
                self, titulo, descripcion,
                [Opcion("Gestionar la situación", "Continuar operaciones", ack)],
                "⚠️",
            )

        dlg.exec()
        self.actualizar_interfaz()

        # Reanudar a la velocidad previa
        self._cambiar_velocidad(velocidad_previa)

    # ── Teclado ───────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Space:
            # Tick manual: solo si está en pausa
            if not self._timer.isActive():
                try:
                    # Registrar tiempo antes del tick para que el reloj
                    # empiece desde 00 tras el salto manual
                    self._last_tick_real_time = time.monotonic()
                    self.motor.ejecutar_tick()
                except Exception as exc:
                    QMessageBox.critical(self, "Error del Motor", str(exc))
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._clock_timer.stop()
        log.info("Cerrando ScienceWorld Park. Guardando estado final...")
        event.accept()
