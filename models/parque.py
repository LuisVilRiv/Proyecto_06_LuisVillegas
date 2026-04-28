"""
ScienceWorld Park — models/parque.py
Estado global y economía del parque activo.
"""

from peewee import CharField, FloatField, IntegerField, BooleanField
from models.db import BaseModel, db
from core.motor import MotorSimulacion


class ParqueModel(BaseModel):
    nombre = CharField()

    # ── ECONOMÍA BASE ─────────────────────────────────────────
    dinero = FloatField(default=2_000_000.0)
    reputacion = FloatField(default=50.0)

    # ── PRECIOS (puedes usarlo como sistema base o override UI)
    precio_entrada = FloatField(default=25.0)  # compatibilidad antigua
    precio_entrada_adulto = FloatField(default=27.0)
    precio_entrada_nino = FloatField(default=18.0)

    # ── TIEMPO DEL JUEGO ──────────────────────────────────────
    dia_actual = IntegerField(default=1)
    hora_actual = IntegerField(default=8)

    # ── ESTADO GLOBAL ─────────────────────────────────────────
    abierto = BooleanField(default=False)

    class Meta:
        table_name = "parque"

    # ───────────────────────────────────────────────────────────
    @classmethod
    def restar_dinero(cls, cantidad: float, parque_id: int = None) -> float:
        """Resta dinero de forma atómica."""
        if parque_id is None:
            parque_id = MotorSimulacion()._parque_id

        with db.atomic():
            parque = cls.get_by_id(parque_id)
            parque.dinero -= cantidad
            parque.save()
            return parque.dinero

    # ───────────────────────────────────────────────────────────
    @classmethod
    def sumar_dinero(cls, cantidad: float, parque_id: int = None) -> float:
        """Añade dinero de forma atómica."""
        if parque_id is None:
            parque_id = MotorSimulacion()._parque_id

        with db.atomic():
            parque = cls.get_by_id(parque_id)
            parque.dinero += cantidad
            parque.save()
            return parque.dinero