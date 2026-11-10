
from database.connection import conectar

try:
    conexion = conectar()
    cursor = conexion.cursor()

    print("\nCONEXION EXITOSA CON SQL SERVER")

    # Mostrar todas las tablas
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)

    tablas = cursor.fetchall()

    for tabla in tablas:
        nombre = tabla[0]

        print("\n" + "=" * 50)
        print("TABLA:", nombre)
        print("=" * 50)

        # Consultar todos los datos de la tabla
        cursor.execute(f"SELECT * FROM [{nombre}]")

        columnas = [col[0] for col in cursor.description]
        filas = cursor.fetchall()

        print(" | ".join(columnas))

        for fila in filas:
            print(" | ".join(str(dato) if dato is not None else "NULL"
                              for dato in fila))

        if not filas:
            print("Esta tabla no tiene registros.")

    conexion.close()

except Exception as error:
    print("ERROR:", error)
