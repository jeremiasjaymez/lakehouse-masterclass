import os

import requests
from dagster import ConfigurableResource


class VaultResource(ConfigurableResource):
    """Lee secretos de HashiCorp Vault (modo dev).

    Configuración por defecto: http://localhost:8200 con token 'root'.
    Sobreescribible vía variables de entorno VAULT_ADDR y VAULT_TOKEN,
    o desde el Launchpad de Dagster.
    """

    addr: str = os.getenv("VAULT_ADDR", "http://localhost:8200")
    token: str = os.getenv("VAULT_TOKEN", "root")

    def read_secret(self, path: str) -> dict:
        url = f"{self.addr}/v1/secret/data/{path}"
        resp = requests.get(url, headers={"X-Vault-Token": self.token}, timeout=5)
        resp.raise_for_status()
        return resp.json()["data"]["data"]
