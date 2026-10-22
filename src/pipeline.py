"""Validación y transformación de los registros de viajes."""

import csv
import re
from datetime import datetime

from .modelo import BalanceEstacion

CAMPOS = ("viaje_id", "inicio", "fin", "origen", "destino")
ESTACIONES = ("CENTRO", "FACULTAD", "PARQUE", "PLAZA", "RETIRO")
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
PATRON_FECHA = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}"
)
PATRON_ID = re.compile(r"V[0-9]{3}")


def convertir_fecha(texto):
    """Comprueba formato y calendario antes de devolver un datetime."""
    if not isinstance(texto, str) or not PATRON_FECHA.fullmatch(texto):
        raise ValueError("Se espera una fecha con formato AAAA-MM-DD HH:MM:SS.")
    try:
        return datetime.strptime(texto, FORMATO_FECHA)
    except ValueError as error:
        raise ValueError("La fecha u hora no existe en el calendario.") from error


def validar_esquema(registros):
    if not registros:
        raise ValueError("El archivo no contiene viajes.")
    for fila, registro in enumerate(registros, start=1):
        if not isinstance(registro, dict) or set(registro) != set(CAMPOS):
            raise ValueError(
                f"Registro {fila}: se requieren exactamente los campos "
                + ", ".join(CAMPOS) + "."
            )


def normalizar_registro(registro):
    """Crea una copia con espacios exteriores quitados y códigos en mayúsculas."""
    limpio = {}
    for campo, valor in registro.items():
        if isinstance(valor, str):
            valor = valor.strip()
            if campo in ("viaje_id", "origen", "destino"):
                valor = valor.upper()
        limpio[campo] = valor
    return limpio


def validar_recorrido(registro):
    """Devuelve todos los motivos por los que no se puede usar el viaje."""
    motivos = []
    codigo = registro["viaje_id"]
    if not isinstance(codigo, str) or not PATRON_ID.fullmatch(codigo):
        motivos.append("viaje_id debe ser V seguido de tres dígitos")
    for campo in ("origen", "destino"):
        if registro[campo] not in ESTACIONES:
            motivos.append(f"{campo} faltante o estación desconocida")

    fechas = {}
    for campo in ("inicio", "fin"):
        try:
            fechas[campo] = convertir_fecha(registro[campo])
        except ValueError as error:
            motivos.append(f"{campo}: {error}")
    if len(fechas) == 2 and fechas["fin"] <= fechas["inicio"]:
        motivos.append("el fin debe ser posterior al inicio")
    return motivos


def limpiar_viajes(registros):
    """Devuelve válidos, rechazos y correcciones sin modificar la entrada."""
    validar_esquema(registros)
    validos, rechazos, correcciones = [], [], []
    aceptados = set()
    for fila, original in enumerate(registros, start=1):
        registro = normalizar_registro(original)
        for campo in CAMPOS:
            if original[campo] != registro[campo]:
                correcciones.append({
                    "fila": fila, "campo": campo,
                    "original": original[campo], "normalizado": registro[campo],
                })
        motivos = validar_recorrido(registro)
        if not motivos and registro["viaje_id"] in aceptados:
            motivos.append("viaje_id duplicado: se conserva el primero válido")
        if motivos:
            rechazos.append({"fila": fila, **original,
                             "motivo": "; ".join(motivos)})
            continue
        aceptados.add(registro["viaje_id"])
        registro["inicio"] = convertir_fecha(registro["inicio"])
        registro["fin"] = convertir_fecha(registro["fin"])
        validos.append(registro)
    return validos, rechazos, correcciones


def seleccionar_periodo(viajes, desde=None, hasta=None):
    """Selecciona por fecha de inicio, incluyendo ambos días del intervalo."""
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("La fecha desde no puede ser posterior a hasta.")
    return [
        viaje for viaje in viajes
        if (desde is None or viaje["inicio"].date() >= desde)
        and (hasta is None or viaje["inicio"].date() <= hasta)
    ]


def generar_balance(viajes):
    """Cuenta ambos extremos de cada viaje, incluso si vuelve al mismo lugar."""
    estaciones = {nombre: BalanceEstacion(nombre) for nombre in ESTACIONES}
    for viaje in viajes:
        estaciones[viaje["origen"]].registrar_salida()
        estaciones[viaje["destino"]].registrar_llegada()
    return [estacion.como_diccionario() for estacion in estaciones.values()]


def verificar_balance(reporte, cantidad_viajes):
    """Controla conservación de movimientos y coherencia de cada estación."""
    if [fila["estacion"] for fila in reporte] != list(ESTACIONES):
        raise ValueError("El reporte no contiene las estaciones esperadas.")
    for fila in reporte:
        if fila["salidas"] < 0 or fila["llegadas"] < 0:
            raise ValueError("El reporte tiene cantidades negativas.")
        if fila["balance"] != fila["llegadas"] - fila["salidas"]:
            raise ValueError("El balance de una estación es incorrecto.")
    salidas = sum(fila["salidas"] for fila in reporte)
    llegadas = sum(fila["llegadas"] for fila in reporte)
    if salidas != cantidad_viajes or llegadas != cantidad_viajes:
        raise ValueError("El reporte no conserva la cantidad de viajes.")
    if sum(fila["balance"] for fila in reporte) != 0:
        raise ValueError("La suma de los balances debe ser cero.")


def guardar_csv(filas, ruta, campos):
    """Escribe el encabezado incluso cuando no hay filas."""
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)
