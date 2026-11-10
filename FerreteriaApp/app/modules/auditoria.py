from database.connection import consultar


def texto(datos):
    """Convierte un dict en 'Campo: valor, Campo: valor' (formato de tu tabla Auditoria)."""
    return ", ".join(f"{k}: {v}" for k, v in datos.items()) if datos else None


def registrar(cur, usuario_id, tabla, accion, anteriores=None, nuevos=None):
    """Guarda un registro de auditoría usando el cursor de la transacción en curso."""
    cur.execute(
        """INSERT INTO Auditoria(ID_usuario, Tabla_afectada, Accion, Datos_anteriores, Datos_nuevos)
           VALUES (?, ?, ?, ?, ?)""",
        usuario_id, tabla, accion, texto(anteriores), texto(nuevos))


def listar(limite=200):
    return consultar("""
        SELECT TOP (?) a.ID_auditoria, u.Nombre_usuario, a.Tabla_afectada, a.Accion,
               a.Datos_anteriores, a.Datos_nuevos, a.Fecha_hora
        FROM Auditoria a
        LEFT JOIN Usuarios u ON u.ID_usuario = a.ID_usuario
        ORDER BY a.Fecha_hora DESC, a.ID_auditoria DESC
    """, limite)
