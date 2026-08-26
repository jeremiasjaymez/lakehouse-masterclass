# LAB 7 - Terraform: Infraestructura como Código para el Lakehouse

!!! tip
    En este lab vas a declarar el estado inicial del Lakehouse como código: los buckets del medallón en MinIO y el secreto que consumen Spark y Dagster.

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
- Entender qué gestiona Terraform en este stack — y qué **no**.
- Declarar los buckets del medallón y el secreto de Vault como código.
- Adoptar recursos que ya existían con bloques `import {}`.
- Ejecutar `init`, `fmt`, `validate`, `plan`, `apply`.

## Prerrequisitos

- LAB 0 a LAB 6 completados.
- Docker funcionando, con `docker compose up -d` ya levantado (MinIO + Vault).
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

**Los comandos que vas a usar**

| Comando | Qué hace | Cuándo |
|---|---|---|
| `terraform init` | Descarga providers a `.terraform/` y escribe `.terraform.lock.hcl` | Al clonar el repo, o al cambiar un provider |
| `terraform fmt` | Formatea los `.tf` al estilo canónico | Antes de commitear |
| `terraform validate` | Valida sintaxis y referencias internas (no consulta APIs) | En CI, antes del plan |
| `terraform plan` | Lee el state, refresca contra la API real, calcula el diff. **No cambia nada** | Siempre antes de `apply` |
| `terraform apply` | Re-calcula el plan y lo ejecuta. Pide confirmación salvo con `-auto-approve` | Para aplicar cambios |
| `terraform destroy` | Borra los recursos del state. Es un `apply` con plan de destrucción | Para limpiar el entorno |

!!! warning
    No ejecutes `terraform apply` sin revisar antes el `plan`, especialmente cuando
    el lab ya tenga recursos corriendo.

### PASO 2 - Qué gestiona Terraform acá (y qué no)

Esta es **la confusión más común del curso**, así que la sacamos del medio antes de
escribir una sola línea de HCL.

Terraform **no levanta los contenedores**. Eso lo hace Docker Compose. Lo que Terraform
gestiona en este stack es el **estado inicial**: los recursos que viven *adentro* de
esos servicios y que tus pipelines asumen que existen.

```text
docker compose up -d     ← runtime      (MinIO, Nessie y Vault corriendo)
terraform apply          ← estado inicial (buckets + secreto en Vault)
python src/spark/...     ← pipelines
dagster dev              ← orquestación
```

!!! danger "El orden importa"
    Los providers `minio` y `vault` se conectan por HTTP a `localhost:9000` y
    `localhost:8200`. Si corrés `terraform apply` con los contenedores apagados,
    falla con un error de conexión — no con un mensaje lindo.

¿Y por qué no gestionar también los contenedores con el provider `docker`? Se puede,
pero para un curso en una laptop agrega una capa de indirección que no enseña nada:
Compose ya declara el runtime en YAML versionado. Lo que Compose **no** sabe hacer es
"asegurate de que existan estos cuatro buckets y este secreto, y avisame si alguien
los cambió". Eso es exactamente el trabajo de Terraform.

### PASO 3 - Recorrer el código de infra

La carpeta ya está en el repo. Es un módulo raíz plano — tres archivos, sin
sub-módulos: para cuatro buckets y un secreto, la indirección de un `module {}` sería
ceremonia sin beneficio.

```text
infra/terraform/
├── main.tf         # providers + recursos
├── variables.tf    # credenciales parametrizadas (con defaults de demo)
├── outputs.tf      # qué te devuelve el apply
└── .gitignore      # state y tfvars nunca se commitean
```

**El `.gitignore` de infra, desde el arranque**

```text
.terraform/
*.tfstate
*.tfstate.*
crash.log
*.tfvars
!*.tfvars.example
```

!!! danger "El state tiene tus secretos en texto plano"
    `terraform.tfstate` guarda el valor de **todos** los atributos, incluidos los
    marcados `sensitive`. Acá eso es el token de Vault y el password de MinIO.
    Commitear el state es una fuga de credenciales, no un descuido de estilo.

**Los providers** (`main.tf`)

```hcl
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
```

**Adoptar lo que ya existe: los bloques `import {}`**

Los buckets `bronze`, `silver` y `gold` los creaste **a mano en el Lab 1**. Terraform
no lo sabe: para él son recursos que no están en su state, así que intentaría crearlos
y chocaría contra un `BucketAlreadyOwnedByYou`.

Los bloques `import {}` resuelven eso de forma declarativa:

```hcl
import {
  to = minio_s3_bucket.bronze
  id = "bronze"
}

resource "minio_s3_bucket" "bronze" {
  bucket = "bronze"
  acl    = "private"
}
```

Traducido: *"este recurso ya existe en el mundo real con id `bronze`, adoptalo en vez
de crearlo"*.

!!! note "`import {}` vs `terraform import`"
    El comando `terraform import` existe desde siempre, pero es imperativo: lo corrés
    a mano, una vez, y no queda rastro en el código. El **bloque** `import {}` (Terraform
    1.5+) es declarativo y vive en el repo: cualquiera que clone y haga `apply`
    re-importa solo. Es la diferencia entre "yo ya lo importé en mi máquina" y
    "el repo sabe cómo adoptarlo".

**El secreto en Vault**

```hcl
resource "vault_kv_secret_v2" "minio_creds" {
  mount = "secret"
  name  = "minio"

  data_json = jsonencode({
    access_key = var.minio_user
    secret_key = var.minio_password
  })
}
```

Este es el secreto que leen `src/spark/09_spark_with_vault.py` y el `VaultResource` de
Dagster. Hasta ahora lo sembraste a mano con `vault kv put` en el Lab 6: acá pasa a
ser código.

!!! note "El mount `secret` no lo gestionamos"
    Vault en modo dev crea el mount `secret` solo al arrancar. Declararlo en Terraform
    chocaría con el que ya existe, así que lo dejamos afuera a propósito.

### PASO 4 - init, plan, apply

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # ajustá si cambiaste credenciales
terraform init
```

`init` descarga los dos providers y escribe `.terraform.lock.hcl` — ese archivo **sí**
se commitea: pinea las versiones exactas para todos los alumnos.

```bash
terraform fmt
terraform validate
terraform plan
```

En el `plan` vas a ver algo importante: tres recursos **a importar** y uno **a crear**.

```bash
terraform apply
```

**Outputs esperados**

```text
buckets_creados = [
  "bronze",
  "silver",
  "gold",
  "platinum",
]
vault_secret_path = "secret/data/minio"
```

### PASO 5 - `platinum`: el recurso que Terraform crea de cero

`bronze`, `silver` y `gold` se adoptan. **`platinum` no tiene bloque `import {}`**, así
que Terraform lo crea desde cero — es el ejemplo de "recurso nuevo, nacido declarativo".

Abrí la consola de MinIO en <http://localhost:9001> y confirmá que apareció.

Ahora probá el ciclo completo de IaC. Borrá el bucket `platinum` a mano desde la
consola de MinIO y corré:

```bash
terraform plan
```

Terraform detecta el **drift**: alguien tocó la infra por fuera del código. Y te ofrece
volver al estado declarado:

```bash
terraform apply
```

**Validar que el secreto quedó bien sembrado**

```bash
cd ../..                                   # todos los scripts corren desde la raíz
python src/spark/09_spark_with_vault.py
```

Si Spark levanta leyendo las credenciales desde Vault, el circuito del Lab 6 ahora
está declarado como código.

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- `terraform -version` responde
- `terraform init` descarga los providers `minio` y `vault`
- `terraform plan` muestra 3 recursos a importar y 1 a crear
- `terraform apply` termina sin errores
- El bucket `platinum` aparece en la consola de MinIO
- `terraform output` muestra los cuatro buckets y el path del secreto
- `09_spark_with_vault.py` lee las credenciales que sembró Terraform
- `terraform.tfstate` **no** aparece en `git status`

## ¡Momento Click! 🎯

!!! success "El state es descartable, el código no"

    Este es el experimento que separa "corrí unos comandos" de "entendí IaC".

    **1. Borrá el state entero.** Sí, entero:

    ```bash
    cd infra/terraform
    rm -f terraform.tfstate terraform.tfstate.backup
    ```

    Acabás de tirar a la basura todo lo que Terraform sabía sobre tu infraestructura.
    En un flujo imperativo esto sería una catástrofe.

    **2. Mirá los buckets en MinIO.** Siguen ahí. Los datos no se tocaron.

    **3. Corré `terraform apply` de nuevo.**

    ```bash
    terraform apply
    ```

    Terraform re-importa `bronze`, `silver` y `gold` gracias a los bloques `import {}`,
    detecta que `platinum` ya existe, reconstruye el state completo y te dice
    **"No changes"**.

    ---

    **Eso es el click.** El state no es la fuente de verdad: es un caché. La fuente
    de verdad es el código, y el código sabe reconstruirse solo. Es la misma
    diferencia que viste en el Lab 3 entre "hacer un backup del CSV" y "tener el
    historial en Nessie".

    Y ahora hacelo al revés: borrá `platinum` a mano en la consola de MinIO y corré
    `terraform plan`. Terraform ve el drift y te propone arreglarlo. **La infra
    dejó de ser algo que hacés y pasó a ser algo que declarás.**

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`Error: Get "http://localhost:9000/...": dial tcp: connection refused`**

    Los contenedores no están arriba. Terraform no los levanta:

    ```bash
    docker compose up -d && docker ps
    ```

    **`Error: Cannot import non-existent remote object`** → el bucket del bloque
    `import {}` no existe en MinIO. Crealo desde la consola (<http://localhost:9001>)
    o comentá el `import {}` para que Terraform lo cree él.

    **`Error: BucketAlreadyOwnedByYou`** → estás creando un bucket que ya existe sin
    su bloque `import {}`. Agregalo, o borrá el bucket a mano.

    **`Error: failed to create limited child token: permission denied`** → el token
    de Vault venció o no es el de dev. Verificá:

    ```bash
    export VAULT_ADDR=http://localhost:8200
    export VAULT_TOKEN=root
    vault status
    ```

    **`terraform: command not found` después de instalar** → abrí una terminal nueva
    o `hash -r`, el shell tiene cacheada la tabla de comandos.

    **`Error: Invalid provider registry host`** con OpenTofu → borrá `.terraform/` y
    volvé a correr `tofu init`: el lock file de Terraform apunta al registry de
    HashiCorp.

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- Los cuatro buckets del medallón declarados como código, no creados a mano.
- El secreto de MinIO en Vault sembrado por Terraform, consumido por Spark y Dagster.
- Un `apply` idempotente: podés correrlo mil veces y el resultado es el mismo.
- Un state descartable, reconstruible desde el código con los bloques `import {}`.
- Claridad sobre el límite: **Compose gestiona el runtime, Terraform el estado inicial.**
- La base para el Lab 8, donde `fmt`, `validate` y `plan` pasan a correr en CI.
