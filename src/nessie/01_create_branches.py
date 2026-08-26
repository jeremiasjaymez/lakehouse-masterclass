"""
LAB 3 — Crear las ramas dev, staging y prod en Nessie (API REST).

Las ramas se crean desde el tip de main, igual que un `git branch`.
"""

import requests

BASE = "http://localhost:19120/api/v1"


def get_hash(branch="main"):
    r = requests.get(f"{BASE}/trees/tree/{branch}")
    r.raise_for_status()
    return r.json()["hash"]


def create_branch(name, source="main"):
    source_hash = get_hash(source)
    r = requests.post(
        f"{BASE}/trees/tree",
        params={"sourceRefName": source},
        json={"type": "BRANCH", "name": name, "hash": source_hash},
    )
    if r.status_code == 200:
        print(f"  ✓ rama '{name}' creada desde '{source}' @ {source_hash[:12]}...")
    elif r.status_code == 409:
        # Correr el script dos veces es normal: la rama ya está, no es un error.
        print(f"  · rama '{name}' ya existía, la dejamos como está")
    else:
        print(f"  ✗ no pude crear '{name}': {r.status_code} {r.text}")


create_branch("dev")
create_branch("staging")
create_branch("prod")

# Verificamos que quedaron las cuatro
refs = requests.get(f"{BASE}/trees").json()["references"]
print("\nRamas en Nessie:")
for ref in refs:
    print(f"  {ref['name']}")
