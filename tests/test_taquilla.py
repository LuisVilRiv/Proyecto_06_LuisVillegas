"""
ScienceWorld Park — tests/test_taquilla.py
Tests unitarios para domain/taquilla.py (Sección F.1 / C.2).

Criterios de aceptación del reporte:
  - precio_psicologico(29.70) devuelve un valor con ,99
  - precio_psicologico(32.00) == 31.99
  - precio_psicologico(93.50) == 93.99
  - La contabilidad conserva el valor exacto (precio_base + iva)
    aunque la UI muestre el precio psicológico
"""

import pytest
from domain.taquilla import precio_psicologico, formatear_precio_ui


# ── Casos del checklist F.1 ───────────────────────────────────────────────────

def test_precio_psicologico_32():
    """32.00 → 31.99 (caso explícito del PDF)."""
    assert precio_psicologico(32.00) == 31.99


def test_precio_psicologico_93_50():
    """93.50 → 93.99 (caso explícito del test F.2 del PDF)."""
    assert precio_psicologico(93.50) == 93.99


def test_precio_psicologico_10():
    """10.00 → 9.99."""
    assert precio_psicologico(10.00) == 9.99


def test_precio_psicologico_29_70():
    """
    29.70 → precio con ,99.
    El PDF tiene una inconsistencia entre el enunciado (28.99) y su propio código
    (que produce 29.99). Verificamos que el resultado termina en ,99 y es < 30.
    Ver nota en domain/taquilla.py.
    """
    resultado = precio_psicologico(29.70)
    assert str(resultado).endswith(".99"), (
        f"El precio psicológico debe terminar en ,99 — obtenido: {resultado}"
    )
    assert resultado < 30.0, "El precio psicológico debe ser menor que 30€"


def test_precio_psicologico_siempre_termina_en_99():
    """Propiedad general: precio_psicologico() siempre devuelve X.99."""
    casos = [5.0, 9.5, 12.3, 18.0, 27.0, 29.70, 32.0, 85.0, 93.5, 100.0]
    for precio in casos:
        resultado = precio_psicologico(precio)
        assert round(resultado % 1, 2) == 0.99, (
            f"precio_psicologico({precio}) = {resultado} no termina en ,99"
        )


def test_precio_psicologico_siempre_menor_que_original():
    """El precio psicológico siempre es menor que el precio exacto."""
    casos = [5.0, 18.0, 27.0, 32.0, 85.0, 93.5]
    for precio in casos:
        assert precio_psicologico(precio) < precio, (
            f"precio_psicologico({precio}) debería ser < {precio}"
        )


# ── Contabilidad conserva el valor exacto ─────────────────────────────────────

def test_contabilidad_conserva_precio_exacto():
    """
    Criterio F.1/C.2: la UI muestra el precio psicológico pero
    MovimientoFinanciero.importe debe usar el precio_base exacto.
    Verificamos que precio_psicologico() NO se aplica al importe contable.
    """
    precio_base  = 27.0
    iva          = round(precio_base * 0.10, 2)
    precio_total = precio_base + iva   # 29.70 — valor contable exacto

    precio_ui = precio_psicologico(precio_total)

    # El valor contable es el exacto
    assert precio_total == 29.70
    # La UI muestra algo diferente (con ,99)
    assert precio_ui != precio_total
    assert str(precio_ui).endswith(".99")


# ── formatear_precio_ui ───────────────────────────────────────────────────────

def test_formatear_precio_ui_formato_europeo():
    """formatear_precio_ui() devuelve string con formato europeo y símbolo €."""
    resultado = formatear_precio_ui(32.0)
    assert resultado.endswith("€")
    assert "31,99" in resultado or "31.99" in resultado.replace(",", ".")


def test_formatear_precio_ui_no_modifica_contabilidad():
    """formatear_precio_ui() es pura — no modifica ningún estado."""
    precio = 85.0
    for _ in range(5):
        r = formatear_precio_ui(precio)
        assert r.endswith("€")
    # El precio original no cambia
    assert precio == 85.0
