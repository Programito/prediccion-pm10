# Propuesta conceptual de producción de PM10

## Objetivo y alcance

El sistema propuesto apoyaría la planificación de actividades exteriores mediante una previsión diaria de PM10 y una señal de concentración elevada para cada una de las tres estaciones del estudio. La organización revisaría la programación cuando el aviso y sus costes operativos lo justificasen. [Caso de uso y relación de costes](30_metricas_negocio_pm10.md)

El diseño comprende adquisición, controles de calidad, preparación de variables, inferencia, publicación, evaluación posterior y actualización de modelos. Las decisiones de arquitectura y horario que siguen son propuestas para un piloto. La evidencia actual procede de las pruebas retrospectivas y las interfaces locales. [Resultados y limitaciones](26_capitulo_resultados_tfm.md)

## Hora de emisión y disponibilidad

La evaluación actual usa el PM10 diario completo de D−1 para predecir la media del día D. Su emisión simulada coincide con las 00:00 UTC de D. Los archivos históricos anuales de MITECO y las horas verificadas de la EEA permiten reconstruir esa información a posteriori. Su presencia en esos archivos acredita su disponibilidad histórica, pero la hora real de publicación necesita medirse.

El GFS utilizado en clasificación corresponde al ciclo de las 12:00 UTC de D−1. El ciclo identifica cuándo se inicializó la previsión. Para usarlo operativamente habría que registrar también cuándo se publicó el fichero y cuándo lo recibió el sistema.

Para anticipar el día D antes de que comience se propone estudiar una emisión a las **23:00 UTC de D−1**, con corte de entrada a las **22:00 UTC**. Es un horario de diseño elegido para dejar una hora de procesamiento y revisión. Se revisaría con la organización, considerando que la jornada UTC y la jornada local pueden tener límites distintos.

Ese horario requiere modificar las variables de PM10. A las 22:00 UTC todavía no se conoce la media completa de D−1. El nuevo conjunto podría usar el último día completo disponible, las últimas horas recibidas, su cobertura y un resumen parcial con hora de corte explícita. Los retardos y las ventanas se definirían de nuevo con esa disponibilidad. El modelo candidato y su referencia necesitarían entrenamiento y evaluación propios.

| Etapa | Horario o condición | Comprobación necesaria |
| --- | --- | --- |
| Reconstrucción retrospectiva actual | Media completa de D−1 y emisión simulada a las 00:00 UTC de D | Conservar las pruebas y sus hipótesis como evidencia del TFM. |
| Observación de disponibilidad | Registrar cada llegada durante un piloto y abarcar cambios de día, incidencias y periodos de mayor demora | Medir latencia, revisiones, cobertura y compatibilidad de una fuente operativa con las estaciones del estudio. |
| Candidato de anticipación | Corte a las 22:00 UTC y emisión a las 23:00 UTC de D−1 | Construir variables disponibles a ese corte y evaluar una política fijada previamente. |
| Publicación del piloto | Aceptación técnica y de utilidad por la organización | Comprobar la latencia de extremo a extremo y evaluar con observaciones futuras. |

La hora de cada fuente se guardaría junto a la hora de recepción. Para reconstruir un entrenamiento operativo se necesitarían las versiones que realmente estaban disponibles en cada corte. Si solo se dispone de históricos revisados, la evaluación se identificaría como retrospectiva y su supuesto de disponibilidad seguiría visible.

## Ejecución diaria y componentes

La inferencia se ejecutaría mediante un proceso batch diario. El horizonte y las entradas dependen del día objetivo, por lo que un cálculo programado permite controlar el corte de datos y conservar una evidencia completa de cada emisión. Una API serviría los resultados publicados y React permitiría consultarlos por estación y fecha.

```text
Fuentes ambientales y previsiones meteorológicas
    → descarga y registro de recepción y procedencia
    → controles de formato, cobertura y validez temporal
    → instantánea de entradas disponibles al corte
    → mapeadores y preparación de variables versionadas
    → modelos y referencias compatibles con esas variables
    → resultados y estado de la emisión
    → API de consulta
    → panel React y revisión de la programación

Observaciones recibidas posteriormente
    → evaluación de las predicciones publicadas
    → monitorización y revisión de modelos
```

El proceso conservaría cada descarga original con su huella y generaría las tablas tratadas con los mapeadores del proyecto. La preparación operativa compartiría la lógica con entrenamiento, incluida la zona horaria y la definición de ventanas. Cada artefacto se cargaría junto a su esquema de variables, escalado, versión y umbral de decisión.

Ridge produciría la previsión numérica y la logística produciría el aviso según la versión y el corte aprobados para ese uso. La referencia de persistencia se recalcularía sobre el mismo conjunto de casos comparables. La incorporación de nuevas estaciones requeriría revisar la codificación categórica y validar el modelo ampliado.

El complemento sanitario se actualizaría al disponer de nuevos datos anuales compatibles y tendría su propio proceso de revisión. Sus indicadores provinciales y anuales sirven al análisis exploratorio del proyecto.

## Datos ausentes, tardíos y reintentos

| Situación | Comportamiento propuesto |
| --- | --- |
| Falta una variable necesaria de PM10 | Marcar la previsión de la estación como no disponible y registrar qué entrada falta. Mostrar el último resultado con su fecha solo como histórico consultable. |
| Falta meteorología | Publicar la versión sin meteorología únicamente si esa política de respaldo se ha validado con las variables y el horario operativos. Registrar el modelo y el motivo del cambio. |
| Fecha, unidad, estación o esquema incompatibles | Detener el procesamiento del conjunto afectado y emitir una incidencia técnica con su procedencia. |
| Entrada recibida después del corte | Conservarla para la próxima ejecución y para evaluación. Si se autoriza una corrección, publicarla con otra revisión y su hora de emisión. |
| Fallo temporal de descarga | Reintentar dentro del plazo disponible, respetando los límites del proveedor. Al vencer el plazo, registrar la emisión incompleta. |
| Fallo al guardar o publicar | Mantener el resultado preparado y reintentar la publicación con el mismo identificador de ejecución. |

Un campo ausente se conserva como ausente. El preprocesamiento aplicaría únicamente una estrategia de imputación que hubiese sido ajustada con entrenamiento y evaluada para ese candidato. La evaluación del TFM exige variables completas y permite informar la proporción de casos descartados.

La clave de una emisión incluiría estación, fecha objetivo, política de emisión, versión del modelo y revisión. Los reintentos usarían el mismo identificador para evitar duplicados. La publicación se completaría de forma atómica después de validar todas las partes de una emisión. Una corrección conservaría la predicción original y permitiría identificar cuál fue visible a cada hora.

## Información que se conservaría

| Registro | Contenido |
| --- | --- |
| Fuente | URL o petición, fichero, huella, estación, periodo observado, ciclo meteorológico, hora de publicación si existe y hora de recepción. |
| Preparación | Identificador de ejecución, corte temporal, versión del mapeador, calidad, cobertura y variables entregadas al modelo. |
| Modelo | Artefacto, huella, dependencias, esquema de entradas, periodo de entrenamiento, evaluación, umbral de PM10 y corte de probabilidad. |
| Predicción | Estación, día objetivo, hora de emisión, versión del modelo, valor o probabilidad, decisión de aviso, referencia, estado y revisión. |
| Observación posterior | Valor objetivo, validez, fuente, recepción y versión del dato usada para evaluar. |
| Incidencia | Etapa, causa, estaciones afectadas, reintentos y resolución. |

Las copias originales y los artefactos podrían conservarse en almacenamiento de archivos. Si aumentan las consultas y las escrituras concurrentes, una base relacional podría guardar el catálogo, las ejecuciones y las predicciones. La elección de ese soporte se decidiría por volumen, concurrencia y mantenimiento.

## Monitorización

Se distinguirían los controles inmediatos, disponibles antes de conocer el objetivo, de las métricas de rendimiento, calculables cuando llegue una observación válida.

| Área | Indicadores | Acción ante una incidencia |
| --- | --- | --- |
| Ejecución y latencia | Duración, llegada de cada fuente, emisiones puntuales, fallos y reintentos | Revisar proveedor y procesamiento, registrar resultados incompletos y avisar al responsable. |
| Calidad y cobertura | Ausencias por variable y estación, horas recibidas, duplicados, unidades, fechas y cobertura de emisiones | Revisar la causa y suspender el cálculo cuando el esquema o las entradas sean incompatibles. |
| Regresión | MAE, RMSE y sesgo por estación, por periodo y en días elevados, frente a la referencia sobre las mismas filas | Examinar errores persistentes, episodios extremos y diferencias por estación. |
| Clasificación | Matriz de confusión, precisión, recall, avisos y falsas alarmas, con desglose de comienzos y continuaciones | Revisar utilidad y carga de avisos con el responsable de la programación. |
| Utilidad | Coste relativo de errores acordado con la organización, revisiones efectuadas y efecto documentado sobre la programación | Actualizar el análisis de utilidad con costes observados y registrar sus supuestos. |
| Drift de entradas | Distribuciones y cuantiles de PM10, viento, precipitación, cobertura y frecuencia de patrones ausentes | Comparar con entrenamiento y periodos estacionales equivalentes y abrir una investigación. |
| Cambio en la relación predictiva | Evolución de errores y sesgo cuando hay suficientes etiquetas nuevas | Investigar calidad, representatividad y necesidad de un candidato actualizado. |

Como propuesta inicial, el panel mostraría resúmenes móviles de 30 y 90 días, con denominadores y cobertura. La estacionalidad y la dependencia entre días y estaciones obligan a interpretar esas ventanas con cautela. Si hay pocos comienzos, se ampliaría el periodo y se mostrarían los recuentos junto a las tasas.

Los límites de alerta se acordarían con datos del piloto y su referencia estacional. Un cambio de distribución motivaría una investigación antes de atribuirlo a una pérdida de rendimiento. Los picos válidos de contaminación formarían parte del seguimiento de errores y de la cobertura de episodios.

## Reentrenamiento y aprobación

Se propone revisar trimestralmente la necesidad de un candidato cuando existan nuevas observaciones válidas. Esa frecuencia es una decisión inicial del piloto. La aparición de cambios de estación, esquema o calidad y el deterioro persistente del rendimiento activarían una revisión adicional.

1. Registrar el motivo del candidato, las variables disponibles y el criterio de aceptación antes de evaluar.
2. Congelar la instantánea de datos con sus versiones de disponibilidad y calidad. Mantener el objetivo ausente fuera del ajuste y la evaluación.
3. Ajustar el preprocesamiento y el modelo usando solo los periodos de entrenamiento. Utilizar cortes temporales para comparar candidatos y elegir hiperparámetros o probabilidades de aviso.
4. Comparar con el modelo vigente y las referencias sobre las mismas fechas. Incluir cobertura, estaciones, episodios y costes de error acordados.
5. Reservar un periodo posterior independiente. Los años 2024 y 2025 ya examinados quedan como resultados históricos del TFM.
6. Registrar la aprobación y ejecutar el candidato en paralelo al vigente durante un periodo acordado. Evaluar latencia, calidad y rendimiento con resultados futuros.
7. Promover la versión aprobada y conservar la anterior para recuperación.

Una variable nueva implicaría una versión nueva del esquema y del artefacto. Su preparación tendría que ser posible al corte tanto en el histórico operativo como en la ejecución diaria. Si falla una versión, la recuperación cargaría el modelo anterior junto a su preprocesamiento y esquema compatible. Si las entradas actuales son incompatibles, la emisión quedaría no disponible hasta resolver la incidencia.

## Organización de la entrega y siguiente comprobación

El explorador actual consulta archivos y resultados guardados, y permite examinar datos, predicciones y explicaciones. La propuesta incorpora como trabajo futuro la captura operativa con latencias, la inferencia programada, la publicación versionada y la monitorización descritas.

El paso previo a una prueba operativa sería medir la disponibilidad de fuentes y construir el conjunto compatible con el corte propuesto. La entrega del TFM puede explicar ese recorrido y sus criterios de aceptación con los resultados retrospectivos disponibles.

La memoria debe conectar esta propuesta con el [protocolo temporal](11_enfoques_y_evaluacion.md), el [análisis de utilidad](30_metricas_negocio_pm10.md) y la [interpretación del modelo](31_explicabilidad_pm10.md).
