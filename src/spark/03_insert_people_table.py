from pyspark.sql import SparkSession

# LAB 2 — Insertar filas en la tabla Iceberg para generar un snapshot nuevo.
# Prerrequisito: correr antes 02_create_people_table.py

spark = (
    SparkSession.builder.appName("InsertIcebergTable")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,"
        "org.apache.hadoop:hadoop-aws:3.3.4",
    )
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hadoop")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://bronze/iceberg/warehouse")
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
    .config("spark.hadoop.fs.s3a.access.key", "admin")
    .config("spark.hadoop.fs.s3a.secret.key", "password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .getOrCreate()
)

# El INSERT tiene que respetar el schema completo que salió del CSV
# (id, name, bio, department, country). Si le pasás menos columnas, Spark corta con
# INSERT_COLUMN_ARITY_MISMATCH: Iceberg no completa con NULL por su cuenta.
spark.sql("""
    INSERT INTO iceberg.bronze_people VALUES
        (16, 'Gaston', 'Data engineer enfocado en streaming y Kafka', 'Engineering', 'Argentina'),
        (17, 'Gonzalo', 'Analista de datos con foco en reporting financiero', 'Analytics', 'Chile')
""")

print("Filas insertadas correctamente.")

# Este INSERT crea un snapshot NUEVO: la tabla ahora tiene dos versiones.
# Esa es la materia prima del time travel del PASO 8.
df = spark.sql("SELECT * FROM iceberg.bronze_people")

print("Contenido actual de la tabla:")
df.show()
