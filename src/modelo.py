"""Modelo del dominio: movimientos acumulados en una estación."""


class BalanceEstacion:
    def __init__(self, nombre):
        self.nombre = nombre
        self.salidas = 0
        self.llegadas = 0

    def registrar_salida(self):
        self.salidas += 1

    def registrar_llegada(self):
        self.llegadas += 1

    def balance(self):
        return self.llegadas - self.salidas

    def como_diccionario(self):
        return {
            "estacion": self.nombre,
            "salidas": self.salidas,
            "llegadas": self.llegadas,
            "balance": self.balance(),
        }
