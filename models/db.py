"""
ScienceWorld Park — models/db.py
Conexión SQLite + creación de tablas + seed inicial + seeds de modos de juego.

Correcciones aplicadas (v3.0):
 - B.2b: timeout=30 en SqliteDatabase
 - G.1/G.2: seed_modo_campana(dificultad) y seed_modo_extremo() añadidas.
             Se llaman desde LoginWindow antes de MotorSimulacion().cargar_partida().

Correcciones aplicadas (v3.1):
 - MIGRACIÓN: _migrate() añade columnas ausentes en tablas existentes
   (modo, dificultad_key en 'partidas') sin necesidad de borrar la BD.
"""

import os
import sys
from peewee import SqliteDatabase, Model
from core.logger import log


def get_db_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "scienceworld.db")


# B.2b: timeout=30 — evita OperationalError 'database is locked' en acceso concurrente
db = SqliteDatabase(None, timeout=30)


class BaseModel(Model):
    class Meta:
        database = db


# ────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    from models.parque      import ParqueModel
    from models.secciones   import SeccionModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel
    from models.usuarios    import UsuarioModel, PartidaModel
    from models.eventos_log import EventoLogModel
    from models.tickets     import TicketModel
    from models.finanzas    import MovimientoFinanciero

    db.init(get_db_path())
    db.connect(reuse_if_open=True)
    db.pragma("journal_mode", "wal")
    db.pragma("foreign_keys", 1)

    db.create_tables(
        [
            SeccionModel, ParqueModel, AtraccionModel, EmpleadoModel,
            InventarioModel, UsuarioModel, PartidaModel, EventoLogModel,
            TicketModel, MovimientoFinanciero,
        ],
        safe=True,
    )

    # Aplicar migraciones de esquema antes de usar los modelos
    _migrate()
    _seed()


# ────────────────────────────────────────────────────────────────────────────
def _migrate() -> None:
    """
    Añade columnas que pueden faltar en bases de datos creadas con versiones
    anteriores del código. Usa ALTER TABLE … ADD COLUMN que SQLite ignora si
    la columna ya existe (gracias al bloque try/except por columna).

    Añadir aquí cualquier migración futura siguiendo el mismo patrón.
    """
    migraciones = [
        # tabla           columna           definición SQL
        ("partidas", "modo",           "TEXT NOT NULL DEFAULT 'campana'"),
        ("partidas", "dificultad_key", "TEXT NOT NULL DEFAULT 'normal'"),
    ]

    for tabla, columna, definicion in migraciones:
        try:
            db.execute_sql(
                f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion};"
            )
            log.info(f"Migración: columna '{columna}' añadida a '{tabla}'.")
        except Exception:
            # La columna ya existe — ignorar silenciosamente
            pass


# ────────────────────────────────────────────────────────────────────────────
def _seed() -> None:
    """Pobla la BD con datos de referencia si está vacía."""
    from models.secciones   import SeccionModel
    from models.atracciones import AtraccionModel
    from models.inventario  import InventarioModel

    if SeccionModel.select().count() == 0:
        secciones = [
            ("Astronomia",   "🔭"), ("Aeronautica",  "✈️"),
            ("Geologia",     "🪨"), ("Biologia",     "🧬"),
            ("Fisica",       "⚡"), ("Quimica",      "⚗️"),
            ("Oceanografia", "🌊"), ("Neurociencia", "🧠"),
        ]
        for nombre, emoji in secciones:
            SeccionModel.create(nombre=nombre, emoji=emoji)
        log.info("Seed: 8 secciones científicas inicializadas.")

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


# ── Sección G: Modos de juego ────────────────────────────────────────────────

# G.1 — Configuración por dificultad (Modo Campaña)
DIFICULTAD_CONFIG: dict[str, dict] = {
    "facil": {
        "dinero": 750_000, "reputacion": 50,
        "atracciones": 5,  "empleados": 8,
        "umbral_quiebra": 150_000,
        "objetivo_rep": 80, "objetivo_dinero": 1_000_000,
        "prob_eventos_negativo": 0.5,
    },
    "normal": {
        "dinero": 500_000, "reputacion": 35,
        "atracciones": 3,  "empleados": 4,
        "umbral_quiebra": 250_000,
        "objetivo_rep": 85, "objetivo_dinero": 2_000_000,
        "prob_eventos_negativo": 1.0,
    },
    "dificil": {
        "dinero": 250_000, "reputacion": 20,
        "atracciones": 1,  "empleados": 2,
        "umbral_quiebra": 400_000,
        "objetivo_rep": 90, "objetivo_dinero": 3_000_000,
        "prob_eventos_negativo": 1.25,
    },
    "pesadilla": {
        "dinero": 100_000, "reputacion": 10,
        "atracciones": 0,  "empleados": 0,
        "umbral_quiebra": 550_000,
        "objetivo_rep": 95, "objetivo_dinero": 5_000_000,
        "prob_eventos_negativo": 1.5,
    },
}


def seed_modo_campana(parque_id: int, dificultad: str = "normal") -> None:
    """
    G.1: configura el parque para Modo Campaña con la dificultad indicada.
    Llamar ANTES de MotorSimulacion().cargar_partida().
    """
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    cfg = DIFICULTAD_CONFIG.get(dificultad, DIFICULTAD_CONFIG["normal"])

    with db.atomic():
        parque = ParqueModel.get_by_id(parque_id)
        parque.dinero     = cfg["dinero"]
        parque.reputacion = cfg["reputacion"]
        parque.dia_actual  = 1
        parque.hora_actual = 8
        parque.save()

        for i, atr in enumerate(AtraccionModel.select()):
            atr.activo          = (i < cfg["atracciones"])
            atr.en_mantenimiento = False
            atr.integridad      = 100.0
            atr.save()

        for i, emp in enumerate(EmpleadoModel.select()):
            emp.activo = (i < cfg["empleados"])
            emp.save()

        stock_pct = {
            "facil": 0.80, "normal": 0.50,
            "dificil": 0.25, "pesadilla": 0.0,
        }.get(dificultad, 0.50)

        for inv in InventarioModel.select():
            inv.stock_actual = round(inv.stock_maximo * stock_pct)
            inv.save()

    log.info(
        f"Seed Modo Campaña [{dificultad.upper()}]: "
        f"dinero={cfg['dinero']:,}€, rep={cfg['reputacion']}, "
        f"atracciones={cfg['atracciones']}, empleados={cfg['empleados']}"
    )


def seed_modo_extremo(parque_id: int) -> None:
    """
    G.2: configura el parque para Modo Extremo (rescate en bancarrota).
    """
    import random
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    with db.atomic():
        parque = ParqueModel.get_by_id(parque_id)
        parque.dinero     = -180_000
        parque.reputacion = 8
        parque.dia_actual  = 1
        parque.hora_actual = 8
        parque.save()

        atracciones = list(AtraccionModel.select())
        for i, atr in enumerate(atracciones):
            if i < 3:
                atr.activo           = True
                atr.en_mantenimiento = False
                atr.integridad       = 100.0
            else:
                atr.activo           = True
                atr.en_mantenimiento = True
                atr.integridad       = random.uniform(5.0, 30.0)
            atr.save()

        for i, emp in enumerate(EmpleadoModel.select()):
            emp.activo = (i < 3)
            emp.save()

        for inv in InventarioModel.select():
            inv.stock_actual = 0
            inv.save()

    log.info(
        "Seed Modo Extremo: dinero=-180.000€, rep=8, "
        "12/15 atracciones averiadas, stock=0"
    )
