# Validación de la implementación

Fecha de ejecución local: 18 de noviembre de 2026.

Resultado de pytest: **3 passed, 1 warning in 39.51s**.
El aviso procede de un plugin de pytest preinstalado en el entorno de ejecución.

Entorno observado: Python 3.12, OpenJDK 21, PySpark 3.5.3 y delta-spark 3.2.1.
El workflow de GitHub usa Python 3.11 y Java 17.

## Comprobaciones ejecutadas

- Generación reproducible y ocho combinaciones plataforma/categoría con cinco vídeos cada una.
- Rechazo de cabecera incompleta.
- MERGE real sobre tablas Delta locales.
- Primera carga de 40 filas y segunda de 80.
- Repetición con cero inserciones y cero actualizaciones en el historial Delta.
- Corrección del control a versión 2 y 950 reproducciones.
- Reenvío de versión 1 que conserva la corrección.
- Histórico de 470 mediciones válidas.
- Seis rechazos únicos.
- Comparación a edad tres con 39 vídeos.
- Resumen por plataforma con 40 vídeos.
- Crecimiento del control de 250 tras corregir su primera medición.
- Orden numérico de versiones 2 y 10.
- Tasa NULL con cero reproducciones.
- Error explícito ante contenidos contradictorios de una misma clave y versión.

## Verificación en workspace pendiente

Auto Loader, checkpoints remotos, permisos, el job serverless, Repair run,
la programación y el panel necesitan ejecutarse con acceso al workspace de Databricks.
Seguir docs/despliegue.md y docs/demo.md para recoger las evidencias.

La descarga de dependencias Java inicialmente falló por la configuración de red
del entorno. Se descargaron los artefactos oficiales de Maven a la caché local y
se repitieron las pruebas con éxito. El código de las pruebas usa el mecanismo
estándar de delta-spark para resolver esas dependencias.
