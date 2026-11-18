# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
data = spark.table(f"{schemas['silver']}.mediciones")
assert data.count() > 0, "Silver vacío"
assert data.groupBy(*KEY).count().filter("count > 1").count() == 0
assert data.filter("version_origen < 1 OR reproducciones < 0").count() == 0
posts = spark.table(f"{schemas['silver']}.publicaciones")
assert data.join(posts, ["plataforma", "video_id"], "left_anti").count() == 0
print("Claves, métricas e integridad referencial comprobadas")
