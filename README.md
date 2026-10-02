# EVALUACION-
# Sistema de Inventario - Proyecto Integrador
**Autor:** Moris Espinoza Espinoza 
**Materia:** Programación / Desarrollo de Software
**Semanas:** 5, 6 y 7

## 📋 Descripción del Proyecto
Este proyecto es una aplicación de escritorio desarrollada en **Python** que integra los conocimientos adquiridos durante las semanas 5, 6 y 7. Consiste en un sistema de gestión de inventario con interfaz gráfica, persistencia de datos, manejo de eventos, implementación de una estructura de datos abstracta (Pila) y el patrón de diseño Repository, validado mediante pruebas unitarias.

## 🎯 Objetivos Cumplidos
*   **Semana 5 y 6:** Uso de colecciones (listas, diccionarios), genéricos (type hints), creación de una Interfaz Gráfica de Usuario (GUI) con `Tkinter` y manejo de eventos (botones, selección de tabla).
*   **Semana 7:** Implementación de una Pila (Stack) como ADT lineal, aplicación del patrón de diseño **Repository**, persistencia de datos en archivos JSON y pruebas unitarias con `unittest`.

## 🛠️ Tecnologías Utilizadas
*   **Lenguaje:** Python 3.10+
*   **Interfaz Gráfica:** Tkinter (Librería estándar)
*   **Pruebas Unitarias:** Unittest (Librería estándar)
*   **Persistencia:** JSON

## 📁 Estructura del Código
*   `models.py`: Define la entidad `Producto` y su conversión a diccionario (Genéricos/POO).
*   `adt.py`: Implementación de la clase `Pila` (Stack) para el manejo del historial de acciones.
*   `repository.py`: Patrón Repository. Encapsula la lógica de acceso a datos (CRUD) y la persistencia en JSON.
*   `main.py`: Punto de entrada. Interfaz gráfica, manejo de eventos y conexión entre la GUI, el Repository y el ADT.
*   `test_inventario.py`: Pruebas unitarias para validar la Pila y el Repository.
*   # Semana 5 — Colecciones y Genéricos

Catálogo de productos: modelo de datos, colección genérica en memoria y
persistencia en JSON. Es la base sobre la que se construye la interfaz
gráfica de la Semana 6.

## Requisitos

- Python 3.10 o superior.
- No requiere librerías externas.

## Ejecución

```bash
python semana5_coleccion_generica.py
```

Al ejecutarlo directamente se muestra por consola una **demostración** de
todas las operaciones sobre el catálogo: alta, error por código duplicado,
actualización, búsqueda, filtro por bajo stock, categorías registradas,
ordenamiento, resumen estadístico, eliminación y guardado en
`catalogo.json`.

## Contenido del archivo

| Sección | Contenido |
|---|---|
| 1. Excepciones | `ValidacionError`, `ElementoDuplicadoError`, `ElementoNoEncontradoError` |
| 2. Modelo | Clase `Producto` (dataclass con validaciones) |
| 3. Colección genérica | `RepositorioGenerico[T]` y `CatalogoProductos` |
| 4. Persistencia | Funciones `guardar()` y `cargar()` en JSON |
| 5. Demo | Función `_demo()`, se ejecuta solo si corres este archivo directamente |

## La clase Producto

`Producto` es un `dataclass` que valida sus propios datos en el
constructor: código y nombre obligatorios, categoría dentro de una lista
cerrada, precio y stock no negativos. Si algo falla, lanza
`ValidacionError` en vez de dejar pasar datos inconsistentes.

```python
@dataclass
class Producto:
    id: str
    nombre: str
    categoria: str = "Otros"
    precio: float = 0.0
    stock: int = 0
    valor_inventario: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.validar()
        ...
```

## La colección genérica

`RepositorioGenerico[T]` es el corazón de esta entrega. El parámetro de
tipo `T` se declara con `TypeVar` y se acota (`bound`) al protocolo
`Identificable`, es decir, a **cualquier clase que tenga un atributo `id`**.
Gracias a esto, el mismo repositorio funciona con `Producto`, con un
hipotético `Cliente`, o con cualquier otra entidad, sin duplicar código.

```python
@runtime_checkable
class Identificable(Protocol):
    id: str

T = TypeVar("T", bound=Identificable)

class RepositorioGenerico(Generic[T]):
    def __init__(self, elementos: list[T] | None = None) -> None:
        self._elementos: dict[str, T] = {}
        ...
```

| Operación | Método | Estructura usada |
|---|---|---|
| Crear | `agregar(elemento)` | `dict` (clave = id) |
| Leer | `obtener(id)`, `listar()`, `buscar(criterio)` | `dict`, `list` |
| Actualizar | `actualizar(id, elemento)` | `dict` |
| Eliminar | `eliminar(id)` | `dict` |
| Ordenar / agrupar | `ordenar(clave)`, `agrupar_por(clave)` | `list`, `dict` |

`CatalogoProductos` hereda de `RepositorioGenerico[Producto]` y agrega la
lógica propia del negocio: búsqueda por texto, filtro por categoría y por
rango de precio, productos con bajo stock, conjunto (`set`) de categorías
registradas y el valor total del inventario.

### Por qué estas estructuras

- **`dict`** como almacén interno: acceso, inserción y eliminación por
  código en tiempo constante O(1), frente a O(n) de una lista.
- **`list`** para los resultados de búsquedas y ordenamientos: conserva el
  orden de presentación.
- **`set`** para las categorías registradas: elimina duplicados por
  definición, sin lógica adicional.

## Persistencia

`guardar()` y `cargar()` leen y escriben el catálogo como una lista de
diccionarios en `catalogo.json`, en la misma carpeta del script. Si el
archivo no existe o está dañado, `cargar()` genera automáticamente seis
productos de ejemplo para que el programa siempre pueda iniciarse.

## Relación con la Semana 6

Este archivo no importa nada de la Semana 6: es completamente
independiente y se puede probar solo, por consola. El archivo
`semana6_interfaz_grafica.py` es el que depende de este (`from
semana5_coleccion_generica import ...`), no al revés.

## Autor

Moris Patricio Espinoza  — *Programación Orientada a Objetos*, Semana 5.
# Semana 6 — Interfaz Gráfica y Manejo de Eventos

Interfaz gráfica de escritorio (Tkinter/ttk) para el catálogo de productos
desarrollado en la Semana 5. Implementa las cuatro operaciones CRUD
(**C**rear, **C**onsultar, **A**ctualizar, **E**liminar) sobre esa misma
colección, además de búsqueda, filtros y ordenamiento.

## Requisitos

- Python 3.10 o superior.
- Tkinter (viene incluido con Python en Windows y macOS).
  En Linux: `sudo apt install python3-tk`.
- El archivo **`semana5_coleccion_generica.py` debe estar en la misma
  carpeta**, ya que este módulo lo importa.

## Ejecución

```bash
python semana6_interfaz_grafica.py
```

Al iniciar, la ventana carga el catálogo desde `catalogo.json` (o crea
datos de ejemplo si no existe) usando las funciones de la Semana 5.

## Estructura de la ventana

- **Formulario**: código, nombre, categoría, precio y stock.
- **Botonera**: Agregar, Actualizar, Eliminar, Limpiar, Guardar en archivo.
- **Búsqueda y filtro**: campo de texto con filtrado en vivo y combo de
  categoría.
- **Tabla (Treeview)**: lista los productos, resalta en rojo los que
  tienen menos de 5 unidades, y permite ordenar al hacer clic en cualquier
  encabezado.
- **Barra de estado**: total de productos mostrados, categorías, unidades
  y valor del inventario.

## Operaciones CRUD desde la interfaz

| Acción del usuario | Método de la ventana | Método de la colección (Semana 5) |
|---|---|---|
| Botón Agregar | `agregar_producto()` | `catalogo.agregar(producto)` |
| Selección en la tabla | `al_seleccionar_fila()` | `catalogo.obtener(id)` |
| Botón Actualizar | `actualizar_producto()` | `catalogo.actualizar(id, producto)` |
| Botón Eliminar | `eliminar_producto()` | `catalogo.eliminar(id)` |
| Buscador / filtro | `refrescar_tabla()` | `buscar_por_texto()`, `filtrar_por_categoria()` |
| Clic en encabezado | `ordenar_por(columna)` | `ordenar(clave)` |
| Botón Bajo stock | `mostrar_bajo_stock()` | `productos_bajo_stock(5)` |
| Botón Guardar | `guardar_archivo()` | `guardar(catalogo)` |

La ventana nunca manipula listas por su cuenta: cada acción del usuario se
traduce en una llamada a la colección de la Semana 5. Los errores de
validación (`ValidacionError`, `ElementoDuplicadoError`,
`ElementoNoEncontradoError`) se capturan y se muestran en cuadros de
diálogo, no interrumpen el programa.

## Eventos implementados

| Evento | Vinculación | Respuesta de la aplicación |
|---|---|---|
| Clic en botón | `command=` | Ejecuta la operación CRUD correspondiente |
| Selección de fila | `<<TreeviewSelect>>` | Carga el producto en el formulario |
| Doble clic en fila | `<Double-1>` | Muestra el detalle completo del producto |
| Tecla liberada en el buscador | `<KeyRelease>` | Filtra la tabla en vivo |
| Enter | `<Return>` | Agrega o actualiza según haya selección |
| Escape / Suprimir | `<Escape>`, `<Delete>` | Limpia el formulario / elimina el producto |
| Ctrl + S | `<Control-s>` | Guarda el catálogo en el archivo |
| Selección de categoría | `<<ComboboxSelected>>` | Aplica el filtro por categoría |
| Clic en encabezado | `heading(command=)` | Ordena ascendente o descendente |
| Cierre de la ventana | `WM_DELETE_WINDOW` | Pide confirmación y guarda los cambios |

```python
def _registrar_eventos(self) -> None:
    self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)
    self.tabla.bind("<Double-1>", self.al_doble_clic)
    self.tabla.bind("<Delete>", lambda e: self.eliminar_producto())
    self.entrada_busqueda.bind("<KeyRelease>", self.al_escribir_busqueda)
    self.combo_filtro.bind("<<ComboboxSelected>>", lambda e: self.refrescar_tabla())
    self.bind("<Return>", self.al_presionar_enter)
    self.bind("<Escape>", lambda e: self.limpiar_formulario())
    self.bind("<Control-s>", lambda e: self.guardar_archivo())
    self.protocol("WM_DELETE_WINDOW", self.al_cerrar)
```

## Relación con la Semana 5

Este archivo importa todo lo que necesita desde `semana5_coleccion_generica.py`:

```python
from semana5_coleccion_generica import (
    CATEGORIAS, CatalogoError, CatalogoProductos,
    ElementoDuplicadoError, ElementoNoEncontradoError,
    Producto, ValidacionError, cargar, guardar,
)

