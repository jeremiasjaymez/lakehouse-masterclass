# Lakehouse Masterclass — Instrucciones para el asistente

> Este archivo es la **única** fuente de verdad para asistentes de IA en este repo.
> (Reemplaza al viejo `.github/copilot-instructions.md`, que se eliminó para no
> mantener dos archivos que se desincronizan.)

## Contexto del proyecto

Repositorio **educativo** para una masterclass de Data Lakehouse. No es un producto:
cada decisión se juzga por si enseña bien, no por si es la más elegante.

Stack: **Spark + Iceberg + Nessie + MinIO + Vault + Dagster + Terraform + Ollama**,
todo vía docker-compose y corriendo en una laptop (WSL2).

Son 12 labs (0 a 11) en `docs/docs/labs/`, más el runbook de ejecución en
`docs/docs/appendix/student-runbook.md`.

## Audiencia y tono

- Respuestas y comentarios de código en **español rioplatense informal**
  (vos, "che", "tirá", etc.).
- El público son data engineers con experiencia media a senior: **no expliques
  conceptos básicos** de Spark, SQL ni Python.
- Prioridad pedagógica: cada paso tiene que tener un **"momento aha!" demostrable**,
  algo que el alumno vea en pantalla y no pueda ver de otra forma.

## Arquitectura: un solo catálogo

**Nessie es el Iceberg REST Catalog del curso.** Todas las tablas se nombran
`nessie.<namespace>.<tabla>` — por ejemplo `nessie.bronze.people`,
`nessie.silver.people`, `nessie.gold.knowledge_chunks`.

- La sesión de Spark se construye **siempre** con `get_spark_with_nessie(app, ref=...)`
  de `src/spark/utils.py`. El parámetro `ref` es la rama de Nessie.
- `get_spark()` (catálogo `hadoop`, tablas `iceberg.*`) **existe solo para el Lab 2**,
  donde se usa a propósito como el "antes" que el Lab 3 viene a resolver. No lo uses
  en material nuevo.
- Con el catálogo REST los namespaces **no se crean solos**:
  `spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")` antes de escribir.
- DuckDB se conecta con `ATTACH ... (TYPE iceberg, ENDPOINT ...)` y consulta por
  nombre. Ver `src/duckdb/05_attach_nessie_catalog.py`.

## Convenciones del repo

- Los scripts de Spark viven en `src/spark/NN_nombre.py`, **numerados por paso**.
  Un script nuevo va con el número siguiente, no se renumeran los viejos.
- Cada "paso opcional" (Vault, Terraform, etc.) **NO debe modificar archivos
  anteriores** — se agregan archivos nuevos para preservar el progreso pedagógico.
- Credenciales de demo: MinIO `admin`/`password`, Vault token `root`. No son secretos
  reales, está OK que aparezcan en los `docker-compose.*.yml`.
  Los `.env` **sí** están gitigneados: se copian desde `.env.example`.
- **Las imágenes Docker van pineadas por tag**, nunca `latest`. Un curso donde cada
  alumno levanta una versión distinta es un curso irreproducible.
- Dagster usa API moderna: `ConfigurableResource`, no `@resource` legacy.
- Python: nada de type hints exhaustivos ni docstrings largos. **Estilo de notebook
  educativo**: comentarios que expliquen el porqué, código directo.

## Licencias (parte del contenido, no un detalle)

Vault y Terraform son **BUSL-1.1** (licenciante: IBM), no open source. El curso lo
enseña de frente en los Labs 6 y 7, con los forks libres **OpenBao** y **OpenTofu**
como alternativa. Si tocás esos labs o el README, no vuelvas a describir el stack
como "100% open source".

## Validación antes de dar algo por terminado

```bash
uvx ruff@0.15.14 check . --fix          # la versión pineada es la que corre en CI
uvx ruff@0.15.14 format .
cd lakehouse_dagster && uv run --extra dev pytest -q
cd docs && uv run --project .. --group docs mkdocs build --strict
```

Ojo: `uvx ruff` sin versión baja la última release y **puede discrepar con CI**
(por ejemplo con `E402`). Usá siempre el pin.

## Documentación

- Los labs siguen una plantilla: `¿Por qué X?` → objetivo → prerrequisitos → PASOS
  numerados → **Checkpoint de validación** → **¡Momento Click! 🎯** → Troubleshooting
  → Resultado esperado.
- Los `!!! note/tip/warning/danger/success` son de `pymdownx` + `admonition`, ya
  configurados en `docs/mkdocs.yml`.
- Si agregás una página, **agregala al `nav`** de `docs/mkdocs.yml` o `--strict` falla.
- Levantar la documentación en vivo:

```bash
cd docs && uv run --project .. --group docs mkdocs serve
```

## Qué NO hacer

- **No proponer refactors de archivos viejos "de paso".**
- **No agregar tests** salvo que se pidan explícitamente.
- **No generar archivos .md de documentación** salvo pedido explícito.
- No romper la numeración de los scripts ni de los PASOS de los labs.
