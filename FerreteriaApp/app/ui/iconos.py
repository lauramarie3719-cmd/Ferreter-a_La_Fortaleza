"""Iconos sencillos dibujados con Canvas (sin imágenes externas) y botones/campos con estilo."""
import math
import tkinter as tk

from app.ui import theme as t

NOMBRES = ["inicio", "venta", "inventario", "clientes", "proveedores", "facturas", "cxc", "cxp",
           "banco", "reportes", "auditoria", "usuarios", "tablas", "salir", "usuario", "candado",
           "ojo", "ojo_tachado", "engranaje"]


def dibujar_icono(c, nombre, color, tam=18):
    """Dibuja el icono `nombre` en el canvas `c` (cuadrícula base de 18×18, escalada a `tam`)."""
    c.delete("all")
    k = tam / 18
    w = max(1.4, 1.6 * k)

    def P(*v):
        return [x * k for x in v]

    def linea(*v, **kw):
        c.create_line(*P(*v), fill=color, width=w, capstyle="round", joinstyle="round", **kw)

    def poli(*v):
        c.create_polygon(*P(*v), outline=color, fill="", width=w, joinstyle="round")

    def rect(a, b, d, e, relleno=False):
        c.create_rectangle(*P(a, b, d, e), outline=color, width=w, fill=color if relleno else "")

    def ovalo(a, b, d, e, relleno=False):
        c.create_oval(*P(a, b, d, e), outline=color, width=w, fill=color if relleno else "")

    def arco(a, b, d, e, ini, ext):
        c.create_arc(*P(a, b, d, e), start=ini, extent=ext, style="arc", outline=color, width=w)

    if nombre == "inicio":
        linea(2, 9, 9, 3, 16, 9)
        linea(4, 8, 4, 15, 14, 15, 14, 8)
        linea(8, 15, 8, 11, 10, 11, 10, 15)
    elif nombre == "venta":
        linea(1, 3, 4, 3, 6, 12, 15, 12, 16, 6, 5, 6)
        ovalo(6, 14, 8.4, 16.4, True)
        ovalo(12.6, 14, 15, 16.4, True)
    elif nombre == "inventario":
        rect(2, 3.5, 16, 7)
        rect(3, 7, 15, 15)
        linea(7, 10.5, 11, 10.5)
    elif nombre == "clientes":
        ovalo(6, 2.5, 12, 8.5)
        arco(3, 10, 15, 22, 0, 180)
    elif nombre == "proveedores":
        rect(1, 5, 11, 12)
        poli(11, 8, 14.5, 8, 17, 11, 17, 12, 11, 12)
        ovalo(3.5, 11.5, 7.5, 15.5, True)
        ovalo(11.5, 11.5, 15.5, 15.5, True)
    elif nombre == "facturas":
        rect(4, 2, 14, 16)
        linea(6.5, 6, 11.5, 6)
        linea(6.5, 9, 11.5, 9)
        linea(6.5, 12, 9.5, 12)
    elif nombre == "cxc":
        ovalo(2, 2, 16, 16)
        c.create_text(9 * k, 9.3 * k, text="$", fill=color, font=("Arial", max(7, int(9 * k)), "bold"))
    elif nombre == "cxp":
        rect(2, 5, 16, 15)
        linea(2, 8.5, 16, 8.5)
        ovalo(11.5, 10.5, 13.5, 12.5, True)
    elif nombre == "banco":
        linea(2, 7, 9, 2.5, 16, 7, 2, 7)
        linea(4.5, 9, 4.5, 14)
        linea(9, 9, 9, 14)
        linea(13.5, 9, 13.5, 14)
        linea(2, 16, 16, 16)
    elif nombre == "reportes":
        rect(3, 9, 6, 16, True)
        rect(7.5, 5, 10.5, 16, True)
        rect(12, 2, 15, 16, True)
    elif nombre == "auditoria":
        poli(9, 2, 15, 4, 15, 9, 9, 16, 3, 9, 3, 4)
        linea(6, 8.8, 8.3, 11, 12, 6.5)
    elif nombre == "usuarios":
        ovalo(4, 2.5, 9.5, 8)
        arco(1, 9.5, 12.5, 21, 0, 180)
        linea(14, 4, 14, 10)
        linea(11.5, 7, 16.5, 7)
    elif nombre == "tablas":
        rect(2, 3, 16, 15)
        linea(2, 7.5, 16, 7.5)
        linea(2, 11, 16, 11)
        linea(7.5, 3, 7.5, 15)
    elif nombre == "salir":
        linea(8, 2, 3, 2, 3, 16, 8, 16)
        linea(7, 9, 16, 9)
        linea(13, 6, 16, 9, 13, 12)
    elif nombre == "usuario":
        ovalo(5.5, 2.5, 12.5, 9.5)
        arco(2.5, 11, 15.5, 24, 0, 180)
    elif nombre == "candado":
        rect(3.5, 8, 14.5, 16)
        arco(5.5, 2, 12.5, 12, 0, 180)
        linea(9, 11, 9, 13.5)
    elif nombre in ("ojo", "ojo_tachado"):
        ovalo(1, 5, 17, 13)
        ovalo(6.5, 6.5, 11.5, 11.5, True)
        if nombre == "ojo_tachado":
            linea(3, 16, 15, 2)
    elif nombre == "engranaje":
        dibujar_engranaje(c, 9 * k, 9 * k, 7.5 * k, 5.2 * k, 8, color, "", w)
        ovalo(6.5, 6.5, 11.5, 11.5)


def dibujar_engranaje(c, cx, cy, r_ext, r_int, dientes, contorno, relleno="", ancho=1):
    """Engranaje (rueda dentada) como polígono."""
    pts = []
    paso = 2 * math.pi / dientes
    for i in range(dientes):
        a = i * paso
        for frac, radio in ((0.0, r_int), (0.18, r_ext), (0.5, r_ext), (0.68, r_int)):
            ang = a + frac * paso
            pts += [cx + radio * math.cos(ang), cy + radio * math.sin(ang)]
    c.create_polygon(*pts, outline=contorno, fill=relleno, width=ancho, joinstyle="round")


def redondeado(c, x1, y1, x2, y2, r, **kw):
    """Rectángulo con esquinas redondeadas."""
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


class Icono(tk.Canvas):
    def __init__(self, parent, nombre, color, bg, tam=18):
        super().__init__(parent, width=tam, height=tam, bg=bg, highlightthickness=0, bd=0)
        self.nombre, self.tam = nombre, tam
        self.pintar(color)

    def pintar(self, color):
        dibujar_icono(self, self.nombre, color, self.tam)


class BotonRedondo(tk.Canvas):
    """Botón con esquinas redondeadas y efecto al pasar el mouse."""

    def __init__(self, parent, texto, comando, ancho=360, alto=46, color=t.NARANJA,
                 hover=t.NARANJA_HOVER, fg=t.BG, bg=t.PANEL, radio=12, fuente=("Arial", 12, "bold")):
        super().__init__(parent, width=ancho, height=alto, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self._color, self._hover = color, hover
        self._forma = redondeado(self, 1, 1, ancho - 1, alto - 1, radio, fill=color, outline="")
        self.create_text(ancho / 2, alto / 2, text=texto, fill=fg, font=fuente)
        self.bind("<Enter>", lambda e: self.itemconfig(self._forma, fill=self._hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self._forma, fill=self._color))
        self.bind("<Button-1>", lambda e: comando())
