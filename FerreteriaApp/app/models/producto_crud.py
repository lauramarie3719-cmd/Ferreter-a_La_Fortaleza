
from database.connection import conectar


class ProductoCRUD:

    # REGISTRAR PRODUCTO (CREATE)
    @staticmethod
    def crear(producto):
        if not producto.nombre.strip():
            print("El nombre del producto es obligatorio.")
            return False

        if producto.precio_compra < 0 or producto.precio_venta < 0:
            print("Los precios no pueden ser negativos.")
            return False

        if producto.stock_actual < 0:
            print("La existencia no puede ser negativa.")
            return False

        conexion = conectar()

        if conexion is None:
            return False

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO Productos
                (Codigo_barras, Nombre, Descripcion, ID_proveedor,
                 Precio_compra, Precio_venta, Categoria, Stock_actual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                producto.codigo_barras or None,
                producto.nombre,
                producto.descripcion or None,
                producto.id_proveedor,
                producto.precio_compra,
                producto.precio_venta,
                producto.categoria or None,
                producto.stock_actual
            ))

            conexion.commit()
            print("Producto registrado correctamente.")
            return True

        except Exception as error:
            conexion.rollback()
            print("Error al registrar:", error)
            return False

        finally:
            conexion.close()

    # CONSULTAR PRODUCTOS (READ)
    @staticmethod
    def consultar():
        conexion = conectar()

        if conexion is None:
            return []

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT ID_producto, Codigo_barras, Nombre, Descripcion,
                       ID_proveedor, Precio_compra, Precio_venta,
                       Categoria, Stock_actual
                FROM Productos
            """)

            productos = cursor.fetchall()

            for producto in productos:
                print(producto)

            return productos

        except Exception as error:
            print("Error al consultar:", error)
            return []

        finally:
            conexion.close()

    # MODIFICAR PRODUCTO (UPDATE)
    @staticmethod
    def actualizar(producto):
        if producto.id_producto is None:
            print("Debes indicar el ID del producto.")
            return False

        if not producto.nombre.strip():
            print("El nombre del producto es obligatorio.")
            return False

        if producto.precio_compra < 0 or producto.precio_venta < 0:
            print("Los precios no pueden ser negativos.")
            return False

        if producto.stock_actual < 0:
            print("La existencia no puede ser negativa.")
            return False

        conexion = conectar()

        if conexion is None:
            return False

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                UPDATE Productos
                SET Codigo_barras = ?,
                    Nombre = ?,
                    Descripcion = ?,
                    ID_proveedor = ?,
                    Precio_compra = ?,
                    Precio_venta = ?,
                    Categoria = ?,
                    Stock_actual = ?
                WHERE ID_producto = ?
            """, (
                producto.codigo_barras or None,
                producto.nombre,
                producto.descripcion or None,
                producto.id_proveedor,
                producto.precio_compra,
                producto.precio_venta,
                producto.categoria or None,
                producto.stock_actual,
                producto.id_producto
            ))

            conexion.commit()

            if cursor.rowcount > 0:
                print("Producto actualizado correctamente.")
                return True

            print("No se encontró el producto.")
            return False

        except Exception as error:
            conexion.rollback()
            print("Error al actualizar:", error)
            return False

        finally:
            conexion.close()

    # ELIMINAR PRODUCTO (DELETE)
    @staticmethod
    def eliminar(id_producto):
        if id_producto is None:
            print("Debes indicar el ID del producto.")
            return False

        conexion = conectar()

        if conexion is None:
            return False

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                DELETE FROM Productos
                WHERE ID_producto = ?
            """, (id_producto,))

            conexion.commit()

            if cursor.rowcount > 0:
                print("Producto eliminado correctamente.")
                return True

            print("No se encontró el producto.")
            return False

        except Exception as error:
            conexion.rollback()
            print("Error al eliminar:", error)
            return False

        finally:
            conexion.close()
