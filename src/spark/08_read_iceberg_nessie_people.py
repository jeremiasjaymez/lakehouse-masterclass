"""Leer una tabla Iceberg desde una rama específica de Nessie.

Cambiar de rama es cambiar `ref`: el nombre de la tabla no se toca.
"""

from utils import get_spark_with_nessie

# Probá cambiando ref="main" y comparando el resultado.
spark = get_spark_with_nessie("read-nessie-people", ref="dev")

spark.sql("SELECT * FROM nessie.bronze.people ORDER BY id").show()

spark.stop()
