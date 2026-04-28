"""
ScienceWorld Park — gui/vistas/atracciones.py
Vista de atracciones limpia, retro y separada por pestañas.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QMessageBox, QFrame, QInputDialog, QTabWidget
)

from models.atracciones import AtraccionModel
from models.parque import ParqueModel
from models.empleados import EmpleadoModel
from core.motor import MotorSimulacion

_FASES_SECCION = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4}
_TIPO_REQUISITO = {
    "simulador": ("tecnico", 2),
    "mecanica": ("tecnico", 2),
    "extreme": ("tecnico", 3),
    "laboratorio": ("cientifico", 1),
    "interactiva": ("divulgador", 1),
}
_MAX_OBRAS_SIMULTANEAS = 3

_RETRO_TITLE = "color:#00ff9f; font-family:'Courier New'; font-weight:900; font-size:12px;"
_RETRO_SUB = "color:#8b9db3; font-family:'Courier New'; font-size:10px;"


class _RetroCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("SectionCard")


class OperativaCard(_RetroCard):
    def __init__(self, atr_model, parent_view):
        super().__init__()
        self.atr_db = atr_model
        self.parent_view = parent_view

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)

        left = QVBoxLayout()
        left.addWidget(QLabel(f"<b>{self.atr_db.nombre}</b>"))
        estado = "MANTENIMIENTO" if self.atr_db.en_mantenimiento else "OPERATIVA"
        meta = (
            f"[{estado}]  INT {self.atr_db.integridad:.1f}%  |  "
            f"PAX {self.atr_db.capacidad_max}  |  TICKET {self.atr_db.precio_base:.2f}€"
        )
        lbl = QLabel(meta)
        lbl.setStyleSheet(_RETRO_SUB)
        left.addWidget(lbl)
        lay.addLayout(left, 1)

        btn_det = QPushButton("DETALLES")
        btn_det.clicked.connect(self._mostrar_detalles)
        lay.addWidget(btn_det)

        btn_rep = QPushButton("REPARAR")
        btn_rep.clicked.connect(self._reparar)
        lay.addWidget(btn_rep)

    def _mostrar_detalles(self):
        dom = self.atr_db.to_domain()
        coste_rep = dom.calcular_coste_reparacion()
        info = (
            f"{self.atr_db.nombre}\n"
            f"Tipo: {self.atr_db.tipo.capitalize()} | Sección: {self.atr_db.seccion_id}\n"
            f"Integridad: {self.atr_db.integridad:.1f}% | Mantenimiento: {self.atr_db.en_mantenimiento}\n"
            f"Capacidad: {self.atr_db.capacidad_max} pax | Duración: {self.atr_db.duracion_min} min\n"
            f"Altura mín: {self.atr_db.altura_minima_cm} cm | Precio: {self.atr_db.precio_base:.2f} €\n"
            f"Coste reparación: {coste_rep:,.2f} € | Coste construcción: {self.atr_db.coste_construccion:,.0f} €"
        )
        QMessageBox.information(self, "Ficha técnica", info)

    def _reparar(self):
        dom = self.atr_db.to_domain()
        coste = dom.calcular_coste_reparacion()
        parque_id = MotorSimulacion()._parque_id
        parque = ParqueModel.get_by_id(parque_id)
        if parque.dinero < coste:
            QMessageBox.warning(self, "Economía", "Fondos insuficientes.")
            return
        ParqueModel.restar_dinero(coste, parque_id=parque_id)
        dom.reparar()
        AtraccionModel.from_domain(dom)
        self.parent_view.main_window.actualizar_interfaz()


class ProyectoCard(_RetroCard):
    def __init__(self, atr_model, parent_view, parque):
        super().__init__()
        self.atr_db = atr_model
        self.parent_view = parent_view
        self.parque = parque

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)

        fase_req = _FASES_SECCION.get(self.atr_db.seccion_id, 4)
        tipo_req, cant_req = _TIPO_REQUISITO.get(self.atr_db.tipo, ("tecnico", 1))
        activos_req = EmpleadoModel.select().where(
            (EmpleadoModel.activo == True) & (EmpleadoModel.tipo == tipo_req)
        ).count()
        dias = self.atr_db.dias_construccion_estimados

        txt = (
            f"<b>{self.atr_db.nombre}</b><br>"
            f"<span style='{_RETRO_SUB}'>"
            f"{self.atr_db.tipo.upper()} | SECCIÓN {self.atr_db.seccion_id} (F{fase_req}) | "
            f"{self.atr_db.capacidad_max} PAX | {self.atr_db.duracion_min} MIN | "
            f"{dias} DÍAS | {self.atr_db.coste_construccion:,.0f} €<br>"
            f"REQUISITO: {cant_req} {tipo_req.upper()} · DISPONIBLES: {activos_req}"
            f"</span>"
        )
        lay.addWidget(QLabel(txt), 1)

        btn = QPushButton("INICIAR")
        btn.clicked.connect(lambda: self._construir(tipo_req, cant_req, dias))
        lay.addWidget(btn)

    def _construir(self, tipo_req, cant_req, dias):
        parque_id = MotorSimulacion()._parque_id
        parque = ParqueModel.get_by_id(parque_id)
        fase_actual = self.parent_view._fase_actual(parque.dia_actual)
        fase_requerida = _FASES_SECCION.get(self.atr_db.seccion_id, 4)
        if fase_actual < fase_requerida:
            QMessageBox.information(self, "Bloqueado", f"Disponible en fase {fase_requerida}.")
            return

        obras_activas = AtraccionModel.select().where(AtraccionModel.en_construccion == True).count()
        if obras_activas >= _MAX_OBRAS_SIMULTANEAS:
            QMessageBox.information(self, "Cartera llena", "No caben más obras simultáneas.")
            return

        activos_req = EmpleadoModel.select().where(
            (EmpleadoModel.activo == True) & (EmpleadoModel.tipo == tipo_req)
        ).count()
        if activos_req < cant_req:
            QMessageBox.warning(self, "Personal", f"Necesitas {cant_req} {tipo_req}(s) activos.")
            return

        coste = self.atr_db.coste_construccion
        prioridad, ok = QInputDialog.getItem(
            self, "Prioridad", "Selecciona prioridad:", ["baja", "media", "alta"], 1, False
        )
        if not ok:
            return
        ajuste_dias = {"alta": -1, "media": 0, "baja": 1}[prioridad]
        ajuste_coste = {"alta": 0.10, "media": 0.0, "baja": -0.05}[prioridad]
        dias_final = max(1, dias + ajuste_dias)
        coste_final = max(0.0, coste * (1 + ajuste_coste))

        if parque.dinero < coste_final:
            QMessageBox.warning(self, "Economía", "Fondos insuficientes.")
            return

        ParqueModel.restar_dinero(coste_final, parque_id=parque_id)
        self.atr_db.en_construccion = True
        self.atr_db.dias_construccion_restantes = dias_final
        self.atr_db.prioridad_construccion = prioridad
        self.atr_db.construida = False
        self.atr_db.activo = False
        self.atr_db.save()
        self.parent_view.main_window.actualizar_interfaz()


class ObraCard(_RetroCard):
    def __init__(self, atr_model, parent_view):
        super().__init__()
        self.atr_db = atr_model
        self.parent_view = parent_view

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.addWidget(QLabel(
            f"<b>{self.atr_db.nombre}</b>  ·  "
            f"{self.atr_db.dias_construccion_restantes} día(s)  ·  "
            f"PRIORIDAD {self.atr_db.prioridad_construccion.upper()}"
        ), 1)

        btn = QPushButton("REASIGNAR TÉCNICOS")
        btn.clicked.connect(self._reasignar)
        lay.addWidget(btn)

    def _reasignar(self):
        parque_id = MotorSimulacion()._parque_id
        parque = ParqueModel.get_by_id(parque_id)
        tecnicos_activos = EmpleadoModel.select().where(
            (EmpleadoModel.activo == True) & (EmpleadoModel.tipo == "tecnico")
        ).count()
        if tecnicos_activos < 2:
            QMessageBox.information(self, "RRHH", "Necesitas al menos 2 técnicos activos.")
            return

        coste = 1200.0
        if parque.dinero < coste:
            QMessageBox.warning(self, "Economía", "Fondos insuficientes para reasignar.")
            return

        ParqueModel.restar_dinero(coste, parque_id=parque_id)
        self.atr_db.dias_construccion_restantes = max(0, self.atr_db.dias_construccion_restantes - 1)
        self.atr_db.prioridad_construccion = "alta"
        if self.atr_db.dias_construccion_restantes == 0:
            self.atr_db.en_construccion = False
            self.atr_db.construida = True
            self.atr_db.activo = True
        self.atr_db.save()
        self.parent_view.main_window.actualizar_interfaz()


class AtraccionesView(QScrollArea):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.container = QWidget()
        self.root = QVBoxLayout(self.container)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.refresh()

    def refresh(self):
        while self.root.count():
            it = self.root.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        fase = self._fase_actual(parque.dia_actual)
        resumen = QLabel(
            f"╔══ CENTRO DE ATRACCIONES ══╗   FASE {fase}   |   DÍA {parque.dia_actual}   |   SALDO {parque.dinero:,.0f} €"
        )
        resumen.setStyleSheet(_RETRO_TITLE)
        self.root.addWidget(resumen)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #1a1f2e; }")

        tab_oper = QWidget()
        lay_oper = QVBoxLayout(tab_oper)
        for atr in AtraccionModel.select().where(AtraccionModel.construida == True):
            lay_oper.addWidget(OperativaCard(atr, self))
        lay_oper.addStretch()

        tab_obras = QWidget()
        lay_obras = QVBoxLayout(tab_obras)
        for atr in AtraccionModel.select().where(AtraccionModel.en_construccion == True):
            lay_obras.addWidget(ObraCard(atr, self))
        lay_obras.addStretch()

        tab_proj = QWidget()
        lay_proj = QVBoxLayout(tab_proj)
        proyectos = AtraccionModel.select().where(
            (AtraccionModel.construida == False) & (AtraccionModel.en_construccion == False)
        )
        for atr in proyectos:
            lay_proj.addWidget(ProyectoCard(atr, self, parque))
        lay_proj.addStretch()

        tabs.addTab(tab_oper, "[OK] OPERATIVAS")
        tabs.addTab(tab_obras, f"[WIP] OBRAS ({_MAX_OBRAS_SIMULTANEAS} MAX)")
        tabs.addTab(tab_proj, "[PRJ] CARTERA")
        self.root.addWidget(tabs)

    @staticmethod
    def _fase_actual(dia: int) -> int:
        if dia <= 7:
            return 1
        if dia <= 14:
            return 2
        if dia <= 21:
            return 3
        return 4
