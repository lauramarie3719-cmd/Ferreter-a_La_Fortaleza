"""Vista genérica: formulario a la izquierda + tabla de registros a la derecha."""
import re
import tkinter as tk
from tkinter import messagebox

from app.ui import theme as t
from app.ui.exportar import exportar_excel
from app.ui.helpers import (boton, combo, crear_tabla, entrada, formatear,
                            mensaje_error)
from app.utils.validators import decimal_positivo

SIN_PROVEEDOR = "— Sin proveedor —"


class ErrorCampo(ValueError):
    def __init__(self, mensaje, clave):
        super().__init__(mensaje)
        self.clave = clave


class VistaCRUD(tk.Frame):
    """Formulario de alta/edición con tabla. Se configura con un diccionario `spec`:

    titulo_singular, id_param, listar, guardar, eliminar (opcional),
    columnas [(clave, encabezado, ancho, alineación)], visibles [claves],
    campos [dict], ancho_form, resaltar (opcional), acciones_extra (opcional),
    proveedores (función que devuelve los proveedores, opcional).
    """

    def __init__(self, parent, usuario, spec):
        super().__init__(parent, bg=t.BG)
        self.usuario = usuario
        self.spec = spec
        self.id_actual = None
        self.filas = {}
        self.vars, self.widgets = {}, {}
        self.mapa_prov, self.mapa_prov_inv = {SIN_PROVEEDOR: None}, {None: SIN_PROVEEDOR}
        self.buscar_var = tk.StringVar()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._construir_formulario()
        self._construir_tabla()
        self.recargar()

    # ------------------------------------------------------------ Formulario
    def _construir_formulario(self):
        s = self.spec
        card = tk.Frame(self, bg=t.CARD, highlightthickness=1, highlightbackground=t.BORDE,
                        width=s.get("ancho_form", 360))
        card.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        card.grid_propagate(False)
        card.pack_propagate(False)

        self.lbl_modo = tk.Label(card, text="", bg=t.CARD, fg=t.NARANJA,
                                 font=t.F_SECCION, anchor="w")
        self.lbl_modo.pack(fill="x", padx=18, pady=(16, 2))
        tk.Label(card, text="Los campos con * son obligatorios.", bg=t.CARD,
                 fg=t.TEXTO_SUAVE, font=("Arial", 9), anchor="w").pack(fill="x", padx=18)

        cuerpo = tk.Frame(card, bg=t.CARD)
        cuerpo.pack(fill="x", padx=18, pady=(10, 0))
        cuerpo.grid_columnconfigure(0, weight=1, uniform="c")
        cuerpo.grid_columnconfigure(1, weight=1, uniform="c")

        fila, col = 0, 0
        for campo in s["campos"]:
            mitad = campo.get("mitad", False)
            if not mitad and col == 1:
                fila, col = fila + 1, 0
            celda = tk.Frame(cuerpo, bg=t.CARD)
            celda.grid(row=fila, column=col, columnspan=1 if mitad else 2, sticky="ew",
                       padx=(0, 6) if mitad and col == 0 else (6, 0) if mitad else 0,
                       pady=(0, 8))
            etiqueta = campo["label"] + (" *" if campo.get("obligatorio") else "")
            tk.Label(celda, text=etiqueta, bg=t.CARD, fg=t.TEXTO_SUAVE,
                     font=t.F_ETIQUETA, anchor="w").pack(fill="x")
            var = tk.StringVar()
            if campo["tipo"] == "proveedor":
                w = combo(celda, var, [])
            elif campo["tipo"] == "combo":
                w = combo(celda, var, campo["valores"], solo_lectura=False)
            elif campo["tipo"] == "password":
                w = entrada(celda, var, show="*")
            else:
                w = entrada(celda, var)
            w.pack(fill="x", pady=(2, 0),
                   ipady=4 if campo["tipo"] in ("texto", "numero", "entero", "password") else 0)
            self.vars[campo["key"]], self.widgets[campo["key"]] = var, w
            w.bind("<Return>", lambda e, k=campo["key"]: self._enter(k))
            if mitad:
                col += 1
                if col == 2:
                    fila, col = fila + 1, 0
            else:
                fila += 1

        self.lbl_estado = tk.Label(card, text="", bg=t.CARD, fg=t.TEXTO_SUAVE,
                                   font=("Arial", 9), anchor="w", justify="left", wraplength=300)
        self.lbl_estado.pack(fill="x", padx=18, pady=(2, 4))

        barra = tk.Frame(card, bg=t.CARD)
        barra.pack(fill="x", padx=18, pady=(0, 6))
        boton(barra, "Guardar", self.guardar).pack(side="left", fill="x", expand=True)
        boton(barra, "Nuevo", self.nuevo, primario=False).pack(
            side="left", fill="x", expand=True, padx=(8, 0))

        extra = tk.Frame(card, bg=t.CARD)
        extra.pack(fill="x", padx=18, pady=(0, 14))
        if s.get("eliminar"):
            boton(extra, s.get("texto_eliminar", "Eliminar seleccionado"), self.eliminar,
                  primario=False).pack(
                fill="x", pady=(0, 6))
        for texto, funcion in s.get("acciones_extra", []):
            boton(extra, texto, lambda f=funcion: f(self), primario=False).pack(fill="x", pady=(0, 6))
        self.nuevo()

    def _enter(self, clave):
        """Enter: pasa al siguiente campo; en el último, guarda."""
        claves = [c["key"] for c in self.spec["campos"]]
        i = claves.index(clave)
        if i + 1 < len(claves):
            self.widgets[claves[i + 1]].focus_set()
        else:
            self.guardar()
        return "break"

    # ----------------------------------------------------------------- Tabla
    def _construir_tabla(self):
        s = self.spec
        der = tk.Frame(self, bg=t.BG)
        der.grid(row=0, column=1, sticky="nsew")
        der.grid_rowconfigure(1, weight=1)
        der.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(der, bg=t.BG)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(barra, text="Buscar:", bg=t.BG, fg=t.TEXTO_SUAVE,
                 font=t.F_ETIQUETA).pack(side="left", padx=(0, 8))
        self.entrada_buscar = entrada(barra, self.buscar_var)
        self.entrada_buscar.pack(side="left", fill="x", expand=True, ipady=4)
        self.buscar_var.trace_add("write", lambda *_: self._pintar())
        boton(barra, "Actualizar", self.recargar, primario=False).pack(side="left", padx=(10, 0))
        boton(barra, "Exportar a Excel", self.exportar, primario=False).pack(side="left", padx=(8, 0))

        cont, self.tree = crear_tabla(der, s["columnas"], s.get("visibles"))
        cont.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)

        self.lbl_total = tk.Label(der, text="", bg=t.BG, fg=t.TEXTO_SUAVE,
                                  font=("Arial", 9), anchor="e")
        self.lbl_total.grid(row=2, column=0, sticky="ew", pady=(6, 0))

    # ----------------------------------------------------------------- Datos
    def recargar(self):
        try:
            if any(c["tipo"] == "proveedor" for c in self.spec["campos"]):
                self._cargar_proveedores()
            claves = [c[0] for c in self.spec["columnas"]]
            self.filas = {}
            for i, fila in enumerate(self.spec["listar"]()):
                self.filas[str(i)] = dict(zip(claves, fila))
            self._pintar()
        except Exception as exc:
            self.filas = {}
            self._pintar()
            self.estado(mensaje_error(exc), error=True)

    def _cargar_proveedores(self):
        self.mapa_prov, self.mapa_prov_inv = {SIN_PROVEEDOR: None}, {None: SIN_PROVEEDOR}
        for fila in self.spec["proveedores"]():
            pid, nombre = fila[0], fila[1]
            if nombre in self.mapa_prov:
                nombre = f"{nombre} (#{pid})"
            self.mapa_prov[nombre] = pid
            self.mapa_prov_inv[pid] = nombre
        for campo in self.spec["campos"]:
            if campo["tipo"] == "proveedor":
                self.widgets[campo["key"]].configure(values=list(self.mapa_prov))

    def _pintar(self):
        filtro = self.buscar_var.get().strip().lower()
        visibles = self.spec.get("visibles") or [c[0] for c in self.spec["columnas"]]
        resaltar = self.spec.get("resaltar")
        self.tree.delete(*self.tree.get_children())
        n = 0
        for iid, d in self.filas.items():
            valores = [formatear(d[c[0]]) for c in self.spec["columnas"]]
            if filtro and not any(filtro in formatear(d[k]).lower() for k in visibles):
                continue
            tags = ["par" if n % 2 == 0 else "impar"]
            marca = resaltar(d) if resaltar else None
            if marca:
                tags.append(marca)
            self.tree.insert("", "end", iid=iid, values=valores, tags=tags)
            n += 1
        self.lbl_total.config(text=f"{n} registro(s)")

    def enfocar_busqueda(self):
        self.entrada_buscar.focus_set()
        self.entrada_buscar.select_range(0, "end")

    def exportar(self):
        """Exporta a Excel lo que se ve en la tabla (respeta la búsqueda)."""
        visibles = self.spec.get("visibles") or [c[0] for c in self.spec["columnas"]]
        cols = [c for c in self.spec["columnas"] if c[0] in visibles]
        filas = [[self.filas[i][c[0]] for c in cols] for i in self.tree.get_children()]
        exportar_excel(self, self.spec.get("titulo_excel", "Datos"), [c[1] for c in cols], filas)

    def fila_seleccionada(self):
        sel = self.tree.selection()
        return self.filas.get(sel[0]) if sel else None

    def _al_seleccionar(self, _=None):
        d = self.fila_seleccionada()
        if not d:
            return
        self.id_actual = d[self.spec["id_param"]]
        for campo in self.spec["campos"]:
            clave = campo["key"]
            if campo["tipo"] == "proveedor":
                valor = self.mapa_prov_inv.get(d.get(clave), SIN_PROVEEDOR)
            elif campo["tipo"] == "password":
                valor = ""
            elif campo["tipo"] == "numero":
                v = d.get(clave)
                valor = "" if v is None else f"{v:.2f}"
            elif campo["tipo"] == "entero":
                v = d.get(clave)
                valor = "" if v is None else str(v)
            else:
                valor = d.get(clave) or ""
            self.vars[clave].set(valor)
            if campo.get("solo_nuevo"):
                self.widgets[clave].config(state="readonly")
        self.lbl_modo.config(text=f"Editar {self.spec['titulo_singular']}")
        self.estado("")

    # ------------------------------------------------------------- Acciones
    def nuevo(self):
        self.id_actual = None
        if hasattr(self, "tree"):
            self.tree.selection_remove(self.tree.selection())
        for campo in self.spec["campos"]:
            clave = campo["key"]
            if campo["tipo"] == "proveedor":
                self.vars[clave].set(SIN_PROVEEDOR)
            else:
                self.vars[clave].set(campo.get("defecto", ""))
            if campo.get("solo_nuevo"):
                self.widgets[clave].config(state="normal")
        self.lbl_modo.config(text=f"Nuevo {self.spec['titulo_singular']}")
        self.estado("")
        primero = self.spec["campos"][0]["key"]
        self.widgets[primero].focus_set()

    def _leer(self):
        datos = {}
        for campo in self.spec["campos"]:
            clave, etiqueta = campo["key"], campo["label"]
            bruto = self.vars[clave].get().strip()
            if campo["tipo"] == "proveedor":
                datos[clave] = self.mapa_prov.get(bruto)
                continue
            if campo["tipo"] == "password":
                if not bruto:
                    if self.id_actual is None:
                        raise ErrorCampo(f"El campo «{etiqueta}» es obligatorio.", clave)
                    datos[clave] = None          # al editar, vacío = no cambiar
                    continue
                if len(bruto) < campo.get("min", 8):
                    raise ErrorCampo(f"«{etiqueta}» debe tener al menos {campo.get('min', 8)} caracteres.", clave)
                datos[clave] = bruto
                continue
            if campo.get("obligatorio") and not bruto:
                raise ErrorCampo(f"El campo «{etiqueta}» es obligatorio.", clave)
            if campo["tipo"] == "entero":
                try:
                    valor = int(bruto.replace(",", "") or "0")
                except ValueError:
                    raise ErrorCampo(f"«{etiqueta}» debe ser un número entero.", clave)
                if valor < 0:
                    raise ErrorCampo(f"«{etiqueta}» no puede ser negativo.", clave)
                datos[clave] = valor
                continue
            if campo["tipo"] == "numero":
                try:
                    datos[clave] = decimal_positivo(bruto.replace(",", "") or "0",
                                                    etiqueta, permitir_cero=True)
                except ValueError as exc:
                    raise ErrorCampo(str(exc), clave)
                continue
            if bruto and campo.get("max") and len(bruto) > campo["max"]:
                raise ErrorCampo(f"«{etiqueta}» admite máximo {campo['max']} caracteres.", clave)
            if bruto and campo.get("patron") and not re.fullmatch(campo["patron"], bruto):
                raise ErrorCampo(campo.get("error", f"El valor de «{etiqueta}» no es válido."), clave)
            datos[clave] = bruto
        return datos

    def guardar(self):
        try:
            datos = self._leer()
        except ErrorCampo as exc:
            self.estado(str(exc), error=True)
            self.widgets[exc.clave].focus_set()
            return
        try:
            self.spec["guardar"](**datos, **{self.spec["id_param"]: self.id_actual},
                                 usuario_id=self.usuario["usuario_id"])
        except Exception as exc:
            self.estado(mensaje_error(exc), error=True)
            return
        editando = self.id_actual is not None
        self.recargar()
        self.nuevo()
        self.estado(f"✔ {self.spec['titulo_singular'].capitalize()} "
                    f"{'actualizado' if editando else 'guardado'} correctamente.", ok=True)

    def eliminar(self):
        if self.id_actual is None:
            self.estado("Selecciona un registro de la tabla primero.", error=True)
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar este {self.spec['titulo_singular']}? Esta acción no se puede deshacer.",
                                   parent=self):
            return
        try:
            self.spec["eliminar"](self.id_actual, usuario_id=self.usuario["usuario_id"])
        except Exception as exc:
            self.estado(mensaje_error(exc), error=True)
            return
        self.recargar()
        self.nuevo()
        self.estado("✔ Registro eliminado.", ok=True)

    def estado(self, texto, error=False, ok=False):
        color = t.ERROR if error else t.OK if ok else t.TEXTO_SUAVE
        self.lbl_estado.config(text=texto, fg=color)
