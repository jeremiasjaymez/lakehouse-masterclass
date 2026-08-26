from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("spark-basic-test").master("local[*]").getOrCreate()
)

df = spark.range(10)
df.show()

spark.stop()
