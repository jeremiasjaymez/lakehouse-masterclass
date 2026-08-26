from pathlib import Path

import ollama
import pandas as pd
from dagster import asset

REPO_ROOT = Path(__file__).parents[4]


@asset(deps=["bronze_people"])
def silver_people_embeddings():
    df = pd.read_csv(REPO_ROOT / "data" / "bronze" / "people.csv")
    # Embebemos la bio (texto con significado), no el nombre propio.
    df["embedding"] = df["bio"].apply(
        lambda x: ollama.embeddings(model="nomic-embed-text", prompt=x)["embedding"]
    )
    return df
