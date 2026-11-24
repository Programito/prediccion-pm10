# PCA y LDA en validación de Madrid

Esta ampliación añade un análisis exploratorio, disponible en **Experimentos → Madrid → PCA y LDA**. No sustituye modelos finales ni vuelve a evaluar las pruebas conocidas de 2024 y 2025. Barcelona queda fuera de este análisis.

## Preguntas y protocolo

PCA estudia si las entradas correlacionadas se pueden resumir en pocas dimensiones. No utiliza la etiqueta al ajustar y no busca por sí mismo mejorar una predicción. LDA, análisis discriminante lineal, utiliza etiquetas para encontrar una separación entre días elevados y no elevados y también clasifica. No es el modelo de temas Latent Dirichlet Allocation.

| Técnica | Entrenamiento | Validación | Entradas |
| --- | --- | --- | --- |
| PCA | 2017–2022, 6.096 filas | 2023, 1.039 filas | Las 12 variables numéricas originales de PM10 y calendario |
| LDA sin meteorología | 2021–2022, 2.001 filas comunes | 2023, 1.039 filas comunes | Las 12 variables y estación one-hot, iguales que la logística sin meteorología |
| LDA con meteorología | Misma cohorte | Misma cohorte | Las anteriores más viento y precipitación GFS, iguales que la logística con meteorología |

El PM10 objetivo y su etiqueta nunca son predictores. La definición de elevado conserva el umbral estadístico original: PM10 objetivo **> 27 µg/m³**. La etiqueta se usa para colorear PCA después del ajuste y para entrenar LDA. La selección temporal se hace por fecha objetivo, sin división aleatoria.

Se comprueban fechas de entrenamiento y validación, claves únicas, entradas finitas, objetivos finitos y etiquetas compatibles con el umbral. Se conserva la cohorte completa de cada experimento. No se imputan nulos ni se recortan outliers: los picos siguen presentes. Los agregados, retardos y fechas ya proceden de los mapeadores originales; esta ampliación no los modifica.

## PCA: método y resultado

Se ajusta `StandardScaler` solo con entrenamiento, seguido de PCA con `svd_solver="full"`, todas las componentes y sin whitening. Validación utiliza únicamente `transform`, conservando medias, escalas y ejes aprendidos. PCA excluye identificadores de estación, fechas y objetivo.

Las entradas son `pm10_t`, `pm10_t_menos_1`, `pm10_t_menos_2`, `pm10_t_menos_6`, `media_3_dias`, `media_7_dias`, `media_14_dias`, `desviacion_7_dias`, `semana_sin`, `semana_cos`, `mes_sin` y `mes_cos`. Las ocho primeras resumen concentraciones e historial en µg/m³; las cuatro últimas son codificación cíclica sin unidades.

- PC1 explica el **39,71 %** de la varianza de entrenamiento; PC2, el **11,07 %**.
- Las dos primeras conservan **50,77 %**; hacen falta **7 componentes** para alcanzar el 90 %.
- Entre los mayores pesos absolutos de PC1 figuran media de 7 días (0,428), media de 3 días (0,423), PM10 de t−1 (0,362), media de 14 días (0,359) y desviación de 7 días (0,350).

La última componente tiene una varianza prácticamente nula: `media_3_dias` es la combinación `(pm10_t + pm10_t_menos_1 + pm10_t_menos_2) / 3`. Esa redundancia determinista es esperable, no un fallo del cálculo.

Estos pesos son coeficientes del eje sobre variables estandarizadas, no correlaciones variable/componente, porcentajes de importancia ni efectos causales. La fórmula es `PCk = suma(peso_kj × (entrada_j − media_entrenamiento_j) / escala_entrenamiento_j)`. Los signos de los ejes son convencionales. La tabla conserva todos los coeficientes y las estadísticas de ajuste.

La figura PC1/PC2 pierde casi la mitad de la variación y no debe interpretarse como representación completa de los datos. La estandarización iguala escalas, pero no elimina influencia de valores extremos. Incluir varios resúmenes correlacionados puede dar más peso al historial en la geometría. No se ha entrenado una regresión con PCA ni medido una supuesta mejora de MAE.

## LDA: método y comparación

Las dos variantes tienen preprocesado idéntico a sus logísticas: estandarización de numéricas y estación one-hot, ajustados solo con entrenamiento. LDA usa `solver="eigen"`, `shrinkage="auto"`, una componente y probabilidades a priori inferidas del entrenamiento. La regularización automática de la covarianza reduce problemas por entradas correlacionadas. No se hace búsqueda de hiperparámetros.

LDA presupone distribuciones gaussianas por clase y una covarianza compartida; esas aproximaciones pueden ser limitadas en PM10, picos y calendario cíclico. Con dos clases, la reducción tiene como máximo **una dimensión**, LD1. LD1 no es una concentración ni una probabilidad.

Se reutilizan las predicciones guardadas de las logísticas y persistencia, sin reajustarlas. Se verifica igualdad exacta de las claves, etiquetas y concentraciones objetivo de las 1.039 filas. El corte de cada LDA se selecciona con la misma regla preexistente de la comparación meteorológica: no superar las **37 falsas alarmas totales** de persistencia en 2023; priorizar más comienzos detectados, más positivos totales, menos falsas alarmas y corte más alto. Los empates de probabilidad entran juntos y la decisión es `probabilidad >= corte`.

| Modelo | Corte | Verdaderos positivos | Falsas alarmas | Falsos negativos | F1 |
| --- | --- | --- | --- | --- | --- |
| LDA sin meteorología | 0,148687 | 49 | 37 | 44 | 0,5475 |
| LDA con meteorología | 0,156297 | 47 | 37 | 46 | 0,5311 |
| Logística sin meteorología | 0,200729 | 63 | 36 | 30 | 0,6563 |
| Logística con meteorología | 0,199045 | 65 | 35 | 28 | 0,6736 |
| Persistencia | PM10 previo > 27 | 57 | 37 | 36 | 0,6096 |

Las muestras y el límite son comunes; no se fuerza igualdad exacta de falsas alarmas, porque cortes y empates producen conjuntos de avisos discretos. Las métricas se calculan en la misma validación usada para elegir cortes, por lo que pueden ser optimistas. Además, 2023 ya se ha utilizado para decisiones anteriores del proyecto. Esta comparación no es una nueva prueba independiente.

En las **945 filas cuyo día anterior no era elevado** hay **36 comienzos**. LDA sin/con meteorología detecta 1/1 con 12/11 falsas alarmas; logística sin/con meteorología detecta 8/10 con 11/10 falsas alarmas; persistencia detecta 0 con 0 falsas alarmas. No confundir este contexto de 2023 con los 891 casos y 27 comienzos de la prueba ya conocida de 2025.

Como diagnóstico secundario sin fijar corte:

| Modelo | ROC AUC | Average precision |
| --- | --- | --- |
| LDA sin meteorología | 0,9027 | 0,5561 |
| LDA con meteorología | 0,9061 | 0,5608 |
| Logística sin meteorología | 0,9249 | 0,6350 |
| Logística con meteorología | 0,9280 | 0,6499 |

Hay 93 positivos de 1.039 casos (8,95 %). Average precision debe leerse con esa prevalencia de referencia. Estas métricas describen ordenación/discriminación, no calibración ni riesgo sanitario. Los casos próximos en tiempo y las estaciones pueden estar relacionados.

**Resultado:** esta configuración de LDA no mejora la logística. Es una comparación informativa que se conserva con sus limitaciones. No se promociona ni se reevalúa en las pruebas conocidas. Una decisión futura exigiría fijar el procedimiento y disponer de una evaluación temporal independiente.

## Visualización y términos

React ofrece:

- Varianza explicada y acumulada, gráfico PC1/PC2, pesos de cada componente, medias y escalas de ajuste.
- Selección de entrenamiento/validación y estación para las proyecciones. No se muestrean puntos.
- Tabla de proyecciones paginada en bloques de 15 filas, como alternativa accesible a la figura.
- Distribuciones de LD1 por clase con 20 intervalos comunes, proporciones normalizadas **dentro de cada clase**, frecuencias y límites tabulados. El último intervalo incluye su extremo superior; los demás lo excluyen. Al cambiar periodo/estación, los intervalos se recalculan: no son escalas fijas para comparar filtros visualmente.
- Comparación global, comienzos, ROC AUC y average precision; descargas de tablas y protocolo.

VP: elevado correctamente avisado; FP: aviso sin elevado; FN: elevado sin aviso; VN: día no elevado sin aviso. Precisión = VP/(VP+FP); recall o sensibilidad = VP/(VP+FN); F1 combina ambas. Un denominador no definido se conserva como nulo, no se sustituye por cero. Componentes y LD1 son coordenadas sin unidades de concentración.

## Reproducir y auditar

Desde la raíz, con el entorno de dependencias fijadas:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.analyze_pm10_projections
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Los imports de scikit-learn se mantienen dentro de `tfm_data/adapters/sklearn/projections.py`. Las guardas temporales y la selección de corte están en `tfm_data/evaluation/projections.py`; el pipeline prepara el análisis y exporta archivos. Flask solo lee JSON/CSV y no carga modelos.

| Entrada | Formato | Uso |
| --- | --- | --- |
| `data/interim/pm10_prediction/tabla_modelos_completa.csv` | CSV | Entradas numéricas y particiones temporales de PCA |
| `data/interim/pm10_weather/tabla_pm10_meteo.csv` | CSV | Cohorte común, entradas y etiquetas de LDA |
| `data/interim/pm10_weather/esquema_comparacion.json` | JSON | Predictores, umbral y criterio de cohorte |
| `output/pm10_weather_validation/predicciones_validacion_2023.csv` | CSV | Referencias logísticas/persistencia ya guardadas |
| `output/pm10_weather_validation/configuracion.json` | JSON | Cortes originales y límite de falsas alarmas |

El protocolo conserva SHA-256 de estas entradas, versiones y parámetros. El informe protege además los modelos originales y las predicciones finales de Madrid/Barcelona/meteorología, comprobando sus huellas antes y después. Los nuevos artefactos se guardan separados en `output/experiments/projections/artefactos.joblib`; no se sirven por la API.

La carpeta contiene 14 archivos, incluidos:

| Salida | Columnas y tipos |
| --- | --- |
| `pca_componentes.csv` | `component`: entero; `ratio`, `cumulative`: reales entre 0 y 1 |
| `pca_pesos.csv` | `feature`: texto; `mean`, `scale`, `PC1`…`PC12`: reales |
| `pca_proyecciones.csv`, `lda_*_proyecciones.csv` | `station`, `name`: textos; `date`: fecha ISO; `partition`: training/validation; `elevated`: entero 0/1; `x`, `y`: reales. PCA: x=PC1, y=PC2. LDA: x=LD1, y=0 como marcador técnico, no segunda componente |
| `predicciones_validacion_2023.csv` | Estación, nombre, contexto y modelo: textos; objetivo: fecha ISO; PM10 previo/objetivo: reales; `observado`, `aviso`: enteros 0/1; `probabilidad_elevado`: real nullable, no aplica para persistencia |
| `metricas.csv`, `metricas_contexto.csv` | `modelo` y, cuando corresponde, `contexto`: textos; n, VP/FP/FN/VN, avisos, positivos: enteros; precisión, recall y F1: reales nullable |
| `ranking.csv` | `model`: texto; `rocAuc`, `averagePrecision`: reales |
| `lda_*_barrido.csv` | `umbral`: real; positivos, falsas alarmas, comienzos y falsas alarmas con día previo no elevado: recuentos enteros |
| `protocolo.json`, `resumen.json` | JSON con configuración/metadatos y resultados; incluye rutas y huellas |
| `artefactos.joblib` | Binario Python: PCA y dos LDA, junto con los cortes; exclusivamente uso local confiable |

`GET /api/experiments/projections` devuelve el informe JSON. `GET /api/experiments/projections/files/{filename}` permite descargar únicamente los CSV y el protocolo de la lista permitida; otros nombres devuelven 404.

Referencias metodológicas: [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html), [LDA](https://scikit-learn.org/stable/modules/generated/sklearn.discriminant_analysis.LinearDiscriminantAnalysis.html). Los endpoints públicos y mapeadores originales se conservan en las guías de [fuentes](15_fuentes_endpoints_formatos.md), [cruce meteorológico](23_cruce_pm10_meteorologia.md) y [comparación de meteorología](24_comparacion_logistica_meteorologia.md).
