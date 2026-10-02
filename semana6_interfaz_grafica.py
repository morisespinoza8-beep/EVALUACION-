"""
Semana 6 — Interfaz Gráfica y Manejo de Eventos
=================================================
Interfaz gráfica (Tkinter/ttk) para el catálogo de productos desarrollado
en la Semana 5. Este archivo NO redefine el modelo ni la colección: los
importa desde `semana5_coleccion_generica.py`, que debe estar en la misma
carpeta.

Ejecutar con:

    python semana6_interfaz_grafica.py

Autor: Apellido Nombre
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from semana5_coleccion_generica import (
    CATEGORIAS,
    CatalogoError,
    CatalogoProductos,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
    Producto,
    ValidacionError,
    cargar,
    guardar,
)

COLUMNAS = ("id", "nombre", "categoria", "precio", "stock", "valor")
TITULOS = {
    "id": "Código",
    "nombre": "Nombre",
    "categoria": "Categoría",
    "precio": "Precio ($)",
    "stock": "Stock",
    "valor": "Valor ($)",
}


class VentanaPrincipal(tk.Tk):
    """Ventana principal de la aplicación.

    Concentra el manejo de eventos vistos en la Semana 6:
    - ``command`` en botones (clic).
    - ``bind`` de ``<<TreeviewSelect>>`` (selección en la tabla).
    - ``bind`` de ``<Double-1>`` (doble clic sobre una fila).
    - ``bind`` de ``<KeyRelease>`` en el buscador (filtrado en vivo).
    - ``bind`` de ``<Return>``, ``<Escape>``, ``<Delete>``, ``<Control-s>``
      (atajos de teclado).
    - ``<<ComboboxSelected>>`` (filtro por categoría).
    - clic en el encabezado de una columna (ordenamiento).
    - ``protocol("WM_DELETE_WINDOW")`` (evento de cierre de la ventana).
    """

    def __init__(self, catalogo: CatalogoProductos | None = None) -> None:
        super().__init__()
        self.catalogo: CatalogoProductos = catalogo or cargar()
        self.id_seleccionado: str | None = None
        self._orden_descendente: dict[str, bool] = {c: False for c in COLUMNAS}

        self.title("Catálogo de Productos - Semana 6 (Interfaz Gráfica)")
        self.geometry("900x560")
        self.minsize(820, 520)

        self._crear_variables()
        self._construir_interfaz()
        self._registrar_eventos()
        self.refrescar_tabla()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_variables(self) -> None:
        self.var_id = tk.StringVar()
        self.var_nombre = tk.StringVar()
        self.var_categoria = tk.StringVar(value=CATEGORIAS[0])
        self.var_precio = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_busqueda = tk.StringVar()
        self.var_filtro_categoria = tk.StringVar(value="Todas")
        self.var_estado = tk.StringVar(value="Listo")

    def _construir_interfaz(self) -> None:
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=24)
        estilo.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))

        contenedor = ttk.Frame(self, padding=10)
        contenedor.pack(fill=tk.BOTH, expand=True)

        # --- Formulario -------------------------------------------------
        marco_form = ttk.LabelFrame(contenedor, text="Datos del producto", padding=10)
        marco_form.pack(fill=tk.X)

        ttk.Label(marco_form, text="Código:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.entrada_id = ttk.Entry(marco_form, textvariable=self.var_id, width=14)
        self.entrada_id.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(marco_form, text="Nombre:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.entrada_nombre = ttk.Entry(marco_form, textvariable=self.var_nombre, width=32)
        self.entrada_nombre.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(marco_form, text="Categoría:").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        self.combo_categoria = ttk.Combobox(
            marco_form,
            textvariable=self.var_categoria,
            values=list(CATEGORIAS),
            state="readonly",
            width=14,
        )
        self.combo_categoria.grid(row=0, column=5, sticky="w", padx=4, pady=4)

        ttk.Label(marco_form, text="Precio:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.entrada_precio = ttk.Entry(marco_form, textvariable=self.var_precio, width=14)
        self.entrada_precio.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(marco_form, text="Stock:").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.entrada_stock = ttk.Entry(marco_form, textvariable=self.var_stock, width=14)
        self.entrada_stock.grid(row=1, column=3, sticky="w", padx=4, pady=4)

        # --- Botonera ---------------------------------------------------
        marco_botones = ttk.Frame(contenedor, padding=(0, 8))
        marco_botones.pack(fill=tk.X)

        self.boton_agregar = ttk.Button(marco_botones, text="Agregar", command=self.agregar_producto)
        self.boton_actualizar = ttk.Button(
            marco_botones, text="Actualizar", command=self.actualizar_producto, state=tk.DISABLED
        )
        self.boton_eliminar = ttk.Button(
            marco_botones, text="Eliminar", command=self.eliminar_producto, state=tk.DISABLED
        )
        self.boton_limpiar = ttk.Button(marco_botones, text="Limpiar", command=self.limpiar_formulario)
        self.boton_guardar = ttk.Button(marco_botones, text="Guardar en archivo", command=self.guardar_archivo)
        for i, boton in enumerate(
            (self.boton_agregar, self.boton_actualizar, self.boton_eliminar,
             self.boton_limpiar, self.boton_guardar)
        ):
            boton.grid(row=0, column=i, padx=4)

        # --- Búsqueda y filtro -------------------------------------------
        marco_busqueda = ttk.Frame(contenedor)
        marco_busqueda.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(marco_busqueda, text="Buscar:").pack(side=tk.LEFT, padx=(0, 4))
        self.entrada_busqueda = ttk.Entry(marco_busqueda, textvariable=self.var_busqueda, width=30)
        self.entrada_busqueda.pack(side=tk.LEFT)

        ttk.Label(marco_busqueda, text="Categoría:").pack(side=tk.LEFT, padx=(12, 4))
        self.combo_filtro = ttk.Combobox(
            marco_busqueda,
            textvariable=self.var_filtro_categoria,
            values=["Todas", *CATEGORIAS],
            state="readonly",
            width=14,
        )
        self.combo_filtro.pack(side=tk.LEFT)

        ttk.Button(marco_busqueda, text="Bajo stock", command=self.mostrar_bajo_stock).pack(
            side=tk.LEFT, padx=8
        )

        # --- Tabla --------------------------------------------------------
        marco_tabla = ttk.Frame(contenedor)
        marco_tabla.pack(fill=tk.BOTH, expand=True)

        self.tabla = ttk.Treeview(marco_tabla, columns=COLUMNAS, show="headings", selectmode="browse")
        anchos = {"id": 80, "nombre": 260, "categoria": 130, "precio": 100, "stock": 80, "valor": 110}
        for columna in COLUMNAS:
            # Evento: clic en el encabezado ordena por esa columna.
            self.tabla.heading(
                columna,
                text=TITULOS[columna],
                command=lambda c=columna: self.ordenar_por(c),
            )
            alineacion = "w" if columna in ("nombre", "categoria") else "center"
            self.tabla.column(columna, width=anchos[columna], anchor=alineacion)
        self.tabla.tag_configure("bajo_stock", background="#ffe8e8")

        barra = ttk.Scrollbar(marco_tabla, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Barra de estado -----------------------------------------------
        ttk.Separator(contenedor).pack(fill=tk.X, pady=(6, 0))
        ttk.Label(contenedor, textvariable=self.var_estado, anchor="w").pack(fill=tk.X, pady=(4, 0))

    # ------------------------------------------------------------------
    # Registro de eventos
    # ------------------------------------------------------------------
    def _registrar_eventos(self) -> None:
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
        self.tabla.bind("<Double-1>", self.al_doble_clic)
        self.tabla.bind("<Delete>", lambda evento: self.eliminar_producto())
        self.entrada_busqueda.bind("<KeyRelease>", self.al_escribir_busqueda)
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda evento: self.refrescar_tabla())
        self.bind("<Return>", self.al_presionar_enter)
        self.bind("<Escape>", lambda evento: self.limpiar_formulario())
        self.bind("<Control-s>", lambda evento: self.guardar_archivo())
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    # --- Manejadores ----------------------------------------------------
    def al_seleccionar_fila(self, evento: tk.Event | None = None) -> None:
        """Carga en el formulario el producto seleccionado en la tabla."""
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        self.id_seleccionado = seleccion[0]
        producto = self.catalogo.obtener(self.id_seleccionado)
        self.var_id.set(producto.id)
        self.var_nombre.set(producto.nombre)
        self.var_categoria.set(producto.categoria)
        self.var_precio.set(f"{producto.precio:.2f}")
        self.var_stock.set(str(producto.stock))
        self.boton_actualizar.config(state=tk.NORMAL)
        self.boton_eliminar.config(state=tk.NORMAL)
        self._estado(f"Producto seleccionado: {producto.nombre}")

    def al_doble_clic(self, evento: tk.Event) -> None:
        """Doble clic sobre una fila: muestra el detalle del producto."""
        fila = self.tabla.identify_row(evento.y)
        if not fila:
            return
        producto = self.catalogo.obtener(fila)
        messagebox.showinfo(
            "Detalle del producto",
            f"Código: {producto.id}\n"
            f"Nombre: {producto.nombre}\n"
            f"Categoría: {producto.categoria}\n"
            f"Precio: ${producto.precio:,.2f}\n"
            f"Stock: {producto.stock} unidades\n"
            f"Valor en inventario: ${producto.precio * producto.stock:,.2f}",
        )

    def al_escribir_busqueda(self, evento: tk.Event) -> None:
        """Filtrado en vivo mientras el usuario escribe."""
        self.refrescar_tabla()

    def al_presionar_enter(self, evento: tk.Event) -> None:
        """Enter agrega o actualiza según haya o no un producto seleccionado."""
        if self.id_seleccionado:
            self.actualizar_producto()
        else:
            self.agregar_producto()

    def al_cerrar(self) -> None:
        """Evento de cierre: pide confirmación y guarda los datos."""
        if messagebox.askyesno("Salir", "¿Desea guardar los cambios antes de salir?"):
            guardar(self.catalogo)
        self.destroy()

    # ------------------------------------------------------------------
    # Operaciones CRUD (delegadas siempre en la colección de la Semana 5)
    # ------------------------------------------------------------------
    def agregar_producto(self) -> None:
        try:
            producto = self._leer_formulario()
            self.catalogo.agregar(producto)
        except (ValidacionError, ElementoDuplicadoError) as error:
            messagebox.showerror("No se pudo agregar", str(error))
            return
        self.limpiar_formulario()
        self.refrescar_tabla()
        self._estado(f"Producto '{producto.nombre}' agregado.")

    def actualizar_producto(self) -> None:
        if not self.id_seleccionado:
            messagebox.showwarning("Actualizar", "Seleccione primero un producto de la tabla.")
            return
        try:
            producto = self._leer_formulario()
            self.catalogo.actualizar(self.id_seleccionado, producto)
        except CatalogoError as error:
            messagebox.showerror("No se pudo actualizar", str(error))
            return
        self.limpiar_formulario()
        self.refrescar_tabla()
        self._estado(f"Producto '{producto.nombre}' actualizado.")

    def eliminar_producto(self) -> None:
        if not self.id_seleccionado:
            messagebox.showwarning("Eliminar", "Seleccione primero un producto de la tabla.")
            return
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el producto '{self.id_seleccionado}' del catálogo?",
        ):
            return
        try:
            producto = self.catalogo.eliminar(self.id_seleccionado)
        except ElementoNoEncontradoError as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self.limpiar_formulario()
        self.refrescar_tabla()
        self._estado(f"Producto '{producto.nombre}' eliminado.")

    # ------------------------------------------------------------------
    # Consultas desde la interfaz
    # ------------------------------------------------------------------
    def mostrar_bajo_stock(self) -> None:
        productos = self.catalogo.productos_bajo_stock(limite=5)
        if not productos:
            messagebox.showinfo("Bajo stock", "Ningún producto tiene menos de 5 unidades.")
            return
        detalle = "\n".join(f"- {p.nombre}: {p.stock} unidades" for p in productos)
        messagebox.showwarning("Productos con bajo stock", detalle)

    def ordenar_por(self, columna: str) -> None:
        """Ordena la tabla por la columna cuyo encabezado se pulsó."""
        claves = {
            "id": lambda p: p.id,
            "nombre": lambda p: p.nombre.lower(),
            "categoria": lambda p: p.categoria,
            "precio": lambda p: p.precio,
            "stock": lambda p: p.stock,
            "valor": lambda p: p.precio * p.stock,
        }
        descendente = not self._orden_descendente[columna]
        self._orden_descendente[columna] = descendente
        productos = self._productos_visibles()
        productos.sort(key=claves[columna], reverse=descendente)
        self._pintar(productos)
        self._estado(
            f"Ordenado por {TITULOS[columna]} ({'descendente' if descendente else 'ascendente'})."
        )

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _leer_formulario(self) -> Producto:
        """Convierte el contenido del formulario en un ``Producto`` validado."""
        precio_texto = self.var_precio.get().strip().replace(",", ".")
        stock_texto = self.var_stock.get().strip()
        try:
            precio = float(precio_texto) if precio_texto else 0.0
        except ValueError:
            raise ValidacionError("El precio debe ser un número (ej. 12.50).") from None
        try:
            stock = int(stock_texto) if stock_texto else 0
        except ValueError:
            raise ValidacionError("El stock debe ser un número entero (ej. 20).") from None
        return Producto(
            id=self.var_id.get(),
            nombre=self.var_nombre.get(),
            categoria=self.var_categoria.get(),
            precio=precio,
            stock=stock,
        )

    def _productos_visibles(self) -> list[Producto]:
        """Aplica la búsqueda por texto y el filtro de categoría."""
        productos = self.catalogo.buscar_por_texto(self.var_busqueda.get())
        categoria = self.var_filtro_categoria.get()
        if categoria != "Todas":
            productos = [p for p in productos if p.categoria == categoria]
        return productos

    def _pintar(self, productos: list[Producto]) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for producto in productos:
            etiquetas = ("bajo_stock",) if producto.stock < 5 else ()
            self.tabla.insert(
                "",
                tk.END,
                iid=producto.id,
                values=(
                    producto.id,
                    producto.nombre,
                    producto.categoria,
                    f"{producto.precio:,.2f}",
                    producto.stock,
                    f"{producto.precio * producto.stock:,.2f}",
                ),
                tags=etiquetas,
            )

    def refrescar_tabla(self) -> None:
        """Vuelve a dibujar la tabla y actualiza la barra de estado."""
        productos = sorted(self._productos_visibles(), key=lambda p: p.id)
        self._pintar(productos)
        resumen = self.catalogo.resumen()
        self.var_estado.set(
            f"{len(productos)} de {resumen['productos']} productos mostrados | "
            f"{resumen['categorias']} categorías | {resumen['unidades']} unidades | "
            f"valor total: ${resumen['valor_total']:,.2f}"
        )

    def limpiar_formulario(self) -> None:
        self.id_seleccionado = None
        self.var_id.set("")
        self.var_nombre.set("")
        self.var_categoria.set(CATEGORIAS[0])
        self.var_precio.set("")
        self.var_stock.set("")
        self.tabla.selection_remove(*self.tabla.selection())
        self.boton_actualizar.config(state=tk.DISABLED)
        self.boton_eliminar.config(state=tk.DISABLED)
        self.entrada_id.focus_set()

    def guardar_archivo(self) -> None:
        ruta = guardar(self.catalogo)
        self._estado(f"Catálogo guardado en {ruta}")
        messagebox.showinfo("Guardado", f"El catálogo se guardó en:\n{ruta}")

    def _estado(self, mensaje: str) -> None:
        self.var_estado.set(mensaje)
        self.after(4000, self.refrescar_tabla)


def main() -> None:
    """Carga el catálogo (Semana 5) y abre la ventana principal (Semana 6)."""
    catalogo = cargar()
    app = VentanaPrincipal(catalogo)
    app.mainloop()


if __name__ == "__main__":
    main()

