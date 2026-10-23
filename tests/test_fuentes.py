"""Verificaciones de lectura, independientes del tema de los datos."""

import csv
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
        ruta.write_text(texto, encoding="utf-8", newline="\n")
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

    def test_csv_con_marca_bom(self):
        ruta = self.escribir("bom.csv", "\ufeffcodigo,valor\nV001,10\n")
        self.assertEqual(FuenteCSV().cargar(ruta),
                         [{"codigo": "V001", "valor": "10"}])

    def test_json_con_marca_bom(self):
        ruta = self.escribir("bom.json", '\ufeff[{"codigo": "V001"}]')
        self.assertEqual(FuenteJSON().cargar(ruta), [{"codigo": "V001"}])

    def test_csv_respeta_comas_entre_comillas(self):
        ruta = self.escribir("comas.csv", 'nombre,valor\n"Plaza, sur",5\n')
        self.assertEqual(FuenteCSV().cargar(ruta),
                         [{"nombre": "Plaza, sur", "valor": "5"}])

    def test_csv_respeta_saltos_dentro_de_un_campo(self):
        ruta = self.escribir("saltos.csv", 'nota,codigo\n"dos\nlineas",A\n')
        registros = FuenteCSV().cargar(ruta)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["nota"], "dos\nlineas")

    def test_csv_no_inventa_el_valor_de_una_celda_ausente(self):
        ruta = self.escribir("corto.csv", "codigo,valor\nV001\n")
        self.assertEqual(FuenteCSV().cargar(ruta),
                         [{"codigo": "V001", "valor": None}])

    def test_csv_solo_encabezado_no_crea_registros(self):
        ruta = self.escribir("vacio.csv", "codigo,valor\n")
        self.assertEqual(FuenteCSV().cargar(ruta), [])

    def test_csv_con_comillas_sin_cerrar_informa_error(self):
        ruta = self.escribir("comillas.csv", 'codigo,valor\n"V001,10\n')
        with self.assertRaises(csv.Error):
            FuenteCSV().cargar(ruta)

    def test_json_conserva_caracteres_en_utf8(self):
        ruta = self.escribir("texto.json", '[{"nombre": "Estación Ñandú"}]')
        self.assertEqual(FuenteJSON().cargar(ruta),
                         [{"nombre": "Estación Ñandú"}])


if __name__ == "__main__":
    unittest.main()
