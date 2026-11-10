"""Definición de cada pantalla del sistema: formularios, tablas y acciones."""
from datetime import datetime
from tkinter import messagebox

from app.modules import (auditoria, banco, clientes, cuentas_cobrar, cuentas_pagar,
                         inventario, proveedores, usuarios, ventas)
from app.ui import theme as t
from app.modules.factura_pdf import generar_factura_pdf
from app.ui.helpers import abrir_archivo, dinero, mensaje_error, pedir_datos
from app.ui.vista_crud import VistaCRUD
from app.ui.vista_lista import VistaLista
from app.ui.vista_resumen import VistaResumen
from app.ui.vista_venta import VistaVenta
from app.utils.validators import decimal_positivo

TEL = dict(patron=r"[0-9+\-\s()]{7,20}", error="El teléfono solo admite números, +, - y paréntesis (7 a 20 caracteres).")
CORREO = dict(patron=r"[^@\s]+@[^@\s]+\.[^@\s]+", error="El correo no tiene un formato válido (ejemplo@correo.com).")


def _monto(texto, nombre):
    return decimal_positivo(texto.replace(",", ""), nombre)


# ------------------------------------------------------------ Formularios CRUD
def _spec_clientes():
    return dict(
        titulo_excel="Clientes",
        titulo_singular="cliente", id_param="cliente_id",
        listar=clientes.listar, guardar=clientes.guardar, eliminar=clientes.eliminar,
        columnas=[("cliente_id", "ID", 50, "center"), ("cedula", "Cédula / RNC", 120, "w"),
                  ("nombre", "Nombre", 120, "w"), ("apellido", "Apellido", 120, "w"),
                  ("telefono", "Teléfono", 110, "w"), ("correo", "Correo", 170, "w"),
                  ("direccion", "Dirección", 190, "w")],
        campos=[dict(key="cedula", label="Cédula / RNC", tipo="texto", obligatorio=True, mitad=True, max=20,
                     patron=r"[0-9\-]{9,20}", error="La cédula/RNC solo admite números y guiones (mínimo 9 dígitos)."),
                dict(key="telefono", label="Teléfono", tipo="texto", mitad=True, max=20, **TEL),
                dict(key="nombre", label="Nombre", tipo="texto", obligatorio=True, mitad=True, max=50),
                dict(key="apellido", label="Apellido", tipo="texto", obligatorio=True, mitad=True, max=50),
                dict(key="correo", label="Correo electrónico", tipo="texto", max=100, **CORREO),
                dict(key="direccion", label="Dirección", tipo="texto")],
        ancho_form=400)


def _spec_proveedores():
    return dict(
        titulo_excel="Proveedores",
        titulo_singular="proveedor", id_param="proveedor_id",
        listar=proveedores.listar, guardar=proveedores.guardar, eliminar=proveedores.eliminar,
        columnas=[("proveedor_id", "ID", 50, "center"), ("rnc", "RNC", 100, "w"),
                  ("nombre_empresa", "Empresa", 190, "w"), ("telefono", "Teléfono", 110, "w"),
                  ("correo", "Correo", 170, "w"), ("direccion", "Dirección", 190, "w")],
        campos=[dict(key="nombre_empresa", label="Nombre de la empresa", tipo="texto", obligatorio=True, max=100),
                dict(key="rnc", label="RNC", tipo="texto", obligatorio=True, mitad=True, max=20,
                     patron=r"[0-9\-]{9,20}", error="El RNC solo admite números y guiones (mínimo 9 dígitos)."),
                dict(key="telefono", label="Teléfono", tipo="texto", mitad=True, max=20, **TEL),
                dict(key="correo", label="Correo electrónico", tipo="texto", max=100, **CORREO),
                dict(key="direccion", label="Dirección", tipo="texto")],
        ancho_form=380)


def _ajustar_existencia(vista):
    fila = vista.fila_seleccionada()
    if not fila:
        vista.estado("Selecciona un producto de la tabla para ajustar su existencia.", error=True)
        return
    datos = pedir_datos(vista, f"Ajustar stock: {fila['nombre']}",
                        [("cantidad", f"Cantidad (+ entra / − sale). Stock actual: {fila['stock_actual']}", ""),
                         ("motivo", "Motivo del ajuste", "")], "Aplicar ajuste")
    if not datos:
        return
    try:
        cantidad = int(datos["cantidad"].replace(",", ""))
    except ValueError:
        vista.estado("La cantidad debe ser un número entero (ejemplo: 5 o -3).", error=True)
        return
    try:
        inventario.ajustar_existencia(fila["producto_id"], cantidad, datos["motivo"], vista.usuario["usuario_id"])
    except Exception as exc:
        vista.estado(mensaje_error(exc), error=True)
        return
    vista.recargar()
    vista.estado("✔ Stock ajustado correctamente.", ok=True)


def _spec_inventario():
    def alerta(d):
        s = d["stock_actual"] or 0
        return "critico" if s <= inventario.STOCK_CRITICO else "bajo" if s <= inventario.STOCK_BAJO else None

    return dict(
        titulo_excel="Inventario",
        titulo_singular="producto", id_param="producto_id",
        listar=inventario.listar, guardar=inventario.guardar, eliminar=inventario.eliminar,
        proveedores=proveedores.listar,
        columnas=[("producto_id", "ID", 50, "center"), ("codigo_barras", "Código de barras", 120, "w"),
                  ("nombre", "Producto", 200, "w"), ("categoria", "Categoría", 120, "w"),
                  ("precio_compra", "P. compra", 90, "e"), ("precio_venta", "P. venta", 90, "e"),
                  ("stock_actual", "Stock", 70, "e"), ("proveedor", "Proveedor", 130, "w"),
                  ("descripcion", "Descripción", 150, "w"), ("proveedor_id", "ID prov.", 60, "w")],
        visibles=["codigo_barras", "nombre", "categoria", "precio_venta", "stock_actual"],
        resaltar=alerta,
        campos=[dict(key="codigo_barras", label="Código de barras", tipo="texto", mitad=True, max=30),
                dict(key="categoria", label="Categoría", tipo="texto", mitad=True, max=50),
                dict(key="nombre", label="Nombre del producto", tipo="texto", obligatorio=True, max=100),
                dict(key="descripcion", label="Descripción", tipo="texto"),
                dict(key="proveedor_id", label="Proveedor", tipo="proveedor"),
                dict(key="precio_compra", label="Precio de compra", tipo="numero", mitad=True, defecto="0.00"),
                dict(key="precio_venta", label="Precio de venta", tipo="numero", mitad=True, defecto="0.00"),
                dict(key="stock_actual", label="Stock inicial", tipo="entero", mitad=True,
                     defecto="0", solo_nuevo=True)],
        acciones_extra=[("Ajustar stock del seleccionado", _ajustar_existencia)],
        ancho_form=420)


def _spec_usuarios():
    roles = ["Administrador", "Supervisor", "Cajero", "Almacenista", "Contador", "Director",
             "Auditor", "Encargado Compras", "Servicio al Cliente", "Soporte IT"]
    return dict(
        titulo_excel="Usuarios",
        titulo_singular="usuario", id_param="id_editado",
        listar=usuarios.listar, guardar=usuarios.guardar, eliminar=usuarios.eliminar,
        columnas=[("id_editado", "ID", 50, "center"), ("nombre", "Nombre", 120, "w"),
                  ("apellido", "Apellido", 120, "w"), ("ciudad", "Ciudad", 100, "w"),
                  ("nombre_usuario", "Usuario", 140, "w"), ("rol", "Rol", 140, "w")],
        campos=[dict(key="nombre", label="Nombre", tipo="texto", obligatorio=True, mitad=True, max=50),
                dict(key="apellido", label="Apellido", tipo="texto", obligatorio=True, mitad=True, max=50),
                dict(key="ciudad", label="Ciudad", tipo="texto", mitad=True, max=50),
                dict(key="nombre_usuario", label="Usuario", tipo="texto", obligatorio=True, mitad=True, max=50),
                dict(key="rol", label="Rol", tipo="combo", valores=roles, obligatorio=True, max=50, defecto="Cajero"),
                dict(key="password", label="Contraseña (vacía = no cambiar)", tipo="password", min=8)],
        ancho_form=400)


# ------------------------------------------------------------------- Listados
def _ver_detalle(vista, fila):
    lineas = ventas.detalle_factura(fila["factura_id"])
    texto = "\n".join(f"{c} × {n}   @ {p:,.2f}   =   {c * p:,.2f}" for n, c, p in lineas) or "Sin detalle."
    messagebox.showinfo(f"Factura {fila['numero']}", texto, parent=vista)


def _imprimir_pdf(vista, fila):
    abrir_archivo(generar_factura_pdf(fila["factura_id"]))


def _abono(vista, fila):
    datos = pedir_datos(vista, f"Abono a la cuenta #{fila['cxc_id']}",
                        [("monto", f"Monto del abono (pendiente: {fila['monto_pendiente']:,.2f})", "")],
                        "Registrar abono")
    if datos:
        cuentas_cobrar.registrar_abono(fila["cxc_id"], _monto(datos["monto"], "El abono"),
                                       vista.usuario["usuario_id"])
        vista.recargar()


def _pago(vista, fila):
    datos = pedir_datos(vista, f"Pago a la cuenta #{fila['cxp_id']}",
                        [("monto", f"Monto del pago (pendiente: {fila['monto_pendiente']:,.2f})", "")],
                        "Registrar pago")
    if datos:
        cuentas_pagar.pagar(fila["cxp_id"], _monto(datos["monto"], "El pago"), vista.usuario["usuario_id"])
        vista.recargar()


def _nueva_cxp(vista, _fila):
    provs = {}
    for f in proveedores.listar():
        nombre = f[2] if f[2] not in provs else f"{f[2]} (#{f[0]})"
        provs[nombre] = f[0]
    if not provs:
        messagebox.showinfo("Sin proveedores", "Primero registra un proveedor.", parent=vista)
        return
    datos = pedir_datos(vista, "Nueva cuenta por pagar",
                        [("proveedor", "Proveedor", "", list(provs)), ("monto", "Monto total", ""),
                         ("vence", "Vence (AAAA-MM-DD, opcional)", "")], "Guardar")
    if not datos:
        return
    if datos["proveedor"] not in provs:
        raise ValueError("Elige un proveedor de la lista.")
    vence = None
    if datos["vence"]:
        try:
            vence = datetime.strptime(datos["vence"], "%Y-%m-%d")
        except ValueError:
            raise ValueError("La fecha debe tener el formato AAAA-MM-DD.")
    cuentas_pagar.crear_cuenta(provs[datos["proveedor"]], _monto(datos["monto"], "El monto"), vence,
                               vista.usuario["usuario_id"])
    vista.recargar()


def _nuevo_movimiento(vista, _fila):
    datos = pedir_datos(vista, "Nuevo movimiento bancario",
                        [("banco", "Banco", ""), ("cuenta", "Número de cuenta", ""),
                         ("tipo", "Tipo", "Depósito", list(banco.TIPOS)), ("monto", "Monto", ""),
                         ("referencia", "Referencia (opcional)", "")], "Guardar")
    if datos:
        banco.registrar_movimiento(datos["banco"], datos["cuenta"], datos["tipo"],
                                   _monto(datos["monto"], "El monto"), datos["referencia"],
                                   vista.usuario["usuario_id"])
        vista.recargar()


def _resumen_banco():
    depositos, retiros, balance = banco.resumen()
    return [("DEPÓSITOS", dinero(depositos), t.OK), ("RETIROS", dinero(retiros), t.ERROR),
            ("BALANCE", dinero(balance), t.NARANJA)]


def _spec_facturas():
    return dict(
        titulo_excel="Facturas", listar=ventas.listar_facturas, vacios={"cliente": "Consumidor final"},
        columnas=[("factura_id", "ID", 50, "center"), ("numero", "N.º factura", 110, "w"),
                  ("fecha", "Fecha", 130, "w"), ("cliente", "Cliente", 170, "w"),
                  ("usuario", "Vendedor", 120, "w"), ("tipo_pago", "Pago", 80, "w"),
                  ("subtotal", "Subtotal", 95, "e"), ("itbis", "ITBIS", 85, "e"),
                  ("descuento", "Descuento", 85, "e"), ("total", "Total", 105, "e")],
        acciones=[dict(texto="Ver detalle", fn=_ver_detalle, seleccion=True),
                  dict(texto="Factura PDF", fn=_imprimir_pdf, seleccion=True)])


def _spec_cxc():
    return dict(
        titulo_excel="Cuentas por cobrar", listar=cuentas_cobrar.listar,
        columnas=[("cxc_id", "ID", 50, "center"), ("numero_factura", "Factura", 110, "w"),
                  ("cliente", "Cliente", 190, "w"), ("monto_inicial", "Monto inicial", 110, "e"),
                  ("monto_pendiente", "Pendiente", 110, "e"), ("estado", "Estado", 90, "w"),
                  ("fecha_emision", "Emisión", 130, "w"), ("fecha_vencimiento", "Vence", 130, "w")],
        acciones=[dict(texto="Registrar abono", fn=_abono, seleccion=True)])


def _spec_cxp():
    return dict(
        titulo_excel="Cuentas por pagar", listar=cuentas_pagar.listar,
        columnas=[("cxp_id", "ID", 50, "center"), ("proveedor", "Proveedor", 200, "w"),
                  ("monto_total", "Monto total", 110, "e"), ("monto_pendiente", "Pendiente", 110, "e"),
                  ("estado", "Estado", 90, "w"), ("fecha_registro", "Registro", 130, "w"),
                  ("fecha_vencimiento", "Vence", 130, "w")],
        acciones=[dict(texto="Nueva cuenta", fn=_nueva_cxp, seleccion=False),
                  dict(texto="Registrar pago", fn=_pago, seleccion=True)])


def _spec_banco():
    return dict(
        titulo_excel="Banco", listar=banco.listar, resumen=_resumen_banco,
        columnas=[("banco_id", "ID", 50, "center"), ("banco", "Banco", 130, "w"),
                  ("cuenta", "Cuenta", 120, "w"), ("tipo", "Tipo", 90, "w"),
                  ("monto", "Monto", 110, "e"), ("referencia", "Referencia", 140, "w"),
                  ("fecha", "Fecha", 130, "w")],
        acciones=[dict(texto="Nuevo movimiento", fn=_nuevo_movimiento, seleccion=False)])


def _spec_auditoria():
    return dict(
        titulo_excel="Auditoria", listar=auditoria.listar,
        columnas=[("auditoria_id", "ID", 50, "center"), ("usuario", "Usuario", 110, "w"),
                  ("tabla", "Tabla", 130, "w"), ("accion", "Acción", 80, "w"),
                  ("anteriores", "Datos anteriores", 200, "w"), ("nuevos", "Datos nuevos", 200, "w"),
                  ("fecha", "Fecha", 130, "w")])


# ------------------------------------------------------- Secciones del sistema
# clave: (título, subtítulo, fábrica(parent, usuario, navegar))
SECCIONES = {
    "inicio": ("Inicio", "Resumen general del negocio",
               lambda p, u, nav: VistaResumen(p, u, nav, inicio=True)),
    "venta": ("Nueva venta", "Registra una factura; el stock y las cuentas por cobrar se actualizan solos",
              lambda p, u, nav: VistaVenta(p, u)),
    "inventario": ("Inventario", "Productos y stock; en rojo los críticos (≤ 15) y en amarillo los bajos (≤ 30)",
                   lambda p, u, nav: VistaCRUD(p, u, _spec_inventario())),
    "clientes": ("Clientes", "Registro y consulta de clientes",
                 lambda p, u, nav: VistaCRUD(p, u, _spec_clientes())),
    "proveedores": ("Proveedores", "Registro y consulta de proveedores",
                    lambda p, u, nav: VistaCRUD(p, u, _spec_proveedores())),
    "facturas": ("Facturas / Ventas", "Historial de facturas emitidas",
                 lambda p, u, nav: VistaLista(p, u, _spec_facturas())),
    "cxc": ("Cuentas por cobrar", "Saldos pendientes de clientes",
            lambda p, u, nav: VistaLista(p, u, _spec_cxc())),
    "cxp": ("Cuentas por pagar", "Saldos pendientes con proveedores",
            lambda p, u, nav: VistaLista(p, u, _spec_cxp())),
    "banco": ("Banco", "Depósitos, retiros y balance",
              lambda p, u, nav: VistaLista(p, u, _spec_banco())),
    "reportes": ("Reportes", "Indicadores generales y alertas de inventario",
                 lambda p, u, nav: VistaResumen(p, u, nav, inicio=False)),
    "auditoria": ("Auditoría", "Últimas acciones registradas en el sistema",
                  lambda p, u, nav: VistaLista(p, u, _spec_auditoria())),
    "usuarios": ("Usuarios", "Administración de usuarios y contraseñas",
                 lambda p, u, nav: VistaCRUD(p, u, _spec_usuarios())),
}
