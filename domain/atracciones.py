from dataclasses import dataclass, asdict
from abc import abstractmethod
from domain.base import EntidadBase, MantenibleMixin, FinancieroMixin
from core.exceptions import AforoCompletoError

@dataclass
class AtraccionBase(EntidadBase, MantenibleMixin, FinancieroMixin):
    """Lógica de negocio para las atracciones científicas."""
    capacidad_max: int = 20
    duracion_min: int = 10
    precio_base: float = 0.0
    altura_minima_cm: int = 0
    seccion_id: int = 0
    visitantes_en_cola: int = 0

    @abstractmethod
    def evaluar_fallo(self) -> bool:
        pass

    def admitir_visitante(self):
        if self.visitantes_en_cola >= self.capacidad_max:
            raise AforoCompletoError(f"Atracción {self.nombre} llena.")
        self.visitantes_en_cola += 1

    def calcular_coste_reparacion(self) -> float:
        """Calcula el coste económico para restaurar la integridad."""
        return (100.0 - self.integridad) * 150.0

    def reparar(self):
        """Restaura la integridad y habilita la atracción."""
        self.integridad = 100.0
        self.en_mantenimiento = False

    @property
    def estado_str(self) -> str:
        if not self.activo:
            return "Cerrada"
        if self.en_mantenimiento:
            return "En Avería"
        return "Operativa"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AtraccionBase":
        return cls(**data)

@dataclass
class AtraccionMecanica(AtraccionBase):
    tasa_desgaste: float = 1.5
    def evaluar_fallo(self) -> bool:
        return self.integridad < 10.0

@dataclass
class AtraccionSimulador(AtraccionBase):
    requiere_tecnico_vr: bool = True
    desgaste_software: float = 0.0
    def evaluar_fallo(self) -> bool:
        return self.integridad < 5.0

@dataclass
class AtraccionInteractiva(AtraccionBase):
    aforo_continuo: bool = True
    tasa_desgaste: float = 0.3
    def evaluar_fallo(self) -> bool:
        return False

@dataclass
class AtraccionLaboratorio(AtraccionBase):
    requiere_cientifico: bool = True
    riesgo_incidente: float = 0.002
    def evaluar_fallo(self) -> bool:
        return False

@dataclass
class AtraccionExtreme(AtraccionMecanica):
    edad_minima: int = 12
    factor_satisfaccion: float = 1.8