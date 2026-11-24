# Tablas originales, columnas y tipos por endpoint

Inventario generado inspeccionando las cabeceras de cada CSV y todas las hojas Excel de los originales descargados, incluidos los miembros de los ZIP. Incluye sanidad, contaminación, metadatos y demografía.

Un CSV no declara tipos. **Tipo lógico** describe cómo interpretar el dato según su columna; no es un contrato publicado por el proveedor. Los CSV se inspeccionan como `string`, igual que los lectores del proyecto, para conservar códigos y formato numérico original. Excel contiene celdas tipadas y puede mezclar tipos en una columna.

[Tablas por descarga](source_tables.csv) relaciona cada URL con archivo, miembro ZIP, hoja y esquema. [Diccionario completo de columnas](source_columns.csv) añade el tipo lógico, tipo de lectura y dtype de pandas observado en una muestra de hasta 30 filas por tabla. Ese dtype es orientativo: no certifica el tipo ni la ausencia de nulos del archivo completo. No se ha hecho una validación completa de todos los contaminantes ni se han añadido al modelado.

Los esquemas repetidos se muestran una sola vez y se enlazan desde la documentación de endpoints. La lista exacta de tablas que usa cada esquema figura debajo. `Unnamed: n` identifica una cabecera vacía del Excel, no un nombre oficial.

## schema-01

Área: `health`. Formato: `csv`. Tablas con esta estructura: 3.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| Diagnóstico principal (CIE10MC) | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Total Nacional | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Comunidades y Ciudades Autónomas | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Provincias | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Total | decimal o ausente | string | Tasa de altas por 100.000; formato español; '..' o blanco = ausente. |

Tablas originales que utilizan este esquema:

- `source-table-001`: `data/raw/health_air_history/ine_tasas_residencia_2016.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/28285.csv).
- `source-table-004`: `data/raw/health_air_history/ine_tasas_residencia_2019.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/48186.csv).
- `source-table-006`: `data/raw/health_air_history/ine_tasas_residencia_2021.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/58468.csv).

## schema-02

Área: `health`. Formato: `csv`. Tablas con esta estructura: 7.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| Diagnóstico principal (CIE10MC) | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Provincia, Comunidad y Ciudad autónoma de residencia | texto | string | Diagnóstico o territorio original; puede incluir código y nombre. |
| Total | decimal o ausente | string | Tasa de altas por 100.000; formato español; '..' o blanco = ausente. |

Tablas originales que utilizan este esquema:

- `source-table-002`: `data/raw/health_air_history/ine_tasas_residencia_2017.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/30126.csv).
- `source-table-003`: `data/raw/health_air_history/ine_tasas_residencia_2018.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/34937.csv).
- `source-table-005`: `data/raw/health_air_history/ine_tasas_residencia_2020.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/52180.csv).
- `source-table-007`: `data/raw/health_air_history/ine_tasas_residencia_2022.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/66371.csv).
- `source-table-008`: `data/raw/health_air_history/ine_tasas_residencia_2023.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/74921.csv).
- `source-table-009`: `data/raw/health_air_history/ine_tasas_residencia_2024.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/79536.csv).
- `source-table-185`: `data/raw/health_air_feasibility/ine_morbilidad_residencia_2024_79536.csv` — [GET](https://www.ine.es/jaxi/files/tpx/csv_bdsc/79536.csv).

## schema-03

Área: `air`. Formato: `csv`. Tablas con esta estructura: 69.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| PROVINCIA | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| MAGNITUD | código (texto recomendado) | string | Puede aparecer como número en Excel. Identificador, no cantidad. |
| PUNTO_MUESTREO | texto identificador | string | Conservar exactamente; no convertir a número. |
| ANNO | entero | string | Componente de fecha; no es una fecha completa por sí solo. |
| MES | entero | string | Componente de fecha; no es una fecha completa por sí solo. |
| D01 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D02 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D03 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D04 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D05 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D06 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D07 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D08 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D09 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D10 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D11 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D12 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D13 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D14 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D15 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D16 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D17 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D18 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D19 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D20 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D21 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D22 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D23 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D24 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D25 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D26 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D27 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D28 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D29 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D30 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D31 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |

Tablas originales que utilizan este esquema:

- `source-table-010`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/As_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-011`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/B(a)P_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-012`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/C6H6_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-013`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/Cd_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-014`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/Ni_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-015`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/Pb_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-016`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/PM10_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-017`: `data/raw/health_air_history/miteco_diarios_2023.zip → Datos diarios 2023/PM2.5_DD_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20diarios%202023.zip).
- `source-table-030`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/As_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-031`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/B(a)P_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-032`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/C6H6_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-033`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/Cd_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-034`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/Ni_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-035`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/Pb_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-036`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/PM10_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-037`: `data/raw/health_air_history/miteco_diarios_2022.zip → Datos diarios 2022/PM2.5_DD_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20diarios%202022.zip).
- `source-table-049`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/As_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-050`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/BaP_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-051`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/Cd_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-052`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/Ni_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-053`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/Pb_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-054`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/PM10_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-055`: `data/raw/health_air_history/miteco_diarios_2021.zip → Datos_diarios/PM25_DD_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_diarios_tcm30-545536.zip).
- `source-table-072`: `data/raw/health_air_history/miteco_diarios_2020.zip → As_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-073`: `data/raw/health_air_history/miteco_diarios_2020.zip → B(a)P_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-074`: `data/raw/health_air_history/miteco_diarios_2020.zip → C6H6_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-075`: `data/raw/health_air_history/miteco_diarios_2020.zip → Cd_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-076`: `data/raw/health_air_history/miteco_diarios_2020.zip → Ni_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-077`: `data/raw/health_air_history/miteco_diarios_2020.zip → Pb_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-078`: `data/raw/health_air_history/miteco_diarios_2020.zip → PM10_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-079`: `data/raw/health_air_history/miteco_diarios_2020.zip → PM2.5_DD_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2020_tcm30-531263.zip).
- `source-table-091`: `data/raw/health_air_history/miteco_diarios_2019.zip → As_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-092`: `data/raw/health_air_history/miteco_diarios_2019.zip → BaP_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-093`: `data/raw/health_air_history/miteco_diarios_2019.zip → C6H6_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-094`: `data/raw/health_air_history/miteco_diarios_2019.zip → Cd_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-095`: `data/raw/health_air_history/miteco_diarios_2019.zip → Ni_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-096`: `data/raw/health_air_history/miteco_diarios_2019.zip → Pb_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-097`: `data/raw/health_air_history/miteco_diarios_2019.zip → PM10_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-098`: `data/raw/health_air_history/miteco_diarios_2019.zip → PM25_DD_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_2019_tcm30-513558.zip).
- `source-table-110`: `data/raw/health_air_history/miteco_diarios_2018.zip → As_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-111`: `data/raw/health_air_history/miteco_diarios_2018.zip → B(a)P_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-112`: `data/raw/health_air_history/miteco_diarios_2018.zip → Cd_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-113`: `data/raw/health_air_history/miteco_diarios_2018.zip → Ni_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-114`: `data/raw/health_air_history/miteco_diarios_2018.zip → Pb_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-115`: `data/raw/health_air_history/miteco_diarios_2018.zip → PM10_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-116`: `data/raw/health_air_history/miteco_diarios_2018.zip → PM2.5_DD_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/dd_2018_tcm30-501405.zip).
- `source-table-128`: `data/raw/health_air_history/miteco_diarios_2017.zip → As_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-129`: `data/raw/health_air_history/miteco_diarios_2017.zip → B(a)P_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-130`: `data/raw/health_air_history/miteco_diarios_2017.zip → Cd_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-131`: `data/raw/health_air_history/miteco_diarios_2017.zip → Ni_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-132`: `data/raw/health_air_history/miteco_diarios_2017.zip → Pb_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-133`: `data/raw/health_air_history/miteco_diarios_2017.zip → PM10_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-134`: `data/raw/health_air_history/miteco_diarios_2017.zip → PM2.5_DD_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-481444.zip).
- `source-table-164`: `data/raw/health_air_history/miteco_diarios_2024.zip → Pb_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-165`: `data/raw/health_air_history/miteco_diarios_2024.zip → PM2.5_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-166`: `data/raw/health_air_history/miteco_diarios_2024.zip → PM10_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-167`: `data/raw/health_air_history/miteco_diarios_2024.zip → As_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-168`: `data/raw/health_air_history/miteco_diarios_2024.zip → B(a)P_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-169`: `data/raw/health_air_history/miteco_diarios_2024.zip → C6H6_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-170`: `data/raw/health_air_history/miteco_diarios_2024.zip → Cd_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-171`: `data/raw/health_air_history/miteco_diarios_2024.zip → Ni_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-186`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → Pb_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-187`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → PM2.5_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-188`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → PM10_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-189`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → As_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-190`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → B(a)P_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-191`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → C6H6_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-192`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → Cd_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).
- `source-table-193`: `data/raw/health_air_feasibility/miteco_datos_diarios_2024.zip → Ni_DD_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip).

## schema-04

Área: `air`. Formato: `csv`. Tablas con esta estructura: 75.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| PROVINCIA | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | string | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| MAGNITUD | código (texto recomendado) | string | Puede aparecer como número en Excel. Identificador, no cantidad. |
| PUNTO_MUESTREO | texto identificador | string | Conservar exactamente; no convertir a número. |
| ANNO | entero | string | Componente de fecha; no es una fecha completa por sí solo. |
| MES | entero | string | Componente de fecha; no es una fecha completa por sí solo. |
| DIA | entero | string | Componente de fecha; no es una fecha completa por sí solo. |
| H01 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H02 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H03 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H04 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H05 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H06 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H07 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H08 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H09 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H10 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H11 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H12 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H13 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H14 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H15 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H16 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H17 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H18 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H19 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H20 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H21 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H22 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H23 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H24 | decimal o ausente | string | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |

Tablas originales que utilizan este esquema:

- `source-table-018`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/C6H6_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-019`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/CO_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-020`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/NO2_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-021`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/NOx_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-022`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/NO_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-023`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/O3_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-024`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/PM10_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-025`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/PM25_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-026`: `data/raw/health_air_history/miteco_horarios_2023.zip → Datos horarios 2023/SO2_HH_2023.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Datos%20horarios%202023.zip).
- `source-table-038`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/C6H6_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-039`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/CO_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-040`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/NO2_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-041`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/NOx_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-042`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/O3_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-043`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/PM10_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-044`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/PM25_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-045`: `data/raw/health_air_history/miteco_horarios_2022.zip → Datos horarios 2022/SO2_HH_2022.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Datos%20horarios%202022.zip).
- `source-table-056`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/20_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-057`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/31_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-058`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/42_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-059`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/431_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-060`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/44_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-061`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/C6H6_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-062`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/CO_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-063`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/NO2_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-064`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/NOx_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-065`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/O3_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-066`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/PM10_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-067`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/PM25_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-068`: `data/raw/health_air_history/miteco_horarios_2021.zip → Datos_horarios/SO2_HH_2021.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/datos_horarios_tcm30-545543.zip).
- `source-table-080`: `data/raw/health_air_history/miteco_horarios_2020.zip → C6H6_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-081`: `data/raw/health_air_history/miteco_horarios_2020.zip → CO_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-082`: `data/raw/health_air_history/miteco_horarios_2020.zip → NO2_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-083`: `data/raw/health_air_history/miteco_horarios_2020.zip → NOx_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-084`: `data/raw/health_air_history/miteco_horarios_2020.zip → NO_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-085`: `data/raw/health_air_history/miteco_horarios_2020.zip → O3_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-086`: `data/raw/health_air_history/miteco_horarios_2020.zip → PM10_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-087`: `data/raw/health_air_history/miteco_horarios_2020.zip → PM25_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-088`: `data/raw/health_air_history/miteco_horarios_2020.zip → SO2_HH_2020.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2020_tcm30-531262.zip).
- `source-table-099`: `data/raw/health_air_history/miteco_horarios_2019.zip → C6H6_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-100`: `data/raw/health_air_history/miteco_horarios_2019.zip → CO_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-101`: `data/raw/health_air_history/miteco_horarios_2019.zip → NO2_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-102`: `data/raw/health_air_history/miteco_horarios_2019.zip → NOx_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-103`: `data/raw/health_air_history/miteco_horarios_2019.zip → NO_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-104`: `data/raw/health_air_history/miteco_horarios_2019.zip → O3_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-105`: `data/raw/health_air_history/miteco_horarios_2019.zip → PM10_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-106`: `data/raw/health_air_history/miteco_horarios_2019.zip → PM25_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-107`: `data/raw/health_air_history/miteco_horarios_2019.zip → SO2_HH_2019.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2019_tcm30-513559.zip).
- `source-table-117`: `data/raw/health_air_history/miteco_horarios_2018.zip → C6H6_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-118`: `data/raw/health_air_history/miteco_horarios_2018.zip → CO_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-119`: `data/raw/health_air_history/miteco_horarios_2018.zip → NO2_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-120`: `data/raw/health_air_history/miteco_horarios_2018.zip → NOx_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-121`: `data/raw/health_air_history/miteco_horarios_2018.zip → NO_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-122`: `data/raw/health_air_history/miteco_horarios_2018.zip → O3_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-123`: `data/raw/health_air_history/miteco_horarios_2018.zip → PM10_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-124`: `data/raw/health_air_history/miteco_horarios_2018.zip → PM25_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-125`: `data/raw/health_air_history/miteco_horarios_2018.zip → SO2_HH_2018.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_2018_tcm30-501406.zip).
- `source-table-135`: `data/raw/health_air_history/miteco_horarios_2017.zip → C6H6_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-136`: `data/raw/health_air_history/miteco_horarios_2017.zip → CO_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-137`: `data/raw/health_air_history/miteco_horarios_2017.zip → NO2_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-138`: `data/raw/health_air_history/miteco_horarios_2017.zip → NOx_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-139`: `data/raw/health_air_history/miteco_horarios_2017.zip → NO_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-140`: `data/raw/health_air_history/miteco_horarios_2017.zip → O3_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-141`: `data/raw/health_air_history/miteco_horarios_2017.zip → PM10_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-142`: `data/raw/health_air_history/miteco_horarios_2017.zip → PM25_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-143`: `data/raw/health_air_history/miteco_horarios_2017.zip → SO2_HH_2017.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-481445.zip).
- `source-table-172`: `data/raw/health_air_history/miteco_horarios_2024.zip → PM10_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-173`: `data/raw/health_air_history/miteco_horarios_2024.zip → PM25_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-174`: `data/raw/health_air_history/miteco_horarios_2024.zip → SO2_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-175`: `data/raw/health_air_history/miteco_horarios_2024.zip → C6H6_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-176`: `data/raw/health_air_history/miteco_horarios_2024.zip → CO_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-177`: `data/raw/health_air_history/miteco_horarios_2024.zip → NO_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-178`: `data/raw/health_air_history/miteco_horarios_2024.zip → NO2_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-179`: `data/raw/health_air_history/miteco_horarios_2024.zip → NOx_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).
- `source-table-180`: `data/raw/health_air_history/miteco_horarios_2024.zip → O3_HH_2024.csv` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_HH_2024.zip).

## schema-05

Área: `air`. Formato: `xlsx`. Tablas con esta estructura: 9.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| MAGNITUD | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Identificador, no cantidad. |
| NOMBRE | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| ABREVIATURA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| UNIDAD | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| GRUPO | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |

Tablas originales que utilizan este esquema:

- `source-table-027`: `data/raw/health_air_history/miteco_estaciones_2023.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Metainformacion2023_19022025.xlsx).
- `source-table-046`: `data/raw/health_air_history/miteco_estaciones_2022.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Metainformacion2022.xlsx).
- `source-table-069`: `data/raw/health_air_history/miteco_estaciones_2021.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion2021_tcm30-545563.xlsx).
- `source-table-089`: `data/raw/health_air_history/miteco_estaciones_2020.xlsx → magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacionestacionesymagnitudes2020_tcm30-531266.xlsx).
- `source-table-108`: `data/raw/health_air_history/miteco_estaciones_2019.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion_2019_tcm30-513561.xlsx).
- `source-table-126`: `data/raw/health_air_history/miteco_estaciones_2018.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion_2018_tcm30-501408.xlsx).
- `source-table-144`: `data/raw/health_air_history/miteco_estaciones_2017.xlsx → magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/estacionesymagnitudes_2017_tcm30-481509.xlsx).
- `source-table-181`: `data/raw/health_air_history/miteco_estaciones_2024.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).
- `source-table-194`: `data/raw/health_air_feasibility/miteco_metainformacion_2024.xlsx → Magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).

## schema-06

Área: `air`. Formato: `xlsx`. Tablas con esta estructura: 5.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| TECNICA | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Identificador, no cantidad. |
| NOMBRE | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| NOMBRE_I | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| Unnamed: 3 | sin interpretación asignada | Celdas Excel; dtype inferido por pandas | Encabezado vacío en el Excel: nombre asignado por pandas. No utilizado por los mapeadores. |
| Unnamed: 4 | sin interpretación asignada | Celdas Excel; dtype inferido por pandas | Encabezado vacío en el Excel: nombre asignado por pandas. No utilizado por los mapeadores. |
| OTROS CÓDIGOS | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| Unnamed: 6 | sin interpretación asignada | Celdas Excel; dtype inferido por pandas | Encabezado vacío en el Excel: nombre asignado por pandas. No utilizado por los mapeadores. |

Tablas originales que utilizan este esquema:

- `source-table-028`: `data/raw/health_air_history/miteco_estaciones_2023.xlsx → Técnicas` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Metainformacion2023_19022025.xlsx).
- `source-table-047`: `data/raw/health_air_history/miteco_estaciones_2022.xlsx → Técnicas` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Metainformacion2022.xlsx).
- `source-table-070`: `data/raw/health_air_history/miteco_estaciones_2021.xlsx → Técnicas` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion2021_tcm30-545563.xlsx).
- `source-table-182`: `data/raw/health_air_history/miteco_estaciones_2024.xlsx → Técnicas` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).
- `source-table-195`: `data/raw/health_air_feasibility/miteco_metainformacion_2024.xlsx → Técnicas` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).

## schema-07

Área: `air`. Formato: `xlsx`. Tablas con esta estructura: 9.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| COD_LOCAL | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 8 posiciones en el esquema normalizado. |
| PROVINCIA | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| COD_ESTACION_DEM | texto identificador | Celdas Excel; dtype inferido por pandas | Conservar exactamente; no convertir a número. |
| N_RED | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| NOMBRE | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| FECHA_INI | fecha o ausente | Celdas Excel; dtype inferido por pandas | Inicio/fin registrado de estación; conservar ausencia de fin. Revisar celdas originales antes de convertir. |
| FECHA_FIN | fecha o ausente | Celdas Excel; dtype inferido por pandas | Inicio/fin registrado de estación; conservar ausencia de fin. Revisar celdas originales antes de convertir. |
| LATITUD_G | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| LONGITUD_G | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| ALTITUD | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| N_CCAA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| N_PROVINCIA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| N_MUNICIPIO | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_ESTACION | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_AREA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_SUBAREA_RURAL | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| EST | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| ZONA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| DIRECCION | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |

Tablas originales que utilizan este esquema:

- `source-table-029`: `data/raw/health_air_history/miteco_estaciones_2023.xlsx → Estaciones2023` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2023/Metainformacion2023_19022025.xlsx).
- `source-table-048`: `data/raw/health_air_history/miteco_estaciones_2022.xlsx → Estaciones` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2022/Metainformacion2022.xlsx).
- `source-table-071`: `data/raw/health_air_history/miteco_estaciones_2021.xlsx → Estaciones` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion2021_tcm30-545563.xlsx).
- `source-table-090`: `data/raw/health_air_history/miteco_estaciones_2020.xlsx → Estaciones` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacionestacionesymagnitudes2020_tcm30-531266.xlsx).
- `source-table-109`: `data/raw/health_air_history/miteco_estaciones_2019.xlsx → Estaciones evaluación 2019` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion_2019_tcm30-513561.xlsx).
- `source-table-127`: `data/raw/health_air_history/miteco_estaciones_2018.xlsx → Estaciones evaluación 2018` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/metainformacion_2018_tcm30-501408.xlsx).
- `source-table-145`: `data/raw/health_air_history/miteco_estaciones_2017.xlsx → estaciones_evaluacion_2017` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/estacionesymagnitudes_2017_tcm30-481509.xlsx).
- `source-table-183`: `data/raw/health_air_history/miteco_estaciones_2024.xlsx → Estaciones_2024` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).
- `source-table-196`: `data/raw/health_air_feasibility/miteco_metainformacion_2024.xlsx → Estaciones_2024` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Metainformacion_2024.xlsx).

## schema-08

Área: `air`. Formato: `xlsx`. Tablas con esta estructura: 7.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| PROVINCIA | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| MAGNITUD | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Identificador, no cantidad. |
| PUNTO_MUESTREO | texto identificador | Celdas Excel; dtype inferido por pandas | Conservar exactamente; no convertir a número. |
| ANNO | entero | Celdas Excel; dtype inferido por pandas | Componente de fecha; no es una fecha completa por sí solo. |
| MES | entero | Celdas Excel; dtype inferido por pandas | Componente de fecha; no es una fecha completa por sí solo. |
| D01 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D02 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D03 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D04 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D05 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D06 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D07 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D08 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D09 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D10 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D11 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D12 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D13 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D14 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D15 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D16 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D17 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D18 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D19 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D20 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D21 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D22 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D23 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D24 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D25 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D26 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D27 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D28 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D29 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D30 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| D31 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |

Tablas originales que utilizan este esquema:

- `source-table-146`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/As_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-147`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/B(a)P_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-148`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/Cd_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-149`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/Ni_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-150`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/Pb_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-151`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/PM10_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).
- `source-table-152`: `data/raw/health_air_history/miteco_diarios_2016.zip → Diarios/PM25_DD_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/diarios_tcm30-432277.zip).

## schema-09

Área: `air`. Formato: `xlsx`. Tablas con esta estructura: 9.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| PROVINCIA | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| MAGNITUD | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Identificador, no cantidad. |
| PUNTO_MUESTREO | texto identificador | Celdas Excel; dtype inferido por pandas | Conservar exactamente; no convertir a número. |
| ANNO | entero | Celdas Excel; dtype inferido por pandas | Componente de fecha; no es una fecha completa por sí solo. |
| MES | entero | Celdas Excel; dtype inferido por pandas | Componente de fecha; no es una fecha completa por sí solo. |
| DIA | entero | Celdas Excel; dtype inferido por pandas | Componente de fecha; no es una fecha completa por sí solo. |
| H01 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H02 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H03 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H04 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H05 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H06 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H07 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H08 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H09 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H10 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H11 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H12 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H13 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H14 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H15 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H16 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H17 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H18 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H19 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H20 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H21 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H22 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H23 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |
| H24 | decimal o ausente | Celdas Excel; dtype inferido por pandas | Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero. |

Tablas originales que utilizan este esquema:

- `source-table-153`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/C6H6_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-154`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/CO_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-155`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/NO2_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-156`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/NOx_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-157`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/NO_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-158`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/O3_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-159`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/PM10_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-160`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/PM2.5_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).
- `source-table-161`: `data/raw/health_air_history/miteco_horarios_2016.zip → Horarios/SO2_HH_2016.xlsx → Hoja1` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/horarios_tcm30-432276.zip).

## schema-10

Área: `air`. Formato: `xls`. Tablas con esta estructura: 1.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| MAGNITUD | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Identificador, no cantidad. |
| NOMBRE | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| ABREVIATURA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| UNIDAD | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| GRUPO | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |

Tablas originales que utilizan este esquema:

- `source-table-162`: `data/raw/health_air_history/miteco_estaciones_2016.xls → magnitudes` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/estacionesymagnitudesevaluacion2016_tcm30-432280.xls).

## schema-11

Área: `air`. Formato: `xls`. Tablas con esta estructura: 1.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| COD_LOCAL | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 8 posiciones en el esquema normalizado. |
| PROVINCIA | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 2 posiciones en el esquema normalizado. |
| MUNICIPIO | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| ESTACION | código (texto recomendado) | Celdas Excel; dtype inferido por pandas | Puede aparecer como número en Excel. Conservar como texto con 3 posiciones en el esquema normalizado. |
| COD_ESTACION_DEM | texto identificador | Celdas Excel; dtype inferido por pandas | Conservar exactamente; no convertir a número. |
| N_RED | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| NOMBRE | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| FECHA_INI | fecha o ausente | Celdas Excel; dtype inferido por pandas | Inicio/fin registrado de estación; conservar ausencia de fin. Revisar celdas originales antes de convertir. |
| FECHA_FIN | fecha o ausente | Celdas Excel; dtype inferido por pandas | Inicio/fin registrado de estación; conservar ausencia de fin. Revisar celdas originales antes de convertir. |
| LATITUD_G | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| LONGITUD_G | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| ALTITUD | decimal o ausente | Celdas Excel; dtype inferido por pandas | Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional. |
| N_CCAA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| N_PROVINCIA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| N_MUNICIPIO | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_ESTACION | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_AREA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| TIPO_SUBAREA_RURAL | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| EST | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| ZONA | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |
| DIRECCION | texto o ausente | Celdas Excel; dtype inferido por pandas | Etiqueta o categoría del catálogo original. |

Tablas originales que utilizan este esquema:

- `source-table-163`: `data/raw/health_air_history/miteco_estaciones_2016.xls → estaciones_evaluación_2016` — [GET](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/estacionesymagnitudesevaluacion2016_tcm30-432280.xls).

## schema-12

Área: `demographics`. Formato: `csv`. Tablas con esta estructura: 1.

| Columna original | Tipo lógico | Tipo de lectura | Interpretación |
| --- | --- | --- | --- |
| Edad simple | texto | string | Categoría original; Provincias incluye código y nombre. |
| Provincias | texto | string | Categoría original; Provincias incluye código y nombre. |
| Sexo | texto | string | Categoría original; Provincias incluye código y nombre. |
| Periodo | texto de fecha de referencia | string | Etiqueta del INE; se convierte a año y fecha de referencia tras filtrar. |
| Total | entero o ausente | string | Población; formato español. La selección utilizada exige recuentos completos. |

Tablas originales que utilizan este esquema:

- `source-table-184`: `data/raw/demographics/ine_poblacion_provincias_edad_56945.csv` — [GET](https://www.ine.es/jaxiT3/files/t/csv_bdsc/56945.csv).

