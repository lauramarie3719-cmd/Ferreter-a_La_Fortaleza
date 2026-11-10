from app.modules.auditoria import registrar
from database.connection import consultar, transaccion


def listar():
    return consultar("""SELECT ID_cliente, Cedula, Nombre, Apellido, Telefono, Correo_electronico, Direccion
                        FROM Clientes ORDER BY Nombre, Apellido""")


def guardar(cedula, nombre, apellido, telefono="", correo="", direccion="",
            cliente_id=None, usuario_id=None):
    telefono, correo, direccion = telefono or None, correo or None, direccion or None
    with transaccion() as cn:
        cur = cn.cursor()
        if cur.execute("SELECT COUNT(*) FROM Clientes WHERE Cedula=? AND ID_cliente<>?",
                       cedula, cliente_id or 0).fetchone()[0]:
            raise ValueError("Ya existe un cliente con esa cédula/RNC.")
        nuevos = {"Cedula": cedula, "Nombre": f"{nombre} {apellido}"}
        if cliente_id:
            ant = cur.execute("SELECT Cedula, Nombre, Apellido FROM Clientes WHERE ID_cliente=?",
                              cliente_id).fetchone()
            cur.execute("""UPDATE Clientes SET Cedula=?, Nombre=?, Apellido=?, Telefono=?,
                           Correo_electronico=?, Direccion=? WHERE ID_cliente=?""",
                        cedula, nombre, apellido, telefono, correo, direccion, cliente_id)
            registrar(cur, usuario_id, "Clientes", "UPDATE",
                      {"Cedula": ant[0], "Nombre": f"{ant[1]} {ant[2]}"} if ant else None, nuevos)
        else:
            cur.execute("""INSERT INTO Clientes(Cedula, Nombre, Apellido, Telefono, Correo_electronico, Direccion)
                           VALUES (?,?,?,?,?,?)""", cedula, nombre, apellido, telefono, correo, direccion)
            registrar(cur, usuario_id, "Clientes", "INSERT", None, nuevos)


def eliminar(cliente_id, usuario_id=None):
    with transaccion() as cn:
        cur = cn.cursor()
        ant = cur.execute("SELECT Cedula, Nombre, Apellido FROM Clientes WHERE ID_cliente=?", cliente_id).fetchone()
        cur.execute("DELETE FROM Clientes WHERE ID_cliente=?", cliente_id)
        if ant:
            registrar(cur, usuario_id, "Clientes", "DELETE",
                      {"Cedula": ant[0], "Nombre": f"{ant[1]} {ant[2]}"}, None)


def para_venta():
    return consultar("SELECT ID_cliente, Nombre, Apellido, Cedula FROM Clientes ORDER BY Nombre, Apellido")
