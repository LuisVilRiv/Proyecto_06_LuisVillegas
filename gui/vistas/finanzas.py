"""
ScienceWorld Park — gui/vistas/finanzas.py
PIXEL ART RETRO Finance view.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

CATEGORIAS = {
    "entradas":     ("[E]", "VENTA ENTRADAS"),
    "restauracion": ("[R]", "RESTAURACION"),
    "tienda":       ("[T]", "TIENDA/SOUVENIRS"),
    "nominas":      ("[N]", "NOMINAS"),
    "reparaciones": ("[X]", "REPARACIONES"),
    "logistica":    ("[L]", "LOGISTICA/PEDIDOS"),
}

_MONO = "font-family: 'Courier New', monospace; background: transparent; border: none;"


def _section_header(txt: str) -> QLabel:
    lbl = QLabel(f"╔══[ {txt} ]")
    lbl.setStyleSheet(
        f"color: #00FF41; font-size: 11px; font-weight: 900;"
        f"letter-spacing: 2px; {_MONO}"
    )
    return lbl


class PixelKpiBox(QFrame):
    """Bloque KPI estilo terminal."""

    def __init__(self, titulo: str, valor: str, color: str = "#00FF41") -> None:
        super().__init__()
        self.setObjectName("SectionCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(3)

        self._lbl_titulo = QLabel(f">> {titulo}")
        self._lbl_titulo.setStyleSheet(
            f"color: #1A5C21; font-size: 8px; font-weight: 900;"
            f"letter-spacing: 2px; {_MONO} text-transform: uppercase;"
        )

        sep = QLabel("─" * 18)
        sep.setStyleSheet(f"color: #1A3D1E; font-size: 8px; {_MONO}")

        self._lbl_valor = QLabel(valor)
        self._lbl_valor.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: 900;"
            f"letter-spacing: 1px; {_MONO}"
        )

        lay.addWidget(self._lbl_titulo)
        lay.addWidget(sep)
        lay.addWidget(self._lbl_valor)

    def update(self, valor: str, color: str = None) -> None:
        self._lbl_valor.setText(valor)
        if color:
            self._lbl_valor.setStyleSheet(
                f"color: {color}; font-size: 20px; font-weight: 900;"
                f"letter-spacing: 1px; {_MONO}"
            )


class FinanzasView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 18, 20, 18)
        main_lay.setSpacing(14)

        main_lay.addWidget(_section_header("CENTRO FINANCIERO // P&L REPORT"))

        # KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self._kpi_ingresos = PixelKpiBox("INGRESOS HOY",  "$0",  "#00FF41")
        self._kpi_gastos   = PixelKpiBox("GASTOS HOY",    "$0",  "#FF2D55")
        self._kpi_balance  = PixelKpiBox("BALANCE NETO",  "$0",  "#00FFFF")
        self._kpi_saldo    = PixelKpiBox("SALDO ACTUAL",  "$0",  "#FFE600")
        for kpi in (self._kpi_ingresos, self._kpi_gastos,
                    self._kpi_balance, self._kpi_saldo):
            kpi_row.addWidget(kpi)
        main_lay.addLayout(kpi_row)

        # Tabla P&L
        main_lay.addWidget(_section_header("P&L POR CATEGORIA  //  DIA ACTUAL"))

        self._tabla_pl = QTableWidget(0, 4)
        self._tabla_pl.setHorizontalHeaderLabels(
            [">> CATEGORIA", ">> INGRESOS", ">> GASTOS", ">> RESULTADO"]
        )
        self._tabla_pl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabla_pl.setMaximumHeight(230)
        self._tabla_pl.verticalHeader().setVisible(False)
        self._tabla_pl.setStyleSheet(
            "font-family: 'Courier New', monospace; font-size: 10px;"
        )
        main_lay.addWidget(self._tabla_pl)

        # Histórico
        main_lay.addWidget(_section_header("HISTORICO  //  ULTIMOS 7 DIAS"))

        self._tabla_hist = QTableWidget(0, 4)
        self._tabla_hist.setHorizontalHeaderLabels(
            [">> DIA", ">> INGRESOS", ">> GASTOS", ">> BALANCE"]
        )
        self._tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabla_hist.verticalHeader().setVisible(False)
        self._tabla_hist.setStyleSheet(
            "font-family: 'Courier New', monospace; font-size: 10px;"
        )
        main_lay.addWidget(self._tabla_hist)
        main_lay.addStretch()
        self.refresh()

    def refresh(self) -> None:
        try:
            from models.finanzas import MovimientoFinanciero
            from models.parque   import ParqueModel
            from core.motor      import MotorSimulacion

            parque     = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
            dia_actual = parque.dia_actual

            ingresos = MovimientoFinanciero.ingresos_dia(dia_actual)
            gastos   = MovimientoFinanciero.gastos_dia(dia_actual)
            balance  = ingresos - gastos

            self._kpi_ingresos.update(f"${ingresos:,.0f}", "#00FF41")
            self._kpi_gastos.update(f"${gastos:,.0f}", "#FF2D55")
            color_bal = "#00FF41" if balance >= 0 else "#FF2D55"
            self._kpi_balance.update(f"${balance:,.0f}", color_bal)
            color_sal = "#00FF41" if parque.dinero >= 0 else "#FF2D55"
            self._kpi_saldo.update(f"${parque.dinero:,.0f}", color_sal)

            self._poblar_tabla_pl(MovimientoFinanciero.resumen_por_categoria(dia_actual))
            self._poblar_tabla_historico(MovimientoFinanciero.historico_diario(7))

        except Exception:
            pass

    def _poblar_tabla_pl(self, resumen: dict) -> None:
        self._tabla_pl.setRowCount(0)
        cats = ["entradas", "restauracion", "tienda", "nominas", "reparaciones", "logistica"]
        for cat in cats:
            datos = resumen.get(cat, {"ingresos": 0.0, "gastos": 0.0})
            ico, alias = CATEGORIAS.get(cat, ("[?]", cat.upper()))
            row = self._tabla_pl.rowCount()
            self._tabla_pl.insertRow(row)
            self._tabla_pl.setItem(row, 0, QTableWidgetItem(f"{ico}  {alias}"))

            for col, val, color in [
                (1, datos["ingresos"], "#00FF41"),
                (2, datos["gastos"],   "#FF2D55"),
                (3, datos["ingresos"] - datos["gastos"],
                   "#00FF41" if datos["ingresos"] >= datos["gastos"] else "#FF2D55"),
            ]:
                item = QTableWidgetItem(f"${val:,.0f}" if col != 3
                                        else f"${datos['ingresos'] - datos['gastos']:,.0f}")
                item.setForeground(Qt.green if color == "#00FF41" else Qt.red)
                self._tabla_pl.setItem(row, col, item)

    def _poblar_tabla_historico(self, historico: list[dict]) -> None:
        self._tabla_hist.setRowCount(0)
        for entry in historico:
            row = self._tabla_hist.rowCount()
            self._tabla_hist.insertRow(row)
            self._tabla_hist.setItem(row, 0, QTableWidgetItem(f"DIA {entry['dia']:03d}"))

            ing = QTableWidgetItem(f"${entry['ingresos']:,.0f}")
            ing.setForeground(Qt.green)
            self._tabla_hist.setItem(row, 1, ing)

            gst = QTableWidgetItem(f"${entry['gastos']:,.0f}")
            gst.setForeground(Qt.red)
            self._tabla_hist.setItem(row, 2, gst)

            bal = entry["balance"]
            bal_item = QTableWidgetItem(f"${bal:,.0f}")
            bal_item.setForeground(Qt.green if bal >= 0 else Qt.red)
            self._tabla_hist.setItem(row, 3, bal_item)
