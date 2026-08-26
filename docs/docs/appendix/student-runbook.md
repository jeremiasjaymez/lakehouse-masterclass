# Recorrido del alumno (runbook paso a paso)

Esta página es el curso entero como una secuencia de comandos, en orden, con lo que
tenés que ver en cada uno. Sirve para dos cosas:

- **Hacer el curso** de punta a punta sin perderte entre labs.
- **Testear el repo**: si todos los checkpoints de acá dan verde, el material funciona.

!!! tip "Cómo usar esta página"
    Cada bloque tiene un **objetivo**, los **comandos** y un **checkpoint**. No pases
    al bloque siguiente hasta que el checkpoint dé verde: casi todos los problemas
    de los labs siguientes son en realidad un bloque anterior a medias.

## Regla de oro para testear

Ejecutá los comandos **desde la raíz del repo** y con el entorno activado:

```bash
cd ~/repos/lakehouse-masterclass
source .venv/bin/activate
```

Los scripts leen rutas relativas (`data/bronze/people.csv`), así que correrlos desde
otra carpeta falla con `FileNotFoundError`.

---

## Bloque 0 — Pre-work (hacelo una sola vez)

**Objetivo**: tener la máquina lista sin descargar nada en el medio del curso.

Seguí el [Lab 0](../labs/lab-00-setup-global.md) completo y después:

```bash
uv sync                                   # dependencias Python
docker compose pull                       # imágenes MinIO + Nessie + Vault
ollama pull llama3.1                      # ~4.7 GB
ollama pull nomic-embed-text              # ~275 MB
python src/spark/01_test_spark.py         # cachea ~300 MB de jars en ~/.ivy2/
```

**Checkpoint**

```bash
docker --version && uv --version && ollama list
```

Tenés que ver los dos modelos listados. Este bloque baja ~10 GB: es el más lento de
todos y el único que conviene hacer la noche anterior.

⏱️ **20-60 min** según tu conexión.

---

## Bloque 1 — Storage y table format (Labs 1 y 2)

**Objetivo**: MinIO andando, un bucket, y una tabla Iceberg con time travel.

```bash
docker compose up -d
docker ps
```

Creá los buckets `bronze`, `silver` y `gold` desde la consola
(<http://localhost:9001>, usuario `admin` / `password`), como indica el
[Lab 1](../labs/lab-01-minio.md).

```bash
python src/minio/test_minio.py            # sube people.csv a bronze
python src/spark/02_create_people_table.py   # crea iceberg.bronze_people
python src/duckdb/01_read_people_table.py    # DuckDB lee POR RUTA
python src/spark/03_insert_people_table.py   # segundo snapshot (17 filas)
python src/duckdb/02_read_snapshot_version.py
python src/duckdb/03_read_people_table_as_version.py   # time travel al primero
```

**Checkpoint**

- `test_minio.py` imprime `Archivo descargado correctamente.`
- `01_read_people_table.py` imprime `Tabla leída correctamente: 15 filas`.
- `02_read_snapshot_version.py` lista **2 o más** `snapshot_id`.
- `03_read_people_table_as_version.py` viaja al snapshot viejo y muestra **15 filas**:
  Gaston y Gonzalo no aparecen.

!!! note "Lo que tenés que registrar de este bloque"
    DuckDB leyó con `iceberg_scan('s3://bronze/iceberg/warehouse/bronze_people')`:
    **una ruta**. Acordate de esta incomodidad, porque el Lab 3 la resuelve.

⏱️ **30-40 min** (la primera corrida de Spark baja jars).

---

## Bloque 2 — El catálogo (Lab 3)

**Objetivo**: Nessie como Iceberg REST Catalog, con ramas.

```bash
docker compose up -d nessie
curl http://localhost:19120/api/v1/trees
python src/nessie/01_create_branches.py
python src/spark/04_nessie_commit_dev.py
```

**Checkpoint** — el final de `04_nessie_commit_dev.py` tiene que mostrar:

```text
=== 4. MAIN (sin cambios) ===
|  1|Jeremias|
=== 4. DEV (con el UPDATE) ===
|  1|Jeremias DEV|
```

La **misma tabla**, `nessie.bronze.people`, con dos contenidos al mismo tiempo. Si
ves eso, el catálogo versionado funciona.

```bash
python src/spark/08_read_iceberg_nessie_people.py   # lee la rama dev
python src/nessie/02_merge_dev_to_staging.py
curl http://localhost:19120/api/v1/trees/tree/staging/log
```

!!! warning "Si Nessie no levanta"
    ```bash
    docker logs nessie | tail -20
    ```
    Nessie necesita MinIO corriendo (administra el warehouse en S3) y guarda su
    estado en el volumen `nessie-data`.

⏱️ **30-40 min**.

---

## Bloque 3 — Compute (Lab 4)

**Objetivo**: el ETL bronze → silver, ya sobre el catálogo versionado.

```bash
python src/spark/06_read_iceberg_people.py
python src/spark/07_etl_bronze_to_silver.py
python src/duckdb/05_attach_nessie_catalog.py
```

**Checkpoint**

- `07` imprime `Tabla silver_people creada con 15 filas`.
- `05_attach_nessie_catalog.py` lista las tablas **por nombre**:

```text
   nessie.bronze.people
   nessie.silver.people
   nessie.silver.people_partitioned
```

!!! success "El contraste con el Bloque 1"
    En el Lab 2 DuckDB necesitaba la ruta completa en S3. Ahora pregunta *qué tablas
    existen* y le responde el catálogo. Esa es la diferencia entre un montón de
    archivos y un Lakehouse.

⏱️ **20-30 min**.

---

## Bloque 4 — Orquestación (Lab 5)

**Objetivo**: los mismos pasos, pero declarados como assets con lineage.

```bash
cp lakehouse_dagster/.env.example lakehouse_dagster/.env
# editá DAGSTER_HOME con la ruta ABSOLUTA de tu repo
mkdir -p .dagster                 # Dagster no crea este directorio solo
cd lakehouse_dagster && dagster dev
```

En <http://localhost:3000> → **Assets** → materializá `gold_people`.

**Checkpoint**: Dagster ejecuta `bronze_people → silver_people → gold_people` en ese
orden, y el grafo de lineage muestra las flechas. Después:

```bash
cd lakehouse_dagster && uv run --extra dev pytest -v
```

Tienen que pasar los 5 tests.

⏱️ **30-40 min**.

---

## Bloque 5 — Secretos, IaC y CI (Labs 6, 7 y 8)

**Objetivo**: sacar las credenciales del código y declarar la infra.

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root
python src/vault/read_secrets.py
python src/spark/09_spark_with_vault.py
```

**Checkpoint**: `09` termina con
`OK ✅ — 15 filas leídas usando credenciales de Vault`.

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply -auto-approve
cd ../..
```

**Checkpoint**: `terraform apply` termina sin error y crea el bucket `platinum`
(los otros tres los adopta con bloques `import`).

Para el Lab 8, pusheá y mirá que los tres workflows queden en verde.

⏱️ **40-50 min**.

---

## Bloque 6 — IA (Lab 9)

**Objetivo**: embeddings locales guardados como columna en Iceberg.

```bash
python src/ai/generate_embeddings.py
python src/spark/10_save_embeddings_iceberg.py
python src/spark/11_read_iceberg_people_embeddings.py
python src/ai/sql_generator.py
python src/spark/12_run_generated_sql.py
```

**Checkpoint**

- `generate_embeddings.py` dice `Embeddings generados para 15 filas`.
- `11` muestra la columna `embedding` con arrays de floats (768 dimensiones).
- `12` imprime el SQL generado y lo ejecuta.

!!! warning "El LLM se equivoca, y está bien"
    `12_run_generated_sql.py` a veces genera SQL con una columna inventada o un
    filtro que no matchea nada y devuelve 0 filas. **No es un bug del lab**: es la
    lección sobre qué garantías te da (y cuáles no) un text-to-SQL. Volvé a correrlo.

⏱️ **20-30 min**.

---

## Bloque 7 — Capstone y RAG (Labs 10 y 11)

**Objetivo**: el pipeline completo y el bonus de RAG.

Recorré el [Lab 10](../labs/lab-10-capstone.md) de punta a punta — a esta altura ya
corriste casi todos los pasos, así que sirve como repaso y verificación.

```bash
python src/ai/ask_llm_without_rag.py "¿En qué lab se configura Nessie?"
python src/spark/13_save_rag_index_iceberg.py
python src/spark/14_rag_answer_from_iceberg.py "¿En qué lab se configura Nessie?"
```

**Checkpoint**

- `13` termina con `Tabla gold_knowledge_chunks guardada con NNN chunks` (unos 200+).
- `14` responde **y lista las fuentes**, empezando por `lab-03-nessie.md`.

Compará la respuesta sin RAG con la respuesta con RAG: ese contraste es el lab.

⏱️ **30-40 min** (el indexado de embeddings es lo más lento).

---

## Volver a cero

Para repetir el curso desde limpio, o si algo quedó en un estado raro. Hay un script
que hace todos los pasos:

```bash
./scripts/reset-environment.sh --dry-run   # mostrar qué haría, sin tocar nada
./scripts/reset-environment.sh             # ejecutar, pidiendo confirmación
```

Borra el estado **derivado** y preserva lo que cuesta caro volver a tener:

| Se borra | Se preserva |
|---|---|
| Los dos warehouses en MinIO | Los buckets (bronze, silver, gold, platinum) |
| El volumen `nessie-data` (ramas y commits) | `data/bronze/people.csv` (el dataset, versionado) |
| Los secretos de Vault (modo dev) | `~/.ivy2/` (~300 MB de jars de Spark) |
| `spark-warehouse/`, `iceberg_catalog.db`, `.dagster/` | Los modelos de Ollama (~5 GB) |
| Los artefactos de `data/` (descargas, embeddings) | |

Al final valida solo: Nessie tiene que quedar con **una sola rama, `main`**, y el
secreto `minio` re-sembrado en Vault.

!!! warning "Hay DOS warehouses, no uno"
    Es el error más fácil de cometer al resetear a mano. El Lab 2 usa el catálogo
    `hadoop` (`bronze/iceberg/warehouse/`) y del Lab 3 en adelante todo vive en el
    warehouse que administra Nessie (`bronze/iceberg/nessie-warehouse/`). Si borrás
    solo el segundo, el Lab 2 arranca con los snapshots de tu corrida anterior y el
    checkpoint de time travel te va a mostrar datos de otro día.

### Qué hace por dentro

Si preferís correrlo a mano, o querés entender qué toca cada paso:

```bash
# 1. Bajar todo y borrar el estado de Nessie (el -v es lo que borra las ramas)
docker compose down -v

# 2. Levantar solo MinIO para poder limpiar los buckets
docker compose up -d minio

# 3. Vaciar los DOS warehouses con boto3 (los buckets NO se borran).
#    Prefijos: iceberg/nessie-warehouse/ , iceberg/warehouse/ , people.csv

# 4. Estado derivado local
rm -rf spark-warehouse iceberg_catalog.db .dagster
rm -f data/bronze/people_downloaded.csv data/silver/people_with_embeddings.json

# 5. Volver a levantar y re-sembrar los secretos
docker compose up -d
docker exec vault vault kv put secret/minio access_key=admin secret_key=password
docker exec vault vault kv put secret/nessie user=admin password=admin
```

El paso 5 hace falta porque Vault corre en **modo dev**: guarda todo en memoria y el
`down` del paso 1 se lleva los secretos puestos. Si ya hiciste el Lab 7, en vez de los
`kv put` podés correr `terraform apply` — que es exactamente el punto de ese lab.

**Validar a mano**

```bash
curl -s http://localhost:19120/api/v1/trees | python3 -m json.tool | grep '"name"'
```

Tiene que aparecer **solo `main`**. Si ves `dev`, `staging` o `prod`, el volumen de
Nessie no se borró: revisá que hayas corrido `down -v` con el `-v`.

!!! danger "Lo que NO hay que borrar"
    - **`minio-data/`** — ahí viven tus buckets. Si lo borrás, tenés que volver a crear
      `bronze`, `silver`, `gold` y `platinum` antes de seguir.
    - **`data/bronze/people.csv`** — es el dataset del curso y está versionado. Si lo
      pisaste sin querer: `git checkout -- data/bronze/people.csv`.
    - **`~/.ivy2/`** — los ~300 MB de jars de Spark. Borrarlo solo agrega 3 minutos
      a tu próxima corrida.
    - **Los modelos de Ollama** — son ~5 GB, no los bajes de nuevo.

---

## Tabla resumen de tiempos

| Bloque | Labs | Tiempo |
|---|---|---|
| 0 - Pre-work | 0 | 20-60 min |
| 1 - Storage y table format | 1, 2 | 30-40 min |
| 2 - Catálogo | 3 | 30-40 min |
| 3 - Compute | 4 | 20-30 min |
| 4 - Orquestación | 5 | 30-40 min |
| 5 - Secretos, IaC, CI | 6, 7, 8 | 40-50 min |
| 6 - IA | 9 | 20-30 min |
| 7 - Capstone y RAG | 10, 11 | 30-40 min |

**Total sin el pre-work: ~4 h.** Con el pre-work hecho aparte, entra cómodo en una
jornada de trabajo.

---

## Los tres errores más comunes

**1. `FileNotFoundError: data/bronze/people.csv`**
Estás corriendo el script desde otra carpeta. Volvé a la raíz del repo.

**2. `NoSuchNamespaceException` al escribir una tabla nueva**
Con el catálogo REST los namespaces no se crean solos:

```python
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")
```

**3. La primera corrida de Spark parece colgada**
Está bajando ~300 MB de jars a `~/.ivy2/`. Tarda 2-3 minutos **una sola vez**.
