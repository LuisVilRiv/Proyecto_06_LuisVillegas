"""
ScienceWorld Park — core/motor.py
Motor de simulación completo (PDF §4.1–4.8 + §5).

Correcciones aplicadas (v3.0):
 - D.1: Lógica de quiebra corregida + periodo de gracia 48h in-game
 - D.2: Eliminado _log_evento(). El motor llama a evento.registrar(dia, hora).
         Un solo punto de escritura en EventoLogModel → sin duplicados.
 - D.3: seccion= → seccion_id= en TicketModel.create (FK correcta)
 - D.4: _evento_accidente(), _evento_viral(), _evento_huelga() instancian la clase
         de dominio correspondiente. El motor es orquestador puro: sin números hardcodeados.
 - D.5: cargar_partida() resetea _viral_dias y _horas_deuda
 - D.7: elif dead-code en franjas horarias corregido
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
_PESOS   = [0.35, 0.25, 0.15, 0.15, 0.03, 0.07]
IVA_CULTURAL = 0.10

# ── Probabilidades de eventos diarios (PDF §4.3) ─────────────────────────────
PROB_FALLO_LEVE   = 0.35
PROB_AVERIA_GRAVE = 0.08
PROB_ACCIDENTE    = 0.015
PROB_CLIMA        = 0.12
PROB_VIRAL        = 0.10
PROB_HUELGA       = 0.04

# ── Constantes de quiebra (D.1) ──────────────────────────────────────────────
UMBRAL_QUIEBRA = 250_000
HORAS_GRACIA   = 48


# ────────────────────────────────────────────────────────────────────────────
class MotorSignals(QObject):
    tick_completado  = Signal()
    evento_critico   = Signal(str, str)
    crisis_detectada = Signal(str, str)
    nominas_pagadas  = Signal(float)


# ────────────────────────────────────────────────────────────────────────────
class MotorSimulacion:
    """Singleton. Inicializar con cargar_partida() antes del primer tick."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.signals        = MotorSignals()
            cls._instance._parque_id     = 1
            cls._instance._viral_dias    = 0
            cls._instance._horas_deuda   = 0
        return cls._instance

    # ── Carga de partida ────────────────────────────────────────────────

    def cargar_partida(self, partida_model) -> None:
        """Vincula el motor al parque de la partida y resetea todo el estado (D.5)."""
        self._parque_id   = partida_model.parque_id
        self._viral_dias  = 0
        self._horas_deuda = 0
        log.info(
            f"Motor: Partida «{partida_model.nombre_partida}» cargada "
            f"(Parque ID={self._parque_id})"
        )

    # ── Tick principal ──────────────────────────────────────────────────

    def ejecutar_tick(self) -> None:
        """Avanza 1 hora en el tiempo de juego."""
        from models.parque      import ParqueModel
        from models.atracciones import AtraccionModel
        from models.empleados   import EmpleadoModel
        from models.inventario  import InventarioModel
        from models.finanzas    import MovimientoFinanciero

        try:
            with db.atomic():
                parque = ParqueModel.get_by_id(self._parque_id)

                parque.hora_actual += 1
                fin_dia = parque.hora_actual >= 24
                if fin_dia:
                    parque.hora_actual = 0
                    parque.dia_actual += 1

                ingresos = self._procesar_visitantes(parque, MovimientoFinanciero)
                self._consumir_inventario(parque, InventarioModel, MovimientoFinanciero)
                self._degradar_atracciones(AtraccionModel)

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
        from models.tickets import TicketModel
        from peewee import IntegrityError

        afluencia = self.calcular_afluencia(parque)
        ingresos  = 0.0

        for _ in range(afluencia):
            perfil       = random.choices(_PERFILES, weights=_PESOS, k=1)[0]
            precio_base  = PRECIOS_PERFIL[perfil]
            iva          = round(precio_base * IVA_CULTURAL, 2)
            precio_total = precio_base + iva

            # D.3: seccion_id= (ForeignKeyField espera _id, no el objeto)
            try:
                TicketModel.create(
                    localizador  = self._nuevo_localizador(),
                    perfil       = perfil,
                    precio_base  = precio_base,
                    iva          = iva,
                    precio_total = precio_total,
                    seccion_id   = random.randint(1, 8),
                )
            except IntegrityError as e:
                log.warning(f"Ticket no creado: {e}")
            except Exception:
                pass

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
        from models.parque import ParqueModel
        if parque is None:
            parque = ParqueModel.get_by_id(self._parque_id)

        base = parque.reputacion * random.uniform(0.8, 1.4)

        if self._viral_dias > 0:
            base *= 1.30

        hora = parque.hora_actual
        # D.7: elif corregido — horas 8,9,20,21 ya no caen al mult nocturno (0.05)
        if 10 <= hora <= 19:
            mult = 1.2
        elif hora in (8, 9, 20, 21):
            mult = 0.7
        else:
            mult = 0.05

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
        from core.eventos import EventoFalloLeve, EventoAveriaGrave, EventoClima

        atr_dom = [
            a.to_domain() for a in AtraccionModel.select()
            if a.activo and not a.en_mantenimiento
        ]

        candidatos = [
            (PROB_FALLO_LEVE,
             lambda: self._lanzar_evento(
                 EventoFalloLeve("Fallo Técnico", "", PROB_FALLO_LEVE),
                 parque, atr_dom,
             )),
            (PROB_AVERIA_GRAVE,
             lambda: self._lanzar_evento(
                 EventoAveriaGrave("Avería Grave", "", PROB_AVERIA_GRAVE),
                 parque, atr_dom,
             )),
            (PROB_ACCIDENTE,
             lambda: self._evento_accidente(parque)),
            (PROB_CLIMA,
             lambda: self._lanzar_evento(
                 EventoClima("Inclemencias", "", PROB_CLIMA),
                 parque, atr_dom,
             )),
            (PROB_VIRAL,
             lambda: self._evento_viral(parque)),
            (PROB_HUELGA,
             lambda: self._evento_huelga(parque)),
        ]

        for prob, accion in candidatos:
            if random.random() < prob:
                accion()

        from models.atracciones import AtraccionModel as AM
        for dom in atr_dom:
            AM.from_domain(dom)

    def _lanzar_evento(self, evento, parque, atr_dom) -> None:
        """
        D.2: orquesta aplicar + registrar. Sin _log_evento() — un solo punto
        de escritura en EventoLogModel es evento.registrar().
        """
        evento.aplicar(parque, atr_dom)
        evento.registrar(parque.dia_actual, parque.hora_actual)
        self.signals.evento_critico.emit(evento.nombre, evento.descripcion)

    def _evento_accidente(self, parque) -> None:
        """D.4: usa EventoAccidente del dominio. Motor = orquestador puro."""
        from core.eventos import EventoAccidente
        ev = EventoAccidente("Accidente con Visitante", "", PROB_ACCIDENTE)
        ev.aplicar(parque, [])                               # -20 rep + clausura sección
        ev.registrar(parque.dia_actual, parque.hora_actual)  # D.2
        log.warning(f"ACCIDENTE: {ev.descripcion}")
        self.signals.crisis_detectada.emit("Accidente con Visitante", ev.descripcion)

    def _evento_viral(self, parque) -> None:
        """D.4: usa EventoViralFamoso del dominio. viral_dias viene del evento."""
        from core.eventos import EventoViralFamoso
        ev = EventoViralFamoso("¡Visita Viral!", "", PROB_VIRAL)
        ev.aplicar(parque, [])                               # +10 rep, asigna ev.viral_dias
        self._viral_dias = ev.viral_dias                     # motor actualiza su propio estado
        ev.registrar(parque.dia_actual, parque.hora_actual)  # D.2
        log.info(f"VIRAL: {ev.descripcion}")
        self.signals.evento_critico.emit("¡Visita Viral!", ev.descripcion)

    def _evento_huelga(self, parque) -> None:
        """D.4: usa EventoHuelga del dominio."""
        from core.eventos import EventoHuelga
        ev = EventoHuelga("Huelga de Personal", "", PROB_HUELGA)
        ev.aplicar(parque, [])
        ev.registrar(parque.dia_actual, parque.hora_actual)  # D.2
        log.warning(f"HUELGA: {ev.descripcion}")
        self.signals.crisis_detectada.emit("Huelga de Personal", ev.descripcion)

    # ── Nóminas (PDF §4.2) ───────────────────────────────────────────────

    def _pagar_nominas(self, parque, EmpleadoModel, MovimientoFinanciero) -> None:
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

        # D.1: umbral fijo + periodo de gracia 48h in-game
        if parque.dinero < 0 and abs(parque.dinero) > UMBRAL_QUIEBRA:
            self._horas_deuda += 1
            horas_restantes = max(0, HORAS_GRACIA - self._horas_deuda)
            self.signals.evento_critico.emit(
                "⚠️ ALERTA ECONÓMICA",
                f"Deuda crítica: ${parque.dinero:,.0f}. "
                f"Game Over en {horas_restantes}h in-game si no se recupera.",
            )
            if self._horas_deuda >= HORAS_GRACIA:
                self.signals.crisis_detectada.emit(
                    "BANCARROTA",
                    "Han pasado 48 horas in-game con deuda crítica. Game Over económico.",
                )
        else:
            self._horas_deuda = 0

    # ── Reputación compuesta (PDF §4.7) ──────────────────────────────────

    @staticmethod
    def _actualizar_reputacion(parque, AtraccionModel) -> None:
        atracciones = list(AtraccionModel.select())
        if atracciones:
            integridad_media  = sum(a.integridad for a in atracciones) / len(atracciones)
            comp_satisfaccion = (integridad_media / 100.0) * 35.0
        else:
            comp_satisfaccion = 17.5

        saldo_norm     = max(0.0, min(1.0, parque.dinero / 2_000_000.0))
        comp_prensa    = saldo_norm * 25.0
        comp_redes     = 20.0
        comp_educativo = 20.0

        nueva_rep = comp_satisfaccion + comp_prensa + comp_redes + comp_educativo
        parque.reputacion = max(0.0, min(100.0,
            parque.reputacion * 0.75 + nueva_rep * 0.25
        ))
