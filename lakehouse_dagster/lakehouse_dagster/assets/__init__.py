# Importamos el asset que enriquece con embeddings usando Ollama.
from lakehouse_dagster.assets.ai_enrich import ai_enriched_people
from lakehouse_dagster.assets.bronze import bronze_people
from lakehouse_dagster.assets.gold import gold_people
from lakehouse_dagster.assets.silver import silver_people

# Importamos los assets del demo de Vault.
from lakehouse_dagster.assets.vault_demo import minio_check

__all__ = [
    "ai_enriched_people",
    "bronze_people",
    "gold_people",
    "minio_check",
    "silver_people",
]
