from app.modules.auditoria import registrar
from database.connection import consultar, transaccion


def listar():
    return consultar("""SELECT ID_proveedor, RNC, Nombre_empresa, Telefono, Correo_electronico, Direccion
                        FROM Proveedor ORDER BY Nombre_empresa""")


def guardar(rnc, nombre_empresa, telefono="", correo="", direccion="",
            proveedor_id=None, usuario_id=None):
    telefono, correo, direccion = telefono or None, correo or None, direccion or None
    with transaccion() as cn:
        cur = cn.cursor()
        if cur.execute("SELECT COUNT(*) FROM Proveedor WHERE RNC=? AND ID_proveedor<>?",
                       rnc, proveedor_id or 0).fetchone()[0]:
            raise ValueError("Ya existe un proveedor con ese RNC.")
        nuevos = {"RNC": rnc, "Nombre_empresa": nombre_empresa}
        if proveedor_id:
            ant = cur.execute("SELECT RNC, Nombre_empresa FROM Proveedor WHERE ID_proveedor=?",
                              proveedor_id).fetchone()
            cur.execute("""UPDATE Proveedor SET RNC=?, Nombre_empresa=?, Telefono=?,
                           Correo_electronico=?, Direccion=? WHERE ID_proveedor=?""",
                        rnc, nombre_empresa, telefono, correo, direccion, proveedor_id)
            registrar(cur, usuario_id, "Proveedor", "UPDATE",
                      {"RNC": ant[0], "Nombre_empresa": ant[1]} if ant else None, nuevos)
        else:
            cur.execute("""INSERT INTO Proveedor(RNC, Nombre_empresa, Telefono, Correo_electronico, Direccion)
                           VALUES (?,?,?,?,?)""", rnc, nombre_empresa, telefono, correo, direccion)
            registrar(cur, usuario_id, "Proveedor", "INSERT", None, nuevos)


def eliminar(proveedor_id, usuario_id=None):
    with transaccion() as cn:
        cur = cn.cursor()
        ant = cur.execute("SELECT RNC, Nombre_empresa FROM Proveedor WHERE ID_proveedor=?", proveedor_id).fetchone()
        cur.execute("DELETE FROM Proveedor WHERE ID_proveedor=?", proveedor_id)
        if ant:
            registrar(cur, usuario_id, "Proveedor", "DELETE", {"RNC": ant[0], "Nombre_empresa": ant[1]}, None)
