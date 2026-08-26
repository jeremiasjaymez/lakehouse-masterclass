# LAB 7 - Terraform: Infraestructura como Código para el Lakehouse

!!! tip
    En este lab vas a crear infraestructura reproducible con Terraform, levantar servicios del Lakehouse con módulos y preparar la base para CI/CD.

## ¿Por qué Terraform?

Hasta ahora levantamos todo con `docker compose up`. Sirve, pero no escala: si querés replicar el stack en otra máquina o nube, terminás copiando comandos a mano. **Terraform** declara la infra como código versionable — los mismos archivos sirven para tu laptop (provider Docker), para Hetzner (provider hcloud) o para cualquier nube. Si mañana querés migrar, cambiás el provider, no toda la arquitectura.

## Atención: Terraform tampoco es open source

!!! danger "Misma historia que Vault, mismo mes"
    Si venís del [Lab 6](lab-06-vault.md#atencion-vault-ya-no-es-open-source) ya
    conocés el patrón. En **agosto de 2023**, en el mismo anuncio, HashiCorp
    relicenció **Terraform** de MPL-2.0 a **BUSL-1.1**. Desde 2025 el licenciante
    es **IBM**:

    ```text
    Licensor: International Business Machines Corporation (IBM)
    ```

    Usar Terraform para tu infra está permitido. Ofrecer un producto que compita
    con HashiCorp usando Terraform, no. Es *source-available*, no libre.

    Vale la pena que registres el detalle: **dos de las herramientas de esta
    masterclass cambiaron de licencia el mismo día**. Eso no es mala suerte, es un
    patrón de la industria — capital de riesgo que necesita monetizar. Cuando elegís
    una herramienta, estás apostando también a su modelo de negocio.

### El fork libre: OpenTofu

**OpenTofu** es el fork de Terraform bajo la **Linux Foundation**, licencia
**MPL-2.0**, con releases activas. Es un reemplazo directo:

```bash
# Instalar (ver https://opentofu.org/docs/intro/install/)
curl -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
chmod +x install-opentofu.sh && ./install-opentofu.sh --install-method deb
```

Y después, **los mismos comandos con `tofu` en vez de `terraform`**:

```bash
cd infra/terraform
tofu init
tofu plan
tofu apply
```

!!! success "No hay que tocar el código"
    `main.tf`, `variables.tf` y `outputs.tf` de este repo funcionan tal cual: la
    sintaxis HCL es la misma y los dos providers que usamos
    (`aminueza/minio` y `hashicorp/vault`) están publicados en el registry de
    OpenTofu. Lo único que cambia es el binario que ejecuta el plan y el nombre
    del archivo de estado por defecto.

### ¿Qué usamos en el curso?

Seguimos con **Terraform** como camino principal, por la misma razón que con Vault:
es lo que vas a encontrar en el trabajo. Pero si tu objetivo es un stack sin
restricciones de licencia, `tofu` es un reemplazo directo — y ahora sabés que la
decisión existe.

## Objetivo del lab

- Instalar Terraform.
- Crear un proyecto IaC.
- Crear módulos para MinIO, Nessie, Spark y Vault.
- Ejecutar terraform init, plan, apply.
- Versionar infraestructura como código.

## Prerrequisitos

- LAB 0 a LAB 6 completados.
- Docker funcionando.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

Terraform se instala directamente en WSL2.

### PASO 1 - Instalar Terraform en Ubuntu

```bash
sudo apt-get update && sudo apt-get install -y \
  gnupg software-properties-common curl lsb-release
```

```bash
curl -fsSL https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
```

```bash
gpg --no-default-keyring \
    --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    --fingerprint
```

```bash
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list > /dev/null
```

```bash
sudo apt-get update && sudo apt-get install -y terraform
terraform -version
```

**Resumen del flujo Terraform**

- `terraform init`: prepara el directorio y descarga providers.
- `terraform validate`: valida sintaxis y referencias internas sin tocar infraestructura.
- `terraform plan`: muestra qué cambios se aplicarían.
- `terraform apply`: ejecuta el plan y actualiza el state.
- `terraform destroy`: elimina lo que Terraform creó.

**Comandos esenciales**

```text
terraform init
Descarga providers a .terraform/ y crea .terraform.lock.hcl con las versiones
Una vez al clonar el repo, o cuando agregás/cambiás un provider
terraform fmt
Formatea los .tf (estilo canónico)
Antes de commitear
terraform validate
Valida sintaxis y referencias internas (no consulta APIs)
En CI antes de plan
terraform plan
Lee el state, refresca contra la API real, calcula el diff. No cambia nada
Siempre antes de apply
terraform apply
Re-calcula el plan y lo ejecuta. Pide confirmación interactiva salvo con -auto-approve
Para aplicar cambios
terraform destroy
Borra todos los recursos del state. Es apply con plan de destrucción
Limpiar el entorno
```

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

!!! warning
    No ejecutes `terraform apply` sin revisar antes el `plan`, especialmente cuando el lab ya tenga recursos corriendo.

### PASO 2 - Crear carpeta de infraestructura

**En la raíz del repo**

```bash
mkdir -p infra/terraform
cd infra/terraform
```

Inicializar con `.gitignore` desde el arranque:

```text
.terraform/
*.tfstate
*.tfstate.*
crash.log
*.tfvars
!*.tfvars.example
```

```bash
docker compose up -d
```

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

**Outputs esperados**

```text
buckets_creados = ["bronze", "silver", "gold"]
vault_secret_path = "secret/data/minio"
```

```bash
python ../../src/spark/09_spark_with_vault.py
```

```bash
terraform plan
terraform apply
```

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Terraform instalado
- Módulos creados
- terraform init funciona
- terraform plan muestra recursos
- terraform apply levanta toda la infraestructura
- Contenedores corriendo correctamente

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- Infraestructura del Lakehouse automatizada
- Módulos Terraform para cada servicio
- Capacidad de levantar todo con un solo comando
- Base para CI/CD en el Lab 8
- Este lab convierte tu Lakehouse en un sistema reproducible y profesional.