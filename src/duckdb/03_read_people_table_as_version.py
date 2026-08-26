# Step 10 — Time travel a snapshot anterior
# Reads the Iceberg table at the oldest available snapshot (before any updates)

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

# List all snapshots ordered from oldest to newest
snapshots = con.execute(f"""
    SELECT sequence_number, snapshot_id, timestamp_ms
    FROM iceberg_snapshots('{TABLE_PATH}')
    ORDER BY timestamp_ms ASC
""").df()

print("All snapshots:")
print(snapshots)
print()

# Pick the first (oldest) snapshot — equivalent to before any updates
first_snapshot_id = int(snapshots.iloc[0]["snapshot_id"])
print(f"Time-traveling to first snapshot: {first_snapshot_id}")
print()

# Equivalent of: SELECT * FROM iceberg.bronze_people FOR SYSTEM_TIME AS OF <snapshot_id>
df = con.execute(f"""
    SELECT * FROM iceberg_scan('{TABLE_PATH}', snapshot_from_id={first_snapshot_id})
""").df()

print("Data at first snapshot (before updates):")
print(df)
