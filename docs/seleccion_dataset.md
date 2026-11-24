# Selección inicial del dataset

Revisión: 15 de noviembre de 2026. Los recuentos proceden de los CSV descargados mediante la API pública de Kaggle. No se han entrenado modelos. La recomendación es provisional hasta completar una exploración guiada.

## Candidato recomendado: Vending Machine Sales

Fuente: https://www.kaggle.com/datasets/awesomeasingh/vending-machine-sales

Licencia declarada por Kaggle: CC0. Copia original: `data/candidates/vending-machine-sales/vending_machine_sales.csv`. La procedencia y las huellas SHA-256 figuran en `source.json`, junto a los datos.

| Comprobación | Resultado |
| --- | --- |
| Filas y columnas | 9.617 líneas, 18 columnas |
| Transacciones distintas | 9.116 |
| Periodo de venta | 1 enero a 31 diciembre de 2022 |
| Días con alguna fila en el conjunto | 362 de 365 |
| Máquinas y ubicaciones | 5 máquinas, 4 ubicaciones |
| Productos distintos con nombre | 184 |
| Ausencias | Product: 6; Category: 267; MPrice: 3 |
| Duplicados exactos | 0 |
| Estado | 9.614 Processed y 3 Unlinked |
| Cantidad por precio frente a LineTotal | Coincide en todas las filas, con tolerancia 0,01 |

El autor describe ubicaciones de oficina, fabricación, biblioteca y centro comercial. La primera venta registrada de la biblioteca es del 14 de marzo: no se debe convertir automáticamente todo enero y febrero en ventas cero.

### Enfoque propuesto

Predecir las unidades vendidas por máquina durante los próximos siete días. Empezar con ventas diarias agregadas por máquina y evaluate orígenes de predicción semanales sin solapamiento. Comparar una referencia basada en los siete días anteriores con alternativas sencillas y, si hay señal suficiente, un modelo que comparta información entre máquinas.

Separar entrenamiento, validación y prueba por fecha. Todas las variables históricas deben construirse solo con información disponible antes del momento de predicción. La ingeniería de variables, elección de modelos y métricas se desarrollarán junto con el alumno.

### Límites que condicionan el proyecto

- Solo hay un año: no permite demostrar que se aprende una estacionalidad anual repetida.
- Las 9.617 líneas no son 9.617 ejemplos temporales independientes. Al agregar por máquina y día hay muchos menos ejemplos, relacionados entre sí.
- Las máquinas menos activas rondan 2-3 unidades por día al dividir por los 365 días. La predicción por producto y máquina sería muy dispersa como punto de partida.
- Un día sin registros puede representar cierre, ausencia de ventas, fallo de registro o falta de producto. Revisar calendarios y huecos antes de imputar.
- No hay columnas explícitas de existencias, reposiciones, costes de compra o averías. No presentar ventas como demanda no censurada ni deducir un optimizador real de reposición.
- El impacto económico se puede evaluate mediante escenarios con supuestos explícitos y análisis de sensibilidad. No constituye ahorro observado.
- Las filas representan líneas de venta. `TransTotal` puede repetirse entre líneas de una misma transacción: usar el importe por línea al agregar, después de validar su significado.
- `Prcd Date` es posterior a la venta en algunos registros. No utilizarla como predictor sin justificar su disponibilidad en el momento de la previsión.
- Conservar las filas originales. Decidir y documentar el tratamiento de los estados Unlinked y los valores ausentes durante la limpieza.

## Alternativa: Coffee Sales

Fuente: https://www.kaggle.com/datasets/ihelon/coffee-sales

Licencia declarada por Kaggle: CC0. Hay dos archivos cuya relación debe comprobarse en la documentación antes de combinarlos.

| Archivo | Filas | Cobertura | Bebidas distintas |
| --- | --- | --- | --- |
| index_1.csv | 3.636 | 1 marzo 2024 a 23 marzo 2025 | 8 |
| index_2.csv | 262 | 8 febrero a 23 marzo 2025 | 30 |

`index_1.csv` contiene 381 días con registros dentro de un intervalo de 388 días, 89 identificadores de tarjeta ausentes y ningún duplicado exacto. `index_2.csv` contiene dos filas duplicadas exactas; no eliminarlas sin analizar su significado. Los archivos difieren en columnas, nombres y variedad de bebidas. No concatenarlos automáticamente.

Es una alternativa más pequeña, útil para practicar, pero el candidato de snacks y bebidas aporta varias máquinas y ubicaciones para una comparación operativa más rica. La ventaja debe confirmarse mediante evaluación temporal: no se presupone que un modelo complejo superará a la referencia.

## Decisión propuesta

Usar Vending Machine Sales para la primera exploración guiada. Confirmar la elección tras revisar las series, los días sin datos, los cambios de actividad y la estabilidad de los importes. Mantener el proyecto RAG independiente de esta decisión.
