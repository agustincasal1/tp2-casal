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


if __name__ == "__main__":
    unittest.main()
