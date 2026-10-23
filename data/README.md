# Datos de los viajes

La muestra se generó para este TP el 23/10/2026. Responsable: Agustín Casal.
La fuente es el script `generar_datos.py`; no se descargó de un sitio externo
ni corresponde a viajes reales de Ecobici. Se permite usarla y modificarla
con fines educativos citando este repositorio.

## Variables y formato

Cada fila representa un viaje. `viajes.csv` y `viajes.json` contienen los mismos
68 registros en el mismo orden: son dos formatos de una sola muestra.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `viaje_id` | Texto | V seguida de tres dígitos ASCII |
| `inicio` | Texto | Inicio local, `AAAA-MM-DD HH:MM:SS` |
| `fin` | Texto | Fin con el mismo formato, posterior al inicio |
| `origen` | Texto | Estación de salida |
| `destino` | Texto | Estación de llegada |

Las estaciones ficticias son CENTRO, PARQUE, RETIRO, FACULTAD y PLAZA.
Se usa hora local de Buenos Aires, sin conversiones de zona horaria.
Ambos archivos tienen codificación UTF-8. El CSV usa coma como separador y
encabezado; el JSON es una lista de objetos con los cinco campos.

## Generación

Los archivos ya están incluidos. Para regenerarlos desde `tp2-casal`:

```bash
python data/generar_datos.py
```

El script usa `random.Random(42)` para crear 60 viajes entre el 1 y el 10 de
septiembre de 2026, seis por día, con duraciones de 8 a 45 minutos. Origen y
destino se eligen de forma independiente; un viaje puede volver a la misma
estación. Con la misma semilla se reproduce la muestra.

Se agregan ocho registros para comprobar los rechazos. La numeración empieza
en 1 y no cuenta el encabezado CSV:

| Fila | Problema |
| --- | --- |
| 61 | Identificador V004 repetido |
| 62 | Identificador con formato incorrecto |
| 63 | Fecha que no existe |
| 64 | Fin anterior al inicio |
| 65 | Origen faltante |
| 66 | Destino desconocido |
| 67 | Fin faltante |
| 68 | Fin igual al inicio |

Las filas 1, 2 y 3 tienen espacios o minúsculas que se corrigen. La fila 62
también pasa a mayúsculas, pero su identificador sigue siendo inválido.
El resultado esperado es 60 viajes válidos, ocho rechazos y cuatro cambios
de campos registrados.

## Limitaciones

No hay datos personales. Los nombres de las estaciones son ficticios y la
frecuencia de seis viajes diarios fue elegida para simplificar la muestra.
No se modelan demanda, distancias, clima, capacidad ni reposiciones; los datos
sirven para comprobar el funcionamiento del programa.
