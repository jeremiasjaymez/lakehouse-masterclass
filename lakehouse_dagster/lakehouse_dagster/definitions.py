from dagster import Definitions, load_assets_from_package_module

# Importamos los assets del demo de Vault.
# Importamos el asset de IA (embeddings con Ollama).
from lakehouse_dagster.assets import ai_enrich, bronze, gold, silver, vault_demo

# Importamos los jobs.
from lakehouse_dagster.jobs import bronze_job, etl_job, gold_job, silver_job

# Recurso para Vault
from lakehouse_dagster.resources.vault_resource import VaultResource

# Importamos el schedule.
from lakehouse_dagster.schedules import daily_etl_schedule

defs = Definitions(
    assets=[
        *load_assets_from_package_module(bronze, group_name="bronze"),
        *load_assets_from_package_module(silver, group_name="silver"),
        *load_assets_from_package_module(gold, group_name="gold"),
        *load_assets_from_package_module(vault_demo, group_name="vault_demo"),
        *load_assets_from_package_module(ai_enrich, group_name="ai_enrich"),
    ],
    # Agregado luego, en el paso de definición de jobs
    jobs=[etl_job, bronze_job, silver_job, gold_job],
    # Agregado luego, en el paso de definición de schedules
    schedules=[daily_etl_schedule],
    # Agregado luego, en el paso de definición de recursos para vault
    resources={"vault": VaultResource()},
)
