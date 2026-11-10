"""Colores, fuentes y estilos compartidos por todas las interfaces."""
from tkinter import ttk

BG = "#17191f"          # fondo general
PANEL = "#1f222a"       # menú lateral / cabeceras
CARD = "#292d36"        # tarjetas
CARD_ALT = "#2f343e"    # filas alternas
INPUT = "#20232b"       # campos de texto
BORDE = "#3a3f4b"
NARANJA = "#f28c28"
NARANJA_HOVER = "#ffad52"
TEXTO = "#ffffff"
TEXTO_SUAVE = "#9aa0ad"
OK = "#4caf50"
ERROR = "#ff6b61"
AVISO = "#f2c94c"

F_TITULO = ("Arial", 20, "bold")
F_SUBTITULO = ("Arial", 11)
F_SECCION = ("Arial", 13, "bold")
F_TEXTO = ("Arial", 10)
F_ETIQUETA = ("Arial", 9, "bold")
F_BOTON = ("Arial", 10, "bold")
F_NUMERO = ("Arial", 20, "bold")


def aplicar_estilo(root):
    """Configura los widgets ttk (tablas, combos, barras de desplazamiento)."""
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXTO,
                rowheight=28, borderwidth=0, font=F_TEXTO)
    s.configure("Treeview.Heading", background=PANEL, foreground=NARANJA,
                font=("Arial", 10, "bold"), relief="flat", padding=(6, 6))
    s.map("Treeview", background=[("selected", NARANJA)], foreground=[("selected", BG)])
    s.map("Treeview.Heading", background=[("active", BORDE)])

    s.configure("TCombobox", fieldbackground=INPUT, background=CARD, foreground=TEXTO,
                arrowcolor=TEXTO, bordercolor=BORDE, lightcolor=INPUT, darkcolor=INPUT,
                padding=5, selectbackground=INPUT, selectforeground=TEXTO)
    s.map("TCombobox", fieldbackground=[("readonly", INPUT)],
          foreground=[("readonly", TEXTO)], bordercolor=[("focus", NARANJA)])

    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar", background=BORDE, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXTO, lightcolor=BORDE, darkcolor=BORDE)

    root.option_add("*TCombobox*Listbox.background", INPUT)
    root.option_add("*TCombobox*Listbox.foreground", TEXTO)
    root.option_add("*TCombobox*Listbox.selectBackground", NARANJA)
    root.option_add("*TCombobox*Listbox.selectForeground", BG)
