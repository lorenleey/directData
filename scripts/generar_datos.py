import csv
import random
from datetime import date, timedelta
from pathlib import Path

rng = random.Random(750)
inicio = date(2026, 11, 1)
carpeta = Path(__file__).resolve().parents[1] / "data/sample"
campos = ["plataforma", "video_id", "fecha_medicion", "version_origen",
          "reproducciones", "me_gusta", "comentarios", "compartidos"]
vistas = [0] * 40

publicaciones = carpeta / "publicaciones"
publicaciones.mkdir(parents=True, exist_ok=True)
with (publicaciones / "publicaciones.csv").open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(["plataforma", "video_id", "fecha_publicacion", "categoria", "titulo"])
    for i in range(40):
        fecha_publicacion = inicio - timedelta(days=(i // 2) % 3)
        categorias = ("regalos", "comida asiática", "belleza", "juguetes")
        categoria = categorias[(i // 2 + i % 2) % 4]
        if i == 0:
            categoria = "Regalos "  # Silver aplicará lower(trim(categoria)).
        escritor.writerow([("tiktok", "instagram")[i % 2], f"V{i // 2:03}",
                           fecha_publicacion, categoria,
                           f"Vídeo de tienda {i + 1}"])

for dia in range(12):
    lote = {0: "lote_01", 1: "lote_02"}.get(dia, "lote_03")
    destino = carpeta / lote
    destino.mkdir(parents=True, exist_ok=True)
    fecha = inicio + timedelta(days=dia)
    with (destino / f"mediciones_{fecha}.csv").open(
        "w", newline="", encoding="utf-8"
    ) as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(campos)
        for i in range(40):
            if i == 0 and dia >= 2:
                continue
            if i == 0:
                vistas[i] = [1000, 1200][dia]
            else:
                vistas[i] += rng.randint(5, 180)
            plataforma = ("tiktok", "instagram")[i % 2]
            escritor.writerow([plataforma, f"V{i // 2:03}", fecha, 1, vistas[i],
                               vistas[i] // 20, vistas[i] // 70, vistas[i] // 90])

with (carpeta / "lote_03" / "video_desconocido.csv").open(
    "w", newline="", encoding="utf-8"
) as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(campos)
    escritor.writerow(["tiktok", "V999", inicio + timedelta(days=2), 1, 100, 5, 1, 1])

correccion = carpeta / "lote_correccion"
correccion.mkdir(parents=True, exist_ok=True)
with (correccion / "correccion_dia_1.csv").open(
    "w", newline="", encoding="utf-8"
) as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(campos)
    escritor.writerow(["tiktok", "V000", inicio, 2, 950, 47, 13, 10])

reenvio = carpeta / "lote_reenvio"
reenvio.mkdir(parents=True, exist_ok=True)
with (reenvio / "reenvio_dia_1_v1.csv").open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(campos)
    escritor.writerow(["tiktok", "V000", inicio, 1, 1000, 50, 14, 11])
# Casos de calidad separados de los lotes que muestran 40 y 80 filas válidas.
calidad = carpeta / "lote_calidad"
calidad.mkdir(parents=True, exist_ok=True)
with (calidad / "calidad.csv").open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(campos)
    escritor.writerows([
        ["tiktok", "V001", inicio, 1, "", 1, 1, 1],
        ["tiktok", "V001", inicio, 1, "muchas", 1, 1, 1],
        ["tiktok", "V001", inicio, 1, -10, 1, 1, 1],
        ["tiktok", "", inicio, 1, 10, 1, 1, 1],
        ["tiktok", "V999", inicio, 1, 10, 1, 1, 1],
        ["tiktok", "V000", inicio, 1, 1000, 50, 14, 11],
        ["tiktok", "V000", inicio, 1, 1000, 50, 14, 11],
    ])
# Error de cabecera aislado para demostrar el fallo antes de Bronze.
fallo = carpeta / "lote_fallo"
fallo.mkdir(parents=True, exist_ok=True)
with (fallo / "cabecera_incorrecta.csv").open("w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo, lineterminator="\n")
    escritor.writerow(campos[:-1])
    escritor.writerow(["tiktok", "V000", inicio, 1, 1000, 50, 14])
print("Datos generados en", carpeta.resolve())
