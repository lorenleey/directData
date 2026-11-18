# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
# Serie temporal: fecha_medicion en X, reproducciones en Y, por plataforma y video_id.
display(spark.table(f"{schemas['gold']}.por_video").orderBy("plataforma", "video_id", "fecha_medicion"))

# COMMAND ----------
# Barras: categoria en X, tasa_interaccion en Y; filtro de plataforma.
# videos muestra la cobertura de la comparación al tercer día.
display(spark.table(f"{schemas['gold']}.por_categoria").orderBy("plataforma", "categoria"))

# COMMAND ----------
# Tabla resumen: última medición disponible de cada vídeo.
display(spark.table(f"{schemas['gold']}.por_plataforma"))
