"""
ScienceWorld Park — gui/vistas/finanzas.py
Vista de Finanzas: P&L desglosado por categoría (PDF §4.8 + §4.1).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt


# Iconos y alias para cada categoría financiera
CATEGORIAS = {
    "entradas":     ("🎟️",  "Venta de Entradas"),
    "restauracion": ("🍽️",  "Restauración"),
    "tienda":       ("🛍️",  "Tienda"),
    "nominas":      ("👥",  "Nóminas"),
    "reparaciones": ("🔧",  "Reparaciones"),
    "logistica":    ("📦",  "Logística / Pedidos"),
}


class KpiBox(QFrame):
    """Bloque de KPI grande para el resumen superior."""

    def __init__(self, titulo: str, valor: str, color: str = "#00d1ff") -> None:
        super().__init__()
        self.setObjectName("SectionCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)

        self._lbl_titulo = QLabel(titulo.upper())
        self._lbl_titulo.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )

        self._lbl_valor = QLabel(valor)
        self._lbl_valor.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 900;"
            "background: transparent;"
        )

        lay.addWidget(self._lbl_titulo)
        lay.addWidget(self._lbl_valor)

    def update(self, valor: str, color: str = None) -> None:
        self._lbl_valor.setText(valor)
        if color:
            self._lbl_valor.setStyleSheet(
                f"color: {color}; font-size: 22px; font-weight: 900;"
                "background: transparent;"
            )


class FinanzasView(QWidget):
    """
    Panel de finanzas con:
      · Resumen del día (ingresos, gastos, balance)
      · Desglose P&L por categoría
      · Histórico de los últimos 7 días
    """

    def __init__(self) -> None:
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 20, 24, 20)
        main_lay.setSpacing(20)

        # ── Cabecera ─────────────────────────────────────────────────────
        lbl_titulo = QLabel("CENTRO FINANCIERO")
        lbl_titulo.setStyleSheet(
            "color: #00d1ff; font-size: 16px; font-weight: 900;"
            "letter-spacing: 3px;"
        )
        main_lay.addWidget(lbl_titulo)

        # ── KPIs ─────────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self._kpi_ingresos = KpiBox("Ingresos Hoy",  "$0",   "#10b981")
        self._kpi_gastos   = KpiBox("Gastos Hoy",    "$0",   "#ef4444")
        self._kpi_balance  = KpiBox("Balance Neto",  "$0",   "#00d1ff")
        self._kpi_saldo    = KpiBox("Saldo Actual",  "$0",   "#a78bfa")
        for kpi in (self._kpi_ingresos, self._kpi_gastos,
                    self._kpi_balance, self._kpi_saldo):
            kpi_row.addWidget(kpi)
        main_lay.addLayout(kpi_row)

        # ── Desglose por categoría (día actual) ──────────────────────────
        lbl_pl = QLabel("P&L POR CATEGORÍA  —  DÍA ACTUAL")
        lbl_pl.setStyleSheet(
            "color: #4b5563; font-size: 10px; font-weight: 800; letter-spacing: 2px;"
        )
        main_lay.addWidget(lbl_pl)

        self._tabla_pl = QTableWidget(0, 4)
        self._tabla_pl.setHorizontalHeaderLabels(
            ["Categoría", "Ingresos", "Gastos", "Resultado"]
        )
        self._tabla_pl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabla_pl.setMaximumHeight(260)
        self._tabla_pl.verticalHeader().setVisible(False)
        main_lay.addWidget(self._tabla_pl)

        # ── Histórico 7 días ─────────────────────────────────────────────
        lbl_hist = QLabel("HISTÓRICO  —  ÚLTIMOS 7 DÍAS")
        lbl_hist.setStyleSheet(
            "color: #4b5563; font-size: 10px; font-weight: 800; letter-spacing: 2px;"
        )
        main_lay.addWidget(lbl_hist)

        self._tabla_hist = QTableWidget(0, 4)
        self._tabla_hist.setHorizontalHeaderLabels(
            ["Día", "Ingresos", "Gastos", "Balance"]
        )
        self._tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabla_hist.verticalHeader().setVisible(False)
        main_lay.addWidget(self._tabla_hist)

        main_lay.addStretch()
        self.refresh()

    # ── Refresco de datos ────────────────────────────────────────────────

    def refresh(self) -> None:
        try:
            from models.finanzas import MovimientoFinanciero
            from models.parque   import ParqueModel
            from core.motor      import MotorSimulacion

            parque     = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
            dia_actual = parque.dia_actual

            # KPIs del día
            ingresos = MovimientoFinanciero.ingresos_dia(dia_actual)
            gastos   = MovimientoFinanciero.gastos_dia(dia_actual)
            balance  = ingresos - gastos

            self._kpi_ingresos.update(f"${ingresos:,.0f}", "#10b981")
            self._kpi_gastos.update(f"${gastos:,.0f}", "#ef4444")
            color_bal = "#10b981" if balance >= 0 else "#ef4444"
            self._kpi_balance.update(f"${balance:,.0f}", color_bal)
            color_sal = "#10b981" if parque.dinero >= 0 else "#ef4444"
            self._kpi_saldo.update(f"${parque.dinero:,.0f}", color_sal)

            # Tabla P&L por categoría
            resumen = MovimientoFinanciero.resumen_por_categoria(dia_actual)
            self._poblar_tabla_pl(resumen)

            # Histórico
            historico = MovimientoFinanciero.historico_diario(7)
            self._poblar_tabla_historico(historico)

        except Exception as exc:
            pass  # BD aún vacía al inicio — silencioso

    def _poblar_tabla_pl(self, resumen: dict) -> None:
        self._tabla_pl.setRowCount(0)

        # Asegurar que todas las categorías conocidas aparecen
        cats_orden = ["entradas", "restauracion", "tienda",
                      "nominas", "reparaciones", "logistica"]
        for cat in cats_orden:
            datos = resumen.get(cat, {"ingresos": 0.0, "gastos": 0.0})
            ico, alias = CATEGORIAS.get(cat, ("·", cat.capitalize()))

            row = self._tabla_pl.rowCount()
            self._tabla_pl.insertRow(row)

            self._tabla_pl.setItem(row, 0,
                QTableWidgetItem(f"{ico}  {alias}"))

            ing_item = QTableWidgetItem(f"${datos['ingresos']:,.0f}")
            ing_item.setForeground(Qt.green if datos['ingresos'] > 0 else Qt.gray)
            self._tabla_pl.setItem(row, 1, ing_item)

            gst_item = QTableWidgetItem(f"${datos['gastos']:,.0f}")
            gst_item.setForeground(Qt.red if datos['gastos'] > 0 else Qt.gray)
            self._tabla_pl.setItem(row, 2, gst_item)

            resultado = datos['ingresos'] - datos['gastos']
            res_item  = QTableWidgetItem(f"${resultado:,.0f}")
            res_item.setForeground(Qt.green if resultado >= 0 else Qt.red)
            self._tabla_pl.setItem(row, 3, res_item)

    def _poblar_tabla_historico(self, historico: list[dict]) -> None:
        self._tabla_hist.setRowCount(0)
        for entry in historico:
            row = self._tabla_hist.rowCount()
            self._tabla_hist.insertRow(row)
            self._tabla_hist.setItem(row, 0,
                QTableWidgetItem(f"Día {entry['dia']}"))

            ing = QTableWidgetItem(f"${entry['ingresos']:,.0f}")
            ing.setForeground(Qt.green)
            self._tabla_hist.setItem(row, 1, ing)

            gst = QTableWidgetItem(f"${entry['gastos']:,.0f}")
            gst.setForeground(Qt.red)
            self._tabla_hist.setItem(row, 2, gst)

            bal = entry['balance']
            bal_item = QTableWidgetItem(f"${bal:,.0f}")
            bal_item.setForeground(Qt.green if bal >= 0 else Qt.red)
            self._tabla_hist.setItem(row, 3, bal_item)
