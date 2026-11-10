from dataclasses import dataclass

@dataclass
class Cliente:
    cliente_id: int | None
    nombre: str
    telefono: str = ""
    correo: str = ""
    direccion: str = ""
    limite_credito: float = 0
