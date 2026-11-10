from dataclasses import dataclass

@dataclass
class Usuario:
    usuario_id: int | None
    nombre: str
    nombre_usuario: str
    rol: str
    activo: bool = True

