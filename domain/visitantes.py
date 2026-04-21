import random
from dataclasses import dataclass
from domain.base import EntidadBase

@dataclass
class VisitanteBase(EntidadBase):
    satisfaccion: float = 50.0
    presupuesto: float = 50.0
    tiempo_restante: float = 6.0
    posicion_seccion: int = 0

    def decidir_consumo(self, prob_base: float = 0.2):
        """Probabilidad de gasto en restauración o tienda según satisfacción."""
        modificador = self.satisfaccion / 100.0
        if random.random() < (prob_base * modificador):
            # Decidir categoría
            categoria = "Comida" if random.random() < 0.7 else "Souvenir"
            gasto = random.uniform(5.0, 25.0)
            
            if self.presupuesto >= gasto:
                self.presupuesto -= gasto
                return {"categoria": categoria, "monto": gasto}
        return None

    def actualizar_satisfaccion(self, delta: float):
        self.satisfaccion = max(0.0, min(100.0, self.satisfaccion + delta))

@dataclass
class Familia(VisitanteBase):
    num_ninos: int = 2
    presupuesto: float = 80.0
@dataclass
class VisitanteVIP(VisitanteBase):
    fast_track: bool = True
    presupuesto: float = 200.0