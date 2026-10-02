"""
Semana 5 — Colecciones y Genéricos
===================================
Catálogo de productos: modelo de datos, colección genérica (TypeVar,
Generic, Protocol) y persistencia en JSON.

Este módulo se puede ejecutar solo para ver una demostración por consola
de las operaciones CRUD sobre la colección:

    python semana5_coleccion_generica.py

También es importado por `semana6_interfaz_grafica.py`, que construye la
interfaz gráfica sobre esta misma colección.

Autor: Apellido Nombre
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
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
# 2. MODELO: Producto
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

    # Campo calculado, no se recibe en el constructor.
    valor_inventario: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.validar()
        self.id = self.id.strip().upper()
        self.nombre = self.nombre.strip()
        self.precio = float(self.precio)
        self.stock = int(self.stock)
        self.valor_inventario = round(self.precio * self.stock, 2)

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
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
# 3. COLECCIÓN GENÉRICA (TypeVar, Generic, Protocol)
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

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
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
        """Reemplaza el elemento identificado por ``id_elemento``.

        Permite además cambiar el código: si el nuevo id ya pertenece a otro
        elemento se lanza ``ElementoDuplicadoError``.
        """
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

    # ------------------------------------------------------------------
    # Consultas de alto orden (funciones lambda como parámetro)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Métodos especiales: la colección se comporta como un contenedor Python
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Búsquedas y filtros
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------
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
# 5. DEMOSTRACIÓN POR CONSOLA (solo si se ejecuta este archivo directamente)
# ======================================================================


def _demo() -> None:
    """Muestra por consola las operaciones CRUD y de consulta del catálogo."""
    print("=" * 60)
    print("DEMO — Semana 5: Colecciones y Genéricos")
    print("=" * 60)

    catalogo = CatalogoProductos(datos_de_ejemplo())
    print(f"\n1) Catálogo inicial ({len(catalogo)} productos):")
    for producto in catalogo.ordenar(lambda p: p.id):
        print("   ", producto)

    print("\n2) Agregar un producto nuevo (P007):")
    catalogo.agregar(Producto("P007", "Audífonos bluetooth", "Electrónica", 29.90, 7))
    print("   ", catalogo.obtener("P007"))

    print("\n3) Intentar agregar un código duplicado (P007):")
    try:
        catalogo.agregar(Producto("P007", "Otro producto", "Hogar", 1.0, 1))
    except ElementoDuplicadoError as error:
        print("    Error controlado:", error)

    print("\n4) Actualizar el precio de P002:")
    p2 = catalogo.obtener("P002")
    catalogo.actualizar("P002", Producto("P002", p2.nombre, p2.categoria, 15.99, p2.stock))
    print("   ", catalogo.obtener("P002"))

    print("\n5) Buscar productos que contengan 'a' en el nombre o código:")
    for p in catalogo.buscar_por_texto("a"):
        print("   ", p)

    print("\n6) Productos con menos de 5 unidades en stock:")
    for p in catalogo.productos_bajo_stock(5):
        print("   ", p)

    print("\n7) Categorías registradas (set, sin repetidos):")
    print("   ", catalogo.categorias_registradas())

    print("\n8) Ordenar por precio (descendente):")
    for p in catalogo.ordenar(lambda p: p.precio, descendente=True):
        print("   ", p)

    print("\n9) Resumen del catálogo:")
    for clave, valor in catalogo.resumen().items():
        print(f"    {clave}: {valor}")

    print("\n10) Eliminar P007:")
    catalogo.eliminar("P007")
    print(f"    Productos restantes: {len(catalogo)}")

    ruta = guardar(catalogo)
    print(f"\n11) Catálogo guardado en: {ruta}")

    print("\nDemo finalizada. Ejecuta 'semana6_interfaz_grafica.py' para ver la GUI.")


if __name__ == "__main__":
    _demo()
