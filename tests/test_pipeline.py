from pathlib import Path
import csv
import subprocess
import sys

import pytest
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from directdata.contracts import MEDICIONES, PUBLICACIONES, validate_headers
from directdata.transforms import publications, measurements, merge_measurements, gold_tables

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/sample"


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    warehouse = tmp_path_factory.mktemp("warehouse")
    builder = (SparkSession.builder.master("local[2]").appName("DirectData-tests")
               .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
               .config("spark.sql.warehouse.dir", str(warehouse))
               .config("spark.sql.shuffle.partitions", "2")
               .config("spark.databricks.delta.snapshotPartitions", "2")
               .config("spark.ui.enabled", "false")
               .config("spark.jars.repositories", "https://repo.maven.apache.org/maven2"))
    session = configure_spark_with_delta_pip(builder).getOrCreate()
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def read(spark, folders, columns):
    records = []
    for folder in folders:
        for path in sorted((DATA / folder).glob("*.csv")):
            with path.open(encoding="utf-8") as stream:
                records.extend([tuple(row[c] for c in columns) for row in csv.DictReader(stream)])
    return spark.createDataFrame(records, ", ".join(f"{c} string" for c in columns))


def test_generator_and_header():
    subprocess.run([sys.executable, str(ROOT / "scripts/generar_datos.py")], check=True)
    validate_headers(DATA / "lote_01", MEDICIONES)
    with pytest.raises(ValueError, match="Cabecera"):
        validate_headers(DATA / "lote_fallo", MEDICIONES)
    with (DATA / "publicaciones/publicaciones.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    from collections import Counter
    counts = Counter((r["plataforma"], r["categoria"].strip().lower()) for r in rows)
    assert len(counts) == 8 and set(counts.values()) == {5}


def test_end_to_end(spark):
    posts = publications(read(spark, ["publicaciones"], PUBLICACIONES))
    first, _ = measurements(read(spark, ["lote_01"], MEDICIONES), posts)
    target = "default.directdata_test_mediciones"
    merge_measurements(spark, first, target)
    assert spark.table(target).count() == 40
    second, _ = measurements(read(spark, ["lote_02"], MEDICIONES), posts)
    merge_measurements(spark, second, target)
    assert spark.table(target).count() == 80
    merge_measurements(spark, second, target)
    history = spark.sql(f"DESCRIBE HISTORY {target} LIMIT 1").first()["operationMetrics"]
    assert int(history["numTargetRowsInserted"]) == 0
    assert int(history["numTargetRowsUpdated"]) == 0
    correction, _ = measurements(read(spark, ["lote_correccion"], MEDICIONES), posts)
    merge_measurements(spark, correction, target)
    resend, _ = measurements(read(spark, ["lote_reenvio"], MEDICIONES), posts)
    merge_measurements(spark, resend, target)
    control = spark.table(target).filter("plataforma='tiktok' AND video_id='V000'").orderBy("fecha_medicion").collect()
    assert [(r.reproducciones, r.version_origen) for r in control] == [(950, 2), (1200, 1)]
    full, rejects = measurements(read(spark, ["lote_01", "lote_02", "lote_03",
                                             "lote_correccion", "lote_reenvio", "lote_calidad"], MEDICIONES), posts)
    merge_measurements(spark, full, target)
    assert spark.table(target).count() == 470
    assert rejects.count() == 6
    tables = gold_tables(spark.table(target), posts)
    assert tables["por_categoria"].agg({"videos": "sum"}).first()[0] == 39
    assert tables["por_plataforma"].agg({"videos": "sum"}).first()[0] == 40
    assert tables["por_video"].filter("plataforma='tiktok' AND video_id='V000' AND edad_dias=1").first().crecimiento == 250


def test_versions_zero_and_conflict(spark):
    posts = publications(read(spark, ["publicaciones"], PUBLICACIONES))
    schema = ", ".join(f"{c} string" for c in MEDICIONES)
    rows = [("tiktok", "V000", "2026-11-01", v, n, "0", "0", "0")
            for v, n in [("2", "1"), ("10", "0")]]
    valid, _ = measurements(spark.createDataFrame(rows, schema), posts)
    assert valid.first().version_origen == 10
    assert gold_tables(valid, posts)["por_video"].first().tasa_interaccion is None
    rows.append(("tiktok", "V000", "2026-11-01", "10", "2", "0", "0", "0"))
    with pytest.raises(ValueError, match="Misma clave"):
        measurements(spark.createDataFrame(rows, schema), posts)
