# LAB 6 - Vault: Secret Management para el Lakehouse

!!! tip
    En este lab vas a instalar y ejecutar HashiCorp Vault en modo dev, crear secretos, leerlos desde Python y preparar la integración con Dagster, Spark y Terraform.

## ¿Por qué Vault?

Las credenciales hardcodeadas en `docker-compose.yml` están OK para una demo, pero en cualquier ambiente real son un disparo en el pie. **HashiCorp Vault** te da un servicio centralizado para guardar secretos, rotarlos, auditarlos y entregarlos solo a los procesos autorizados. Lo importante no es Vault en sí — es entender el **patrón**: tus pipelines piden secretos a un servicio, nunca los conocen estáticamente. Si mañana querés usar OpenBao o el secret manager de tu cloud, el patrón es el mismo.

## Atención: Vault ya no es open source

!!! danger "El lab de soberanía sobre una herramienta que dejó de ser libre"
    Esta masterclass se vende como stack 100% open-source. Vault es la excepción, y
    preferimos decírtelo de frente en vez de que lo descubras en una auditoría.

    En **agosto de 2023** HashiCorp relicenció Vault (y Terraform, Consul, Nomad y
    Packer) de **MPL-2.0** a **BUSL-1.1** — *Business Source License*. En **2025**
    HashiCorp fue adquirida por **IBM**. Hoy el `LICENSE` del repo dice:

    ```text
    Licensor: International Business Machines Corporation (IBM)
    ```

    **BUSL no es open source.** Es *source-available*: podés leer el código y usarlo,
    pero tiene una restricción de uso (no podés ofrecer un servicio que compita con
    el licenciante) y recién se convierte en licencia libre pasado un plazo — cuatro
    años, versión por versión.

    Para este lab no cambia nada: correr Vault en tu laptop está permitido. Pero si
    mañana tu empresa ofrece un producto sobre Vault, esa cláusula es un problema
    legal, no técnico.

### El fork libre: OpenBao

Cuando HashiCorp cambió la licencia, la comunidad forkeó la última versión MPL. Ese
fork es **OpenBao**, hoy bajo la **Linux Foundation** y licencia **MPL-2.0**, con
releases activas.

Es compatible a nivel de API con Vault, así que **el cambio es una línea**:

```yaml
# docker-compose.vault.yml — versión OpenBao
services:
  vault:
    image: openbao/openbao:latest      # antes: hashicorp/vault:1.18.5
    container_name: vault
    ports:
      - "8200:8200"
    environment:
      BAO_DEV_ROOT_TOKEN_ID: root      # antes: VAULT_DEV_ROOT_TOKEN_ID
      BAO_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
```

Los paths HTTP son los mismos (`/v1/secret/data/...`), así que
`src/vault/read_secrets.py` y el `VaultResource` de Dagster **funcionan sin tocar una
línea**. La CLI se llama `bao` en vez de `vault`.

!!! success "El verdadero momento click de este lab"
    El patrón "pedí los secretos a un servicio" es lo que tenés que aprender, y es
    **portable entre implementaciones**. Por eso el código lee de una URL y no de un
    SDK propietario: cambiar Vault por OpenBao no te obliga a reescribir los pipelines.

    Esa es la definición práctica de soberanía tecnológica — no "usar cosas gratis",
    sino **poder cambiar de proveedor sin reescribir tu plataforma**. La licencia de
    una herramienta es una decisión de arquitectura, igual que el formato de tabla.

### ¿Qué usamos en el curso?

Seguimos con **HashiCorp Vault** como camino principal, por una razón pragmática:
es lo que te vas a encontrar en el 90% de las empresas y lo que aparece en las
búsquedas laborales. Pero ahora sabés que existe la alternativa libre y cómo migrar.

## Objetivo del lab

- Levantar Vault localmente con Docker.
- Crear secretos (MinIO, Spark, Nessie, etc.).
- Leer secretos desde Python.
- Integrar Vault con pipelines.
- Entender políticas y tokens.

## Prerrequisitos

- LAB 0 a LAB 5 completados.
- Docker funcionando.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

Vault se ejecutará en modo dev (ideal para labs).

### PASO 1 - Crear archivo docker-compose para Vault

**En la raíz del repo**

Creá `docker-compose.vault.yml`.

### PASO 2 - Levantar Vault

```bash
docker compose -f docker-compose.vault.yml up -d
```

**Ver logs**

```bash
docker logs -f vault
```

**Deberías ver**

- Root Token: root

### PASO 3 - Exportar variables de entorno

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root
```

### PASO 4 - Validar que Vault está vivo

Instalá Vault CLI si todavía no lo tenés:

```bash
sudo snap install vault --channel=1.18/stable
```

```bash
vault status
```

**Deberías ver**

- Initialized: true
- Sealed: false

### PASO 5 - Habilitar el motor de secretos KV

**Para dev no es necesario**

```bash
vault secrets enable -path=secret kv
```

### PASO 6 - Crear secretos del Lakehouse

**Credenciales de MinIO**

```bash
vault kv put secret/minio \
    access_key=admin \
    secret_key=password
```

**Credenciales de Nessie**

```bash
vault kv put secret/nessie \
    user=admin \
    password=admin
```

**Configuración de Spark (opcional)**

```bash
vault kv put secret/spark \
    master=local[*]
```

### PASO 7 - Leer un secreto desde CLI

```bash
vault kv get secret/minio
```

### PASO 8 - Leer secretos desde Python

**Crear archivo**

`src/vault/read_secrets.py`

**Ejecutar**

```bash
python src/vault/read_secrets.py
```

**Deberías ver**

- MinIO credentials: {'access_key': 'admin', 'secret_key': 'password'}

### PASO 9 - Integrar Vault con Spark (opcional)

Crear y ejecutar `src/spark/09_spark_with_vault.py`.

```bash
vault kv put secret/minio access_key=wrong secret_key=wrong
```

```bash
python src/spark/09_spark_with_vault.py
```

```bash
vault kv put secret/minio access_key=admin secret_key=password
```

```bash
python src/spark/09_spark_with_vault.py
```

!!! warning
    Este ejercicio muestra por qué conviene desacoplar secretos y código: cambiás el secreto una vez y el comportamiento del pipeline cambia sin editar scripts.

### PASO 10 - Integrar Vault con Dagster (opcional)

Prepará estos archivos:

- `lakehouse_dagster/lakehouse_dagster/resources/vault_resource.py`
- `lakehouse_dagster/lakehouse_dagster/resources/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/definitions.py`
- `lakehouse_dagster/lakehouse_dagster/assets/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/assets/vault_demo/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/assets/vault_demo/minio_check.py`

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Vault levanta correctamente
- Podés crear y leer secretos
- Python puede leer secretos vía API
- Dagster puede consumir secretos
- Spark puede usar secretos para conectarse a MinIO

## ¡Momento Click! 🎯

!!! success "Secret rotation en vivo sin tocar el código"
    1. **Rompé las credenciales**:
    ```bash
    docker exec -it vault vault kv put secret/minio access_key=wrong secret_key=wrong
    ```
    2. En la UI de Dagster, re-materializació el asset `minio_connectivity_check` → **rojo**.
       El log muestra `InvalidAccessKeyId` — MinIO rechazó las creds inválidas.
    3. **Restaurá las credenciales**:
    ```bash
    docker exec -it vault vault kv put secret/minio access_key=admin secret_key=password
    ```
    4. Re-materializá de nuevo → **verde**.

    El código del asset **nunca cambió**. Ese es el patrón de secretos externalizado:
    el pipeline pide credenciales al runtime, no las conoce en tiempo de compilación.
    En producción, esto te permite rotar claves de acceso sin redeploys.

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`connection refused` en :8200** → Vault no está corriendo.
    ```bash
    docker compose -f docker-compose.vault.yml up -d
    ```

    **`permission denied` en CLI** → faltan las variables de entorno:
    ```bash
    export VAULT_ADDR=http://localhost:8200
    export VAULT_TOKEN=root
    ```

    **Vault sella al reiniciar el contenedor** → en modo dev se pierde el estado.
    Hay que volver a ejecutar los `vault kv put` del PASO 6 después de cada
    `docker compose up`.

    **Asset `minio_connectivity_check` falla con `ResourceNotFound`** →
    verificar que `VaultResource` está registrado en `definitions.py` bajo la
    clave `"vault"`.

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- Vault funcionando como secret manager
- Secretos del Lakehouse centralizados
- Integración con Python, Spark y Dagster
- Base para Terraform y CI/CD
- Este lab completa la capa de seguridad del Lakehouse.