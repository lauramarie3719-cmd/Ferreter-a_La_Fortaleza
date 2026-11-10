from decimal import Decimal

from app.modules.auditoria import registrar
from database.connection import consultar, transaccion


def listar():
    return consultar("""
        SELECT cp.ID_cxp, p.Nombre_empresa, cp.Monto_total, cp.Monto_pendiente,
               CASE WHEN cp.Monto_pendiente <= 0 THEN 'Pagada' ELSE 'Pendiente' END AS Estado,
               cp.Fecha_registro, cp.Fecha_vencimiento
        FROM Cuenta_por_Pagar cp
        LEFT JOIN Proveedor p ON p.ID_proveedor = cp.ID_proveedor
        ORDER BY cp.ID_cxp DESC
    """)


def crear_cuenta(proveedor_id, monto, fecha_vencimiento=None, usuario_id=None):
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")
    with transaccion() as cn:
        cur = cn.cursor()
        cur.execute("""INSERT INTO Cuenta_por_Pagar(ID_proveedor, Monto_total, Monto_pendiente, Fecha_vencimiento)
                       VALUES (?,?,?,?)""", proveedor_id, monto, monto, fecha_vencimiento)
        registrar(cur, usuario_id, "Cuenta_por_Pagar", "INSERT", None,
                  {"ID_proveedor": proveedor_id, "Monto_total": monto})


def pagar(cxp_id, monto, usuario_id):
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValueError("El pago debe ser mayor que cero.")
    with transaccion() as cn:
        cur = cn.cursor()
        fila = cur.execute("SELECT Monto_pendiente FROM Cuenta_por_Pagar WITH (UPDLOCK) WHERE ID_cxp=?",
                           cxp_id).fetchone()
        if not fila:
            raise ValueError("Cuenta no encontrada.")
        if monto > fila[0]:
            raise ValueError(f"El pago no puede ser mayor que el saldo pendiente ({fila[0]:,.2f}).")
        nuevo = fila[0] - monto
        cur.execute("UPDATE Cuenta_por_Pagar SET Monto_pendiente=? WHERE ID_cxp=?", nuevo, cxp_id)
        registrar(cur, usuario_id, "Cuenta_por_Pagar", "UPDATE",
                  {"Monto_pendiente": fila[0]}, {"Monto_pendiente": nuevo})
