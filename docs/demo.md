# Demostración verificable

Subir cada carpeta a recepcion con su nombre y pasar ese nombre como parámetro lote. publicaciones permanece disponible desde la primera carga.

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | lote_01 | Silver 40 filas. Control día 1 = 1.000 |
| 2 | lote_02 | Silver 80 filas. Control día 2 = 1.200 |
| 3 | Repetir lote_02 | Bronze y Silver conservan sus recuentos. MERGE inserta y actualiza cero filas |
| 4 | lote_03 | Silver 470 filas. Un rechazo. Categorías suma 39 vídeos al tercer día |
| 5 | lote_correccion | Silver 470 filas. Control día 1 = 950, versión 2. Día 2 = 1.200, crecimiento 250 |
| 6 | lote_reenvio | Control día 1 conserva 950 y versión 2 |
| 7 | lote_calidad | Silver conserva 470 filas. Rechazos únicos total 6 |
| 8 | lote_fallo | Falla validar antes de Bronze. Guardar captura |
| 9 | Corregir CSV y Repair run | Cinco tareas correctas, control conserva versión 2 |

El nombre V000 aparece en dos plataformas. Filtrar siempre por ambas columnas.

## Evidencias a capturar en el workspace

Guardar capturas en docs/evidencias con los nombres carga_01, carga_02, repeticion, correccion, reenvio, rechazos, job_fallido, job_reparado y panel. Adjuntar el historial Delta y la ruta del run.

El repositorio incluye resultados de pruebas locales. Las capturas del workspace y el vídeo se incorporan después del despliegue.

## Guion de vídeo de 2–3 minutos

- Presentar la pregunta de negocio y mostrar el panel.
- Mostrar las dos fechas del control, 950 y 1.200, y explicar la corrección tardía.
- Mostrar que un reenvío conserva la versión 2.
- Mostrar un rechazo con el JSON original y el motivo.
- Abrir el job fallido por cabecera y su reparación.
- Cerrar con la comparación por categoría a edad tres y su cobertura de 39 vídeos.

## Pruebas adicionales de calidad

tests/test_pipeline.py comprueba versiones 2 y 10, tasa con cero reproducciones y conflictos de contenido para una misma versión. Un descenso entre fechas se representa con crecimiento negativo y descenso_acumulado.
