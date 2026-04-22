"""
ScienceWorld Park — models/finanzas.py
Registro de todos los movimientos financieros del parque (P&L por categoría).
"""

from datetime import datetime
from peewee import CharField, FloatField, IntegerField, DateTimeField
from models.db import BaseModel


class MovimientoFinanciero(BaseModel):
    """
    Cada operación económica queda registrada aquí.
    Permite el P&L por categoría que describe el PDF §4.8.

    tipo       : 'ingreso' | 'gasto'
    categoria  : 'entradas' | 'restauracion' | 'tienda' |
                 'nominas'  | 'reparaciones' | 'logistica'
    """

    tipo       = CharField()
    categoria  = CharField()
    concepto   = CharField()
    importe    = FloatField()           # base sin IVA
    iva        = FloatField(default=0.0)
    dia_juego  = IntegerField(default=1)
    hora_juego = IntegerField(default=0)
    timestamp  = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "movimientos_financieros"

    @property
    def total(self) -> float:
        return self.importe + self.iva

    # ── Helpers de consulta ──────────────────────────────────────────────

    @classmethod
    def ingresos_dia(cls, dia: int) -> float:
        return (
            cls.select()
            .where(cls.tipo == "ingreso", cls.dia_juego == dia)
            .scalar(cls.importe.sum()) or 0.0
        )

    @classmethod
    def gastos_dia(cls, dia: int) -> float:
        return (
            cls.select()
            .where(cls.tipo == "gasto", cls.dia_juego == dia)
            .scalar(cls.importe.sum()) or 0.0
        )

    @classmethod
    def balance_dia(cls, dia: int) -> float:
        return cls.ingresos_dia(dia) - cls.gastos_dia(dia)

    @classmethod
    def resumen_por_categoria(cls, dia: int) -> dict:
        """Devuelve {categoria: {'ingresos': x, 'gastos': y}} para el día indicado."""
        rows = cls.select().where(cls.dia_juego == dia)
        resumen: dict = {}
        for row in rows:
            cat = row.categoria
            if cat not in resumen:
                resumen[cat] = {"ingresos": 0.0, "gastos": 0.0}
            if row.tipo == "ingreso":
                resumen[cat]["ingresos"] += row.importe
            else:
                resumen[cat]["gastos"] += row.importe
        return resumen

    @classmethod
    def historico_diario(cls, ultimos_n_dias: int = 7) -> list[dict]:
        """Lista [{dia, ingresos, gastos, balance}] para los últimos N días."""
        from models.parque import ParqueModel
        try:
            dia_actual = ParqueModel.get_by_id(1).dia_actual
        except Exception:
            dia_actual = 1

        resultado = []
        for d in range(max(1, dia_actual - ultimos_n_dias + 1), dia_actual + 1):
            ingresos = cls.ingresos_dia(d)
            gastos   = cls.gastos_dia(d)
            resultado.append({
                "dia":      d,
                "ingresos": ingresos,
                "gastos":   gastos,
                "balance":  ingresos - gastos,
            })
        return resultado
