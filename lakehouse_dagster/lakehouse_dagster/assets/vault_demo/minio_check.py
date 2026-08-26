"""
PASO 10 — Dagster + Vault
Asset de demostración: lee credenciales de MinIO desde Vault y las usa
para listar buckets reales. Si Vault tiene credenciales válidas → verde.
Si se rotan a basura → rojo. El código nunca cambia.

Para demostrar la rotación en vivo:
    # Romper
    docker exec -it vault vault kv put secret/minio access_key=wrong secret_key=wrong
    # Re-materializar → asset rojo (InvalidAccessKeyId)

    # Restaurar
    docker exec -it vault vault kv put secret/minio access_key=admin secret_key=password
    # Re-materializar → asset verde
"""

import boto3
from botocore.client import Config
from dagster import AssetExecutionContext, asset

from lakehouse_dagster.resources.vault_resource import VaultResource


def _mask(v: str) -> str:
    return v[:3] + "***" if v else "<empty>"


@asset(group_name="vault_demo")
def minio_connectivity_check(
    context: AssetExecutionContext, vault: VaultResource
) -> list:
    """Lee credenciales de Vault y las usa para listar los buckets de MinIO."""
    # 1) Leer secreto desde Vault
    creds = vault.read_secret("minio")
    context.log.info(f"access_key desde Vault = {_mask(creds['access_key'])}")
    context.log.info("(las credenciales NO están en el código fuente)")

    # 2) Usar las credenciales para conectarse a MinIO
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id=creds["access_key"],
        aws_secret_access_key=creds["secret_key"],
        config=Config(signature_version="s3v4"),
    )

    # 3) Operación real: si las creds son inválidas, esto lanza ClientError
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    context.log.info(f"Buckets MinIO accesibles: {buckets}")
    return buckets
