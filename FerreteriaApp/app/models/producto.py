
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Producto:
    id_producto: int | None = None
    codigo_barras: str = ""
    nombre: str = ""
    descripcion: str = ""
    id_proveedor: int | None = None
    precio_compra: Decimal = Decimal("0.00")
    precio_venta: Decimal = Decimal("0.00")
    categoria: str = ""
    stock_actual: int = 0
