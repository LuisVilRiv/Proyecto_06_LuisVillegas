from dataclasses import dataclass
from domain.base import EntidadBase

@dataclass
class EmpleadoBase(EntidadBase):
    salario: float = 0.0
    satisfaccion: float = 80.0
    seccion_asignada: int = 1 # Obligatorio según diseño

@dataclass
class Tecnico(EmpleadoBase):
    especialidad: str = "mecanica"
    eficiencia_reparacion: float = 1.2

@dataclass
class PersonalCientifico(EmpleadoBase):
    disciplina: str = "Fisica"
    nivel_divulgacion: int = 2

@dataclass
class Divulgador(PersonalCientifico):
    bonus_reputacion: float = 0.05

@dataclass
class PersonalHosteleria(EmpleadoBase):
    velocidad_servicio: float = 1.0 # Influye en ingresos de comida