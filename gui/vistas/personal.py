from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QDialog, QFormLayout, 
                               QLineEdit, QComboBox, QSpinBox, QDialogButtonBox, QMessageBox, QLabel)
from models.empleados import EmpleadoModel
from models.secciones import SeccionModel
from models.parque import ParqueModel
from core.motor import MotorSimulacion

class ContratarDialog(QDialog):
    """Diálogo intuitivo para contratación de personal."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contratar Nuevo Especialista")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        
        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Ej: Dr. Elena Satine")
        
        self.tipo = QComboBox()
        self.tipo.addItems(["Tecnico", "Cientifico", "Divulgador", "Hosteleria"])
        
        # Combo de Secciones con Nombres Reales en lugar de IDs numéricos
        self.seccion_combo = QComboBox()
        self.secciones_map = {}
        # Cargar secciones de la DB para el mapeo
        for sec in SeccionModel.select():
            texto = f"{sec.emoji} {sec.nombre}"
            self.seccion_combo.addItem(texto)
            self.secciones_map[texto] = sec.id
            
        self.salario = QSpinBox()
        self.salario.setRange(1500, 10000)
        self.salario.setSingleStep(100)
        self.salario.setValue(2500)
        self.salario.setSuffix(" €")
        
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Puesto:", self.tipo)
        layout.addRow("Sección Destino:", self.seccion_combo)
        layout.addRow("Salario Mensual:", self.salario)
        
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btns.accepted.connect(self.validar_y_aceptar)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

    def validar_y_aceptar(self):
        """Valida que los campos no estén vacíos."""
        if not self.nombre.text().strip():
            QMessageBox.warning(self, "Validación", "Debes introducir un nombre.")
            return
        
        # Validar fondos (Coste de gestión de contratación: 1.000€)
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        if parque.dinero < 1000:
            QMessageBox.critical(self, "Fondos Insuficientes", 
                                 "No tienes fondos para cubrir los costes de gestión (1.000€).")
            return
            
        self.accept()

class PersonalView(QWidget):
    """Panel de gestión de Recursos Humanos."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        self.lbl_resumen = QLabel()
        self.lbl_resumen.setStyleSheet(
            "color:#00ff9f; font-weight:900; font-family:'Courier New'; letter-spacing:1px;"
        )
        layout.addWidget(self.lbl_resumen)
        
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Especialidad", "Sección", "Salario"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.btn_contratar = QPushButton("CONTRATAR ESPECIALISTA")
        self.btn_contratar.setFixedHeight(40)
        self.btn_contratar.clicked.connect(self.abrir_dialogo_contratacion)
        layout.addWidget(self.btn_contratar)
        
        self.refresh()

    def refresh(self):
        """Refresca la tabla de empleados."""
        self.tabla.setRowCount(0)
        empleados = list(EmpleadoModel.select())
        activos = [emp for emp in empleados if emp.activo]
        self.lbl_resumen.setText(
            f"PLANTILLA ACTIVA AL INICIO/ACTUAL: {len(activos)} · DISPONIBLES EN BOLSA: {len(empleados) - len(activos)}"
        )

        for emp in empleados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(emp.nombre))
            self.tabla.setItem(row, 1, QTableWidgetItem(emp.tipo.capitalize()))
            
            # Mostrar nombre de sección en lugar de ID
            nombre_sec = emp.seccion.nombre if emp.seccion else "General"
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre_sec))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${emp.salario_mes:,.2f}"))

    def abrir_dialogo_contratacion(self):
        """Abre el diálogo y guarda al nuevo empleado si se acepta."""
        dlg = ContratarDialog(self)
        if dlg.exec():
            # Mapeo de nombre seleccionado a ID de DB
            nombre_seleccionado = dlg.seccion_combo.currentText()
            id_seccion = dlg.secciones_map[nombre_seleccionado]
            
            # Descontar coste de gestión
            ParqueModel.restar_dinero(1000.0)
            
            # Crear empleado
            EmpleadoModel.create(
                nombre=dlg.nombre.text(),
                tipo=dlg.tipo.currentText().lower(),
                salario_mes=dlg.salario.value(),
                seccion=id_seccion,
                activo=True
            )
            
            self.refresh()
            self.main_window.actualizar_interfaz()