"""Convierte montos a letras en español (para la factura): 1493.00 -> MIL CUATROCIENTOS ..."""
from decimal import ROUND_HALF_UP, Decimal

_UNI = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
        "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho",
        "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
        "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_DEC = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta",
        80: "ochenta", 90: "noventa"}
_CEN = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
        500: "quinientos", 600: "seiscientos", 700: "setecientos", 800: "ochocientos",
        900: "novecientos"}


def _menor_mil(n):
    if n == 100:
        return "cien"
    partes = []
    c, r = n // 100 * 100, n % 100
    if c:
        partes.append(_CEN[c])
    if r:
        if r < 30:
            partes.append(_UNI[r])
        else:
            d, u = r // 10 * 10, r % 10
            partes.append(_DEC[d] + (f" y {_UNI[u]}" if u else ""))
    return " ".join(partes)


def _apocope(texto):
    if texto.endswith("veintiuno"):
        return texto[:-9] + "veintiún"
    return texto[:-1] if texto.endswith("uno") else texto


def entero_a_letras(n):
    if n == 0:
        return "cero"
    if n >= 1_000_000_000:
        return str(n)
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("un millón" if millones == 1 else f"{_apocope(_menor_mil(millones))} millones")
    if miles:
        partes.append("mil" if miles == 1 else f"{_apocope(_menor_mil(miles))} mil")
    if unidades:
        partes.append(_menor_mil(unidades))
    return " ".join(partes)


def monto_a_letras(monto, moneda_singular="peso dominicano", moneda_plural="pesos dominicanos"):
    """Ejemplo: 1493.5 -> 'MIL CUATROCIENTOS NOVENTA Y TRES PESOS DOMINICANOS CON 50/100'."""
    total = (Decimal(str(monto)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    entero, centavos = divmod(int(total), 100)
    texto = _apocope(entero_a_letras(entero))      # "uno peso" -> "un peso"
    if entero and entero % 1_000_000 == 0:
        texto += " de"
    moneda = moneda_singular if entero == 1 else moneda_plural
    return f"{texto} {moneda} con {centavos:02d}/100".upper()
