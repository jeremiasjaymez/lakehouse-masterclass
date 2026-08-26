from pyspark.sql import functions as F
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("etl-bronze-to-silver")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")

# Leer tabla bronze
bronze_df = spark.read.format("iceberg").load("nessie.bronze.people")

print("=== Bronze (original) ===")
bronze_df.show()

# Transformaciones
silver_df = bronze_df.withColumn("name_upper", F.upper(F.col("name"))).withColumn(
    "ingestion_ts", F.current_timestamp()
)

print("=== Silver (transformado) ===")
silver_df.show()

# Escribir como tabla Iceberg silver
silver_df.writeTo("nessie.silver.people").createOrReplace()

print("Tabla silver_people creada con", silver_df.count(), "filas")

# Tabla alternativa: particionada por inicial del nombre (baja cardinalidad)
silver_partitioned_df = silver_df.withColumn(
    "name_initial", F.upper(F.col("name")).substr(1, 1)
)

(
    silver_partitioned_df.writeTo("nessie.silver.people_partitioned")
    .partitionedBy("name_initial")
    .createOrReplace()
)

print("Tabla silver_people_partitioned creada con particionado por name_initial")

spark.stop()
