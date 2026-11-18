# Despliegue de DirectData

## Preparar archivos y workspace

1. Ejecutar python scripts/generar_datos.py desde la copia local.
2. Crear un Git folder en Databricks con la URL del repositorio y seleccionar la rama implementacion-completa. Una vez integrado en main, utilizar main.
3. Abrir notebooks/00_config. Usar serverless. Indicar un catálogo existente con permisos de creación. El valor inicial es workspace, que puede necesitar adaptación.
4. Ejecutar 00_config. Se crean directdata_bronze, directdata_silver y directdata_gold, además del volumen directdata_bronze.archivos.
5. En Catalog, abrir ese volumen y crear recepcion/publicaciones y recepcion/lote_01. Subir publicaciones.csv a la primera carpeta y el CSV del día 1 a la segunda.
6. Los archivos de entrada de un lote se mantienen inmutables después de ingerir. Cada lote tiene un checkpoint propio. Una corrección se entrega como nuevo archivo en lote_correccion.

## Ejecutar la primera carga

Ejecutar en orden los notebooks 01_validar, 02_bronze, 03_silver, 04_comprobar y 05_gold. En cada uno usar el mismo catalogo, prefijo directdata y lote lote_01.

Ejecutar en una celda SQL, sustituyendo workspace por el catálogo elegido:

```sql
SELECT COUNT(*) FROM workspace.directdata_bronze.mediciones;
SELECT COUNT(*) FROM workspace.directdata_silver.mediciones;
SELECT * FROM workspace.directdata_gold.por_video
WHERE plataforma = 'tiktok' AND video_id = 'V000';
```

Las dos primeras consultas devolverán 40. El control mostrará 1.000 reproducciones. Guardar la captura de esas consultas. Repetir 02_bronze con el mismo checkpoint y comprobar que Bronze sigue con 40.

## Crear el job

Opción de interfaz. Crear un Job llamado DirectData con cinco tareas Notebook, todas serverless, siguiendo este orden:

| Tarea | Notebook | Depende de |
|---|---|---|
| validar | 01_validar | Inicio |
| bronze | 02_bronze | validar |
| silver | 03_silver | bronze |
| comprobar | 04_comprobar | silver |
| gold | 05_gold | comprobar |

Añadir parámetros del job catalogo, prefijo y lote. Elegir máximo de ejecuciones concurrentes 1 y ejecutar manualmente. Configurar run_id como parámetro de tarea con valor {{job.run_id}}. Las dependencias deben conservar la condición predeterminada All succeeded.

Opción CLI. Con la CLI oficial de Databricks autenticada en tu workspace:

```powershell
python scripts/crear_job.py --workspace-path "/Workspace/Users/TU_USUARIO/directData" --catalogo workspace
databricks jobs create --json @jobs/directdata.json
```

El script escribe un JSON con las rutas reales. Usar el job_id devuelto para ejecutar:

```powershell
databricks jobs run-now --json '{"job_id":123,"job_parameters":{"lote":"lote_01"}}'
```

La autenticación y el identificador del workspace pertenecen a la cuenta que realiza el despliegue.

## Panel

Abrir 06_panel y ejecutar las tres celdas. Configurar una línea temporal sobre fecha_medicion y reproducciones, filtrando por plataforma y video_id. Configurar barras por categoria con tasa_interaccion y filtro de plataforma. La tercera visualización será una tabla resumen.

También pueden crearse las mismas visualizaciones en un dashboard SQL con estas consultas, ajustando el catálogo:

```sql
SELECT * FROM workspace.directdata_gold.por_video;
SELECT * FROM workspace.directdata_gold.por_categoria;
SELECT * FROM workspace.directdata_gold.por_plataforma;
```

Publicar o actualizar el dashboard después de un job correcto. El gráfico de categorías comenzará a tener datos cuando se carguen mediciones de edad tres.

## Programación y seguimiento

Para evidenciar programación, añadir un horario en el Job, esperar una ejecución, guardar su historial y pausar el horario después. Configurar notificaciones de fallo en la interfaz con una dirección propia si la cuenta lo admite. El código entrega ejecuciones manuales por defecto.

Consultar silver.ejecuciones para el volumen procesado y DESCRIBE HISTORY sobre silver.mediciones para el detalle de MERGE. El estado de tareas fallidas está en el historial del job.

## Recuperación

Subir lote_fallo y ejecutar el job con ese parámetro. validar fallará y las tareas dependientes quedarán sin ejecutar. Corregir el mismo CSV añadiendo compartidos a su cabecera y 11 a la fila. Como el fallo sucede antes de Bronze, se puede sustituir el archivo en recepción. En la ejecución fallida elegir Repair run para volver a ejecutar validar y sus dependientes.

Mantener los checkpoints después de cualquier caída. Una repetición de Silver reevalúa Bronze y conserva versiones ya aceptadas. Una reparación de Gold vuelve a publicar las tres tablas.
