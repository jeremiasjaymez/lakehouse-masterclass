# src/spark/09_spark_with_vault.py
"""
LAB 6 — Spark + Vault
Demuestra cómo inyectar credenciales de MinIO en Spark leyéndolas de Vault
en lugar de hardcodearlas (compará con src/spark/utils.py).
"""

import sys
from pathlib import Path
from urllib.parse import quote

from pyspark.sql import SparkSession

# Permitir importar src/vault/read_secrets.py sin instalarlo como paquete
sys.path.append(str(Path(__file__).resolve().parents[1]))
from vault.read_secrets import read_secret


def mask(value: str, visible: int = 3) -> str:
    return value[:visible] + "***" if value else "<empty>"


# 1) Traer credenciales desde Vault
print("== Paso 1: leyendo secreto 'minio' desde Vault ==")
creds = read_secret("minio")
print(f"  access_key = {mask(creds['access_key'])}")
print(f"  secret_key = {mask(creds['secret_key'])}")
print("  (las credenciales NO están en el código fuente)\n")

# 2) Construir Spark inyectando los secretos en el catálogo Nessie
print("== Paso 2: creando SparkSession con creds de Vault ==")
prefix = quote("main|warehouse", safe="")
spark = (
    SparkSession.builder.appName("spark-with-vault")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,"
        "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
    )
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.nessie.type", "rest")
    .config("spark.sql.catalog.nessie.uri", "http://localhost:19120/iceberg")
    .config("spark.sql.catalog.nessie.prefix", prefix)
    .config("spark.sql.catalog.nessie.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config("spark.sql.catalog.nessie.s3.endpoint", "http://127.0.0.1:9000")
    .config("spark.sql.catalog.nessie.s3.path-style-access", "true")
    # 👇 ACÁ está la magia: vienen de Vault, no de un literal
    .config("spark.sql.catalog.nessie.s3.access-key-id", creds["access_key"])
    .config("spark.sql.catalog.nessie.s3.secret-access-key", creds["secret_key"])
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# 3) Probar que las credenciales son válidas leyendo una tabla real
print("\n== Paso 3: leyendo nessie.bronze.people para probar el acceso ==")
df = spark.table("nessie.bronze.people")
df.show()
print(f"OK ✅ — {df.count()} filas leídas usando credenciales de Vault")

spark.stop()
