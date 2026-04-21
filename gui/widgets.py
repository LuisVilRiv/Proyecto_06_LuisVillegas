from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout

class InfoCard(QFrame):
    def __init__(self, titulo, valor, icono="📊"):
        super().__init__()
        self.setObjectName("InfoCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        layout = QHBoxLayout(self)
        
        self.lbl_icon = QLabel(icono)
        self.lbl_icon.setStyleSheet("font-size: 32px;")
        layout.addWidget(self.lbl_icon)
        
        text_layout = QVBoxLayout()
        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setStyleSheet("color: #00d1ff; font-size: 10px; font-weight: bold;")
        
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        text_layout.addWidget(self.lbl_titulo)
        text_layout.addWidget(self.lbl_valor)
        layout.addLayout(text_layout)

    def update_value(self, nuevo_valor):
        self.lbl_valor.setText(nuevo_valor)

class StatusBadge(QLabel):
    def __init__(self, color="green"):
        super().__init__()
        self.setFixedSize(12, 12)
        self.update_color(color)

    def update_color(self, color):
        colores = {
            "green": "#2ecc71",
            "yellow": "#f1c40f",
            "red": "#e74c3c"
        }
        hex_color = colores.get(color, "#95a5a6")
        self.setStyleSheet(f"background-color: {hex_color}; border-radius: 6px;")