"""
ScienceWorld Park — core/eventos.py
Jerarquía de eventos del dominio (PDF §4.3).

Correcciones aplicadas (v3.0):
 - D.2: registrar() es el único punto de escritura en EventoLogModel.
         El motor no debe llamar a _log_evento() — solo a evento.registrar().
 - D.4: EventoAccidente y EventoViralFamoso tienen toda la lógica de impacto aquí.
         El motor es un orquestador puro: aplica y registra, no hardcodea números.
 - NUEVO: EventoHuelga añadida para que _evento_huelga() del motor también use dominio.
"""

import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from domain.atracciones import AtraccionBase
from models.eventos_log import EventoLogModel
from models.secciones import SeccionModel


class EventoBase(ABC):
    def __init__(self, nombre: str, descripcion: str, probabilidad: float):
        self.nombre = nombre
        self.descripcion = descripcion
        self.probabilidad = probabilidad

    @abstractmethod
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        pass

    def registrar(self, dia: int, hora: int):
        """Único punto de escritura en EventoLogModel (D.2)."""
        EventoLogModel.create(
            tipo=self.nombre,
            descripcion=self.descripcion,
            dia_juego=dia,
            hora_juego=hora,
            timestamp=datetime.now()
        )


class EventoFalloLeve(EventoBase):
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        if not atracciones:
            return
        target = random.choice(atracciones)
        perdida = random.uniform(5.0, 15.0)
        target.degradar(perdida)
        self.descripcion = f"Fallo leve en {target.nombre}: -{perdida:.1f}% integridad."


class EventoAveriaGrave(EventoBase):
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        if not atracciones:
            return
        target = random.choice(atracciones)
        target.integridad = 0.0
        target.en_mantenimiento = True
        self.descripcion = f"Avería grave en {target.nombre}. Fuera de servicio."


class EventoAccidente(EventoBase):
    """
    D.4: toda la lógica de impacto reside aquí, no en motor._evento_accidente().
    Penalización: -20 reputación (no -15) + clausura de una sección.
    """
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        parque_domain.reputacion = max(0.0, parque_domain.reputacion - 20.0)
        seccion_id = random.randint(1, 8)
        SeccionModel.update(activa=False).where(SeccionModel.id == seccion_id).execute()
        self.descripcion = (
            f"Accidente reportado. Reputación -20. "
            f"Sección {seccion_id} clausurada temporalmente."
        )


class EventoClima(EventoBase):
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        afectadas = [a for a in atracciones if a.to_dict().get('tipo') in ['mecanica', 'extreme']]
        for a in afectadas:
            a.degradar(2.0)
        self.descripcion = f"Clima adverso afectando a {len(afectadas)} atracciones mecánicas."


class EventoViralFamoso(EventoBase):
    """
    D.4: expone viral_dias para que el motor pueda actualizar _viral_dias
    sin hardcodear lógica en el motor.
    """
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        parque_domain.reputacion = min(100.0, parque_domain.reputacion + 10.0)
        self.viral_dias = random.randint(2, 4)
        self.descripcion = (
            f"Un influencer visita el parque. Reputación +10. "
            f"Afluencia +30% durante {self.viral_dias} días."
        )


class EventoHuelga(EventoBase):
    """
    NUEVO: clase de dominio para huelgas. El impacto económico (restauración al 20%)
    lo gestiona el CrisisDialog — aquí solo se describe el evento.
    """
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        self.descripcion = (
            "El personal de hostelería ha convocado huelga. "
            "Ingresos de restauración reducidos al 20% durante 24h."
        )
