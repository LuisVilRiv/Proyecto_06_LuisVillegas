from peewee import CharField, FloatField, IntegerField, BooleanField
from models.db import BaseModel, db

class ParqueModel(BaseModel):
    """Representa el estado global del parque y su economía."""
    nombre = CharField()
    dinero = FloatField(default=2000000.0)
    reputacion = FloatField(default=50.0)
    dia_actual = IntegerField(default=1)
    hora_actual = IntegerField(default=8)
    abierto = BooleanField(default=False)

    class Meta:
        table_name = 'parque'

    @classmethod
    def restar_dinero(cls, cantidad: float):
        """Resta fondos de forma atómica y garantiza la persistencia."""
        with db.atomic():
            parque = cls.get_by_id(1)
            parque.dinero -= cantidad
            parque.save()
            return parque.dinero