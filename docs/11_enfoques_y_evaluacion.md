# Enfoques predictivos y protocolo inicial

Fecha del protocolo: 16 de noviembre de 2026. Se fija antes de comparar algoritmos de contaminación.

## Problema principal

Predecir el PM10 medio del día siguiente en Tres Olivos, Majadahonda y San Martín de Valdeiglesias, tres estaciones de fondo de Madrid con áreas urbana, suburbana y rural. El análisis sanitario provincial y anual se conserva como complemento exploratorio.

Un usuario posible es una organización que programa actividades exteriores y necesita anticipar días de concentración inusualmente alta para revisar su programación. La previsión será apoyo informativo: no sustituye avisos oficiales ni produce recomendaciones clínicas. Los costes de falsas alertas o de episodios no detectados se podrán analizar mediante escenarios declarados, sin presentarlos como ahorros observados.

## Tres enfoques relacionados

| Enfoque | Objetivo | Referencias y algoritmos candidatos | Estado |
| --- | --- | --- | --- |
| Regresión | PM10 medio de mañana en µg/m3. | Persistencia, media móvil, referencia semanal; después Ridge, Random Forest y Gradient Boosting. | Preparación de tabla y referencias iniciales. |
| Clasificación | Mañana supera un umbral de PM10 elevado respecto al historial de entrenamiento. | Clase mayoritaria y frecuencia histórica; después regresión logística, árbol y Random Forest. | Etiqueta y umbral definidos; pendiente entrenar y evaluate clasificadores. |
| Series temporales | El mismo PM10 futuro, modelando dependencia temporal. | Persistencia y referencia semanal; después modelo autorregresivo o SARIMA, con estacionalidad semanal si está justificada. | Referencias compartidas con regresión; modelos clásicos pendientes. |

Regresión y series temporales se solapan. Un modelo de árboles con retardos también es un modelo para previsión temporal. Los enfoques no son tres proyectos independientes ni requieren entrenar todos los algoritmos. Se empezará con pocas alternativas y se ampliará si los resultados y el aprendizaje lo justifican. Las redes profundas quedan fuera del alcance inicial.

## Clasificación: definición antes de observar la prueba

El umbral inicial es el percentil 90 de las concentraciones objetivo válidas del periodo de entrenamiento, agrupando las tres estaciones. Se fija una sola vez y se conserva en validación y prueba. La clase positiva significa estrictamente `PM10 > umbral`. La prevalencia puede ser distinta por estación.

Es una definición relativa de concentración elevada, no un límite legal, una recomendación médica ni una categoría oficial de calidad del aire. Se documenta el valor resultante y se comprueba el número de positivos en entrenamiento y validación antes de elegir métricas y clasificadores. Un objetivo ausente permanece sin etiqueta, no se transforma en clase negativa.

Se usarán precisión, recall, F1, matriz de confusión y, cuando existan probabilidades, average precision/curva precisión-recall. Se indicará la definición exacta de cualquier área calculada. Accuracy no será la métrica principal si hay desbalance. Las decisiones de umbral de probabilidad y balanceo se harán con entrenamiento/validación, nunca mirando la prueba final.

## Separación temporal

La partición depende de la **fecha del día que se predice**, no de la fecha de la última observación:

- Entrenamiento: objetivos de 2017 a 2022.
- Validación: objetivos de 2023.
- Prueba final: objetivos de 2024, que se reservaron durante esta etapa. [Protocolo final](20_protocolo_prueba_final_pm10.md) · [Resultados de 2024](21_resultados_prueba_final_pm10.md)

Las tres estaciones comparten las mismas fronteras temporales. No se mezclan días al azar ni se supone independencia entre estaciones o entre días próximos. Escalado, imputación, selección de variables y ajuste de modelos aprenderán solo con entrenamiento. Cualquier búsqueda posterior se limita a ese periodo mediante divisiones temporales, con validación para la elección inicial y una evaluación final sin reajustar según su resultado.

La selección de estaciones ya utilizó la cobertura del periodo completo y las fuentes son versiones históricas revisadas. El experimento será retrospectivo; una validación operativa requeriría versiones y disponibilidad real de cada dato.

## Emisión y disponibilidad de variables

Cada fila se construye al finalizar el día t, con objetivo para t+1. Se registra como emisión simulada el inicio UTC del día objetivo. Esto supone, solo para la comparación retrospectiva, que el resumen del día t estuviera disponible inmediatamente. Los archivos oficiales anuales utilizados no demuestran esa disponibilidad en tiempo real.

Variables iniciales:

- PM10 de t, t-1, t-2 y t-6. Este último corresponde al mismo día semanal que el objetivo t+1, una semana antes.
- Media de los últimos 3, 7 y 14 días, incluyendo t; se exige el número completo de días válidos, sin rellenar ausencias.
- Desviación típica de los últimos 7 días, exigiendo siete valores.
- Día semanal y mes del objetivo, con codificación cíclica; son conocidos al emitir.
- Identificación de la estación como variable categórica, cuyo tratamiento se ajustará con entrenamiento.

No se incluyen la concentración del día objetivo, otras estaciones de ese día, meteorología observada del futuro ni medias móviles centradas. Si se incorpora meteorología, deberá usarse información pasada o previsiones archivadas que estuvieran disponibles al emitir.

El calentamiento inicial y las ausencias se registran. No se imputa el objetivo para evaluate. El primer conjunto común para comparar modelos solo utiliza filas con objetivo y variables numéricas completos; se informa de cuántas filas se pierden. Una variante con imputación de predictores podría evaluarse más adelante con un proceso ajustado solo con entrenamiento.

## Referencias de regresión

1. Persistencia: mañana será como t.
2. Media móvil: mañana será la media de los siete días hasta t.
3. Referencia semanal: mañana será como t-6.

Se comparan con el mismo conjunto de filas en validación, utilizando MAE, RMSE y sesgo medio (predicción menos observación), tanto globalmente como por estación. Estas referencias también permiten valorar los modelos temporales clásicos. Todavía no se comparan métricas de 2024 ni se elige un modelo final.

## Qué permitirá decidir

Primero comprobaremos que la tabla no tiene fugas temporales y que los objetivos y referencias se interpretan bien. Después entrenaremos un modelo lineal regularizado y un modelo de árboles. Solo si mejoran de forma útil y estable las referencias se justificará aumentar la complejidad. Se reportarán también fallos, incertidumbre y resultados por estación y por episodios de concentración elevada.
