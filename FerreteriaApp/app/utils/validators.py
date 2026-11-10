from decimal import Decimal, InvalidOperation

def texto_obligatorio(valor, campo):
    valor = str(valor).strip()
    if not valor:
        raise ValueError(f"El campo {campo} es obligatorio.")
    return valor

def decimal_positivo(valor, campo="monto", permitir_cero=False):
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        raise ValueError(f"{campo} debe ser un número válido.")
    if numero < 0 or (numero == 0 and not permitir_cero):
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return numero
