from pyspark.sql import SparkSession

# Step 2: Insert data into the Iceberg table and query it
# Prerequisite: run 01_create_people_table.py (or create_people_table.py) first

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

# Insert new rows into the existing table
spark.sql("""
    INSERT INTO iceberg.bronze_people VALUES
        (5, 'Gaston'),
        (6, 'Gonzalo')
""")

print("Rows inserted successfully.")

# Query all data
df = spark.sql("SELECT * FROM iceberg.bronze_people")

print("Current table contents:")
df.show()
