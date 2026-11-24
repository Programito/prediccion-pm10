# Verificación de la entrega en un entorno aislado

La comprobación del 19 de noviembre de 2026 reconstruyó el proyecto en una copia independiente con Python 3.12.14 y paquetes instalados desde los requisitos del repositorio. El entorno se creó sin heredar los paquetes del Python base. El frontend se instaló y compiló en otra carpeta sin dependencias previas.

## Alcance y resultado

La entrada de datos fue una copia de los originales conservados en data/raw/, las referencias territoriales y el extracto compacto de GFS con sus manifiestos. El pipeline de inventario validó 40 originales registrados y 22 tablas principales. Los Parquet de la EEA se verificaron al ejecutar la prueba de 2025.

El extracto meteorológico contiene las celdas y campos elegidos para el modelo. Su adquisición inicial procesó los GRIB2 en memoria y transfirió aproximadamente 5,52 GB. Esta comprobación reutilizó ese extracto. La nueva descarga desde todos los proveedores sigue pendiente de una prueba específica de disponibilidad y restauración.

| Comprobación | Resultado |
| --- | --- |
| Instalación Python desde requisitos y pip check | Dependencias compatibles en el entorno aislado. |
| Pruebas del proyecto | 52 pruebas iniciales y 56 tras incorporar las cuatro comprobaciones del restaurador. |
| Preparación de sanidad, demografía y aire | Ejecutada desde los originales conservados. |
| Auditorías, selección de estaciones y tabla predictiva | Ejecutadas en la copia. |
| Ajuste de Ridge, Random Forest y las logísticas | Ejecutado de nuevo. |
| Artefactos guardados | Los cuatro archivos joblib coinciden byte a byte con los registrados. |
| Pruebas finales de 2024 y 2025 | Ejecutadas con los protocolos y artefactos registrados. |
| Comparación de tablas y métricas | 13 archivos coinciden con tolerancia numérica de 10⁻⁸. |
| Notebook | Las 11 celdas iniciales y las 12 de la versión ampliada con incertidumbre se ejecutan en el entorno aislado. |
| Frontend | Instalación congelada con pnpm 11.2.2 y compilación TypeScript correctas. |
| Flask con datos reconstruidos | Catálogo, tablas tratadas, explicación, documentación y frontend comprobados. |
| Docker | Imagen construida sin caché y comprobación HTTP del frontend y cinco vistas de API en el puerto 8067. |

Los cuatro archivos joblib contienen Ridge, Random Forest, la logística inicial y el conjunto de dos logísticas de la comparación meteorológica. Los nuevos artefactos se conservaron aparte para comparar sus huellas. La evaluación final volvió a cargar las copias registradas, que resultaron idénticas a las regeneradas.

El [informe estructurado](../output/delivery_verification/report.json) conserva archivos comparados, recuentos, huellas y alcance. El [registro de etapas](../output/delivery_verification/pipeline_stages.json) incluye los intentos de ejecución. Su estado final es correcto para las 26 etapas.

## Orden comprobado de reconstrucción

Los comandos siguientes deben ejecutarse desde la raíz de una copia del proyecto, con el entorno y las entradas anteriores disponibles. Generan o actualizan las salidas de esa copia.

Primero se preparan los datos sanitarios y demográficos y se revisa la red ambiental

~~~powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_health
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_demographics
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_air
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_air_coverage
.\.venv\Scripts\python.exe -m tfm_data.evaluation.station_review
.\.venv\Scripts\python.exe -m tfm_data.evaluation.provincial_prototype
.\.venv\Scripts\python.exe -m tfm_data.evaluation.historical_feasibility
.\.venv\Scripts\python.exe -m tfm_data.evaluation.initial_health_comparison
~~~

Después se seleccionan las series diarias y se generan las variables y experimentos de validación

~~~powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.pollution_sample
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_pm10_forecast
.\.venv\Scripts\python.exe -m tfm_data.pipelines.train_pm10_regression
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_pm10_quality
.\.venv\Scripts\python.exe -m tfm_data.pipelines.train_pm10_classification
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_pm10_classification_thresholds
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_pm10_weekday
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_pm10_weather
.\.venv\Scripts\python.exe -m tfm_data.pipelines.compare_pm10_weather
~~~

Finalmente se reproducen las evaluaciones y salidas de consulta

~~~powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_final
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_pm10_errors
.\.venv\Scripts\python.exe -m tfm_data.pipelines.bootstrap_pm10_errors
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_weather_2025
.\.venv\Scripts\python.exe -m tfm_data.pipelines.explain_pm10_models
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_business
.\.venv\Scripts\python.exe -m tfm_data.pipelines.document_sources
.\.venv\Scripts\python.exe scripts/build_demo_data.py
~~~

El guion inicial de esta comprobación ejecutó la auditoría de PM10 antes del entrenamiento e inicialmente omitió la revisión de puntos. Ambos intentos evidenciaron dependencias que se resolvieron al ordenar las etapas. El orden anterior incluye esas correcciones. La auditoría lee las predicciones de validación y el inventario exige la tabla de revisión de puntos.

Los protocolos identifican los artefactos y las tablas por sus huellas. Una diferencia de entorno o serialización que altere un artefacto exige investigar su equivalencia con la versión registrada y conservar la trazabilidad del experimento.

## Archivos que se contrastaron

La comparación incluyó las tasas sanitarias provinciales, la demografía, las 8.766 filas diarias y las 8.148 filas supervisadas completas. También se contrastaron las métricas sanitarias, las validaciones de regresión y clasificación, las métricas finales de 2024 y 2025 y los nueve escenarios de coste.

Se compararon además las predicciones o probabilidades de los modelos regenerados Ridge, Random Forest y logística inicial con los guardados en las mismas filas de validación. La coincidencia de huellas de los cuatro artefactos completa la verificación de las versiones ajustadas.

## Preparación de los archivos de entrega

La ampliación territorial de Barcelona se verifica por separado en `incremental_barcelona` del informe. Reutiliza los ZIP nacionales conservados, añade tablas y modelos propios y contrasta las huellas de los artefactos protegidos de Madrid. El alcance y las diferencias de cobertura se describen en [la comparación territorial](38_experimentos_madrid_barcelona.md).

Dos originales conservados superan los 100 MB y el conjunto de data/raw/ ocupa aproximadamente 547 MB. La [guía del evaluador](34_guia_evaluador.md) describe el paquete del proyecto, el paquete de fuentes y el restaurador que usa los manifiestos y verifica huellas. El extracto meteorológico compacto forma parte del paquete del proyecto.

La obtención desde los proveedores se comprobó para tres archivos de INE, MITECO y EEA, y el resto se conserva en la instantánea. La publicación debe proporcionar una ubicación accesible de los paquetes y comprobar sus enlaces desde la cuenta del evaluador. Las instrucciones de ejecución local, el notebook y Docker están enlazados desde el [README principal](../README.md).

Los dos paquetes se extrajeron en otra carpeta y los 43 originales restaurados superaron la comprobación de tamaño y SHA-256. Las huellas de los ZIP están en checksums.json, junto a los paquetes de output/delivery/.

La auditoría descriptiva de errores y el bootstrap se incorporaron posteriormente al recorrido. Reutilizan las predicciones congeladas de 2024. Sus agregados se contrastaron con las métricas originales y los intervalos con las réplicas guardadas. La suite actual reúne 106 pruebas, incluidas ocho de la ampliación territorial y su auditoría, cinco de estadísticas descriptivas, cuatro de diagramas de caja, cinco de la comparación de ventanas, seis de la permutación agrupada, cuatro de los casos de estudio y cinco de PCA/LDA. Los filtros de errores e intervalos se comprobaron en el navegador, el frontend pasó la compilación TypeScript y el notebook ampliado se ejecutó con el entorno aislado.

## Casos de estudio

La pantalla **Casos** prepara tres ejemplos y una falsa alarma de contraste con evidencias CSV. El [guion de defensa](43_casos_de_estudio_defensa.md) explica la selección reproducible, los cortes originales, el contexto retrospectivo y las limitaciones. Los modelos y las predicciones originales se conservan. El ensayo con el autor sigue pendiente.

## Análisis PCA y LDA

Disponible en **Experimentos → PCA y LDA**. El [protocolo exploratorio](44_pca_lda_pm10.md) conserva ajuste solo con entrenamiento y validación de 2023, gráficos, comparación y descargas. No se reevalúan 2024/2025 ni se sustituyen modelos finales.

## Gráficos territoriales

El [selector de territorio](45_graficos_territoriales.md) conecta mapa, observaciones, predicciones, regresión, errores e intervalos con las salidas guardadas de Madrid o Barcelona provincia. Se añadieron y ejecutaron cinco pruebas de API en la imagen Docker del explorador; TypeScript y la compilación también se verificaron en Docker. No se reentrenaron modelos ni se recalcularon pruebas finales.
