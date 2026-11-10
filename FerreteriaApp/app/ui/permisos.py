"""Qué secciones puede abrir cada rol. Edita este diccionario para ajustar los permisos."""

INICIO = "inicio"

PERMISOS = {
    "administrador": {"inicio", "venta", "inventario", "clientes", "proveedores", "facturas",
                      "cxc", "cxp", "banco", "reportes", "auditoria", "usuarios"},
    "director": {"inicio", "inventario", "clientes", "proveedores", "facturas",
                 "cxc", "cxp", "banco", "reportes", "auditoria"},
    "supervisor": {"inicio", "venta", "inventario", "clientes", "facturas", "cxc", "reportes"},
    "cajero": {"inicio", "venta", "clientes", "facturas", "cxc"},
    "almacenista": {"inicio", "inventario", "proveedores"},
    "contador": {"inicio", "facturas", "cxc", "cxp", "banco", "reportes"},
    "auditor": {"inicio", "facturas", "cxc", "cxp", "banco", "reportes", "auditoria"},
    "encargado compras": {"inicio", "inventario", "proveedores", "cxp"},
    "servicio al cliente": {"inicio", "clientes", "facturas"},
    "soporte it": {"inicio", "usuarios", "auditoria"},
    "chofer": {"inicio", "facturas"},
    "ayudante de despacho": {"inicio", "facturas"},
}


def puede(rol, seccion):
    """True si el rol tiene acceso a la sección. Un rol desconocido solo ve el Inicio."""
    permitidas = PERMISOS.get((rol or "").strip().lower(), {INICIO})
    return seccion in permitidas
