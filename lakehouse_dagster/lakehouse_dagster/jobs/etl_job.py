from dagster import AssetSelection, define_asset_job

# Corre TODOS los assets (bronze -> silver -> gold)
etl_job = define_asset_job(
    name="etl_job",
    selection=AssetSelection.all(),
)

# Opcionales: jobs por capa, útiles para backfills/debug
bronze_job = define_asset_job("bronze_job", selection=AssetSelection.groups("bronze"))
silver_job = define_asset_job("silver_job", selection=AssetSelection.groups("silver"))
gold_job = define_asset_job("gold_job", selection=AssetSelection.groups("gold"))
