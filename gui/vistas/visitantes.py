from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QListWidget, QFrame
from PySide6.QtCore import Qt
import random

class VisitantesView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("[VIS] CENTRO DE VISITANTES")
        title.setStyleSheet(
            "color:#00ff9f; font-size:13px; font-weight:900; font-family:'Courier New'; letter-spacing:1px;"
        )
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("SectionCard")
        card_l = QVBoxLayout(card)

        self.lbl_count = QLabel("VISITANTES EN EL PARQUE: 0")
        self.lbl_count.setStyleSheet("font-size: 12px; font-weight: 900; color: #a8ffd9;")
        card_l.addWidget(self.lbl_count)

        card_l.addWidget(QLabel("[AVG] SATISFACCION MEDIA:"))
        self.bar_sat = QProgressBar()
        self.bar_sat.setRange(0, 100)
        self.bar_sat.setValue(75)
        card_l.addWidget(self.bar_sat)
        layout.addWidget(card)

        layout.addWidget(QLabel("[FEED] COMENTARIOS DE VISITANTES:"))
        self.list_feedback = QListWidget()
        self.list_feedback.setStyleSheet("font-style: italic;")
        layout.addWidget(self.list_feedback)

        self.feedbacks = [
            "¡El Planetario es asombroso!",
            "Las colas son un poco largas hoy.",
            "Me encanta la sección de Biología.",
            "Un poco caro el precio de la entrada.",
            "¿Dónde están los guías científicos?",
            "¡La montaña rusa de ADN es adrenalina pura!"
        ]
        self.refresh()

    def refresh(self):
        from models.parque import ParqueModel
        from core.motor import MotorSimulacion

        p = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        
        # Simulación de datos de visitantes basada en reputación
        count = int(p.reputacion * random.uniform(5, 12))
        self.lbl_count.setText(f"VISITANTES EN EL PARQUE: {count}")
        
        sat = int(p.reputacion * random.uniform(0.8, 1.1))
        self.bar_sat.setValue(min(100, max(0, sat)))
        
        if random.random() < 0.3:
            self.list_feedback.insertItem(0, random.choice(self.feedbacks))
            if self.list_feedback.count() > 10:
                self.list_feedback.takeItem(10)