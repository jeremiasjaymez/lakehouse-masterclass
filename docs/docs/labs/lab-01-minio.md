# LAB 1 - Storage Layer con MinIO

Objetivo: levantar MinIO localmente, crear buckets, conectarse desde Python y dejar listo el storage del Lakehouse.

## ¿Por qué MinIO?

En un Lakehouse, el **storage** es el cimiento: ahí viven los archivos Parquet, los manifiestos de Iceberg y todo lo demás. La API estándar de la industria es S3, pero no queremos depender de AWS para algo tan básico. **MinIO** es un servidor S3-compatible open-source que corre en cualquier lado (tu laptop, un VPS, on-prem) y habla exactamente el mismo protocolo que S3. Lo que aprendás acá se puede extrapolar a otro servicio.

## Objetivo del lab

- Instalar y ejecutar MinIO localmente usando Docker.
- Crear buckets bronze/silver/gold.
- Conectarse desde Python usando boto3.
- Validar que el storage funciona correctamente.

## Prerrequisitos

- LAB 0 completado (WSL2 + Docker + uv + proyecto base).
- Docker Desktop funcionando.
- Entorno virtual activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

Este lab crea el storage layer del Lakehouse.

### PASO 1 - Crear archivo docker-compose para MinIO

**En la raíz del proyecto**

```text
docker-compose.minio.yml
```

!!! warning "Por qué la imagen está pineada (y qué pasó con MinIO)"
    En el compose vas a ver un tag explícito, no `latest`:

    ```yaml
    image: minio/minio:RELEASE.2025-09-07T16-13-09Z
    ```

    Dos razones:

    1. **Reproducibilidad.** `latest` significa "lo que haya hoy". Un curso donde
       cada alumno levanta una versión distinta del storage es un curso irreproducible.
    2. **MinIO cambió de rumbo.** En la release del 2025-05-24 (marcada por ellos
       mismos como *Breaking Release*) MinIO sacó la consola web embebida del
       servidor community y removió el login vía LDAP/OIDC, empujando esas
       funciones a su producto comercial AIStor. El repo del servidor community
       quedó archivado y la última imagen publicada en Docker Hub es la que usamos acá.

    Para este curso **no cambia nada**: la consola de esta versión sigue creando
    buckets y navegando objetos, que es todo lo que necesitamos. Pero es un buen
    ejemplo de algo que vas a evaluar toda tu carrera: la licencia de una herramienta
    (MinIO sigue siendo AGPL-3.0) no te dice hacia dónde va el proyecto.

### PASO 2 - Levantar MinIO

```bash
docker compose -f docker-compose.minio.yml up -d
```

**Ver logs**

```bash
docker logs -f minio
```

**Esperar hasta ver**

```text
API: http://0.0.0.0:9000
Console: http://0.0.0.0:9001
```

### PASO 3 - Abrir MinIO Console

**Ir a**

<http://localhost:9001>

**Login**

- User: `admin`
- Password: `password`

### PASO 4 - Crear buckets del Lakehouse

**En la consola**

- Click en Buckets
- Crear:
- bronze
- silver
- gold
- Estos serán tus data zones.

### PASO 5 - Crear carpeta de datos local

```bash
mkdir -p data/bronze
mkdir -p data/silver
mkdir -p data/gold
```

### PASO 6 - Crear archivo de prueba

```bash
echo "id,name
1,Jeremias
2,Franco" > data/bronze/people.csv
```

### PASO 7 - Subir archivo a MinIO (opcional)

Desde la consola web -> bucket bronze -> Upload -> people.csv.

### PASO 8 - Conectarse a MinIO desde Python

Crear el archivo `src/minio/test_minio.py`.

**Ejecutar en root**

```bash
python src/minio/test_minio.py
```

## Validación

- MinIO levanta sin errores
- Acceso a http://localhost:9001
- Buckets creados
- Python puede listar buckets
- Python puede subir y descargar archivos

## Código de ejemplo adicional

- Listar objetos en un bucket:

```python
resp = s3.list_objects_v2(Bucket="bronze")
print(resp.get("Contents", []))
```

- Crear un bucket desde Python:

```python
s3.create_bucket(Bucket="test-bucket")
```

## ¡Momento Click! 🎯

!!! success "¡Esto es lo que tiene que pasar!"
    Navegá a <http://localhost:9001>, entrá al bucket `bronze` y vas a ver `people.csv`.
    Ahora abrí otra terminal y ejecutá `python src/minio/test_minio.py`.
    El mismo archivo aparece listado por boto3 en Python.

    Eso es la gracia del protocolo S3: **tu código es el mismo si mañana apuntás a AWS, GCS
    (con un gateway S3-compatible) o a MinIO en otro servidor**. Nada del código cambia.

## Troubleshooting frecuente

!!! warning "Si algo no anda"
    **Puerto 9000/9001 ocupado**
    ```bash
    lsof -i :9001
    ```
    Matá el proceso que lo tiene o cambiá el puerto en `docker-compose.minio.yml`.

    **`Connection refused` en boto3** → el contenedor no levantó todavía.
    ```bash
    docker logs minio
    ```
    Esperará hasta ver `API: http://0.0.0.0:9000`.

    **`Access Denied` al subir** → verificar `aws_access_key_id="admin"` y
    `aws_secret_access_key="password"` en el script.

    **Bucket no existe al subir** → creálo primero desde la UI o con
    `s3.create_bucket(Bucket="bronze")`.

## Resultado esperado

- Al finalizar este lab, deberías tener:
- MinIO ejecutándose localmente
- Buckets bronze/silver/gold creados
- Conexión Python <-> MinIO funcionando
- Archivos subidos y descargados correctamente
- Este es el primer componente del Lakehouse y base para Iceberg, Nessie, Spark y Dagster.