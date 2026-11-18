# Databricks notebook source
import sys
from pathlib import Path
from uuid import uuid4
from pyspark.sql import functions as F

# Git folders conserva src y notebooks en el mismo repositorio.
sys.path.insert(0, str(Path.cwd().parent / "src"))
from directdata.contracts import PUBLICACIONES, MEDICIONES, KEY, validate_headers
from directdata.transforms import publications, measurements, merge_measurements, gold_tables

for name, default in [("catalogo", "workspace"), ("prefijo", "directdata"),
                      ("lote", "lote_01"), ("run_id", "manual")]:
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.text(name, default)
catalog = dbutils.widgets.get("catalogo")
prefix = dbutils.widgets.get("prefijo")
batch = dbutils.widgets.get("lote")
run_id = dbutils.widgets.get("run_id")
import re
for value in (catalog, prefix, batch):
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", value):
        raise ValueError("Usa identificadores alfanuméricos con guion bajo")
schemas = {name: f"{catalog}.{prefix}_{name}" for name in ("bronze", "silver", "gold")}
for schema in schemas.values():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {schemas['bronze']}.archivos")
root = f"/Volumes/{catalog}/{prefix}_bronze/archivos"
if run_id == "manual":
    run_id = str(uuid4())
