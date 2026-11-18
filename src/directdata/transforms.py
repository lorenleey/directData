from pyspark.sql import functions as F, Window
from delta.tables import DeltaTable
from .contracts import PUBLICACIONES, MEDICIONES, METRICS, KEY


def publications(raw):
    data = raw.select(*PUBLICACIONES).dropDuplicates()
    for column in ("plataforma", "categoria"):
        data = data.withColumn(column, F.lower(F.trim(F.col(column))))
    data = data.withColumn("video_id", F.trim("video_id"))
    data = data.withColumn("fecha_publicacion", F.expr("try_cast(fecha_publicacion as date)"))
    invalid = (
        F.col("plataforma").isNull() |
        ~F.col("plataforma").isin("tiktok", "instagram") |
        F.col("video_id").isNull() | (F.col("video_id") == "") |
        F.col("fecha_publicacion").isNull() |
        F.col("categoria").isNull() |
        ~F.col("categoria").isin("regalos", "comida asiática", "belleza", "juguetes")
    )
    if data.filter(invalid).limit(1).count():
        raise ValueError("Catálogo de publicaciones inválido")
    data = data.dropDuplicates()
    if data.groupBy("plataforma", "video_id").count().filter("count > 1").limit(1).count():
        raise ValueError("Publicaciones contradictorias para la misma clave")
    return data


def measurements(raw, posts):
    # El JSON conserva los campos originales para explicar cada rechazo.
    data = raw.withColumn("original", F.to_json(F.struct(*[F.col(c) for c in MEDICIONES])))
    data = data.withColumn("plataforma", F.lower(F.trim("plataforma")))
    data = data.withColumn("video_id", F.trim("video_id"))
    data = data.withColumn("fecha_medicion", F.expr("try_cast(fecha_medicion as date)"))
    data = data.withColumn("version_origen", F.expr("try_cast(version_origen as int)"))
    for column in METRICS:
        data = data.withColumn(column, F.expr(f"try_cast({column} as bigint)"))
    data = data.join(posts.select("plataforma", "video_id", "fecha_publicacion"),
                     ["plataforma", "video_id"], "left")
    reason = (F.when(F.col("plataforma").isNull() | F.col("video_id").isNull() |
                     (F.col("video_id") == ""), "clave ausente")
              .when(F.col("fecha_medicion").isNull(), "fecha inválida")
              .when(F.col("version_origen").isNull() | (F.col("version_origen") < 1),
                    "versión inválida")
              .when(F.col("fecha_publicacion").isNull(), "vídeo desconocido")
              .when(F.col("fecha_medicion") < F.col("fecha_publicacion"), "medición anterior a publicación"))
    for column in METRICS:
        reason = reason.when(F.col(column).isNull(), f"{column} ausente o ilegible")
        reason = reason.when(F.col(column) < 0, f"{column} negativo")
    data = data.withColumn("motivo", reason)
    rejects = data.filter("motivo IS NOT NULL").select("original", "motivo").dropDuplicates()
    good = data.filter("motivo IS NULL").select(*MEDICIONES).dropDuplicates()
    conflicts = good.groupBy(*(KEY + ["version_origen"])).count().filter("count > 1")
    if conflicts.limit(1).count():
        raise ValueError("Misma clave y versión con métricas diferentes")
    window = Window.partitionBy(*KEY).orderBy(F.col("version_origen").desc())
    latest = good.withColumn("_rank", F.row_number().over(window)).filter("_rank = 1").drop("_rank")
    return latest, rejects


def merge_measurements(spark, source, target):
    if not spark.catalog.tableExists(target):
        source.limit(0).write.format("delta").saveAsTable(target)
    # Una versión ya aceptada debe tener un contenido único.
    current = spark.table(target)
    same = source.alias("s").join(current.alias("d"), KEY + ["version_origen"])
    changed = None
    for column in METRICS:
        differs = ~F.col(f"s.{column}").eqNullSafe(F.col(f"d.{column}"))
        changed = differs if changed is None else changed | differs
    if same.filter(changed).limit(1).count():
        raise ValueError("Conflicto con una versión ya almacenada")
    condition = " AND ".join(f"s.{c} = d.{c}" for c in KEY)
    (DeltaTable.forName(spark, target).alias("d").merge(source.alias("s"), condition)
     .whenMatchedUpdateAll(condition="s.version_origen > d.version_origen")
     .whenNotMatchedInsertAll().execute())


def gold_tables(measurements_df, posts):
    video = measurements_df.join(posts, ["plataforma", "video_id"])
    video = video.withColumn("edad_dias", F.datediff("fecha_medicion", "fecha_publicacion"))
    video = video.withColumn("interacciones", F.col("me_gusta") + F.col("comentarios") + F.col("compartidos"))
    video = video.withColumn("tasa_interaccion", F.when(F.col("reproducciones") > 0,
                                                     100.0 * F.col("interacciones") / F.col("reproducciones")))
    timeline = Window.partitionBy("plataforma", "video_id").orderBy("fecha_medicion")
    video = video.withColumn("crecimiento", F.col("reproducciones") - F.lag("reproducciones").over(timeline))
    video = video.withColumn("descenso_acumulado", F.coalesce(F.col("crecimiento") < 0, F.lit(False)))
    category = video.filter("edad_dias = 3").groupBy("plataforma", "categoria").agg(
        F.count("*").alias("videos"), F.sum("reproducciones").alias("reproducciones"),
        F.sum("interacciones").alias("interacciones"))
    category = category.withColumn("tasa_interaccion", F.when(F.col("reproducciones") > 0,
                                      100.0 * F.col("interacciones") / F.col("reproducciones")))
    latest = video.withColumn("_rank", F.row_number().over(
        Window.partitionBy("plataforma", "video_id").orderBy(F.col("fecha_medicion").desc())))
    platform = latest.filter("_rank = 1").groupBy("plataforma").agg(
        F.count("*").alias("videos"), F.sum("reproducciones").alias("reproducciones"),
        F.sum("interacciones").alias("interacciones"))
    return {"por_video": video, "por_categoria": category, "por_plataforma": platform}
