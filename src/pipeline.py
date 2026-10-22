"""Validación y transformación de los registros de viajes."""

import re
from datetime import datetime

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
