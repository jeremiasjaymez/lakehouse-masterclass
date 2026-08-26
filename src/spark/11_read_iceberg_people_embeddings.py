from utils import get_spark_with_nessie

spark = get_spark_with_nessie("mi-app")
spark.sql("SELECT * FROM nessie.silver.people_embeddings").show()
# df = spark.read.format("iceberg").load("nessie.bronze.people").show()

spark.stop()
