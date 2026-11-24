# Recorrido explicativo del TFM

Abre [el notebook de PM10](01_pm10_end_to_end.ipynb) para recorrer la preparación de variables, el entrenamiento, la validación y la interpretación de resultados. Incluye tablas y cuatro figuras con las salidas de una ejecución completa.

## Preparación

Desde la raíz del proyecto, con el entorno Python creado, instala las dependencias del notebook

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r notebooks/requirements.txt
~~~

En VS Code, abre el archivo con las extensiones de Python y Jupyter y selecciona el ejecutable de Python de .venv como kernel. Ejecuta todas las celdas en orden. El notebook encuentra la raíz tanto si se inicia desde la carpeta principal como desde notebooks/.

Se necesitan las tablas diarias y predictivas de data/interim/, los resultados guardados de output/ y el artefacto de Ridge de models/pm10/validation_2023/. Las fuentes y su preparación se describen en las guías enlazadas desde el [README principal](../README.md).

## Qué ejecuta

El recorrido tiene 25 celdas, de las cuales 12 contienen código.

1. Revisa cobertura, claves y valores ausentes de la tabla diaria.
2. Reconstruye las variables con el mapeador del proyecto y las contrasta con la tabla guardada.
3. Comprueba la separación temporal por fecha objetivo.
4. Ajusta Ridge y Random Forest en memoria con 2017–2022 y reproduce la comparación de validación de 2023.
5. Carga el Ridge congelado, comprueba sus huellas y reproduce las 1.013 predicciones de prueba de 2024.
6. Examina un pico, descompone una predicción y consulta los intervalos bootstrap de la diferencia de MAE.
7. Revisa los resultados de clasificación de 2025 y recalcula los escenarios de costes relativos.
8. Muestra las métricas guardadas del complemento sanitario y plantea preguntas para preparar la defensa.

El entrenamiento de validación reutiliza las clases y funciones del proyecto. Las predicciones de clasificación y las métricas sanitarias se leen de las salidas existentes. La preparación de las descargas originales y el ajuste completo de esos otros experimentos se reproducen mediante sus pipelines.

Las celdas leen los archivos del proyecto y mantienen los nuevos ajustes en memoria. Los modelos, las tablas y las métricas existentes sirven como referencias para las comprobaciones. Al guardar el notebook se conservan sus salidas y figuras dentro del archivo.

## Comprobación realizada

El 19 de noviembre de 2026 se ejecutaron todas las celdas con las dependencias fijadas en [requirements.txt](requirements.txt). Se verificaron los contrastes numéricos con los resultados guardados y se revisaron las cuatro figuras. La reproducción completa desde la descarga en un entorno limpio sigue siendo una tarea de entrega.
