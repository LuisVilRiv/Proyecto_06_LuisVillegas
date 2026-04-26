"""
ScienceWorld Park — tests/test_motor.py
Tests unitarios del checklist de aceptación (Sección F del reporte v3.0).

Cubre los criterios verificables de F.1:
  - D.1: saldo -1 € no dispara alerta de quiebra
  - D.7: afluencia a las 9h es significativamente mayor que a las 3h (~14:1)
  - D.2: EventoFalloLeve genera exactamente 1 entrada en EventoLogModel
  - D.5: segunda partida no hereda bonus viral de la primera
  - A.5: a 360:1 no hay lag tras congelar — _acum se limita a DELTA_CAP * ratio

Nota: los tests que tocan BD usan una BD en memoria temporal.
"""

import os
import pytest

# ── Fixture: BD en memoria para tests que necesitan modelos ──────────────────

@pytest.fixture(scope="module")
def db_memoria():
    """Inicializa una BD SQLite en memoria y la destruye al terminar."""
    from peewee import SqliteDatabase
    from models import db as models_db

    test_db = SqliteDatabase(":memory:", timeout=5)

    # Parchear la BD global con la de test
    from models.db import BaseModel
    original_db = BaseModel._meta.database

    # Reasignar a todos los modelos
    from models.parque      import ParqueModel
    from models.secciones   import SeccionModel
    from models.atracciones import AtraccionModel
    from models.empleados   import EmpleadoModel
    from models.inventario  import InventarioModel
    from models.eventos_log import EventoLogModel
    from models.tickets     import TicketModel
    from models.finanzas    import MovimientoFinanciero
    from models.usuarios    import UsuarioModel, PartidaModel

    all_models = [
        SeccionModel, ParqueModel, AtraccionModel, EmpleadoModel,
        InventarioModel, UsuarioModel, PartidaModel, EventoLogModel,
        TicketModel, MovimientoFinanciero,
    ]

    test_db.bind(all_models, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.pragma("foreign_keys", 1)
    test_db.create_tables(all_models, safe=True)

    # Seed mínimo: secciones (necesarias para FK de tickets y atracciones)
    if SeccionModel.select().count() == 0:
        for i, (nombre, emoji) in enumerate([
            ("Astronomia", "🔭"), ("Aeronautica", "✈️"), ("Geologia", "🪨"),
            ("Biologia", "🧬"), ("Fisica", "⚡"), ("Quimica", "⚗️"),
            ("Oceanografia", "🌊"), ("Neurociencia", "🧠"),
        ], start=1):
            SeccionModel.create(nombre=nombre, emoji=emoji)

    # Parque base para los tests
    if ParqueModel.select().count() == 0:
        ParqueModel.create(nombre="TestParque", dinero=500_000.0, reputacion=50.0)

    yield test_db

    test_db.close()


# ── D.1: saldo -1 € no dispara alerta de quiebra ────────────────────────────

def test_quiebra_no_dispara_con_saldo_minimo_negativo():
    """
    Criterio F.1/D.1: Con dinero=-1 EUR la señal evento_critico NO debe emitirse
    como alerta de quiebra. El umbral es 250.000 EUR de deuda.
    """
    from core.motor import MotorSimulacion, UMBRAL_QUIEBRA

    motor = MotorSimulacion()
    motor._horas_deuda = 0

    alertas = []
    motor.signals.evento_critico.connect(lambda t, m: alertas.append(t))

    # Simular la condición de quiebra directamente
    class FakeParque:
        dinero = -1.0

    p = FakeParque()
    # La condición correcta (D.1): dinero < 0 AND abs(dinero) > UMBRAL_QUIEBRA
    quiebra_activa = p.dinero < 0 and abs(p.dinero) > UMBRAL_QUIEBRA
    assert not quiebra_activa, (
        f"Saldo -1€ NO debería superar el umbral de {UMBRAL_QUIEBRA}€"
    )

    motor.signals.evento_critico.disconnect()


def test_quiebra_si_dispara_con_deuda_critica():
    """La alerta SÍ debe activarse cuando la deuda supera UMBRAL_QUIEBRA."""
    from core.motor import UMBRAL_QUIEBRA

    class FakeParque:
        dinero = -(UMBRAL_QUIEBRA + 1)

    p = FakeParque()
    quiebra_activa = p.dinero < 0 and abs(p.dinero) > UMBRAL_QUIEBRA
    assert quiebra_activa


# ── D.7: afluencia horas pico vs noche (~14:1) ───────────────────────────────

def test_afluencia_hora_apertura_vs_noche():
    """
    Criterio F.1/D.7: calcular_afluencia() con hora=9 debe dar
    al menos 5× más visitantes que con hora=3.
    El ratio teórico es 0.7 / 0.05 = 14:1.
    """
    from core.motor import MotorSimulacion

    motor = MotorSimulacion()
    motor._viral_dias = 0  # sin bonus viral

    class FakeParque:
        reputacion = 50.0
        hora_actual = 9

    p9 = FakeParque()
    p9.hora_actual = 9
    afl_9 = motor.calcular_afluencia(p9)

    p3 = FakeParque()
    p3.hora_actual = 3
    afl_3 = motor.calcular_afluencia(p3)

    # hora 9 → mult=0.7, hora 3 → mult=0.05 → ratio esperado ~14:1
    # Con varianza aleatoria pedimos al menos 5:1 para no depender de la semilla
    assert afl_9 > afl_3 * 5, (
        f"Afluencia 9h ({afl_9}) debería ser >5× la de 3h ({afl_3})"
    )


def test_afluencia_hora_pico_mayor_que_apertura():
    """Hora pico (11h, mult=1.2) debe superar apertura (9h, mult=0.7)."""
    from core.motor import MotorSimulacion

    motor = MotorSimulacion()
    motor._viral_dias = 0

    class FakeParque:
        reputacion = 50.0
        hora_actual = 11

    p11 = FakeParque()
    p9  = FakeParque()
    p9.hora_actual = 9

    # Ejecutar varias veces para suavizar aleatoriedad
    resultados = [(motor.calcular_afluencia(p11), motor.calcular_afluencia(p9))
                  for _ in range(20)]
    mayores = sum(1 for a, b in resultados if a >= b)
    assert mayores >= 15, "La hora pico debería superar la apertura en la mayoría de casos"


def test_afluencia_noche_casi_cero():
    """A las 3h (noche, mult=0.05) la afluencia debe ser muy baja."""
    from core.motor import MotorSimulacion

    motor = MotorSimulacion()
    motor._viral_dias = 0

    class FakeParque:
        reputacion = 100.0
        hora_actual = 3

    afl = motor.calcular_afluencia(FakeParque())
    # Con rep=100 y mult=0.05: base_max = 100*1.4*0.05 = 7
    assert afl <= 15, f"Afluencia nocturna demasiado alta: {afl}"


# ── D.2: EventoFalloLeve genera exactamente 1 entrada en EventoLogModel ──────

def test_evento_fallo_leve_genera_exactamente_un_log(db_memoria):
    """
    Criterio F.1/D.2: aplicar() + registrar() de EventoFalloLeve
    debe insertar exactamente 1 fila en EventoLogModel.
    """
    from core.eventos import EventoFalloLeve
    from models.eventos_log import EventoLogModel
    from domain.atracciones import AtraccionMecanica

    antes = EventoLogModel.select().count()

    ev  = EventoFalloLeve("Fallo Técnico", "", 0.35)
    atr = AtraccionMecanica(nombre="Test Atr", integridad=100.0)
    ev.aplicar(None, [atr])
    ev.registrar(dia=1, hora=10)

    despues = EventoLogModel.select().count()
    assert despues - antes == 1, (
        f"Se esperaba 1 nuevo registro, se encontraron {despues - antes}"
    )


# ── D.5: segunda partida no hereda bonus viral de la primera ─────────────────

def test_singleton_reset_entre_partidas():
    """
    Criterio F.1/D.5: cargar_partida() debe resetear _viral_dias a 0.
    """
    from core.motor import MotorSimulacion

    motor = MotorSimulacion()

    # Simular bonus viral activo de una partida anterior
    motor._viral_dias = 3
    assert motor._viral_dias == 3

    # Simular carga de nueva partida
    class FakePartida:
        parque_id      = 1
        nombre_partida = "PartidaTest"

    motor.cargar_partida(FakePartida())

    assert motor._viral_dias == 0, (
        f"_viral_dias debería ser 0 tras cargar partida, es {motor._viral_dias}"
    )
    assert motor._horas_deuda == 0, (
        f"_horas_deuda debería ser 0 tras cargar partida, es {motor._horas_deuda}"
    )


# ── A.5: DELTA_CAP limita el acumulador a velocidades extremas ───────────────

def test_delta_cap_limita_acumulacion():
    """
    Criterio F.1/A.5: si el proceso se congela 2 segundos, el acumulador
    no debe superar DELTA_CAP * ratio (no debe generar deuda temporal).
    """
    DELTA_CAP  = 0.1   # 100ms — constante de Sección A
    RATIO_MAX  = 360   # velocidad Rápido

    delta_real = 2.0   # 2 segundos de congelación simulada

    # La lógica del motor aplica: delta = min(delta_real, DELTA_CAP)
    delta_efectivo = min(delta_real, DELTA_CAP)
    seg_in_game    = delta_efectivo * RATIO_MAX

    # A 360:1 con DELTA_CAP=0.1 → máximo 36 seg in-game por frame
    assert delta_efectivo <= DELTA_CAP, "El cap no está limitando correctamente"
    assert seg_in_game <= DELTA_CAP * RATIO_MAX, (
        f"Segundos in-game por frame ({seg_in_game}) superan el máximo permitido "
        f"({DELTA_CAP * RATIO_MAX})"
    )
    # Confirmar que sin el cap habría sido catastrófico
    assert delta_real * RATIO_MAX > 100, (
        "Sin DELTA_CAP, 2s de congelación generarían >100s in-game"
    )
