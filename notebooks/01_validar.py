# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------
# La validación lee las cabeceras con csv antes de iniciar Auto Loader.
validate_headers(f"{root}/recepcion/publicaciones", PUBLICACIONES)
validate_headers(f"{root}/recepcion/{batch}", MEDICIONES)
print(f"Cabeceras válidas para {batch}")
