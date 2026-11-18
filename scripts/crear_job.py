"""Genera el JSON para Jobs API con rutas reales del workspace."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--workspace-path", required=True, help="Ruta del Git folder, /Workspace/Users/.../directData")
parser.add_argument("--catalogo", default="workspace")
args = parser.parse_args()
names = ["validar", "bronze", "silver", "comprobar", "gold"]
files = ["01_validar", "02_bronze", "03_silver", "04_comprobar", "05_gold"]
tasks = []
for index, (name, file) in enumerate(zip(names, files)):
    task = {"task_key": name, "timeout_seconds": 1800, "max_retries": 0,
            "notebook_task": {"notebook_path": f"{args.workspace_path.rstrip('/')}/notebooks/{file}",
                              "source": "WORKSPACE",
                              "base_parameters": {"catalogo": args.catalogo,
                                                  "run_id": "{{job.run_id}}"}}}
    if index:
        task["depends_on"] = [{"task_key": names[index - 1]}]
    tasks.append(task)
job = {"name": "DirectData", "max_concurrent_runs": 1,
       "queue": {"enabled": True},
       "parameters": [{"name": "lote", "default": "lote_01"},
                      {"name": "prefijo", "default": "directdata"}],
       "tasks": tasks}
destination = Path(__file__).resolve().parents[1] / "jobs" / "directdata.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
print(destination)
