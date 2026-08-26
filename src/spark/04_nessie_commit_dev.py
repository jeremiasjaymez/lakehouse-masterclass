"""
LAB 3 — Ramas y commits en Nessie (vía Iceberg REST Catalog)
=============================================================
Qué hace:
  1. Carga data/bronze/people.csv en nessie.bronze.people (rama main).
  2. Crea la rama dev a partir de main.
  3. Aplica un UPDATE SOLO en dev.
  4. Muestra main y dev lado a lado: main queda intacta.

Con el protocolo REST la rama se elige por configuración de catálogo, no con
`USE REFERENCE`. Por eso registramos un catálogo por rama (nessie_main,
nessie_dev) y podemos compararlas en la misma sesión de Spark.
"""

import requests
from utils import get_spark_multibranch

BASE = "http://localhost:19120/api/v1"


def branch_hash(ref: str) -> str:
    resp = requests.get(f"{BASE}/trees/tree/{ref}", timeout=30)
    resp.raise_for_status()
    return resp.json()["hash"]


def recreate_branch(name: str, source: str = "main") -> None:
    """Borra la rama si existe y la vuelve a crear desde `source`."""
    try:
        existing = branch_hash(name)
        requests.delete(
            f"{BASE}/trees/branch/{name}",
            params={"expectedHash": existing},
            timeout=30,
        )
        print(f"  rama '{name}' anterior eliminada")
    except requests.HTTPError:
        pass

    resp = requests.post(
        f"{BASE}/trees/tree",
        params={"sourceRefName": source},
        json={"type": "BRANCH", "name": name, "hash": branch_hash(source)},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"  rama '{name}' creada desde '{source}'")


# ── 1. Semilla en main ───────────────────────────────────────────────────────
spark = get_spark_multibranch("nessie-branches", refs=("main", "dev"))
spark.sparkContext.setLogLevel("ERROR")

print("\n=== 1. Cargando bronze en la rama MAIN ===")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie_main.bronze")
people = spark.read.csv("data/bronze/people.csv", header=True, inferSchema=True)
people.writeTo("nessie_main.bronze.people").createOrReplace()
print(f"  nessie.bronze.people cargada con {people.count()} filas")

# ── 2. Crear dev DESPUÉS de que la tabla existe en main ──────────────────────
print("\n=== 2. Creando la rama DEV ===")
recreate_branch("dev", source="main")

# ── 3. El commit: UPDATE solo en dev ────────────────────────────────────────
print("\n=== 3. UPDATE aplicado SOLO en DEV ===")
spark.sql("UPDATE nessie_dev.bronze.people SET name = 'Jeremias DEV' WHERE id = 1")
print("  UPDATE aplicado -> nuevo commit en dev")

# ── 4. Comparación lado a lado ──────────────────────────────────────────────
print("\n=== 4. MAIN (sin cambios) ===")
spark.sql("SELECT id, name FROM nessie_main.bronze.people ORDER BY id LIMIT 3").show()

print("=== 4. DEV (con el UPDATE) ===")
spark.sql("SELECT id, name FROM nessie_dev.bronze.people ORDER BY id LIMIT 3").show()

print("=== Commits de la rama DEV ===")
log = requests.get(f"{BASE}/trees/tree/dev/log", timeout=30).json()
for entry in log.get("logEntries", [])[:3]:
    meta = entry.get("commitMeta", {})
    print(f"  {entry.get('hash', '')[:12]}...  {meta.get('message', '')}")

spark.stop()
