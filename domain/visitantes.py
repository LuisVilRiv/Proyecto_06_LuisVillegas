"""
ScienceWorld Park — domain/visitantes.py
Jerarquía de Visitantes (PDF §8.4).
Clases Python puro.
"""

import random
from dataclasses import dataclass
from domain.base import EntidadBase


@dataclass
class VisitanteBase(EntidadBase):
    satisfaccion: float = 50.0
    presupuesto: float = 50.0
    tiempo_restante: float = 6.0
    posicion_seccion: int = 0

    # ── Economía ────────────────────────────────────────────────────────

    def gastar(self, cantidad: float) -> bool:
        """Intenta descontar *cantidad* del presupuesto. Devuelve True si puede."""
        if self.presupuesto >= cantidad:
            self.presupuesto -= cantidad
            return True
        return False

    def decidir_consumo(self, prob_base: float = 0.2):
        """Decide aleatoriamente si el visitante consume algo. Devuelve dict o None."""
        modificador = self.satisfaccion / 100.0
        if random.random() < (prob_base * modificador):
            categoria = "Comida" if random.random() < 0.7 else "Souvenir"
            gasto = random.uniform(5.0, 25.0)
            if self.gastar(gasto):
                return {"categoria": categoria, "monto": round(gasto, 2)}
        return None

    # ── Satisfacción ────────────────────────────────────────────────────

    def actualizar_satisfaccion(self, delta: float) -> None:
        self.satisfaccion = max(0.0, min(100.0, self.satisfaccion + delta))


# ── Perfiles (PDF §4.4) ──────────────────────────────────────────────────────

@dataclass
class Familia(VisitanteBase):
    """Sensible al precio, prioriza talleres y restauración."""
    num_ninos: int = 2
    presupuesto: float = 80.0
    tiempo_restante: float = 7.0


@dataclass
class GrupoEscolar(VisitanteBase):
    """Descuento automático, guía obligatorio, alta sensibilidad al precio."""
    num_alumnos: int = 25
    presupuesto: float = 30.0
    tiempo_restante: float = 6.0


@dataclass
class Turista(VisitanteBase):
    """Mayor presupuesto, más tiempo en el parque, más souvenirs."""
    presupuesto: float = 120.0
    tiempo_restante: float = 9.0


@dataclass
class AficionadoCiencia(VisitanteBase):
    """Maximiza exhibiciones, baja sensibilidad al precio."""
    presupuesto: float = 60.0
    tiempo_restante: float = 8.0


@dataclass
class VisitanteVIP(VisitanteBase):
    """Fast-track incluido, mayor gasto medio, sin sensibilidad al precio."""
    fast_track: bool = True
    presupuesto: float = 200.0
    tiempo_restante: float = 5.0  # visita rápida pero intensiva
