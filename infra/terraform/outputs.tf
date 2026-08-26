output "buckets_creados" {
  description = "Buckets del medallón aprovisionados en MinIO"
  value = [
    minio_s3_bucket.bronze.bucket,
    minio_s3_bucket.silver.bucket,
    minio_s3_bucket.gold.bucket,
    minio_s3_bucket.platinum.bucket, # el único que Terraform crea de cero
  ]
}

output "vault_secret_path" {
  description = "Path completo del secreto en Vault (lo leen Spark y Dagster)"
  value       = vault_kv_secret_v2.minio_creds.path
}
