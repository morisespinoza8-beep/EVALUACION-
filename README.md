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

## 🚀 Instalación y Ejecución
1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/sistema-inventario.git
