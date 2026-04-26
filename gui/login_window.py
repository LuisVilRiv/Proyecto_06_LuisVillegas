"""
ScienceWorld Park — gui/login_window.py

Correcciones aplicadas (v3.1):
 - G.1/G.2: Selector de modo (Campaña / Extremo) y dificultad antes de crear partida.
             Al confirmar se llama a seed_modo_campana() o seed_modo_extremo()
             antes de emitir partida_seleccionada.
 - NUEVO: Pantalla de registro (página 3) accesible desde el login.
          Permite crear nuevas cuentas de usuario con validación de campos.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QComboBox, QStackedWidget,
    QMessageBox, QFrame, QButtonGroup, QAbstractButton,
)
from PySide6.QtCore import Qt, Signal

from models.usuarios import UsuarioModel, PartidaModel
from models.parque   import ParqueModel
from models.db       import db

# Mapeo etiqueta UI → clave interna de DIFICULTAD_CONFIG
_DIFF_MAP = {
    "Fácil":      "facil",
    "Normal":     "normal",
    "Difícil":    "dificil",
    "Pesadilla":  "pesadilla",
}


class LoginWindow(QWidget):
    partida_seleccionada = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ScienceWorld Park — Acceso")
        self.setFixedSize(520, 640)
        self._aplicar_estilo()

        self.layout_principal = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.layout_principal.addWidget(self.stack)

        self._setup_login_ui()       # página 0
        self._setup_partidas_ui()    # página 1
        self._setup_nueva_ui()       # página 2 — selector de modo/dificultad
        self._setup_registro_ui()    # página 3 — nueva cuenta

    # ── Estilos ───────────────────────────────────────────────────────────

    def _aplicar_estilo(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0d18;
                color: #e2e8f0;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #0f1423;
                border: 1px solid #00d1ff;
                padding: 10px;
                border-radius: 5px;
                color: #e2e8f0;
            }
            QPushButton {
                background-color: rgba(0,209,255,0.12);
                color: #00d1ff;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
                border: 1px solid rgba(0,209,255,0.35);
            }
            QPushButton:hover { background-color: rgba(0,209,255,0.22); }
            QPushButton:checked {
                background-color: rgba(0,209,255,0.30);
                border-color: #00d1ff;
            }
            QPushButton#BtnSecundario {
                background-color: transparent;
                color: #4b5563;
                border: 1px solid #1a1f2e;
                padding: 10px;
            }
            QPushButton#BtnSecundario:hover {
                background-color: rgba(255,255,255,0.04);
                color: #9ca3af;
                border-color: #374151;
            }
            QListWidget {
                background-color: #0f1423;
                border: 1px solid #1a1f2e;
                color: #e2e8f0;
            }
            QListWidget::item:selected { background: rgba(0,209,255,0.15); color: #00d1ff; }
            QComboBox {
                background-color: #0f1423;
                border: 1px solid #2d3748;
                padding: 8px;
                border-radius: 5px;
                color: #e2e8f0;
            }
            QFrame#ModeCard {
                background: #0f1423;
                border: 1px solid #1a1f2e;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame#ModeCard:hover { border-color: rgba(0,209,255,0.4); }
            QFrame#Separador {
                background: #1a1f2e;
                max-height: 1px;
                border: none;
            }
        """)

    # ── Página 0: Login ───────────────────────────────────────────────────

    def _setup_login_ui(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setSpacing(14)
        lay.setContentsMargins(40, 40, 40, 40)

        title = QLabel("SCIENCEWORLD PARK")
        title.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #00d1ff;"
            "letter-spacing: 4px;"
        )
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Sistema de Gestión del Parque")
        subtitle.setStyleSheet("color: #374151; font-size: 11px; letter-spacing: 2px;")
        subtitle.setAlignment(Qt.AlignCenter)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Usuario")

        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.returnPressed.connect(self._intentar_login)

        btn_login = QPushButton("ENTRAR AL SISTEMA")
        btn_login.clicked.connect(self._intentar_login)

        # Separador visual
        sep_frame = QFrame()
        sep_frame.setObjectName("Separador")
        sep_frame.setFixedHeight(1)

        # Botón de registro secundario
        btn_registro = QPushButton("¿Primera vez?  CREAR CUENTA NUEVA")
        btn_registro.setObjectName("BtnSecundario")
        btn_registro.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        lay.addStretch()
        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addSpacing(20)
        lay.addWidget(self.txt_user)
        lay.addWidget(self.txt_pass)
        lay.addWidget(btn_login)
        lay.addSpacing(8)
        lay.addWidget(sep_frame)
        lay.addSpacing(4)
        lay.addWidget(btn_registro)
        lay.addStretch()

        self.stack.addWidget(page)

    # ── Página 1: Selección de partida ────────────────────────────────────

    def _setup_partidas_ui(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setSpacing(12)
        lay.setContentsMargins(30, 30, 30, 30)

        lbl = QLabel("SELECCIONAR PARTIDA")
        lbl.setStyleSheet(
            "color: #00d1ff; font-size: 13px; font-weight: 900; letter-spacing: 3px;"
        )
        lay.addWidget(lbl)

        self.lista_partidas = QListWidget()
        lay.addWidget(self.lista_partidas)

        btn_cargar = QPushButton("CARGAR PARTIDA")
        btn_cargar.clicked.connect(self._cargar_partida)
        lay.addWidget(btn_cargar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #1a1f2e;")
        lay.addWidget(sep)

        btn_nueva = QPushButton("+ NUEVA PARTIDA")
        btn_nueva.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        lay.addWidget(btn_nueva)

        self.stack.addWidget(page)

    # ── Página 2: Selector de modo y dificultad ───────────────────────────

    def _setup_nueva_ui(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setSpacing(14)
        lay.setContentsMargins(30, 24, 30, 24)

        # Cabecera
        lbl_titulo = QLabel("NUEVA PARTIDA")
        lbl_titulo.setStyleSheet(
            "color: #00d1ff; font-size: 13px; font-weight: 900; letter-spacing: 3px;"
        )
        lay.addWidget(lbl_titulo)

        # Nombre del parque
        self.txt_nueva = QLineEdit()
        self.txt_nueva.setPlaceholderText("Nombre del parque...")
        lay.addWidget(self.txt_nueva)

        # ── Selector de modo ──────────────────────────────────────────────
        lbl_modo = QLabel("MODO DE JUEGO")
        lbl_modo.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800; letter-spacing: 2px;"
        )
        lay.addWidget(lbl_modo)

        modo_row = QHBoxLayout()
        modo_row.setSpacing(10)

        self._modo_group = QButtonGroup(self)
        self._modo_group.setExclusive(True)

        self._btn_campana = QPushButton("🏗️  MODO CAMPAÑA\nEmpieza desde cero")
        self._btn_campana.setCheckable(True)
        self._btn_campana.setChecked(True)
        self._btn_campana.setMinimumHeight(60)
        self._btn_campana.clicked.connect(self._on_modo_changed)

        self._btn_extremo = QPushButton("🔥  MODO EXTREMO\nRescata el parque en quiebra")
        self._btn_extremo.setCheckable(True)
        self._btn_extremo.setMinimumHeight(60)
        self._btn_extremo.clicked.connect(self._on_modo_changed)

        self._modo_group.addButton(self._btn_campana, 0)
        self._modo_group.addButton(self._btn_extremo, 1)
        modo_row.addWidget(self._btn_campana)
        modo_row.addWidget(self._btn_extremo)
        lay.addLayout(modo_row)

        # ── Selector de dificultad (solo visible en Modo Campaña) ─────────
        self._diff_frame = QFrame()
        diff_lay = QVBoxLayout(self._diff_frame)
        diff_lay.setContentsMargins(0, 0, 0, 0)
        diff_lay.setSpacing(6)

        lbl_diff = QLabel("DIFICULTAD")
        lbl_diff.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800; letter-spacing: 2px;"
        )
        diff_lay.addWidget(lbl_diff)

        self.combo_diff = QComboBox()
        self.combo_diff.addItems(["Fácil", "Normal", "Difícil", "Pesadilla"])
        self.combo_diff.setCurrentIndex(1)  # Normal por defecto
        self.combo_diff.currentIndexChanged.connect(self._actualizar_desc_dificultad)
        diff_lay.addWidget(self.combo_diff)

        # Descripción de la dificultad seleccionada
        self._lbl_diff_desc = QLabel()
        self._lbl_diff_desc.setWordWrap(True)
        self._lbl_diff_desc.setStyleSheet("color: #6b7280; font-size: 10px; padding: 4px 0;")
        diff_lay.addWidget(self._lbl_diff_desc)
        lay.addWidget(self._diff_frame)

        # ── Descripción del Modo Extremo (oculta inicialmente) ────────────
        self._extremo_frame = QFrame()
        ext_lay = QVBoxLayout(self._extremo_frame)
        ext_lay.setContentsMargins(0, 0, 0, 0)

        lbl_ext = QLabel(
            "⚠️  Condiciones iniciales fijas:\n"
            "• Saldo: -180.000 € (crédito de emergencia de 200.000 €)\n"
            "• Reputación: 8/100  ·  12 de 15 atracciones averiadas\n"
            "• Solo 3 empleados activos  ·  Inventario completamente vacío\n"
            "• Eventos negativos ×3 durante los primeros 30 días"
        )
        lbl_ext.setWordWrap(True)
        lbl_ext.setStyleSheet(
            "color: #f59e0b; font-size: 10px; padding: 8px;"
            "background: rgba(245,158,11,0.08); border-radius: 6px;"
            "border: 1px solid rgba(245,158,11,0.2);"
        )
        ext_lay.addWidget(lbl_ext)
        lay.addWidget(self._extremo_frame)
        self._extremo_frame.setVisible(False)

        # Inicializar descripción de dificultad
        self._actualizar_desc_dificultad()

        lay.addStretch()

        # Botones de acción
        btn_row = QHBoxLayout()
        btn_volver = QPushButton("← VOLVER")
        btn_volver.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_iniciar = QPushButton("INICIAR PARTIDA →")
        btn_iniciar.clicked.connect(self._crear_partida)
        btn_row.addWidget(btn_volver)
        btn_row.addWidget(btn_iniciar)
        lay.addLayout(btn_row)

        self.stack.addWidget(page)

    # ── Página 3: Registro de nueva cuenta ───────────────────────────────

    def _setup_registro_ui(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setSpacing(14)
        lay.setContentsMargins(40, 36, 40, 36)

        # Cabecera
        lbl_titulo = QLabel("NUEVA CUENTA")
        lbl_titulo.setStyleSheet(
            "font-size: 22px; font-weight: 900; color: #00d1ff; letter-spacing: 4px;"
        )
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_titulo)

        lbl_sub = QLabel("Crea tus credenciales de acceso al sistema")
        lbl_sub.setStyleSheet("color: #374151; font-size: 10px; letter-spacing: 1px;")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_sub)

        lay.addSpacing(10)

        # ── Campos ────────────────────────────────────────────────────────
        lbl_user = QLabel("NOMBRE DE USUARIO")
        lbl_user.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800; letter-spacing: 2px;"
        )
        lay.addWidget(lbl_user)

        self.txt_reg_user = QLineEdit()
        self.txt_reg_user.setPlaceholderText("Mínimo 3 caracteres...")
        lay.addWidget(self.txt_reg_user)

        lbl_pw = QLabel("CONTRASEÑA")
        lbl_pw.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800; letter-spacing: 2px;"
        )
        lay.addWidget(lbl_pw)

        self.txt_reg_pass = QLineEdit()
        self.txt_reg_pass.setPlaceholderText("Mínimo 6 caracteres...")
        self.txt_reg_pass.setEchoMode(QLineEdit.Password)
        lay.addWidget(self.txt_reg_pass)

        lbl_pw2 = QLabel("CONFIRMAR CONTRASEÑA")
        lbl_pw2.setStyleSheet(
            "color: #4b5563; font-size: 9px; font-weight: 800; letter-spacing: 2px;"
        )
        lay.addWidget(lbl_pw2)

        self.txt_reg_pass2 = QLineEdit()
        self.txt_reg_pass2.setPlaceholderText("Repite la contraseña...")
        self.txt_reg_pass2.setEchoMode(QLineEdit.Password)
        self.txt_reg_pass2.returnPressed.connect(self._registrar_usuario)
        lay.addWidget(self.txt_reg_pass2)

        # Mensaje de estado (errores / éxito)
        self._lbl_reg_estado = QLabel("")
        self._lbl_reg_estado.setWordWrap(True)
        self._lbl_reg_estado.setAlignment(Qt.AlignCenter)
        self._lbl_reg_estado.setStyleSheet("font-size: 10px; padding: 4px 0;")
        lay.addWidget(self._lbl_reg_estado)

        lay.addStretch()

        # Botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_volver = QPushButton("← VOLVER AL LOGIN")
        btn_volver.setObjectName("BtnSecundario")
        btn_volver.clicked.connect(self._volver_login_desde_registro)

        btn_registrar = QPushButton("CREAR CUENTA →")
        btn_registrar.clicked.connect(self._registrar_usuario)

        btn_row.addWidget(btn_volver)
        btn_row.addWidget(btn_registrar)
        lay.addLayout(btn_row)

        self.stack.addWidget(page)

    # ── Helpers de UI ─────────────────────────────────────────────────────

    def _on_modo_changed(self):
        es_extremo = self._btn_extremo.isChecked()
        self._diff_frame.setVisible(not es_extremo)
        self._extremo_frame.setVisible(es_extremo)

    _DIFF_DESCS = {
        "Fácil":     "750.000 €  ·  5 atracciones  ·  8 empleados  ·  Stock 80%\nEventos negativos reducidos al 50%",
        "Normal":    "500.000 €  ·  3 atracciones  ·  4 empleados  ·  Stock 50%\nEventos normales — dificultad recomendada",
        "Difícil":   "250.000 €  ·  1 atracción    ·  2 empleados  ·  Stock 25%\nEventos negativos +25%  ·  Umbral quiebra 400.000 €",
        "Pesadilla": "100.000 €  ·  0 atracciones  ·  0 empleados  ·  Sin stock\nEventos negativos +50%  ·  Umbral quiebra 550.000 €",
    }

    def _actualizar_desc_dificultad(self):
        label = self.combo_diff.currentText()
        self._lbl_diff_desc.setText(self._DIFF_DESCS.get(label, ""))

    def _volver_login_desde_registro(self):
        """Limpia los campos de registro y vuelve al login."""
        self.txt_reg_user.clear()
        self.txt_reg_pass.clear()
        self.txt_reg_pass2.clear()
        self._lbl_reg_estado.setText("")
        self.stack.setCurrentIndex(0)

    # ── Lógica de negocio ─────────────────────────────────────────────────

    def _intentar_login(self):
        user = UsuarioModel.get_or_none(UsuarioModel.username == self.txt_user.text())
        if user and user.verificar_password(self.txt_pass.text()):
            self._refrescar_partidas()
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")

    def _registrar_usuario(self):
        """Valida los campos y crea el usuario si todo es correcto."""
        username = self.txt_reg_user.text().strip()
        password = self.txt_reg_pass.text()
        confirm  = self.txt_reg_pass2.text()

        # Validaciones
        if len(username) < 3:
            self._mostrar_error_registro("El nombre de usuario debe tener al menos 3 caracteres.")
            return

        if len(password) < 6:
            self._mostrar_error_registro("La contraseña debe tener al menos 6 caracteres.")
            return

        if password != confirm:
            self._mostrar_error_registro("Las contraseñas no coinciden.")
            return

        if UsuarioModel.get_or_none(UsuarioModel.username == username):
            self._mostrar_error_registro(f"El usuario «{username}» ya existe.")
            return

        # Crear cuenta
        try:
            UsuarioModel.crear_usuario(username, password, "Manager")
        except Exception as exc:
            self._mostrar_error_registro(f"Error al crear la cuenta: {exc}")
            return

        # Éxito — pre-rellenar el login y redirigir
        self._lbl_reg_estado.setText("✅  ¡Cuenta creada con éxito!")
        self._lbl_reg_estado.setStyleSheet("color: #10b981; font-size: 10px; padding: 4px 0;")

        self.txt_user.setText(username)
        self.txt_pass.clear()

        # Limpiar campos de registro
        self.txt_reg_user.clear()
        self.txt_reg_pass.clear()
        self.txt_reg_pass2.clear()

        QMessageBox.information(
            self,
            "Cuenta Creada",
            f"Usuario «{username}» registrado correctamente.\n"
            "Ya puedes iniciar sesión con tus credenciales.",
        )
        self._lbl_reg_estado.setText("")
        self.stack.setCurrentIndex(0)

    def _mostrar_error_registro(self, mensaje: str):
        self._lbl_reg_estado.setText(f"⚠  {mensaje}")
        self._lbl_reg_estado.setStyleSheet(
            "color: #ef4444; font-size: 10px; padding: 4px 0;"
        )

    def _refrescar_partidas(self):
        self.lista_partidas.clear()
        self.partidas_cache = list(PartidaModel.select())
        for p in self.partidas_cache:
            modo_label = "🔥 EXTREMO" if p.modo == "extremo" else "🏗️ CAMPAÑA"
            self.lista_partidas.addItem(
                f"{p.nombre_partida}  [{modo_label} · {p.dificultad}]"
            )

    def _crear_partida(self):
        nombre = self.txt_nueva.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "Introduce un nombre para el parque.")
            return

        es_extremo  = self._btn_extremo.isChecked()
        diff_label  = self.combo_diff.currentText()
        diff_key    = _DIFF_MAP.get(diff_label, "normal")
        modo        = "extremo" if es_extremo else "campana"

        with db.atomic():
            nuevo_parque = ParqueModel.create(
                nombre     = nombre,
                dinero     = 2_000_000.0,  # se sobrescribe por el seed
                reputacion = 50.0,
            )
            nueva_p = PartidaModel.create(
                nombre_partida = nombre,
                dificultad     = diff_label if not es_extremo else "Extremo",
                modo           = modo,
                dificultad_key = diff_key if not es_extremo else "extremo",
                parque         = nuevo_parque,
            )

        # G.1/G.2: aplicar seed del modo elegido
        from models.db import seed_modo_campana, seed_modo_extremo
        if es_extremo:
            seed_modo_extremo(nuevo_parque.id)
        else:
            seed_modo_campana(nuevo_parque.id, diff_key)

        self.partida_seleccionada.emit(nueva_p)

    def _cargar_partida(self):
        idx = self.lista_partidas.currentRow()
        if idx >= 0:
            self.partida_seleccionada.emit(self.partidas_cache[idx])
        else:
            QMessageBox.information(self, "Selección", "Selecciona una partida de la lista.")
