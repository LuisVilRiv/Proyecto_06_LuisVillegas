"""
ScienceWorld Park — models/parque.py
Estado global y economía del parque activo.
"""

from peewee import CharField, FloatField, IntegerField, BooleanField
from models.db import BaseModel, db


class ParqueModel(BaseModel):
    nombre     = CharField()
    dinero     = FloatField(default=2_000_000.0)
    reputacion = FloatField(default=50.0)
    dia_actual = IntegerField(default=1)
    hora_actual = IntegerField(default=8)
    abierto    = BooleanField(default=False)

    class Meta:
        table_name = "parque"

    @classmethod
    def restar_dinero(cls, cantidad: float, parque_id: int = None) -> float:
        """
        Resta *cantidad* de forma atómica.
        Usa el parque activo del motor si no se especifica parque_id.
        """
        from core.motor import MotorSimulacion
        if parque_id is None:
            parque_id = MotorSimulacion()._parque_id

        with db.atomic():
            parque = cls.get_by_id(parque_id)
            parque.dinero -= cantidad
            parque.save()
            return parque.dinero

    @classmethod
    def sumar_dinero(cls, cantidad: float, parque_id: int = None) -> float:
        """Añade *cantidad* de forma atómica."""
        from core.motor import MotorSimulacion
        if parque_id is None:
            parque_id = MotorSimulacion()._parque_id

        with db.atomic():
            parque = cls.get_by_id(parque_id)
            parque.dinero += cantidad
            parque.save()
            return parque.dinero
