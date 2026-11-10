"""Gráfico de barras sencillo dibujado con Canvas (no necesita librerías extra)."""
import tkinter as tk
from decimal import Decimal

from app.ui import theme as t

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def abreviar(valor):
    v = float(valor)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}k"
    return f"{v:.0f}"


class GraficoBarras(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=t.CARD, highlightthickness=0, height=200, **kw)
        self.datos = []
        self.bind("<Configure>", lambda e: self._dibujar())

    def mostrar_ventas(self, serie):
        """serie: [(fecha, total)] ordenada de más antigua a hoy."""
        self.datos = [(f"{DIAS[d.weekday()]}\n{d.day:02d}/{d.month:02d}", Decimal(str(v or 0)))
                      for d, v in serie]
        self._dibujar()

    def _dibujar(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 60 or h < 60 or not self.datos:
            return
        maximo = max(v for _, v in self.datos)
        if maximo <= 0:
            self.create_text(w / 2, h / 2, text="Sin ventas en los últimos 7 días",
                             fill=t.TEXTO_SUAVE, font=t.F_TEXTO)
            return
        izq, der, arriba, abajo = 12, 12, 24, 38
        base = h - abajo
        paso = (w - izq - der) / len(self.datos)
        ancho = paso * 0.55
        self.create_line(izq, base, w - der, base, fill=t.BORDE)
        for i, (etiqueta, valor) in enumerate(self.datos):
            centro = izq + paso * i + paso / 2
            alto = (base - arriba) * float(valor / maximo)
            if valor > 0:
                color = t.NARANJA if i == len(self.datos) - 1 else "#b8671a"
                self.create_rectangle(centro - ancho / 2, base - alto, centro + ancho / 2, base,
                                      fill=color, outline="")
                self.create_text(centro, base - alto - 9, text=abreviar(valor), fill=t.TEXTO,
                                 font=("Arial", 8, "bold"))
            self.create_text(centro, base + 20, text=etiqueta, fill=t.TEXTO_SUAVE,
                             font=("Arial", 8), justify="center")
