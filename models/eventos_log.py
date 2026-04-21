from peewee import CharField, TextField, IntegerField, DateTimeField
from models.db import BaseModel

class EventoLogModel(BaseModel):
    """Historial de incidencias y eventos del motor del juego."""
    tipo = CharField()
    descripcion = TextField()
    dia_juego = IntegerField()
    hora_juego = IntegerField()
    timestamp = DateTimeField()

    class Meta:
        table_name = 'eventos_log'