# LAB 3 - Nessie: Catálogo y Versionado de Datos

Objetivo: instalar y ejecutar Project Nessie, crear ramas, hacer commits y merges, y conectar el catálogo con Iceberg.

## ¿Por qué Nessie?

Iceberg te resuelve la tabla individual, pero ¿cómo coordinás cambios entre tablas? ¿Cómo probás un ETL en una "rama" sin romper producción? **Project Nessie** trae el modelo de Git al catálogo de datos: branches, commits, merges, rollback atómico multi-tabla. Es la diferencia entre "subo a prod y rezo" y "merge a main solo cuando los tests pasan". Open-source y self-hostable, es una alternativa neutral a catálogos propietarios como Unity Catalog.

## Objetivo del lab

- Levantar Nessie localmente con Docker.
- Crear ramas (dev, staging, prod).
- Hacer commits y merges de datos.
- Integrar Nessie con Iceberg.
- Entender cómo versionar datos como código.

## Prerrequisitos

- LAB 0 (setup global)
- LAB 1 (MinIO)
- LAB 2 (Iceberg)
- Docker funcionando
- Entorno activado:

```bash
source .venv/bin/activate
```

## Nessie es también un Iceberg REST Catalog

Esta es la pieza clave del curso y conviene entenderla antes de tocar nada.

Iceberg define un **protocolo estándar de catálogo sobre HTTP**: el *Iceberg REST
Catalog*. Nessie lo implementa. Eso significa que un único servidor te da:

- **Nombres de tres niveles**: `nessie.bronze.people` en vez de rutas
  `s3://bucket/warehouse/...`.
- **Ramas de datos**: Nessie enruta cada request con un prefijo `<rama>|<warehouse>`.
- **Un catálogo compartido**: Spark, DuckDB y pyiceberg hablan el mismo protocolo.

```text
        Spark ─┐
      DuckDB ─┼─► Iceberg REST API ─► Nessie ─► metadata + ramas
   pyiceberg ─┘   (protocolo estándar)     └───► MinIO (Parquet)
```

Comparalo con el Lab 2: ahí el catálogo era `hadoop`, un montón de archivos en un
bucket, sin servidor y sin ramas. Servía para entender el table format. **A partir
de este lab, ese catálogo queda atrás**: todo lo que sigue usa Nessie.

!!! note "Por qué la imagen viene de ghcr.io"
    En `docker-compose.nessie.yml` vas a ver `ghcr.io/projectnessie/nessie:0.108.4`.
    Las imágenes de Nessie en Docker Hub quedaron congeladas en la 0.76.6; las
    versiones actuales — las que traen el Iceberg REST Catalog — se publican en el
    registry de GitHub. También fijamos la versión: `latest` en un curso es una
    receta para que a cada alumno le pase algo distinto.

## Instalación y setup

Vamos a levantar Nessie usando Docker y luego interactuar con su API REST.

!!! warning "Nessie necesita MinIO"
    Como Nessie ahora administra el warehouse en S3, necesita alcanzar a MinIO.
    Los compose comparten la red `lakehouse`, así que **levantá MinIO primero**:

    ```bash
    docker compose -f docker-compose.minio.yml up -d
    docker compose -f docker-compose.nessie.yml up -d
    ```

    O todo junto con `docker compose up -d`.

### PASO 1 - Crear archivo docker-compose para Nessie

**En la raíz del proyecto**

```text
docker-compose.nessie.yml
```

### PASO 2 - Levantar Nessie

```bash
docker compose -f docker-compose.nessie.yml up -d
```

**Ver logs**

```bash
docker logs -f nessie
```

**Esperar hasta ver**

```text
Listening on: http://0.0.0.0:19120
```

### PASO 3 - Validar que Nessie está vivo

```bash
curl http://localhost:19120/api/v1/trees
```

Deberías ver algo como:

```json
{
  "token": null,
  "references": [
    {
      "type": "BRANCH",
      "name": "main",
      "hash": "2e1cfa82b035c26cbbbdae632cea070514eb8b773f616aaeaf668e2f0be8f10d"
    }
  ],
  "hasMore": false
}
```

### PASO 4 - Crear ramas (dev, staging, prod)

**Creamos un script**

```bash
python src/nessie/01_create_branches.py
```

### PASO 5 - Listar ramas

```bash
curl http://localhost:19120/api/v1/trees
```

**Deberías ver**

- main
- dev
- staging
- prod

### PASO 6 - Integrar Iceberg con Nessie y crear commit en dev

Spark escribe -> Nessie registra el commit -> Iceberg guarda los archivos -> MinIO los almacena.

El script hace cuatro cosas: carga `people.csv` en `nessie.bronze.people` (rama
`main`), crea la rama `dev`, aplica un `UPDATE` **solo en dev**, y muestra las dos
ramas lado a lado.

```bash
python src/spark/04_nessie_commit_dev.py
```

### PASO 7 - Ver commits de la rama dev

```bash
curl http://localhost:19120/api/v1/trees/tree/dev/log
```

### PASO 8 - Merge dev -> staging

Creamos script:
`src/nessie/02_merge_dev_to_staging.py`

### PASO 9 - Validar que staging tiene los cambios

```bash
curl http://localhost:19120/api/v1/trees/tree/staging/log
```

## Validación

- Nessie levanta correctamente
- Ramas creadas: main, dev, staging, prod
- Iceberg puede leer usando Nessie como catálogo
- Cambios hechos en dev no afectan staging/prod
- Merge dev -> staging funciona

## Código adicional opcional

- Borrar una rama:

```python
h = requests.get(f"{BASE}/trees/tree/staging").json()["hash"]
requests.delete(f"{BASE}/trees/branch/staging", params={"expectedHash": h})
```

## ¡Momento Click! 🎯

!!! success "Aislamiento de ramas, en una sola pantalla"
    Ejecutá `python src/spark/04_nessie_commit_dev.py` y mirá el final de la salida:

    ```text
    === 4. MAIN (sin cambios) ===        === 4. DEV (con el UPDATE) ===
    +---+--------+                       +---+------------+
    | id|    name|                       | id|        name|
    +---+--------+                       +---+------------+
    |  1|Jeremias|                       |  1|Jeremias DEV|
    |  2|  Franco|                       |  2|      Franco|
    ```

    **La misma tabla, `nessie.bronze.people`, con dos contenidos distintos al mismo
    tiempo.** No son dos copias: es una tabla con dos ramas, igual que un archivo en
    Git. El `UPDATE` creó un commit que existe solo en `dev`.

    Ese es el punto: podés correr un ETL experimental en `dev`, validarlo, y mergear
    a `main` solo cuando el resultado convence. Igual que Git, pero para tablas con
    millones de filas.

## De acá en adelante, todo vive en Nessie

Este es el cambio de arquitectura más importante del curso, así que vale decirlo
explícito:

| | Lab 2 (catálogo `hadoop`) | Lab 3 en adelante (catálogo `nessie`) |
|---|---|---|
| Nombre de tabla | `iceberg.bronze_people` | `nessie.bronze.people` |
| Helper | `get_spark()` | `get_spark_with_nessie(ref=...)` |
| Cómo lo lee DuckDB | `iceberg_scan('s3://...')` | por nombre, vía `ATTACH` |
| Ramas y commits | ❌ | ✅ |
| Servidor de catálogo | ninguno | Nessie |

El catálogo `hadoop` del Lab 2 **no es un camino paralelo**: es el escalón que te
muestra por qué querés un catálogo de verdad. Una vez que tenés Nessie, el ETL
(Lab 4), los embeddings (Lab 9), el capstone (Lab 10) y el RAG (Lab 11) escriben
todos en el mismo catálogo versionado.

Es decir: **todo lo que construyas de acá en adelante es versionable por rama**.

### Cómo se elige la rama

No hay `USE REFERENCE` como en las extensiones SQL de Nessie: con el protocolo REST
la rama es **configuración del catálogo**. En `src/spark/utils.py`:

```python
spark = get_spark_with_nessie(ref="dev")  # todo apunta a dev
spark = get_spark_with_nessie(ref="main")  # todo apunta a main
```

Y si querés comparar dos ramas en la misma query, registrás una por catálogo:

```python
spark = get_spark_multibranch(refs=("main", "dev"))
spark.sql("SELECT * FROM nessie_main.bronze.people")
spark.sql("SELECT * FROM nessie_dev.bronze.people")
```

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`Connection refused` en :19120** → Nessie no levantó.
    ```bash
    docker logs nessie
    ```
    Esperará hasta ver `Listening on: http://0.0.0.0:19120`.

    **`409 Conflict` al crear rama** → la rama ya existe. El script
    `04_nessie_commit_dev.py` hace `DROP BRANCH IF EXISTS` antes de crear,
    pero si creáste la rama a mano, borrála primero:
    ```bash
    HASH=$(curl -s http://localhost:19120/api/v1/trees/tree/dev | python3 -c "import sys,json; print(json.load(sys.stdin)['hash'])")
    curl -X DELETE "http://localhost:19120/api/v1/trees/branch/dev?expectedHash=$HASH"
    ```

    **`catalog 'nessie' not found` en Spark** → usá `get_spark_with_nessie()` de
    `src/spark/utils.py`, que ya arma toda la configuración REST.

    **`NoSuchNamespaceException`** → con el catálogo REST los namespaces no se
    crean solos:
    ```python
    spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.silver")
    ```

    **`Failed to create request URI from base ...dev|warehouse...`** → el `|` del
    prefijo va URL-encodeado (`%7C`). `get_spark_with_nessie()` ya lo hace.

    **Nessie arranca y se cae con `Permission denied` en RocksDB** → el volumen
    tiene que montarse en `/home/nessie`, que es el directorio del usuario del
    contenedor. Está así en el compose del repo.

## Resultado esperado

- Al finalizar este lab, deberías tener:
- Un catálogo Nessie funcionando
- Ramas dev/staging/prod
- Integración Iceberg <-> Nessie
- Commits y merges funcionando
- Versionado de datos como código
- Este es el corazón de la gobernanza del Lakehouse.