"""
LAB 3, PASO 8 — Merge dev → staging (Nessie REST API)
=====================================================
Aplica todos los commits de la rama dev sobre staging.
La rama dev permanece intacta.

Nota: expectedHash es un query-param (no va en el body).
"""

import requests

BASE = "http://localhost:19120/api/v1"


def get_hash(branch: str) -> str:
    r = requests.get(f"{BASE}/trees/tree/{branch}")
    r.raise_for_status()
    return r.json()["hash"]


def get_log(branch: str) -> list:
    r = requests.get(f"{BASE}/trees/tree/{branch}/log")
    r.raise_for_status()
    return r.json().get("logEntries", [])


# ── Si staging no tiene commits en común con dev, la recreamos desde main.
#    (Ocurre cuando staging fue creada antes de que existiera cualquier commit.)
staging_log = get_log("staging")
if not staging_log:
    print(
        "  ℹ staging no tiene commits — la recreamos desde main para compartir ancestro."
    )
    staging_hash = get_hash("staging")
    main_hash = get_hash("main")
    # Asignamos staging al tip de main
    r = requests.put(
        f"{BASE}/trees/branch/staging",
        params={"expectedHash": staging_hash},
        json={"type": "BRANCH", "name": "staging", "hash": main_hash},
    )
    r.raise_for_status()
    print(f"  ✓ staging reapuntada a main ({main_hash[:12]}...)\n")

# Estado previo
print("=" * 55)
print("  Estado ANTES del merge")
print("=" * 55)
for branch in ("dev", "staging"):
    h = get_hash(branch)
    print(f"  {branch:10s} → {h[:12]}...")

# Merge dev → staging
# expectedHash va como query-param (requerido por la API v1)
staging_hash = get_hash("staging")
dev_hash = get_hash("dev")

r = requests.post(
    f"{BASE}/trees/branch/staging/merge",
    params={"expectedHash": staging_hash},
    json={"fromRefName": "dev", "fromHash": dev_hash},
)

print(f"\nPOST /trees/branch/staging/merge  →  {r.status_code}")
if r.status_code in (200, 204):
    print("  ✓ Merge exitoso")
else:
    print(f"  ✗ Error: {r.text}")
    raise SystemExit(1)

# Estado posterior
print("\n" + "=" * 55)
print("  Estado DESPUÉS del merge")
print("=" * 55)
for branch in ("dev", "staging"):
    h = get_hash(branch)
    print(f"  {branch:10s} → {h[:12]}...")

# Commits recientes en staging
print("\n" + "=" * 55)
print("  Últimos commits en staging")
print("=" * 55)
log = requests.get(f"{BASE}/trees/tree/staging/log").json()
for entry in log.get("logEntries", [])[:5]:
    meta = entry.get("commitMeta", {})
    print(f"  hash   : {entry.get('hash', '')[:12]}...")
    print(f"  mensaje: {meta.get('message', '')}")
    print(f"  fecha  : {meta.get('commitTime', '')}")
    print()
