# LAB 2 - Iceberg: Tablas ACID sobre MinIO

Objetivo: crear tablas Iceberg sobre MinIO, entender snapshots, time travel y dejar listo el table format del Lakehouse.

## ¿Por qué Iceberg?

Tirar Parquets sueltos en un bucket no es un Lakehouse, es un pantano. Te faltan: transacciones ACID, schema evolution sin reescribir todo, time-travel y un manifiesto que evite escanear millones de archivos. **Apache Iceberg** te da todo eso como un table format abierto, neutral (gobernanza Apache), soportado por Spark, Flink, Trino, DuckDB, Snowflake y BigQuery. La gracia: tus datos siguen siendo Parquet en MinIO — Iceberg es solo metadata. Si mañana cambiás de motor de compute, las tablas siguen intactas.

## Objetivo del lab

- Configurar un catálogo Iceberg.
- Crear una tabla Iceberg sobre MinIO.
- Insertar datos y hacer time travel.

## Prerrequisitos

- LAB 0 y LAB 1 completados.
- MinIO corriendo en http://localhost:9000.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup específico

Ya instalaste pyiceberg en el pyproject.toml.
Ahora solo vamos a:
- definir el catálogo
- crear tablas
- probar lecturas/escrituras

### PASO 1 - Entender qué catálogo vamos a usar

Una tabla Iceberg necesita un **catálogo**: el componente que sabe cuál es el
snapshot vigente de cada tabla. En este lab usamos el catálogo más simple posible,
el tipo `hadoop`: la metadata vive como archivos en MinIO, al lado de los datos.

- **Ventaja**: cero servicios extra. Solo necesitás el bucket.
- **Límite**: no tiene ramas ni commits. Eso llega en el Lab 3 con Nessie.

La configuración está en `src/spark/utils.py`, en el catálogo llamado `iceberg`:

```python
.config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
.config("spark.sql.catalog.iceberg.type", "hadoop")
.config("spark.sql.catalog.iceberg.warehouse", "s3a://bronze/iceberg/warehouse")
```

Por eso en **este lab** las tablas se llaman `iceberg.bronze_people`: `iceberg` es
el nombre del catálogo, no del formato.

!!! note "Ojo: esto cambia en el Lab 3"
    A partir del Lab 3 el curso usa Nessie como catálogo y las tablas pasan a
    llamarse `nessie.bronze.people` — catálogo, namespace, tabla. Este catálogo
    `hadoop` existe para que veas el escalón anterior: **un table format sin
    servidor de catálogo**, con sus límites (sin ramas, sin nombres de tres
    niveles, DuckDB obligado a leer por ruta). Es el "antes" que hace obvio el
    "después".

### PASO 2 - Preparar datos de ejemplo en MinIO

Asegurate de que exista `data/bronze/people.csv` y que el bucket `bronze` esté creado:

```bash
python src/minio/test_minio.py
```

### PASO 3 - Abrir DuckDB con soporte Iceberg

DuckDB ya está instalado como dependencia del proyecto (`duckdb==1.5.2` en el
`pyproject.toml`), así que **no hace falta instalarlo por separado**. Para la CLI
interactiva:

```bash
python -c "import duckdb; duckdb.sql('SELECT 1').show()"   # validar la librería
duckdb                                                      # CLI, si la tenés instalada
```

!!! note
    Todos los pasos de este lab que muestran SQL de DuckDB también existen como
    scripts Python en `src/duckdb/`. Si no querés instalar la CLI, usá los scripts.

### PASO 4 - Conectar DuckDB a MinIO

**En DuckDB**

```sql
INSTALL httpfs;
LOAD httpfs;
INSTALL iceberg;
LOAD iceberg;
```

```sql
SET s3_endpoint='localhost:9000';
SET s3_access_key_id='admin';
SET s3_secret_access_key='password';
SET s3_use_ssl=false;
SET s3_url_style='path';
SET s3_region='us-east-1';
```

```sql
SELECT * FROM glob('s3://bronze/*');
```

### PASO 5 - Crear una tabla Iceberg con Spark + datos iniciales

Ejecutar el script `src/spark/02_create_people_table.py`.

**Con DuckDB + configuración inicial, correr**

```sql
SELECT * FROM iceberg_scan('s3://bronze/iceberg/warehouse/bronze_people');
```

**También se puede ejecutar el script**

```bash
python src/duckdb/01_read_people_table.py
```

!!! note "¿Por qué `iceberg_scan('s3://...')` y no `SELECT * FROM bronze_people`?"
    Con el catálogo `hadoop` no hay un servicio que resuelva nombres de tabla, así
    que DuckDB necesita la ruta explícita del warehouse. Para consultar por nombre
    hace falta un catálogo REST — Nessie (Lab 3) o Polaris. En este curso usamos
    Nessie; Polaris queda como alternativa a mirar cuando madure.

### PASO 6 - Insertar nuevos datos en la tabla Iceberg

Ejecutar

```bash
python src/spark/03_insert_people_table.py
```

```sql
SELECT * FROM iceberg_scan('s3://bronze/iceberg/warehouse/bronze_people');
```

También se puede leer con `python src/duckdb/01_read_people_table.py`.

> One limitation to be aware of: DuckDB's Iceberg extension currently has no write support, so INSERT INTO iceberg.bronze_people won't work - writes must go through Spark. DuckDB's role in this lakehouse is as a fast analytical read layer.

### PASO 7 - Ver snapshots (versionado)

Ejecutar

```bash
python src/duckdb/02_read_snapshot_version.py
```

Deberías ver 2 `snapshot_id`.

### PASO 8 - Time travel a snapshot anterior

**Tomá el `snapshot_id` del primer snapshot y ejecutá**

```bash
python src/duckdb/03_read_people_table_as_version.py
```

Deberías ver los datos antes del update.

## Validación

- Podés hacer SELECT * sin errores.
- Hay múltiples snapshots en `iceberg_internals.snapshots`.
- El time travel devuelve el estado anterior de los datos.

## ¡Momento Click! 🎯

!!! success "Time travel en 3 pasos"
    1. **Anotá** el `snapshot_id` del paso 7 (antes de insertar filas nuevas).
    2. Ejecutá `python src/spark/03_insert_people_table.py` para agregar más datos.
    3. Ejecutá `python src/duckdb/03_read_people_table_as_version.py` apuntando al snapshot original.

    Las filas nuevas **no aparecen** en la consulta del snapshot viejo. Iceberg nunca
    sobreescribe el Parquet anterior — solo agrega snapshots como commits inmutables.
    Si algo sale mal en producción, podés volver a cualquier punto del tiempo sin
    restaurar backups.

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **`NoSuchTableException`** → corré primero `python src/spark/02_create_people_table.py`.

    **DuckDB no lee la tabla desde S3**
    ```sql
    SET s3_endpoint='localhost:9000';
    SET s3_url_style='path';
    SET s3_use_ssl=false;
    ```
    Aseguráte de correr estas tres líneas antes del `iceberg_scan()`.

    **`NoSuchObjectException` en time travel** → el `snapshot_id` debe estar entre los que
    lista `iceberg_internals.snapshots`. Copiará uno entero, sin truncar.

    **Spark descarga jars la primera vez y tarda 2-3 min** → normal, son unos 300MB.
    Después quedan en caché local en `~/.ivy2/`.

## Resultado esperado

- Al finalizar este lab, deberías tener:
- Una tabla Iceberg creada sobre MinIO.
- Datos insertados y modificados.
- Múltiples snapshots registrados.
- Time travel funcionando.
- Este lab deja listo el table format ACID sobre el cual luego vas a:
- conectar Spark
- versionar con Nessie
- orquestar con Dagster
- enriquecer con IA