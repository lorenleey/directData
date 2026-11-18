import csv
from pathlib import Path

PUBLICACIONES = ["plataforma", "video_id", "fecha_publicacion", "categoria", "titulo"]
MEDICIONES = ["plataforma", "video_id", "fecha_medicion", "version_origen",
              "reproducciones", "me_gusta", "comentarios", "compartidos"]
KEY = ["plataforma", "video_id", "fecha_medicion"]
METRICS = MEDICIONES[4:]


def validate_headers(directory, expected):
    files = sorted(Path(directory).rglob("*.csv"))
    if not files:
        raise ValueError(f"No hay CSV en {directory}")
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), [])
        if header != expected:
            raise ValueError(f"Cabecera incorrecta en {path.name}: {header}")
    return files
