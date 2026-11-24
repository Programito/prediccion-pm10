# Revisión de requisitos y evidencias del TFM

Revisión realizada el 19 de noviembre de 2026 sobre los archivos locales del proyecto.

La referencia es el documento entregado por el alumno, `enunciado_TFM_MDATA2-.pdf`, conservado en su carpeta Downloads. Las páginas indicadas corresponden a las páginas físicas del PDF, de 1 a 11. Los requisitos se han parafraseado para convertirlos en acciones verificables. La revisión comprende código, documentación, resultados y la [reconstrucción comprobada en un entorno aislado](33_verificacion_entrega.md) a partir de las entradas conservadas. La restauración mediante nuevas descargas queda pendiente.

## Alcance de la entrega

Las páginas 1 y 2 exigen dos proyectos. El proyecto predictivo representa el 60 % de la nota. El otro 40 % corresponde a una elección entre resumen multimodal de investigación y asistente RAG multiformato. Cada proyecto necesita su propio repositorio de GitHub y su enlace debe enviarse por el campus.

El trabajo de esta carpeta corresponde al proyecto predictivo. La elección y ejecución del segundo proyecto siguen pendientes de acreditar en los archivos revisados.

## Proyecto predictivo

**Cubierto** significa que existe evidencia local del requisito. **Parcial** indica que la evidencia necesita interpretación, integración o verificación adicional. **Pendiente** indica que falta un entregable verificable.

| Requisito del enunciado | Página | Estado | Evidencia local y acción pendiente |
| --- | --- | --- | --- |
| Definir un objetivo de negocio y las preguntas que responderá el modelo | 4 y 6 | Cubierto como caso propuesto | [Caso de uso y decisión](30_metricas_negocio_pm10.md) concreta una organización de actividades exteriores, revisión anticipada ante avisos y valoración por costes hipotéticos de errores. La validación con una organización real queda como trabajo futuro. |
| Elegir un problema de regresión, clasificación o series temporales y justificarlo | 4 y 6 | Cubierto | [Enfoques](11_enfoques_y_evaluacion.md) y [resultados](26_capitulo_resultados_tfm.md) describen predicción diaria numérica y clasificación de días elevados. El enunciado permite elegir una de esas categorías. |
| Documentar los datos y facilitar los datos utilizados o enlaces públicos | 5 y 6 | Cubierto | [Fuentes y formatos](15_fuentes_endpoints_formatos.md), [inventario](reference/source_endpoints.md) y manifiestos en `data/raw/`. Verificar los enlaces relativos y las instrucciones de descarga al preparar el repositorio de entrega. |
| Explorar, limpiar y preparar las variables | 4 y 6 | Cubierto | [Trazabilidad de mapeadores](16_trazabilidad_mappers_tablas.md), [auditoría de huecos y picos](17_auditoria_huecos_y_picos_pm10.md), módulos en `tfm_data/mappers/` y pruebas en `tests/`. |
| Entrenar, validar y comparar modelos y justificar las elecciones | 4 y 6 | Cubierto | [Validación de regresión](13_primeros_modelos_regresion.md), [clasificación](18_clasificacion_pm10_elevado.md), [comparación meteorológica](24_comparacion_logistica_meteorologia.md) y pruebas finales de [2024](21_resultados_prueba_final_pm10.md) y [2025](25_prueba_meteorologia_2025.md). |
| Elegir métricas técnicas apropiadas y explicar los resultados | 6 | Cubierto | [Capítulo de resultados](26_capitulo_resultados_tfm.md) y CSV de `output/` presentan MAE, RMSE, sesgo, precisión, recall y recuentos de avisos. Se distinguen falsas alarmas totales y falsas alarmas en posibles comienzos. |
| Aplicar explicabilidad e interpretar las variables que más influyen | 4 y 6 | Cubierto | [Explicabilidad](31_explicabilidad_pm10.md) interpreta coeficientes, importancias y límites. React muestra gráficos globales y la descomposición exacta de las 1.013 predicciones de Ridge de 2024. Se contrastan las versiones guardadas y las huellas. |
| Traducir resultados técnicos a métricas de negocio e impacto real o potencial | 4 a 6 | Cubierto mediante escenarios | [Métricas de negocio](30_metricas_negocio_pm10.md) y resultados en `output/pm10_business_2025/` incluyen tres escenarios de coste, diferencias frente a persistencia y puntos de equilibrio. Los costes son supuestos y el análisis conserva los modelos y cortes de 2025. |
| Describir la propuesta conceptual de producción | 4 a 6 | Cubierto como diseño | La [propuesta de producción](32_propuesta_produccion_pm10.md) define batch diario y API de consulta, disponibilidad y corte temporal, ausencias y reintentos, monitorización, drift, revisión trimestral, validación de candidatos y recuperación de versiones. El piloto operativo queda como trabajo futuro. |
| Incluir resultados y visualizaciones | 1, 2 y 5 | Cubierto | [README integrado](../README.md) con cuatro figuras exportadas del notebook, [demo](27_demo_pm10.md), [explorador React](28_explorador_react.md) y resultados en `output/`. |
| Incluir código que reproduzca todo el flujo | 1 y 5 | Comprobado desde entradas conservadas; distribución preparada | La [verificación aislada](33_verificacion_entrega.md) reconstruye las etapas y reproduce resultados. La [guía del evaluador](34_guia_evaluador.md) describe paquetes, manifiestos, huellas y restauración. Se comprobaron descargas de tres originales y se conserva la instantánea completa. Queda verificar los enlaces de publicación. |
| Elaborar un Markdown principal con narrativa coherente | 1, 3, 5 y 6 | Cubierto como versión integrada | El [README](../README.md) reúne objetivo, fuentes, preparación, decisiones, dificultades, resultados, figuras, explicabilidad, costes relativos, producción conceptual y conclusiones. Queda la revisión del autor antes de publicar. |
| Incluir un esquema del sistema completo | 3 y 5 | Cubierto | [Flujo de datos](../explorer/src/lineage.mmd), diagramas de tablas tratadas y vista de Mermaid en React. Revisar que la explicación final recorra preparación, modelado, evaluación y comunicación. |
| Explicar dificultades, conclusiones y mejoras futuras | 3 y 6 | Cubierto | El [README](../README.md) integra cobertura, cambio de fuente en 2025, disponibilidad temporal, límites de las mejoras y prioridades de una versión futura. Enlaza las auditorías y el [capítulo de resultados](26_capitulo_resultados_tfm.md). |
| Publicar el proyecto en GitHub y enviar su enlace | 1 y 5 | Pendiente de verificar | La carpeta revisada carece de `.git/` y no acredita un repositorio remoto ni el envío por campus. Preparar los archivos de entrega y comprobar la publicación cuando corresponda. |

## Prioridades para terminar el proyecto predictivo

1. Revisar como autor el [README integrado](../README.md), sus conclusiones y el caso de uso propuesto.
2. Revisar los paquetes y la [guía del evaluador](34_guia_evaluador.md) y comprobar sus ubicaciones de publicación. La reconstrucción y el orden de ejecución ya están [verificados](33_verificacion_entrega.md).
3. Preparar los archivos que se publicarán, comprobar las referencias y publicar el repositorio cuando corresponda.
4. Recorrer el [notebook ejecutado](../notebooks/01_pm10_end_to_end.ipynb) y seleccionar los casos de la defensa. Sus instrucciones y alcance figuran en la [guía del notebook](../notebooks/README.md).
5. Completar el segundo proyecto elegido y su repositorio y comprobar los enlaces que se enviarán al campus.

En esta revisión se detectó una incidencia del entorno local. `.venv/pyvenv.cfg` apuntaba a una versión anterior del Python integrado en Codex que ya no estaba disponible. Se reparó el 19 de noviembre de 2026 y se verificó ejecutando la exportación de explicaciones y las pruebas del proyecto.

## Segundo proyecto

La página 1 establece que debe elegirse una de las dos alternativas. El PDF titula la alternativa RAG como «Proyecto 3» en la página 10, aunque constituye una de las opciones del segundo proyecto a entregar.

| Alternativa | Requisitos que habrá que acreditar | Referencia |
| --- | --- | --- |
| Resumen multimodal | Extracción de texto escrito mediante scraping o API y transcripción de audio o vídeo, limpieza y unificación, resumen e insights, dos visualizaciones, ejemplo de ejecución, Markdown y esquema del sistema. | Páginas 7 a 9 |
| Asistente RAG multiformato | Ingesta de cinco formatos distintos, embeddings y almacenamiento vectorial, asistente con LLM y recuperación, versión básica y mejorada, evaluación del impacto de la mejora, ejemplo de ejecución, Markdown y esquema del sistema. | Páginas 10 y 11 |

## Distinción entre requisitos y decisiones del proyecto

El enunciado acepta código en scripts o notebooks. El notebook es una propuesta didáctica para este trabajo. Para el proyecto predictivo, la producción se describe conceptualmente. React, Docker, PostgreSQL, un alojamiento público, un PDF de memoria y un algoritmo concreto de series temporales son decisiones o posibles ampliaciones que deben justificarse por su aportación al proyecto.

El complemento sanitario ya está recogido en el capítulo de resultados. Su función es ampliar el análisis exploratorio y sus limitaciones deben acompañar las comparaciones por territorio y año.

La rúbrica asigna por proyecto 3 puntos a investigación y justificación técnica, 2,5 a resultados y visualizaciones, 2 a código y estructura, 1,5 a innovación y 1 a documentación. Estos pesos orientan las prioridades. El estado de esta lista acredita evidencias locales y tareas pendientes, y la calificación corresponde a la evaluación del curso.
