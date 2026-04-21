import random
from PySide6.QtCore import QObject, Signal
from core.logger import log
from models.parque import ParqueModel
from models.atracciones import AtraccionModel
from models.inventario import InventarioModel
from models.db import db

class MotorSignals(QObject):
    evento_critico = Signal(str, str)
    tick_completado = Signal()

class MotorSimulacion:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MotorSimulacion, cls).__new__(cls)
            cls._instance.signals = MotorSignals()
        return cls._instance

    def ejecutar_tick(self):
        """Ciclo de simulación de 1 hora con consumo determinista de stock."""
        try:
            with db.atomic():
                self.parque_db = ParqueModel.get_by_id(1)
                self.parque_db.hora_actual += 1
                if self.parque_db.hora_actual >= 24:
                    self.parque_db.hora_actual = 0
                    self.parque_db.dia_actual += 1

                # 1. Simulación de Visitantes
                num_visitantes = int(self.parque_db.reputacion * random.uniform(3.0, 6.0))
                
                # 2. Lógica de Consumo de Productos
                for _ in range(num_visitantes):
                    if random.random() < 0.25: # 25% prob. de querer consumir
                        producto = "Comida Espacial" if random.random() > 0.4 else "Newton Peluche"
                        
                        # Intentar vender (Resta stock manual del jugador)
                        if InventarioModel.reducir_stock(producto, 1):
                            # Venta exitosa: Ingreso para el parque
                            precio_venta = 20.0 if producto == "Comida Espacial" else 35.0
                            self.parque_db.dinero += precio_venta
                        else:
                            # Venta fallida por falta de suministros
                            log.warning(f"VENTA PERDIDA: Sin stock de {producto}.")
                            # Penalización leve en reputación por mal servicio
                            self.parque_db.reputacion = max(0.0, self.parque_db.reputacion - 0.05)

                # 3. Desgaste de Atracciones
                for atr in AtraccionModel.select():
                    dom = atr.to_domain()
                    dom.degradar(random.uniform(0.3, 0.9))
                    AtraccionModel.from_domain(dom)

                self.parque_db.save()
                self.signals.tick_completado.emit()
                
        except Exception as e:
            log.error(f"Fallo en motor durante tick: {e}")
            raise e