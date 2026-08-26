"""
DuckDB contra el catálogo Nessie (Iceberg REST).

Muestra dos cosas:

  1. ATTACH del catálogo -> DuckDB descubre namespaces y tablas POR NOMBRE.
  2. Lectura de los datos -> hoy hay que ir por la ruta del warehouse.

Sobre el punto 2: la extensión `iceberg` de DuckDB todavía no implementa el
mecanismo de credenciales que Nessie usa para entregar los archivos, así que el
`SELECT ... FROM nessie.silver.people` falla con HTTP 403. El catálogo sirve
igual para *descubrir* qué hay; los datos se leen con `iceberg_scan()` sobre la
ruta. Cuando DuckDB soporte credential vending, el paso 2 sobra.
"""

import duckdb

NESSIE_REST = "http://localhost:19120/iceberg"
WAREHOUSE = "s3://bronze/iceberg/nessie-warehouse"

con = duckdb.connect()
con.execute("INSTALL iceberg; LOAD iceberg;")
con.execute("INSTALL httpfs; LOAD httpfs;")

# Las tablas que administra Nessie no llevan archivo version-hint
con.execute("SET unsafe_enable_version_guessing = true;")

con.execute("""
    CREATE OR REPLACE SECRET minio_secret (
        TYPE s3, KEY_ID 'admin', SECRET 'password',
        ENDPOINT '127.0.0.1:9000', USE_SSL false,
        URL_STYLE 'path', REGION 'us-east-1'
    );
""")

# ── 1. Descubrir el catálogo por nombre ──────────────────────────────────────
con.execute(f"""
    ATTACH 'warehouse' AS nessie (
        TYPE iceberg, ENDPOINT '{NESSIE_REST}', AUTHORIZATION_TYPE 'none'
    );
""")

print("=== Namespaces que ve DuckDB en Nessie ===")
for (schema,) in con.execute(
    "SELECT schema_name FROM duckdb_schemas() WHERE database_name = 'nessie'"
).fetchall():
    print("  ", schema)

print("\n=== Tablas del catálogo (descubiertas por nombre) ===")
for row in con.execute("SHOW ALL TABLES").fetchall():
    print(f"   {row[0]}.{row[1]}.{row[2]}")


# ── 2. Leer los datos por ruta ───────────────────────────────────────────────
def table_path(namespace: str, table: str) -> str:
    """Nessie le agrega un sufijo UUID a la carpeta de cada tabla."""
    rows = con.execute(
        """
        SELECT DISTINCT regexp_replace(file, '/metadata/.*$', '') AS dir
        FROM glob($1) WHERE file LIKE '%/metadata/%'
        """,
        [f"{WAREHOUSE}/{namespace}/**"],
    ).fetchall()
    matches = [r[0] for r in rows if r[0].rsplit("/", 1)[-1].startswith(f"{table}_")]
    if not matches:
        raise SystemExit(f"No encontré la tabla {namespace}.{table} en {WAREHOUSE}")
    return matches[0]


path = table_path("silver", "people")
print("\n=== Datos de silver.people (vía iceberg_scan) ===")
rows = con.execute(f"""
    SELECT department, country, COUNT(*) AS n
    FROM iceberg_scan('{path}')
    GROUP BY department, country ORDER BY n DESC LIMIT 5
""").fetchall()
for department, country, n in rows:
    print(f"   {department:<12} {country:<12} {n}")

con.close()
