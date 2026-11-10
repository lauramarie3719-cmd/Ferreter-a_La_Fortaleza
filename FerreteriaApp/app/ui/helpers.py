"""Widgets y utilidades reutilizables de la interfaz."""
import os
import re
import subprocess
import sys
import tkinter as tk
from datetime import date, datetime
from decimal import Decimal
from tkinter import ttk

from app.config import MONEDA
from app.ui import theme as t


# ---------- Textos ----------
def mensaje_error(exc):
    """Convierte excepciones técnicas en mensajes entendibles."""
    texto = str(exc)
    bajo = texto.lower()
    if exc.__class__.__name__ == "ErrorConexion":
        return texto
    if isinstance(exc, ModuleNotFoundError):
        return (f"Falta instalar la librería «{exc.name}».\n"
                "En la terminal ejecuta: pip install -r requirements.txt")
    if isinstance(exc, (AttributeError, TypeError)) and "nonetype" in bajo:
        return ("No se pudo conectar con la base de datos.\n"
                "Verifica que SQL Server esté activo y revisa app/config.py.")
    if "conflicted with the reference" in bajo:
        return ("No se puede eliminar: este registro tiene datos relacionados "
                "(facturas, productos, movimientos, etc.).")
    if "conflicted with the foreign key" in bajo:
        return "El cliente, proveedor o producto seleccionado no existe."
    if "unique" in bajo or "duplicate key" in bajo:
        return "Ya existe un registro con ese mismo valor (dato duplicado)."
    if "[sql server]" in bajo:
        corto = texto.split("[SQL Server]")[-1]
        return re.sub(r"\s*\(\d+\).*$", "", corto).strip(" \"')") or texto
    return texto or exc.__class__.__name__


def formatear(valor):
    if valor is None:
        return ""
    if isinstance(valor, (Decimal, float)):
        return f"{valor:,.2f}"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor)


def dinero(valor):
    return f"{MONEDA} {Decimal(str(valor or 0)):,.2f}"


def abrir_archivo(ruta):
    """Abre un archivo con el programa predeterminado del sistema (PDF, Excel...)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(ruta)])
        else:
            subprocess.Popen(["xdg-open", str(ruta)])
    except Exception:
        pass


# ---------- Ventanas ----------
def centrar(ventana, ancho, alto):
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = max(0, (ventana.winfo_screenheight() - alto) // 2 - 20)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# ---------- Widgets ----------
def boton(parent, texto, comando, primario=True, **kw):
    bg, hover = (t.NARANJA, t.NARANJA_HOVER) if primario else (t.BORDE, "#4a505e")
    fg = t.BG if primario else t.TEXTO
    b = tk.Button(parent, text=texto, command=comando, bg=bg, fg=fg,
                  activebackground=hover, activeforeground=fg, relief="flat", bd=0,
                  highlightthickness=0, font=t.F_BOTON, cursor="hand2",
                  padx=14, pady=8, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def entrada(parent, variable, **kw):
    return tk.Entry(parent, textvariable=variable, bg=t.INPUT, fg=t.TEXTO,
                    insertbackground=t.TEXTO, relief="flat", font=t.F_TEXTO,
                    highlightthickness=1, highlightbackground=t.BORDE,
                    highlightcolor=t.NARANJA, disabledbackground=t.BG,
                    readonlybackground=t.BG, disabledforeground=t.TEXTO_SUAVE, **kw)


def combo(parent, variable, valores, solo_lectura=True):
    return ttk.Combobox(parent, textvariable=variable, values=valores,
                        state="readonly" if solo_lectura else "normal", font=t.F_TEXTO)


def tarjeta(parent, **kw):
    return tk.Frame(parent, bg=t.CARD, highlightthickness=1,
                    highlightbackground=t.BORDE, **kw)


def tarjeta_dato(parent, titulo, valor, color=t.NARANJA):
    """Tarjeta con un indicador (cifra grande) y su título."""
    c = tarjeta(parent)
    tk.Frame(c, bg=color, height=3).pack(fill="x")
    tk.Label(c, text=titulo, bg=t.CARD, fg=t.TEXTO_SUAVE, font=t.F_ETIQUETA,
             anchor="w").pack(fill="x", padx=14, pady=(10, 0))
    n = len(valor)          # cifras largas usan letra más pequeña para que no se corten
    tam = 20 if n <= 11 else 18 if n <= 13 else 16 if n <= 15 else 14
    tk.Label(c, text=valor, bg=t.CARD, fg=t.TEXTO, font=("Arial", tam, "bold"),
             anchor="w").pack(fill="x", padx=14, pady=(0, 12))
    return c


def crear_tabla(parent, columnas, visibles=None):
    """Tabla con barras de desplazamiento.

    columnas: lista de (clave, encabezado, ancho, alineación).
    Devuelve (contenedor, treeview).
    """
    cont = tk.Frame(parent, bg=t.CARD, highlightthickness=1, highlightbackground=t.BORDE)
    claves = [c[0] for c in columnas]
    tree = ttk.Treeview(cont, columns=claves, show="headings", selectmode="browse",
                        displaycolumns=visibles or "#all")
    for clave, enc, ancho, anchor in columnas:
        tree.heading(clave, text=enc)
        tree.column(clave, width=ancho, minwidth=50, anchor=anchor)
    vsb = ttk.Scrollbar(cont, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(cont, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    cont.grid_rowconfigure(0, weight=1)
    cont.grid_columnconfigure(0, weight=1)
    tree.tag_configure("par", background=t.CARD)
    tree.tag_configure("impar", background=t.CARD_ALT)
    tree.tag_configure("alerta", foreground=t.ERROR)
    tree.tag_configure("critico", foreground=t.ERROR)
    tree.tag_configure("bajo", foreground=t.AVISO)
    return cont, tree


def pedir_datos(parent, titulo, campos, texto_ok="Aceptar"):
    """Cuadro de diálogo con formulario corto.

    campos: lista de (clave, etiqueta, valor_inicial[, lista_de_opciones]).
    Devuelve un dict con los textos escritos, o None si se cancela.
    """
    top = tk.Toplevel(parent)
    top.title(titulo)
    top.configure(bg=t.PANEL)
    top.resizable(False, False)
    top.transient(parent.winfo_toplevel())

    tk.Label(top, text=titulo, bg=t.PANEL, fg=t.NARANJA, font=t.F_SECCION,
             anchor="w").pack(fill="x", padx=24, pady=(20, 12))

    variables, primero = {}, None
    for campo in campos:
        clave, etiqueta, inicial = campo[:3]
        opciones = campo[3] if len(campo) > 3 else None
        tk.Label(top, text=etiqueta, bg=t.PANEL, fg=t.TEXTO_SUAVE, font=t.F_ETIQUETA,
                 anchor="w").pack(fill="x", padx=24)
        var = tk.StringVar(value=inicial)
        w = combo(top, var, opciones) if opciones else entrada(top, var, width=38)
        w.pack(fill="x", padx=24, pady=(2, 12), ipady=4 if not opciones else 0)
        variables[clave] = var
        primero = primero or w

    resultado = {}

    def aceptar(_=None):
        resultado.update({k: v.get().strip() for k, v in variables.items()})
        top.destroy()

    barra = tk.Frame(top, bg=t.PANEL)
    barra.pack(fill="x", padx=24, pady=(4, 20))
    boton(barra, texto_ok, aceptar).pack(side="right")
    boton(barra, "Cancelar", top.destroy, primario=False).pack(side="right", padx=(0, 8))
    top.bind("<Return>", aceptar)
    top.bind("<Escape>", lambda e: top.destroy())

    top.update_idletasks()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    top.geometry(f"+{px + (pw - top.winfo_width()) // 2}+{py + (ph - top.winfo_height()) // 3}")
    try:
        top.wait_visibility()
        top.grab_set()
    except tk.TclError:
        pass
    if primero is not None:
        primero.focus_set()
    parent.wait_window(top)
    return resultado or None
