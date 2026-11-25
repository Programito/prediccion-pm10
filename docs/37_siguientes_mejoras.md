# Trabajo pendiente y presentación del proyecto

Las siguientes tareas se conservan para una fase posterior. El explorador ya dispone de Inicio, mapa, comparación de Madrid y Barcelona, auditoría de exclusiones y comparación de ventanas en validación de 2023. La variante sin media de 14 días recupera casos a cambio de un pequeño aumento del MAE en filas comunes. Los modelos actuales se conservan; cualquier promoción requiere fijar la variante y comprobarla en un periodo temporal independiente.

## Recorrer juntos el notebook

Estado pendiente de una sesión guiada con el autor.

Recorrer el notebook por bloques y pedir al autor que explique qué representa una fila, cómo se construyen retardos y ventanas, qué información está disponible antes del objetivo y por qué se utiliza persistencia como referencia. Revisar MAE, sesgo, días elevados y el significado de que el intervalo bootstrap incluya cero.

La tarea se considerará completada cuando el autor pueda explicar las decisiones con sus palabras y reproducir una predicción y su evaluación. El recorrido y las preguntas de práctica están en el [notebook](../notebooks/01_pm10_end_to_end.ipynb).

## Importancia por permutación en validación

Estado implementado en los Ridge originales de Madrid y Barcelona, sobre sus validaciones completas de 2023. El [diagnóstico agrupado](42_importancia_agrupada_pm10.md) documenta los desplazamientos circulares, las rotaciones de estación, la sensibilidad conjunta y sus límites. Los resultados se consultan en React, en Experimentos → Importancia agrupada.

Se evaluó cuánto aumenta el MAE al alterar PM10 reciente y retardos, medias y variabilidad, calendario y estación. Los grupos se fijaron antes del cálculo y sus columnas se desplazan juntas. Se añadió una sensibilidad con todo el historial para estudiar la dependencia entre los dos primeros grupos.

Se conservó el orden circular por estación y se registraron semillas, repeticiones y planes. Las combinaciones alteradas pueden ser poco realistas y no representan predicciones operativas. Los rangos entre alteraciones no son intervalos de confianza. React incluye referencias de coeficientes de Ridge e impureza del bosque con sus diferencias de interpretación.

Se dispone de código reproducible, resultados, visualización y limitaciones. Los modelos congelados y las pruebas de 2024 y 2025 se conservan como resultados ya conocidos.

## Presentar los resultados

Estado: materiales y selección implementados en la pantalla **Casos**. El [guion reproducible](43_casos_de_estudio.md) documenta selección, resultados, extractos descargables y límites.

Preparar tres casos verificables en la aplicación

- Una predicción habitual: Tres Olivos, 10 de abril de 2024, seleccionada por concentración central entre días no elevados, sin usar el error.
- El pico de Tres Olivos del 31 de octubre de 2024, para explicar la infraestimación y las aportaciones de Ridge.
- El comienzo de Tres Olivos del 5 de agosto de 2025, detectado por la logística con meteorología.

Relacionar cada caso con la cobertura, el objetivo, la referencia y el coste de errores. Incorporar la falsa alarma del 22 de febrero de 2025 al explicar el intercambio entre anticipación y avisos erróneos.

La tarea se considerará completada con un guion breve, las vistas preparadas y un ensayo en el que el autor pueda justificar resultados y limitaciones.

## Mejoras del explorador

El análisis exploratorio [PCA y LDA](44_pca_lda_pm10.md) ya está implementado en Experimentos. Ajusta solo con entrenamiento y consulta validación de 2023. PCA conserva el 90 % de la varianza con siete componentes; las dos variantes LDA no mejoran a sus logísticas en esta comparación. Los modelos y resultados finales se conservan.

Las vistas de gráficos comparten estación y fecha entre observaciones, predicciones y explicación. Los análisis agregados conservan su ámbito temporal de 2024. Casos conserva el ejemplo seleccionado al salir y volver, con acceso a las explicaciones de 2024 y observaciones de 2025.

La pantalla de Inicio ya está implementada con resultados leídos de las salidas existentes, periodos, limitaciones y accesos al análisis. También están disponibles el mapa y los casos de estudio, con consulta diaria de las probabilidades y decisiones de 2025. Quedan propuestas para priorizar más adelante una vista sanitaria específica, ayudas adicionales junto a las métricas y la conservación de filtros en la URL.
