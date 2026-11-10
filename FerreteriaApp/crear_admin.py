from getpass import getpass

from app.modules.usuarios import crear_usuario
from database.connection import probar_conexion

if __name__ == "__main__":
    if probar_conexion():
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        ciudad = input("Ciudad (opcional): ").strip()
        usuario = input("Nombre de usuario: ").strip()
        clave = getpass("Contraseña (mínimo 8 caracteres): ")
        try:
            crear_usuario(nombre, apellido, ciudad, usuario, clave, "Administrador")
            print("Administrador creado correctamente.")
        except Exception as exc:
            print("No se pudo crear:", exc)
