"""
Jerarquía de excepciones personalizadas para ScienceWorld Park.
"""

class ScienceWorldError(Exception):
    """Raíz de todas las excepciones del sistema."""
    pass

# --- Atracciones ---
class AtraccionError(ScienceWorldError):
    """Errores relacionados con las atracciones."""
    pass

class AforoCompletoError(AtraccionError):
    """La cola o el aforo de la atracción está lleno."""
    pass

class AtraccionCerradaError(AtraccionError):
    """La atracción no está operativa."""
    pass

class AlturaInsuficienteError(AtraccionError):
    """El visitante no cumple los requisitos físicos."""
    pass

# --- Finanzas ---
class FinanzasError(ScienceWorldError):
    """Errores relacionados con la economía del parque."""
    pass

class SaldoInsuficienteError(FinanzasError):
    """No hay fondos suficientes para la operación."""
    pass

class LimiteCreditoError(FinanzasError):
    """Se ha superado el límite de crédito bancario."""
    pass

class TransaccionError(FinanzasError):
    """Fallo al persistir un movimiento contable."""
    pass

# --- Personal ---
class PersonalError(ScienceWorldError):
    """Errores relacionados con la gestión de empleados."""
    pass

class EmpleadoNoDisponibleError(PersonalError):
    """No hay empleados libres con el perfil requerido."""
    pass

class NominaError(PersonalError):
    """Error en el cálculo o pago de salarios."""
    pass

# --- Logística ---
class LogisticaError(ScienceWorldError):
    """Errores relacionados con el inventario y suministros."""
    pass

class StockInsuficienteError(LogisticaError):
    """No hay unidades disponibles de un producto."""
    pass

class ProveedorNoDisponibleError(LogisticaError):
    """Fallo en la comunicación o pedido al proveedor."""
    pass

# --- Taquilla ---
class TaquillaError(ScienceWorldError):
    """Errores en la venta y validación de entradas."""
    pass

class LocalizadorDuplicadoError(TaquillaError):
    """El código de ticket generado ya existe."""
    pass

class EntradaYaUsadaError(TaquillaError):
    """El ticket ya ha sido validado previamente."""
    pass

# --- Base de Datos ---
class BaseDatosError(ScienceWorldError):
    """Errores de persistencia."""
    pass

class ConexionBDError(BaseDatosError):
    """No se pudo establecer conexión con SQLite."""
    pass