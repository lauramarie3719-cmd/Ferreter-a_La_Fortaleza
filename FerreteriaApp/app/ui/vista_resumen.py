"""Página de inicio y reportes: indicadores, gráfico de ventas y productos con stock bajo."""
import tkinter as tk
from datetime import datetime

from app.modules import inventario, reportes
from app.ui import theme as t
from app.ui.grafico import GraficoBarras
from app.ui.helpers import (boton, crear_tabla, dinero, formatear, mensaje_error,
                            tarjeta, tarjeta_dato)
from app.ui.permisos import puede

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


class VistaResumen(tk.Frame):
    def __init__(self, parent, usuario, navegar=None, inicio=True):
        super().__init__(parent, bg=t.BG)
        self.usuario, self.navegar, self.inicio = usuario, navegar, inicio
        self.rol = usuario["rol"]
        self.ver_stock = puede(self.rol, "inventario")
        self.ver_grafico = puede(self.rol, "facturas")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        if inicio:
            self._bienvenida().grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.zona_cifras = tk.Frame(self, bg=t.BG)
        self.zona_cifras.grid(row=1, column=0, sticky="ew")
        if inicio and navegar:
            accesos = self._accesos()
            if accesos is not None:
                accesos.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        if self.ver_stock or self.ver_grafico:
            abajo = tk.Frame(self, bg=t.BG)
            abajo.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
            abajo.grid_rowconfigure(0, weight=1)
            col = 0
            if self.ver_grafico:
                abajo.grid_columnconfigure(col, weight=2, uniform="b")
                self._panel_grafico(abajo).grid(row=0, column=col, sticky="nsew",
                                                padx=(0, 12 if self.ver_stock else 0))
                col += 1
            if self.ver_stock:
                abajo.grid_columnconfigure(col, weight=3, uniform="b")
                self._stock_bajo(abajo).grid(row=0, column=col, sticky="nsew")
        self.recargar()

    # ------------------------------------------------------------ Secciones
    def _bienvenida(self):
        ahora = datetime.now()
        fecha = f"{DIAS[ahora.weekday()].capitalize()}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
        c = tarjeta(self)
        tk.Frame(c, bg=t.NARANJA, width=5).pack(side="left", fill="y")
        txt = tk.Frame(c, bg=t.CARD)
        txt.pack(side="left", padx=18, pady=14)
        tk.Label(txt, text=f"¡Hola, {self.usuario['nombre']}!", bg=t.CARD, fg=t.TEXTO,
                 font=("Arial", 16, "bold"), anchor="w").pack(fill="x")
        tk.Label(txt, text=f"Rol: {self.usuario['rol']}   ·   {fecha}", bg=t.CARD,
                 fg=t.TEXTO_SUAVE, font=t.F_SUBTITULO, anchor="w").pack(fill="x")
        return c

    def _accesos(self):
        opciones = [(k, x) for k, x in [("venta", "Nueva venta"), ("inventario", "Inventario"),
                                        ("clientes", "Clientes"), ("facturas", "Facturas / Ventas")]
                    if puede(self.rol, k)]
        if not opciones:
            return None
        f = tk.Frame(self, bg=t.BG)
        tk.Label(f, text="Accesos rápidos", bg=t.BG, fg=t.TEXTO, font=t.F_SECCION).pack(anchor="w")
        fila = tk.Frame(f, bg=t.BG)
        fila.pack(fill="x", pady=(8, 0))
        for i, (clave, texto) in enumerate(opciones):
            fila.grid_columnconfigure(i, weight=1, uniform="a")
            boton(fila, texto, lambda k=clave: self.navegar(k), primario=(i == 0)).grid(
                row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
        return f

    def _panel_grafico(self, parent):
        f = tk.Frame(parent, bg=t.BG)
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        tk.Label(f, text="Ventas de los últimos 7 días", bg=t.BG, fg=t.TEXTO,
                 font=t.F_SECCION, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 8))
        card = tarjeta(f)
        card.grid(row=1, column=0, sticky="nsew")
        self.grafico = GraficoBarras(card)
        self.grafico.pack(fill="both", expand=True, padx=8, pady=8)
        return f

    def _stock_bajo(self, parent):
        f = tk.Frame(parent, bg=t.BG)
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        tk.Label(f, text="Productos con stock bajo", bg=t.BG, fg=t.TEXTO,
                 font=t.F_SECCION, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 8))
        cols = [("codigo", "Código", 110, "w"), ("producto", "Producto", 190, "w"),
                ("categoria", "Categoría", 110, "w"), ("stock", "Stock", 60, "e"),
                ("estado", "Estado", 80, "w")]
        cont, self.tabla_stock = crear_tabla(f, cols)
        cont.grid(row=1, column=0, sticky="nsew")
        self.lbl_stock = tk.Label(f, text="", bg=t.BG, fg=t.TEXTO_SUAVE, font=("Arial", 9), anchor="w")
        self.lbl_stock.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        return f

    # ---------------------------------------------------------------- Datos
    def recargar(self):
        for w in self.zona_cifras.winfo_children():
            w.destroy()
        if self.ver_stock:
            self.tabla_stock.delete(*self.tabla_stock.get_children())
        try:
            r = reportes.resumen_general()
            todas = [("inventario", "PRODUCTOS", str(r["productos"]), t.NARANJA),
                     ("clientes", "CLIENTES", str(r["clientes"]), "#4aa3ff"),
                     ("facturas", "VENTAS DE HOY", dinero(r["ventas_hoy"]), t.OK),
                     ("cxc", "POR COBRAR", dinero(r["por_cobrar"]), t.AVISO),
                     ("cxp", "POR PAGAR", dinero(r["por_pagar"]), t.ERROR)]
            cifras = [(a, b, c) for sec, a, b, c in todas if puede(self.rol, sec)]
            for i, (titulo, valor, color) in enumerate(cifras):
                self.zona_cifras.grid_columnconfigure(i, weight=1, uniform="k")
                tarjeta_dato(self.zona_cifras, titulo, valor, color).grid(
                    row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            if self.ver_grafico:
                self.grafico.mostrar_ventas(reportes.ventas_ultimos_dias(7))
            if self.ver_stock:
                bajos = inventario.productos_alerta()
                for n, fila in enumerate(bajos):
                    critico = "CR" in str(fila[4]).upper()
                    self.tabla_stock.insert("", "end", values=[formatear(v) for v in fila],
                                            tags=("par" if n % 2 == 0 else "impar",
                                                  "critico" if critico else "bajo"))
                self.lbl_stock.config(
                    text=f"{len(bajos)} producto(s) con stock bajo o crítico." if bajos
                    else "Todo el inventario tiene stock suficiente.", fg=t.TEXTO_SUAVE)
        except Exception as exc:
            tk.Label(self.zona_cifras, text=mensaje_error(exc), bg=t.BG, fg=t.ERROR,
                     font=t.F_TEXTO, justify="left", anchor="w").pack(fill="x")
            if self.ver_stock:
                self.lbl_stock.config(text="")
