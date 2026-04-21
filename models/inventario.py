from peewee import CharField, FloatField
from models.db import BaseModel, db
from core.logger import log

class InventarioModel(BaseModel):
    """Gestión de existencias para ScienceFood y ScienceStore."""
    nombre = CharField(unique=True)
    categoria = CharField()  # Comida, Souvenir, Repuesto
    stock_actual = FloatField(default=0.0)
    stock_minimo = FloatField(default=10.0)
    stock_maximo = FloatField(default=500.0)
    precio_compra = FloatField(default=0.0)

    class Meta:
        table_name = 'inventario'

    @classmethod
    def reducir_stock(cls, nombre: str, cantidad: float) -> bool:
        """Resta stock si existe y hay cantidad. Devuelve éxito."""
        item = cls.get_or_none(cls.nombre == nombre)
        if item and item.stock_actual >= cantidad:
            item.stock_actual -= cantidad
            item.save()
            return True
        return False

    @classmethod
    def comprar_stock(cls, nombre: str, cantidad: int, coste_total: float) -> bool:
        """
        Operación atómica: resta dinero del parque y suma stock.
        Valida que no se supere el stock_maximo.
        """
        from models.parque import ParqueModel
        try:
            with db.atomic():
                item = cls.get_or_none(cls.nombre == nombre)
                parque = ParqueModel.get_by_id(1)
                
                if not item or parque.dinero < coste_total:
                    return False
                
                # Ejecutar transacción
                parque.dinero -= coste_total
                # Limitar al máximo definido en diseño
                nuevo_stock = item.stock_actual + cantidad
                item.stock_actual = min(item.stock_maximo, nuevo_stock)
                
                item.save()
                parque.save()
                
                log.info(f"Logística: Compra de {cantidad} uds de {nombre} por ${coste_total:,.2f}")
                return True
        except Exception as e:
            log.error(f"Error en transacción de compra: {e}")
            return False