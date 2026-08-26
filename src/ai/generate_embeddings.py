from pathlib import Path

import ollama
import pandas as pd

# Embebemos la BIO, no el nombre: el vector tiene que representar el *significado*
# del texto. Embeber "Ada" no dice nada; embeber su bio sí permite búsqueda semántica.
OUTPUT = Path("data/silver/people_with_embeddings.json")

df = pd.read_csv("data/bronze/people.csv")
df["embedding"] = df["bio"].apply(
    lambda x: ollama.embeddings(model="nomic-embed-text", prompt=x)["embedding"]
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_json(OUTPUT, orient="records")
print(df.head())
print(f"Embeddings generados para {len(df)} filas ->", OUTPUT)
