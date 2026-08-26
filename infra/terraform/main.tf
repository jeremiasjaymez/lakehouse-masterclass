# PASO 11 — Terraform: bootstrap declarativo del stack
#
# Qué hace este archivo:
#   1. Crea los buckets bronze/silver/gold en MinIO  (opción A)
#   2. Siembra el secreto "minio" en Vault            (opción B)
#
# Qué NO hace: levantar contenedores.
# Para eso usá: docker compose up -d
# Después de eso, corrés: terraform apply
#
# Flujo completo:
#   docker compose up -d        ← infraestructura (contenedores)
#   terraform apply             ← estado inicial (buckets + secretos)
#   python src/spark/...        ← pipelines
#   dagster dev                 ← orquestación

terraform {
  required_version = ">= 1.5.0" # import {} blocks requieren 1.5+
  required_providers {
    minio = {
      source  = "aminueza/minio"
      version = "~> 2.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
  }
}

# Provider MinIO — asume docker compose ya corriendo en :9000
provider "minio" {
  minio_server   = var.minio_server
  minio_user     = var.minio_user
  minio_password = var.minio_password
  minio_ssl      = false
}

# Provider Vault — asume docker compose ya corriendo en :8200
provider "vault" {
  address = var.vault_addr
  token   = var.vault_token
}

# ─────────────────────────────────────────────
# A) Buckets del medallón
# ─────────────────────────────────────────────
#
# bronze/silver/gold ya existían antes de este paso — los import blocks
# le dicen a Terraform "adoptá este recurso, no lo crees de nuevo".
# Si el state se borra, el próximo apply re-importa solo.
# Buckets nuevos (ej: platinum) no necesitan import block: Terraform los crea.

import {
  to = minio_s3_bucket.bronze
  id = "bronze"
}

import {
  to = minio_s3_bucket.silver
  id = "silver"
}

import {
  to = minio_s3_bucket.gold
  id = "gold"
}

resource "minio_s3_bucket" "bronze" {
  bucket = "bronze"
  acl    = "private"
}

resource "minio_s3_bucket" "silver" {
  bucket = "silver"
  acl    = "private"
}

resource "minio_s3_bucket" "gold" {
  bucket = "gold"
  acl    = "private"
}

resource "minio_s3_bucket" "platinum" {
  bucket = "platinum"
  acl    = "private"
}

# ─────────────────────────────────────────────
# B) Secreto MinIO en Vault (el que usan los pasos 9 y 10)
# ─────────────────────────────────────────────

# Nota: Vault en modo dev ya crea el mount "secret" automáticamente.
# No lo gestionamos con Terraform para no chocar con él.

resource "vault_kv_secret_v2" "minio_creds" {
  mount = "secret"
  name  = "minio"

  data_json = jsonencode({
    access_key = var.minio_user
    secret_key = var.minio_password
  })

  # Si cambiás bucket plantium y hacés terraform apply, veras como cambia.
}
