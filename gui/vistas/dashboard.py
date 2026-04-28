"""
ScienceWorld Park — gui/vistas/dashboard.py
Dashboard principal: historial de eventos + resumen de estado del parque.

Correcciones aplicadas (v3.0):
 - E.2: refresh() ya no silencia excepciones — las loggea con traceback completo
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QFrame, QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui  import QColor
from core.logger import log


# Colores por tipo de evento
_COLORES_EVENTO = {
    "Fallo Técnico": "#f59e0b",
    "Avería Grave":  "#ef4444",
    "Accidente":     "#ef4444",
    "Inclemencias":  "#6b7280",
    "Viral":         "#10b981",
    "Huelga":        "#a78bfa",
}
_COLOR_DEFAULT = "#4b5563"


class StatRow(QFrame):
    """Fila de estadística con barra de progreso."""

    def __init__(self, etiqueta: str, color: str = "#00d1ff") -> None:
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(12)

        self._lbl = QLabel(etiqueta)
        self._lbl.setFixedWidth(180)
        self._lbl.setStyleSheet("color: #6b7280; font-size: 11px;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
        )

        lay.addWidget(self._lbl)
        lay.addWidget(self._bar)

    def set_value(self, v: int, texto: str = "") -> None:
        self._bar.setValue(max(0, min(100, v)))
        if texto:
            self._bar.setFormat(texto)


class DashboardView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        main = QHBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(20)

        # ── Columna izquierda: estado del parque ──────────────────────────
        left = QVBoxLayout()
        left.setSpacing(14)

        lbl_estado = QLabel("[OK] ESTADO DEL PARQUE")
        lbl_estado.setStyleSheet(
            "color: #00ff9f; font-size: 13px; font-weight: 900;"
            "letter-spacing: 2px; font-family: 'Courier New';"
        )
        left.addWidget(lbl_estado)

        card = QFrame()
        card.setObjectName("SectionCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(18, 16, 18, 16)
        card_lay.setSpacing(10)

        self._stat_rep    = StatRow("Reputación",          "#a78bfa")
        self._stat_int    = StatRow("Integridad Atracciones", "#00d1ff")
        self._stat_stock  = StatRow("Stock Inventario",    "#10b981")
        self._stat_emp    = StatRow("Personal Activo",     "#f59e0b")

        for s in (self._stat_rep, self._stat_int, self._stat_stock, self._stat_emp):
            card_lay.addWidget(s)
        left.addWidget(card)

        # Resumen económico
        lbl_eco = QLabel("[FIN] RESUMEN ECONÓMICO")
        lbl_eco.setStyleSheet(
            "color: #79d2b5; font-size: 10px; font-weight: 800; letter-spacing: 1px;"
            "font-family: 'Courier New';"
        )
        left.addWidget(lbl_eco)

        eco_card = QFrame()
        eco_card.setObjectName("SectionCard")
        eco_lay = QVBoxLayout(eco_card)
        eco_lay.setContentsMargins(18, 14, 18, 14)
        eco_lay.setSpacing(6)

        self._lbl_eco_items: dict[str, QLabel] = {}
        for clave, texto in [
            ("saldo",    "Saldo:"),
            ("dia",      "Día actual:"),
            ("empleados","Empleados:"),
            ("atracciones", "Atracciones:"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl_k = QLabel(texto)
            lbl_k.setStyleSheet("color: #4b5563; font-size: 11px;")
            lbl_k.setFixedWidth(120)
            lbl_v = QLabel("—")
            lbl_v.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
            row.addWidget(lbl_k)
            row.addWidget(lbl_v)
            row.addStretch()
            eco_lay.addLayout(row)
            self._lbl_eco_items[clave] = lbl_v

        left.addWidget(eco_card)
        left.addStretch()

        # ── Columna derecha: historial de eventos ─────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        lbl_hist = QLabel("[LOG] HISTORIAL DE EVENTOS")
        lbl_hist.setStyleSheet(
            "color: #00ff9f; font-size: 13px; font-weight: 900;"
            "letter-spacing: 2px; font-family: 'Courier New';"
        )
        right.addWidget(lbl_hist)

        lbl_hint = QLabel("Los últimos 20 sucesos registrados por el motor de simulación.")
        lbl_hint.setStyleSheet("color: #374151; font-size: 10px;")
        right.addWidget(lbl_hint)

        self._list_events = QListWidget()
        self._list_events.setSpacing(1)
        right.addWidget(self._list_events)

        main.addLayout(left, 35)
        main.addLayout(right, 65)

        self.refresh()

    # ── Refresco ─────────────────────────────────────────────────────────

    def refresh(self) -> None:
        # E.2: ya no silenciamos excepciones — las loggeamos con traceback completo
        try:
            self._refrescar_estado()
            self._refrescar_eventos()
        except Exception as exc:
            log.error(f"Dashboard refresh fallido: {exc}", exc_info=True)

    def _refrescar_estado(self) -> None:
        from models.parque      import ParqueModel
        from models.atracciones import AtraccionModel
        from models.empleados   import EmpleadoModel
        from models.inventario  import InventarioModel
        from core.motor         import MotorSimulacion

        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)

        self._stat_rep.set_value(int(parque.reputacion), f"{parque.reputacion:.1f}%")

        atracciones = list(AtraccionModel.select())
        if atracciones:
            int_media = sum(a.integridad for a in atracciones) / len(atracciones)
            self._stat_int.set_value(int(int_media), f"{int_media:.1f}%")
        else:
            self._stat_int.set_value(0)

        items  = list(InventarioModel.select())
        ok     = sum(1 for i in items if i.stock_actual > i.stock_minimo)
        pct    = int((ok / len(items)) * 100) if items else 100
        self._stat_stock.set_value(pct, f"{ok}/{len(items)} OK")

        total_emp  = EmpleadoModel.select().count()
        activos    = EmpleadoModel.select().where(EmpleadoModel.activo == True).count()
        pct_emp    = int((activos / total_emp) * 100) if total_emp else 0
        self._stat_emp.set_value(pct_emp, f"{activos} activos")

        self._lbl_eco_items["saldo"].setText(f"${parque.dinero:,.0f}")
        self._lbl_eco_items["saldo"].setStyleSheet(
            f"color: {'#10b981' if parque.dinero >= 0 else '#ef4444'};"
            "font-size: 11px; font-weight: bold;"
        )
        self._lbl_eco_items["dia"].setText(
            f"Día {parque.dia_actual}  ·  {parque.hora_actual:02d}:00h"
        )
        self._lbl_eco_items["empleados"].setText(str(total_emp))
        self._lbl_eco_items["atracciones"].setText(
            f"{len([a for a in atracciones if a.activo])} / {len(atracciones)}"
        )

    def _refrescar_eventos(self) -> None:
        from models.eventos_log import EventoLogModel

        self._list_events.clear()
        logs = (EventoLogModel.select()
                .order_by(EventoLogModel.id.desc())
                .limit(20))

        for entry in logs:
            color = _COLORES_EVENTO.get(entry.tipo, _COLOR_DEFAULT)
            texto = (
                f"  [Día {entry.dia_juego:3d}  {entry.hora_juego:02d}:00]  "
                f"{entry.tipo}:  {entry.descripcion}"
            )
            item = QListWidgetItem(texto)
            item.setForeground(QColor(color))
            self._list_events.addItem(item)
