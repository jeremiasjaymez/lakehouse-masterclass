# LAB 2 — Time travel a un snapshot anterior.
# Lee la tabla Iceberg en el snapshot más viejo, o sea antes de cualquier update.

import duckdb

TABLE_PATH = "s3://bronze/iceberg/warehouse/bronze_people"

con = duckdb.connect()

con.execute("INSTALL iceberg; LOAD iceberg;")
con.execute("INSTALL httpfs; LOAD httpfs;")

con.execute("""
    SET s3_endpoint = 'localhost:9000';
    SET s3_access_key_id = 'admin';
    SET s3_secret_access_key = 'password';
    SET s3_use_ssl = false;
    SET s3_url_style = 'path';
""")

# Listamos todos los snapshots, del más viejo al más nuevo
snapshots = con.execute(f"""
    SELECT sequence_number, snapshot_id, timestamp_ms
    FROM iceberg_snapshots('{TABLE_PATH}')
    ORDER BY timestamp_ms ASC
""").df()

print("Todos los snapshots:")
print(snapshots)
print()

# Agarramos el primero (el más viejo): el estado previo a los INSERT
first_snapshot_id = int(snapshots.iloc[0]["snapshot_id"])
print(f"Viajando al primer snapshot: {first_snapshot_id}")
print()

# Equivale a: SELECT * FROM iceberg.bronze_people FOR SYSTEM_VERSION AS OF <snapshot_id>
df = con.execute(f"""
    SELECT * FROM iceberg_scan('{TABLE_PATH}', snapshot_from_id={first_snapshot_id})
""").df()

print("Datos en el primer snapshot (antes de los INSERT):")
print(df)
