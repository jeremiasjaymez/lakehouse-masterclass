# LAB 8 - CI/CD: GitHub Actions para el Lakehouse

Objetivo: crear pipelines CI/CD que validen Terraform, ejecuten tests, validen Dagster y preparen despliegues automáticos del Lakehouse.

## ¿Por qué CI/CD desde el día 1?

Un Lakehouse "funciona en mi máquina" no es un Lakehouse, es un demo. CI/CD te da dos cosas críticas: **(1)** confianza para mergear cambios sin romper el pipeline de noche, y **(2)** documentación viva de cómo se construye y valida el sistema. GitHub Actions es gratis para repos públicos y open-source. Cuando el repo crezca, los mismos workflows se mueven a GitLab CI o Forgejo Actions sin grandes cambios.

## Objetivo del lab

- Crear los tres workflows de GitHub Actions del repo.
- Validar Terraform sin credenciales (`fmt`, `init -backend=false`, `validate`).
- Lintear y formatear el código Python con `ruff` **pineado**.
- Correr los tests de los assets de Dagster.
- Validar que las definitions de Dagster cargan sin errores.

## Prerrequisitos

- LAB 0 a LAB 7 completados.
- Repositorio GitHub creado y con el código subido.
- Terraform y Dagster funcionando localmente.

## Instalación y setup

GitHub Actions no requiere instalación local. Solo necesitás la carpeta
`.github/workflows/` y que los tres archivos YAML estén commiteados.

### PASO 1 - Crear carpeta de workflows

**En la raíz del repo**

```bash
mkdir -p .github/workflows
```

### PASO 2 - Crear workflow para Terraform

`.github/workflows/terraform.yml`:

```yaml
name: Terraform CI

on:
  push:
    branches: [ "master" ]
  pull_request:

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra/terraform

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.0"

      - name: Terraform fmt
        run: terraform fmt -check -recursive

      - name: Terraform init (sin backend, sin hablar con providers)
        run: terraform init -backend=false

      - name: Terraform validate
        run: terraform validate
```

!!! note "Por qué no hay `terraform plan` acá"
    Un `plan` necesita hablar con MinIO y Vault de verdad, y en el runner de GitHub
    esos servicios no existen. Por eso el CI se queda en la validación **estática**:
    `fmt` verifica estilo, `init -backend=false` resuelve los providers sin tocar el
    state, y `validate` chequea sintaxis y referencias internas. Es lo que se puede
    verificar sin infraestructura — y atrapa la mayoría de los errores de HCL.

### PASO 3 - Crear workflow para Python

`.github/workflows/python.yml`:

```yaml
name: Python CI

on:
  push:
    branches: [ "master" ]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup uv
        uses: astral-sh/setup-uv@v3

      # Ruff pineado: 'uvx ruff' sin versión trae la última release, y una regla
      # nueva puede poner el CI en rojo sin que hayas tocado una línea de código.
      - name: Ruff check
        run: uvx ruff@0.15.14 check .

      - name: Ruff format (check)
        run: uvx ruff@0.15.14 format --check .

  tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: lakehouse_dagster
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install deps
        run: uv sync --extra dev
      - name: Run tests
        run: uv run --extra dev pytest -v
```

Son **dos jobs que corren en paralelo**:

- `lint` no instala nada del proyecto — `uvx` baja ruff aislado y termina en segundos.
- `tests` sí sincroniza el entorno de `lakehouse_dagster` y corre los tests de assets
  (los del [apéndice de testing](../appendix/testing-dagster.md)).

!!! warning "El pin de ruff no es opcional"
    Fijate que la versión aparece **tres veces**: en los dos pasos del workflow y en
    el `CLAUDE.md` del repo. Si corrés `uvx ruff check .` local sin versión y el CI
    corre `ruff@0.15.14`, tarde o temprano vas a discutir con un `E402` que en tu
    máquina no aparece. Local y CI tienen que correr el mismo binario.

### PASO 4 - Crear workflow para Dagster

`.github/workflows/dagster.yml`:

```yaml
name: Dagster CI

on:
  push:
    branches: [ "master" ]
  pull_request:

jobs:
  validate-definitions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup uv
        uses: astral-sh/setup-uv@v3

      - name: Install deps
        run: |
          uv sync
          uv pip install -e ./lakehouse_dagster --no-deps

      - name: Validate Dagster definitions
        run: uv run dagster definitions validate -m lakehouse_dagster.definitions
```

`dagster definitions validate` importa **todo** el objeto `Definitions`: assets, jobs,
schedules y recursos. Si renombraste un asset y quedó una dependencia colgada, o un
`ConfigurableResource` pide un campo que nadie le pasa, el CI se pone en rojo acá — sin
levantar la UI ni materializar nada.

!!! warning "Corre desde la raíz, no desde `lakehouse_dagster/`"
    Es intencional: `uv sync` en la raíz trae `pandas`, `pyspark` y `ollama`, que los
    assets importan. Después `uv pip install -e ./lakehouse_dagster --no-deps` monta el
    paquete encima **sin** re-resolver dependencias. Al revés no funciona.

### PASO 5 - Verificar que los workflows pasan

```bash
git add .github/
git commit -m "ci: add terraform, lint and dagster workflows"
git push
```

Ir a **GitHub → Actions** y verificar que los tres workflows quedan en verde.

!!! tip "Corré las mismas validaciones antes de pushear"
    Todo lo que hace el CI lo podés correr local, y tarda menos que esperar el runner:

    ```bash
    uvx ruff@0.15.14 check . --fix
    uvx ruff@0.15.14 format .
    cd lakehouse_dagster && uv run --extra dev pytest -q
    terraform -chdir=infra/terraform fmt -check
    ```

### PASO 6 - Agregar badges al README

**En tu README.md**

```markdown
[![Terraform](https://github.com/<USER>/<REPO>/actions/workflows/terraform.yml/badge.svg)](https://github.com/<USER>/<REPO>/actions/workflows/terraform.yml)
[![Python CI](https://github.com/<USER>/<REPO>/actions/workflows/python.yml/badge.svg)](https://github.com/<USER>/<REPO>/actions/workflows/python.yml)
[![Dagster](https://github.com/<USER>/<REPO>/actions/workflows/dagster.yml/badge.svg)](https://github.com/<USER>/<REPO>/actions/workflows/dagster.yml)
```

Envolver el badge en un link al workflow hace que se pueda clickear para ver la
última corrida — un badge suelto solo muestra un color.

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Los tres archivos existen en `.github/workflows/`
- **Terraform CI** en verde (`fmt`, `init -backend=false`, `validate`)
- **Python CI** en verde, con sus dos jobs (`lint` y `tests`)
- **Dagster CI** en verde (`definitions validate`)
- Los tres badges se ven en el README y linkean a su workflow
- Un PR de prueba dispara los tres workflows

## ¡Momento Click! 🎯

!!! success "El CI te frena antes de que rompas master"

    Leer tres YAML en verde no enseña nada. Rompelos a propósito:

    **1. Creá una rama y meté una falla de estilo:**

    ```bash
    git checkout -b test-ci
    echo "import os" >> src/spark/01_test_spark.py   # import sin usar
    ```

    **2. Desformateá un archivo de Terraform** — sacale la indentación a
    cualquier bloque de `infra/terraform/main.tf`.

    **3. Rompé un asset de Dagster:** en
    `lakehouse_dagster/lakehouse_dagster/assets/silver/silver_people.py`,
    cambiá el parámetro `bronze_people` por `bronze_peopl`.

    **4. Pusheá y abrí un PR:**

    ```bash
    git commit -am "test: romper el CI a proposito"
    git push -u origin test-ci
    ```

    ---

    Los tres workflows se ponen en rojo, cada uno por su motivo, y **GitHub te
    bloquea el merge**:

    - `Python CI / lint` → `F401 'os' imported but unused`
    - `Terraform CI / fmt` → el diff exacto que esperaba
    - `Dagster CI` → esto:

    ```text
    DagsterInvalidDefinitionError: Input asset "["bronze_peopl"]" is not produced
    by any of the provided asset ops and is not one of the provided sources.
    Did you mean one of the following?
        ["bronze_people"]
    ```

    Ese último es el que más impresiona: **nadie ejecutó el pipeline**. No se levantó
    Spark, no se materializó nada, no hubo un solo dato tocado. Dagster detectó un
    lineage roto **leyendo el grafo**, en 40 segundos, sobre un typo de una letra.
    Con scripts sueltos ese error aparece a las 3 AM del martes.

    Volvé para atrás y borrá la rama:

    ```bash
    git checkout master && git branch -D test-ci
    git push origin --delete test-ci
    ```

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **Los workflows no aparecen en la pestaña Actions** → o los YAML no están en
    `master`, o tienen un error de sintaxis. GitHub ignora silenciosamente un workflow
    mal formado. Validá la indentación con:

    ```bash
    python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/python.yml'))"
    ```

    **`terraform fmt -check` falla en CI pero local está bien** → corré
    `terraform fmt -recursive` desde la raíz, no desde `infra/terraform`. El flag
    `-recursive` del CI mira subcarpetas que tu `fmt` local puede estar salteando.

    **Ruff falla en CI y pasa local** → estás corriendo versiones distintas.
    Verificá con `uvx ruff@0.15.14 --version` y usá siempre el pin.

    **`ModuleNotFoundError` en Dagster CI** → falta el `uv pip install -e
    ./lakehouse_dagster --no-deps`, o lo pusiste antes del `uv sync` (el orden importa:
    sync primero, el paquete encima).

    **Los workflows no corren en tu fork** → GitHub deshabilita Actions en forks por
    defecto. Andá a **Actions → I understand my workflows, go ahead and enable them**.

    **La rama por defecto no es `master`** → los tres workflows filtran por
    `branches: [ "master" ]`. Si tu repo usa `main`, cambialo en los tres archivos o
    los push a la rama principal no van a disparar nada.

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- Tres workflows corriendo en cada push y en cada PR.
- Validación estática de la infraestructura, sin necesidad de credenciales.
- Lint, formato y tests de Python automatizados, con ruff pineado.
- El grafo de assets de Dagster validado sin ejecutar el pipeline.
- Badges clickeables en el README.
- Un repo donde "anda en mi máquina" dejó de ser un argumento válido.
