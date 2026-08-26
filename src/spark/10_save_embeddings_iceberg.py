import pandas as pd
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("save-embeddings")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")

df = pd.read_json("data/silver/people_with_embeddings.json")
spark_df = spark.createDataFrame(df)

spark_df.writeTo("nessie.silver.people_embeddings").createOrReplace()

print("Tabla silver_people_embeddings guardada con", spark_df.count(), "filas")

spark.stop()
