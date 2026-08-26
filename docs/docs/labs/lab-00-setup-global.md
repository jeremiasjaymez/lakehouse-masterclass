# LAB 0 - Setup Global del Entorno

Comenzamos con el Lab 0, que prepara el entorno base para los demás labs.

Es el más importante porque prepara todo el entorno para los demás labs.

!!! tip "¿No querés instalar nada, o se te rompió el setup?"
    El repo trae un **devcontainer**: Python 3.12, Java 17, Docker y uv ya
    configurados. Abrilo en **GitHub Codespaces** (botón `Code` → `Codespaces` →
    `Create codespace`) o en VS Code con *Dev Containers: Reopen in Container*, y
    todo este lab ya está hecho.

    Es también el plan B oficial de la masterclass: si tu WSL2 o tu Docker no
    arrancan el día de la clase, entrás por el navegador y seguís sin perderte nada.

    Los labs 9 y 11 (IA) necesitan además `bash .devcontainer/setup-ollama.sh`.

## Objetivo

- Configurar un entorno Linux reproducible para ejecutar todo el Lakehouse localmente:
- WSL2
- Ubuntu 24.04 LTS
- Docker Desktop
- uv (gestor de entornos + dependencias)
- Proyecto base con pyproject.toml
- Validación de Python, Spark y MinIO

## Prerrequisitos

- Windows 10/11
- Virtualización habilitada
- **25 GB libres**. El desglose aproximado: imágenes Docker (~3 GB), jars de
  Spark en `~/.ivy2/` (~300 MB), dependencias Python (~2 GB), modelos de Ollama
  (~5.5 GB entre `llama3.1` y `nomic-embed-text`) y los datos del Lakehouse.

## Instalación y setup

### PASO 1 - Instalar WSL2

**Abrir PowerShell como Administrador**

```bash
wsl --install
```

**Seleccionar**

- Ubuntu 24.04 LTS
- Reiniciar.

### PASO 2 - Configurar Ubuntu

Abrir Ubuntu desde el menú Inicio. Crear usuario y contraseña.

**Validar la versión instalada**

```bash
cat /etc/os-release
```

**Actualizar paquetes**

```bash
sudo apt update && sudo apt upgrade -y
```

### PASO 3 - Instalar Docker Desktop + Integración WSL2

Instalar Docker Desktop desde la web oficial https://www.docker.com/products/docker-desktop/
Tested with 4.73.1
Abrir Settings -> Resources -> WSL Integration
Activar Ubuntu

**Validar**

```bash
docker run hello-world
```

### PASO 4 - Instalar uv

```bash
# curl -LsSf https://astral.sh/uv/install.sh | sh
curl -LsSf https://astral.sh/uv/0.11.14/install.sh | sh
```

**Validar**

```bash
uv --version
```

### PASO 5 - Crear proyecto base

```bash
mkdir lakehouse-masterclass
cd lakehouse-masterclass
uv init
```

**Esto crea**

- pyproject.toml
- src/
- tests/

### PASO 6 - Crear archivo pyproject.toml

**Reemplazar el contenido por**

```toml
[project]
name = "lakehouse-masterclass"
version = "1.0.0"
description = "Open-Source Lakehouse Masterclass Environment"
requires-python = ">=3.12,<3.13"

dependencies = [
    "pyspark==3.5.4",
    "pyiceberg[pyarrow]==0.11.1",
    "boto3==1.43.8",
    "dagster==1.13.5",
    "dagster-webserver==1.13.5",
    "python-dotenv==1.2.2",
    "requests==2.32.3",
    "pandas==2.2.3",
    "duckdb==1.5.2",
    "ollama==0.6.2",
]

[dependency-groups]
dev = [
    "pytest==9.0.3",
    "jupyterlab==4.5.7",
]
```

### PASO 7 - Crear entorno virtual

```bash
uv venv
source .venv/bin/activate
```

### PASO 8 - Instalar dependencias

```bash
uv sync
```

### PASO 9 - Validar Python

```bash
python -c "print('Python OK')"
```

### PASO 10 - Validar Spark

Crear archivo en `src/spark/01_test_spark.py`.

**Ejecutar**

```bash
python src/spark/01_test_spark.py
```

### PASO 11 - (Recomendado) Descargar los modelos de IA por adelantado

Los Labs 9 y 11 usan modelos locales con Ollama. Son ~5.5 GB de descarga, así que
conviene bajarlos **ahora** y no en medio de la clase.

!!! tip "Modo curso en vivo"
    Este paso es **pre-work obligatorio**: pedile a los alumnos que lo corran antes
    de la sesión. Descargar 5.5 GB × N alumnos sobre el wifi de una sala es la forma
    más rápida de perder media hora de workshop.

```bash
sudo apt-get install -y zstd
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1          # ~4.7 GB — generación (SQL, respuestas RAG)
ollama pull nomic-embed-text  # ~275 MB — embeddings
```

**Validar**

```bash
ollama list
```

Deberías ver los dos modelos listados. Si no vas a hacer los labs de IA, podés
saltear este paso y volver cuando llegues al Lab 9.

## Validación final

- Si todo está correcto, deberías tener:
- WSL2 funcionando
- Ubuntu actualizado
- Docker operativo
- uv instalado
- Proyecto Python creado
- Dependencias instaladas
- Spark funcionando

## Resultado esperado

- Un entorno Linux reproducible, aislado, moderno y listo para ejecutar todos los labs del Lakehouse.