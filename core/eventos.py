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
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        parque_domain.reputacion = max(0.0, parque_domain.reputacion - 20.0)
        seccion_id = random.randint(1, 8)
        SeccionModel.update(activa=False).where(SeccionModel.id == seccion_id).execute()
        self.descripcion = f"Accidente reportado. Reputación -20. Sección {seccion_id} clausurada."

class EventoClima(EventoBase):
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        afectadas = [a for a in atracciones if a.to_dict().get('tipo') in ['mecanica', 'extreme']]
        for a in afectadas:
            a.degradar(2.0)
        self.descripcion = f"Clima adverso afectando a {len(afectadas)} atracciones mecánicas."

class EventoViralFamoso(EventoBase):
    def aplicar(self, parque_domain, atracciones: List[AtraccionBase]):
        parque_domain.reputacion = min(100.0, parque_domain.reputacion + 10.0)
        self.descripcion = "Un influencer visita el parque. Reputación +10."