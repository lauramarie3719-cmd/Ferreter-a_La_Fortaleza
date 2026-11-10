import secrets

from app.modules.auditoria import registrar
from app.utils.security import crear_hash, verificar_password
from database.connection import consultar, transaccion


def autenticar(nombre_usuario, password):
    """Devuelve los datos del usuario si las credenciales son correctas, o None.

    Acepta contraseñas con hash (sal$hash). Si la contraseña guardada está en texto
    plano (datos de prueba antiguos) también la acepta y la convierte a hash.
    """
    filas = consultar("""SELECT ID_usuario, Nombre, Apellido, Nombre_usuario, [Contraseña], Rol
                         FROM Usuarios WHERE Nombre_usuario = ?""", nombre_usuario)
    if not filas:
        return None
    f = filas[0]
    guardada = f[4] or ""
    if "$" in guardada:
        valida = verificar_password(password, guardada)
    else:
        valida = secrets.compare_digest(guardada.encode("utf-8"), password.encode("utf-8"))
        if valida:
            with transaccion() as cn:
                cn.cursor().execute("UPDATE Usuarios SET [Contraseña]=? WHERE ID_usuario=?",
                                    crear_hash(password), f[0])
    if not valida:
        return None
    return {"usuario_id": f[0], "nombre": f"{f[1]} {f[2]}".strip(), "nombre_usuario": f[3],
            "rol": f[5], "requiere_cambio": False}


def listar():
    return consultar("""SELECT ID_usuario, Nombre, Apellido, Ciudad, Nombre_usuario, Rol
                        FROM Usuarios ORDER BY Nombre, Apellido""")


def _validar_password(password):
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")


def guardar(nombre, apellido, ciudad, nombre_usuario, rol, password=None,
            id_editado=None, usuario_id=None):
    ciudad = ciudad or None
    with transaccion() as cn:
        cur = cn.cursor()
        repetido = cur.execute("SELECT COUNT(*) FROM Usuarios WHERE Nombre_usuario=? AND ID_usuario<>?",
                               nombre_usuario, id_editado or 0).fetchone()[0]
        if repetido:
            raise ValueError("Ya existe un usuario con ese nombre de usuario.")
        if id_editado:
            ant = cur.execute("SELECT Nombre, Apellido, Ciudad, Nombre_usuario, Rol FROM Usuarios "
                              "WHERE ID_usuario=?", id_editado).fetchone()
            cur.execute("""UPDATE Usuarios SET Nombre=?, Apellido=?, Ciudad=?, Nombre_usuario=?, Rol=?
                           WHERE ID_usuario=?""", nombre, apellido, ciudad, nombre_usuario, rol, id_editado)
            if password:
                _validar_password(password)
                cur.execute("UPDATE Usuarios SET [Contraseña]=? WHERE ID_usuario=?",
                            crear_hash(password), id_editado)
            registrar(cur, usuario_id, "Usuarios", "UPDATE",
                      {"Nombre_usuario": ant[3], "Rol": ant[4]},
                      {"Nombre_usuario": nombre_usuario, "Rol": rol})
        else:
            _validar_password(password or "")
            cur.execute("""INSERT INTO Usuarios(Nombre, Apellido, Ciudad, Nombre_usuario, [Contraseña], Rol)
                           VALUES (?,?,?,?,?,?)""",
                        nombre, apellido, ciudad, nombre_usuario, crear_hash(password), rol)
            registrar(cur, usuario_id, "Usuarios", "INSERT", None,
                      {"Nombre_usuario": nombre_usuario, "Rol": rol})


def crear_usuario(nombre, apellido, ciudad, nombre_usuario, password, rol="Cajero", usuario_actor=None):
    guardar(nombre, apellido, ciudad, nombre_usuario, rol, password, None, usuario_actor)


def cambiar_password(usuario_id, password_nueva):
    _validar_password(password_nueva)
    with transaccion() as cn:
        cur = cn.cursor()
        cur.execute("UPDATE Usuarios SET [Contraseña]=? WHERE ID_usuario=?",
                    crear_hash(password_nueva), usuario_id)
        registrar(cur, usuario_id, "Usuarios", "UPDATE", None, {"Contraseña": "actualizada"})


def eliminar(id_editado, usuario_id=None):
    if id_editado == usuario_id:
        raise ValueError("No puedes eliminar tu propio usuario.")
    with transaccion() as cn:
        cur = cn.cursor()
        ant = cur.execute("SELECT Nombre_usuario, Rol FROM Usuarios WHERE ID_usuario=?", id_editado).fetchone()
        cur.execute("DELETE FROM Usuarios WHERE ID_usuario=?", id_editado)
        if ant:
            registrar(cur, usuario_id, "Usuarios", "DELETE",
                      {"Nombre_usuario": ant[0], "Rol": ant[1]}, None)


def registrar_acceso(usuario_id, accion):
    """Deja constancia en Auditoria de que un usuario inició o cerró sesión (LOGIN / LOGOUT)."""
    try:
        with transaccion() as cn:
            nombre = cn.cursor().execute("SELECT Nombre_usuario FROM Usuarios WHERE ID_usuario=?",
                                         usuario_id).fetchone()
            registrar(cn.cursor(), usuario_id, "Usuarios", accion, None,
                      {"Usuario": nombre[0] if nombre else usuario_id})
    except Exception:
        pass        # la auditoría de accesos nunca debe impedir entrar o salir
