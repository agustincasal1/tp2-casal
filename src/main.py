"""Uso: python -m src.main data/viajes.csv --desde 2026-09-01."""

import argparse
import csv
import json
import sys
from pathlib import Path

from .fuentes import FuenteCSV, FuenteJSON
from .pipeline import (
    CAMPOS, convertir_fecha, generar_balance, guardar_csv,
    limpiar_viajes, seleccionar_periodo, verificar_balance,
)


def fecha_argumento(texto):
    try:
        return convertir_fecha(texto + " 00:00:00").date()
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "La fecha debe existir y usar el formato AAAA-MM-DD."
        ) from error


def ejecutar(ruta, carpeta_salida, desde=None, hasta=None):
    ruta = Path(ruta)
    fuentes = {".csv": FuenteCSV(), ".json": FuenteJSON()}
    if ruta.suffix.lower() not in fuentes:
        raise ValueError("La entrada debe ser un archivo .csv o .json.")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("La fecha desde no puede ser posterior a hasta.")
    registros = fuentes[ruta.suffix.lower()].cargar(ruta)
    validos, rechazos, correcciones = limpiar_viajes(registros)
    seleccionados = seleccionar_periodo(validos, desde, hasta)
    reporte = generar_balance(seleccionados)
    verificar_balance(reporte, len(seleccionados))
    auditoria = {
        "leidos": len(registros), "validos": len(validos),
        "rechazados": len(rechazos), "campos_normalizados": len(correcciones),
        "seleccionados": len(seleccionados),
        "fuera_del_periodo": len(validos) - len(seleccionados),
        "desde": desde.isoformat() if desde else None,
        "hasta": hasta.isoformat() if hasta else None,
    }
    if auditoria["leidos"] != auditoria["validos"] + auditoria["rechazados"]:
        raise ValueError("La limpieza perdió registros sin contabilizar.")

    carpeta = Path(carpeta_salida)
    nombres_salida = ("reporte.csv", "rechazos.csv", "correcciones.csv",
                      "seleccionados.csv", "resumen.json")
    rutas_salida = [(carpeta / nombre).resolve() for nombre in nombres_salida]
    if ruta.resolve() in rutas_salida:
        raise ValueError("La salida sobrescribiría el archivo de entrada.")
    carpeta.mkdir(parents=True, exist_ok=True)
    guardar_csv(reporte, carpeta / "reporte.csv",
                ("estacion", "salidas", "llegadas", "balance"))
    guardar_csv(rechazos, carpeta / "rechazos.csv",
                ("fila", *CAMPOS, "motivo"))
    guardar_csv(correcciones, carpeta / "correcciones.csv",
                ("fila", "campo", "original", "normalizado"))
    guardar_csv(seleccionados, carpeta / "seleccionados.csv", CAMPOS)
    with (carpeta / "resumen.json").open("w", encoding="utf-8") as archivo:
        json.dump(auditoria, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    return reporte, auditoria


def main():
    parser = argparse.ArgumentParser(
        description="Reporte de movimientos de bicicletas."
    )
    parser.add_argument("archivo", help="Archivo de viajes CSV o JSON")
    parser.add_argument("--desde", type=fecha_argumento,
                        help="Primer día, AAAA-MM-DD")
    parser.add_argument("--hasta", type=fecha_argumento,
                        help="Último día, AAAA-MM-DD")
    parser.add_argument("--salida", default="outputs",
                        help="Carpeta de resultados")
    args = parser.parse_args()
    try:
        reporte, resumen = ejecutar(
            args.archivo, args.salida, args.desde, args.hasta
        )
    except UnicodeDecodeError:
        print("Error: el archivo debe estar guardado con codificación UTF-8.",
              file=sys.stderr)
        return 1
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Leídos: {resumen['leidos']} | Válidos: {resumen['validos']} | "
          f"Rechazados: {resumen['rechazados']}")
    print(f"Viajes del período: {resumen['seleccionados']}")
    print(f"{'Estación':12} {'Salidas':>8} {'Llegadas':>8} {'Balance':>8}")
    for fila in reporte:
        print(f"{fila['estacion']:12} {fila['salidas']:8} "
              f"{fila['llegadas']:8} {fila['balance']:8}")
    print(f"Archivos guardados en: {args.salida}")
    if resumen["validos"] == 0:
        print("No quedaron viajes válidos. Revisá rechazos.csv.",
              file=sys.stderr)
        return 1
    if resumen["seleccionados"] == 0:
        print("No hay viajes en el período elegido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
