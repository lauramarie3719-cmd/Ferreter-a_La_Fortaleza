"""Exportar el contenido de una tabla a un archivo de Excel (.xlsx)."""
import re
from datetime import date, datetime
from decimal import Decimal
from tkinter import filedialog, messagebox

from app.ui.helpers import abrir_archivo, mensaje_error


def _valor(v):
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, bool):
        return "Sí" if v else "No"
    return v


def guardar_excel(ruta, titulo, encabezados, filas):
    """Escribe el archivo .xlsx (sin ventanas; se puede probar por separado)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = re.sub(r"[\[\]\*\?:/\\]", "-", titulo)[:31] or "Datos"
    ws.append(list(encabezados))
    for c in ws[1]:
        c.font = Font(bold=True, color="17191F")
        c.fill = PatternFill("solid", fgColor="F28C28")
        c.alignment = Alignment(horizontal="center", vertical="center")
    for fila in filas:
        ws.append([_valor(v) for v in fila])
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            if isinstance(c.value, str) and c.value.startswith("="):
                c.data_type = "s"            # texto, nunca como fórmula
            elif isinstance(c.value, float):
                c.number_format = "#,##0.00"
            elif isinstance(c.value, datetime):
                c.number_format = "dd/mm/yyyy hh:mm"
            elif isinstance(c.value, date):
                c.number_format = "dd/mm/yyyy"
    for i, col in enumerate(ws.columns, 1):
        ancho = max(len(str(c.value if c.value is not None else "")) for c in col)
        ws.column_dimensions[get_column_letter(i)].width = min(max(ancho + 3, 10), 50)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(ruta)


def exportar_excel(parent, titulo, encabezados, filas):
    """Pide dónde guardar y crea el Excel con lo que se está viendo en la tabla."""
    if not filas:
        messagebox.showinfo("Exportar a Excel", "No hay datos para exportar.", parent=parent)
        return
    nombre = re.sub(r"[^\w\- ]", "", titulo).strip().replace(" ", "_") or "Datos"
    ruta = filedialog.asksaveasfilename(
        parent=parent, title="Guardar como", defaultextension=".xlsx",
        filetypes=[("Archivo de Excel", "*.xlsx")], initialfile=f"{nombre}_{date.today():%Y-%m-%d}.xlsx")
    if not ruta:
        return
    try:
        guardar_excel(ruta, titulo, encabezados, filas)
    except PermissionError:
        messagebox.showerror("No se pudo guardar",
                             "Cierra el archivo si lo tienes abierto en Excel e inténtalo otra vez.", parent=parent)
        return
    except Exception as exc:
        messagebox.showerror("No se pudo exportar", mensaje_error(exc), parent=parent)
        return
    if messagebox.askyesno("Exportado", f"Se guardaron {len(filas)} registro(s).\n¿Abrir el archivo ahora?",
                           parent=parent):
        abrir_archivo(ruta)
