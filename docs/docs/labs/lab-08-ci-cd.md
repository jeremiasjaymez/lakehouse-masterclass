# LAB 8 - CI/CD: GitHub Actions para el Lakehouse

Objetivo: crear pipelines CI/CD que validen Terraform, ejecuten tests, validen Dagster y preparen despliegues automáticos del Lakehouse.

## ¿Por qué CI/CD desde el día 1?

Un Lakehouse "funciona en mi máquina" no es un Lakehouse, es un demo. CI/CD te da dos cosas críticas: **(1)** confianza para mergear cambios sin romper el pipeline de noche, y **(2)** documentación viva de cómo se construye y valida el sistema. GitHub Actions es gratis para repos públicos y open-source. Cuando el repo crezca, los mismos workflows se mueven a GitLab CI o Forgejo Actions sin grandes cambios.

## Objetivo del lab

- Crear workflows de GitHub Actions.
- Validar Terraform (fmt, init, plan).
- Lintear código Python (ruff).
- Validar assets de Dagster.
- Preparar pipeline para despliegues automáticos.

## Prerrequisitos

- LAB 0 a LAB 7 completados.
- Repositorio GitHub creado.
- Código del Lakehouse subido al repo.
- Terraform y Dagster funcionando localmente.

## Instalación y setup

GitHub Actions no requiere instalación local.
Solo necesitás:
`.github/workflows/`

### PASO 1 - Crear carpeta de workflows

**En la raíz del repo**

```bash
mkdir -p .github/workflows
```

### PASO 2 - Crear workflow para Terraform

**Archivo**

```text
.github/workflows/terraform.yml
```

- Este workflow valida que tu infraestructura es correcta antes de mergear.

### PASO 3 - Crear workflow para lint de Python

**Archivo**

```text
.github/workflows/python.yml
```

- Usa `ruff` para verificar estilo e imports sin usar.
- No requiere instalar dependencias del proyecto — corre en segundos.

### PASO 4 - Crear workflow para Dagster

**Archivo**

```text
.github/workflows/dagster.yml
```

- Instala todas las dependencias desde la raíz (`uv sync`) y monta el paquete Dagster encima.
- Ejecuta `dagster definitions validate` para verificar que todos los assets, jobs y schedules cargan sin errores.

!!! warning
    El comando corre **desde la raíz del repo**, no desde `lakehouse_dagster/`. Esto es intencional: el venv raíz tiene `pandas`, `pyspark` y demás dependencias que los assets importan.

### PASO 5 - Verificar que los workflows pasan

```bash
git add .github/
git commit -m "ci: add terraform, lint and dagster workflows"
git push
```

Ir a **GitHub → Actions** y verificar que los tres jobs quedan en verde.

### PASO 6 - Agregar badges al README

**En tu README.md**

```markdown
![Terraform](https://github.com/<USER>/<REPO>/actions/workflows/terraform.yml/badge.svg)
![Python CI](https://github.com/<USER>/<REPO>/actions/workflows/python.yml/badge.svg)
![Dagster](https://github.com/<USER>/<REPO>/actions/workflows/dagster.yml/badge.svg)
```

- Si todo está verde, tu Lakehouse es CI/CD-ready.

## Validación

- Terraform validado automáticamente
- Lint de Python ejecutado (ruff)
- Dagster definitions validadas
- Workflows funcionando en GitHub
- Badges agregados al README

## Código adicional opcional

- Cache de dependencias (ya incluido en el workflow de Dagster via `enable-cache: true` de `setup-uv`).
  Para activarlo también en otros jobs:

```yaml
- uses: astral-sh/setup-uv@v3
  with:
    python-version-file: "pyproject.toml"
    enable-cache: true
```

## Resultado esperado

- Al finalizar este lab, deberías tener:
- CI/CD completo para tu Lakehouse
- Validación automática de infraestructura (Terraform)
- Lint automático de código Python (ruff)
- Validación automática de pipelines (Dagster definitions)
- Base para agregar tests cuando los haya
- Base para despliegues automáticos

Este lab convierte tu Lakehouse en un sistema profesional y enterprise-ready.