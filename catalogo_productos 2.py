"""
Catálogo de Productos — Semanas 5 y 6
======================================
Colecciones, Genéricos, Interfaz Gráfica y Manejo de Eventos.

Archivo único, listo para ejecutar con:

    python catalogo_productos.py

Requisitos: Python 3.10+ con Tkinter (incluido en la instalación estándar).
No requiere librerías externas.

Autor: Apellido Nombre
"""

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable, Generic, Iterator, Protocol, TypeVar, runtime_checkable

# ======================================================================
# 1. EXCEPCIONES DEL DOMINIO
# ======================================================================


class CatalogoError(Exception):
    """Excepción base de la aplicación."""


class ValidacionError(CatalogoError):
    """Se lanza cuando los datos de un producto no son válidos."""


class ElementoDuplicadoError(CatalogoError):
    """Se lanza al intentar agregar un elemento con un ID ya existente."""


class ElementoNoEncontradoError(CatalogoError):
    """Se lanza al consultar, actualizar o eliminar un ID inexistente."""


# ======================================================================
# 2. MODELO: Producto  (Semana 5 — clase de dominio)
# ======================================================================

CATEGORIAS = (
    "Electrónica",
    "Alimentos",
    "Hogar",
    "Ropa",
    "Papelería",
    "Otros",
)


@dataclass
class Producto:
    """Representa un producto del catálogo.

    Attributes:
        id: código único del producto (por ejemplo ``P001``).
        nombre: nombre comercial.
        categoria: una de las categorías definidas en ``CATEGORIAS``.
        precio: precio unitario en dólares, mayor o igual a 0.
        stock: unidades disponibles, entero mayor o igual a 0.
    """

    id: str
    nombre: str
    categoria: str = "Otros"
    precio: float = 0.0
    stock: int = 0

    valor_inventario: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.validar()
        self.id = self.id.strip().upper()
        self.nombre = self.nombre.strip()
        self.precio = float(self.precio)
        self.stock = int(self.stock)
        self.valor_inventario = round(self.precio * self.stock, 2)

    def validar(self) -> None:
        """Valida los datos del producto.

        Raises:
            ValidacionError: si algún campo no cumple las reglas de negocio.
        """
        if not str(self.id).strip():
            raise ValidacionError("El código del producto es obligatorio.")
        if not str(self.nombre).strip():
            raise ValidacionError("El nombre del producto es obligatorio.")
        if len(str(self.nombre).strip()) < 3:
            raise ValidacionError("El nombre debe tener al menos 3 caracteres.")
        if self.categoria not in CATEGORIAS:
            raise ValidacionError(
                f"Categoría inválida. Use una de: {', '.join(CATEGORIAS)}."
            )
        try:
            precio = float(self.precio)
        except (TypeError, ValueError):
            raise ValidacionError("El precio debe ser un número.") from None
        if precio < 0:
            raise ValidacionError("El precio no puede ser negativo.")
        try:
            stock = int(self.stock)
        except (TypeError, ValueError):
            raise ValidacionError("El stock debe ser un número entero.") from None
        if stock < 0:
            raise ValidacionError("El stock no puede ser negativo.")

    def a_diccionario(self) -> dict[str, Any]:
        """Convierte el producto en un diccionario (para guardar en JSON)."""
        datos = asdict(self)
        datos.pop("valor_inventario", None)
        return datos

    @classmethod
    def desde_diccionario(cls, datos: dict[str, Any]) -> "Producto":
        """Crea un producto a partir de un diccionario."""
        return cls(
            id=datos["id"],
            nombre=datos["nombre"],
            categoria=datos.get("categoria", "Otros"),
            precio=datos.get("precio", 0.0),
            stock=datos.get("stock", 0),
        )

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.nombre} | {self.categoria} | "
            f"${self.precio:,.2f} | stock: {self.stock}"
        )


# ======================================================================
# 3. COLECCIÓN GENÉRICA  (Semana 5 — TypeVar, Generic, Protocol)
# ======================================================================


@runtime_checkable
class Identificable(Protocol):
    """Contrato mínimo que debe cumplir toda entidad almacenable."""

    id: str


# T queda acotado (bound) a las clases que cumplen el protocolo Identificable.
T = TypeVar("T", bound=Identificable)


class RepositorioGenerico(Generic[T]):
    """Colección genérica en memoria con operaciones CRUD.

    Internamente usa un ``dict`` (clave = id) porque ofrece búsqueda,
    inserción y eliminación en tiempo constante, a diferencia de una lista.
    No está atada a ``Producto``: funciona con cualquier clase que tenga un
    atributo ``id`` (por eso es "genérica").
    """

    def __init__(self, elementos: list[T] | None = None) -> None:
        self._elementos: dict[str, T] = {}
        for elemento in elementos or []:
            self.agregar(elemento)

    # --------------------------- CRUD --------------------------------
    def agregar(self, elemento: T) -> T:
        """Agrega un elemento nuevo.

        Raises:
            ElementoDuplicadoError: si ya existe un elemento con ese id.
        """
        clave = str(elemento.id)
        if clave in self._elementos:
            raise ElementoDuplicadoError(f"Ya existe un elemento con el código '{clave}'.")
        self._elementos[clave] = elemento
        return elemento

    def obtener(self, id_elemento: str) -> T:
        """Devuelve el elemento con el id indicado.

        Raises:
            ElementoNoEncontradoError: si el id no existe.
        """
        clave = str(id_elemento).strip().upper()
        if clave not in self._elementos:
            raise ElementoNoEncontradoError(f"No existe el elemento con código '{clave}'.")
        return self._elementos[clave]

    def listar(self) -> list[T]:
        """Devuelve todos los elementos como lista (copia defensiva)."""
        return list(self._elementos.values())

    def actualizar(self, id_elemento: str, elemento: T) -> T:
        """Reemplaza el elemento identificado por ``id_elemento``."""
        clave_original = str(id_elemento).strip().upper()
        if clave_original not in self._elementos:
            raise ElementoNoEncontradoError(
                f"No existe el elemento con código '{clave_original}'."
            )
        clave_nueva = str(elemento.id)
        if clave_nueva != clave_original and clave_nueva in self._elementos:
            raise ElementoDuplicadoError(f"Ya existe un elemento con el código '{clave_nueva}'.")
        del self._elementos[clave_original]
        self._elementos[clave_nueva] = elemento
        return elemento

    def eliminar(self, id_elemento: str) -> T:
        """Elimina y devuelve el elemento indicado."""
        clave = str(id_elemento).strip().upper()
        if clave not in self._elementos:
            raise ElementoNoEncontradoError(f"No existe el elemento con código '{clave}'.")
        return self._elementos.pop(clave)

    def vaciar(self) -> None:
        """Elimina todos los elementos de la colección."""
        self._elementos.clear()

    # --------------- Consultas de alto orden (lambdas) ----------------
    def buscar(self, criterio: Callable[[T], bool]) -> list[T]:
        """Devuelve los elementos que cumplen el criterio recibido."""
        return [e for e in self._elementos.values() if criterio(e)]

    def ordenar(self, clave: Callable[[T], object], descendente: bool = False) -> list[T]:
        """Devuelve los elementos ordenados según la clave indicada."""
        return sorted(self._elementos.values(), key=clave, reverse=descendente)

    def agrupar_por(self, clave: Callable[[T], str]) -> dict[str, list[T]]:
        """Agrupa los elementos en un diccionario de listas."""
        grupos: dict[str, list[T]] = {}
        for elemento in self._elementos.values():
            grupos.setdefault(clave(elemento), []).append(elemento)
        return grupos

    def existe(self, id_elemento: str) -> bool:
        """Indica si el id está registrado."""
        return str(id_elemento).strip().upper() in self._elementos

    # ------------------- Métodos especiales ---------------------------
    def __len__(self) -> int:
        return len(self._elementos)

    def __iter__(self) -> Iterator[T]:
        return iter(self._elementos.values())

    def __contains__(self, id_elemento: object) -> bool:
        return str(id_elemento).strip().upper() in self._elementos

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(elementos={len(self)})"


class CatalogoProductos(RepositorioGenerico[Producto]):
    """Colección especializada de productos (hereda el CRUD genérico)."""

    # --------------------------- Búsquedas -----------------------------
    def buscar_por_texto(self, texto: str) -> list[Producto]:
        """Busca por coincidencia parcial en el código o el nombre."""
        texto = texto.strip().lower()
        if not texto:
            return self.listar()
        return self.buscar(
            lambda p: texto in p.nombre.lower() or texto in p.id.lower()
        )

    def filtrar_por_categoria(self, categoria: str) -> list[Producto]:
        """Devuelve los productos de una categoría."""
        return self.buscar(lambda p: p.categoria == categoria)

    def filtrar_por_rango_precio(self, minimo: float, maximo: float) -> list[Producto]:
        """Devuelve los productos cuyo precio está en el rango indicado."""
        return self.buscar(lambda p: minimo <= p.precio <= maximo)

    def productos_bajo_stock(self, limite: int = 5) -> list[Producto]:
        """Devuelve los productos con stock por debajo del límite."""
        return self.buscar(lambda p: p.stock < limite)

    # -------------------------- Estadísticas ----------------------------
    def categorias_registradas(self) -> set[str]:
        """Conjunto (``set``) de categorías presentes: no admite repetidos."""
        return {p.categoria for p in self}

    def por_categoria(self) -> dict[str, list[Producto]]:
        """Diccionario categoría -> lista de productos."""
        return self.agrupar_por(lambda p: p.categoria)

    def valor_total_inventario(self) -> float:
        """Suma de precio * stock de todos los productos."""
        return round(sum(p.precio * p.stock for p in self), 2)

    def unidades_totales(self) -> int:
        """Total de unidades almacenadas."""
        return sum(p.stock for p in self)

    def producto_mas_caro(self) -> Producto | None:
        """Producto de mayor precio, o ``None`` si el catálogo está vacío."""
        if len(self) == 0:
            return None
        return max(self, key=lambda p: p.precio)

    def resumen(self) -> dict[str, object]:
        """Resumen usado por la barra de estado de la interfaz gráfica."""
        return {
            "productos": len(self),
            "categorias": len(self.categorias_registradas()),
            "unidades": self.unidades_totales(),
            "valor_total": self.valor_total_inventario(),
        }


# ======================================================================
# 4. PERSISTENCIA EN JSON
# ======================================================================

RUTA_DATOS = Path(__file__).resolve().parent / "catalogo.json"


def guardar(catalogo: CatalogoProductos, ruta: Path = RUTA_DATOS) -> Path:
    """Guarda el catálogo en un archivo JSON."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = [p.a_diccionario() for p in catalogo.ordenar(lambda p: p.id)]
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def cargar(ruta: Path = RUTA_DATOS) -> CatalogoProductos:
    """Carga el catálogo desde un archivo JSON.

    Si el archivo no existe o está dañado, crea un catálogo con datos de
    ejemplo para que la aplicación siempre pueda iniciarse.
    """
    catalogo = CatalogoProductos()
    try:
        contenido = json.loads(Path(ruta).read_text(encoding="utf-8"))
        for registro in contenido:
            catalogo.agregar(Producto.desde_diccionario(registro))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        for producto in datos_de_ejemplo():
            catalogo.agregar(producto)
    return catalogo


def datos_de_ejemplo() -> list[Producto]:
    """Productos iniciales para probar la aplicación."""
    return [
        Producto("P001", "Teclado mecánico", "Electrónica", 45.90, 12),
        Producto("P002", "Mouse inalámbrico", "Electrónica", 18.50, 30),
        Producto("P003", "Café molido 500 g", "Alimentos", 7.25, 48),
        Producto("P004", "Juego de sábanas", "Hogar", 32.00, 9),
        Producto("P005", "Camiseta algodón", "Ropa", 12.75, 3),
        Producto("P006", "Cuaderno A4", "Papelería", 2.40, 100),
    ]


# ======================================================================
# 5. INTERFAZ GRÁFICA  (Semana 6 — Tkinter/ttk y manejo de eventos)
# ======================================================================

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
    """Ventana principal de la aplicación."""

    def __init__(self, catalogo: CatalogoProductos | None = None) -> None:
        super().__init__()
        self.catalogo: CatalogoProductos = catalogo or cargar()
        self.id_seleccionado: str | None = None
        self._orden_descendente: dict[str, bool] = {c: False for c in COLUMNAS}

        self.title("Catálogo de Productos - Semanas 5 y 6")
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
    # Operaciones CRUD
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


# ======================================================================
# 6. PUNTO DE ENTRADA
# ======================================================================


def main() -> None:
    """Carga el catálogo y abre la ventana principal."""
    catalogo = cargar()
    app = VentanaPrincipal(catalogo)
    app.mainloop()


if __name__ == "__main__":
    main()
