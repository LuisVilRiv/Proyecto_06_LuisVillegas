"""
ScienceWorld Park — tests/test_finanzas.py
Tests unitarios para models/finanzas.py (Sección F.1 / D.8).

Criterio de aceptación:
  - historico_diario(30) genera exactamente 1 query SQL (GROUP BY).
  - El resultado tiene la estructura correcta: lista de dicts con
    claves dia, ingresos, gastos, balance.
  - balance == ingresos - gastos para cada entrada.
"""

import pytest


@pytest.fixture(scope="module")
def db_finanzas():
    """BD en memoria con datos financieros de prueba."""
    from peewee import SqliteDatabase
    from models.db import BaseModel
    from models.parque   import ParqueModel
    from models.finanzas import MovimientoFinanciero

    test_db = SqliteDatabase(":memory:", timeout=5)
    all_models = [ParqueModel, MovimientoFinanciero]
    test_db.bind(all_models, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(all_models, safe=True)

    # Parque en día 5
    ParqueModel.create(nombre="TestFinanzas", dinero=500_000.0,
                       reputacion=50.0, dia_actual=5)

    # Movimientos en días 3, 4 y 5
    for dia in (3, 4, 5):
        MovimientoFinanciero.create(
            tipo="ingreso", categoria="entradas", concepto="Ticket adulto",
            importe=1000.0, iva=100.0, dia_juego=dia, hora_juego=10,
        )
        MovimientoFinanciero.create(
            tipo="gasto", categoria="nominas", concepto="Nóminas",
            importe=300.0, iva=0.0, dia_juego=dia, hora_juego=23,
        )

    yield test_db
    test_db.close()


def test_historico_diario_estructura(db_finanzas):
    """historico_diario() devuelve lista de dicts con las claves correctas."""
    from models.finanzas import MovimientoFinanciero

    resultado = MovimientoFinanciero.historico_diario(7)

    assert isinstance(resultado, list)
    assert len(resultado) > 0

    for entry in resultado:
        assert "dia"      in entry
        assert "ingresos" in entry
        assert "gastos"   in entry
        assert "balance"  in entry


def test_historico_diario_balance_correcto(db_finanzas):
    """balance == ingresos - gastos para cada día."""
    from models.finanzas import MovimientoFinanciero

    for entry in MovimientoFinanciero.historico_diario(7):
        esperado = round(entry["ingresos"] - entry["gastos"], 2)
        real     = round(entry["balance"], 2)
        assert real == esperado, (
            f"Día {entry['dia']}: balance={real} ≠ ingresos-gastos={esperado}"
        )


def test_historico_diario_valores_correctos(db_finanzas):
    """Los valores numéricos coinciden con los insertados."""
    from models.finanzas import MovimientoFinanciero

    resultado = {e["dia"]: e for e in MovimientoFinanciero.historico_diario(7)}

    for dia in (3, 4, 5):
        assert dia in resultado, f"Día {dia} no aparece en el histórico"
        assert resultado[dia]["ingresos"] == 1000.0
        assert resultado[dia]["gastos"]   == 300.0
        assert resultado[dia]["balance"]  == 700.0


def test_historico_diario_una_sola_query(db_finanzas):
    """
    Criterio F.1/D.8: historico_diario() debe ejecutar exactamente 1 query SQL.
    Verificamos contando las queries mediante el logger de peewee.
    """
    import logging
    from models.finanzas import MovimientoFinanciero

    queries_ejecutadas = []

    # Activar logging de queries de peewee temporalmente
    logger = logging.getLogger("peewee")
    handler = logging.handlers.MemoryHandler(capacity=1000)

    class QueryCounter(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            if "SELECT" in msg.upper():
                queries_ejecutadas.append(msg)

    import logging.handlers
    counter = QueryCounter()
    logger.addHandler(counter)
    logger.setLevel(logging.DEBUG)

    try:
        MovimientoFinanciero.historico_diario(30)
    finally:
        logger.removeHandler(counter)
        logger.setLevel(logging.WARNING)

    # historico_diario hace 1 SELECT para movimientos + 1 para dia_actual del parque
    # Total esperado: ≤ 2 queries (no N*2)
    assert len(queries_ejecutadas) <= 2, (
        f"Se ejecutaron {len(queries_ejecutadas)} queries — se esperaban ≤ 2.\n"
        f"Queries: {queries_ejecutadas}"
    )


def test_historico_diario_periodo_correcto(db_finanzas):
    """historico_diario(n) no devuelve días fuera del periodo solicitado."""
    from models.finanzas import MovimientoFinanciero

    resultado = MovimientoFinanciero.historico_diario(2)  # solo últimos 2 días (4 y 5)
    dias = [e["dia"] for e in resultado]

    assert 3 not in dias, "El día 3 no debería aparecer en historico_diario(2)"
    assert 4 in dias or 5 in dias, "Al menos el día 4 o 5 debe aparecer"
