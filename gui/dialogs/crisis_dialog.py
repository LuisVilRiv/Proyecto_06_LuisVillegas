"""
ScienceWorld Park — gui/dialogs/crisis_dialog.py
Diálogos de Decisión Crítica para eventos narrativos (PDF §4.3 + §5).
"""

from dataclasses import dataclass
from typing import Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Qt


# ── Modelo de opción ────────────────────────────────────────────────────────

@dataclass
class Opcion:
    etiqueta:    str            # Texto principal del botón
    efecto_desc: str            # Subtexto descriptivo del impacto
    callback:    Callable       # Función que aplica el efecto al parque


# ── Diálogo ─────────────────────────────────────────────────────────────────

class CrisisDialog(QDialog):
    """
    Ventana modal de 'Decisión Crítica' que interrumpe el juego
    y fuerza al jugador a elegir una de varias opciones con consecuencias.
    """

    def __init__(
        self,
        parent,
        titulo:      str,
        descripcion: str,
        opciones:    list[Opcion],
        emoji:       str = "⚠️",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Crisis — {titulo}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )

        self._aplicar_estilo()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 28)
        layout.setSpacing(16)

        # ── Cabecera ──────────────────────────────────────────────────────
        lbl_ico = QLabel(emoji)
        lbl_ico.setAlignment(Qt.AlignCenter)
        lbl_ico.setStyleSheet("font-size: 52px; background: transparent;")
        layout.addWidget(lbl_ico)

        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #ef4444;"
            "letter-spacing: 2px; background: transparent;"
        )
        layout.addWidget(lbl_titulo)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #1f2937; background: #1f2937; max-height: 1px;")
        layout.addWidget(sep)

        # ── Descripción ───────────────────────────────────────────────────
        lbl_desc = QLabel(descripcion)
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setStyleSheet(
            "color: #9ca3af; font-size: 13px; padding: 8px 0;"
            "background: transparent;"
        )
        layout.addWidget(lbl_desc)

        lbl_prompt = QLabel("¿CUÁL ES TU DECISIÓN?")
        lbl_prompt.setAlignment(Qt.AlignCenter)
        lbl_prompt.setStyleSheet(
            "color: #00d1ff; font-size: 10px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )
        layout.addWidget(lbl_prompt)

        # ── Opciones ──────────────────────────────────────────────────────
        for i, opcion in enumerate(opciones):
            btn = self._crear_boton_opcion(opcion, i)
            layout.addWidget(btn)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _crear_boton_opcion(self, opcion: Opcion, idx: int) -> QPushButton:
        btn = QPushButton()
        btn.setMinimumHeight(64)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setText(f"  {opcion.etiqueta}\n  → {opcion.efecto_desc}")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #d1d5db;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 12px 18px;
                text-align: left;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1f2937;
                color: #ffffff;
                border-color: #00d1ff;
            }
            QPushButton:pressed {
                background-color: rgba(0, 209, 255, 0.15);
            }
        """)
        btn.clicked.connect(lambda: self._confirmar(opcion))
        return btn

    def _confirmar(self, opcion: Opcion) -> None:
        opcion.callback()
        self.accept()

    def _aplicar_estilo(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0d18;
                border: 1px solid #1f2937;
                border-radius: 12px;
            }
        """)


# ── Fábrica de crisis predefinidas ──────────────────────────────────────────

def crisis_accidente(parent, toast_manager=None) -> CrisisDialog:
    """Crea el diálogo de crisis para un accidente con visitante."""

    def pagar_compensacion():
        from models.parque import ParqueModel
        from core.motor import MotorSimulacion
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        parque.dinero     -= 50_000
        parque.reputacion  = min(100.0, parque.reputacion + 5.0)
        parque.save()
        if toast_manager:
            toast_manager.show(
                "Compensación Pagada",
                "50.000€ abonados. Reputación parcialmente recuperada.",
                "warning",
            )

    def declaracion_publica():
        from models.parque import ParqueModel
        from core.motor import MotorSimulacion
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        parque.reputacion = min(100.0, parque.reputacion + 2.0)
        parque.save()
        if toast_manager:
            toast_manager.show(
                "Declaración Emitida",
                "La prensa cubre el comunicado. Reputación +2.",
                "info",
            )

    def cierre_preventivo():
        from models.atracciones import AtraccionModel
        import random
        atrs = list(AtraccionModel.select().where(AtraccionModel.activo == True))
        if atrs:
            target = random.choice(atrs)
            target.en_mantenimiento = True
            target.save()
        if toast_manager:
            toast_manager.show(
                "Sección Cerrada",
                "Cierre preventivo activado. Ingresos reducidos 24h.",
                "error",
            )

    return CrisisDialog(
        parent,
        "Accidente con Visitante",
        (
            "Se ha reportado un incidente grave en el parque. "
            "Las autoridades están investigando. Reputación en riesgo."
        ),
        [
            Opcion("Pagar compensación urgente (50.000€)",
                   "Reputación +5 · Coste inmediato", pagar_compensacion),
            Opcion("Emitir declaración pública de transparencia",
                   "Reputación +2 · Sin coste", declaracion_publica),
            Opcion("Cierre preventivo de atracción (24h)",
                   "Evita multa regulatoria · Pérdida de ingresos", cierre_preventivo),
        ],
        "🚨",
    )


def crisis_huelga(parent, toast_manager=None) -> CrisisDialog:
    """Crea el diálogo de crisis para una huelga de personal."""

    def subir_salarios():
        from models.empleados import EmpleadoModel
        from models.parque    import ParqueModel
        from core.motor       import MotorSimulacion
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        parque.dinero -= 30_000
        parque.save()
        EmpleadoModel.update(
            {EmpleadoModel.salario_mes: EmpleadoModel.salario_mes * 1.10}
        ).execute()
        if toast_manager:
            toast_manager.show(
                "Acuerdo Salarial",
                "+10% salarios. Huelga resuelta. Coste 30.000€.",
                "success",
            )

    def negociar():
        from models.parque import ParqueModel
        from core.motor    import MotorSimulacion
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        parque.reputacion = max(0.0, parque.reputacion - 3.0)
        parque.save()
        if toast_manager:
            toast_manager.show(
                "Negociación en Curso",
                "La huelga continúa. Reputación -3.",
                "warning",
            )

    def despedir_huelguistas():
        from models.parque import ParqueModel
        from core.motor    import MotorSimulacion
        parque = ParqueModel.get_by_id(MotorSimulacion()._parque_id)
        parque.reputacion = max(0.0, parque.reputacion - 8.0)
        parque.save()
        if toast_manager:
            toast_manager.show(
                "Despidos Ejecutados",
                "Personal hostelería reducido. Reputación -8. Servicio degradado.",
                "error",
            )

    return CrisisDialog(
        parent,
        "Huelga de Personal",
        (
            "El sindicato de hostelería ha convocado huelga indefinida. "
            "Los restaurantes operan al 20% de capacidad."
        ),
        [
            Opcion("Aceptar subida salarial del 10% (30.000€)",
                   "Huelga resuelta · Costes permanentes +10%", subir_salarios),
            Opcion("Abrir mesa de negociación",
                   "Huelga continúa 24h más · Reputación -3", negociar),
            Opcion("Despedir al personal en huelga",
                   "Huelga termina · Reputación -8 · Capacidad reducida", despedir_huelguistas),
        ],
        "🪧",
    )
