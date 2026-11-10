from datetime import date, timedelta
from decimal import Decimal

from database.connection import consultar, transaccion


def resumen_general():
    with transaccion() as cn:
        cur = cn.cursor()
        productos = cur.execute("SELECT COUNT(*) FROM Productos").fetchone()[0]
        clientes = cur.execute("SELECT COUNT(*) FROM Clientes").fetchone()[0]
        ventas_hoy = cur.execute("""SELECT COALESCE(SUM(Total), 0) FROM Facturacion
                                    WHERE CAST(Fecha_hora AS date) = CAST(GETDATE() AS date)""").fetchone()[0]
        por_cobrar = cur.execute("SELECT COALESCE(SUM(Monto_pendiente), 0) FROM Cuenta_por_Cobrar").fetchone()[0]
        por_pagar = cur.execute("SELECT COALESCE(SUM(Monto_pendiente), 0) FROM Cuenta_por_Pagar").fetchone()[0]
    return {"productos": productos, "clientes": clientes, "ventas_hoy": ventas_hoy,
            "por_cobrar": por_cobrar, "por_pagar": por_pagar}


def ventas_ultimos_dias(dias=7):
    """[(fecha, total_vendido)] de los últimos `dias` días (con 0 en los días sin ventas)."""
    filas = consultar("""
        SELECT CAST(Fecha_hora AS date), SUM(Total) FROM Facturacion
        WHERE CAST(Fecha_hora AS date) >= DATEADD(DAY, ?, CAST(GETDATE() AS date))
        GROUP BY CAST(Fecha_hora AS date)
    """, -(dias - 1))
    por_dia = {f[0]: f[1] for f in filas}
    hoy = date.today()
    dias_lista = [hoy - timedelta(days=i) for i in range(dias - 1, -1, -1)]
    return [(d, por_dia.get(d, Decimal("0"))) for d in dias_lista]
