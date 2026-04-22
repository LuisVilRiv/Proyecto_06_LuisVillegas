"""
ScienceWorld Park — models/db.py
Conexión SQLite + creación de tablas + seed inicial.
"""

import os
import sys
from peewee import SqliteDatabase, Model
from core.logger import log


def get_db_path() -> str:
    """Ruta portable del .db, compatible con PyInstaller frozen."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        # Durante desarrollo: raíz del proyecto (un nivel sobre /models)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "scienceworld.db")


db = SqliteDatabase(None)  # Se inicializa en init_db()


class BaseModel(Model):
    class Meta:
        database = db


# ────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """Inicializa la BD, crea tablas y ejecuta el seed si la BD es nueva."""
    from models.parque import ParqueModel
    from models.secciones import SeccionModel
    from models.atracciones import AtraccionModel
    from models.empleados import EmpleadoModel
    from models.inventario import InventarioModel
    from models.usuarios import UsuarioModel, PartidaModel
    from models.eventos_log import EventoLogModel
    from models.tickets import TicketModel
    from models.finanzas import MovimientoFinanciero

    db.init(get_db_path())
    db.connect(reuse_if_open=True)
    db.pragma("journal_mode", "wal")
    db.pragma("foreign_keys", 1)

    # Orden respetuoso con las FKs
    db.create_tables(
        [
            SeccionModel,
            ParqueModel,
            AtraccionModel,
            EmpleadoModel,
            InventarioModel,
            UsuarioModel,
            PartidaModel,
            EventoLogModel,
            TicketModel,
            MovimientoFinanciero,
        ],
        safe=True,
    )

    _seed(SeccionModel, AtraccionModel, InventarioModel)


# ────────────────────────────────────────────────────────────────────────────
def _seed(SeccionModel, AtraccionModel, InventarioModel) -> None:
    """Pobla la BD con datos de referencia si está vacía."""

    # Secciones (PDF §2)
    if SeccionModel.select().count() == 0:
        secciones = [
            ("Astronomia",   "🔭"),
            ("Aeronautica",  "✈️"),
            ("Geologia",     "🪨"),
            ("Biologia",     "🧬"),
            ("Fisica",       "⚡"),
            ("Quimica",      "⚗️"),
            ("Oceanografia", "🌊"),
            ("Neurociencia", "🧠"),
        ]
        for nombre, emoji in secciones:
            SeccionModel.create(nombre=nombre, emoji=emoji)
        log.info("Seed: 8 secciones científicas inicializadas.")

    # Atracciones (PDF §3 + schema.sql)
    if AtraccionModel.select().count() == 0:
        atracciones = [
            ("Lanzadera Estelar",    "simulador",   1,   8, 12,  8.0),
            ("Tunel del Big Bang",   "interactiva", 1,  40,  8,  4.0),
            ("Planetario Digital",   "simulador",   1, 120, 30,  5.0),
            ("Simulador de Piloto",  "simulador",   2,   2, 15,  9.0),
            ("Tunel de Viento",      "interactiva", 2,   4, 10,  3.0),
            ("Viaje al Centro",      "mecanica",    3,  30, 18,  6.0),
            ("Simulador Sismico",    "mecanica",    3,  12,  6,  4.0),
            ("Biomas Vivientes",     "interactiva", 4,  60, 45,  5.0),
            ("Montana ADN",          "extreme",     4,  16,  4,  7.0),
            ("Sala del Rayo",        "interactiva", 5,  25, 10,  4.0),
            ("La Montana Reaccion",  "extreme",     6,  16,  4,  7.0),
            ("Submarino Profundo",   "simulador",   7,   8, 15,  9.0),
            ("ROVs Programables",    "laboratorio", 7,   6, 20,  6.0),
            ("Cerebro Transitable",  "interactiva", 8,  20, 25,  5.0),
            ("Capsula Sueno Lucido", "simulador",   8,   1, 30, 12.0),
        ]
        for nombre, tipo, sec_id, cap, dur, precio in atracciones:
            AtraccionModel.create(
                nombre=nombre, tipo=tipo, seccion=sec_id,
                capacidad_max=cap, duracion_min=dur, precio_base=precio,
            )
        log.info("Seed: 15 atracciones científicas inicializadas.")

    # Inventario (ScienceFood + ScienceStore)
    if InventarioModel.select().count() == 0:
        productos = [
            ("Comida Espacial", "Comida",   200, 20, 500,  5.0),
            ("Newton Peluche",  "Souvenir", 150, 15, 300, 10.0),
            ("Kit ADN Junior",  "Souvenir",  50, 10, 150,  8.0),
            ("Cristal Mineral", "Souvenir",  80, 10, 200,  3.0),
        ]
        for nombre, cat, stock, minimo, maximo, precio in productos:
            InventarioModel.create(
                nombre=nombre, categoria=cat,
                stock_actual=stock, stock_minimo=minimo,
                stock_maximo=maximo, precio_compra=precio,
            )
        log.info("Seed: Productos de inventario inicializados.")
