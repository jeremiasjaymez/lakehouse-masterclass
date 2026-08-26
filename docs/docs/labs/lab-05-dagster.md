# LAB 5 - Dagster: Orquestación Moderna del Lakehouse

Objetivo: crear un pipeline orquestado bronze -> silver -> gold usando Dagster, integrarlo con Spark y preparar el terreno para IA y Data Quality.

## ¿Por qué Dagster?

Un Lakehouse sin orquestación son scripts cron sueltos y esperanza. Podríamos usar Airflow, pero **Dagster** apuesta a un modelo más moderno: pensás en **assets** (las tablas y datasets que producís) en vez de tasks. Eso te da lineage automático, observabilidad por dataset y testing más fácil. Es open-source, self-hostable, y la API moderna (`ConfigurableResource`, software-defined assets) hace que orquestar un Lakehouse se sienta natural.

## Objetivo del lab

- Instalar y levantar Dagster localmente.
- Crear assets (bronze, silver, gold).
- Integrar Spark dentro de Dagster.
- Ejecutar pipelines manualmente y con schedules.
- Visualizar lineage.

## Prerrequisitos

- LAB 0 (setup global)
- LAB 1 (MinIO)
- LAB 2 (Iceberg)
- LAB 3 (Nessie)
- LAB 4 (Spark)
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

Dagster ya está instalado vía pyproject.toml.

**Vamos a**

- crear un proyecto Dagster
- definir assets
- integrarlo con Spark
- ejecutar pipelines

### PASO 1 - Crear proyecto Dagster

Dagster trae su propio scaffolder. Correlo desde la raíz del repo:

```bash
# 1. Scaffold del proyecto
dagster project scaffold --name lakehouse_dagster
```

Te deja un paquete Python con la estructura mínima (`definitions.py`, `pyproject.toml`,
carpeta de tests). Todavía no tiene assets: eso lo agregamos nosotros.

**Configurar `DAGSTER_HOME`**

Dagster necesita un directorio donde guardar el estado de las corridas (logs, runs,
materializaciones). Sin esa variable, `dagster dev` levanta pero la UI queda en blanco:

```bash
cp lakehouse_dagster/.env.example lakehouse_dagster/.env
```

Editá `lakehouse_dagster/.env` y poné la ruta **absoluta** de tu repo:

```bash
DAGSTER_HOME=/home/tu-usuario/repos/lakehouse-masterclass/.dagster
```

Y creá el directorio, porque Dagster **no lo crea solo**:

```bash
mkdir -p .dagster
```

!!! warning "Tiene que ser absoluta, y tiene que existir"
    `DAGSTER_HOME` no acepta rutas relativas ni `~`. Y si el directorio no existe,
    `dagster dev` corta con:

    ```text
    DagsterInvariantViolationError: $DAGSTER_HOME "..." is not a directory
    or does not exist
    ```

### PASO 2 - Revisar las dependencias del proyecto

El scaffold genera un `pyproject.toml` propio, separado del de la raíz. Este es el
del repo, con todo pineado — un curso donde cada alumno resuelve una versión distinta
de Dagster es un curso irreproducible:

```toml
[project]
name = "lakehouse_dagster"
version = "0.1.0"
description = "Lakehouse Masterclass — Dagster project"
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
    "boto3==1.43.10",
    "dagster==1.13.5",
    "dagster-cloud==1.13.5",
    "ollama==0.6.2",
    "pandas==2.2.3",
    "pyiceberg==0.11.1",
    "pyspark==3.5.4",
]

[project.optional-dependencies]
dev = [
    "dagster-webserver==1.13.5",
    "pytest",
]

[build-system]
requires = ["hatchling>=1.19.0"]
build-backend = "hatchling.build"

[tool.dagster]
module_name = "lakehouse_dagster.definitions"
code_location_name = "lakehouse_dagster"
```

!!! note "Por qué un pyproject aparte"
    El proyecto Dagster se instala como paquete propio (`module_name` en
    `[tool.dagster]` es lo que hace que `dagster dev` lo encuentre). Mantenerlo
    separado te permite deployarlo solo, sin arrastrar Spark ni las dependencias
    de los labs de IA.

**Levantar la UI para verificar que el scaffold quedó bien**

```bash
cd lakehouse_dagster
dagster dev
```

Deberías ver la UI en <http://localhost:3000> sin assets todavía. Cortá con `Ctrl+C`
y seguimos.

### PASO 3 - Crear asset bronze_people

Crear estas carpetas con su `__init__.py` vacío:

- `lakehouse_dagster/lakehouse_dagster/assets/bronze/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/assets/silver/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/assets/gold/__init__.py`

!!! note
    El `__init__.py` vacío es necesario para que `load_assets_from_package_module` los detecte como paquetes Python.

Crear `lakehouse_dagster/lakehouse_dagster/assets/bronze/bronze_people.py`.

### PASO 4 - Crear asset silver_people (transformación)

Crear `lakehouse_dagster/lakehouse_dagster/assets/silver/silver_people.py`.

### PASO 5 - Crear asset gold_people (enriquecido)

Crear `lakehouse_dagster/lakehouse_dagster/assets/gold/gold_people.py`.

### PASO 6 - Registrar assets en init.py

Editar estos archivos:

- `lakehouse_dagster/lakehouse_dagster/assets/__init__.py`
- `lakehouse_dagster/lakehouse_dagster/definitions.py`

### PASO 7 - Crear job que ejecute todos los assets

- `lakehouse_dagster/lakehouse_dagster/jobs/etl_job.py`
- `lakehouse_dagster/lakehouse_dagster/jobs/__init__.py`

### PASO 8 - Crear schedule diario

Cuando quieras correrlo en horario, agregá `schedules/etl_schedule.py` y `schedules/__init__.py`.

### PASO 9 - Levantar Dagster UI

**Desde la raíz del proyecto**

```bash
cd lakehouse_dagster
dagster dev
```

**Abrir**

```text
http://localhost:3000
```

### PASO 10 - Ejecutar pipeline manualmente

En Dagster UI:

- Abrí <http://127.0.0.1:3000/assets>
- Ir a Assets
- Seleccionar todas las tablas
- Click en Materialize
- Dagster ejecutará `bronze_people`, `silver_people` y `gold_people`

### PASO 11 - Ver lineage

En la UI:

- Ir a Assets
- Click en `gold_people`
- Verás el grafo: `bronze_people -> silver_people -> gold_people`

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Dagster levanta sin errores
- Podés ver los assets en la UI
- Podés ejecutar el pipeline
- El lineage se muestra correctamente
- Los assets se ejecutan en orden

## ¡Momento Click! 🎯

!!! success "Lineage automático + observabilidad de assets"
    1. Materialización inicial: en la UI ir a **Assets**, seleccionar todas las tablas
       y hacer **Materialize**.
    2. Hacer click en `gold_people` → vas a ver el grafo:
       `bronze_people → silver_people → gold_people`
    3. Ahora **rompé el pipeline a propósito**: renombrá el CSV o cambiá su path
       en `bronze_people.py`. Re-materializá → Dagster muestra exactamente
       qué falló y qué assets downstream quedaron sin datos válidos.

    Eso es lo que no tenés con scripts sueltos + cron: **lineage, observabilidad y
    manejo de fallos integrados**. Dagster sabe qué alimenta qué sin que lo
    configures explícitamente.

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`Port 3000 already in use`**
    ```bash
    lsof -i :3000
    kill -9 <PID>
    ```
    O cambiá el puerto: `dagster dev --port 3001`.

    **`ModuleNotFoundError: lakehouse_dagster`** → el paquete no está instalado en el venv.
    ```bash
    uv pip install -e ./lakehouse_dagster --no-deps
    ```

    **Assets no aparecen en la UI** → verificar que `definitions.py` importa y
    registra el módulo correspondiente con `load_assets_from_package_module`.

    **`dagster dev` corre pero la UI está en blanco** → verificar que
    `DAGSTER_HOME` apunta a un directorio existente. Crealo si no existe:
    ```bash
    mkdir -p .dagster
    ```

## Resultado esperado

Al finalizar este lab, deberías tener:

- Un proyecto Dagster funcionando
- Assets bronze -> silver -> gold
- Un job ETL
- Un schedule diario
- Lineage visual
- Integración lista para Spark e IA
- Este es el motor de orquestación del Lakehouse.