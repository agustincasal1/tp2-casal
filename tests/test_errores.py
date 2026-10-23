"""Seis errores de entrada o salida comprobados desde la consola."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


class TestErrores(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def ejecutar_comando(self, entrada, salida):
        return subprocess.run(
            [sys.executable, "-m", "src.main", str(entrada),
             "--salida", str(salida)],
            cwd=RAIZ, capture_output=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def comprobar_error_de_entrada(self, nombre, contenido, mensaje):
        entrada = self.carpeta / nombre
        entrada.write_bytes(contenido)
        salida = self.carpeta / "resultados"
        resultado = self.ejecutar_comando(entrada, salida)
        self.assertEqual(resultado.returncode, 1, resultado.stderr)
        self.assertIn(mensaje, resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertFalse(salida.exists())
        self.assertEqual(entrada.read_bytes(), contenido)

    def test_error_01_json_con_sintaxis_incompleta(self):
        self.comprobar_error_de_entrada(
            "incompleto.json", b'[{"viaje_id": "V001"', "JSON inválido",
        )

    def test_error_02_faltan_columnas_necesarias(self):
        self.comprobar_error_de_entrada(
            "columnas.csv", b"viaje_id,origen\nV001,CENTRO\n",
            "se requieren exactamente los campos",
        )

    def test_error_03_fila_csv_con_valores_de_mas(self):
        self.comprobar_error_de_entrada(
            "sobrante.csv", b"viaje_id,origen\nV001,CENTRO,PARQUE\n",
            "más valores que columnas",
        )

    def test_error_04_encabezado_csv_repetido(self):
        self.comprobar_error_de_entrada(
            "repetido.csv", b"viaje_id,viaje_id\nV001,V002\n",
            "columnas repetidas",
        )

    def test_error_05_archivo_con_codificacion_incorrecta(self):
        self.comprobar_error_de_entrada(
            "codificacion.csv", b"viaje_id,origen\nV001,\xff\n", "UTF-8",
        )

    def test_error_06_carpeta_de_salida_ocupada_por_un_archivo(self):
        salida = self.carpeta / "resultados"
        salida.write_bytes(b"contenido que debe conservarse")
        resultado = self.ejecutar_comando(RAIZ / "data/viajes.csv", salida)
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Error:", resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertEqual(salida.read_bytes(), b"contenido que debe conservarse")
        self.assertEqual(list(self.carpeta.iterdir()), [salida])


if __name__ == "__main__":
    unittest.main()
