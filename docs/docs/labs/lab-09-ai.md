# LAB 9 - IA Aplicada al Lakehouse

!!! tip
    En este lab vas a integrar IA al Lakehouse usando modelos open-source locales, generar embeddings, enriquecer datos y habilitar consultas en lenguaje natural.

## ¿Por qué IA local?

Llamarle a OpenAI por cada fila de tu tabla es caro, lento y manda tus datos a otro continente. Para muchos casos de uso del Lakehouse (embeddings, clasificación, SQL generation sobre tu schema) un modelo open-source corriendo local alcanza y sobra. **Ollama** te da una API tipo OpenAI sobre modelos locales y cubre las dos necesidades del lab: `llama3.1` para generación y `nomic-embed-text` para embeddings. Bonus soberanía: tus datos nunca cruzan la frontera.

## Objetivo del lab

- Instalar y usar Ollama para correr LLMs localmente.
- Generar embeddings con Ollama (`nomic-embed-text`).
- Guardar embeddings en Iceberg como columnas vectoriales.
- Crear un ETL con IA (bronze -> silver enriched).
- Crear un SQL Generator usando un LLM local.
- Integrar IA con Spark y Dagster.

## Prerrequisitos

- LAB 0 a LAB 8 completados.
- Spark funcionando.
- MinIO funcionando.
- Iceberg funcionando.
- Dagster funcionando.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

Este lab requiere instalar Ollama en WSL2.

### PASO 1 - Instalar Ollama en WSL2

!!! note
    Si ya hiciste el PASO 11 del [Lab 0](lab-00-setup-global.md), Ollama y los
    modelos ya están instalados. Saltá directo al PASO 3.

```bash
sudo apt-get install zstd
curl -fsSL https://ollama.com/install.sh | sh
```

**Validar**

```bash
ollama --version
```

### PASO 2 - Descargar modelos necesarios

**Modelo para embeddings**

```bash
ollama pull nomic-embed-text
```

**Modelo para SQL generation (LLM)**

```bash
ollama pull llama3.1
```

### PASO 3 - Crear carpeta IA

```bash
mkdir -p src/ai
```

### PASO 4 - Generar embeddings con Ollama

**Crear archivo** `src/ai/generate_embeddings.py`

La librería `ollama` de Python ya incluye un cliente que se conecta automáticamente
al servidor local; no hace falta configurar la URL.

!!! important "Qué columna embebemos y por qué"
    El script embebe **`bio`**, no `name`. Un embedding representa el *significado*
    de un texto: vectorizar `"Ada"` no produce nada útil, porque un nombre propio no
    tiene contenido semántico. Vectorizar `"Perra salchicha muy inteligente"` sí
    permite después buscar "mascotas" y que la fila aparezca.

    Es el error más común al arrancar con embeddings: elegir la columna equivocada
    y concluir que "la búsqueda semántica no funciona".

**Ejecutar**

```bash
python src/ai/generate_embeddings.py
```

- `nomic-embed-text` genera embeddings de **768 dimensiones**.
- El resultado queda en `data/silver/people_with_embeddings.json`.

### PASO 5 - Guardar embeddings en Iceberg

Creá el script `src/spark/10_save_embeddings_iceberg.py`.

**Ejecutar**

```bash
python src/spark/10_save_embeddings_iceberg.py
```

### PASO 6 - Validar embeddings en Iceberg

Creá el script `src/spark/11_read_iceberg_people_embeddings.py`.

**Ejecutar**

```bash
python src/spark/11_read_iceberg_people_embeddings.py
```

- Deberías ver una columna embedding con arrays de floats.

### PASO 7 - Crear un SQL Generator usando Ollama

**Crear archivo** `src/ai/sql_generator.py` y `src/ai/__init__.py`

En este caso, estamos llamando directamente a la API REST de Ollama.

**Ejecutar**

```bash
python src/ai/sql_generator.py
```

- Deberías ver SQL generado automáticamente.

### PASO 8 - Ejecutar SQL generado en Spark

**Crear archivo** `src/spark/12_run_generated_sql.py`

**Ejecutar**

```bash
python src/spark/12_run_generated_sql.py
```

- Esto convierte lenguaje natural -> SQL -> resultado real.

### PASO 9 - Integrar IA en Dagster (ETL enriquecido)

Creá el asset `lakehouse_dagster/lakehouse_dagster/assets/ai_enrich/ai_enriched_people.py` y
`lakehouse_dagster/lakehouse_dagster/assets/ai_enrich/__init__.py`.

Registrar en `lakehouse_dagster/lakehouse_dagster/assets/__init__.py`
y `lakehouse_dagster/lakehouse_dagster/definitions.py`

### PASO 10 - Ejecutar pipeline con IA

En la UI de Dagster:

- cd lakehouse_dagster
- dagster dev
- Ir a Assets.
- Seleccionar `silver_people_embeddings`.
- Hacer click en Materialize.
- Dagster ejecuta IA dentro del pipeline.

## Checkpoint de validación

!!! important
    Completá esta validación antes de continuar con el siguiente bloque.

- Ollama instalado y funcionando
- Embeddings generados correctamente
- Embeddings guardados en Iceberg
- SQL generado por LLM local
- SQL ejecutado en Spark
- Dagster ejecuta IA dentro del pipeline

## Resultado esperado

!!! note
    Esta sección resume el estado mínimo esperado al cerrar el lab.

Al finalizar este lab, deberías tener:

- IA integrada al Lakehouse
- Embeddings almacenados en Iceberg
- SQL Generator con LLM local
- Pipelines Dagster con IA
- Spark ejecutando consultas generadas por IA
- Este lab convierte tu Lakehouse en un sistema inteligente y moderno, comparable al stack de empresas como Netflix, Uber o Shopify.