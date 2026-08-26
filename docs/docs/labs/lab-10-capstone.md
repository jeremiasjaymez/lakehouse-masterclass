# LAB 10 - Capstone Project: Lakehouse Completo + IA Integrada

!!! tip
    En este capstone vas a construir un Lakehouse completo, automatizado, versionado, orquestado y enriquecido con IA, ejecutando un pipeline real de punta a punta.

## ¿Por qué un Capstone?

Cada lab por separado te muestra una pieza. El Capstone te obliga a ver el sistema **como un todo**: Docker Compose levanta los servicios, Terraform declara el estado inicial, Vault entrega secretos, Spark procesa sobre Iceberg en MinIO, Nessie versiona, Dagster orquesta, IA enriquece y CI/CD valida. Ese "click mental" de ver el flujo end-to-end es lo que diferencia a alguien que "tocó cada herramienta" de alguien que puede construir y razonar sobre el sistema completo.

## Objetivo del lab

- Levantar los servicios con Docker Compose y el estado inicial con Terraform.
- Cargar datos en MinIO (bronze).
- Crear tablas Iceberg y versionarlas con Nessie.
- Ejecutar ETLs Spark -> Iceberg.
- Orquestar todo con Dagster.
- Enriquecer datos con embeddings.
- Habilitar consultas en lenguaje natural con LLM local.
- Validar CI/CD.
- Ejecutar el pipeline completo end-to-end.

## Prerrequisitos

- LAB 0 a LAB 9 completados.
- Repositorio GitHub funcionando.
- Ollama instalado.
- Terraform instalado.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Arquitectura final del capstone

```text
               +-------------------+
               |     Terraform     |
               |  (Infra as Code)  |
               +---------+---------+
                         |
                         v
+---------+     +---------+---------+     +---------+
|  Vault  |     |      MinIO        |     |  Nessie |
|Secrets  |<--->|   (S3 Storage)    |<--->| Catalog |
+---------+     +---------+---------+     +---------+
                         |
                         v
                   +-----+------+
                   |   Iceberg  |
                   |  Tables    |
                   +-----+------+
                         |
                         v
                   +-----+------+
                   |   Spark    |
                   |  Compute   |
                   +-----+------+
                         |
                         v
                   +-----+------+
                   |  Dagster   |
                   |Orquestación|
                   +-----+------+
                         |
                         v
                   +-----+------+
                   |    IA      |
                   |Embeddings +|
                   |LLM (Ollama)|
                   +------------+
```

### PASO 1 - Levantar los servicios y el estado inicial

!!! warning "Terraform NO levanta contenedores"
    Es la confusión más común de este capstone. Terraform gestiona el **estado
    inicial** (buckets y secretos), no el runtime. Los contenedores los levanta
    Docker Compose. El orden importa:

**1) Contenedores (MinIO + Nessie + Vault)**

```bash
docker compose up -d
docker ps
```

Deberías ver `minio`, `nessie` y `vault` corriendo.

**2) Estado inicial declarativo (buckets + secreto de Vault)**

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # ajustá si cambiaste credenciales
terraform init
terraform apply -auto-approve
cd ../..
```

Esto crea/adopta los buckets `bronze`, `silver`, `gold`, `platinum` y siembra el
secreto `minio` en Vault.

!!! note
    Los buckets `bronze/silver/gold` los creaste a mano en el Lab 1. Por eso
    `main.tf` usa bloques `import {}`: le dicen a Terraform "adoptá este recurso,
    no lo crees de nuevo". `platinum` sí lo crea Terraform desde cero — es el
    ejemplo de recurso nuevo.

**Validar**

```bash
docker ps
terraform -chdir=infra/terraform output
```

### PASO 2 - Cargar datos en bronze (MinIO)

El dataset del curso está en `data/bronze/people.csv` (15 filas):

```csv
id,name,bio,department,country
1,Jeremias,"Data engineer apasionado por lakehouse y arquitecturas open-source",Engineering,Argentina
2,Franco,"Diseñador UX especializado en productos de datos",Product,Argentina
3,Matias,"Analista de datos con foco en analytics y visualización",Analytics,Mexico
...
```

**Subir a MinIO**

```bash
python src/minio/test_minio.py
```

El script sube `people.csv` al bucket `bronze`, lo vuelve a descargar como
`data/bronze/people_downloaded.csv` y lista el contenido del bucket.

### PASO 3 - (Opcional) Repaso del Lab 2: catálogo Hadoop

Este paso reproduce el escalón inicial — Iceberg sin servidor de catálogo:

```bash
python src/spark/02_create_people_table.py   # crea iceberg.bronze_people
python src/duckdb/01_read_people_table.py    # DuckDB lee por RUTA
```

Es útil para tener fresco el contraste con lo que viene. El pipeline del capstone
no depende de este paso.

### PASO 4 - Cargar bronze en Nessie y versionar con ramas

Acá arranca el pipeline de verdad. Todo lo que sigue vive en el catálogo `nessie`:

```bash
python src/nessie/01_create_branches.py      # crea dev, staging, prod
python src/spark/04_nessie_commit_dev.py     # carga bronze en main + UPDATE en dev
python src/nessie/02_merge_dev_to_staging.py # merge dev -> staging
```

`04_nessie_commit_dev.py` carga `data/bronze/people.csv` en `nessie.bronze.people`
(rama `main`), crea `dev`, aplica un `UPDATE` solo en `dev` y muestra las dos ramas
lado a lado.

**Validar**

```bash
curl http://localhost:19120/api/v1/trees
curl http://localhost:19120/api/v1/trees/tree/dev/log
```

### PASO 5 - Ejecutar ETL Spark (bronze -> silver)

```bash
python src/spark/07_etl_bronze_to_silver.py
```

El script agrega `name_upper` e `ingestion_ts`, escribe `nessie.silver.people` y
además genera `nessie.silver.people_partitioned` particionada por inicial del nombre:

```python
silver_df = bronze_df.withColumn("name_upper", F.upper(F.col("name"))).withColumn(
    "ingestion_ts", F.current_timestamp()
)
silver_df.writeTo("nessie.silver.people").createOrReplace()
```

### PASO 6 - Enriquecer datos con IA (embeddings)

**1) Generar los embeddings de la columna `bio`**

```bash
python src/ai/generate_embeddings.py
```

Deja `data/silver/people_with_embeddings.json` con vectores de 768 dimensiones
(`nomic-embed-text`).

**2) Guardarlos en Iceberg**

```bash
python src/spark/10_save_embeddings_iceberg.py
```

**3) Validar**

```bash
python src/spark/11_read_iceberg_people_embeddings.py
```

Deberías ver la columna `embedding` con arrays de floats.

### PASO 7 - Revisar los assets de Dagster

Los assets ya existen en el repo, organizados por capa (un paquete por capa, no un
único `pipeline.py`):

```text
lakehouse_dagster/lakehouse_dagster/assets/
├── bronze/bronze_people.py          → lee data/bronze/people.csv
├── silver/silver_people.py          → agrega name_upper
├── gold/gold_people.py              → agrega record_source
├── ai_enrich/ai_enriched_people.py  → embeddings con Ollama
└── vault_demo/minio_check.py        → conectividad a MinIO con creds de Vault
```

El encadenado se declara por nombre de parámetro:

```python
@asset
def silver_people(bronze_people):  # ← depende de bronze_people
    df = bronze_people.copy()
    df["name_upper"] = df["name"].str.upper()
    return df
```

### PASO 8 - Revisar jobs y schedule

`lakehouse_dagster/lakehouse_dagster/jobs/etl_job.py`:

```python
etl_job = define_asset_job(name="etl_job", selection=AssetSelection.all())
```

`lakehouse_dagster/lakehouse_dagster/schedules/etl_schedule.py`:

```python
daily_etl_schedule = ScheduleDefinition(job=etl_job, cron_schedule="0 6 * * *")
```

Ambos se registran en `definitions.py` junto con el recurso `VaultResource`.

### PASO 9 - Ejecutar el pipeline completo en Dagster

```bash
cp lakehouse_dagster/.env.example lakehouse_dagster/.env   # ajustá DAGSTER_HOME
cd lakehouse_dagster
dagster dev
```

**En la UI** (<http://localhost:3000>):

- Andá a **Assets**.
- Seleccioná `gold_people` y hacé click en **Materialize**.
- Dagster ejecuta `bronze_people -> silver_people -> gold_people` respetando el lineage.
- Materializá también `silver_people_embeddings` para ver el asset de IA.

### PASO 10 - Validar el circuito de secretos (Vault)

```bash
python src/spark/09_spark_with_vault.py
```

Lee las credenciales de MinIO desde Vault y las inyecta en la SparkSession, en lugar
de hardcodearlas como hace `src/spark/utils.py`. Compará los dos archivos: esa
diferencia es todo el Lab 6.

### PASO 11 - Consultas en lenguaje natural (LLM local)

```bash
python src/spark/12_run_generated_sql.py
```

- El LLM (`llama3.1`) recibe el schema de `nessie.bronze.people` y `nessie.silver.people`.
- Genera SQL de Spark.
- Spark lo ejecuta y muestra el resultado.

Para cambiar la pregunta, editá la variable `prompt` del script:

```python
prompt = "mostrame las bios en mayúsculas ordenadas por id"
```

!!! warning "El LLM se equivoca"
    A veces genera SQL inválido, inventa columnas o envuelve la respuesta en
    ```` ```sql ````. El script limpia los backticks, y el prompt le pasa los
    nombres de tres niveles ya resueltos (`nessie.bronze.people`) para que no
    tenga que adivinar el catálogo. Aun así falla cada tanto: volvé a correrlo.
    **Esa inconsistencia es la lección**, no un bug del lab — un text-to-SQL sin
    validación no te da ninguna garantía sobre lo que va a ejecutar.

### PASO 12 - Validar CI/CD

```bash
git add -A
git commit -m "capstone: pipeline end-to-end"
git push
```

Revisá en GitHub Actions que corran los tres workflows: `Python CI` (ruff + pytest),
`Dagster` y `Terraform`.

### PASO 13 - (Bonus) RAG sobre la documentación

Si querés cerrar con el bonus, seguí el
[Lab 11 - RAG local sobre el Lakehouse](lab-11-rag.md): indexa la documentación del
curso en `nessie.gold.knowledge_chunks` y responde preguntas con fuentes.

## Checkpoint de validación

!!! important
    Completá esta validación antes de cerrar el capstone.

- Contenedores corriendo (`docker ps` muestra minio, nessie, vault)
- `terraform apply` sin errores y buckets/secreto creados
- `people.csv` visible en el bucket `bronze`
- `nessie.bronze.people` legible desde Spark y DuckDB
- Ramas `dev`/`staging`/`prod` en Nessie, con commits en `dev`
- `nessie.silver.people` con `name_upper` e `ingestion_ts`
- `nessie.silver.people_embeddings` con vectores de 768 dimensiones
- Dagster materializa `bronze_people -> silver_people -> gold_people`
- `09_spark_with_vault.py` lee credenciales desde Vault
- El LLM genera SQL y Spark lo ejecuta
- Los tres workflows de GitHub Actions en verde

## ¡Momento Click! 🎯

!!! success "Un solo catálogo, y la rama es solo una columna más"

    Todo el capstone se apoya en una idea: **el catálogo es el punto de
    integración**. Nadie le pasó una ruta de S3 a nadie. Spark escribió por nombre,
    Dagster orquestó por nombre, el LLM generó SQL por nombre. Este es el
    experimento que lo hace visible.

    Pegá esto en un archivo y correlo desde la raíz del repo:

    ```python
    import sys
    sys.path.insert(0, "src/spark")
    from utils import get_spark_multibranch

    # UN catálogo por rama, en la MISMA sesión
    spark = get_spark_multibranch(refs=("main", "dev"))

    spark.sql("""
        SELECT m.id,
               m.name AS name_en_main,
               d.name AS name_en_dev
        FROM nessie_main.bronze.people m
        JOIN nessie_dev.bronze.people d USING (id)
        WHERE m.name <> d.name
    """).show()
    ```

    Salida:

    ```text
    +---+------------+------------+
    | id|name_en_main| name_en_dev|
    +---+------------+------------+
    |  1|    Jeremias|Jeremias DEV|
    +---+------------+------------+
    ```

    ---

    **Frená un segundo en lo que acabás de hacer.** Eso es un `JOIN` entre dos
    versiones de la misma tabla, en la misma query, sin haber copiado un solo byte.
    No hay dos tablas: hay una tabla y dos ramas, y el catálogo resuelve qué
    archivos corresponden a cada una.

    Ahora pensá en el reflejo que tenías antes de este curso. ¿Cómo comparabas
    "producción contra lo que va a salir en el próximo deploy"? Duplicando la tabla
    con un sufijo `_backup_final_v2`, o exportando dos CSV y abriéndolos en pestañas
    distintas. **Acá el diff entre ambientes es una query.**

    Y todo lo demás del capstone cuelga de ahí: Dagster no tiene idea de dónde viven
    los archivos, DuckDB descubre las tablas sin que le expliques el layout, el LLM
    genera SQL contra nombres estables. El día que muevas el warehouse a otro bucket
    — o a otra nube — no cambia una línea de esos cuatro. Cambia una config del
    catálogo. **Eso es un Lakehouse y no un montón de Parquet en un balde.**

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`terraform apply` falla con `connection refused`** → los contenedores no están
    arriba. Terraform gestiona el estado inicial, no el runtime:
    `docker compose up -d && docker ps`.

    **`NoSuchNamespaceException: Namespace does not exist: silver`** → con el catálogo
    REST los namespaces no se crean solos. Corré antes:

    ```python
    spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")
    ```

    **Las ramas de Nessie desaparecieron después de reiniciar Docker** → verificá que
    el volumen `nessie-data` siga existiendo (`docker volume ls`). El compose usa
    RocksDB justamente para que el estado persista; un `docker compose down -v` lo borra.

    **Dagster materializa `bronze/silver/gold` pero falla `silver_people_embeddings`**
    → Ollama no está corriendo o falta el modelo:

    ```bash
    ollama list          # ¿está nomic-embed-text?
    ollama pull nomic-embed-text
    ```

    **El SQL del LLM falla con `TABLE_OR_VIEW_NOT_FOUND`** → inventó un nombre de
    tabla. Correlo de nuevo; si insiste, revisá que `nessie.silver.people` exista
    (el PASO 5 tiene que haber corrido antes que el PASO 11).

    **`py4j.protocol.Py4JJavaError` al arrancar cualquier script de Spark** → la
    primera corrida baja los JARs de Iceberg desde Maven. Necesita red y tarda un
    par de minutos. Si venís de cortar una corrida a la mitad, limpiá el caché:
    `rm -rf ~/.ivy2/cache/org.apache.iceberg`.

    **Los tres workflows no aparecen en GitHub Actions** → tu rama por defecto no es
    `master`. Los workflows filtran por esa rama; ajustá el `branches:` de los tres.

## Entrega final del capstone

!!! note
    Esta es la entrega sugerida para cerrar la masterclass con evidencia técnica y de comunicación.

1. Repositorio GitHub con `infra/terraform`, `src/spark`, `src/ai`, `src/nessie`, `lakehouse_dagster`, `data/bronze` y `.github/workflows`.
2. Documento PDF con arquitectura, explicación del pipeline, capturas de Dagster y ejemplos de SQL generados por IA.
3. Video opcional con la ejecución end-to-end del pipeline.

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, habrás construido un Lakehouse moderno, completo, automatizado,
versionado, seguro y con IA integrada.

No es un stack de juguete: son **los mismos primitivos arquitectónicos** que empresas
como Netflix, Uber, Shopify o Airbnb corren a escala — Iceberg para el table format,
un catálogo versionado, separación compute/storage, orquestación declarativa por assets.
Lo que cambia allá es el volumen, el tamaño del cluster y el equipo de plataforma
detrás. Los conceptos que acabás de ejecutar en tu laptop son los mismos.

!!! tip
    Próximos entregables posibles: README final del repositorio, portada del PDF, sílabus académico, landing page comercial y script de demo final para presentar el capstone.