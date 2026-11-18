# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
posts = publications(spark.table(f"{schemas['bronze']}.publicaciones"))
posts.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{schemas['silver']}.publicaciones")
# Releer Bronze completo hace recuperable una caída después de ingerir.
# El tamaño de la muestra permite reconciliar todo el histórico.
raw = spark.table(f"{schemas['bronze']}.mediciones")
valid, rejected = measurements(raw, posts)
target = f"{schemas['silver']}.mediciones"
merge_measurements(spark, valid, target)
rejected.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{schemas['silver']}.rechazos")
metrics = spark.sql(f"DESCRIBE HISTORY {target} LIMIT 1").first()["operationMetrics"]
log = [(run_id, batch, raw.count(), rejected.count(),
        int(metrics.get("numTargetRowsInserted", 0)),
        int(metrics.get("numTargetRowsUpdated", 0)))]
(spark.createDataFrame(log, "run_id string, lote string, filas_bronze long, rechazos_unicos long, insertadas long, actualizadas long")
 .withColumn("registrado_en", F.current_timestamp())
 .write.format("delta").mode("append").saveAsTable(f"{schemas['silver']}.ejecuciones"))
