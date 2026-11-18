# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
outputs = gold_tables(spark.table(f"{schemas['silver']}.mediciones"),
                      spark.table(f"{schemas['silver']}.publicaciones"))
for name, frame in outputs.items():
    frame.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{schemas['gold']}.{name}")
print("Tres tablas Gold publicadas")
