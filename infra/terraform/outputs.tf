output "buckets_creados" {
  description = "Buckets del medallón aprovisionados en MinIO"
  value       = [minio_s3_bucket.bronze.bucket, minio_s3_bucket.silver.bucket, minio_s3_bucket.gold.bucket]
}

output "vault_secret_path" {
  description = "Path completo del secreto en Vault (usado por pasos 9 y 10)"
  value       = vault_kv_secret_v2.minio_creds.path
}
