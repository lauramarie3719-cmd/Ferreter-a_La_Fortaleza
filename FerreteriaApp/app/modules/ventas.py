from decimal import ROUND_HALF_UP, Decimal

from app.config import ITBIS_PORCENTAJE
from app.modules.auditoria import registrar
from database.connection import consultar, transaccion

TIPOS_PAGO = ("Efectivo", "Tarjeta", "Transferencia", "Crédito")


def calcular_totales(detalles, descuento=0):
    """Misma fórmula de tus facturas: ITBIS sobre el subtotal y Total = Subtotal + ITBIS - Descuento."""
    subtotal = sum((Decimal(str(d["cantidad"])) * Decimal(str(d["precio"])) for d in detalles),
                   Decimal("0"))
    itbis = (subtotal * Decimal(str(ITBIS_PORCENTAJE))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    descuento = Decimal(str(descuento or 0))
    return subtotal, itbis, descuento, subtotal + itbis - descuento


def registrar_venta(cliente_id, usuario_id, tipo_pago, detalles, descuento=0):
    """Registra la factura y su detalle.

    OJO: no se toca el stock ni se crea la cuenta por cobrar desde aquí, porque tus triggers
    TR_ActualizarStock_Venta y TR_GenerarCxC_FacturaCredito ya lo hacen automáticamente.
    Devuelve (id_factura, numero_factura, total).
    """
    if not detalles:
        raise ValueError("Agrega al menos un producto a la venta.")
    if tipo_pago not in TIPOS_PAGO:
        raise ValueError("Elige un tipo de pago válido.")
    if tipo_pago == "Crédito" and not cliente_id:
        raise ValueError("Una venta a crédito necesita un cliente.")
    if Decimal(str(descuento or 0)) < 0:
        raise ValueError("El descuento no puede ser negativo.")

    pedido = {}
    for d in detalles:
        cantidad = int(d["cantidad"])
        if cantidad <= 0:
            raise ValueError("Las cantidades deben ser mayores que cero.")
        pid = int(d["producto_id"])
        pedido[pid] = pedido.get(pid, 0) + cantidad

    with transaccion() as cn:
        cur = cn.cursor()
        lineas = []
        for pid, cantidad in pedido.items():
            p = cur.execute("""SELECT Nombre, Stock_actual, Precio_venta
                               FROM Productos WITH (UPDLOCK, ROWLOCK) WHERE ID_producto=?""", pid).fetchone()
            if not p:
                raise ValueError("Uno de los productos de la venta ya no existe.")
            if (p[1] or 0) < cantidad:
                raise ValueError(f"Existencia insuficiente de «{p[0]}» (disponible: {p[1] or 0}).")
            lineas.append({"producto_id": pid, "cantidad": cantidad, "precio": p[2]})

        subtotal, itbis, descuento, total = calcular_totales(lineas, descuento)
        if total < 0:
            raise ValueError("El descuento no puede ser mayor que el total de la venta.")

        siguiente = cur.execute("SELECT ISNULL(MAX(ID_factura), 0) + 1 FROM Facturacion").fetchone()[0]
        while True:
            numero = f"B01{siguiente:08d}"
            if not cur.execute("SELECT 1 FROM Facturacion WHERE Numero_factura=?", numero).fetchone():
                break
            siguiente += 1

        cur.execute("""INSERT INTO Facturacion(Numero_factura, ID_cliente, ID_usuario, Subtotal, ITBIS,
                       Descuento, Total, Tipo_pago) VALUES (?,?,?,?,?,?,?,?)""",
                    numero, cliente_id, usuario_id, subtotal, itbis, descuento, total, tipo_pago)
        factura_id = cur.execute("SELECT ID_factura FROM Facturacion WHERE Numero_factura=?",
                                 numero).fetchone()[0]
        for l in lineas:
            cur.execute("""INSERT INTO Detalle_Venta(ID_factura, ID_producto, Cantidad, Precio_unitario)
                           VALUES (?,?,?,?)""", factura_id, l["producto_id"], l["cantidad"], l["precio"])
        registrar(cur, usuario_id, "Facturacion", "INSERT", None,
                  {"Numero_factura": numero, "Total": total, "Tipo_pago": tipo_pago})
    return factura_id, numero, total


def listar_facturas():
    return consultar("""
        SELECT f.ID_factura, f.Numero_factura, f.Fecha_hora,
               NULLIF(LTRIM(RTRIM(CONCAT(c.Nombre, ' ', c.Apellido))), '') AS Cliente,
               u.Nombre_usuario, f.Tipo_pago, f.Subtotal, f.ITBIS, f.Descuento, f.Total
        FROM Facturacion f
        LEFT JOIN Clientes c ON c.ID_cliente = f.ID_cliente
        LEFT JOIN Usuarios u ON u.ID_usuario = f.ID_usuario
        ORDER BY f.Fecha_hora DESC, f.ID_factura DESC
    """)


def detalle_factura(factura_id):
    return consultar("""
        SELECT p.Nombre, d.Cantidad, d.Precio_unitario
        FROM Detalle_Venta d LEFT JOIN Productos p ON p.ID_producto = d.ID_producto
        WHERE d.ID_factura = ? ORDER BY d.ID_detalle
    """, factura_id)


def datos_factura(factura_id):
    """Todo lo necesario para imprimir una factura completa."""
    filas = consultar("""
        SELECT f.Numero_factura, f.Fecha_hora,
               NULLIF(LTRIM(RTRIM(CONCAT(c.Nombre, ' ', c.Apellido))), ''), c.Cedula, c.Telefono,
               c.Direccion, c.Correo_electronico,
               NULLIF(LTRIM(RTRIM(CONCAT(u.Nombre, ' ', u.Apellido))), ''), u.Rol,
               f.Tipo_pago, f.Subtotal, f.ITBIS, f.Descuento, f.Total,
               cc.Monto_pendiente, cc.Fecha_vencimiento, f.ID_factura
        FROM Facturacion f
        LEFT JOIN Clientes c ON c.ID_cliente = f.ID_cliente
        LEFT JOIN Usuarios u ON u.ID_usuario = f.ID_usuario
        LEFT JOIN Cuenta_por_Cobrar cc ON cc.ID_factura = f.ID_factura
        WHERE f.ID_factura = ?
    """, factura_id)
    if not filas:
        raise ValueError("Factura no encontrada.")
    h = filas[0]
    lineas = consultar("""
        SELECT p.Codigo_barras, p.Nombre, p.Categoria, d.Cantidad, d.Precio_unitario
        FROM Detalle_Venta d LEFT JOIN Productos p ON p.ID_producto = d.ID_producto
        WHERE d.ID_factura = ? ORDER BY d.ID_detalle
    """, factura_id)
    return {"numero": h[0], "fecha": h[1], "cliente": h[2] or "Consumidor final",
            "cedula": h[3] or "", "telefono": h[4] or "", "direccion": h[5] or "", "correo": h[6] or "",
            "vendedor": h[7] or "", "rol_vendedor": h[8] or "", "tipo_pago": h[9],
            "subtotal": h[10], "itbis": h[11], "descuento": h[12], "total": h[13],
            "pendiente": h[14], "vence": h[15], "id": h[16],
            "lineas": [(c or "", n or "(producto eliminado)", cat or "", cant, precio)
                       for c, n, cat, cant, precio in lineas]}
