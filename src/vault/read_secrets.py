import os

import requests

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")


def read_secret(path):
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    resp = requests.get(url, headers=headers)
    return resp.json()["data"]["data"]


if __name__ == "__main__":
    creds = read_secret("minio")
    print("MinIO credentials:", creds)
