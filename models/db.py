"""
ScienceWorld Park — models/db.py
Conexión SQLite + creación de tablas + seed inicial + modos de juego.
"""

import os
import sys
import random
from peewee import SqliteDatabase, Model
from core.logger import log

# ─────────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────────

db = SqliteDatabase(None, timeout=30)


class BaseModel(Model):
    class Meta:
        database = db


def get_db_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "scienceworld.db")


# ─────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────

def init_db() -> None:
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

    db.create_tables([
        SeccionModel, ParqueModel, AtraccionModel, EmpleadoModel,
        InventarioModel, UsuarioModel, PartidaModel, EventoLogModel,
        TicketModel, MovimientoFinanciero
    ], safe=True)

    _migrate()
    _seed()


# ─────────────────────────────────────────────────────────────
# MIGRACIONES
# ─────────────────────────────────────────────────────────────

def _migrate() -> None:
    migraciones = [
        ("partidas", "modo", "TEXT NOT NULL DEFAULT 'campana'"),
        ("partidas", "dificultad_key", "TEXT NOT NULL DEFAULT 'normal'"),
        ("atracciones", "construida", "INTEGER NOT NULL DEFAULT 0"),
        ("atracciones", "en_construccion", "INTEGER NOT NULL DEFAULT 0"),
        ("atracciones", "dias_construccion_restantes", "INTEGER NOT NULL DEFAULT 0"),
        ("atracciones", "prioridad_construccion", "TEXT NOT NULL DEFAULT 'media'"),
    ]

    for tabla, columna, definicion in migraciones:
        try:
            db.execute_sql(
                f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion};"
            )
            log.info(f"Migración: {columna} añadida a {tabla}")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# SEED BASE
# ─────────────────────────────────────────────────────────────

def _seed() -> None:
    from models.secciones import SeccionModel
    from models.atracciones import AtraccionModel
    from models.inventario import InventarioModel
    from models.empleados import EmpleadoModel

    # ── Secciones ──
    if SeccionModel.select().count() == 0:
        secciones = [
            ("Astronomia", "🔭"), ("Aeronautica", "✈️"),
            ("Geologia", "🪨"), ("Biologia", "🧬"),
            ("Fisica", "⚡"), ("Quimica", "⚗️"),
            ("Oceanografia", "🌊"), ("Neurociencia", "🧠"),
        ]
        for n, e in secciones:
            SeccionModel.create(nombre=n, emoji=e)
        log.info("Seed: Secciones inicializadas")

    # ── Atracciones ──
    atracciones = [
        ("Lanzadera Estelar", "simulador", 1, 8, 12, 130, 8.0),
        ("Tunel del Big Bang", "interactiva", 1, 40, 8, 0, 4.0),
        ("Planetario Digital", "simulador", 1, 120, 30, 0, 5.0),
        ("Simulador de Piloto", "simulador", 2, 2, 15, 130, 9.0),
        ("Tunel de Viento Interactivo", "interactiva", 2, 4, 10, 120, 3.0),
        ("Viaje al Centro de la Tierra", "mecanica", 3, 30, 18, 0, 6.0),
        ("Simulador Sismico", "mecanica", 3, 12, 6, 120, 4.0),
        ("Biomas Vivientes", "interactiva", 4, 60, 45, 0, 5.0),
        ("Montana Rusa del ADN", "extreme", 4, 16, 4, 140, 7.0),
        ("Sala del Rayo", "interactiva", 5, 25, 10, 110, 4.0),
        ("La Montana de la Reaccion", "extreme", 6, 16, 4, 140, 7.5),
        ("Submarino Profundo", "simulador", 7, 8, 15, 120, 9.0),
        ("ROVs Programables", "laboratorio", 7, 6, 20, 0, 6.0),
        ("Cerebro Gigante Transitable", "interactiva", 8, 20, 25, 0, 5.0),
        ("Capsula de Sueno Lucido", "simulador", 8, 1, 30, 150, 12.0),
    ]

    nuevas_atracciones = 0
    for n, t, s, c, d, h, p in atracciones:
        _, created = AtraccionModel.get_or_create(
            nombre=n,
            defaults={
                "tipo": t,
                "seccion": s,
                "capacidad_max": c,
                "duracion_min": d,
                "altura_minima_cm": h,
                "precio_base": p,
                "construida": False,
                "activo": False,
            },
        )
        if created:
            nuevas_atracciones += 1
    if nuevas_atracciones:
        log.info(f"Seed: {nuevas_atracciones} atracciones añadidas")

    # ── Inventario ──
    productos = [
        ("Comida Espacial", "Comida", 200, 20, 500, 5.0),
        ("Bebida Isotonica Lab", "Comida", 220, 25, 550, 2.5),
        ("Snack Proteico Orbital", "Comida", 180, 20, 450, 3.2),
        ("Camiseta ScienceWorld", "Souvenir", 120, 20, 350, 9.5),
        ("Newton Peluche", "Souvenir", 150, 15, 300, 10.0),
        ("Kit ADN Junior", "Souvenir", 50, 10, 150, 8.0),
        ("Poster Sistema Solar", "Souvenir", 160, 20, 400, 2.0),
        ("Cristal Mineral", "Souvenir", 80, 10, 200, 3.0),
        ("Pack Pilas Sensores", "Repuesto", 100, 20, 300, 4.0),
        ("Lubricante Industrial", "Repuesto", 70, 15, 220, 6.5),
        ("Fuse de Seguridad", "Repuesto", 200, 40, 500, 1.0),
        ("Panel Holografico", "Repuesto", 20, 5, 60, 45.0),
    ]

    nuevos_productos = 0
    for n, c, s, min_s, max_s, p in productos:
        _, created = InventarioModel.get_or_create(
            nombre=n,
            defaults={
                "categoria": c,
                "stock_actual": s,
                "stock_minimo": min_s,
                "stock_maximo": max_s,
                "precio_compra": p,
            },
        )
        if created:
            nuevos_productos += 1
    if nuevos_productos:
        log.info(f"Seed: {nuevos_productos} productos de inventario añadidos")

    # ── EMPLEADOS (POOL GLOBAL) ──
    if EmpleadoModel.select().count() == 0:
        pool = [
            ("Dr. Aris Tóteles", "cientifico", 3500),
            ("Ada Lovelace", "tecnico", 3200),
            ("Nikola Tesla", "tecnico", 3000),
            ("Marie Curie", "cientifico", 3800),
            ("Carl Sagan", "divulgador", 2800),
            ("Isaac Newton", "hosteleria", 2500),
            ("Neil Armstrong", "tecnico", 3100),
            ("Hedy Lamarr", "tecnico", 3300),
            ("Jane Goodall", "cientifico", 3400),
            ("Neil deGrasse", "divulgador", 2900),
        ]

        for n, t, s in pool:
            EmpleadoModel.create(
                nombre=n,
                tipo=t,
                salario_mes=s,
                activo=False
            )

        log.info("Seed: Pool de empleados creado")


# ─────────────────────────────────────────────────────────────
# DIFICULTADES
# ─────────────────────────────────────────────────────────────

DIFICULTAD_CONFIG = {
    "facil": {
        "dinero": 750000,
        "reputacion": 50,
        "atracciones": 5,
        "empleados": 8,
    },
    "normal": {
        "dinero": 500000,
        "reputacion": 35,
        "atracciones": 3,
        "empleados": 4,
    },
    "dificil": {
        "dinero": 250000,
        "reputacion": 20,
        "atracciones": 1,
        "empleados": 2,
    },
    "pesadilla": {
        "dinero": 100000,
        "reputacion": 10,
        "atracciones": 0,
        "empleados": 0,
    },
}


# ─────────────────────────────────────────────────────────────
# MODO CAMPAÑA
# ─────────────────────────────────────────────────────────────

def seed_modo_campana(parque_id: int, dificultad: str = "normal") -> None:
    from models.parque import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados import EmpleadoModel

    cfg = DIFICULTAD_CONFIG.get(dificultad, DIFICULTAD_CONFIG["normal"])

    with db.atomic():
        parque = ParqueModel.get_by_id(parque_id)
        parque.dinero = cfg["dinero"]
        parque.reputacion = cfg["reputacion"]
        parque.dia_actual = 1
        parque.hora_actual = 8
        parque.save()

        # Atracciones
        for i, atr in enumerate(AtraccionModel.select()):
            atr.construida = i < cfg["atracciones"]
            atr.activo = i < cfg["atracciones"]
            atr.en_mantenimiento = False
            atr.integridad = 100.0
            atr.en_construccion = False
            atr.dias_construccion_restantes = 0
            atr.save()

        # EMPLEADOS: asegurar plantilla inicial exacta según dificultad
        EmpleadoModel.update(activo=False).execute()

        empleados = (
            EmpleadoModel
            .select()
            .order_by(EmpleadoModel.id)
            .limit(cfg["empleados"])
        )

        for i, emp in enumerate(empleados):
            emp.activo = True
            # Asignación mínima para que empiecen operativos por sección
            emp.seccion = (i % 8) + 1
            emp.save()

    log.info(
        f"Dificultad {dificultad.upper()}: "
        f"{cfg['empleados']} empleados activos"
    )


# ─────────────────────────────────────────────────────────────
# MODO EXTREMO
# ─────────────────────────────────────────────────────────────

def seed_modo_extremo(parque_id: int) -> None:
    from models.parque import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados import EmpleadoModel

    with db.atomic():
        p = ParqueModel.get_by_id(parque_id)
        p.dinero = -180000
        p.reputacion = 8
        p.save()

        AtraccionModel.update(
            construida=True,
            activo=True,
            integridad=25,
            en_mantenimiento=True,
            en_construccion=False,
            dias_construccion_restantes=0,
        ).execute()

        EmpleadoModel.update(activo=False).execute()

        for e in EmpleadoModel.select().limit(3):
            e.activo = True
            e.save()

    log.info("Seed modo extremo aplicado")