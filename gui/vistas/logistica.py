"""
SCIENCEWORLD PARK - Centro de Logística
Archivo: gui/vistas/logistica.py
Descripción: Gestión manual de inventario para ScienceFood y ScienceStore.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, 
    QInputDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from models.inventario import InventarioModel
from core.logger import log

class LogisticaView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Diseño Principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado
        self.lbl_info = QLabel("CENTRO DE SUMINISTROS Y LOGÍSTICA")
        self.lbl_info.setStyleSheet("""
            font-weight: bold; 
            color: #00d1ff; 
            font-size: 18px; 
            margin-bottom: 10px;
        """)
        layout.addWidget(self.lbl_info)

        # Tabla de Inventario
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Stock Actual", "Capacidad Máx", "Precio Unidad", "Gestión"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #252538;
                color: white;
                gridline-color: #2d2d44;
                border: 1px solid #2d2d44;
            }
            QHeaderView::section {
                background-color: #161623;
                color: #a2a2b5;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.tabla)

        # Inicializar
        self.refresh()

    def refresh(self):
        """Limpia y vuelve a cargar la tabla de suministros."""
        # Desactivar señales temporalmente para evitar efectos secundarios al limpiar
        self.tabla.setRowCount(0)
        
        # Consultamos todos los productos
        productos = list(InventarioModel.select().order_by(InventarioModel.nombre))

        for item in productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            # 1. Nombre con color de alerta si el stock es bajo
            nombre_item = QTableWidgetItem(item.nombre)
            if item.stock_actual <= item.stock_minimo:
                nombre_item.setForeground(Qt.red)
            self.tabla.setItem(row, 0, nombre_item)

            # 2. Stock
            self.tabla.setItem(row, 1, QTableWidgetItem(f"{int(item.stock_actual)} uds"))

            # 3. Límite
            self.tabla.setItem(row, 2, QTableWidgetItem(f"{int(item.stock_maximo)} uds"))

            # 4. Precio
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${item.precio_compra:,.2f}"))

            # 5. Botón de Compra (Contenedor para centrarlo)
            btn_comprar = QPushButton("REALIZAR PEDIDO")
            btn_comprar.setCursor(Qt.PointingHandCursor)
            
            if item.stock_actual >= item.stock_maximo:
                btn_comprar.setEnabled(False)
                btn_comprar.setText("ALMACÉN LLENO")
                btn_comprar.setStyleSheet("background-color: #2d2d44; color: #a2a2b5;")
            else:
                btn_comprar.setStyleSheet("""
                    QPushButton {
                        background-color: #2ecc71;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #27ae60;
                    }
                """)
                
                # CRÍTICO: Usamos el ID del item para evitar problemas de referencia en el lambda
                item_id = item.id
                btn_comprar.clicked.connect(lambda checked=False, id_p=item_id: self.ejecutar_compra(id_p))

            self.tabla.setCellWidget(row, 4, btn_comprar)

    def ejecutar_compra(self, producto_id):
        """Lógica que se dispara al pulsar el botón de comprar."""
        # Recuperamos el item fresco de la DB
        item = InventarioModel.get_by_id(producto_id)
        espacio = int(item.stock_maximo - item.stock_actual)

        if espacio <= 0:
            return

        # Pedir cantidad al usuario
        cantidad, ok = QInputDialog.getInt(
            self, 
            "Logística: Nuevo Pedido",
            f"Producto: {item.nombre}\nCoste unidad: ${item.precio_compra:.2f}\n"
            f"Espacio disponible: {espacio} unidades\n\n¿Cantidad a pedir?",
            value=min(50, espacio),
            minValue=1,
            maxValue=espacio,
            step=1
        )

        if ok:
            coste_total = cantidad * item.precio_compra
            
            # Ejecutar transacción en el modelo
            exito = InventarioModel.comprar_stock(item.nombre, cantidad, coste_total)
            
            if exito:
                log.info(f"Suministros: Recibidas {cantidad} uds de {item.nombre}.")
                # 1. Refrescar esta vista
                self.refresh()
             