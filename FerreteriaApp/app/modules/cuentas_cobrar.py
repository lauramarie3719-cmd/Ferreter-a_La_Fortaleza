from decimal import Decimal

from app.modules.auditoria import registrar
from database.connection import consultar, transaccion


def listar():
    return consultar("""
        SELECT cc.ID_cxc, f.Numero_factura,
               NULLIF(LTRIM(RTRIM(CONCAT(c.Nombre, ' ', c.Apellido))), '') AS Cliente,
               cc.Monto_inicial, cc.Monto_pendiente,
               CASE WHEN cc.Monto_pendiente <= 0 THEN 'Pagada' ELSE 'Pendiente' END AS Estado,
               cc.Fecha_emision, cc.Fecha_vencimiento
        FROM Cuenta_por_Cobrar cc
        LEFT JOIN Facturacion f ON f.ID_factura = cc.ID_factura
        LEFT JOIN Clientes c ON c.ID_cliente = cc.ID_cliente
        ORDER BY cc.ID_cxc DESC
    """)


def registrar_abono(cxc_id, monto, usuario_id):
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValueError("El abono debe ser mayor que cero.")
    with transaccion() as cn:
        cur = cn.cursor()
        fila = cur.execute("SELECT Monto_pendiente FROM Cuenta_por_Cobrar WITH (UPDLOCK) WHERE ID_cxc=?",
                           cxc_id).fetchone()
        if not fila:
            raise ValueError("Cuenta no encontrada.")
        if monto > fila[0]:
            raise ValueError(f"El abono no puede ser mayor que el saldo pendiente ({fila[0]:,.2f}).")
        nuevo = fila[0] - monto
        cur.execute("UPDATE Cuenta_por_Cobrar SET Monto_pendiente=? WHERE ID_cxc=?", nuevo, cxc_id)
        registrar(cur, usuario_id, "Cuenta_por_Cobrar", "UPDATE",
                  {"Monto_pendiente": fila[0]}, {"Monto_pendiente": nuevo})
