"""
Tests básicos del Lakehouse — patrón de ejemplo.

Tres estrategias demostradas:
  1. materialize()       → test de integración liviano (sin mocks, lee CSV real)
  2. invocación directa  → test unitario de transformación pura
  3. mock de requests    → test unitario de resource con I/O externo
  4. import de defs      → smoke test de que Dagster levanta sin explotar
"""

from unittest.mock import MagicMock, patch

import pandas as pd
from dagster import materialize
from lakehouse_dagster.assets.bronze.bronze_people import bronze_people
from lakehouse_dagster.assets.silver.silver_people import silver_people
from lakehouse_dagster.assets.vault_demo.minio_check import minio_connectivity_check
from lakehouse_dagster.resources.vault_resource import VaultResource

# ─── 1. bronze_people lee el CSV real y devuelve un DataFrame ─────────────────


def test_bronze_people_carga_csv():
    result = materialize([bronze_people])
    assert result.success
    df = result.output_for_node("bronze_people")
    assert not df.empty
    assert "name" in df.columns


# ─── 2. silver_people agrega name_upper (transformación pura) ─────────────────


def test_silver_people_agrega_columna():
    entrada = pd.DataFrame({"id": [1, 2], "name": ["jeremias", "ada"]})
    # @asset es callable directamente como función normal
    salida = silver_people(entrada)
    assert "name_upper" in salida.columns
    assert salida["name_upper"].tolist() == ["JEREMIAS", "ADA"]


# ─── 3. VaultResource.read_secret mockea requests.get ────────────────────────


def test_vault_resource_devuelve_secreto():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"data": {"access_key": "admin", "secret_key": "password"}}
    }
    mock_resp.raise_for_status = MagicMock()

    with patch(
        "lakehouse_dagster.resources.vault_resource.requests.get",
        return_value=mock_resp,
    ):
        vault = VaultResource(addr="http://fake-vault:8200", token="root")
        creds = vault.read_secret("minio")

    assert creds["access_key"] == "admin"
    assert creds["secret_key"] == "password"


# ─── 4. minio_connectivity_check con Vault y boto3 mockeados ─────────────────


def test_minio_connectivity_check_con_creds_validas():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"data": {"access_key": "admin", "secret_key": "password"}}
    }
    mock_resp.raise_for_status = MagicMock()

    mock_s3 = MagicMock()
    mock_s3.list_buckets.return_value = {
        "Buckets": [{"Name": "bronze"}, {"Name": "silver"}, {"Name": "gold"}]
    }

    with (
        patch(
            "lakehouse_dagster.resources.vault_resource.requests.get",
            return_value=mock_resp,
        ),
        patch(
            "lakehouse_dagster.assets.vault_demo.minio_check.boto3.client",
            return_value=mock_s3,
        ),
    ):
        result = materialize(
            [minio_connectivity_check],
            resources={
                "vault": VaultResource(addr="http://fake-vault:8200", token="root")
            },
        )

    assert result.success
    buckets = result.output_for_node("minio_connectivity_check")
    assert "bronze" in buckets


# ─── 5. Smoke test: Definitions carga sin errores ────────────────────────────


def test_definitions_cargan():
    from lakehouse_dagster.definitions import defs

    assert defs is not None
