# Apéndice — Tests para Assets de Dagster

Objetivo: escribir tests útiles para assets de Dagster sin levantar servicios externos, usando los tres patrones que cubre este apéndice.

## ¿Por qué testear assets?

Un asset sin test es un script con nombre bonito. El argumento clásico de "los tests tardan mucho en escribirse" se invierte rápido cuando empezás a agregar assets que tocan MinIO, Vault, Iceberg y Spark al mismo tiempo: sin mocks, un test tarda segundos; con servicios reales, puede tardar minutos y depende de que docker compose esté levantado.

Tres beneficios concretos para el Lakehouse:

- **Confianza para refactorear**: si `silver_people` sigue devolviendo `name_upper`, el test lo dice.
- **CI/CD honesto**: el workflow de GitHub Actions corre los tests sin Docker, sin Vault, sin MinIO. Si pasa, el código está sano.
- **Documentación ejecutable**: el test muestra exactamente qué columnas y tipos produce cada asset.

## Prerrequisitos

- LAB 5 (Dagster) completado.
- LAB 8 (CI/CD) completado.
- Entorno activado:

```bash
source .venv/bin/activate
```

## Instalación y setup

pytest ya está declarado como dependencia de desarrollo en `pyproject.toml`.

```toml
[project.optional-dependencies]
dev = [
    "dagster-webserver==1.13.5",
    "pytest",
]
```

No hace falta instalar nada extra.

## Los tres patrones

### PATRÓN 1 — `materialize()`: test de integración liviano

Sirve para assets que leen I/O real que sí está disponible en CI (archivos locales, por ejemplo).

**Archivo de test**

```text
lakehouse_dagster/lakehouse_dagster_tests/test_assets.py
```

**Código**

```python
from dagster import materialize
from lakehouse_dagster.assets.bronze.bronze_people import bronze_people


def test_bronze_people_carga_csv():
    result = materialize([bronze_people])
    assert result.success
    df = result.output_for_node("bronze_people")
    assert not df.empty
    assert "name" in df.columns
```

- `materialize()` ejecuta el asset completo, incluyendo el código de producción real.
- No necesita levantar Dagster: corre en proceso, en menos de un segundo.
- Ideal para assets que solo leen archivos locales o hacen transformaciones puras.

### PATRÓN 2 — Invocación directa: test unitario de transformación pura

Un `@asset` en Dagster es una función Python normal. Se puede llamar directamente sin pasar por Dagster.

**Código**

```python
import pandas as pd
from lakehouse_dagster.assets.silver.silver_people import silver_people


def test_silver_people_agrega_columna():
    entrada = pd.DataFrame({"id": [1, 2], "name": ["jeremias", "ada"]})
    salida = silver_people(entrada)
    assert "name_upper" in salida.columns
    assert salida["name_upper"].tolist() == ["JEREMIAS", "ADA"]
```

- Pasás el DataFrame de entrada directamente, sin tocar el asset upstream.
- Perfecto para testear lógica de transformación aislada.
- El test no sabe nada de Dagster: es Python puro.

!!! tip
    Este patrón es el más rápido de escribir y el más fácil de mantener. Usalo siempre que el asset sea una transformación sin I/O externo.

### PATRÓN 3 — Mock de dependencias externas

Para assets que hablan con Vault, MinIO, APIs, etc. La idea: reemplazás la llamada HTTP (o boto3) con un objeto falso que devuelve lo que vos querés.

**Mockear el VaultResource**

```python
from unittest.mock import patch, MagicMock
from lakehouse_dagster.resources.vault_resource import VaultResource


def test_vault_resource_devuelve_secreto():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"data": {"access_key": "admin", "secret_key": "password"}}
    }
    mock_resp.raise_for_status = MagicMock()

    with patch(
        "lakehouse_dagster.resources.vault_resource.requests.get",
        return_value=mock_resp,
    ):
        vault = VaultResource(addr="http://fake-vault:8200", token="root")
        creds = vault.read_secret("minio")

    assert creds["access_key"] == "admin"
```

- `patch` intercepta `requests.get` solo dentro del `with`. Fuera del bloque, vuelve a la función real.
- `MagicMock()` simula cualquier objeto: podés definir `.json()`, `.raise_for_status()`, etc.

**Mockear Vault + boto3 juntos**

```python
from dagster import materialize
from lakehouse_dagster.assets.vault_demo.minio_check import minio_connectivity_check


def test_minio_connectivity_check_con_creds_validas():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"data": {"access_key": "admin", "secret_key": "password"}}
    }
    mock_resp.raise_for_status = MagicMock()

    mock_s3 = MagicMock()
    mock_s3.list_buckets.return_value = {
        "Buckets": [{"Name": "bronze"}, {"Name": "silver"}, {"Name": "gold"}]
    }

    with (
        patch(
            "lakehouse_dagster.resources.vault_resource.requests.get",
            return_value=mock_resp,
        ),
        patch(
            "lakehouse_dagster.assets.vault_demo.minio_check.boto3.client",
            return_value=mock_s3,
        ),
    ):
        result = materialize(
            [minio_connectivity_check],
            resources={
                "vault": VaultResource(addr="http://fake-vault:8200", token="root")
            },
        )

    assert result.success
    buckets = result.output_for_node("minio_connectivity_check")
    assert "bronze" in buckets
```

!!! warning
    El path del `patch` tiene que coincidir con **dónde se importa el símbolo**, no dónde está definido. Si `minio_check.py` hace `import boto3`, el patch va en `lakehouse_dagster.assets.vault_demo.minio_check.boto3.client`.

## PASO 1 — Smoke test de Definitions

Antes de testear assets individuales, asegurate de que Dagster puede cargar todo el grafo sin explotar.

```python
def test_definitions_cargan():
    from lakehouse_dagster.definitions import defs

    assert defs is not None
```

Si este test falla, hay un error de importación o configuración en algún asset, job o schedule. Es el primer test que conviene correr.

## PASO 2 — Correr los tests localmente

```bash
cd lakehouse_dagster
uv run --extra dev pytest -v
```

Resultado esperado:

```text
PASSED test_bronze_people_carga_csv
PASSED test_silver_people_agrega_columna
PASSED test_vault_resource_devuelve_secreto
PASSED test_minio_connectivity_check_con_creds_validas
PASSED test_definitions_cargan
5 passed in 1.54s
```

## PASO 3 — Verificar que corren en CI

El workflow `.github/workflows/python.yml` ya tiene el job `tests` activo:

```yaml
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

Push al repo y verificá en **GitHub → Actions → Python CI** que el job `tests` queda en verde junto a `lint`.

## Cuándo agregar más tests

| Situación | Patrón a usar |
|---|---|
| Nuevo asset de transformación | Invocación directa |
| Asset que lee archivo local | `materialize()` |
| Asset que llama a una API/servicio externo | Mock de `requests` o `boto3` |
| Refactor de un resource | Test unitario del resource directamente |
| Cambio en `definitions.py` | Smoke test de Definitions |

## Resultado esperado

Al finalizar este apéndice:

- 5 tests corriendo en menos de 2 segundos.
- CI verde sin necesitar Docker, Vault ni MinIO.
- Patrón claro para agregar tests a cualquier asset nuevo.
