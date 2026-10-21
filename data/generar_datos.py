"""Genera la muestra de práctica en ambos formatos, siempre con semilla 42."""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generar_viajes():
    azar = random.Random(42)
    estaciones = ["CENTRO", "PARQUE", "RETIRO", "FACULTAD", "PLAZA"]
    viajes = []
    for numero in range(60):
        inicio = datetime(2026, 9, 1, 7) + timedelta(
            days=numero // 6, hours=(numero % 6) * 2,
            minutes=azar.randint(0, 59),
        )
        fin = inicio + timedelta(minutes=azar.randint(8, 45))
        viajes.append({
            "viaje_id": f"V{numero + 1:03d}",
            "inicio": inicio.strftime("%Y-%m-%d %H:%M:%S"),
            "fin": fin.strftime("%Y-%m-%d %H:%M:%S"),
            "origen": azar.choice(estaciones),
            "destino": azar.choice(estaciones),
        })

    # Tres filas recuperables con espacios o diferencias de mayúsculas.
    viajes[0]["viaje_id"] = " v001 "
    viajes[1]["origen"] = " " + viajes[1]["origen"].lower() + " "
    viajes[2]["inicio"] = " " + viajes[2]["inicio"] + " "

    base = viajes[3]
    viajes.extend([
        dict(base),
        dict(base, viaje_id="viaje-61"),
        dict(base, viaje_id="V062", inicio="2026-02-30 10:00:00"),
        dict(base, viaje_id="V063", fin="2026-08-31 08:00:00"),
        dict(base, viaje_id="V064", origen=""),
        dict(base, viaje_id="V065", destino="ESTACION_INEXISTENTE"),
        dict(base, viaje_id="V066", fin=""),
        dict(base, viaje_id="V067", fin=base["inicio"]),
    ])
    return viajes


def main():
    carpeta = Path(__file__).resolve().parent
    viajes = generar_viajes()
    with (carpeta / "viajes.csv").open(
        "w", encoding="utf-8", newline=""
    ) as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=list(viajes[0]), lineterminator="\n"
        )
        escritor.writeheader()
        escritor.writerows(viajes)
    with (carpeta / "viajes.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as archivo:
        json.dump(viajes, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    print(f"Generados {len(viajes)} registros en CSV y JSON.")


if __name__ == "__main__":
    main()
