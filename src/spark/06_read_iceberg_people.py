from utils import get_spark_with_nessie

spark = get_spark_with_nessie("mi-app")
spark.sql("SELECT * FROM nessie.bronze.people").show()
# df = spark.read.format("iceberg").load("nessie.bronze.people").show()

spark.stop()
