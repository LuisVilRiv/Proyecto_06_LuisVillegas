from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from models.eventos_log import EventoLogModel

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.lbl_titulo = QLabel("HISTORIAL DE EVENTOS Y SUCESOS")
        self.lbl_titulo.setStyleSheet("font-weight: bold; color: #00d1ff; font-size: 14px;")
        layout.addWidget(self.lbl_titulo)
        
        self.list_events = QListWidget()
        layout.addWidget(self.list_events)
        
        self.refresh()

    def refresh(self):
        """Carga los últimos 15 eventos registrados en la base de datos."""
        self.list_events.clear()
        logs = EventoLogModel.select().order_by(EventoLogModel.id.desc()).limit(15)
        
        for entry in logs:
            msg = f"[Día {entry.dia_juego} - {entry.hora_juego:02d}:00] {entry.tipo}: {entry.descripcion}"
            self.list_events.addItem(msg)