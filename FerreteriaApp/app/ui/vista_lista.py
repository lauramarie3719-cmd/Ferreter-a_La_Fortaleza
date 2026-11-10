"""Vista genérica de listado (tabla con búsqueda, resumen y acciones opcionales)."""
import tkinter as tk
from tkinter import messagebox

from app.ui import theme as t
from app.ui.exportar import exportar_excel
from app.ui.helpers import (boton, crear_tabla, entrada, formatear, mensaje_error,
                            tarjeta_dato)


class VistaLista(tk.Frame):
    """spec: listar, columnas [(clave, encabezado, ancho, alineación)],
    vacios {clave: texto}, resumen (función -> [(título, valor, color)]),
    acciones [{texto, fn(vista, fila), seleccion(bool)}]."""

    def __init__(self, parent, usuario, spec):
        super().__init__(parent, bg=t.BG)
        self.usuario, self.spec, self.filas = usuario, spec, {}
        self.buscar_var = tk.StringVar()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.zona_resumen = tk.Frame(self, bg=t.BG)
        self.zona_resumen.grid(row=0, column=0, sticky="ew")

        barra = tk.Frame(self, bg=t.BG)
        barra.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        tk.Label(barra, text="Buscar:", bg=t.BG, fg=t.TEXTO_SUAVE,
                 font=t.F_ETIQUETA).pack(side="left", padx=(0, 8))
        self.entrada_buscar = entrada(barra, self.buscar_var)
        self.entrada_buscar.pack(side="left", fill="x", expand=True, ipady=4)
        self.buscar_var.trace_add("write", lambda *_: self._pintar())
        boton(barra, "Actualizar", self.recargar, primario=False).pack(side="left", padx=(10, 0))
        boton(barra, "Exportar a Excel", self.exportar, primario=False).pack(side="left", padx=(8, 0))
        for accion in spec.get("acciones", []):
            boton(barra, accion["texto"], lambda a=accion: self._ejecutar(a)).pack(
                side="left", padx=(10, 0))

        cont, self.tree = crear_tabla(self, spec["columnas"])
        cont.grid(row=2, column=0, sticky="nsew")

        self.lbl_pie = tk.Label(self, text="", bg=t.BG, fg=t.TEXTO_SUAVE,
                                font=("Arial", 9), anchor="e")
        self.lbl_pie.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.recargar()

    def recargar(self):
        try:
            self._pintar_resumen()
            claves = [c[0] for c in self.spec["columnas"]]
            self.filas = {str(i): dict(zip(claves, f)) for i, f in enumerate(self.spec["listar"]())}
            self.lbl_pie.config(fg=t.TEXTO_SUAVE)
        except Exception as exc:
            self.filas = {}
            self.lbl_pie.config(text=mensaje_error(exc), fg=t.ERROR)
            self.tree.delete(*self.tree.get_children())
            return
        self._pintar()

    def _pintar_resumen(self):
        for w in self.zona_resumen.winfo_children():
            w.destroy()
        if not self.spec.get("resumen"):
            return
        datos = self.spec["resumen"]()
        for i, (titulo, valor, color) in enumerate(datos):
            self.zona_resumen.grid_columnconfigure(i, weight=1, uniform="r")
            tarjeta_dato(self.zona_resumen, titulo, valor, color).grid(
                row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(0, 12))

    def _pintar(self):
        filtro = self.buscar_var.get().strip().lower()
        vacios = self.spec.get("vacios", {})
        self.tree.delete(*self.tree.get_children())
        n = 0
        for iid, d in self.filas.items():
            valores = [formatear(d[c[0]]) or vacios.get(c[0], "") for c in self.spec["columnas"]]
            if filtro and not any(filtro in v.lower() for v in valores):
                continue
            self.tree.insert("", "end", iid=iid, values=valores,
                             tags=("par" if n % 2 == 0 else "impar",))
            n += 1
        self.lbl_pie.config(text=f"{n} registro(s)" if n or self.filas else "No hay registros para mostrar.")

    def enfocar_busqueda(self):
        self.entrada_buscar.focus_set()
        self.entrada_buscar.select_range(0, "end")

    def exportar(self):
        """Exporta a Excel lo que se ve en la tabla (respeta la búsqueda)."""
        cols = self.spec["columnas"]
        vacios = self.spec.get("vacios", {})
        filas = [[self.filas[i][c[0]] if self.filas[i][c[0]] is not None else vacios.get(c[0])
                  for c in cols] for i in self.tree.get_children()]
        exportar_excel(self, self.spec.get("titulo_excel", "Datos"), [c[1] for c in cols], filas)

    def fila_seleccionada(self):
        sel = self.tree.selection()
        return self.filas.get(sel[0]) if sel else None

    def _ejecutar(self, accion):
        fila = self.fila_seleccionada()
        if accion.get("seleccion") and not fila:
            messagebox.showinfo("Selecciona un registro",
                                "Elige una fila de la tabla para continuar.", parent=self)
            return
        try:
            accion["fn"](self, fila)
        except Exception as exc:
            messagebox.showerror("Error", mensaje_error(exc), parent=self)
