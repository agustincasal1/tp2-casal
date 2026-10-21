"""Verificaciones de lectura, independientes del tema de los datos."""

import tempfile
import unittest
from pathlib import Path

from src.fuentes import FuenteCSV, FuenteDatos, FuenteJSON


class TestFuentes(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def escribir(self, nombre, texto):
        ruta = self.carpeta / nombre
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    def test_lecturas_equivalentes(self):
        csv = self.escribir("muestra.csv", "codigo,valor\nA,10\n")
        json = self.escribir(
            "muestra.json", '[{"codigo": "A", "valor": "10"}]'
        )
        self.assertEqual(FuenteCSV().cargar(csv), FuenteJSON().cargar(json))

    def test_no_se_puede_crear_la_fuente_abstracta(self):
        with self.assertRaises(TypeError):
            FuenteDatos()

    def test_archivo_ausente(self):
        for fuente in (FuenteCSV(), FuenteJSON()):
            with self.subTest(fuente=type(fuente).__name__):
                with self.assertRaises(FileNotFoundError):
                    fuente.cargar(self.carpeta / "ausente")

    def test_json_invalido(self):
        for texto in ('{"datos": []}', '[1, 2]', '[{"codigo":'):
            with self.subTest(texto=texto):
                ruta = self.escribir("mal.json", texto)
                with self.assertRaises(ValueError):
                    FuenteJSON().cargar(ruta)

    def test_csv_con_encabezado_o_filas_incorrectas(self):
        for texto in ("", "codigo,codigo\nA,B\n", "codigo\nA,B\n"):
            with self.subTest(texto=texto):
                ruta = self.escribir("mal.csv", texto)
                with self.assertRaises(ValueError):
                    FuenteCSV().cargar(ruta)


if __name__ == "__main__":
    unittest.main()
