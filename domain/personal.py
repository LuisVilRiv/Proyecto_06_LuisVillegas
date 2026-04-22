"""
ScienceWorld Park — domain/personal.py
Jerarquía completa de Personal (PDF §8.3).
Clases Python puro: sin PySide6, sin Peewee.
"""

from dataclasses import dataclass, field
from domain.base import EntidadBase
from core.exceptions import NominaError


# ── Base ────────────────────────────────────────────────────────────────────

@dataclass
class EmpleadoBase(EntidadBase):
    salario: float = 0.0
    satisfaccion: float = 80.0
    nivel: int = 1
    turno: str = "mañana"
    seccion_asignada: int = 1

    def cobrar_nomina(self) -> float:
        """Devuelve importe de la nómina mensual.  Lanza NominaError si inválido."""
        if self.salario <= 0:
            raise NominaError(
                f"Salario inválido para empleado '{self.nombre}': {self.salario}"
            )
        return self.salario

    def nomina_diaria(self) -> float:
        """Importe proporcional diario (1/30 del salario mensual)."""
        return self.cobrar_nomina() / 30.0


# ── Personal Operativo ───────────────────────────────────────────────────────

@dataclass
class PersonalOperativo(EmpleadoBase):
    especialidad: str = "general"
    zona_asignada: str = ""


@dataclass
class Tecnico(EmpleadoBase):
    """Técnico de mantenimiento mecánico / eléctrico."""
    especialidad: str = "mecanica"
    eficiencia_reparacion: float = 1.2
    atracciones_asignadas: list = field(default_factory=list)


@dataclass
class PersonalLimpieza(PersonalOperativo):
    indice_limpieza: float = 1.0


# ── Personal Científico ─────────────────────────────────────────────────────

@dataclass
class PersonalCientifico(EmpleadoBase):
    disciplina: str = "Fisica"
    nivel_divulgacion: int = 2
    talleres_impartidos: int = 0


@dataclass
class Divulgador(PersonalCientifico):
    bonus_reputacion: float = 0.05
    seccion_especialidad: str = ""
    satisfaccion_bonus_visitante: float = 2.0


# ── Hostelería ───────────────────────────────────────────────────────────────

@dataclass
class PersonalHosteleria(EmpleadoBase):
    rol: str = "camarero"
    velocidad_servicio: float = 1.0
    restaurante_asignado: int = 0


@dataclass
class Cocinero(PersonalHosteleria):
    nivel_cocina: int = 1
    recetas_disponibles: int = 5


# ── Técnicos Especializados ──────────────────────────────────────────────────

@dataclass
class TecnicoEspecializado(EmpleadoBase):
    """VR / laboratorio / eléctrico / simulador (PDF §8.3)."""
    tipo_especialidad: str = "simulador"
    tiempo_reparacion_base: float = 2.0
