
import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import conectar


def abrir_explorador(ventana_padre):
    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Explorador de tablas - La Fortaleza")
    ventana.geometry("1100x650")
    ventana.configure(bg="#17191f")

    tk.Label(
        ventana,
        text="EXPLORADOR DE BASE DE DATOS",
        bg="#17191f",
        fg="#f28c28",
        font=("Arial", 20, "bold")
    ).pack(pady=15)

    principal = tk.Frame(ventana, bg="#17191f")
    principal.pack(fill="both", expand=True, padx=15, pady=10)

    # Panel izquierdo: lista de tablas
    panel_izquierdo = tk.Frame(principal, bg="#222630", width=230)
    panel_izquierdo.pack(side="left", fill="y", padx=(0, 12))
    panel_izquierdo.pack_propagate(False)

    tk.Label(
        panel_izquierdo,
        text="MIS TABLAS",
        bg="#222630",
        fg="white",
        font=("Arial", 13, "bold")
    ).pack(pady=12)

    lista_tablas = tk.Listbox(
        panel_izquierdo,
        bg="#292d36",
        fg="white",
        selectbackground="#f28c28",
        selectforeground="black",
        font=("Arial", 11),
        relief="flat",
        activestyle="none"
    )
    lista_tablas.pack(fill="both", expand=True, padx=10, pady=5)

    # Panel derecho: registros de la tabla seleccionada
    panel_derecho = tk.Frame(principal, bg="#17191f")
    panel_derecho.pack(side="right", fill="both", expand=True)

    titulo = tk.Label(
        panel_derecho,
        text="Selecciona una tabla",
        bg="#17191f",
        fg="white",
        font=("Arial", 15, "bold")
    )
    titulo.pack(anchor="w", pady=(0, 10))

    contenedor = tk.Frame(panel_derecho, bg="#222630")
    contenedor.pack(fill="both", expand=True)

    tabla_visual = ttk.Treeview(contenedor, show="headings")
    scroll_y = ttk.Scrollbar(
        contenedor, orient="vertical", command=tabla_visual.yview
    )
    scroll_x = ttk.Scrollbar(
        contenedor, orient="horizontal", command=tabla_visual.xview
    )

    tabla_visual.configure(
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set
    )

    tabla_visual.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    contenedor.grid_rowconfigure(0, weight=1)
    contenedor.grid_columnconfigure(0, weight=1)

    estado = tk.Label(
        panel_derecho,
        text="",
        bg="#17191f",
        fg="#cccccc",
        font=("Arial", 10)
    )
    estado.pack(anchor="w", pady=8)

    nombres_tablas = []

    def cargar_tablas():
        try:
            with conectar() as conexion:
                cursor = conexion.cursor()
                cursor.execute("""
                    SELECT TABLE_SCHEMA, TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """)
                resultados = cursor.fetchall()

            nombres_tablas.clear()
            lista_tablas.delete(0, tk.END)

            for fila in resultados:
                esquema = fila[0]
                nombre = fila[1]
                nombres_tablas.append((esquema, nombre))
                lista_tablas.insert(tk.END, nombre)

            estado.config(text=f"Total de tablas: {len(nombres_tablas)}")

            if not nombres_tablas:
                estado.config(text="No se encontraron tablas.")

        except Exception as error:
            messagebox.showerror(
                "Error de conexión",
                f"No se pudieron cargar las tablas:\n{error}"
            )

    def mostrar_registros(event=None):
        seleccion = lista_tablas.curselection()

        if not seleccion:
            return

        esquema, nombre = nombres_tablas[seleccion[0]]

        try:
            # Se escapan los nombres para evitar errores con identificadores.
            tabla_sql = (
                "[" + esquema.replace("]", "]]") + "]."
                "[" + nombre.replace("]", "]]") + "]"
            )

            with conectar() as conexion:
                cursor = conexion.cursor()
                cursor.execute(f"SELECT TOP (500) * FROM {tabla_sql}")
                filas = cursor.fetchall()
                columnas = [columna[0] for columna in cursor.description]

            tabla_visual.delete(*tabla_visual.get_children())
            tabla_visual["columns"] = columnas

            for columna in columnas:
                tabla_visual.heading(columna, text=columna)
                tabla_visual.column(columna, width=150, minwidth=90)

            for fila in filas:
                tabla_visual.insert(
                    "",
                    tk.END,
                    values=[str(valor) if valor is not None else "" for valor in fila]
                )

            titulo.config(text=f"Tabla: {nombre}")
            estado.config(
                text=f"Registros mostrados: {len(filas)} (máximo 500)"
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudo mostrar la tabla:\n{error}"
            )

    lista_tablas.bind("<<ListboxSelect>>", mostrar_registros)

    boton_actualizar = tk.Button(
        panel_izquierdo,
        text="Actualizar tablas",
        command=cargar_tablas,
        bg="#f28c28",
        fg="black",
        font=("Arial", 10, "bold"),
        relief="flat",
        cursor="hand2"
    )
    boton_actualizar.pack(fill="x", padx=10, pady=12)

    cargar_tablas()
