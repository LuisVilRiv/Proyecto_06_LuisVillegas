import random
import string
from datetime import datetime
from peewee import CharField, FloatField, BooleanField, ForeignKeyField, DateTimeField
from models.db import BaseModel
from models.secciones import SeccionModel

class TicketModel(BaseModel):
    """Registro persistente de ventas con localizador único."""
    localizador = CharField(unique=True)
    perfil = CharField()
    precio_base = FloatField()
    iva = FloatField()
    precio_total = FloatField()
    seccion = ForeignKeyField(SeccionModel, backref='tickets', null=True)
    fecha_emision = DateTimeField(default=datetime.now)
    usado = BooleanField(default=False)

    class Meta:
        table_name = 'tickets'

    @classmethod
    def generar_ticket(cls, perfil: str, precio_base: float, seccion_id: int = None):
        """Crea un ticket con IVA del 10% y localizador SW-XXXXXX."""
        iva = precio_base * 0.10
        total = precio_base + iva
        chars = string.ascii_uppercase + string.digits
        loc = f"SW-{''.join(random.choices(chars, k=6))}"
        
        return cls.create(
            localizador=loc,
            perfil=perfil,
            precio_base=precio_base,
            iva=iva,
            precio_total=total,
            seccion=seccion_id
        )