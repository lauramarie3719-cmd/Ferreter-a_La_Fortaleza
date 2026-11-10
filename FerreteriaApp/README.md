# La Fortaleza

Aplicación de escritorio (Python + Tkinter) conectada a SQL Server (base `Ferreteria1`).

## Ejecutar
1. `pip install -r requirements.txt`
2. Revisa `app/config.py` (o crea un `.env`): `DB_SERVER` debe ser el nombre de tu servidor SQL.
3. En `app/config.py` cambia también `EMPRESA` (nombre, RNC, dirección, teléfono): salen en la factura PDF.
4. (Solo la primera vez) `python crear_admin.py` para crear un administrador.
5. `python -m app.main`

Todo lo que se guarda en la app se escribe directamente en SQL Server, y lo que cambies
en SQL Server se ve en la app al pulsar **Actualizar** (F5) o al cambiar de pantalla.

## Atajos
Ctrl+1…9 abre una sección · F5 actualiza · Ctrl+F busca · Ctrl+Q cierra sesión · Enter avanza entre campos.

## Roles
Los permisos por rol están en `app/ui/permisos.py`.
