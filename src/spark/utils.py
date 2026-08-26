from urllib.parse import quote

from pyspark.sql import SparkSession

MINIO_ENDPOINT = "http://127.0.0.1:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password"

NESSIE_URI = "http://localhost:19120/iceberg"
NESSIE_WAREHOUSE = "warehouse"

# Catálogo Hadoop (Lab 2): metadata como archivos, sin servidor de catálogo.
PACKAGES = (
    "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,"
    "org.apache.hadoop:hadoop-aws:3.3.4"
)

# Catálogo Nessie vía Iceberg REST (Lab 3 en adelante).
# iceberg-aws-bundle trae S3FileIO, que es como el cliente REST habla con MinIO.
PACKAGES_NESSIE = (
    "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,"
    "org.apache.iceberg:iceberg-aws-bundle:1.7.1"
)


def get_spark(app_name: str = "spark-iceberg") -> SparkSession:
    """SparkSession con el catálogo Hadoop — SOLO para el Lab 2.

    Es el catálogo más simple que existe: la metadata son archivos en MinIO, no
    hay servidor. Sirve para entender qué resuelve un table format antes de sumar
    un catálogo de verdad. No tiene ramas ni identificadores de tres niveles.

    Del Lab 3 en adelante usá get_spark_with_nessie().
    """
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", PACKAGES)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "hadoop")
        .config("spark.sql.catalog.iceberg.warehouse", "s3a://bronze/iceberg/warehouse")
        # MinIO (S3 compatible) vía el conector s3a de Hadoop
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )


def get_spark_with_nessie(
    app_name: str = "spark-nessie",
    ref: str = "main",
) -> SparkSession:
    """SparkSession contra Nessie usando el protocolo Iceberg REST Catalog.

    Este es el catálogo principal del curso a partir del Lab 3. Te da:

    - Identificadores de tres niveles: nessie.<namespace>.<tabla>
    - Ramas de datos: elegí la rama con el parámetro `ref`
    - Un único catálogo compartido por Spark, DuckDB y pyiceberg

    Nessie enruta cada request con un prefijo `<rama>|<warehouse>`, que va
    URL-encodeado (`%7C` es el `|`). Por eso cambiar de rama es solo cambiar
    `ref`: no hay que tocar los nombres de las tablas.
    """
    prefix = quote(f"{ref}|{NESSIE_WAREHOUSE}", safe="")
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", PACKAGES_NESSIE)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.nessie.type", "rest")
        .config("spark.sql.catalog.nessie.uri", NESSIE_URI)
        .config("spark.sql.catalog.nessie.prefix", prefix)
        # S3FileIO habla directo con MinIO (no pasa por el conector s3a)
        .config(
            "spark.sql.catalog.nessie.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"
        )
        .config("spark.sql.catalog.nessie.s3.endpoint", MINIO_ENDPOINT)
        .config("spark.sql.catalog.nessie.s3.path-style-access", "true")
        .config("spark.sql.catalog.nessie.s3.access-key-id", MINIO_ACCESS_KEY)
        .config("spark.sql.catalog.nessie.s3.secret-access-key", MINIO_SECRET_KEY)
        .getOrCreate()
    )


def _nessie_catalog_config(builder, catalog: str, ref: str):
    """Registra un catálogo Iceberg REST apuntando a una rama de Nessie."""
    prefix = quote(f"{ref}|{NESSIE_WAREHOUSE}", safe="")
    opts = {
        "": "org.apache.iceberg.spark.SparkCatalog",
        "type": "rest",
        "uri": NESSIE_URI,
        "prefix": prefix,
        "io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.path-style-access": "true",
        "s3.access-key-id": MINIO_ACCESS_KEY,
        "s3.secret-access-key": MINIO_SECRET_KEY,
    }
    for key, value in opts.items():
        suffix = f".{key}" if key else ""
        builder = builder.config(f"spark.sql.catalog.{catalog}{suffix}", value)
    return builder


def get_spark_multibranch(
    app_name: str = "spark-nessie-branches",
    refs: tuple[str, ...] = ("main", "dev"),
) -> SparkSession:
    """SparkSession con UN catálogo por rama, para comparar ramas en una sola query.

    Con el protocolo REST no existen las sentencias `USE REFERENCE` de las
    extensiones Nessie: la rama se elige por configuración de catálogo. La ventaja
    es que podés registrar varias a la vez y hacer:

        SELECT * FROM nessie_main.bronze.people
        SELECT * FROM nessie_dev.bronze.people

    ...en la misma sesión, que es la forma más directa de *ver* el aislamiento.
    """
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", PACKAGES_NESSIE)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
    )
    for ref in refs:
        builder = _nessie_catalog_config(builder, f"nessie_{ref}", ref)
    return builder.getOrCreate()
