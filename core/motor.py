"""
ScienceWorld Park — core/motor.py
Motor de simulación completo (PDF §4.1–4.8 + §5).

Correcciones respecto a la versión anterior:
 - cargar_partida() para vincular al parque de la partida activa
 - Ingresos por tickets con IVA 10% y precios por perfil (PDF §12.2)
 - Eventos aleatorios con probabilidades del PDF §4.3
 - Nóminas diarias (1/30 del salario mensual) al cierre de cada día
 - Señal crisis_detectada para diálogos de decisión
 - Índice de reputación dinámico
"""

import random
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from core.logger import log
from models.db import db

# ── Tabla de precios por perfil (PDF §12.2) ─────────────────────────────────
PRECIOS_PERFIL: dict[str, float] = {
    "adulto":        27.0,
    "nino":          18.0,
    "grupo_escolar": 12.0,
    "turista":       32.0,
    "vip":           85.0,
    "aficionado":    27.0,
}
_PERFILES = list(PRECIOS_PERFIL.keys())
_PESOS   = [0.35, 0.25, 0.15, 0.15, 0.03, 0.07]   # suma = 1.0
IVA_CULTURAL = 0.10  # tipo reducido actividades culturales/ocio (PDF §12.2)

# ── Probabilidades de eventos diarios (PDF §4.3) ─────────────────────────────
PROB_FALLO_LEVE   = 0.35   # ~4% por atracción → ~35% global al día
PROB_AVERIA_GRAVE = 0.08
PROB_ACCIDENTE    = 0.015
PROB_CLIMA        = 0.12
PROB_VIRAL        = 0.10   # 1.5%/semana ≈ 10% al día
PROB_HUELGA       = 0.04   # hostelería / técnicos


# ────────────────────────────────────────────────────────────────────────────
class MotorSignals(QObject):
    tick_completado  = Signal()
    evento_critico   = Signal(str, str)   # titulo, mensaje
    crisis_detectada = Signal(str, str)   # titulo, descripcion (abre CrisisDialog)
    nominas_pagadas  = Signal(float)      # importe total del día


# ────────────────────────────────────────────────────────────────────────────
class MotorSimulacion:
    """Singleton. Inicializar con cargar_partida() antes del primer tick."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.signals        = MotorSignals()
            cls._instance._parque_id     = 1
            cls._instance._viral_dias    = 0   # días restantes de bonus viral
        return cls._instance

    # ── Carga de partida ────────────────────────────────────────────────

    def cargar_partida(self, partida_model) -> None:
        """Vincula el motor al parque de la partida seleccionada."""
        self._parque_id = partida_model.parque_id
        log.info(
            f"Motor: Partida «{partida_model.nombre_partida}» cargada "
            f"(Parque ID={self._parque_id})"
        )

    # ── Tick principal ──────────────────────────────────────────────────

    def ejecutar_tick(self) -> None:
        """Avanza 1 hora en el tiempo de juego."""
        from models.parque    import ParqueModel
        from models.atracciones import AtraccionModel
        from models.empleados   import EmpleadoModel
        from models.inventario  import InventarioModel
        from models.finanzas    import MovimientoFinanciero

        try:
            with db.atomic():
                parque = ParqueModel.get_by_id(self._parque_id)

                # 1. Avanzar tiempo
                parque.hora_actual += 1
                fin_dia = parque.hora_actual >= 24
                if fin_dia:
                    parque.hora_actual = 0
                    parque.dia_actual += 1

                # 2. Ingresos por visitantes + tickets con IVA
                ingresos = self._procesar_visitantes(parque, MovimientoFinanciero)

                # 3. Ventas de restauración y tienda
                self._consumir_inventario(parque, InventarioModel, MovimientoFinanciero)

                # 4. Desgaste de atracciones
                self._degradar_atracciones(AtraccionModel)

                # 5. Acciones de fin de día
                if fin_dia:
                    self._evaluar_eventos_dia(parque, AtraccionModel)
                    self._pagar_nominas(parque, EmpleadoModel, MovimientoFinanciero)
                    self._actualizar_reputacion(parque, AtraccionModel)
                    if self._viral_dias > 0:
                        self._viral_dias -= 1

                parque.save()

            log.info(
                f"Tick completado. Ingresos: +${ingresos:,.2f}. "
                f"Día {parque.dia_actual} Hora {parque.hora_actual:02d}"
            )
            self.signals.tick_completado.emit()

        except Exception as exc:
            log.error(f"Fallo crítico en motor: {exc}", exc_info=True)
            raise

    # ── Visitantes e ingresos (PDF §12.2) ───────────────────────────────

    def _procesar_visitantes(self, parque, MovimientoFinanciero) -> float:
        """Genera afluencia, emite tickets con IVA y acumula dinero."""
        from models.tickets import TicketModel

        afluencia   = self.calcular_afluencia(parque)
        ingresos    = 0.0

        for _ in range(afluencia):
            perfil      = random.choices(_PERFILES, weights=_PESOS, k=1)[0]
            precio_base = PRECIOS_PERFIL[perfil]
            iva         = round(precio_base * IVA_CULTURAL, 2)
            precio_total = precio_base + iva

            # Ticket con localizador único
            try:
                TicketModel.create(
                    localizador  = self._nuevo_localizador(),
                    perfil       = perfil,
                    precio_base  = precio_base,
                    iva          = iva,
                    precio_total = precio_total,
                    seccion      = random.randint(1, 8),
                )
            except Exception:
                pass  # localizador duplicado: raro, ignorar

            parque.dinero += precio_total
            ingresos      += precio_total

            MovimientoFinanciero.create(
                tipo       = "ingreso",
                categoria  = "entradas",
                concepto   = f"Ticket {perfil}",
                importe    = precio_base,
                iva        = iva,
                dia_juego  = parque.dia_actual,
                hora_juego = parque.hora_actual,
            )

        return ingresos

    def calcular_afluencia(self, parque=None) -> int:
        """Afluencia horaria basada en reputación, hora del día y eventos activos."""
        from models.parque import ParqueModel
        if parque is None:
            parque = ParqueModel.get_by_id(self._parque_id)

        base = parque.reputacion * random.uniform(0.8, 1.4)

        if self._viral_dias > 0:
            base *= 1.30  # +30% por visita viral (PDF: +20–40%)

        hora = parque.hora_actual
        if   10 <= hora <= 19:  mult = 1.2
        elif  8 <= hora <= 21:  mult = 0.7
        else:                   mult = 0.05  # noche

        return max(0, int(base * mult))

    @staticmethod
    def _nuevo_localizador() -> str:
        import string
        chars = string.ascii_uppercase + string.digits
        return "SW-" + "".join(random.choices(chars, k=8))

    # ── Inventario / restauración / tienda ──────────────────────────────

    @staticmethod
    def _consumir_inventario(parque, InventarioModel, MovimientoFinanciero) -> None:
        productos = [
            ("Comida Espacial", 20.0, "restauracion"),
            ("Newton Peluche",  35.0, "tienda"),
            ("Kit ADN Junior",  25.0, "tienda"),
            ("Cristal Mineral", 15.0, "tienda"),
        ]
        pesos = [0.55, 0.25, 0.12, 0.08]

        # ~25% de los visitantes-hora consumen algo
        consumidores = int(parque.reputacion * random.uniform(0.3, 0.7) * 0.25)
        for _ in range(consumidores):
            nombre, precio, cat = random.choices(productos, weights=pesos, k=1)[0]
            if InventarioModel.reducir_stock(nombre, 1):
                parque.dinero += precio
                MovimientoFinanciero.create(
                    tipo       = "ingreso",
                    categoria  = cat,
                    concepto   = f"Venta {nombre}",
                    importe    = precio,
                    iva        = round(precio * 0.10, 2),
                    dia_juego  = parque.dia_actual,
                    hora_juego = parque.hora_actual,
                )
            else:
                log.warning(f"VENTA PERDIDA: Sin stock de {nombre}.")

    # ── Desgaste de atracciones ─────────────────────────────────────────

    @staticmethod
    def _degradar_atracciones(AtraccionModel) -> None:
        for atr_db in AtraccionModel.select():
            if not atr_db.activo or atr_db.en_mantenimiento:
                continue
            dom = atr_db.to_domain()
            tasa = getattr(dom, "tasa_desgaste", 0.5)
            dom.degradar(random.uniform(tasa * 0.2, tasa * 0.6))
            if dom.integridad <= 0.0:
                dom.en_mantenimiento = True
            AtraccionModel.from_domain(dom)

    # ── Eventos aleatorios (fin de día, PDF §4.3) ────────────────────────

    def _evaluar_eventos_dia(self, parque, AtraccionModel) -> None:
        from core.eventos import (
            EventoFalloLeve, EventoAveriaGrave, EventoClima,
        )
        atr_dom = [
            a.to_domain() for a in AtraccionModel.select()
            if a.activo and not a.en_mantenimiento
        ]

        candidatos = [
            (PROB_FALLO_LEVE,
             lambda: self._lanzar_evento(
                 EventoFalloLeve("Fallo Técnico", "", PROB_FALLO_LEVE),
                 parque, atr_dom, "warning"
             )),
            (PROB_AVERIA_GRAVE,
             lambda: self._lanzar_evento(
                 EventoAveriaGrave("Avería Grave", "", PROB_AVERIA_GRAVE),
                 parque, atr_dom, "error"
             )),
            (PROB_ACCIDENTE,
             lambda: self._evento_accidente(parque)),
            (PROB_CLIMA,
             lambda: self._lanzar_evento(
                 EventoClima("Inclemencias", "", PROB_CLIMA),
                 parque, atr_dom, "warning"
             )),
            (PROB_VIRAL,
             lambda: self._evento_viral(parque)),
            (PROB_HUELGA,
             lambda: self._evento_huelga(parque)),
        ]

        for prob, accion in candidatos:
            if random.random() < prob:
                accion()

        # Persistir cambios en atracciones
        from models.atracciones import AtraccionModel as AM
        for dom in atr_dom:
            AM.from_domain(dom)

    def _lanzar_evento(self, evento, parque, atr_dom, nivel: str) -> None:
        evento.aplicar(parque, atr_dom)
        self._log_evento(evento.nombre, evento.descripcion, parque)
        self.signals.evento_critico.emit(evento.nombre, evento.descripcion)

    def _evento_accidente(self, parque) -> None:
        parque.reputacion = max(0.0, parque.reputacion - 15.0)
        titulo = "Accidente con Visitante"
        desc   = ("Se ha reportado un incidente grave. Reputación -15. "
                  "Inspeccion regulatoria en curso.")
        self._log_evento(titulo, desc, parque)
        log.warning(f"ACCIDENTE: {desc}")
        self.signals.crisis_detectada.emit(titulo, desc)

    def _evento_viral(self, parque) -> None:
        parque.reputacion = min(100.0, parque.reputacion + 10.0)
        self._viral_dias  = random.randint(2, 4)
        titulo = "¡Visita Viral!"
        desc   = (f"Una personalidad famosa visitó el parque. Reputación +10. "
                  f"Afluencia +30% durante {self._viral_dias} días.")
        self._log_evento(titulo, desc, parque)
        log.info(f"VIRAL: {desc}")
        self.signals.evento_critico.emit(titulo, desc)

    def _evento_huelga(self, parque) -> None:
        titulo = "Huelga de Personal"
        desc   = ("El personal de hostelería ha convocado huelga. "
                  "Ingresos de restauración reducidos al 20% durante 24h.")
        self._log_evento(titulo, desc, parque)
        log.warning(f"HUELGA: {desc}")
        self.signals.crisis_detectada.emit(titulo, desc)

    @staticmethod
    def _log_evento(tipo: str, desc: str, parque) -> None:
        from models.eventos_log import EventoLogModel
        EventoLogModel.create(
            tipo       = tipo,
            descripcion= desc,
            dia_juego  = parque.dia_actual,
            hora_juego = parque.hora_actual,
            timestamp  = datetime.now(),
        )

    # ── Nóminas (PDF §4.2) ───────────────────────────────────────────────

    def _pagar_nominas(self, parque, EmpleadoModel, MovimientoFinanciero) -> None:
        """Paga 1/30 del salario mensual de cada empleado activo."""
        empleados = list(EmpleadoModel.select().where(EmpleadoModel.activo == True))
        if not empleados:
            return

        total = sum(e.salario_mes / 30.0 for e in empleados)
        parque.dinero -= total

        MovimientoFinanciero.create(
            tipo       = "gasto",
            categoria  = "nominas",
            concepto   = f"Nóminas {len(empleados)} empleados (pago diario)",
            importe    = total,
            iva        = 0.0,
            dia_juego  = parque.dia_actual,
            hora_juego = parque.hora_actual,
        )
        log.info(f"NÓMINAS PAGADAS: -${total:,.2f} ({len(empleados)} empleados)")
        self.signals.nominas_pagadas.emit(total)

        # Alerta de quiebra (PDF §4.1: deuda > 150% del activo)
        if parque.dinero < 0 and abs(parque.dinero) > parque.dinero * 0.5:
            self.signals.evento_critico.emit(
                "⚠️ ALERTA DE QUIEBRA",
                f"Saldo negativo: ${parque.dinero:,.0f}. Toma medidas urgentes.",
            )

    # ── Reputación compuesta (PDF §4.7) ──────────────────────────────────

    @staticmethod
    def _actualizar_reputacion(parque, AtraccionModel) -> None:
        """
        35% satisfacción visitantes (proxy: integridad media de atracciones)
        25% prensa              (proxy: nivel económico del parque)
        20% redes sociales      (componente fijo moderado)
        20% índice educativo    (componente fijo moderado)
        """
        atracciones = list(AtraccionModel.select())
        if atracciones:
            integridad_media = sum(a.integridad for a in atracciones) / len(atracciones)
            comp_satisfaccion = (integridad_media / 100.0) * 35.0
        else:
            comp_satisfaccion = 17.5

        # Componente prensa: basado en saldo del parque (normalizado a 2M€)
        saldo_norm     = max(0.0, min(1.0, parque.dinero / 2_000_000.0))
        comp_prensa    = saldo_norm * 25.0

        comp_redes     = 20.0   # simplificado (sin módulo Marketing aún)
        comp_educativo = 20.0   # simplificado

        nueva_rep = comp_satisfaccion + comp_prensa + comp_redes + comp_educativo

        # Suavizado: 75% reputación anterior + 25% nuevo cálculo
        parque.reputacion = max(0.0, min(100.0,
            parque.reputacion * 0.75 + nueva_rep * 0.25
        ))
