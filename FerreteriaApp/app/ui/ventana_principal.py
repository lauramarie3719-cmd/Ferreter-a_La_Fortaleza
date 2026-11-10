"""Ventana principal: menú lateral con iconos, barra superior con el usuario y área de contenido."""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from app.config import APP_NAME, DB_NAME, DB_SERVER, EMPRESA
from app.ui import theme as t
from app.ui.helpers import boton, centrar, mensaje_error
from app.ui.iconos import Icono
from app.ui.modulos import SECCIONES
from app.ui.permisos import puede

# (nombre del grupo, [(clave de sección, texto del menú)])
MENU = [
    ("PRINCIPAL", [("inicio", "Inicio")]),
    ("GESTIÓN", [("venta", "Nueva venta"), ("inventario", "Inventario"), ("clientes", "Clientes"),
                 ("proveedores", "Proveedores"), ("facturas", "Facturas / Ventas")]),
    ("FINANZAS", [("cxc", "Cuentas por cobrar"), ("cxp", "Cuentas por pagar"), ("banco", "Banco")]),
    ("SISTEMA", [("reportes", "Reportes"), ("auditoria", "Auditoría"), ("usuarios", "Usuarios")]),
]
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


class ItemMenu(tk.Frame):
    """Opción del menú lateral: icono + texto, con resaltado al pasar el mouse y al estar activa."""

    def __init__(self, parent, texto, icono, comando):
        super().__init__(parent, bg=t.PANEL, cursor="hand2")
        self.activo = False
        self.barra = tk.Frame(self, bg=t.PANEL, width=4)
        self.barra.pack(side="left", fill="y")
        self.icono = Icono(self, icono, t.TEXTO_SUAVE, t.PANEL)
        self.icono.pack(side="left", padx=(16, 11), pady=6)
        self.texto = tk.Label(self, text=texto, bg=t.PANEL, fg=t.TEXTO, font=("Arial", 11),
                              anchor="w", cursor="hand2")
        self.texto.pack(side="left", fill="x", expand=True)
        for w in (self, self.barra, self.icono, self.texto):
            w.bind("<Button-1>", lambda e: comando())
            w.bind("<Enter>", lambda e: self._pintar(True))
            w.bind("<Leave>", self._sale)

    def _sale(self, evento):
        bajo = self.winfo_containing(evento.x_root, evento.y_root)
        if bajo is not None and str(bajo).startswith(str(self)):
            return                       # el mouse solo pasó a un hijo del mismo item
        self._pintar(False)

    def _pintar(self, hover):
        fondo = t.CARD if (self.activo or hover) else t.PANEL
        color = t.NARANJA if self.activo else (t.TEXTO if hover else t.TEXTO_SUAVE)
        for w in (self, self.icono, self.texto):
            w.config(bg=fondo)
        self.barra.config(bg=t.NARANJA if self.activo else fondo)
        self.texto.config(fg=t.NARANJA if self.activo else t.TEXTO,
                          font=("Arial", 11, "bold" if self.activo else "normal"))
        self.icono.pintar(color)

    def marcar(self, activo):
        self.activo = activo
        self._pintar(False)


class VentanaPrincipal:
    def __init__(self, usuario):
        self.usuario = usuario
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Panel principal")
        centrar(self.root, 1240, 780)
        self.root.minsize(1060, 700)
        self.root.configure(bg=t.BG)
        t.aplicar_estilo(self.root)

        self.items = {}      # clave -> ItemMenu
        self.orden = []      # secciones visibles, en el orden del menú (para Ctrl+1, Ctrl+2...)
        self.vista_actual = None
        self.actual = None
        self._reloj_id = None
        self._menu_lateral()
        self._area_contenido()
        self._atajos()
        self.navegar("inicio")

    # ---------------------------------------------------------- Menú lateral
    def _menu_lateral(self):
        lateral = tk.Frame(self.root, bg=t.PANEL, width=240)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        # Marca arriba
        marca = tk.Frame(lateral, bg=t.PANEL)
        marca.pack(fill="x", pady=(20, 8))
        Icono(marca, "engranaje", t.NARANJA, t.PANEL, tam=30).pack(side="left", padx=(20, 10))
        textos = tk.Frame(marca, bg=t.PANEL)
        textos.pack(side="left")
        tk.Label(textos, text=EMPRESA["nombre"].upper(), bg=t.PANEL, fg=t.NARANJA, font=("Arial", 14, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(textos, text="Sistema de gestión", bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 8),
                 anchor="w").pack(fill="x")

        # Parte inferior (se empaqueta ANTES que las opciones para que SIEMPRE se vea)
        pie = tk.Frame(lateral, bg=t.PANEL)
        pie.pack(side="bottom", fill="x", pady=(0, 10))
        tk.Frame(pie, bg=t.BORDE, height=1).pack(fill="x", padx=16, pady=(0, 8))
        ItemMenu(pie, "Cerrar sesión", "salir", self.cerrar_sesion).pack(fill="x")
        if puede(self.usuario["rol"], "usuarios"):          # solo roles técnicos ven las tablas crudas
            ItemMenu(pie, "Explorar tablas", "tablas", self.abrir_tablas).pack(fill="x")

        for grupo, opciones in MENU:
            visibles = [(c, x) for c, x in opciones if puede(self.usuario["rol"], c)]
            if not visibles:
                continue
            tk.Label(lateral, text=grupo, bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 8, "bold"),
                     anchor="w").pack(fill="x", padx=20, pady=(12, 2))
            for clave, texto in visibles:
                item = ItemMenu(lateral, texto, clave, lambda k=clave: self.navegar(k))
                item.pack(fill="x")
                self.items[clave] = item
                self.orden.append(clave)

    def _marcar(self, clave):
        for k, item in self.items.items():
            item.marcar(k == clave)

    # ------------------------------------------------------------- Contenido
    def _area_contenido(self):
        der = tk.Frame(self.root, bg=t.BG)
        der.pack(side="left", fill="both", expand=True)

        # Barra de estado (abajo)
        estado = tk.Frame(der, bg=t.PANEL, height=26)
        estado.pack(side="bottom", fill="x")
        self.punto = tk.Canvas(estado, width=10, height=10, bg=t.PANEL, highlightthickness=0)
        self.punto.pack(side="left", padx=(14, 6), pady=8)
        self.lbl_conexion = tk.Label(estado, text="", bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 8))
        self.lbl_conexion.pack(side="left")
        tk.Label(estado, text=f"{APP_NAME} · v1.0", bg=t.PANEL, fg=t.TEXTO_SUAVE,
                 font=("Arial", 8)).pack(side="right", padx=14)
        self._comprobar_conexion()

        # Cabecera: título a la izquierda, reloj + usuario + cerrar sesión a la derecha
        cab = tk.Frame(der, bg=t.BG)
        cab.pack(fill="x", padx=28, pady=(18, 12))
        izq = tk.Frame(cab, bg=t.BG)
        izq.pack(side="left", fill="x", expand=True)
        self.lbl_titulo = tk.Label(izq, text="", bg=t.BG, fg=t.TEXTO, font=t.F_TITULO, anchor="w")
        self.lbl_titulo.pack(fill="x")
        self.lbl_sub = tk.Label(izq, text="", bg=t.BG, fg=t.TEXTO_SUAVE, font=t.F_SUBTITULO, anchor="w")
        self.lbl_sub.pack(fill="x")

        derecha = tk.Frame(cab, bg=t.BG)
        derecha.pack(side="right")
        reloj = tk.Frame(derecha, bg=t.BG)
        reloj.pack(side="left", padx=(0, 16))
        self.lbl_hora = tk.Label(reloj, text="", bg=t.BG, fg=t.TEXTO, font=("Arial", 14, "bold"), anchor="e")
        self.lbl_hora.pack(fill="x")
        self.lbl_fecha = tk.Label(reloj, text="", bg=t.BG, fg=t.TEXTO_SUAVE, font=("Arial", 9), anchor="e")
        self.lbl_fecha.pack(fill="x")
        self._chip_usuario(derecha).pack(side="left")
        self._tick_reloj()

        tk.Frame(der, bg=t.NARANJA, height=2).pack(fill="x", padx=28)
        self.contenido = tk.Frame(der, bg=t.BG)
        self.contenido.pack(fill="both", expand=True, padx=28, pady=18)

    def _chip_usuario(self, parent):
        """Avatar con iniciales + nombre, rol y botón «Cerrar sesión» (visible para todos los roles)."""
        chip = tk.Frame(parent, bg=t.CARD, highlightthickness=1, highlightbackground=t.BORDE)
        palabras = self.usuario["nombre"].split()
        iniciales = "".join(p[0] for p in palabras[:2]).upper() or "?"
        av = tk.Canvas(chip, width=40, height=40, bg=t.CARD, highlightthickness=0)
        av.create_oval(2, 2, 38, 38, fill=t.NARANJA, outline="")
        av.create_text(20, 20, text=iniciales, fill=t.BG, font=("Arial", 12, "bold"))
        av.pack(side="left", padx=(10, 8), pady=8)
        datos = tk.Frame(chip, bg=t.CARD)
        datos.pack(side="left", padx=(0, 12))
        tk.Label(datos, text=self.usuario["nombre"], bg=t.CARD, fg=t.TEXTO, font=("Arial", 10, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(datos, text=self.usuario["rol"], bg=t.CARD, fg=t.NARANJA, font=("Arial", 9),
                 anchor="w").pack(fill="x")
        b = boton(chip, "Cerrar sesión", self.cerrar_sesion, primario=False)
        b.config(padx=10, pady=5, font=("Arial", 9, "bold"))
        b.pack(side="left", padx=(0, 10))
        return chip

    # ------------------------------------------------------- Reloj y estado
    def _tick_reloj(self):
        ahora = datetime.now()
        self.lbl_hora.config(text=ahora.strftime("%I:%M %p").lstrip("0"))
        self.lbl_fecha.config(text=f"{DIAS[ahora.weekday()]}, {ahora.day} {MESES[ahora.month - 1]} {ahora.year}")
        self._reloj_id = self.root.after(15000, self._tick_reloj)

    def _comprobar_conexion(self):
        try:
            from database.connection import conectar
            conectar().close()
            color, texto = t.OK, f"Conectado a {DB_SERVER} · base {DB_NAME}"
        except Exception:
            color, texto = t.ERROR, f"Sin conexión con {DB_SERVER} · base {DB_NAME}"
        self.punto.delete("all")
        self.punto.create_oval(1, 1, 9, 9, fill=color, outline="")
        self.lbl_conexion.config(text=texto)

    def navegar(self, clave):
        if not puede(self.usuario["rol"], clave):
            messagebox.showwarning("Acceso restringido",
                                   "Tu rol no tiene permiso para entrar a esta sección.", parent=self.root)
            return
        titulo, subtitulo, fabrica = SECCIONES[clave]
        for w in self.contenido.winfo_children():
            w.destroy()
        self.actual = clave
        self._marcar(clave)
        self.lbl_titulo.config(text=titulo)
        self.lbl_sub.config(text=subtitulo)
        self.vista_actual = None
        try:
            vista = fabrica(self.contenido, self.usuario, self.navegar)
            vista.pack(fill="both", expand=True)
            self.vista_actual = vista
        except Exception as exc:
            tk.Label(self.contenido, text=f"No se pudo abrir esta sección.\n{mensaje_error(exc)}",
                     bg=t.BG, fg=t.ERROR, font=t.F_SUBTITULO, justify="left").pack(anchor="w")

    # ----------------------------------------------------------------- Atajos
    def _atajos(self):
        """Ctrl+1…9 abren las secciones del menú; F5 actualiza; Ctrl+F busca; Ctrl+Q cierra sesión."""
        for i, clave in enumerate(self.orden[:9], start=1):
            self.root.bind(f"<Control-Key-{i}>", lambda e, k=clave: self.navegar(k))
        self.root.bind("<F5>", lambda e: self._llamar("recargar"))
        self.root.bind("<Control-f>", lambda e: self._llamar("enfocar_busqueda"))
        self.root.bind("<Control-q>", lambda e: self.cerrar_sesion())

    def _llamar(self, metodo):
        accion = getattr(self.vista_actual, metodo, None)
        if callable(accion):
            accion()

    # --------------------------------------------------------------- Acciones
    def abrir_tablas(self):
        try:
            from app.modules.explorar_tablas import abrir_explorador
            abrir_explorador(self.root)
        except Exception as exc:
            messagebox.showerror("Error", mensaje_error(exc), parent=self.root)

    def cerrar_sesion(self):
        if not messagebox.askyesno("Cerrar sesión", f"¿Deseas cerrar la sesión de {self.usuario['nombre']}?",
                                   parent=self.root):
            return
        from app.modules.usuarios import registrar_acceso
        registrar_acceso(self.usuario["usuario_id"], "LOGOUT")
        if self._reloj_id:
            self.root.after_cancel(self._reloj_id)
        self.root.destroy()
        from app.modules.login import iniciar_login
        iniciar_login()

    def iniciar(self):
        self.root.mainloop()
