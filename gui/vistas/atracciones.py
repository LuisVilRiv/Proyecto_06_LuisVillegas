from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from models.atracciones import AtraccionModel
from models.parque import ParqueModel
from core.logger import log

class AtraccionRow(QFrame):
    def __init__(self, atr_model, parent_view):
        super().__init__()
        self.atr_db = atr_model
        self.parent_view = parent_view
        self.setStyleSheet("background-color: #252538; border-radius: 5px; margin: 2px;")
        
        layout = QHBoxLayout(self)
        dom = self.atr_db.to_domain()
        self.coste = dom.calcular_coste_reparacion()
        
        layout.addWidget(QLabel(f"<b>{dom.nombre}</b>"), 2)
        layout.addWidget(QLabel(f"{dom.integridad:.1f}%"), 1)
        
        lbl_coste = QLabel(f"${self.coste:,.2f}")
        lbl_coste.setStyleSheet("color: #00d1ff;")
        layout.addWidget(lbl_coste, 1)
        
        self.btn_reparar = QPushButton("Reparar")
        self.btn_reparar.setFixedWidth(80)
        self.btn_reparar.clicked.connect(self.reparar_accion)
        
        if dom.integridad >= 100:
            self.btn_reparar.setEnabled(False)
            
        layout.addWidget(self.btn_reparar)

    def reparar_accion(self):
        p_actual = ParqueModel.get_by_id(1)
        if p_actual.dinero < self.coste:
            QMessageBox.warning(self, "Economía", "Fondos insuficientes.")
            return
            
        # Acción atómica y desactivación inmediata
        self.btn_reparar.setEnabled(False)
        ParqueModel.restar_dinero(self.coste)
        
        dom = self.atr_db.to_domain()
        dom.reparar()
        AtraccionModel.from_domain(dom)
        
        log.info(f"Reparación: {dom.nombre}")
        # Notificación reactiva a la ventana principal
        self.parent_view.main_window.actualizar_interfaz()

class AtraccionesView(QScrollArea):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.container = QWidget()
        self.layout_p = QVBoxLayout(self.container)
        self.layout_p.setAlignment(Qt.AlignTop)
        self.setWidget(self.container)
        self.refresh()

    def refresh(self):
        while self.layout_p.count():
            child = self.layout_p.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        for atr in AtraccionModel.select():
            self.layout_p.addWidget(AtraccionRow(atr, self))