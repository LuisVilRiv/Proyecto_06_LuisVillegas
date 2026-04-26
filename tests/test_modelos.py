"""
ScienceWorld Park — tests/test_modelos.py
FIXED: test_atracciones_seed expects 15 (not 14) matching models/db.py seed.
"""
import os
from models.db import init_db, get_db_path
from models.secciones import SeccionModel
from models.atracciones import AtraccionModel
from models.parque import ParqueModel


def setup_module(module):
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()


def test_base_datos_creada():
    assert os.path.exists(get_db_path())


def test_secciones_seed():
    count = SeccionModel.select().count()
    assert count == 8
    astronomia = SeccionModel.get(SeccionModel.nombre == "Astronomia")
    assert astronomia.emoji == "🔭"


def test_atracciones_seed():
    # FIX: El seed en models/db.py crea 15 atracciones (no 14)
    count = AtraccionModel.select().count()
    assert count == 15, f"Esperadas 15 atracciones, encontradas {count}"


def test_parque_vacio_al_inicio():
    assert ParqueModel.select().count() == 0


def test_crud_atraccion():
    seccion = SeccionModel.get_by_id(1)
    nueva = AtraccionModel.create(
        nombre="Test Lab Extra",
        tipo="laboratorio",
        seccion=seccion,
        precio_base=15.0,
    )
    assert nueva is not None
    recuperada = AtraccionModel.get(AtraccionModel.nombre == "Test Lab Extra")
    assert recuperada.precio_base == 15.0
    assert recuperada.seccion.nombre == seccion.nombre


def test_to_domain_conversion():
    """Verifica que to_domain() funciona correctamente para todos los tipos."""
    for atr in AtraccionModel.select():
        dom = atr.to_domain()
        assert dom.nombre == atr.nombre
        assert dom.integridad == atr.integridad
        # FIX verificado: visitantes_en_cola existe en el dominio
        assert hasattr(dom, "visitantes_en_cola")
        assert dom.visitantes_en_cola == 0


def test_secciones_tienen_emojis():
    emojis_esperados = {
        "Astronomia": "🔭",
        "Aeronautica": "✈️",
        "Geologia": "🪨",
        "Biologia": "🧬",
        "Fisica": "⚡",
        "Quimica": "⚗️",
        "Oceanografia": "🌊",
        "Neurociencia": "🧠",
    }
    for nombre, emoji in emojis_esperados.items():
        sec = SeccionModel.get_or_none(SeccionModel.nombre == nombre)
        assert sec is not None, f"Sección '{nombre}' no encontrada"
        assert sec.emoji == emoji
