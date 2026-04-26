"""
ScienceWorld Park — models/usuarios.py

Correcciones aplicadas (v3.0):
 - G.4: PartidaModel añade columnas `modo` y `dificultad` para que el motor
         sepa qué umbrales aplicar al recargar una partida guardada.
"""

import datetime
import bcrypt
from peewee import CharField, DateTimeField, ForeignKeyField
from models.db import BaseModel, db
from models.parque import ParqueModel


class UsuarioModel(BaseModel):
    username   = CharField(unique=True, max_length=50)
    password_h = CharField()
    rol        = CharField(default="Manager")

    class Meta:
        table_name = "usuarios"

    @classmethod
    def crear_usuario(cls, username, password, rol="Manager"):
        salt    = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
        return cls.create(
            username=username,
            password_h=pw_hash.decode("utf-8"),
            rol=rol,
        )

    def verificar_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_h.encode("utf-8"),
        )


class PartidaModel(BaseModel):
    nombre_partida = CharField(max_length=100)
    fecha_creacion = DateTimeField(default=datetime.datetime.now)
    dificultad     = CharField(default="Normal")   # Fácil / Normal / Difícil / Pesadilla
    # G.4: modo y dificultad_key persisten para que el motor sepa qué config aplicar
    modo           = CharField(default="campana")   # 'campana' | 'extremo'
    dificultad_key = CharField(default="normal")    # clave de DIFICULTAD_CONFIG
    parque         = ForeignKeyField(ParqueModel, backref="partida", unique=True)

    class Meta:
        table_name = "partidas"


def inicializar_usuarios():
    if UsuarioModel.select().count() == 0:
        UsuarioModel.crear_usuario("admin", "science2026", "Admin")
        print("SISTEMA: Usuario 'admin' creado por defecto.")
