# Guía para obtener y ejecutar la entrega

La entrega preparada contiene dos paquetes complementarios y un archivo de huellas. El paquete del proyecto reúne código, dependencias, modelos, tablas tratadas, métricas, notebook, documentación y aplicaciones. El paquete de fuentes conserva los 43 originales exactos que identifican los manifiestos.

## Restaurar la versión utilizada en el TFM

El paquete del proyecto incluye también el experimento de Barcelona provincia y su comparación con Madrid. Ambos se consultan en **Experimentos** dentro de React. Los originales nacionales ya incluidos en el paquete de fuentes permiten reconstruir Barcelona; el [recorrido territorial](38_experimentos_madrid_barcelona.md) detalla las cuatro etapas y sus resultados. La réplica territorial y su auditoría incorporan ocho pruebas adicionales; la suite actual contiene 106 pruebas, incluidas nueve de estadísticas descriptivas y diagramas de caja, cinco de la comparación de ventanas, seis de la permutación agrupada, cuatro de los casos de estudio y cinco de PCA/LDA.

Guarda juntos los siguientes archivos de entrega

- tfm_pm10_project.zip
- tfm_pm10_sources.zip
- checksums.json

Compara los SHA-256 de ambos ZIP con los valores de checksums.json mediante Get-FileHash. A continuación, extrae los paquetes en una misma carpeta

~~~powershell
Expand-Archive .\tfm_pm10_project.zip -DestinationPath .\tfm_pm10
Expand-Archive .\tfm_pm10_sources.zip -DestinationPath .\tfm_pm10
cd tfm_pm10
~~~

El proyecto puede obtenerse también desde el repositorio cuando se publique. El paquete de fuentes debe extraerse en su raíz para recuperar los mismos originales.

Con Python 3.12 instalado, crea un entorno e instala las dependencias

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r explorer/requirements.txt
.\.venv\Scripts\python.exe scripts/restore_sources.py
~~~

La comprobación debe terminar indicando **Verificados 43/43 originales**. Comprueba tamaño y SHA-256 frente a los manifiestos. La instalación de dependencias y la construcción de imágenes necesitan acceso a sus registros o una caché disponible.

Ambos paquetes se extrajeron juntos en una carpeta nueva el 19 de noviembre de 2026. Se verificaron sus huellas, la integridad de los ZIP y los 43 originales restaurados.

## Alternativa de descarga pública

Con el código y los manifiestos del proyecto disponibles, se pueden descargar los originales ausentes

~~~powershell
.\.venv\Scripts\python.exe scripts/restore_sources.py --download
~~~

El programa consulta únicamente las URLs HTTPS registradas y verifica cada fichero antes de incorporarlo a la carpeta de datos. Un fichero existente se comprueba y un conflicto de huella queda señalado. Una respuesta diferente al original registrado se descarta y se informa como error. Una nueva ejecución aprovecha los archivos ya verificados.

Para seleccionar una fuente concreta

~~~powershell
.\.venv\Scripts\python.exe scripts/restore_sources.py --download --file data/raw/health_air_history/miteco_diarios_2024.zip
~~~

Los proveedores pueden revisar sus históricos. El paquete de fuentes conserva la versión de la evaluación y permite reproducirla cuando una URL devuelve otra versión. Los manifiestos documentan las fuentes públicas y sus huellas.

En la comprobación del 19 de noviembre de 2026 se restauraron mediante sus URLs tres archivos de una carpeta inicialmente vacía, correspondientes a INE, MITECO y EEA. Las tres descargas coincidieron con sus huellas registradas. El resto de originales se comprobó a partir de la instantánea incluida.

## Consultar la aplicación

Con Docker en ejecución, desde la raíz

~~~powershell
docker compose -f explorer/compose.yaml up --build
~~~

Abre http://127.0.0.1:8066. Las carpetas de datos, documentación y resultados se montan desde la copia extraída.

Para desarrollar en local, arranca Flask en una terminal

~~~powershell
.\.venv\Scripts\python.exe -m explorer.server
~~~

En otra terminal, con Node 24 y pnpm 11.2.2

~~~powershell
cd explorer
pnpm install --frozen-lockfile
pnpm run dev
~~~

Abre la dirección que muestre Vite. Las peticiones de API se redirigen a Flask en el puerto 8066. Corepack permite ejecutar los comandos de pnpm mediante corepack pnpm.

## Recorrer y reproducir resultados

El [README principal](../README.md) contiene la memoria del proyecto. Para recorrer los cálculos, instala las [dependencias del notebook](../notebooks/requirements.txt), abre el [notebook ejecutado](../notebooks/01_pm10_end_to_end.ipynb) en VS Code y selecciona el Python de .venv como kernel.

La [verificación en entorno aislado](33_verificacion_entrega.md) proporciona el orden comprobado de los pipelines para reconstruir tablas y experimentos. El extracto meteorológico compacto y sus manifiestos están en data/interim/weather_forecasts/ y forman parte del paquete del proyecto. La extracción inicial de GRIB2, que requirió unos 5,52 GB transferidos, está descrita en la [guía de NOAA](22_viabilidad_meteorologia_pm10.md).

Las pruebas se ejecutan desde la raíz

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
~~~

En esa comprobación incremental se contaban 64 pruebas. Incluye comprobaciones de restauración, errores pareados y bootstrap por bloques, con conservación de huecos y sincronización entre estaciones.

## Preparación de los paquetes por el autor

Desde la copia completa, con los originales presentes y verificados

~~~powershell
.\.venv\Scripts\python.exe scripts/build_delivery.py
~~~

Se generan los dos ZIP y checksums.json en output/delivery/. El constructor comprueba primero los originales y después la integridad de ambos ZIP.

El paquete del proyecto conserva los manifiestos de data/raw/ y distribuye los datos originales en el segundo paquete. Los entornos, dependencias instaladas y archivos temporales quedan fuera de los paquetes. La configuración de Git ignora los originales voluminosos y los ZIP generados.

Para publicar la entrega habrá que compartir el repositorio del proyecto y una ubicación accesible del paquete de fuentes. Los enlaces de publicación y el envío por campus se completan al efectuar la entrega.

## Casos de estudio

La pantalla **Casos** prepara tres ejemplos y una falsa alarma de contraste con evidencias CSV. El [guion de defensa](43_casos_de_estudio_defensa.md) explica la selección reproducible, los cortes originales, el contexto retrospectivo y las limitaciones. Los modelos y las predicciones originales se conservan. El ensayo con el autor sigue pendiente.

## Análisis PCA y LDA

Disponible en **Experimentos → PCA y LDA**. El [protocolo exploratorio](44_pca_lda_pm10.md) conserva ajuste solo con entrenamiento y validación de 2023, gráficos, comparación y descargas. No se reevalúan 2024/2025 ni se sustituyen modelos finales.

## Gráficos territoriales

El [selector de territorio](45_graficos_territoriales.md) conecta mapa, observaciones, predicciones, regresión, errores e intervalos con las salidas guardadas de Madrid o Barcelona provincia. Se añadieron y ejecutaron cinco pruebas de API en la imagen Docker del explorador; TypeScript y la compilación también se verificaron en Docker. No se reentrenaron modelos ni se recalcularon pruebas finales.
