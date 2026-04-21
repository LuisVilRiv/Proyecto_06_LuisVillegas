from peewee import SqliteDatabase, Model
import os

db = SqliteDatabase('scienceworld.db')

class BaseModel(Model):
    class Meta:
        database = db

def init_db():
    from models.parque import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados import EmpleadoModel
    from models.inventario import InventarioModel
    from models.usuarios import UsuarioModel, PartidaModel
    
    db.connect(reuse_if_open=True)
    # Creamos todas las tablas, incluidas las nuevas de usuarios y partidas
    db.create_tables([
        ParqueModel, 
        AtraccionModel, 
        EmpleadoModel, 
        InventarioModel, 
        UsuarioModel, 
        PartidaModel
    ])
