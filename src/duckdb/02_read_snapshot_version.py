import duckdb

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

df = con.execute(
    "SELECT * FROM iceberg_snapshots('s3://bronze/iceberg/warehouse/bronze_people')"
).df()

print(df)
