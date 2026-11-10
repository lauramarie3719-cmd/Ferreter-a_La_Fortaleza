from decimal import Decimal

from app.modules.auditoria import registrar
from database.connection import consultar, transaccion

TIPOS = ("Depósito", "Retiro")


def listar():
    return consultar("""
        SELECT ID_transaccion_banco, Nombre_banco, Numero_cuenta, Tipo_movimiento, Monto,
               Referencia_bancaria, Fecha_hora
        FROM Banco ORDER BY Fecha_hora DESC, ID_transaccion_banco DESC
    """)


def registrar_movimiento(banco, cuenta, tipo, monto, referencia="", usuario_id=None):
    if tipo not in TIPOS:
        raise ValueError("El tipo debe ser Depósito o Retiro.")
    if not banco.strip() or not cuenta.strip():
        raise ValueError("Escribe el banco y el número de cuenta.")
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")
    with transaccion() as cn:
        cur = cn.cursor()
        cur.execute("""INSERT INTO Banco(Nombre_banco, Numero_cuenta, Tipo_movimiento, Monto, Referencia_bancaria)
                       VALUES (?,?,?,?,?)""", banco.strip(), cuenta.strip(), tipo, monto, referencia.strip() or None)
        registrar(cur, usuario_id, "Banco", "INSERT", None,
                  {"Tipo_movimiento": tipo, "Monto": monto, "Banco": banco.strip()})


def resumen():
    """(depósitos, retiros, balance)"""
    f = consultar("""SELECT COALESCE(SUM(CASE WHEN Tipo_movimiento = 'Depósito' THEN Monto END), 0),
                            COALESCE(SUM(CASE WHEN Tipo_movimiento = 'Retiro' THEN Monto END), 0)
                     FROM Banco""")[0]
    return f[0], f[1], f[0] - f[1]
