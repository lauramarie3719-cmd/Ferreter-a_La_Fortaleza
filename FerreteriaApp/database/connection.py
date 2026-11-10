from contextlib import contextmanager

import pyodbc

from app.config import (DB_DRIVER, DB_NAME, DB_PASSWORD, DB_SERVER, DB_USUARIO)


class ErrorConexion(Exception):
    """No se pudo abrir la conexión con SQL Server."""


def _elegir_driver():
    instalados = pyodbc.drivers()
    if DB_DRIVER in instalados:
        return DB_DRIVER
    for preferido in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server",
                      "ODBC Driver 13 for SQL Server", "SQL Server Native Client 11.0",
                      "SQL Server"):
        if preferido in instalados:
            return preferido
    raise ErrorConexion("No hay ningún driver ODBC de SQL Server instalado.\n"
                        "Instala «ODBC Driver 17 for SQL Server» (gratis, de Microsoft).")


def conectar():
    """Abre una conexión nueva. Lanza ErrorConexion si no se puede."""
    cadena = (f"DRIVER={{{_elegir_driver()}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
              "TrustServerCertificate=yes;")
    cadena += (f"UID={DB_USUARIO};PWD={DB_PASSWORD};" if DB_USUARIO
               else "Trusted_Connection=yes;")
    try:
        return pyodbc.connect(cadena, timeout=10)
    except pyodbc.Error as exc:
        detalle = str(exc.args[-1] if exc.args else exc).split("[SQL Server]")[-1][:250]
        raise ErrorConexion(f"No se pudo conectar a SQL Server (servidor «{DB_SERVER}», "
                            f"base «{DB_NAME}»).\n{detalle}")


@contextmanager
def transaccion():
    """Conexión con commit automático si todo sale bien y rollback si hay error."""
    cn = conectar()
    try:
        yield cn
        cn.commit()
    except Exception:
        cn.rollback()
        raise
    finally:
        cn.close()


def consultar(sql, *params):
    """Ejecuta un SELECT y devuelve todas las filas."""
    with transaccion() as cn:
        return cn.cursor().execute(sql, *params).fetchall()


def probar_conexion():
    try:
        cn = conectar()
    except ErrorConexion as exc:
        print(exc)
        return False
    cn.close()
    print("Conexión con SQL Server correcta.")
    return True
