from peewee import CharField, BooleanField
from models.db import BaseModel

class SeccionModel(BaseModel):
    """Disciplinas científicas que dividen el parque."""
    nombre = CharField(unique=True)
    emoji = CharField()
    activa = BooleanField(default=True)

    class Meta:
        table_name = 'secciones'