"""
ScienceWorld Park — core/motor.py
Motor de simulación completo (PDF §4.1–4.8 + §5).
"""

import random
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from core.logger import log
from models.db import db

# ── Tabla de precios por perfil (se mantiene como fallback) ────────────────
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

# ── Probabilidades de eventos ──────────────────────────────────────────────
PROB_FALLO_LEVE   = 0.35
PROB_AVERIA_GRAVE = 0.08
PROB_ACCIDENTE    = 0.015
PROB_CLIMA        = 0.12
PROB_VIRAL        = 0.10
PROB_HUELGA       = 0.04

# ── Quiebra ────────────────────────────────────────────────────────────────
UMBRAL_QUIEBRA = 250_000
HORAS_GRACIA   = 48
PENALIZACION_SOBRECARGA = 0.8


class MotorSignals(QObject):
    tick_completado  = Signal()
    evento_critico   = Signal(str, str)
    crisis_detectada = Signal(str, str)
    nominas_pagadas  = Signal(float)


class MotorSimulacion:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.signals        = MotorSignals()
            cls._instance._parque_id     = 1
            cls._instance._viral_dias    = 0
            cls._instance._horas_deuda   = 0
            cls._instance._factor_riesgo_sobrecarga = 1.0
        return cls._instance

    def cargar_partida(self, partida_model) -> None:
        self._parque_id   = partida_model.parque_id
        self._viral_dias  = 0
        self._horas_deuda = 0
        self._factor_riesgo_sobrecarga = 1.0
        log.info(
            f"Motor: Partida «{partida_model.nombre_partida}» cargada "
            f"(Parque ID={self._parque_id})"
        )

    # ── TICK ────────────────────────────────────────────────────────────

    def ejecutar_tick(self) -> None:
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
                    self._procesar_construcciones(AtraccionModel)
                    self._aplicar_penalizacion_sobrecarga(parque, EmpleadoModel, AtraccionModel)
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

    # ── VISITANTES (AQUÍ ESTÁ EL CAMBIO) ─────────────────────────────────

    def _procesar_visitantes(self, parque, MovimientoFinanciero) -> float:
        from models.tickets import TicketModel
        from peewee import IntegrityError

        afluencia = self.calcular_afluencia(parque)
        ingresos  = 0.0

        for _ in range(afluencia):
            perfil = random.choices(_PERFILES, weights=_PESOS, k=1)[0]

            # 🔥 NUEVA LÓGICA DINÁMICA
            if perfil == "nino":
                precio_base = parque.precio_entrada_nino
            elif perfil == "adulto":
                precio_base = parque.precio_entrada_adulto
            else:
                # fallback para otros perfiles
                precio_base = PRECIOS_PERFIL[perfil]

            iva          = round(precio_base * IVA_CULTURAL, 2)
            precio_total = precio_base + iva

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

    # ── RESTO SIN CAMBIOS ───────────────────────────────────────────────

    def calcular_afluencia(self, parque=None) -> int:
        from models.parque import ParqueModel
        if parque is None:
            parque = ParqueModel.get_by_id(self._parque_id)

        base = parque.reputacion * random.uniform(0.8, 1.4)

        if self._viral_dias > 0:
            base *= 1.30

        hora = parque.hora_actual
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

    @staticmethod
    def _procesar_construcciones(AtraccionModel) -> None:
        pendientes = (
            AtraccionModel
            .select()
            .where(AtraccionModel.en_construccion == True)
        )
        for atr in pendientes:
            atr.dias_construccion_restantes = max(0, atr.dias_construccion_restantes - 1)
            if atr.dias_construccion_restantes == 0:
                atr.en_construccion = False
                atr.construida = True
                atr.activo = True
                log.info(f"Construcción finalizada: {atr.nombre}")
            atr.save()

    def _aplicar_penalizacion_sobrecarga(self, parque, EmpleadoModel, AtraccionModel) -> None:
        obras = AtraccionModel.select().where(AtraccionModel.en_construccion == True).count()
        tecnicos = EmpleadoModel.select().where(
            (EmpleadoModel.activo == True) & (EmpleadoModel.tipo == "tecnico")
        ).count()
        capacidad = max(1, tecnicos // 2)
        if obras > capacidad:
            exceso = obras - capacidad
            parque.reputacion = max(0.0, parque.reputacion - (PENALIZACION_SOBRECARGA * exceso))
            self._factor_riesgo_sobrecarga = min(1.8, 1.0 + 0.2 * exceso)
            log.warning(
                "Sobrecarga de personal de obra: "
                f"{obras} obras para {tecnicos} técnicos. "
                f"Reputación penalizada a {parque.reputacion:.1f}. "
                f"Riesgo técnico x{self._factor_riesgo_sobrecarga:.2f}"
            )
        else:
            self._factor_riesgo_sobrecarga = 1.0

    def _degradar_atracciones(self, AtraccionModel) -> None:
        factor = max(1.0, self._factor_riesgo_sobrecarga)
        for atr in AtraccionModel.select().where(AtraccionModel.activo == True):
            desgaste = random.uniform(0.05, 0.35) * factor
            atr.integridad = max(0.0, atr.integridad - desgaste)
            atr.save()

    @staticmethod
    def _consumir_inventario(parque, InventarioModel, MovimientoFinanciero) -> None:
        for item in InventarioModel.select():
            consumo = min(item.stock_actual, random.uniform(0.2, 1.2))
            if consumo <= 0:
                continue
            item.stock_actual = max(0.0, item.stock_actual - consumo)
            item.save()
            MovimientoFinanciero.create(
                tipo="gasto",
                categoria="logistica",
                concepto=f"Consumo operativo {item.nombre}",
                importe=round(consumo * item.precio_compra, 2),
                iva=0.0,
                dia_juego=parque.dia_actual,
                hora_juego=parque.hora_actual,
            )

    @staticmethod
    def _evaluar_eventos_dia(parque, AtraccionModel) -> None:
        from models.eventos_log import EventoLogModel

        if random.random() < PROB_FALLO_LEVE:
            EventoLogModel.create(
                tipo="Fallo Técnico",
                descripcion="Incidencia menor en operación diaria",
                dia_juego=parque.dia_actual,
                hora_juego=parque.hora_actual,
            )
        if random.random() < PROB_AVERIA_GRAVE:
            parque.reputacion = max(0.0, parque.reputacion - 1.5)
            EventoLogModel.create(
                tipo="Avería Grave",
                descripcion="Avería crítica en una atracción",
                dia_juego=parque.dia_actual,
                hora_juego=parque.hora_actual,
            )
            atr = AtraccionModel.select().where(AtraccionModel.activo == True).first()
            if atr:
                atr.activo = False
                atr.en_mantenimiento = True
                atr.save()

    def _pagar_nominas(self, parque, EmpleadoModel, MovimientoFinanciero) -> None:
        total = sum(
            emp.salario_mes / 30.0
            for emp in EmpleadoModel.select().where(EmpleadoModel.activo == True)
        )
        if total <= 0:
            return
        parque.dinero -= total
        MovimientoFinanciero.create(
            tipo="gasto",
            categoria="nominas",
            concepto="Pago de nóminas diarias",
            importe=round(total, 2),
            iva=0.0,
            dia_juego=parque.dia_actual,
            hora_juego=parque.hora_actual,
        )
        self.signals.nominas_pagadas.emit(total)

    @staticmethod
    def _actualizar_reputacion(parque, AtraccionModel) -> None:
        activas = list(AtraccionModel.select().where(AtraccionModel.activo == True))
        if not activas:
            parque.reputacion = max(0.0, parque.reputacion - 0.5)
            return
        integridad_media = sum(a.integridad for a in activas) / len(activas)
        parque.reputacion = max(
            0.0,
            min(100.0, parque.reputacion + ((integridad_media - 70.0) / 100.0)),
        )