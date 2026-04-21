import pytest
from core.motor import MotorSimulacion
from models.parque import ParqueModel
from core.eventos import EventoAveriaGrave
from domain.atracciones import AtraccionMecanica

@pytest.fixture
def motor():
    return MotorSimulacion()

def test_avanzar_hora(motor):
    motor.parque_db.hora_actual = 23
    motor.parque_db.dia_actual = 1
    motor.avanzar_hora()
    assert motor.parque_db.hora_actual == 0
    assert motor.parque_db.dia_actual == 2
    
    # Verificar persistencia
    db_p = ParqueModel.get_by_id(1)
    assert db_p.dia_actual == 2

def test_ciclo_24_ticks(motor):
    dia_inicial = motor.parque_db.dia_actual
    for _ in range(24):
        motor.ejecutar_tick()
    assert motor.parque_db.dia_actual == dia_inicial + 1

def test_evento_averia_grave():
    evento = EventoAveriaGrave("Test", "Test", 1.0)
    atr = AtraccionMecanica(nombre="Test Atr", integridad=100.0, en_mantenimiento=False)
    evento.aplicar(None, [atr])
    assert atr.integridad == 0.0
    assert atr.en_mantenimiento is True

def test_afluencia_no_negativa(motor):
    motor.parque_db.reputacion = 0.0
    afluencia = motor.calcular_afluencia()
    assert afluencia >= 0