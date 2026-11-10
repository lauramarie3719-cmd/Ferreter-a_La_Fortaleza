from dataclasses import dataclass
from decimal import Decimal

@dataclass
class DetalleVenta:
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")

@dataclass
class Factura:
    cliente_id: int | None
    usuario_id: int
    tipo_pago: str
    detalles: list
    descuento: Decimal = Decimal("0")
