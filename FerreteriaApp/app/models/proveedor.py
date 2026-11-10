from dataclasses import dataclass

@dataclass
class Proveedor:
    proveedor_id: int | None
    nombre: str
    rnc: str = ""
    telefono: str = ""
    correo: str = ""
    direccion: str = ""
