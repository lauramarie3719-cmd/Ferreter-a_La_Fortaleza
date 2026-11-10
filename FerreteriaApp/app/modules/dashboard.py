from app.ui.ventana_principal import VentanaPrincipal


def abrir_dashboard(usuario):
    """Abre la ventana principal (menú lateral + pantallas del sistema)."""
    VentanaPrincipal(usuario).iniciar()
