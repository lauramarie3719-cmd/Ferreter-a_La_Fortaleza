"""Formulario de nueva venta (factura): cliente, productos, totales y registro."""
import tkinter as tk
from decimal import Decimal, InvalidOperation

from app.modules import clientes, inventario, ventas
from app.modules.factura_pdf import generar_factura_pdf
from app.ui import theme as t
from app.ui.helpers import (abrir_archivo, boton, combo, crear_tabla, dinero, entrada, mensaje_error,
                            tarjeta)

CONSUMIDOR = "Consumidor final"


class VistaVenta(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=t.BG)
        self.usuario = usuario
        self.carrito, self.productos, self.clientes = [], {}, {CONSUMIDOR: None}
        self.var_cliente = tk.StringVar(value=CONSUMIDOR)
        self.var_pago = tk.StringVar(value="Efectivo")
        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar(value="1")
        self.var_descuento = tk.StringVar(value="0")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._izquierda()
        self._derecha()
        self.var_descuento.trace_add("write", lambda *_: self._recalcular())
        self.cargar_datos()

    # ------------------------------------------------------------ Construcción
    def _etiqueta(self, padre, texto):
        return tk.Label(padre, text=texto, bg=t.CARD, fg=t.TEXTO_SUAVE, font=t.F_ETIQUETA, anchor="w")

    def _izquierda(self):
        izq = tk.Frame(self, bg=t.BG)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        izq.grid_columnconfigure(0, weight=1)
        izq.grid_rowconfigure(2, weight=1)

        datos = tarjeta(izq)
        datos.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        datos.grid_columnconfigure(0, weight=2)
        datos.grid_columnconfigure(1, weight=1)
        self._etiqueta(datos, "Cliente").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        self._etiqueta(datos, "Tipo de pago").grid(row=0, column=1, sticky="w", padx=14, pady=(12, 0))
        self.cb_cliente = combo(datos, self.var_cliente, [CONSUMIDOR])
        self.cb_cliente.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 12))
        combo(datos, self.var_pago, list(ventas.TIPOS_PAGO)).grid(
            row=1, column=1, sticky="ew", padx=14, pady=(2, 12))

        prod = tarjeta(izq)
        prod.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        prod.grid_columnconfigure(0, weight=1)
        self._etiqueta(prod, "Producto (escribe para buscar por nombre o código de barras)").grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        self._etiqueta(prod, "Cantidad").grid(row=0, column=1, sticky="w", padx=6, pady=(12, 0))
        self.cb_producto = combo(prod, self.var_producto, [], solo_lectura=False)
        self.cb_producto.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 4))
        self.cb_producto.bind("<KeyRelease>", self._filtrar)
        self.cb_producto.bind("<<ComboboxSelected>>", lambda e: self._mostrar_info())
        self.cb_producto.bind("<Return>", lambda e: self.agregar())
        e = entrada(prod, self.var_cantidad, width=8)
        e.grid(row=1, column=1, padx=6, pady=(2, 4), ipady=4)
        e.bind("<Return>", lambda ev: self.agregar())
        boton(prod, "Agregar", self.agregar).grid(row=1, column=2, padx=(6, 14), pady=(2, 4))
        self.lbl_info = tk.Label(prod, text="", bg=t.CARD, fg=t.TEXTO_SUAVE, font=("Arial", 9), anchor="w")
        self.lbl_info.grid(row=2, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))

        cols = [("producto", "Producto", 300, "w"), ("cantidad", "Cant.", 70, "e"),
                ("precio", "Precio", 100, "e"), ("importe", "Importe", 110, "e")]
        cont, self.tabla = crear_tabla(izq, cols)
        cont.grid(row=2, column=0, sticky="nsew")
        boton(izq, "Quitar línea seleccionada", self.quitar, primario=False).grid(
            row=3, column=0, sticky="e", pady=(8, 0))

    def _derecha(self):
        der = tarjeta(self, width=320)
        der.grid(row=0, column=1, sticky="ns")
        der.pack_propagate(False)
        tk.Label(der, text="Resumen", bg=t.CARD, fg=t.NARANJA, font=t.F_SECCION,
                 anchor="w").pack(fill="x", padx=18, pady=(16, 8))

        def fila(texto):
            f = tk.Frame(der, bg=t.CARD)
            f.pack(fill="x", padx=18, pady=4)
            tk.Label(f, text=texto, bg=t.CARD, fg=t.TEXTO_SUAVE, font=t.F_TEXTO).pack(side="left")
            lbl = tk.Label(f, text="", bg=t.CARD, fg=t.TEXTO, font=("Arial", 11, "bold"))
            lbl.pack(side="right")
            return lbl

        self.lbl_subtotal = fila("Subtotal")
        self.lbl_itbis = fila("ITBIS (18%)")
        f = tk.Frame(der, bg=t.CARD)
        f.pack(fill="x", padx=18, pady=4)
        tk.Label(f, text="Descuento", bg=t.CARD, fg=t.TEXTO_SUAVE, font=t.F_TEXTO).pack(side="left")
        entrada(f, self.var_descuento, width=12, justify="right").pack(side="right", ipady=3)
        tk.Frame(der, bg=t.BORDE, height=1).pack(fill="x", padx=18, pady=10)
        tk.Label(der, text="TOTAL", bg=t.CARD, fg=t.TEXTO_SUAVE, font=t.F_ETIQUETA,
                 anchor="w").pack(fill="x", padx=18)
        self.lbl_total = tk.Label(der, text="", bg=t.CARD, fg=t.NARANJA, font=("Arial", 24, "bold"), anchor="w")
        self.lbl_total.pack(fill="x", padx=18, pady=(0, 10))

        self.lbl_estado = tk.Label(der, text="", bg=t.CARD, fg=t.TEXTO_SUAVE, font=("Arial", 9),
                                   anchor="w", justify="left", wraplength=280)
        self.lbl_estado.pack(fill="x", padx=18, pady=(0, 8))
        boton(der, "Registrar venta", self.registrar).pack(fill="x", padx=18, pady=(0, 6))
        boton(der, "Limpiar", self.limpiar, primario=False).pack(fill="x", padx=18)
        self._recalcular()

    # ------------------------------------------------------------------- Datos
    def cargar_datos(self):
        try:
            self.clientes = {CONSUMIDOR: None}
            for cid, nom, ape, ced in clientes.para_venta():
                self.clientes[f"{nom} {ape} — {ced}"] = cid
            self.cb_cliente.configure(values=list(self.clientes))
            self.productos = {}
            for pid, codigo, nombre, precio, stock in inventario.para_venta():
                clave = f"{nombre} [{codigo}]" if codigo else nombre
                if clave in self.productos:
                    clave = f"{clave} (#{pid})"
                self.productos[clave] = {"producto_id": pid, "codigo": codigo, "nombre": nombre,
                                         "precio": precio, "stock": stock or 0}
            self.cb_producto.configure(values=list(self.productos))
        except Exception as exc:
            self.estado(mensaje_error(exc), error=True)

    def _filtrar(self, evento=None):
        if evento is not None and evento.keysym in ("Return", "Up", "Down", "Tab"):
            return
        txt = self.var_producto.get().strip().lower()
        self.cb_producto.configure(values=[k for k in self.productos if txt in k.lower()] if txt
                                   else list(self.productos))
        self._mostrar_info()

    def _resolver(self):
        txt = self.var_producto.get().strip()
        if txt in self.productos:
            return self.productos[txt]
        bajo = txt.lower()
        if not bajo:
            return None
        for p in self.productos.values():
            if p["codigo"] and p["codigo"].lower() == bajo:
                return p
        coincidencias = [p for k, p in self.productos.items() if bajo in k.lower()]
        return coincidencias[0] if len(coincidencias) == 1 else None

    def _mostrar_info(self):
        p = self._resolver()
        self.lbl_info.config(text=f"Precio: {dinero(p['precio'])}   ·   Disponible: {p['stock']}" if p else "")

    # ----------------------------------------------------------------- Acciones
    def agregar(self):
        p = self._resolver()
        if not p:
            return self.estado("Elige un producto de la lista.", error=True)
        try:
            cantidad = int(self.var_cantidad.get().strip())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            return self.estado("La cantidad debe ser un número entero mayor que cero.", error=True)
        linea = next((l for l in self.carrito if l["producto_id"] == p["producto_id"]), None)
        if (linea["cantidad"] if linea else 0) + cantidad > p["stock"]:
            return self.estado(f"Solo hay {p['stock']} unidad(es) de «{p['nombre']}».", error=True)
        if linea:
            linea["cantidad"] += cantidad
        else:
            self.carrito.append({"producto_id": p["producto_id"], "nombre": p["nombre"],
                                 "cantidad": cantidad, "precio": p["precio"]})
        self.var_producto.set("")
        self.var_cantidad.set("1")
        self.lbl_info.config(text="")
        self.cb_producto.configure(values=list(self.productos))
        self.cb_producto.focus_set()
        self.estado("")
        self._pintar_carrito()

    def quitar(self):
        sel = self.tabla.selection()
        if not sel:
            return self.estado("Selecciona una línea de la tabla para quitarla.", error=True)
        self.carrito.pop(int(sel[0]))
        self._pintar_carrito()

    def _pintar_carrito(self):
        self.tabla.delete(*self.tabla.get_children())
        for i, l in enumerate(self.carrito):
            importe = l["cantidad"] * l["precio"]
            self.tabla.insert("", "end", iid=str(i), tags=("par" if i % 2 == 0 else "impar",),
                              values=(l["nombre"], l["cantidad"], f"{l['precio']:,.2f}", f"{importe:,.2f}"))
        self._recalcular()

    def _descuento(self, estricto=False):
        texto = self.var_descuento.get().strip().replace(",", "") or "0"
        try:
            valor = Decimal(texto)
            if valor < 0:
                raise InvalidOperation
            return valor
        except InvalidOperation:
            if estricto:
                raise ValueError("El descuento debe ser un número válido (0 o mayor).")
            return Decimal("0")

    def _recalcular(self):
        sub, itbis, desc, total = ventas.calcular_totales(self.carrito, self._descuento())
        self.lbl_subtotal.config(text=dinero(sub))
        self.lbl_itbis.config(text=dinero(itbis))
        self.lbl_total.config(text=dinero(total))

    def registrar(self):
        try:
            descuento = self._descuento(estricto=True)
            fid, numero, total = ventas.registrar_venta(
                self.clientes.get(self.var_cliente.get()), self.usuario["usuario_id"],
                self.var_pago.get(), self.carrito, descuento)
        except Exception as exc:
            return self.estado(mensaje_error(exc), error=True)
        self.limpiar()
        self.cargar_datos()          # el stock cambió (lo descuenta tu trigger)
        mensaje = f"✔ Venta registrada: factura {numero} por {dinero(total)}."
        try:
            abrir_archivo(generar_factura_pdf(fid))
            mensaje += "\nLa factura en PDF se guardó en la carpeta «facturas»."
        except Exception as exc:
            mensaje += f"\nNo se pudo crear el PDF: {mensaje_error(exc)}"
        self.estado(mensaje, ok=True)

    def limpiar(self):
        self.carrito = []
        self.var_cliente.set(CONSUMIDOR)
        self.var_pago.set("Efectivo")
        self.var_producto.set("")
        self.var_cantidad.set("1")
        self.var_descuento.set("0")
        self.lbl_info.config(text="")
        self._pintar_carrito()
        self.estado("")

    def estado(self, texto, error=False, ok=False):
        self.lbl_estado.config(text=texto, fg=t.ERROR if error else t.OK if ok else t.TEXTO_SUAVE)
