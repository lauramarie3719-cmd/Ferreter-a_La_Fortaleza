from pathlib import Path
import tkinter as tk
from tkinter import simpledialog

from app.config import APP_NAME, EMPRESA
from app.modules.dashboard import abrir_dashboard
from app.modules.usuarios import autenticar, cambiar_password, registrar_acceso
from app.ui import theme as t
from app.ui.helpers import centrar, mensaje_error
from app.ui.iconos import BotonRedondo, Icono, dibujar_icono

FONDO = Path(__file__).resolve().parents[1] / "assets" / "login_fondo.png"
BLANCO = "#ffffff"


def dibujar_logo(c, cx, y):
    """Logo: casa naranja con martillo (dibujado con líneas, centrado en cx)."""
    ox = cx - 112
    naranja, ancho = t.NARANJA, 7
    c.create_line(ox + 6, y + 70, ox + 138, y + 70, fill=naranja, width=6, capstyle="round")
    c.create_line(ox + 2, y + 62, ox + 98, y + 6, ox + 170, y + 48, fill=naranja, width=ancho,
                  capstyle="round", joinstyle="round")
    c.create_rectangle(ox + 30, y + 20, ox + 41, y + 40, fill=naranja, outline="")
    for dx in (0, 11):
        for dy in (0, 11):
            c.create_rectangle(ox + 88 + dx, y + 24 + dy, ox + 97 + dx, y + 33 + dy, fill=BLANCO, outline="")
    c.create_line(ox + 156, y + 72, ox + 202, y + 30, fill=BLANCO, width=8, capstyle="round")
    c.create_polygon(ox + 184, y + 10, ox + 208, y + 2, ox + 226, y + 14, ox + 220, y + 26,
                     ox + 204, y + 24, ox + 192, y + 22, fill=BLANCO, outline=BLANCO, width=2, joinstyle="round")


def dibujar_panel_marca(c, w, h, fondo=None):
    """Panel izquierdo del login: foto de ferretería con el logo y el nombre del negocio encima."""
    if fondo is not None:
        c.create_image(0, 0, image=fondo, anchor="nw")
    cx = w // 2
    dibujar_logo(c, cx, 58)
    c.create_text(cx, 168, text=EMPRESA["nombre"].upper(), fill=BLANCO, font=("Arial", 30, "bold"))
    c.create_text(cx, 205, text=EMPRESA["eslogan"], fill=t.NARANJA, font=("Arial", 12, "bold"))
    c.create_text(cx, 252, text=EMPRESA["lema"], fill=BLANCO, font=("Arial", 12, "italic"))


class _Sub:
    """Dibuja un icono dentro de un canvas mayor, desplazado (x, y)."""

    def __init__(self, c, dx, dy):
        self.c, self.dx, self.dy = c, dx, dy

    def delete(self, *_):
        pass

    def _mover(self, coords):
        return [v + (self.dx if i % 2 == 0 else self.dy) for i, v in enumerate(coords)]

    def create_line(self, *p, **kw):
        return self.c.create_line(*self._mover(p), **kw)

    def create_polygon(self, *p, **kw):
        return self.c.create_polygon(*self._mover(p), **kw)

    def create_oval(self, *p, **kw):
        return self.c.create_oval(*self._mover(p), **kw)

    def create_rectangle(self, *p, **kw):
        return self.c.create_rectangle(*self._mover(p), **kw)

    def create_arc(self, *p, **kw):
        return self.c.create_arc(*self._mover(p), **kw)

    def create_text(self, x, y, **kw):
        return self.c.create_text(x + self.dx, y + self.dy, **kw)


class CampoLogin(tk.Frame):
    """Campo de texto con icono a la izquierda y, si es contraseña, botón de ojo."""

    def __init__(self, parent, icono, variable, oculto=False):
        super().__init__(parent, bg=t.INPUT, highlightthickness=1, highlightbackground=t.BORDE)
        self.icono = Icono(self, icono, t.TEXTO_SUAVE, t.INPUT)
        self.icono.pack(side="left", padx=(12, 8))
        self.entrada = tk.Entry(self, textvariable=variable, bg=t.INPUT, fg=t.TEXTO, relief="flat", bd=0,
                                insertbackground=t.TEXTO, highlightthickness=0, font=("Arial", 12),
                                show="*" if oculto else "")
        self.entrada.pack(side="left", fill="x", expand=True, ipady=11)
        self.ojo = None
        if oculto:
            self.ojo = Icono(self, "ojo_tachado", t.TEXTO_SUAVE, t.INPUT)
            self.ojo.config(cursor="hand2")
            self.ojo.pack(side="right", padx=(6, 12))
            self.ojo.bind("<Button-1>", lambda e: self.alternar())
            self.ojo.bind("<Enter>", lambda e: self.ojo.pintar(t.NARANJA))
            self.ojo.bind("<Leave>", lambda e: self.ojo.pintar(t.TEXTO_SUAVE))
        self.entrada.bind("<FocusIn>", lambda e: self._foco(True))
        self.entrada.bind("<FocusOut>", lambda e: self._foco(False))

    def _foco(self, activo):
        self.config(highlightbackground=t.NARANJA if activo else t.BORDE)
        self.icono.pintar(t.NARANJA if activo else t.TEXTO_SUAVE)

    def alternar(self):
        """Muestra u oculta la contraseña."""
        visible = self.entrada.cget("show") == ""
        self.entrada.config(show="*" if visible else "")
        self.ojo.nombre = "ojo_tachado" if visible else "ojo"
        self.ojo.pintar(t.TEXTO_SUAVE)


def iniciar_login():
    ventana = tk.Tk()
    ventana.title(f"{APP_NAME} - Iniciar sesión")
    centrar(ventana, 940, 580)
    ventana.resizable(False, False)
    ventana.configure(bg=t.PANEL)

    # ---- Panel izquierdo (marca)
    arte = tk.Canvas(ventana, width=460, height=580, bg=t.NARANJA, highlightthickness=0, bd=0)
    arte.pack(side="left", fill="y")
    try:
        arte.fondo = tk.PhotoImage(file=str(FONDO))      # guardar la referencia evita que se borre
    except tk.TclError:
        arte.fondo = None                                  # sin foto: queda el panel naranja liso
    dibujar_panel_marca(arte, 460, 580, arte.fondo)

    # ---- Panel derecho (formulario)
    derecha = tk.Frame(ventana, bg=t.PANEL)
    derecha.pack(side="left", fill="both", expand=True)
    form = tk.Frame(derecha, bg=t.PANEL, width=340)
    form.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(form, text="Bienvenido de nuevo", bg=t.PANEL, fg=t.TEXTO, font=("Arial", 22, "bold"),
             anchor="w").pack(fill="x")
    tk.Label(form, text="Ingresa tus credenciales para continuar", bg=t.PANEL, fg=t.TEXTO_SUAVE,
             font=("Arial", 10), anchor="w").pack(fill="x", pady=(2, 26))

    var_usuario, var_clave = tk.StringVar(), tk.StringVar()
    tk.Label(form, text="USUARIO", bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 8, "bold"),
             anchor="w").pack(fill="x")
    campo_usuario = CampoLogin(form, "usuario", var_usuario)
    campo_usuario.pack(fill="x", pady=(4, 16))
    tk.Label(form, text="CONTRASEÑA", bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 8, "bold"),
             anchor="w").pack(fill="x")
    campo_clave = CampoLogin(form, "candado", var_clave, oculto=True)
    campo_clave.pack(fill="x", pady=(4, 6))

    lbl_error = tk.Label(form, text="", bg=t.PANEL, fg=t.ERROR, font=("Arial", 9), anchor="w",
                         justify="left", wraplength=340)
    lbl_error.pack(fill="x", pady=(2, 8))

    def entrar(_=None):
        lbl_error.config(text="")
        if not var_usuario.get().strip() or not var_clave.get():
            lbl_error.config(text="Escribe tu usuario y tu contraseña.")
            return
        try:
            usuario = autenticar(var_usuario.get().strip(), var_clave.get())
            if not usuario:
                lbl_error.config(text="Usuario o contraseña incorrectos.")
                campo_clave.entrada.focus_set()
                campo_clave.entrada.select_range(0, "end")
                return
            if usuario["requiere_cambio"]:
                nueva = simpledialog.askstring("Cambiar contraseña",
                    "Debes cambiar tu contraseña (mínimo 8 caracteres):", show="*", parent=ventana)
                if not nueva:
                    return
                cambiar_password(usuario["usuario_id"], nueva)
            registrar_acceso(usuario["usuario_id"], "LOGIN")
            ventana.destroy()
            abrir_dashboard(usuario)
        except Exception as exc:
            lbl_error.config(text=mensaje_error(exc))

    BotonRedondo(form, "INICIAR SESIÓN", entrar, ancho=340, alto=48).pack(pady=(4, 18))
    tk.Label(form, text="¿Olvidaste tu contraseña? Pídele al administrador que la restablezca.",
             bg=t.PANEL, fg=t.TEXTO_SUAVE, font=("Arial", 9), anchor="w", justify="left",
             wraplength=340).pack(fill="x")

    tk.Label(derecha, text="Enter: continuar   ·   Esc: salir", bg=t.PANEL, fg=t.TEXTO_SUAVE,
             font=("Arial", 8)).pack(side="bottom", pady=14)

    campo_usuario.entrada.bind("<Return>", lambda e: campo_clave.entrada.focus_set())
    campo_clave.entrada.bind("<Return>", entrar)
    ventana.bind("<Escape>", lambda e: ventana.destroy())
    campo_usuario.entrada.focus_set()
    ventana.mainloop()
