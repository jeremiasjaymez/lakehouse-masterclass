# Lakehouse Masterclass

Esta guía funciona como índice de la masterclass y punto de entrada para todos los labs.

## Modos de uso

Hay dos formas de recorrer el material según el contexto:

### Modo curso en vivo (instructor + alumnos)

Ideal para workshops presenciales o sesiones sincrónicas de 4-8 horas.

- El instructor levanta el stack completo antes de empezar (`docker compose up -d`).
- Cada lab se recorre en conjunto: el instructor ejecuta, los alumnos replican.
- **Foco**: los momentos AHA de cada lab. Cada paso tiene un resultado visible concreto.
- Podés saltear los labs opcionales (7-Terraform, 8-CI/CD) si el tiempo es justo.
- Duración estimada: Labs 0-6 en 4 h, Labs 7-11 en otras 3 h.

!!! danger "Pre-work obligatorio para los alumnos"
    Mandá esto **antes** de la sesión. Son ~10 GB de descargas que no querés hacer
    en vivo sobre el wifi de una sala:

    1. Lab 0 completo (WSL2 + Docker + uv + `uv sync`).
    2. `ollama pull llama3.1` y `ollama pull nomic-embed-text` (PASO 11 del Lab 0).
    3. Un `docker compose pull` para bajar MinIO, Nessie y Vault.
    4. Una corrida de `python src/spark/01_test_spark.py`, que cachea ~300 MB de
       jars en `~/.ivy2/`.

### Modo self-paced (autoguiado)

Ideal para estudio individual a tu ritmo.

- Seguí los labs en orden: cada uno asume que el anterior está completo.
- Antes de cada lab, verificá que los servicios del anterior siguen corriendo con `docker ps`.
- Si algo no funciona, revisá la sección **Troubleshooting** al final de cada lab.
- Para profundizar, cada lab tiene referencias opcionales y código extra comentado.
- No te saltes el Lab 10 (Capstone): es donde todas las piezas encajan y el sistema cobra sentido.

!!! tip "¿Querés la secuencia exacta, comando por comando?"
    El [Recorrido del alumno](appendix/student-runbook.md) es el runbook completo:
    todos los comandos en orden, qué tenés que ver en cada uno, y cuánto tarda cada
    bloque. Sirve para hacer el curso entero de punta a punta y verificar que todo
    funciona.

!!! tip "Consejo para ambos modos"
    Antes de arrancar cualquier lab, activá el entorno virtual:
    ```bash
    source .venv/bin/activate
    ```
    Y verificá que los servicios necesarios están corriendo:
    ```bash
    docker ps
    ```

!!! warning "Desde el Lab 4, Nessie es obligatorio"
    Los Labs 0-2 solo necesitan MinIO. A partir del Lab 3 el curso usa **Nessie como
    catálogo Iceberg REST**, y todas las tablas pasan a llamarse
    `nessie.<namespace>.<tabla>`. Como Nessie administra el warehouse en S3,
    **necesita MinIO corriendo**: levantá siempre MinIO primero, o usá
    `docker compose up -d` que arranca los tres servicios juntos.

## Cómo navegar

- Empezá por [Lab 0](labs/lab-00-setup-global.md).
- Avanzá en orden: cada lab usa el anterior como base.
- Usá esta página para ubicarte y la plantilla común para escribir nuevos labs.

## Índice de labs

- [Lab 0 - Setup Global del Entorno](labs/lab-00-setup-global.md)
- [Lab 1 - Storage Layer con MinIO](labs/lab-01-minio.md)
- [Lab 2 - Iceberg: Tablas ACID sobre MinIO](labs/lab-02-iceberg.md)
- [Lab 3 - Nessie: Catálogo y Versionado de Datos](labs/lab-03-nessie.md)
- [Lab 4 - Spark: Compute Layer sobre Iceberg + MinIO](labs/lab-04-spark.md)
- [Lab 5 - Dagster: Orquestación Moderna del Lakehouse](labs/lab-05-dagster.md)
- [Lab 6 - Vault: Secret Management para el Lakehouse](labs/lab-06-vault.md)
- [Lab 7 - Terraform: Infraestructura como Código](labs/lab-07-terraform.md)
- [Lab 8 - CI/CD: GitHub Actions para el Lakehouse](labs/lab-08-ci-cd.md)
- [Lab 9 - IA Aplicada al Lakehouse](labs/lab-09-ai.md)
- [Lab 10 - Capstone Project](labs/lab-10-capstone.md)

## Bonus avanzado

- [Lab 11 - RAG local sobre el Lakehouse](labs/lab-11-rag.md)

## Apéndice

- [Recorrido del alumno (runbook paso a paso)](appendix/student-runbook.md)
- [Cómo documentar el proyecto](appendix/project-documentation.md)
- [Tests para Assets de Dagster](appendix/testing-dagster.md)

## Plantilla base de cada lab

!!! note
    Usá las notas como guía rápida, los warnings para limitaciones reales y los checkpoints de validación antes de avanzar al siguiente lab.

### Objetivo

### Prerrequisitos

### Instalación y setup

Pasos detallados (template)

### Validación

### Código de ejemplo

### Resultado esperado