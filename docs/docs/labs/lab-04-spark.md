# LAB 4 - Spark: Compute Layer sobre Iceberg + MinIO

!!! tip
    En este lab vas a usar Spark como motor de cómputo del Lakehouse, leyendo y escribiendo tablas Iceberg sobre MinIO, con Nessie como catálogo versionado.

## ¿Por qué Spark?

Necesitamos un motor de cómputo que entienda Iceberg, escale de un laptop a un cluster y sea estándar de la industria. **Apache Spark** sigue siendo la opción más madura para batch sobre Lakehouse: tiene el conector Iceberg más completo (incluyendo `MERGE INTO`, branching, time-travel SQL) y se integra con Nessie de forma nativa. Lo corremos en modo `local[*]` — exactamente la misma API que usarías en EMR, Dataproc o un cluster k8s on-prem.

## Objetivo del lab

- Levantar Spark en modo local.
- Leer datos desde Iceberg.
- Construir un ETL simple: bronze -> silver.
- Escribir resultados nuevamente en Iceberg.

## Prerrequisitos

- LAB 0, 1, 2 y 3 completados.
- MinIO corriendo (http://localhost:9000).
- Nessie corriendo (http://localhost:19120) — desde este lab es obligatorio.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup específico

Ya tenés pyspark instalado vía pyproject.toml.

En este lab vas a:

- Levantar Spark en modo local.
- Conectarlo a Iceberg.
- Ejecutar un ETL end-to-end.

### PASO 1 - Crear carpeta para scripts Spark

```bash
mkdir -p src/spark
```

### PASO 2 - Crear un SparkSession básico (modo local)

Archivo de referencia: `src/spark/05_spark_session.py`.

**Ejecutar**

```bash
python src/spark/05_spark_session.py
```

- Si ves los números del 0 al 9, Spark está OK.

### PASO 3 - Los dos helpers de sesión

Toda la configuración de Spark vive en `src/spark/utils.py`, en dos funciones:

| Helper | Catálogo | Tablas | Cuándo |
|---|---|---|---|
| `get_spark()` | `hadoop` | `iceberg.bronze_people` | Solo Lab 2 |
| `get_spark_with_nessie(ref=...)` | Nessie REST | `nessie.bronze.people` | **Lab 3 en adelante** |

En este lab y en todos los que siguen usás el segundo:

```python
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("mi-app")  # rama main
spark = get_spark_with_nessie("mi-app", ref="dev")  # rama dev
```

**Lo que configura por vos**

- Catálogo Iceberg REST apuntando a `http://localhost:19120/iceberg`
- El prefijo de rama (`<rama>|warehouse`, URL-encodeado)
- `S3FileIO` contra MinIO en `http://127.0.0.1:9000`
- Los jars: `iceberg-spark-runtime` + `iceberg-aws-bundle`

### PASO 4 - Leer una tabla Iceberg desde Spark

En el Lab 3 cargaste `nessie.bronze.people` con `04_nessie_commit_dev.py`. Ahora la leemos desde Spark vía el catálogo `nessie`.

Archivo de referencia: `src/spark/06_read_iceberg_people.py`.

!!! note
    Si ves tus filas (`Jeremias`, `Franco`, etc.), Spark ya está leyendo Iceberg correctamente.

### PASO 5 - Crear y validar ETL bronze -> silver

**Vamos a hacer lo siguiente**

- Leer `bronze_people`.
- Limpiar y transformar los datos.
- Escribir `silver_people`.
- Usar `src/spark/07_etl_bronze_to_silver.py`.
- Ejecutar `python src/spark/07_etl_bronze_to_silver.py`.

!!! tip
    Opción B: desde DuckDB, con el script que ataca el catálogo Nessie:

```bash
python src/duckdb/05_attach_nessie_catalog.py
```

### PASO 6 - Todo el ETL corre sobre Nessie

A diferencia del Lab 2, el ETL de este lab **no escribe en un catálogo suelto**:
escribe en Nessie. Mirá el script:

```python
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("etl-bronze-to-silver")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")

bronze_df = spark.read.format("iceberg").load("nessie.bronze.people")
silver_df.writeTo("nessie.silver.people").createOrReplace()
```

Tres cosas para registrar:

1. **Nombres de tres niveles**: `nessie.silver.people` = catálogo, namespace, tabla.
2. **Los namespaces no se crean solos** con el catálogo REST: por eso el
   `CREATE NAMESPACE IF NOT EXISTS`.
3. **La tabla silver ahora es versionable**: vive en el mismo catálogo con ramas
   que `bronze`, así que un merge puede mover bronze y silver de forma atómica.

### PASO 7 - Correr el ETL en una rama y mergear

Este es el flujo que usarías en producción: probás en `dev`, validás, mergeás.

```python
# Correr el ETL apuntando a dev en vez de main
spark = get_spark_with_nessie("etl-bronze-to-silver", ref="dev")
```

Validás el resultado en `dev`:

```bash
curl http://localhost:19120/api/v1/trees/tree/dev/log
```

Y si convence, mergeás:

```bash
python src/nessie/02_merge_dev_to_staging.py
```

!!! success "Por qué esto importa"
    Cuando el ETL corre en una rama, un bug no rompe `main`: rompe `dev`, lo ves en
    el log de commits y lo descartás borrando la rama. Es el mismo gesto mental que
    hacés con Git todos los días, aplicado a tablas de millones de filas.

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Spark corre en modo local.
- Podés leer una tabla Iceberg desde Spark.
- El ETL bronze -> silver se ejecuta sin errores.
- La tabla silver_people existe y tiene columnas nuevas (name_upper, ingestion_ts).
- Entendés que `nessie.silver.people` son catálogo + namespace + tabla.
- Sabés cambiar de rama con el parámetro `ref` de `get_spark_with_nessie()`.

## ¡Momento Click! 🎯

!!! success "Un solo catálogo, tres motores"
    1. Corré el ETL con Spark:
    ```bash
    python src/spark/07_etl_bronze_to_silver.py
    ```
    2. Ahora preguntale al catálogo desde DuckDB, **sin abrir Spark de nuevo**:
    ```bash
    python src/duckdb/05_attach_nessie_catalog.py
    ```

    ```text
    === Namespaces que ve DuckDB en Nessie ===
       bronze
       silver

    === Tablas del catálogo (descubiertas por nombre) ===
       nessie.bronze.people
       nessie.silver.people
       nessie.silver.people_partitioned
    ```

    DuckDB las lista **por nombre**. No le dijiste dónde está nada: se lo preguntó
    a Nessie, igual que Spark. (Cuando hagas los labs 9 y 11 van a aparecer también
    `people_embeddings` y `knowledge_chunks`, sin que toques este script.)

    Eso es un catálogo de verdad. En el Lab 2, DuckDB necesitaba la ruta completa
    `s3://bronze/iceberg/warehouse/bronze_people`; ahora hay **una sola fuente de
    verdad** sobre qué tablas existen y qué snapshot es el vigente.

!!! warning "Limitación honesta de DuckDB (hoy)"
    DuckDB **descubre** las tablas del catálogo por nombre, pero todavía no puede
    **leer los datos** con `SELECT * FROM nessie.silver.people`: falla con HTTP 403.
    Su extensión Iceberg aún no implementa el mecanismo de credenciales que usa
    Nessie para entregar los archivos.

    Por eso `05_attach_nessie_catalog.py` hace las dos cosas: usa el catálogo para
    descubrir, y `iceberg_scan()` sobre la ruta para leer. Spark sí lee por nombre
    sin ninguna limitación. Cuando DuckDB agregue *credential vending*, el rodeo
    sobra — el resto del curso no cambia.

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **Spark descarga jars la primera vez y tarda 2-3 min** → normal. Los jars
    quedan en caché en `~/.ivy2/` y las próximas ejecuciones arrancan rápido.

    **`java.lang.OutOfMemoryError`** → cerrá otras aplicaciones o agregá al
    SparkSession:
    ```python
    .config("spark.driver.memory", "2g")
    ```

    **`NoSuchBucketException`** → el bucket `bronze` no existe en MinIO.
    `src/minio/test_minio.py` **no crea buckets**, solo sube el CSV a uno que ya
    exista. Crealo desde la consola de MinIO (<http://localhost:9001>) como en el
    Lab 1, o con Terraform (`terraform apply` en `infra/terraform`), o desde Python:
    ```python
    s3.create_bucket(Bucket="bronze")
    ```

    **`NoSuchTableException` en `nessie.bronze.people`** → esta es la tabla del
    catálogo Nessie, no la del Lab 2. La carga el script del Lab 3:
    ```bash
    python src/spark/04_nessie_commit_dev.py
    ```

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- Spark integrado al Lakehouse.
- Lectura/escritura sobre Iceberg.
- Un ETL funcional bronze -> silver.
- Base perfecta para orquestar con Dagster en el siguiente lab.