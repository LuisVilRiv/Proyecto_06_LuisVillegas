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
    astronomia = SeccionModel.get(SeccionModel.nombre == 'Astronomia')
    assert astronomia.emoji == '🔭'

def test_atracciones_seed():
    count = AtraccionModel.select().count()
    assert count == 14

def test_parque_vacio_al_inicio():
    assert ParqueModel.select().count() == 0

def test_crud_atraccion():
    seccion = SeccionModel.get_by_id(1)
    nueva = AtraccionModel.create(
        nombre="Test Lab",
        tipo="laboratorio",
        seccion=seccion,
        precio_base=15.0
    )
    assert nueva is not None
    recuperada = AtraccionModel.get(AtraccionModel.nombre == "Test Lab")
    assert recuperada.precio_base == 15.0
    assert recuperada.seccion.nombre == seccion.nombre