"""
SCIENCEWORLD PARK - Proyecto de Simulación y Gestión Científica
Archivo: gui/main_window.py
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QPushButton, QStackedWidget, QMessageBox, QButtonGroup, 
    QLabel, QApplication
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeyEvent

# Importaciones de núcleo y persistencia
from core.motor import MotorSimulacion
from core.logger import log
from models.parque import ParqueModel
from models.inventario import InventarioModel
from models.empleados import EmpleadoModel
from models.atracciones import AtraccionModel

# Importaciones de componentes de interfaz
from gui.widgets import InfoCard
from gui.vistas.dashboard import DashboardView
from gui.vistas.atracciones import AtraccionesView
from gui.vistas.personal import PersonalView
from gui.vistas.logistica import LogisticaView
from gui.vistas.visitantes import VisitantesView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.motor = MotorSimulacion()
        
        self.setWindowTitle("ScienceWorld Park - Panel de Gestión v1.0")
        self.resize(1350, 850)
        self.setMinimumSize(1200, 750)
        
        # Captura de teclado
        self.setFocusPolicy(Qt.StrongFocus)

        # 1. Estilos QSS
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2d; }
            QFrame#Sidebar { background-color: #161623; border-right: 1px solid #2d2d44; }
            QFrame#Topbar { background-color: #1e1e2d; border-bottom: 1px solid #2d2d44; }
            QPushButton#MenuBtn {
                background-color: transparent; color: #a2a2b5; border: none;
                padding: 15px; text-align: left; font-size: 13px; font-weight: bold;
            }
            QPushButton#MenuBtn:hover { background-color: #2d2d44; color: #00d1ff; }
            QPushButton#MenuBtn:checked { 
                background-color: #252538; color: #00d1ff; border-left: 4px solid #00d1ff; 
            }
            QLabel#Logo {
                color: #ffffff; font-size: 18px; font-weight: bold; padding: 25px;
                border-bottom: 1px solid #2d2d44;
            }
        """)

        # 2. Layouts
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 3. Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(210)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_logo = QLabel("SCIENCEWORLD")
        lbl_logo.setObjectName("Logo")
        lbl_logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(lbl_logo)

        self.btn_group = QButtonGroup(self)
        secciones = [
            ("Dashboard", "📊", 0), ("Atracciones", "🎢", 1),
            ("Personal", "👥", 2), ("Logística", "📦", 3),
            ("Visitantes", "🎟️", 4), ("Finanzas", "💹", 5)
        ]

        for texto, icono, idx in secciones:
            btn = QPushButton(f"  {icono}  {texto.upper()}")
            btn.setObjectName("MenuBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(60)
            btn.clicked.connect(lambda ch, i=idx: self._cambiar_vista(i))
            self.btn_group.addButton(btn, idx)
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)

        # 4. Área de Contenido
        self.right_container = QWidget()
        self.content_layout = QVBoxLayout(self.right_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Topbar
        self.topbar = QFrame()
        self.topbar.setObjectName("Topbar")
        self.topbar.setFixedHeight(110)
        self.top_layout = QHBoxLayout(self.topbar)
        
        self.card_dinero = InfoCard("FONDOS", "$0", "💰")
        self.card_rep = InfoCard("PRESTIGIO", "0%", "⭐️")
        self.card_time = InfoCard("TIEMPO", "Día 1", "🕒")
        self.card_visi = InfoCard("PÚBLICO", "0", "👥")
        self.card_stock = InfoCard("LOGÍSTICA", "OK", "🧪")
        
        for card in [self.card_dinero, self.card_rep, self.card_time, self.card_visi, self.card_stock]:
            self.top_layout.addWidget(card)
        
        self.content_layout.addWidget(self.topbar)

        # Vistas
        self.views = QStackedWidget()
        self.view_dash = DashboardView()
        self.view_atrac = AtraccionesView(main_window=self)
        self.view_pers = PersonalView(main_window=self)
        self.view_log = LogisticaView(main_window=self)
        self.view_visi = VisitantesView()
        
        self.views.addWidget(self.view_dash)    # 0
        self.views.addWidget(self.view_atrac)   # 1
        self.views.addWidget(self.view_pers)    # 2
        self.views.addWidget(self.view_log)     # 3
        self.views.addWidget(self.view_visi)    # 4
        self.views.addWidget(QLabel("Módulo Finanzas")) # 5
        
        self.content_layout.addWidget(self.views)
        self.main_layout.addWidget(self.right_container)

        # 5. Señales y Refresco
        self.motor.signals.tick_completado.connect(self.actualizar_interfaz)
        self.motor.signals.evento_critico.connect(lambda t, m: QMessageBox.warning(self, t, m))
        
        self.btn_group.button(0).setChecked(True)
        self.actualizar_interfaz()

    def _cambiar_vista(self, index):
        self.views.setCurrentIndex(index)
        w = self.views.currentWidget()
        if hasattr(w, 'refresh'): w.refresh()

    @Slot()
    def actualizar_interfaz(self):
        """Sincroniza la UI con la base de datos."""
        try:
            p = ParqueModel.get_by_id(1)
            self.card_dinero.update_value(f"${p.dinero:,.2f}")
            self.card_rep.update_value(f"{p.reputacion:.1f}%")
            self.card_time.update_value(f"Día {p.dia_actual} - {p.hora_actual:02d}:00")
            
            # Stock
            bajo = InventarioModel.select().where(InventarioModel.stock_actual <= InventarioModel.stock_minimo).exists()
            self.card_stock.update_value("BAJO" if bajo else "ÓPTIMO")
            self.card_stock.lbl_valor.setStyleSheet(f"color: {'#e74c3c' if bajo else '#2ecc71'}; font-size: 18px; font-weight: bold;")

            # Visitantes
            v = sum(a.visitantes_en_cola for a in AtraccionModel.select()) + int(p.reputacion * 2)
            self.card_visi.update_value(str(v))

            w = self.views.currentWidget()
            if hasattr(w, 'refresh'): w.refresh()
            self.setFocus()
        except Exception as e:
            log.error(f"Error UI: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            try:
                self.motor.ejecutar_tick()
                self.actualizar_interfaz()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo motor: {e}")
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        log.info("Cierre de aplicación.")
        event.accept()