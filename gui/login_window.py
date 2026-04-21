from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QListWidget, QComboBox, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, Signal
from models.usuarios import UsuarioModel, PartidaModel
from models.parque import ParqueModel
from models.db import db

class LoginWindow(QWidget):
    partida_seleccionada = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScienceWorld Park - Acceso")
        self.setFixedSize(500, 600)
        self._aplicar_estilo()
        self.layout_principal = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.layout_principal.addWidget(self.stack)
        self._setup_login_ui()
        self._setup_partidas_ui()

    def _aplicar_estilo(self):
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2d; color: #ffffff; font-family: 'Segoe UI'; }
            QLineEdit { background-color: #252538; border: 1px solid #00d1ff; padding: 10px; border-radius: 5px; }
            QPushButton { background-color: #00d1ff; color: #1e1e2d; font-weight: bold; padding: 12px; border-radius: 5px; }
            QPushButton:hover { background-color: #00b8e6; }
            QListWidget { background-color: #252538; border: 1px solid #2d2d44; }
        """)

    def _setup_login_ui(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(20)
        title = QLabel("SCIENCEWORLD PARK\nGestión de Proyectos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d1ff;")
        title.setAlignment(Qt.AlignCenter)
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Usuario (admin)")
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña (science2026)")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        btn_login = QPushButton("ENTRAR AL SISTEMA")
        btn_login.clicked.connect(self._intentar_login)
        lay.addWidget(title)
        lay.addWidget(self.txt_user)
        lay.addWidget(self.txt_pass)
        lay.addWidget(btn_login)
        self.stack.addWidget(page)

    def _setup_partidas_ui(self):
        self.page_partidas = QWidget()
        lay = QVBoxLayout(self.page_partidas)
        lay.addWidget(QLabel("SELECCIONAR PARTIDA:"))
        self.lista_partidas = QListWidget()
        btn_cargar = QPushButton("CARGAR PARTIDA")
        btn_cargar.clicked.connect(self._cargar_partida)
        lay.addWidget(self.lista_partidas)
        lay.addWidget(btn_cargar)
        lay.addWidget(QLabel("\nNUEVA PARTIDA:"))
        self.txt_nueva = QLineEdit()
        self.txt_nueva.setPlaceholderText("Nombre del parque...")
        self.combo_diff = QComboBox()
        self.combo_diff.addItems(["Fácil", "Normal", "Científico"])
        btn_crear = QPushButton("INICIAR PROYECTO")
        btn_crear.clicked.connect(self._crear_partida)
        lay.addWidget(self.txt_nueva)
        lay.addWidget(self.combo_diff)
        lay.addWidget(btn_crear)
        self.stack.addWidget(self.page_partidas)

    def _intentar_login(self):
        user = UsuarioModel.get_or_none(UsuarioModel.username == self.txt_user.text())
        if user and user.verificar_password(self.txt_pass.text()):
            self._refrescar_partidas()
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")

    def _refrescar_partidas(self):
        self.lista_partidas.clear()
        self.partidas_cache = list(PartidaModel.select())
        for p in self.partidas_cache:
            self.lista_partidas.addItem(f"{p.nombre_partida} [{p.dificultad}]")

    def _crear_partida(self):
        nombre = self.txt_nueva.text()
        if not nombre: return
        diff = self.combo_diff.currentText()
        presupuestos = {"Fácil": 5000000.0, "Normal": 2000000.0, "Científico": 800000.0}
        with db.atomic():
            nuevo_parque = ParqueModel.create(nombre=nombre, dinero=presupuestos[diff], reputacion=50.0)
            nueva_p = PartidaModel.create(nombre_partida=nombre, dificultad=diff, parque=nuevo_parque)
        self.partida_seleccionada.emit(nueva_p)

    def _cargar_partida(self):
        idx = self.lista_partidas.currentRow()
        if idx >= 0:
            self.partida_seleccionada.emit(self.partidas_cache[idx])
