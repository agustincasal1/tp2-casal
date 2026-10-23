# TP2 - Movimientos de bicicletas

Agustín Casal · Programación Orientada a Datos · UCA, 2026

## Problema

Una persona que administra una red de bicicletas necesita saber cuántas salidas
y llegadas hubo en cada estación durante un período. Contarlas a mano lleva
tiempo, y los viajes repetidos o incompletos pueden cambiar el resultado.

El programa lee viajes desde CSV o JSON, separa los registros con errores y
arma un reporte por estación. Permite elegir fechas y guardar los resultados.
Tomé como base la propuesta de Ecobici del apéndice A de la consigna, con cinco
estaciones ficticias para mantener acotado el trabajo.

## Fuente de los datos

La muestra es simulada y se preparó para este TP el 23/10/2026 con el script
`data/generar_datos.py`, usando semilla 42. No son datos oficiales de Ecobici.
Cada fila representa un viaje con identificador, inicio, fin, origen y destino.
Hay 60 viajes válidos y ocho registros con errores agregados para probar la
limpieza. Los archivos CSV y JSON contienen la misma muestra.

La descripción de las variables y el procedimiento están en
[data/README.md](data/README.md). Se permite usar y modificar estos datos con
fines educativos citando el repositorio. No contienen datos personales.

## Cómo correrlo

Se necesita Python 3.10 o superior; fue probado con Python 3.13. Solo usa la
biblioteca estándar, por lo que no hay paquetes externos para instalar.
`requirements.txt` también lo indica.

Desde la carpeta que contiene el proyecto, entrá a `tp2-casal` y ejecutá:

```bash
cd tp2-casal
python -m src.main data/viajes.csv
```

Si la terminal ya está en `tp2-casal`, ejecutá solo el comando de Python.
Para consultar dos días usando JSON y guardar esa consulta por separado:

```bash
python -m src.main data/viajes.json --desde 2026-09-01 --hasta 2026-09-02 --salida outputs/dos_dias
```

Las fechas incluyen ambos días. Se puede usar un solo límite o ninguno. El
filtro toma la fecha de inicio: si un viaje termina al día siguiente, se cuentan
sus dos extremos en el día en que empezó. La ayuda se consulta con
`python -m src.main --help`.

## Limpieza

Se comprueba que estén los cinco campos, se quitan espacios exteriores y se
pasan los códigos y estaciones a mayúsculas. Cada cambio queda registrado.
El identificador debe cumplir `V[0-9]{3}` con `fullmatch`, por ejemplo `V015`.
Las fechas se revisan con una expresión regular y con `datetime.strptime`,
porque tener el formato correcto no garantiza que existan en el calendario.

Se rechazan los faltantes, las estaciones desconocidas, los identificadores
incorrectos y los viajes cuyo fin no sea posterior al inicio. Ante un duplicado
se conserva la primera aparición válida del identificador. No se completan
valores desconocidos. Se limpia todo el archivo antes de filtrar las fechas,
y el archivo original no se modifica.

## Resultados

Con la muestra completa, tanto en CSV como en JSON:

```text
Leídos: 68 | Válidos: 60 | Rechazados: 8
Viajes del período: 60
Estación      Salidas Llegadas  Balance
CENTRO             15       13       -2
FACULTAD            5       11        6
PARQUE             18       11       -7
PLAZA              13       15        2
RETIRO              9       10        1
```

El balance es llegadas menos salidas. Por ejemplo, PARQUE tiene siete salidas
más que llegadas. La suma de los balances da cero porque cada viaje aporta una
salida y una llegada. La consulta del 1 y 2 de septiembre selecciona 12 viajes.

Los archivos quedan en `outputs/` o en la carpeta elegida con `--salida`:

| Archivo | Contenido |
| --- | --- |
| `reporte.csv` | Salidas, llegadas y balance por estación |
| `seleccionados.csv` | Viajes usados en el reporte |
| `rechazos.csv` | Filas originales rechazadas y sus motivos |
| `correcciones.csv` | Valores originales y normalizados |
| `resumen.json` | Conteos generales y fechas consultadas |

Las filas se numeran desde 1, sin contar el encabezado CSV. Cada ejecución
reemplaza las salidas de la carpeta indicada, incluso cuando no hay rechazos.
Para conservar consultas distintas hay que usar carpetas distintas.

Si no hay viajes en el período, se informa y se muestran ceros. Si todos son
inválidos, se guardan los rechazos y se termina con error. Una falla de lectura
o de estructura detiene la ejecución y no actualiza las salidas anteriores.

## Organización y pruebas

- `src/fuentes.py`: `FuenteDatos` define la interfaz de lectura; `FuenteCSV`
  y `FuenteJSON` la implementan y devuelven listas de diccionarios.
- `src/modelo.py`: `BalanceEstacion` guarda los conteos de una estación y tiene
  métodos para registrar movimientos y calcular su balance.
- `src/pipeline.py`: validación, limpieza, selección, cálculo y escritura.
- `src/main.py`: argumentos de consola y coordinación del procesamiento.
- `tests/`: pruebas de lectura, limpieza, balances y ejecución completa.

La limpieza usa ciclos, condicionales y un conjunto para detectar duplicados.
El filtro usa una comprensión y los controles de totales usan generadores.
Las transformaciones devuelven resultados nuevos; la lectura y escritura se
mantienen separadas de los cálculos.

Desde `tp2-casal`, las pruebas se ejecutan con:

```bash
python -m unittest discover -s tests -v
```

Hay 66 pruebas, incluidos seis casos de error de consola en `test_errores.py`:
JSON incompleto, columnas faltantes, valores sobrantes, encabezados repetidos,
codificación incorrecta y una carpeta de salida ocupada por un archivo.
Se espera que el programa los detecte, termine con código 1 y conserve las
entradas. También se comprueba que no se pierdan filas, que los balances sumen
cero y que CSV y JSON produzcan las mismas salidas.

## Limitaciones

El balance no indica bicicletas disponibles: faltan el stock inicial y las
reposiciones. Esta versión no incluye mapas, reservas ni conexión con servicios
externos. Los datos simulados permiten comprobar el programa, pero no estudiar
la demanda real.

Versión de entrega: `v1.0`.
