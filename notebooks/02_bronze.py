# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
from pyspark.sql.types import StructType, StructField, StringType

# Revalidar ambas fuentes antes de escribir permite la ejecución independiente.
validate_headers(f"{root}/recepcion/publicaciones", PUBLICACIONES)
validate_headers(f"{root}/recepcion/{batch}", MEDICIONES)
for source, columns, folder in [
    ("publicaciones", PUBLICACIONES, "publicaciones"),
    ("mediciones", MEDICIONES, batch),
]:
    path = f"{root}/recepcion/{folder}"
    validate_headers(path, columns)
    schema = StructType([StructField(c, StringType(), True) for c in columns])
    # Checkpoint estable por lote. Reparar conserva su progreso.
    checkpoint = f"{root}/checkpoints/{source}/{folder}"
    stream = (spark.readStream.format("cloudFiles")
              .option("cloudFiles.format", "csv")
              .option("header", "true")
              .option("mode", "FAILFAST")
              .option("cloudFiles.schemaEvolutionMode", "none")
              .schema(schema).load(path)
              .withColumn("archivo_origen", F.col("_metadata.file_path"))
              .withColumn("lote", F.lit(folder))
              .withColumn("ingestado_en", F.current_timestamp()))
    query = (stream.writeStream.format("delta").outputMode("append")
             .option("checkpointLocation", checkpoint)
             .trigger(availableNow=True).toTable(f"{schemas['bronze']}.{source}"))
    query.awaitTermination()
    print(source, query.lastProgress)
