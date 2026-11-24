# Demo retrospectiva de PM10

La demo permite consultar las **1.013 observaciones de regresión de 2024** y las **1.003 de clasificación de 2025** en tres estaciones de Madrid. Cada vista permite elegir la estación y la fecha objetivo entre las observaciones evaluadas.

- **Regresión 2024.** Se muestran el PM10 observado, la previsión de Ridge, la persistencia y el error absoluto de ambos métodos.
- **Clasificación 2025.** Se muestran el PM10 del día anterior, el observado, las previsiones de viento y precipitación, la probabilidad de cada logística, su corte y la decisión de aviso. El 5 de agosto y el 22 de febrero en Tres Olivos permiten mostrar un comienzo detectado y una falsa alarma.

La interfaz es estática y usa los resultados guardados de las pruebas. Una vez montada la imagen, funciona localmente con los datos incluidos. [Regresión de 2024](21_resultados_prueba_final_pm10.md) · [Clasificación de 2025](25_prueba_meteorologia_2025.md)

## Ejecutar con Docker

Desde la raíz del proyecto, con Docker en ejecución:

```powershell
docker build -t tfm-pm10-demo ./demo
docker run --rm -p 127.0.0.1:8065:80 tfm-pm10-demo
```

Abrir [la demo en el navegador](http://127.0.0.1:8065/). Para detener el contenedor, usar `Ctrl+C` en el terminal donde se ejecutó.

## Regenerar los datos de la demo

El archivo `demo/data.js` ya está incluido. El exportador toma los resultados de ambas pruebas, comprueba que los métodos coincidan en estación y fecha, y añade el ciclo meteorológico y las dos previsiones de NOAA para los casos de 2025. Si se regeneran los resultados originales, se puede actualizar el archivo antes de reconstruir la imagen. [Exportador](../scripts/build_demo_data.py)

```powershell
.\.venv\Scripts\python.exe scripts/build_demo_data.py
```
