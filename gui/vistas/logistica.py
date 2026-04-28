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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_info = QLabel("CENTRO DE SUMINISTROS Y LOGÍSTICA")
        self.lbl_info.setStyleSheet(
            "font-weight: 900; color: #00ff9f; font-size: 13px; margin-bottom: 8px;"
            "font-family: 'Courier New'; letter-spacing: 1px;"
        )
        layout.addWidget(self.lbl_info)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Producto", "Stock Actual", "Capacidad Máx", "Precio Unidad", "Gestión"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        self.refresh()

    # ------------------------------------------------------------------ #

    def refresh(self):
        """Limpia y vuelve a cargar la tabla de suministros."""
        self.tabla.setRowCount(0)

        productos = list(InventarioModel.select().order_by(InventarioModel.nombre))

        for item in productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            # 1. Nombre — rojo si stock bajo
            nombre_item = QTableWidgetItem(item.nombre)
            if item.stock_actual <= item.stock_minimo:
                nombre_item.setForeground(Qt.red)
            self.tabla.setItem(row, 0, nombre_item)

            # 2. Stock actual
            self.tabla.setItem(row, 1, QTableWidgetItem(f"{int(item.stock_actual)} uds"))

            # 3. Capacidad máxima
            self.tabla.setItem(row, 2, QTableWidgetItem(f"{int(item.stock_maximo)} uds"))

            # 4. Precio unitario
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${item.precio_compra:,.2f}"))

            # 5. Botón de compra (sin selectores CSS para evitar el error de Qt)
            btn = QPushButton("REALIZAR PEDIDO")
            btn.setCursor(Qt.PointingHandCursor)

            if item.stock_actual >= item.stock_maximo:
                btn.setEnabled(False)
                btn.setText("LLENO")
            else:
                # Capturamos el id en el closure para evitar referencia tardía
                item_id = item.id
                btn.clicked.connect(
                    lambda checked=False, id_p=item_id: self.ejecutar_compra(id_p)
                )

            self.tabla.setCellWidget(row, 4, btn)

    # ------------------------------------------------------------------ #

    def ejecutar_compra(self, producto_id: int):
        """Lógica que se dispara al pulsar el botón de comprar."""
        item = InventarioModel.get_by_id(producto_id)
        espacio = int(item.stock_maximo - item.stock_actual)

        if espacio <= 0:
            return

        cantidad, ok = QInputDialog.getInt(
            self,
            "Logística: Nuevo Pedido",
            f"Producto: {item.nombre}\n"
            f"Coste unidad: ${item.precio_compra:.2f}\n"
            f"Espacio disponible: {espacio} unidades\n\n"
            f"¿Cantidad a pedir?",
            value=min(50, espacio),
            minValue=1,
            maxValue=espacio,
            step=1,
        )

        if ok:
            coste_total = cantidad * item.precio_compra
            exito = InventarioModel.comprar_stock(item.nombre, cantidad, coste_total)

            if exito:
                log.info(f"Suministros: Recibidas {cantidad} uds de {item.nombre}.")
                self.refresh()
                if self.main_window:
                    self.main_window.actualizar_interfaz()
            else:
                QMessageBox.warning(
                    self,
                    "Fondos Insuficientes",
                    f"No hay fondos para comprar {cantidad} uds de {item.nombre} "
                    f"(coste: ${coste_total:,.2f}).",
                )
