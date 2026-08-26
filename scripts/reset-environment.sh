#!/usr/bin/env bash
#
# reset-environment.sh — devolver el Lakehouse al estado inicial.
#
# Borra el estado DERIVADO (tablas, ramas, snapshots, embeddings) y deja intacto
# lo que cuesta caro volver a tener (buckets, jars de Spark, modelos de Ollama).
#
#   ./scripts/reset-environment.sh --dry-run   # mostrar qué haría, sin tocar nada
#   ./scripts/reset-environment.sh             # ejecutar, pidiendo confirmación
#   ./scripts/reset-environment.sh --yes       # ejecutar sin preguntar
#
# Ver el apéndice "Volver a cero" del runbook para el detalle de cada paso.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DRY_RUN=false
ASSUME_YES=false

for arg in "$@"; do
    case "$arg" in
        --dry-run|-n) DRY_RUN=true ;;
        --yes|-y)     ASSUME_YES=true ;;
        --help|-h)
            cat <<'AYUDA'
reset-environment.sh — devolver el Lakehouse al estado inicial.

Borra el estado DERIVADO (tablas, ramas, snapshots, embeddings) y deja intacto
lo que cuesta caro volver a tener (buckets, jars de Spark, modelos de Ollama).

  ./scripts/reset-environment.sh --dry-run   mostrar qué haría, sin tocar nada
  ./scripts/reset-environment.sh             ejecutar, pidiendo confirmación
  ./scripts/reset-environment.sh --yes       ejecutar sin preguntar

Ver el apéndice "Volver a cero" del runbook para el detalle de cada paso.
AYUDA
            exit 0
            ;;
        *)
            echo "Opción desconocida: $arg (probá --help)" >&2
            exit 2
            ;;
    esac
done

# ── Colores solo si la salida es una terminal ────────────────────────────────
if [[ -t 1 ]]; then
    BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'
    GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
    BOLD=''; DIM=''; RED=''; GREEN=''; YELLOW=''; RESET=''
fi

step() { echo; echo "${BOLD}▸ $*${RESET}"; }
info() { echo "  $*"; }
ok()   { echo "  ${GREEN}✓${RESET} $*"; }
warn() { echo "  ${YELLOW}!${RESET} $*"; }
die()  { echo "${RED}✗ $*${RESET}" >&2; exit 1; }

# En dry-run mostramos el comando en vez de ejecutarlo.
run() {
    if $DRY_RUN; then
        echo "  ${DIM}\$ $*${RESET}"
    else
        "$@"
    fi
}

# ── Intérprete de Python con boto3 (el del proyecto) ─────────────────────────
if [[ -x .venv/bin/python ]]; then
    PY=(.venv/bin/python)
elif command -v uv >/dev/null 2>&1; then
    PY=(uv run --project . python)
else
    die "No encontré .venv/bin/python ni uv. Corré 'uv venv && uv sync' primero (Lab 0)."
fi

command -v docker >/dev/null 2>&1 || die "Docker no está instalado o no está en el PATH."

MINIO_URL="http://127.0.0.1:9000"
NESSIE_URL="http://localhost:19120"

# ── Qué se borra y qué no ────────────────────────────────────────────────────
cat <<EOF

${BOLD}Reset del entorno Lakehouse${RESET}
${DIM}$REPO_ROOT${RESET}

${BOLD}SE BORRA${RESET} (estado derivado — se regenera corriendo los labs)
  · MinIO   bronze/iceberg/nessie-warehouse/   tablas del catálogo Nessie
  · MinIO   bronze/iceberg/warehouse/          tablas del Lab 2 (catálogo hadoop)
  · MinIO   bronze/people.csv                  lo vuelve a subir el Lab 1
  · Docker  volumen nessie-data                ramas dev / staging / prod
  · Docker  secretos de Vault                  modo dev: viven en memoria
  · Local   spark-warehouse/  iceberg_catalog.db  .dagster/
  · Local   data/bronze/people_downloaded.csv
  · Local   data/silver/people_with_embeddings.json

${BOLD}SE PRESERVA${RESET}
  · Los buckets (bronze, silver, gold, platinum)
  · data/bronze/people.csv    ${DIM}← el dataset del curso, versionado en git${RESET}
  · ~/.ivy2/                  ${DIM}← ~300 MB de jars de Spark${RESET}
  · Los modelos de Ollama     ${DIM}← ~5 GB${RESET}
EOF

if $DRY_RUN; then
    echo
    warn "${BOLD}DRY RUN${RESET} — no se va a tocar nada."
elif ! $ASSUME_YES; then
    echo
    read -r -p "¿Seguimos? [s/N] " respuesta
    case "$respuesta" in
        [sSyY]) ;;
        *) echo "Cancelado."; exit 0 ;;
    esac
fi

# ── 1. Bajar servicios y borrar el estado de Nessie ──────────────────────────
step "1/5  Bajando servicios y borrando el estado de Nessie"
info "El -v borra el volumen nessie-data, donde viven las ramas y los commits."
run docker compose down -v

# ── 2. Levantar MinIO solo, para poder limpiar los buckets ───────────────────
step "2/5  Levantando MinIO para limpiar los buckets"
run docker compose up -d minio

if ! $DRY_RUN; then
    info "Esperando a que MinIO responda..."
    for _ in $(seq 1 30); do
        if curl -sf "$MINIO_URL/minio/health/live" >/dev/null 2>&1; then break; fi
        sleep 1
    done
    curl -sf "$MINIO_URL/minio/health/live" >/dev/null 2>&1 \
        || die "MinIO no respondió en 30s. Revisá 'docker logs minio'."
    ok "MinIO respondiendo"
fi

# ── 3. Vaciar los DOS warehouses ─────────────────────────────────────────────
# Ojo: son dos. El Lab 2 escribe en iceberg/warehouse/ (catálogo hadoop) y del
# Lab 3 en adelante todo va a iceberg/nessie-warehouse/. Borrar solo el segundo
# deja los snapshots viejos del Lab 2 y el time travel muestra datos de otra corrida.
step "3/5  Vaciando los warehouses en MinIO (los buckets quedan)"
if $DRY_RUN; then
    echo "  ${DIM}\$ ${PY[*]}  # borra vía boto3, con estos prefijos del bucket 'bronze':${RESET}"
    echo "  ${DIM}      iceberg/nessie-warehouse/${RESET}"
    echo "  ${DIM}      iceberg/warehouse/${RESET}"
    echo "  ${DIM}      people.csv${RESET}"
else
    "${PY[@]}" - <<'PY'
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="password",
)

PREFIXES = ["iceberg/nessie-warehouse/", "iceberg/warehouse/", "people.csv"]
total = 0

for prefix in PREFIXES:
    batch = []
    try:
        pages = s3.get_paginator("list_objects_v2").paginate(Bucket="bronze", Prefix=prefix)
        for page in pages:
            for obj in page.get("Contents", []):
                batch.append({"Key": obj["Key"]})
                if len(batch) == 1000:
                    s3.delete_objects(Bucket="bronze", Delete={"Objects": batch})
                    total += len(batch)
                    batch = []
        if batch:
            s3.delete_objects(Bucket="bronze", Delete={"Objects": batch})
            total += len(batch)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchBucket", "404"):
            print(f"  ! el bucket 'bronze' no existe todavía — nada que limpiar")
            break
        raise
    print(f"  ✓ {prefix}")

print(f"  objetos borrados: {total}")
PY
fi

# ── 4. Estado derivado local ─────────────────────────────────────────────────
step "4/5  Borrando el estado derivado local"
run rm -rf spark-warehouse iceberg_catalog.db .dagster
run rm -f data/bronze/people_downloaded.csv data/silver/people_with_embeddings.json
$DRY_RUN || ok "listo"

if [[ -f data/bronze/people.csv ]]; then
    ok "data/bronze/people.csv intacto ($(wc -l < data/bronze/people.csv) líneas)"
else
    warn "Falta data/bronze/people.csv — recuperalo con: git checkout -- data/bronze/people.csv"
fi

# ── 5. Volver a levantar y re-sembrar los secretos ───────────────────────────
# Vault corre en modo dev: guarda todo en memoria, así que el 'down' del paso 1
# se llevó los secretos. Sin esto, 09_spark_with_vault.py falla.
step "5/5  Levantando todo y re-sembrando los secretos de Vault"
run docker compose up -d

if ! $DRY_RUN; then
    info "Esperando a Vault..."
    for _ in $(seq 1 30); do
        if docker exec vault vault status >/dev/null 2>&1; then break; fi
        sleep 1
    done
fi

run docker exec vault vault kv put secret/minio access_key=admin secret_key=password
run docker exec vault vault kv put secret/nessie user=admin password=admin

# ── Validación ───────────────────────────────────────────────────────────────
step "Validación"
if $DRY_RUN; then
    echo "  ${DIM}\$ curl -s $NESSIE_URL/api/v1/trees   # tiene que listar solo 'main'${RESET}"
    echo
    warn "DRY RUN terminado — no se tocó nada."
    exit 0
fi

info "Esperando a Nessie..."
for _ in $(seq 1 45); do
    if curl -sf "$NESSIE_URL/api/v1/trees" >/dev/null 2>&1; then break; fi
    sleep 1
done

ramas=$("${PY[@]}" - <<PY
import json, urllib.request
try:
    with urllib.request.urlopen("$NESSIE_URL/api/v1/trees", timeout=10) as resp:
        data = json.load(resp)
    print(",".join(sorted(r["name"] for r in data.get("references", []))))
except Exception:
    print("<sin respuesta>")
PY
)

if [[ "$ramas" == "main" ]]; then
    ok "Nessie tiene solo la rama 'main'"
elif [[ "$ramas" == "<sin respuesta>" ]]; then
    warn "Nessie todavía no responde. Probá en unos segundos: curl $NESSIE_URL/api/v1/trees"
else
    warn "Nessie lista: $ramas"
    warn "Se esperaba solo 'main'. ¿Corriste el paso 1 con el flag -v?"
fi

secreto=$(docker exec vault vault kv get -field=access_key secret/minio 2>/dev/null || echo "")
[[ "$secreto" == "admin" ]] && ok "Secreto 'minio' sembrado en Vault" \
                            || warn "No pude leer el secreto 'minio' de Vault"

echo
echo "${GREEN}${BOLD}Entorno reseteado.${RESET} Arrancá de nuevo desde el Bloque 1 del runbook:"
echo "  ${DIM}python src/minio/test_minio.py${RESET}"
