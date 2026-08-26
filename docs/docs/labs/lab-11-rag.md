# LAB 11 - Bonus avanzado: RAG local sobre el Lakehouse

!!! tip
    En este bonus lab vas a convertir la documentación de la masterclass en una base de conocimiento consultable con RAG, guardando chunks y embeddings en Iceberg.

!!! note
    Este bonus lab mantiene el foco en RAG sobre Iceberg. No vamos a sumar vector DB, Dagster ni agentes: la idea es ver el patrón completo con las piezas que ya trae la masterclass.

## ¿Por qué RAG sobre el Lakehouse?

Un LLM local puede responder preguntas generales, pero no conoce tu repo ni tus decisiones de arquitectura. RAG cambia eso: primero recupera fragmentos relevantes de tu documentación y recién después le pide al modelo que responda usando ese contexto.

El momento AHA de este lab es ver que el Lakehouse no solo sirve para datos analíticos: también puede guardar conocimiento documentado, versionado y listo para alimentar una app de IA.

## Objetivo del lab

- Comparar una respuesta de LLM sin RAG contra una respuesta con RAG.
- Leer la documentación de la masterclass como corpus.
- Partir Markdown en chunks por secciones.
- Generar embeddings locales con Ollama.
- Guardar el índice RAG en una tabla Iceberg.
- Hacer retrieval semántico con Spark/Python.
- Responder preguntas mostrando fuentes recuperadas.

## Prerrequisitos

- LAB 0 a LAB 10 completados.
- MinIO funcionando.
- Iceberg funcionando.
- Spark funcionando.
- Ollama instalado y corriendo.
- Modelos descargados:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

- Entorno activado:

```bash
source .venv/bin/activate
```

## Corpus del RAG

El corpus es la biblioteca que el RAG puede consultar. En este lab vamos a indexar solo documentación principal de la masterclass:

```text
docs/docs/guide.md
docs/docs/labs/*.md
```

No vamos a indexar:

- `docs/site/`, porque es HTML generado por MkDocs.
- `README.md`, para evitar duplicar contenido.
- `docs/docs/appendix/`, porque son temas laterales.
- `src/`, porque RAG sobre código es otro problema.

## Tabla Iceberg del índice RAG

El índice se guarda en:

```text
nessie.gold.knowledge_chunks
```

Schema esperado:

```text
chunk_id STRING
source_path STRING
section_title STRING
chunk_index INT
chunk_text STRING
embedding ARRAY<FLOAT>
ingestion_ts TIMESTAMP
```

`chunk_id` es el DNI reproducible de cada fragmento. Se calcula de forma determinística con el path, la sección, el índice y el texto del chunk. Si el contenido no cambia, el ID vuelve a salir igual.

## PASO 1 - Probar el LLM sin RAG

Primero tirá una pregunta sin darle contexto del repo al modelo:

```bash
python src/ai/ask_llm_without_rag.py "¿En qué lab se configura Nessie?"
```

La respuesta puede sonar razonable, pero no está grounded en la documentación real de la masterclass. Ese es el problema que RAG viene a resolver.

## PASO 2 - Ver cómo se segmentará (chunks) la documentación

Ejecutá el chunker para revisar qué fragmentos salen del corpus:

```bash
python src/ai/rag_chunk_docs.py
```

El chunking usa esta regla:

- Primero separa por headings Markdown (`#`, `##`, `###`).
- Conserva `source_path` y `section_title`.
- Si una sección es muy larga, la divide por tamaño.
- Cada chunk recibe un `chunk_id` determinístico.

## PASO 3 - Crear el índice RAG en Iceberg

Este script lee los Markdown, genera embeddings con `nomic-embed-text` y guarda todo en Iceberg:

```bash
python src/spark/13_save_rag_index_iceberg.py
```

Salida esperada:

```text
Tabla gold_knowledge_chunks guardada con N chunks
```

## PASO 4 - Preguntar con RAG

Ahora hacé la misma pregunta, pero recuperando contexto desde Iceberg:

```bash
python src/spark/14_rag_answer_from_iceberg.py "¿En qué lab se configura Nessie?"
```

Salida esperada:

```text
Pregunta:
¿En qué lab se configura Nessie?

Respuesta:
...

Fuentes recuperadas:
1. docs/docs/labs/lab-03-nessie.md :: sección (score=...)
2. docs/docs/labs/lab-10-capstone.md :: sección (score=...)
3. docs/docs/guide.md :: sección (score=...)
```

Ahí está el click: el modelo ya no responde solo desde su entrenamiento, responde usando chunks recuperados desde el Lakehouse.

## PASO 5 - Ajustar cuántos chunks se recuperan

Por defecto se recuperan 3 chunks (`top_k=3`). Podés cambiarlo con `--top-k`:

```bash
python src/spark/14_rag_answer_from_iceberg.py "¿Cómo conecto Spark con Iceberg?" --top-k 5
```

Más contexto no siempre significa mejor respuesta. Si traés chunks de más, podés meter ruido. Si traés chunks de menos, puede faltar evidencia.

## Checkpoint de validación

!!! important
    Completá esta validación para confirmar que el RAG quedó funcionando de punta a punta.

- El LLM responde sin RAG usando `ask_llm_without_rag.py`.
- El chunker encuentra documentos en `docs/docs/guide.md` y `docs/docs/labs/*.md`.
- La tabla `nessie.gold.knowledge_chunks` se crea correctamente.
- La CLI con RAG responde preguntas y muestra fuentes.
- Las fuentes recuperadas tienen sentido para la pregunta.

## Resultado esperado

Al finalizar este bonus lab, deberías tener:

- Documentación convertida en chunks semánticos.
- Embeddings locales generados con Ollama.
- Índice RAG guardado en Iceberg.
- Retrieval semántico con Spark/Python.
- CLI de preguntas y respuestas con fuentes visibles.
- Una diferencia clara entre llamar a un LLM y construir una respuesta grounded con RAG.

## Ideas para extender

Si querés llevar esto a otra masterclass o a una segunda iteración, podés explorar:

- Indexar metadata de tablas Iceberg.
- Combinar RAG documental con SQL generation.
- Agregar reranking.
- Comparar brute force contra un vector DB.
- Evaluar respuestas con un set de preguntas esperado.