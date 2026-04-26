"""
ScienceWorld Park — gui/vistas/atracciones.py

Correcciones aplicadas (v3.0):
 - E.1: AtraccionRow ya no hardcodea background:#252538 ni color:#00d1ff.
         setObjectName('SectionCard') → hereda el QSS global del tema Cyber-Science.
         QPushButton 'Reparar' hereda QPushButton global (sin styleSheet inline).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from models.atracciones import AtraccionModel
from models.parque import ParqueModel
from core.logger import log


class AtraccionRow(QFrame):
    def __init__(self, atr_model, parent_view):
        super().__init__()
        self.atr_db      = atr_model
        self.parent_view = parent_view

        # E.1: objectName en lugar de styleSheet inline → hereda QSS global
        self.setObjectName("SectionCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        dom        = self.atr_db.to_domain()
        self.coste = dom.calcular_coste_reparacion()

        # Nombre
        lbl_nombre = QLabel(f"<b>{dom.nombre}</b>")
        layout.addWidget(lbl_nombre, 2)

        # Integridad con color semáforo
        color_int = (
            "#10b981" if dom.integridad >= 70
            else "#f59e0b" if dom.integridad >= 30
            else "#ef4444"
        )
        lbl_int = QLabel(f"{dom.integridad:.1f}%")
        lbl_int.setStyleSheet(f"color: {color_int}; background: transparent;")
        layout.addWidget(lbl_int, 1)

        # Estado operativo
        estado_color = {
            "Operativa": "#10b981",
            "En Avería":  "#ef4444",
            "Cerrada":    "#6b7280",
        }.get(dom.estado_str, "#9ca3af")
        lbl_estado = QLabel(dom.estado_str)
        lbl_estado.setStyleSheet(
            f"color: {estado_color}; background: transparent; font-size: 10px;"
        )
        layout.addWidget(lbl_estado, 1)

        # Coste de reparación
        lbl_coste = QLabel(f"${self.coste:,.2f}")
        lbl_coste.setStyleSheet("color: #a78bfa; background: transparent;")
        layout.addWidget(lbl_coste, 1)

        # Botón Reparar — hereda QPushButton del QSS global (E.1, sin styleSheet inline)
        self.btn_reparar = QPushButton("REPARAR")
        self.btn_reparar.setFixedWidth(90)
        self.btn_reparar.setEnabled(dom.integridad < 100.0)
        self.btn_reparar.clicked.connect(self.reparar_accion)
        layout.addWidget(self.btn_reparar)

    def reparar_accion(self):
        p_actual = ParqueModel.get_by_id(1)
        if p_actual.dinero < self.coste:
            QMessageBox.warning(self, "Economía", "Fondos insuficientes.")
            return

        self.btn_reparar.setEnabled(False)
        ParqueModel.restar_dinero(self.coste)

        dom = self.atr_db.to_domain()
        dom.reparar()
        AtraccionModel.from_domain(dom)

        log.info(f"Reparación: {dom.nombre}")
        self.parent_view.main_window.actualizar_interfaz()


class AtraccionesView(QScrollArea):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.container = QWidget()
        self.layout_p  = QVBoxLayout(self.container)
        self.layout_p.setSpacing(6)
        self.layout_p.setAlignment(Qt.AlignTop)
        self.setWidget(self.container)
        self.refresh()

    def refresh(self):
        while self.layout_p.count():
            child = self.layout_p.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for atr in AtraccionModel.select():
            self.layout_p.addWidget(AtraccionRow(atr, self))
