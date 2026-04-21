import pytest
from domain.atracciones import AtraccionMecanica
from domain.personal import EmpleadoBase
from domain.visitantes import VisitanteBase, Familia
from core.exceptions import AforoCompletoError, NominaError

def test_mantenible_mixin():
    obj = AtraccionMecanica(nombre="Test")
    obj.degradar(120.0)
    assert obj.integridad == 0.0
    assert obj.necesita_reparacion is True
    obj.reparar()
    assert obj.integridad == 100.0
    assert obj.en_mantenimiento is False

def test_mantenimiento_umbral():
    obj = AtraccionMecanica(integridad=25.0)
    assert obj.necesita_reparacion is True

def test_aforo_completo_error():
    atr = AtraccionMecanica(capacidad_max=2, visitantes_en_cola=2)
    with pytest.raises(AforoCompletoError):
        atr.admitir_visitante()

def test_nomina_error():
    emp = EmpleadoBase(nombre="Sin Paga", salario=0)
    with pytest.raises(NominaError):
        emp.cobrar_nomina()

def test_visitante_presupuesto():
    f = Familia(presupuesto=10.0)
    assert f.gastar(5.0) is True
    assert f.presupuesto == 5.0
    assert f.gastar(20.0) is False

def test_visitante_satisfaccion_limites():
    v = VisitanteBase(satisfaccion=95.0)
    v.actualizar_satisfaccion(10.0)
    assert v.satisfaccion == 100.0
    v.actualizar_satisfaccion(-110.0)
    assert v.satisfaccion == 0.0

def test_atraccion_serialization():
    original = AtraccionMecanica(id=1, nombre="Noria", integridad=80.0)
    d = original.to_dict()
    assert d["nombre"] == "Noria"
    assert d["integridad"] == 80.0
    nuevo = AtraccionMecanica.from_dict(d)
    assert original == nuevo