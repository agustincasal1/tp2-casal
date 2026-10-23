import csv
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data.generar_datos import generar_viajes
from src.fuentes import FuenteCSV, FuenteJSON
from src.main import ejecutar
from src.pipeline import guardar_csv

RAIZ = Path(__file__).resolve().parents[1]


class TestAplicacion(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def comando(self, *argumentos):
        return subprocess.run(
            [sys.executable, "-m", "src.main", *map(str, argumentos)],
            cwd=RAIZ, capture_output=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
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

    def test_reporte_completo_coincide_con_los_totales_conocidos(self):
        reporte, resumen = ejecutar(RAIZ / "data/viajes.csv", self.carpeta)
        observado = [
            (f["estacion"], f["salidas"], f["llegadas"], f["balance"])
            for f in reporte
        ]
        self.assertEqual(observado, [
            ("CENTRO", 15, 13, -2), ("FACULTAD", 5, 11, 6),
            ("PARQUE", 18, 11, -7), ("PLAZA", 13, 15, 2),
            ("RETIRO", 9, 10, 1),
        ])
        self.assertEqual(resumen["seleccionados"], 60)
        self.assertEqual(resumen["fuera_del_periodo"], 0)
        self.assertIsNone(resumen["desde"])
        self.assertIsNone(resumen["hasta"])

    def test_acepta_extension_en_mayusculas(self):
        entrada = self.carpeta / "VIAJES.JSON"
        entrada.write_bytes((RAIZ / "data/viajes.json").read_bytes())
        resultado = ejecutar(entrada, self.carpeta / "mayusculas")
        esperado = ejecutar(RAIZ / "data/viajes.csv", self.carpeta / "csv")
        self.assertEqual(resultado, esperado)

    def test_crea_carpetas_de_salida_anidadas(self):
        destino = self.carpeta / "consultas/septiembre/completo"
        ejecutar(RAIZ / "data/viajes.csv", destino)
        self.assertEqual({p.name for p in destino.iterdir()}, {
            "reporte.csv", "seleccionados.csv", "rechazos.csv",
            "correcciones.csv", "resumen.json",
        })

    def test_exportar_csv_conserva_comillas_comas_y_acentos(self):
        filas = [{"motivo": 'Estación "otra", no reconocida', "fila": "1"}]
        ruta = self.carpeta / "texto.csv"
        guardar_csv(filas, ruta, ("motivo", "fila"))
        self.assertEqual(FuenteCSV().cargar(ruta), filas)

    def test_exporta_el_detalle_de_las_correcciones(self):
        ejecutar(RAIZ / "data/viajes.csv", self.carpeta)
        cambios = FuenteCSV().cargar(self.carpeta / "correcciones.csv")
        self.assertEqual([c["fila"] for c in cambios], ["1", "2", "3", "62"])
        self.assertEqual(cambios[0], {
            "fila": "1", "campo": "viaje_id", "original": " v001 ",
            "normalizado": "V001",
        })
        self.assertEqual(cambios[-1]["normalizado"], "VIAJE-61")

    def test_exporta_valores_originales_y_motivos_de_rechazo(self):
        ejecutar(RAIZ / "data/viajes.csv", self.carpeta)
        rechazos = FuenteCSV().cargar(self.carpeta / "rechazos.csv")
        por_fila = {r["fila"]: r for r in rechazos}
        self.assertEqual(len(por_fila), 8)
        self.assertEqual(por_fila["62"]["viaje_id"], "viaje-61")
        self.assertIn("duplicado", por_fila["61"]["motivo"])
        self.assertIn("inicio", por_fila["63"]["motivo"])

    def test_null_json_y_celda_vacia_csv_se_rechazan_igual(self):
        registros = [
            {"viaje_id": "V001", "inicio": "2026-09-01 10:00:00",
             "fin": "2026-09-01 10:20:00", "origen": "CENTRO",
             "destino": "PARQUE"},
        ]
        registros.append(dict(registros[0], viaje_id="V002", fin=None))
        entrada_csv = self.carpeta / "entrada.csv"
        entrada_json = self.carpeta / "entrada.json"
        guardar_csv(registros, entrada_csv, list(registros[0]))
        entrada_json.write_text(json.dumps(registros), encoding="utf-8")
        resultado_csv = ejecutar(entrada_csv, self.carpeta / "csv")
        resultado_json = ejecutar(entrada_json, self.carpeta / "json")
        self.assertEqual(resultado_csv, resultado_json)
        self.assertEqual(resultado_csv[1]["rechazados"], 1)
        self.assertEqual(
            (self.carpeta / "csv/rechazos.csv").read_bytes(),
            (self.carpeta / "json/rechazos.csv").read_bytes(),
        )

    def test_generador_reproduce_muestra_sin_cambiar_azar_global(self):
        estado = random.getstate()
        generados = generar_viajes()
        self.assertEqual(random.getstate(), estado)
        self.assertEqual(generados, generar_viajes())
        self.assertEqual(generados, FuenteCSV().cargar(RAIZ / "data/viajes.csv"))
        self.assertEqual(generados, FuenteJSON().cargar(RAIZ / "data/viajes.json"))


if __name__ == "__main__":
    unittest.main()
