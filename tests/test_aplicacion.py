import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.main import ejecutar

RAIZ = Path(__file__).resolve().parents[1]


class TestAplicacion(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def comando(self, *argumentos):
        return subprocess.run(
            [sys.executable, "-m", "src.main", *map(str, argumentos)],
            cwd=RAIZ, capture_output=True, text=True,
        )

    def test_ejecucion_equivalente_y_repetible(self):
        csv_resultado = ejecutar(RAIZ / "data/viajes.csv", self.carpeta / "csv")
        json_resultado = ejecutar(RAIZ / "data/viajes.json", self.carpeta / "json")
        self.assertEqual(csv_resultado, json_resultado)
        archivos = {p.name: p.read_bytes() for p in (self.carpeta / "csv").iterdir()}
        ejecutar(RAIZ / "data/viajes.csv", self.carpeta / "csv")
        for nombre, contenido in archivos.items():
            self.assertEqual(contenido, (self.carpeta / "csv" / nombre).read_bytes())
            self.assertEqual(contenido, (self.carpeta / "json" / nombre).read_bytes())

    def test_comando_con_fechas_y_archivos_exportados(self):
        resultado = self.comando("data/viajes.csv", "--desde", "2026-09-01",
                                 "--hasta", "2026-09-02", "--salida", self.carpeta)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        resumen = json.loads((self.carpeta / "resumen.json").read_text())
        self.assertEqual(resumen["seleccionados"], 12)
        self.assertEqual(resumen["fuera_del_periodo"], 48)
        with (self.carpeta / "seleccionados.csv").open(encoding="utf-8") as archivo:
            seleccionados = list(csv.DictReader(archivo))
        self.assertEqual(len(seleccionados), 12)

    def test_errores_del_comando(self):
        casos = [
            ("no_existe.csv",), ("data/viajes.txt",),
            ("data/viajes.csv", "--desde", "2026-02-30"),
            ("data/viajes.csv", "--desde", "2026-09-03", "--hasta", "2026-09-01"),
        ]
        for argumentos in casos:
            with self.subTest(argumentos=argumentos):
                resultado = self.comando(*argumentos, "--salida", self.carpeta)
                self.assertNotEqual(resultado.returncode, 0)
                self.assertNotIn("Traceback", resultado.stderr)
        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_sin_rechazos_reemplaza_archivos_anteriores(self):
        ejecutar(RAIZ / "data/viajes.csv", self.carpeta)
        ejecutar(self.carpeta / "seleccionados.csv", self.carpeta / "limpios")
        ejecutar(self.carpeta / "limpios/seleccionados.csv", self.carpeta)
        with (self.carpeta / "rechazos.csv").open(encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            self.assertIn("motivo", lector.fieldnames)
            self.assertEqual(list(lector), [])

    def test_no_sobrescribe_la_entrada(self):
        entrada = self.carpeta / "seleccionados.csv"
        entrada.write_bytes((RAIZ / "data/viajes.csv").read_bytes())
        original = entrada.read_bytes()
        with self.assertRaisesRegex(ValueError, "sobrescribiría"):
            ejecutar(entrada, self.carpeta)
        self.assertEqual(entrada.read_bytes(), original)

    def test_todos_rechazados_guarda_motivos_y_falla(self):
        entrada = self.carpeta / "mal.json"
        entrada.write_text(json.dumps([{
            "viaje_id": "V001", "inicio": "", "fin": "",
            "origen": "CENTRO", "destino": "PARQUE",
        }]), encoding="utf-8")
        resultado = self.comando(entrada, "--salida", self.carpeta)
        self.assertEqual(resultado.returncode, 1)
        with (self.carpeta / "rechazos.csv").open(encoding="utf-8") as archivo:
            self.assertEqual(len(list(csv.DictReader(archivo))), 1)

    def test_periodo_vacio_es_consulta_valida(self):
        resultado = self.comando("data/viajes.csv", "--desde", "2027-01-01",
                                 "--salida", self.carpeta)
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("No hay viajes", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
