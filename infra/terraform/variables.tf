variable "minio_server" {
  description = "Host:puerto de MinIO (docker compose)"
  type        = string
  default     = "localhost:9000"
}

variable "minio_user" {
  description = "Usuario admin de MinIO"
  type        = string
  default     = "admin"
}

variable "minio_password" {
  description = "Password admin de MinIO (credencial de demo, no es un secreto real)"
  type        = string
  default     = "password"
}

variable "vault_addr" {
  description = "URL de Vault (docker compose)"
  type        = string
  default     = "http://localhost:8200"
}

variable "vault_token" {
  description = "Token root de Vault (solo modo dev)"
  type        = string
  sensitive   = true
  default     = "root"
}
