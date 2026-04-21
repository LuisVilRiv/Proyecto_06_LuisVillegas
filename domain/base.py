from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class EntidadBase:
    """Mixin para identificar y controlar el ciclo de vida de una entidad."""
    id: int = 0
    nombre: str = ""
    activo: bool = True
    creado_en: datetime = field(default_factory=datetime.now)

@dataclass
class MantenibleMixin:
    """Mixin para objetos que sufren desgaste físico o lógico."""
    integridad: float = 100.0
    en_mantenimiento: bool = False

    def degradar(self, cantidad: float):
        """Reduce la integridad del objeto asegurando que no baje de 0."""
        self.integridad = max(0.0, self.integridad - cantidad)

    def reparar(self):
        """Restaura la integridad al máximo y finaliza el estado de mantenimiento."""
        self.integridad = 100.0
        self.en_mantenimiento = False

    @property
    def necesita_reparacion(self) -> bool:
        """Indica si el objeto está en umbral crítico de fallo."""
        return self.integridad < 30.0

@dataclass
class FinancieroMixin:
    """Mixin para objetos que generan flujo de caja."""
    ingresos_acumulados: float = 0.0
    gastos_acumulados: float = 0.0

    def registrar_ingreso(self, cantidad: float):
        """Suma ingresos brutos."""
        self.ingresos_acumulados += cantidad

    def registrar_gasto(self, cantidad: float):
        """Suma gastos operativos o de inversión."""
        self.gastos_acumulados += cantidad

    @property
    def balance(self) -> float:
        """Resultado neto acumulado."""
        return self.ingresos_acumulados - self.gastos_acumulados