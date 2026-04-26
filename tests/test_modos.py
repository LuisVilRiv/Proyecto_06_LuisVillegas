"""
ScienceWorld Park — tests/test_modos.py
Tests unitarios para seed_modo_campana() y seed_modo_extremo() (Sección G).

Verifican que los seeds aplican correctamente las condiciones iniciales
descritas en el PDF §G.1 y §G.2.
"""

import pytest


@pytest.fixture(scope="module")
def db_modos():
    """BD en memoria con seed completo para tests de modos."""
    from peewee import SqliteDatabase
    from models.parque      import ParqueModel
    from models.secciones   import SeccionModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    test_db = SqliteDatabase(":memory:", timeout=5)
    all_models = [ParqueModel, SeccionModel, AtraccionModel,
                  EmpleadoModel, InventarioModel]
    test_db.bind(all_models, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(all_models, safe=True)

    # Seed mínimo
    for nombre, emoji in [
        ("Astronomia","🔭"),("Aeronautica","✈️"),("Geologia","🪨"),
        ("Biologia","🧬"),("Fisica","⚡"),("Quimica","⚗️"),
        ("Oceanografia","🌊"),("Neurociencia","🧠"),
    ]:
        SeccionModel.create(nombre=nombre, emoji=emoji)

    for nombre, tipo, sec_id in [
        ("Lanzadera Estelar","simulador",1), ("Tunel Big Bang","interactiva",1),
        ("Planetario","simulador",1), ("Simulador Piloto","simulador",2),
        ("Tunel Viento","interactiva",2), ("Viaje al Centro","mecanica",3),
        ("Simulador Sismico","mecanica",3), ("Biomas","interactiva",4),
        ("Montana ADN","extreme",4), ("Sala del Rayo","interactiva",5),
        ("Montana Reaccion","extreme",6), ("Submarino","simulador",7),
        ("ROVs","laboratorio",7), ("Cerebro","interactiva",8),
        ("Capsula","simulador",8),
    ]:
        AtraccionModel.create(nombre=nombre, tipo=tipo, seccion=sec_id,
                              integridad=100.0, activo=True)

    for i in range(8):
        EmpleadoModel.create(nombre=f"Empleado{i}", tipo="tecnico",
                             salario_mes=2500.0, activo=True)

    for nombre, cat, stock, minimo, maximo, precio in [
        ("Comida Espacial","Comida",200,20,500,5.0),
        ("Newton Peluche","Souvenir",150,15,300,10.0),
        ("Kit ADN Junior","Souvenir",50,10,150,8.0),
        ("Cristal Mineral","Souvenir",80,10,200,3.0),
    ]:
        InventarioModel.create(nombre=nombre, categoria=cat,
                               stock_actual=stock, stock_minimo=minimo,
                               stock_maximo=maximo, precio_compra=precio)

    parque = ParqueModel.create(nombre="TestModos", dinero=2_000_000.0, reputacion=50.0)

    yield {"db": test_db, "parque_id": parque.id}
    test_db.close()


# ── Modo Campaña ──────────────────────────────────────────────────────────────

def test_seed_campana_normal(db_modos):
    """Modo Campaña Normal: 500k€, rep=35, 3 atracciones, 4 empleados, stock 50%."""
    from models.db import seed_modo_campana
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    pid = db_modos["parque_id"]
    seed_modo_campana(pid, "normal")

    p = ParqueModel.get_by_id(pid)
    assert p.dinero     == 500_000
    assert p.reputacion == 35

    activas = AtraccionModel.select().where(AtraccionModel.activo == True).count()
    assert activas == 3

    activos = EmpleadoModel.select().where(EmpleadoModel.activo == True).count()
    assert activos == 4

    # Stock ~50% del máximo
    for inv in InventarioModel.select():
        esperado = round(inv.stock_maximo * 0.50)
        assert inv.stock_actual == esperado, (
            f"{inv.nombre}: stock={inv.stock_actual}, esperado≈{esperado}"
        )


def test_seed_campana_facil(db_modos):
    """Modo Campaña Fácil: 750k€, rep=50, 5 atracciones, 8 empleados, stock 80%."""
    from models.db import seed_modo_campana
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel

    pid = db_modos["parque_id"]
    seed_modo_campana(pid, "facil")

    p = ParqueModel.get_by_id(pid)
    assert p.dinero     == 750_000
    assert p.reputacion == 50

    activas = AtraccionModel.select().where(AtraccionModel.activo == True).count()
    assert activas == 5

    activos = EmpleadoModel.select().where(EmpleadoModel.activo == True).count()
    assert activos == 8


def test_seed_campana_pesadilla(db_modos):
    """Modo Pesadilla: 100k€, rep=10, 0 atracciones, 0 empleados, stock vacío."""
    from models.db import seed_modo_campana
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    pid = db_modos["parque_id"]
    seed_modo_campana(pid, "pesadilla")

    p = ParqueModel.get_by_id(pid)
    assert p.dinero     == 100_000
    assert p.reputacion == 10

    activas = AtraccionModel.select().where(AtraccionModel.activo == True).count()
    assert activas == 0

    activos = EmpleadoModel.select().where(EmpleadoModel.activo == True).count()
    assert activos == 0

    for inv in InventarioModel.select():
        assert inv.stock_actual == 0


# ── Modo Extremo ──────────────────────────────────────────────────────────────

def test_seed_extremo_condiciones_iniciales(db_modos):
    """
    Modo Extremo: saldo -180k€, rep=8, 12/15 atracciones averiadas,
    3 empleados, inventario vacío.
    """
    from models.db import seed_modo_extremo
    from models.parque      import ParqueModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel

    pid = db_modos["parque_id"]
    seed_modo_extremo(pid)

    p = ParqueModel.get_by_id(pid)
    assert p.dinero     == -180_000
    assert p.reputacion == 8

    # 12 de 15 en mantenimiento
    en_mantenimiento = AtraccionModel.select().where(
        AtraccionModel.en_mantenimiento == True
    ).count()
    assert en_mantenimiento == 12

    # Las averiadas tienen integridad entre 5% y 30%
    for atr in AtraccionModel.select().where(AtraccionModel.en_mantenimiento == True):
        assert 5.0 <= atr.integridad <= 30.0, (
            f"{atr.nombre}: integridad={atr.integridad:.1f}% fuera de rango 5-30%"
        )

    # 3 empleados activos
    activos = EmpleadoModel.select().where(EmpleadoModel.activo == True).count()
    assert activos == 3

    # Inventario vacío
    for inv in InventarioModel.select():
        assert inv.stock_actual == 0, f"{inv.nombre} tiene stock={inv.stock_actual}"
