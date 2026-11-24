# Gráficos de Madrid y Barcelona provincia

Las pestañas **Madrid** y **Barcelona provincia** de **Gráficos** permiten explorar cada experimento con sus propios datos guardados. No se entrenan ni evalúan modelos de nuevo. Barcelona representa Rubí (Ca n’Oriol), Sant Celoni (Carles Damm) y Sant Vicenç dels Horts (Ribot–Sant Miquel), fuera de Barcelona ciudad. La [selección territorial](38_experimentos_madrid_barcelona.md) detalla cobertura y limitaciones.

## Vistas y navegación

| Vista | Madrid | Barcelona provincia |
| --- | --- | --- |
| Mapa y observaciones | MITECO 2017–2024, EEA 2025 | MITECO 2017–2024 |
| Predicciones | Regresión de 2024 | Regresión de 2024 |
| Resultados | Regresión 2024 y comienzos 2025 | Regresión 2024 |
| Errores | Estación, mes, nivel y sensibilidad a cinco fechas | Estación, mes y nivel; sensibilidad a cinco fechas no preparada |
| Incertidumbre | Bootstrap por bloques guardado | Bootstrap por bloques guardado |
| Explicabilidad individual | Ridge 2024 | Coeficientes en Experimentos → Importancia agrupada |

El título identifica el territorio. Al cambiarlo, se conserva la vista si está disponible en los dos territorios. Si se pasa de Explicabilidad a Barcelona, se abre Predicciones. Se elige la primera estación del nuevo territorio o se mantiene «Todas las estaciones» si estaba elegida. La fecha se conserva dentro del periodo permitido; desde 2025 hacia Barcelona se cambia al mismo mes y día de 2024. Las vistas se reinician para no mostrar resultados anteriores durante la carga. El mapa se centra en los nuevos puntos. El centrado y el zoom no animan transiciones entre territorios para evitar eventos pendientes al desmontar el mapa anterior. Territorio, estación y fecha se comparten entre vistas y se conservan al salir de Gráficos. Los accesos de Inicio y Casos apuntan explícitamente a Madrid, al que pertenecen sus ejemplos.

Concentraciones, predicciones y errores se expresan en µg/m³. El umbral estadístico compartido es PM10 > 27 µg/m³, sin interpretación clínica ni normativa. Los nulos se conservan y las fechas no evaluadas no reciben predicciones inventadas. Los picos originales no se recortan. El mapa no interpola concentraciones y sus coordenadas fijas no reconstruyen movimientos históricos. El fondo OpenStreetMap requiere Internet; valores y lista son locales.

Las muestras evaluadas de 2024 contienen 1.013 filas en Madrid y 801 en Barcelona; los MAE Ridge/persistencia son 5,9581/6,0575 y 4,7204/5,2805 µg/m³. Las fechas y coberturas difieren. La comparación sobre fechas comunes sigue en Experimentos → Comparación; el selector de Gráficos no iguala cohortes ni demuestra transferencia entre territorios.

## Archivos y formatos

| Contenido | Madrid | Barcelona provincia |
| --- | --- | --- |
| Diario observado (CSV) | `data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv`; EEA: `output/pm10_weather_test_2025/pm10_diario_2025.csv` | `data/interim/experiments/barcelona/diario_2017_2024.csv` |
| Coordenadas (CSV) | `data/interim/provincial_feasibility/history/seleccion_estaciones_pm10_2024.csv`, LATITUD_G/LONGITUD_G | `data/interim/experiments/barcelona/estaciones.csv`, latitud/longitud |
| Predicciones (CSV) | `output/pm10_final_2024/predicciones_regresion.csv` | `output/experiments/barcelona/prueba_2024/predicciones.csv` |
| Métricas (CSV) | `output/pm10_final_2024/metricas_regresion.csv` | `output/experiments/barcelona/prueba_2024/metricas.csv` |
| Errores | `output/pm10_error_analysis/analisis.json` | `output/experiments/barcelona/prueba_2024/errores.csv` |
| Intervalos (JSON) | `output/pm10_bootstrap/analisis.json` | `output/experiments/barcelona/prueba_2024/bootstrap.json` |

Los esquemas y mapeadores originales se mantienen en [fuentes](15_fuentes_endpoints_formatos.md), [trazabilidad](16_trazabilidad_mappers_tablas.md) y [experimento territorial](38_experimentos_madrid_barcelona.md).

## API local

Todos los endpoints GET responden JSON y aceptan `territory=madrid|barcelona`; omitirlo mantiene Madrid, por compatibilidad. Las cachés de diarios, predicciones y métricas distinguen territorio.

| Endpoint | Otros parámetros | Contenido y tipos principales |
| --- | --- | --- |
| `/api/charts/map` | `date`: fecha ISO | Fecha/territorio/proveedor/ruta: textos; año: entero; columnas de coordenadas: lista de textos; estaciones: código/nombre (texto), coordenadas (reales), valor (real nullable) |
| `/api/charts/pm10` | `station`: código; `month`: AAAA-MM | Proveedor/territorio: textos; umbral: número; días: fecha ISO y concentración real nullable |
| `/api/charts/predictions` | `station`: código | 366 fechas de 2024; observado/Ridge/persistencia: reales cuando hay evaluación, campos ausentes en caso contrario; episodios: inicio/fin/pico como fechas ISO |
| `/api/charts/metrics` | Ninguno | Regresión por tramo/modelo, n entero y MAE real; comienzos: recuentos para Madrid, lista vacía para Barcelona |
| `/api/charts/errors` | Ninguno | Grupos por estación/mes/nivel, recuentos enteros y métricas reales; sensibilidad: lista vacía en Barcelona |
| `/api/charts/uncertainty` | Ninguno | Configuración y filas por estación/bloque: n entero, estimación e intervalo reales, incluye-cero booleano |

Las estaciones deben pertenecer al territorio; periodos válidos: 2017–2025 para Madrid y 2017–2024 para Barcelona. Región desconocida, estación cruzada y periodo no disponible devuelven HTTP 400. `/api/charts/explanations?territory=barcelona` devuelve 400 con la explicación de disponibilidad.

Flask solo lee CSV/JSON, sin cargar modelos ni scikit-learn. Cinco pruebas de API verifican aislamiento territorial, calendario bisiesto, nulos/cero, diagnósticos propios y peticiones inválidas. Se contrastan además las respuestas con los archivos reales sin recalcular predicciones. PCA/LDA y los casos de defensa mantienen su ámbito de Madrid.
