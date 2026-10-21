# TP2 - Reporte de movimientos de bicicletas

**Autor:** Agustín Casal

**Materia:** Programación Orientada a Datos - UCA, 2026

## Propuesta

Una persona que revisa los viajes de una red de bicicletas necesita saber
cuántas bicicletas salieron y llegaron a cada estación durante un período.
Los archivos pueden contener datos incompletos o viajes repetidos que alteran
los conteos.

La aplicación leerá viajes desde CSV o JSON, separará los registros inválidos,
permitirá elegir fechas y generará un reporte por estación. El balance se
calculará como llegadas menos salidas. Un balance negativo indica más salidas
que llegadas en el período; no indica cuántas bicicletas quedan disponibles.

Es una adaptación de la propuesta 7 del apéndice A de la consigna. La primera
versión usa datos simulados, cinco estaciones ficticias y una interfaz de
consola. Quedan fuera los mapas, las cuentas de usuarios, las reservas,
el inventario inicial y las reposiciones en camión.

## Organización prevista

- `src/`: lectura, validación, balance y ejecución.
- `data/`: muestra equivalente en CSV y JSON y explicación de los datos.
- `tests/`: pruebas ejecutables con `unittest`.
- `outputs/`: reportes generados, excluidos del historial Git.

Solo se necesita Python 3.10 o superior.
