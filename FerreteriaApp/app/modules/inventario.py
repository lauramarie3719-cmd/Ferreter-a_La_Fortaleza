from app.modules.auditoria import registrar
from database.connection import consultar, transaccion

# Mismos límites que usa tu vista VW_Productos_AlertaInventario
STOCK_CRITICO = 15
STOCK_BAJO = 30


def listar():
    return consultar("""
        SELECT p.ID_producto, p.Codigo_barras, p.Nombre, p.Categoria, p.Precio_compra,
               p.Precio_venta, p.Stock_actual, pr.Nombre_empresa AS Proveedor,
               p.Descripcion, p.ID_proveedor
        FROM Productos p LEFT JOIN Proveedor pr ON pr.ID_proveedor = p.ID_proveedor
        ORDER BY p.Nombre
    """)


def guardar(codigo_barras, nombre, descripcion="", categoria="", precio_compra=0,
            precio_venta=0, stock_actual=0, proveedor_id=None,
            producto_id=None, usuario_id=None):
    if float(precio_compra) < 0 or float(precio_venta) < 0 or int(stock_actual) < 0:
        raise ValueError("Los precios y el stock no pueden ser negativos.")
    codigo_barras, descripcion, categoria = codigo_barras or None, descripcion or None, categoria or None
    with transaccion() as cn:
        cur = cn.cursor()
        if codigo_barras and cur.execute(
                "SELECT COUNT(*) FROM Productos WHERE Codigo_barras=? AND ID_producto<>?",
                codigo_barras, producto_id or 0).fetchone()[0]:
            raise ValueError("Ya existe un producto con ese código de barras.")
        nuevos = {"Nombre": nombre, "Precio_venta": precio_venta}
        if producto_id:
            ant = cur.execute("SELECT Nombre, Precio_venta FROM Productos WHERE ID_producto=?",
                              producto_id).fetchone()
            cur.execute("""UPDATE Productos SET Codigo_barras=?, Nombre=?, Descripcion=?, Categoria=?,
                           Precio_compra=?, Precio_venta=?, ID_proveedor=? WHERE ID_producto=?""",
                        codigo_barras, nombre, descripcion, categoria, precio_compra,
                        precio_venta, proveedor_id, producto_id)
            registrar(cur, usuario_id, "Productos", "UPDATE",
                      {"Nombre": ant[0], "Precio_venta": ant[1]} if ant else None, nuevos)
        else:
            cur.execute("""INSERT INTO Productos(Codigo_barras, Nombre, Descripcion, ID_proveedor,
                           Precio_compra, Precio_venta, Categoria, Stock_actual)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        codigo_barras, nombre, descripcion, proveedor_id, precio_compra,
                        precio_venta, categoria, int(stock_actual))
            registrar(cur, usuario_id, "Productos", "INSERT", None,
                      {**nuevos, "Stock_actual": int(stock_actual)})


def eliminar(producto_id, usuario_id=None):
    with transaccion() as cn:
        cur = cn.cursor()
        ant = cur.execute("SELECT Nombre, Stock_actual FROM Productos WHERE ID_producto=?", producto_id).fetchone()
        cur.execute("DELETE FROM Productos WHERE ID_producto=?", producto_id)
        if ant:
            registrar(cur, usuario_id, "Productos", "DELETE",
                      {"Nombre": ant[0], "Stock_actual": ant[1]}, None)


def ajustar_existencia(producto_id, cantidad, motivo, usuario_id):
    """Suma (o resta, si es negativa) unidades al stock y deja constancia en Ajuste_Inventario."""
    cantidad = int(cantidad)
    if cantidad == 0:
        raise ValueError("El ajuste no puede ser cero.")
    if not motivo.strip():
        raise ValueError("Escribe el motivo del ajuste.")
    with transaccion() as cn:
        cur = cn.cursor()
        fila = cur.execute("SELECT Stock_actual FROM Productos WITH (UPDLOCK) WHERE ID_producto=?",
                           producto_id).fetchone()
        if not fila:
            raise ValueError("Producto no encontrado.")
        anterior = fila[0] or 0
        nuevo = anterior + cantidad
        if nuevo < 0:
            raise ValueError(f"El ajuste dejaría el stock negativo (stock actual: {anterior}).")
        cur.execute("UPDATE Productos SET Stock_actual=? WHERE ID_producto=?", nuevo, producto_id)
        cur.execute("""INSERT INTO Ajuste_Inventario(ID_producto, ID_usuario, Stock_anterior, Stock_nuevo, Motivo)
                       VALUES (?,?,?,?,?)""", producto_id, usuario_id, anterior, nuevo, motivo.strip())
        registrar(cur, usuario_id, "Productos", "UPDATE",
                  {"Stock_actual": anterior}, {"Stock_actual": nuevo})


def productos_alerta():
    """Productos con stock bajo o crítico (usa tu vista VW_Productos_AlertaInventario)."""
    return consultar("""
        SELECT Codigo_barras, Producto, Categoria, Stock_actual, Estado_Stock
        FROM VW_Productos_AlertaInventario
        WHERE Estado_Stock <> 'OK' ORDER BY Stock_actual, Producto
    """)


def para_venta():
    return consultar("""SELECT ID_producto, Codigo_barras, Nombre, Precio_venta, Stock_actual
                        FROM Productos ORDER BY Nombre""")
