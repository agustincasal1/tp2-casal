# Datos de práctica

La muestra es **simulada**, no proviene de Ecobici ni describe su operación real.
Se preparó para este TP el 23/10/2026. Responsable: Agustín Casal.
No hay una URL de descarga ni una fecha de consulta externa: el procedimiento
de obtención está en `generar_datos.py`.

Condiciones de uso: se permite usar y modificar esta muestra con fines
educativos, citando este repositorio. No contiene personas ni ubicaciones reales
de estaciones. Los nombres de estaciones son etiquetas ficticias.

## Unidad de análisis y variables

Cada fila representa un viaje de una estación a otra. CSV y JSON contienen los
mismos 68 registros, en el mismo orden; son alternativas de entrada y no deben
sumarse como si fueran dos muestras diferentes.

| Campo | Tipo de entrada | Significado |
| --- | --- | --- |
| `viaje_id` | texto | Identificador `V` seguido de tres dígitos ASCII |
| `inicio` | texto | Inicio local, `AAAA-MM-DD HH:MM:SS` |
| `fin` | texto | Fin local, con el mismo formato y posterior al inicio |
| `origen` | texto | Estación de salida |
| `destino` | texto | Estación de llegada |

Estaciones admitidas: CENTRO, PARQUE, RETIRO, FACULTAD y PLAZA.
Los horarios se interpretan como hora local de Buenos Aires, sin conversiones
de zona horaria. El archivo CSV tiene encabezado y separador coma; el JSON es
una lista de objetos con estos cinco campos. Ambos usan UTF-8.

## Cómo repetir la generación

Desde la raíz del proyecto:

```bash
python data/generar_datos.py
```

El script utiliza `random.Random(42)` para generar 60 viajes del 1 al 10 de
septiembre de 2026, seis por día, con duraciones de 8 a 45 minutos. Origen y
destino se eligen de forma independiente; se admiten regresos a la misma
estación. No es necesario generar de nuevo los archivos para usar la aplicación.

Se agregan ocho filas para verificar el tratamiento de errores:

| Registro (sin encabezado) | Error esperado |
| --- | --- |
| 61 | Repetición del identificador V004 |
| 62 | Identificador con formato incorrecto |
| 63 | Fecha que no existe en el calendario |
| 64 | Fin anterior al inicio |
| 65 | Origen faltante |
| 66 | Destino desconocido |
| 67 | Fin faltante |
| 68 | Fin igual al inicio |

Las filas 1, 2 y 3 contienen espacios o minúsculas recuperables. Se espera
registrar esas tres correcciones, aceptar 60 viajes y rechazar ocho.

## Limitaciones

La frecuencia de seis viajes diarios fue elegida para simplificar la muestra.
No modela demanda, estaciones cercanas, capacidad, clima ni hábitos de personas.
Los conteos sirven para comprobar el programa, no para recomendar cambios en
una red real. No hay inventario inicial ni viajes de reposición.
