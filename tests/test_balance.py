import copy
import unittest
from datetime import date

from src.pipeline import (
    generar_balance, limpiar_viajes, seleccionar_periodo, verificar_balance,
)


def viaje(codigo, origen, destino, inicio="2026-09-01 23:50:00"):
    return {
        "viaje_id": codigo, "inicio": inicio,
        "fin": "2026-09-02 00:10:00", "origen": origen, "destino": destino,
    }


class TestBalance(unittest.TestCase):
    def test_un_viaje_suma_una_salida_y_una_llegada(self):
        validos, _, _ = limpiar_viajes([viaje("V001", "CENTRO", "PARQUE")])
        reporte = generar_balance(validos)
        filas = {fila["estacion"]: fila for fila in reporte}
        self.assertEqual(filas["CENTRO"], {
            "estacion": "CENTRO", "salidas": 1, "llegadas": 0, "balance": -1,
        })
        self.assertEqual(filas["PARQUE"]["balance"], 1)
        verificar_balance(reporte, 1)

    def test_regreso_a_la_misma_estacion(self):
        validos, _, _ = limpiar_viajes([viaje("V001", "CENTRO", "CENTRO")])
        centro = generar_balance(validos)[0]
        self.assertEqual((centro["salidas"], centro["llegadas"]), (1, 1))
        self.assertEqual(centro["balance"], 0)

    def test_rechazados_no_suman_y_balance_total_cero(self):
        registros = [viaje("V001", "CENTRO", "PARQUE"),
                     viaje("V002", "PARQUE", "RETIRO"),
                     viaje("V003", "", "CENTRO")]
        validos, rechazados, _ = limpiar_viajes(registros)
        reporte = generar_balance(validos)
        self.assertEqual(len(rechazados), 1)
        self.assertEqual(sum(f["salidas"] for f in reporte), 2)
        self.assertEqual(sum(f["llegadas"] for f in reporte), 2)
        self.assertEqual(sum(f["balance"] for f in reporte), 0)
        verificar_balance(reporte, 2)

    def test_periodo_inclusivo_y_viaje_que_cruza_medianoche(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE"),
            viaje("V002", "PARQUE", "RETIRO", "2026-09-02 00:00:00"),
        ])
        primero = seleccionar_periodo(validos, date(2026, 9, 1), date(2026, 9, 1))
        segundo = seleccionar_periodo(validos, date(2026, 9, 2), date(2026, 9, 2))
        self.assertEqual([v["viaje_id"] for v in primero], ["V001"])
        self.assertEqual([v["viaje_id"] for v in segundo], ["V002"])
        verificar_balance(generar_balance(primero), 1)

    def test_periodo_sin_coincidencias(self):
        validos, _, _ = limpiar_viajes([viaje("V001", "CENTRO", "PARQUE")])
        seleccion = seleccionar_periodo(validos, date(2027, 1, 1))
        self.assertEqual(seleccion, [])
        reporte = generar_balance(seleccion)
        self.assertTrue(all(f["salidas"] == f["llegadas"] == 0 for f in reporte))
        verificar_balance(reporte, 0)

    def test_periodo_invertido_y_resultado_alterado(self):
        with self.assertRaises(ValueError):
            seleccionar_periodo([], date(2026, 9, 2), date(2026, 9, 1))
        reporte = generar_balance([])
        reporte[0]["salidas"] = 1
        with self.assertRaises(ValueError):
            verificar_balance(reporte, 0)

    def test_sin_filtros_conserva_viajes_y_no_modifica_entrada(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE"),
            viaje("V002", "RETIRO", "PLAZA"),
        ])
        original = copy.deepcopy(validos)
        seleccion = seleccionar_periodo(validos)
        self.assertEqual(seleccion, original)
        self.assertEqual(validos, original)
        self.assertIsNot(seleccion, validos)

    def test_solo_desde_incluye_el_inicio_del_dia(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE"),
            viaje("V002", "PARQUE", "PLAZA", "2026-09-02 00:00:00"),
        ])
        seleccion = seleccionar_periodo(validos, desde=date(2026, 9, 2))
        self.assertEqual([v["viaje_id"] for v in seleccion], ["V002"])

    def test_solo_hasta_incluye_el_ultimo_segundo_del_dia(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE", "2026-09-01 23:59:59"),
            viaje("V002", "PARQUE", "PLAZA", "2026-09-02 00:00:00"),
        ])
        seleccion = seleccionar_periodo(validos, hasta=date(2026, 9, 1))
        self.assertEqual([v["viaje_id"] for v in seleccion], ["V001"])

    def test_recorrido_circular_tiene_movimientos_y_balance_cero(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE"),
            viaje("V002", "PARQUE", "RETIRO"),
            viaje("V003", "RETIRO", "CENTRO"),
        ])
        reporte = generar_balance(validos)
        for fila in reporte:
            self.assertEqual(fila["balance"], 0)
        self.assertEqual(sum(f["salidas"] for f in reporte), 3)
        verificar_balance(reporte, 3)

    def test_orden_de_viajes_no_cambia_el_balance(self):
        validos, _, _ = limpiar_viajes([
            viaje("V001", "CENTRO", "PARQUE"),
            viaje("V002", "CENTRO", "RETIRO"),
        ])
        self.assertEqual(generar_balance(validos),
                         generar_balance(list(reversed(validos))))

    def test_reportes_sucesivos_no_acumulan_movimientos_anteriores(self):
        validos, _, _ = limpiar_viajes([viaje("V001", "CENTRO", "PARQUE")])
        anterior = generar_balance(validos)
        nuevo = generar_balance([])
        self.assertEqual(sum(f["salidas"] for f in anterior), 1)
        self.assertEqual(sum(f["salidas"] for f in nuevo), 0)
        self.assertEqual(generar_balance(validos), anterior)

    def test_detecta_una_estacion_faltante_en_el_reporte(self):
        reporte = generar_balance([])
        with self.assertRaisesRegex(ValueError, "estaciones esperadas"):
            verificar_balance(reporte[:-1], 0)

    def test_detecta_conteos_negativos(self):
        reporte = generar_balance([])
        reporte[0].update(salidas=-1, llegadas=-1)
        with self.assertRaisesRegex(ValueError, "cantidades negativas"):
            verificar_balance(reporte, 0)

    def test_detecta_totales_incorrectos_aunque_el_balance_sea_cero(self):
        reporte = generar_balance([])
        reporte[0].update(salidas=1, llegadas=1)
        with self.assertRaisesRegex(ValueError, "cantidad de viajes"):
            verificar_balance(reporte, 0)

    def test_detecta_estacion_duplicada_en_el_reporte(self):
        reporte = generar_balance([])
        reporte[1]["estacion"] = reporte[0]["estacion"]
        with self.assertRaisesRegex(ValueError, "estaciones esperadas"):
            verificar_balance(reporte, 0)


if __name__ == "__main__":
    unittest.main()
