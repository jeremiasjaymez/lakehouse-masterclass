import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "ai"))

from pyspark.sql.types import (
    ArrayType,
    FloatType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from rag_utils import build_knowledge_chunks
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("save-rag-index")
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.gold")

chunks = build_knowledge_chunks()
schema = StructType(
    [
        StructField("chunk_id", StringType(), False),
        StructField("source_path", StringType(), False),
        StructField("section_title", StringType(), False),
        StructField("chunk_index", IntegerType(), False),
        StructField("chunk_text", StringType(), False),
        StructField("embedding", ArrayType(FloatType()), False),
        StructField("ingestion_ts", TimestampType(), False),
    ]
)
spark_df = spark.createDataFrame(chunks, schema=schema)

spark_df.writeTo("nessie.gold.knowledge_chunks").createOrReplace()

print("Tabla gold_knowledge_chunks guardada con", spark_df.count(), "chunks")

spark.stop()
