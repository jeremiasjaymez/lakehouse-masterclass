import requests


def generate_sql(prompt):
    payload = {
        "model": "llama3.1",
        "prompt": (
            "You are a SQL expert for Apache Spark with Iceberg tables.\n"
            "Available tables:\n"
            "  - nessie.bronze.people (id INT, name STRING, bio STRING, department STRING, country STRING)\n"
            "  - nessie.silver.people (id INT, name STRING, bio STRING, department STRING, country STRING, name_upper STRING, ingestion_ts TIMESTAMP)\n"
            "Convert the following request into a single valid Spark SQL query using those tables. Always use the fully qualified three-level names exactly as given. "
            "Return only the SQL, no explanation, no markdown:\n\n"
            f"{prompt}"
        ),
        "stream": False,  # respuesta única en vez de NDJSON streaming
    }
    resp = requests.post("http://localhost:11434/api/generate", json=payload)
    sql = resp.json()["response"]
    # el LLM a veces envuelve la respuesta en ```sql ... ```, Spark no puede parsear eso
    sql = (
        sql.strip()
        .removeprefix("```sql")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    return sql


if __name__ == "__main__":
    q = "mostrame los nombres en minúsculas."
    print(generate_sql(q))
