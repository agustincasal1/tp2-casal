"""Lectura de archivos tabulares mediante una interfaz común."""

import csv
import json
from abc import ABC, abstractmethod


class FuenteDatos(ABC):
    @abstractmethod
    def cargar(self, ruta):
        """Devuelve una lista de diccionarios, uno por registro."""
        raise NotImplementedError


class FuenteCSV(FuenteDatos):
    def cargar(self, ruta):
        with open(ruta, encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo, strict=True)
            columnas = lector.fieldnames
            if not columnas or any(not nombre for nombre in columnas):
                raise ValueError("El CSV necesita un encabezado con nombres.")
            if len(set(columnas)) != len(columnas):
                raise ValueError("El CSV tiene columnas repetidas.")
            registros = list(lector)
        if any(None in registro for registro in registros):
            raise ValueError("Hay filas CSV con más valores que columnas.")
        return registros


class FuenteJSON(FuenteDatos):
    def cargar(self, ruta):
        with open(ruta, encoding="utf-8-sig") as archivo:
            try:
                registros = json.load(archivo)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido: revisar línea {error.lineno}, "
                    f"columna {error.colno}."
                ) from error
        if not isinstance(registros, list) or not all(
            isinstance(registro, dict) for registro in registros
        ):
            raise ValueError("El JSON debe contener una lista de objetos.")
        return registros
