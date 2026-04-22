"""
ScienceWorld Park — models/inventario.py
Gestión de existencias: ScienceFood y ScienceStore.
"""

from peewee import CharField, FloatField
from models.db import BaseModel, db
from core.logger import log


class InventarioModel(BaseModel):
    nombre        = CharField(unique=True)
    categoria     = CharField()          # Comida | Souvenir | Repuesto
    stock_actual  = FloatField(default=0.0)
    stock_minimo  = FloatField(default=10.0)
    stock_maximo  = FloatField(default=500.0)
    precio_compra = FloatField(default=0.0)

    class Meta:
        table_name = "inventario"

    # ── Operaciones de stock ─────────────────────────────────────────────

    @classmethod
    def reducir_stock(cls, nombre: str, cantidad: float) -> bool:
        """Resta *cantidad* si hay suficiente. Devuelve True si éxito."""
        item = cls.get_or_none(cls.nombre == nombre)
        if item and item.stock_actual >= cantidad:
            item.stock_actual -= cantidad
            item.save()
            return True
        return False

    @classmethod
    def comprar_stock(
        cls,
        nombre: str,
        cantidad: int,
        coste_total: float,
        parque_id: int = None,
    ) -> bool:
        """
        Transacción atómica: descuenta dinero del parque y suma stock.
        Respeta el stock_maximo definido.
        """
        from models.parque import ParqueModel
        from core.motor    import MotorSimulacion
        from models.finanzas import MovimientoFinanciero

        # Resolver parque_id dinámicamente
        if parque_id is None:
            parque_id = MotorSimulacion()._parque_id

        try:
            with db.atomic():
                item   = cls.get_or_none(cls.nombre == nombre)
                parque = ParqueModel.get_by_id(parque_id)

                if not item or parque.dinero < coste_total:
                    return False

                parque.dinero    -= coste_total
                item.stock_actual = min(
                    item.stock_maximo,
                    item.stock_actual + cantidad,
                )
                item.save()
                parque.save()

                # Registrar movimiento financiero
                try:
                    MovimientoFinanciero.create(
                        tipo       = "gasto",
                        categoria  = "logistica",
                        concepto   = f"Pedido {cantidad} uds de {nombre}",
                        importe    = coste_total,
                        iva        = 0.0,
                        dia_juego  = parque.dia_actual,
                        hora_juego = parque.hora_actual,
                    )
                except Exception:
                    pass  # No crítico si falla el registro

                log.info(
                    f"Logística: Compra de {cantidad} uds de {nombre} "
                    f"por ${coste_total:,.2f}"
                )
                return True

        except Exception as exc:
            log.error(f"Error en transacción de compra: {exc}")
            return False
