import copy
import unittest
from datetime import datetime
from pathlib import Path

from src.fuentes import FuenteCSV, FuenteJSON
from src.pipeline import convertir_fecha, limpiar_viajes, normalizar_registro

RAIZ = Path(__file__).resolve().parents[1]
VIAJE = {
    "viaje_id": "V001", "inicio": "2026-09-01 10:00:00",
    "fin": "2026-09-01 10:20:00", "origen": "CENTRO", "destino": "PARQUE",
}


class TestLimpieza(unittest.TestCase):
    def test_muestra_y_equivalencia_de_formatos(self):
        csv = FuenteCSV().cargar(RAIZ / "data/viajes.csv")
        json = FuenteJSON().cargar(RAIZ / "data/viajes.json")
        resultado = limpiar_viajes(csv)
        self.assertEqual(resultado, limpiar_viajes(json))
        validos, rechazos, correcciones = resultado
        self.assertEqual((len(validos), len(rechazos)), (60, 8))
        self.assertEqual(len(validos) + len(rechazos), len(csv))
        self.assertEqual([r["fila"] for r in rechazos], list(range(61, 69)))
        self.assertTrue(all(r["motivo"] for r in rechazos))
        self.assertEqual([c["fila"] for c in correcciones], [1, 2, 3, 62])

    def test_normaliza_sin_modificar_la_entrada(self):
        registros = [dict(VIAJE, origen=" centro ", viaje_id=" v001 ")]
        original = copy.deepcopy(registros)
        validos, rechazos, correcciones = limpiar_viajes(registros)
        self.assertEqual(registros, original)
        self.assertEqual(validos[0]["origen"], "CENTRO")
        self.assertEqual(validos[0]["viaje_id"], "V001")
        self.assertIsInstance(validos[0]["inicio"], datetime)
        self.assertEqual(len(correcciones), 2)
        self.assertEqual(rechazos, [])

    def test_fechas_y_valores_invalidos(self):
        casos = [
            ("inicio", "2026-02-30 10:00:00"),
            ("inicio", "2026/09/01 10:00:00"),
            ("inicio", "2026-09-01 25:00:00"),
            ("fin", VIAJE["inicio"]),
            ("fin", "2026-08-31 10:00:00"),
            ("fin", None), ("origen", ""), ("destino", "OTRA"),
            ("viaje_id", "V0001"), ("viaje_id", "V１２３"),
            ("viaje_id", 1), ("origen", ["CENTRO"]),
        ]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                validos, rechazos, _ = limpiar_viajes([dict(VIAJE, **{campo: valor})])
                self.assertEqual(validos, [])
                self.assertEqual(len(rechazos), 1)

    def test_calendario_bisiesto(self):
        self.assertEqual(convertir_fecha("2024-02-29 00:00:00").day, 29)
        with self.assertRaises(ValueError):
            convertir_fecha("2026-02-29 00:00:00")

    def test_duplicados_conservan_el_primero_valido(self):
        registros = [dict(VIAJE, origen=""), VIAJE, dict(VIAJE, viaje_id=" v001 ")]
        validos, rechazos, _ = limpiar_viajes(registros)
        self.assertEqual(len(validos), 1)
        self.assertEqual(len(rechazos), 2)
        self.assertIn("duplicado", rechazos[1]["motivo"])

    def test_esquema_incompleto_y_archivo_vacio(self):
        for registros in ([], [{"viaje_id": "V001"}]):
            with self.subTest(registros=registros):
                with self.assertRaises(ValueError):
                    limpiar_viajes(registros)

    def test_normalizar_dos_veces_da_el_mismo_resultado(self):
        original = dict(VIAJE, viaje_id=" v001 ", destino=" parque ")
        primera = normalizar_registro(original)
        self.assertEqual(normalizar_registro(primera), primera)
        self.assertEqual(original["destino"], " parque ")

    def test_registra_varios_problemas_de_una_misma_fila(self):
        original = dict(VIAJE, viaje_id="mal", origen="", fin="")
        validos, rechazos, _ = limpiar_viajes([original])
        self.assertEqual(validos, [])
        self.assertEqual(len(rechazos), 1)
        for campo in ("viaje_id", "origen", "fin"):
            self.assertIn(campo, rechazos[0]["motivo"])
        self.assertEqual(rechazos[0]["viaje_id"], "mal")

    def test_esquema_incompleto_en_la_segunda_fila(self):
        incompleto = dict(VIAJE)
        del incompleto["fin"]
        with self.assertRaisesRegex(ValueError, "Registro 2"):
            limpiar_viajes([VIAJE, incompleto])

    def test_esquema_con_columna_desconocida(self):
        with self.assertRaisesRegex(ValueError, "exactamente los campos"):
            limpiar_viajes([dict(VIAJE, duracion=20)])

    def test_registro_que_no_es_diccionario(self):
        with self.assertRaisesRegex(ValueError, "Registro 1"):
            limpiar_viajes([["V001", "CENTRO", "PARQUE"]])

    def test_fecha_numerica_no_se_interpreta_como_texto(self):
        validos, rechazos, _ = limpiar_viajes([dict(VIAJE, inicio=20260901)])
        self.assertEqual(validos, [])
        self.assertIn("inicio", rechazos[0]["motivo"])

    def test_identificador_con_ceros_iniciales_se_conserva(self):
        validos, rechazos, _ = limpiar_viajes([dict(VIAJE, viaje_id="V007")])
        self.assertEqual(validos[0]["viaje_id"], "V007")
        self.assertEqual(rechazos, [])

    def test_misma_ruta_con_ids_distintos_son_dos_viajes(self):
        validos, rechazos, _ = limpiar_viajes([
            VIAJE, dict(VIAJE, viaje_id="V002"),
        ])
        self.assertEqual([v["viaje_id"] for v in validos], ["V001", "V002"])
        self.assertEqual(rechazos, [])

    def test_conserva_correcciones_de_una_fila_rechazada(self):
        validos, rechazos, cambios = limpiar_viajes([
            dict(VIAJE, origen=" otra "),
        ])
        self.assertEqual(validos, [])
        self.assertEqual(rechazos[0]["origen"], " otra ")
        self.assertEqual(cambios, [{
            "fila": 1, "campo": "origen", "original": " otra ",
            "normalizado": "OTRA",
        }])

    def test_datos_correctos_no_generan_correcciones(self):
        validos, rechazos, cambios = limpiar_viajes([VIAJE])
        self.assertEqual(len(validos), 1)
        self.assertEqual((rechazos, cambios), ([], []))


if __name__ == "__main__":
    unittest.main()
