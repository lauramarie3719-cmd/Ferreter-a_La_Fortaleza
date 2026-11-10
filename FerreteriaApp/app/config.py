import os

try:  # permite poner la configuración en un archivo .env (opcional)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Conexión a SQL Server -------------------------------------------------
# Puedes cambiar estos valores aquí o crear un archivo .env junto a este proyecto:
#   DB_SERVER=MI-PC\SQLEXPRESS
#   DB_NAME=Ferreteria1
DB_SERVER = os.getenv("DB_SERVER", "DESKTOP-LI3N4PH")
DB_NAME = os.getenv("DB_NAME", "Ferreteria1")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
# Déjalos vacíos para usar la autenticación de Windows (lo normal en SSMS local).
DB_USUARIO = os.getenv("DB_USUARIO", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

APP_NAME = "La Fortaleza"

ITBIS_PORCENTAJE = 0.18
DIAS_CAMBIO_PASSWORD = 30
MONEDA = "RD$"

# --- Datos de tu negocio (aparecen en la factura en PDF). Cámbialos por los reales. ---
EMPRESA = {
    "nombre": "La Fortaleza",
    "eslogan": "Construimos confianza, entregamos calidad",
    "lema": "Calidad, variedad y el mejor servicio",
    "rnc": "1-01-00000-0",
    "direccion": "Moca, Provincia Espaillat, República Dominicana",
    "telefono": "809-000-0000",
    "correo": "ventas@lafortaleza.com.do",
}
