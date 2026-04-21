import sys
from PySide6.QtWidgets import QApplication
from models.db import init_db
from models.usuarios import inicializar_usuarios
from gui.login_window import LoginWindow
from gui.main_window import MainWindow
from core.motor import MotorSimulacion

class ScienceWorldApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        init_db()
        inicializar_usuarios()
        self.login = LoginWindow()
        self.login.partida_seleccionada.connect(self.iniciar_juego)
        self.login.show()

    def iniciar_juego(self, partida_model):
        MotorSimulacion().cargar_partida(partida_model)
        self.main_window = MainWindow()
        self.main_window.show()
        self.login.close()

    def ejecutar(self):
        return self.app.exec()

if __name__ == "__main__":
    app_runner = ScienceWorldApp()
    sys.exit(app_runner.ejecutar())
