import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # src/spark  → utils
sys.path.insert(0, str(Path(__file__).parent.parent / "ai"))  # src/ai → sql_generator

from sql_generator import generate_sql
from utils import get_spark_with_nessie

spark = get_spark_with_nessie("run-generated-sql")
# Con Nessie los nombres son de tres niveles (nessie.bronze.people), así que el
# prompt del generador ya se los pasa completos: no hace falta un USE por defecto.
prompt = "mostrame los nombres en mayúsculas."
sql = generate_sql(prompt)

print("SQL generado:", sql)

df = spark.sql(sql)
df.show()

spark.stop()
