"""
ScienceWorld Park — models/finanzas.py
Registro de todos los movimientos financieros del parque (P&L por categoría).

Correcciones aplicadas (v3.0):
 - D.8: historico_diario() reescrito con una sola query GROUP BY dia_juego, tipo.
         Antes: N*2 queries en bucle (7 días = 14 queries, 30 días = 60 queries).
         Ahora: exactamente 1 query independientemente del periodo solicitado.
"""

from datetime import datetime
from peewee import CharField, FloatField, IntegerField, DateTimeField, fn
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
    importe    = FloatField()
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
        """
        D.8: una sola query con GROUP BY dia_juego, tipo.
        Antes generaba N*2 queries en bucle (ingresos_dia + gastos_dia por cada día).
        Ahora: 1 query → acumulación en Python → lista ordenada.

        Criterio de aceptación (F.1): historico_diario(30) genera exactamente 1 query SQL.
        """
        from models.parque import ParqueModel
        try:
            dia_actual = ParqueModel.get_by_id(1).dia_actual
        except Exception:
            dia_actual = 1

        dia_inicio = max(1, dia_actual - ultimos_n_dias + 1)

        # 1 sola query: agrupa por día y tipo, suma importes
        rows = (
            cls.select(
                cls.dia_juego,
                cls.tipo,
                fn.SUM(cls.importe).alias("total"),
            )
            .where(cls.dia_juego >= dia_inicio)
            .group_by(cls.dia_juego, cls.tipo)
            .namedtuples()
        )

        # Acumular en dict {dia: {ingresos, gastos}}
        acum: dict[int, dict] = {}
        for r in rows:
            if r.dia_juego not in acum:
                acum[r.dia_juego] = {"ingresos": 0.0, "gastos": 0.0}
            clave = "ingresos" if r.tipo == "ingreso" else "gastos"
            acum[r.dia_juego][clave] = float(r.total)

        # Devolver lista ordenada con balance calculado
        return [
            {
                "dia":      dia,
                "ingresos": v["ingresos"],
                "gastos":   v["gastos"],
                "balance":  v["ingresos"] - v["gastos"],
            }
            for dia, v in sorted(acum.items())
        ]
