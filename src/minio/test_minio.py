import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="password",
)

# Listar buckets
print("Buckets:", s3.list_buckets())

# Subir archivo
s3.upload_file("data/bronze/people.csv", "bronze", "people.csv")

# Descargar archivo
s3.download_file("bronze", "people.csv", "data/bronze/people_downloaded.csv")

print("Archivo descargado correctamente.")

resp = s3.list_objects_v2(Bucket="bronze")
print(resp.get("Contents", []))

# s3.create_bucket(Bucket="test-bucket")
# print("Buckets después de crear test-bucket:", s3.list_buckets())

# s3.delete_bucket(Bucket="test-bucket")
# print("Buckets después de eliminar test-bucket:", s3.list_buckets())
