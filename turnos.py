"""Sistema de turnos con Cola (FIFO) manual y patrón Repository.

Ejecutar:  python turnos.py
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ---------- Cola implementada a mano (nodos enlazados) ----------
class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None


class Cola:
    def __init__(self):
        self._frente = None
        self._final = None
        self._tamano = 0

    def agregar(self, dato):
        nuevo = Nodo(dato)
        if self._final is None:
            self._frente = nuevo
        else:
            self._final.siguiente = nuevo
        self._final = nuevo
        self._tamano += 1

    def eliminar(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        dato = self._frente.dato
        self._frente = self._frente.siguiente
        if self._frente is None:
            self._final = None
        self._tamano -= 1
        return dato

    def consultar_siguiente(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._frente.dato

    def esta_vacia(self):
        return self._tamano == 0

    def cantidad(self):
        return self._tamano


# ---------- Entidad ----------
@dataclass(frozen=True)
class Turno:
    numero: int
    cliente: str


# ---------- Patrón Repository ----------
class RepositorioTurnos(ABC):
    @abstractmethod
    def agregar(self, turno): ...

    @abstractmethod
    def eliminar(self): ...

    @abstractmethod
    def siguiente(self): ...

    @abstractmethod
    def esta_vacio(self): ...

    @abstractmethod
    def cantidad(self): ...


class RepositorioTurnosCola(RepositorioTurnos):
    def __init__(self):
        self._cola = Cola()

    def agregar(self, turno):
        self._cola.agregar(turno)

    def eliminar(self):
        return self._cola.eliminar()

    def siguiente(self):
        return self._cola.consultar_siguiente()

    def esta_vacio(self):
        return self._cola.esta_vacia()

    def cantidad(self):
        return self._cola.cantidad()


# ---------- Lógica de negocio ----------
class ServicioTurnos:
    def __init__(self, repositorio):
        self._repo = repositorio
        self._contador = 0

    def solicitar_turno(self, cliente):
        if not cliente or not cliente.strip():
            raise ValueError("El nombre del cliente es obligatorio")
        self._contador += 1
        turno = Turno(self._contador, cliente.strip())
        self._repo.agregar(turno)
        return turno

    def atender_siguiente(self):
        return self._repo.eliminar()

    def ver_siguiente(self):
        return self._repo.siguiente()

    def turnos_pendientes(self):
        return self._repo.cantidad()


# ---------- Aplicación de consola ----------
MENU = """
--- Cola de turnos ---
1. Solicitar turno
2. Atender siguiente
3. Ver siguiente
4. Turnos pendientes
5. Salir
"""


def main():
    servicio = ServicioTurnos(RepositorioTurnosCola())
    while True:
        print(MENU)
        opcion = input("Opción: ").strip()
        try:
            if opcion == "1":
                t = servicio.solicitar_turno(input("Nombre del cliente: "))
                print(f"Turno #{t.numero} asignado a {t.cliente}")
            elif opcion == "2":
                t = servicio.atender_siguiente()
                print(f"Atendiendo turno #{t.numero}: {t.cliente}")
            elif opcion == "3":
                t = servicio.ver_siguiente()
                print(f"Siguiente: turno #{t.numero} ({t.cliente})")
            elif opcion == "4":
                print(f"Pendientes: {servicio.turnos_pendientes()}")
            elif opcion == "5":
                print("Hasta luego")
                break
            else:
                print("Opción no válida")
        except (IndexError, ValueError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
