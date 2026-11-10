"""Genera la factura de una venta en PDF (carpeta «facturas» del proyecto)."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.config import APP_NAME, EMPRESA, ITBIS_PORCENTAJE, MONEDA
from app.modules.ventas import datos_factura
from app.utils.letras import monto_a_letras

CARPETA = Path(__file__).resolve().parents[2] / "facturas"

CONDICIONES = [
    "Revise su mercancía al momento de la entrega; después de salir del local no se aceptan reclamos por faltantes.",
    "Devoluciones y cambios dentro de los 8 días siguientes, con esta factura y el producto en su empaque original.",
    "Los productos eléctricos, sanitarios y los cortados a medida no tienen devolución una vez entregados.",
    "Esta factura es válida como comprobante de compra. Consérvela para cualquier garantía o reclamación.",
]


def _dinero(v):
    return f"{MONEDA} {Decimal(str(v or 0)):,.2f}"


def generar_factura_pdf(factura_id):
    """Crea el PDF y devuelve la ruta del archivo."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as pdfcanvas
    from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    d = datos_factura(factura_id)
    CARPETA.mkdir(exist_ok=True)
    ruta = CARPETA / f"Factura_{d['numero']}.pdf"

    naranja, oscuro = colors.HexColor("#f28c28"), colors.HexColor("#17191f")
    gris, claro = colors.HexColor("#666666"), colors.HexColor("#f4f4f4")
    linea = colors.HexColor("#dddddd")
    a_credito = (d["tipo_pago"] or "").lower().startswith("cr")

    base = getSampleStyleSheet()["Normal"]
    st = lambda nombre, **kw: ParagraphStyle(nombre, parent=base, **kw)
    s_emp = st("emp", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=oscuro)
    s_peq = st("peq", fontSize=8.5, leading=11.5, textColor=gris)
    s_txt = st("txt", fontSize=9, leading=12.5)
    s_cat = st("cat", fontSize=7.5, leading=9.5, textColor=gris)
    s_tit = st("tit", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.white)
    s_fac = st("fac", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=naranja, alignment=2)
    s_der = st("der", fontSize=9, leading=12.5, alignment=2)
    s_ncf = st("ncf", fontName="Helvetica-Bold", fontSize=11, leading=14, alignment=2)
    s_letras = st("let", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5)

    fecha = d["fecha"] or datetime.now()
    cant_articulos = sum(l[3] for l in d["lineas"])

    def caja(titulo, filas):
        """Cuadro con título oscuro y filas «Etiqueta: valor»."""
        datos = [[Paragraph(titulo, s_tit)]] + [[Paragraph(f"<b>{e}:</b> {v}", s_txt)] for e, v in filas]
        t = Table(datos, colWidths=[8.8 * cm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), oscuro), ("BOX", (0, 0), (-1, -1), 0.6, linea),
                               ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
        return t

    def construir(destino):
        doc = SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                                topMargin=1.4 * cm, bottomMargin=1.8 * cm,
                                title=f"Factura {d['numero']}", author=APP_NAME)
        el = []

        # ---- Encabezado: datos del negocio + recuadro de la factura
        izq = [Paragraph(EMPRESA["nombre"].upper(), s_emp),
               Paragraph(f"<i>{EMPRESA['eslogan']}</i>", s_peq),
               Spacer(1, 4),
               Paragraph(f"RNC: <b>{EMPRESA['rnc']}</b>", s_peq),
               Paragraph(EMPRESA["direccion"], s_peq),
               Paragraph(f"Tel.: {EMPRESA['telefono']}   ·   {EMPRESA['correo']}", s_peq)]
        der = [Paragraph("FACTURA", s_fac),
               Paragraph("Comprobante fiscal / Factura de venta", s_der),
               Spacer(1, 3),
               Paragraph(f"NCF: {d['numero']}", s_ncf),
               Paragraph(f"Fecha de emisión: {fecha:%d/%m/%Y}", s_der),
               Paragraph(f"Hora: {fecha:%I:%M %p}", s_der),
               Paragraph(f"Condición: <b>{'CRÉDITO' if a_credito else 'CONTADO'}</b>", s_der)]
        enc = Table([[izq, der]], colWidths=[10.2 * cm, 7.8 * cm])
        enc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, 0), 2, naranja),
                                 ("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
        el += [enc, Spacer(1, 10)]

        # ---- Cliente y venta
        cliente = caja("DATOS DEL CLIENTE", [
            ("Cliente", d["cliente"]), ("Cédula / RNC", d["cedula"] or "—"),
            ("Teléfono", d["telefono"] or "—"), ("Dirección", d["direccion"] or "—"),
            ("Correo", d["correo"] or "—")])
        venta = caja("DATOS DE LA VENTA", [
            ("Factura interna N.º", d["id"]), ("Atendido por", d["vendedor"] or "—"),
            ("Cargo", d["rol_vendedor"] or "—"), ("Método de pago", d["tipo_pago"]),
            ("Moneda", f"Pesos dominicanos ({MONEDA})")])
        dos = Table([[cliente, venta]], colWidths=[9.1 * cm, 8.9 * cm])
        dos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        el += [dos, Spacer(1, 12)]

        # ---- Detalle de productos
        filas = [["N.º", "Código", "Descripción", "Cant.", "Precio unit.", "Importe"]]
        for i, (codigo, nombre, cat, cant, precio) in enumerate(d["lineas"], 1):
            desc = [Paragraph(nombre, s_txt)] + ([Paragraph(cat, s_cat)] if cat else [])
            filas.append([str(i), Paragraph(codigo or "—", s_cat), desc, str(cant),
                          _dinero(precio), _dinero(Decimal(str(cant)) * Decimal(str(precio)))])
        tabla = Table(filas, colWidths=[1.0 * cm, 3.0 * cm, 6.4 * cm, 1.5 * cm, 3.0 * cm, 3.1 * cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), oscuro), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"), ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, claro]),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, linea), ("BOX", (0, 0), (-1, -1), 0.6, linea),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        el += [tabla, Spacer(1, 10)]

        # ---- Resumen: letras + totales
        resumen_izq = [
            Paragraph(f"<b>Artículos vendidos:</b> {cant_articulos}   ·   <b>Líneas:</b> {len(d['lineas'])}", s_txt),
            Spacer(1, 5), Paragraph("SON:", s_peq), Paragraph(monto_a_letras(d["total"]), s_letras)]
        if a_credito:
            resumen_izq += [Spacer(1, 6), Paragraph(
                f"<b>VENTA A CRÉDITO.</b> Saldo pendiente: <b>{_dinero(d['pendiente'] if d['pendiente'] is not None else d['total'])}</b>"
                + (f" · vence el {d['vence']:%d/%m/%Y}" if d["vence"] else ""), s_txt)]
        else:
            resumen_izq += [Spacer(1, 6), Paragraph("<b>FACTURA PAGADA.</b> Gracias por su pago.", s_txt)]

        tot = Table([["Subtotal", _dinero(d["subtotal"])],
                     [f"ITBIS ({round(ITBIS_PORCENTAJE * 100)}%)", _dinero(d["itbis"])],
                     ["Descuento", f"- {_dinero(d['descuento'])}"],
                     ["TOTAL A PAGAR", _dinero(d["total"])]], colWidths=[3.6 * cm, 3.6 * cm])
        tot.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LINEBELOW", (0, 0), (-1, 2), 0.25, linea),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, -1), (-1, -1), 10.5),
            ("BACKGROUND", (0, -1), (-1, -1), naranja), ("TEXTCOLOR", (0, -1), (-1, -1), oscuro),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        bloque = Table([[resumen_izq, tot]], colWidths=[10.5 * cm, 7.5 * cm])
        bloque.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0),
                                    ("RIGHTPADDING", (-1, 0), (-1, 0), 0), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
        el.append(bloque)

        # ---- Firmas + condiciones (se mantienen juntos en la misma página)
        firmas = Table([["", "", ""], ["Despachado por", "", "Recibido conforme (nombre y firma)"]],
                       colWidths=[7.5 * cm, 3 * cm, 7.5 * cm], rowHeights=[1.1 * cm, None], hAlign="CENTER")
        firmas.setStyle(TableStyle([("LINEABOVE", (0, 1), (0, 1), 0.6, gris), ("LINEABOVE", (2, 1), (2, 1), 0.6, gris),
                                    ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                                    ("TEXTCOLOR", (0, 1), (-1, 1), gris)]))
        cond = [Paragraph("<b>CONDICIONES DE VENTA</b>", s_peq)] + [Paragraph(f"• {c}", s_peq) for c in CONDICIONES]

        el.append(KeepTogether([Spacer(1, 6), firmas, Spacer(1, 12), *cond, Spacer(1, 12),
                                Paragraph("<b>¡Gracias por preferirnos!</b>", st("g", fontSize=10, alignment=1,
                                                                                  textColor=naranja))]))

        # ---- Marca de agua y pie de página con «Página X de Y»
        sello, color_sello = ("A CRÉDITO", colors.HexColor("#d98a1d")) if a_credito else ("PAGADA", colors.HexColor("#2e9e4f"))

        class Numerado(pdfcanvas.Canvas):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                self._paginas = []

            def showPage(self):
                self._paginas.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                total = len(self._paginas)
                for estado in self._paginas:
                    self.__dict__.update(estado)
                    self._pie(total)
                    super().showPage()
                super().save()

            def _pie(self, total):
                self.saveState()
                self.translate(10.5 * cm, 14.8 * cm)
                self.rotate(35)
                self.setFillColor(color_sello)
                self.setFillAlpha(0.07)
                self.setFont("Helvetica-Bold", 90)
                self.drawCentredString(0, 0, sello)
                self.restoreState()
                self.setStrokeColor(linea)
                self.line(1.5 * cm, 1.4 * cm, 19.5 * cm, 1.4 * cm)
                self.setFont("Helvetica", 7.5)
                self.setFillColor(gris)
                self.drawString(1.5 * cm, 0.95 * cm,
                                f"Documento generado por {APP_NAME} el {datetime.now():%d/%m/%Y %I:%M %p}")
                self.drawRightString(19.5 * cm, 0.95 * cm, f"Página {self._pageNumber} de {total}")

        doc.build(el, canvasmaker=Numerado)

    try:
        construir(ruta)
    except PermissionError:          # el PDF anterior está abierto en un visor
        ruta = CARPETA / f"Factura_{d['numero']}_{datetime.now():%H%M%S}.pdf"
        construir(ruta)
    return ruta
