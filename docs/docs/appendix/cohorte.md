# Guía de la cohorte (para el instructor)

Todo lo necesario para correr la masterclass como clase virtual: filtro de entrada,
pre-work, guion minuto a minuto de las 4 sesiones y Demo Day.

!!! tip "La idea de fondo"
    El material es gratis y público. Lo escaso es **tu tiempo**. Por eso la cohorte
    no se paga con plata: se paga con **compromiso demostrado**. El pre-work no es
    burocracia — es el filtro que hace que la clase funcione.

## Formato

| | |
|---|---|
| **Duración** | 4 sesiones de 2 h, una por semana |
| **Cupo** | 25 personas |
| **Precio** | Gratis, con postulación |
| **Requisito** | Pre-work verificado con capturas |
| **Entrega** | Capstone + Demo Day |
| **Certificado** | Solo para quienes entregan el capstone |

---

## 1. Formulario de postulación

Seis preguntas, tres minutos. Copiá esto a un Google Form.

> **Masterclass Lakehouse Open Source — Postulación**
>
> Son 4 sesiones de 2 h + un pre-work de ~1 h. El cupo es de 25 personas.
> El material es gratis y queda tuyo (Apache-2.0).
>
> 1. **Nombre y apellido** *(texto)*
> 2. **LinkedIn o GitHub** *(texto)*
> 3. **¿Qué hacés hoy?** Rol y años de experiencia en datos. *(texto)*
> 4. **¿Con qué stack trabajás?** Marcá lo que uses: *(múltiple)*
>    Spark · Databricks · Snowflake · BigQuery · dbt · Airflow · Dagster ·
>    Postgres/SQL · Ninguno todavía
> 5. **¿Qué querés construir después de esta masterclass?** *(texto largo)*
> 6. **¿Podés comprometerte a las 4 sesiones en vivo y a hacer el pre-work antes
>    de la primera?** *(Sí / No)*

!!! important "La pregunta que filtra es la 5"
    Las otras cinco son datos. La 5 te dice quién pensó dos minutos antes de
    postularse. Respuestas de una línea genérica ("aprender lakehouse") van al final
    de la lista; respuestas con un problema concreto ("quiero sacar a mi equipo de
    un warehouse propietario") entran primero.

    **No filtres por seniority.** Filtrá por intención.

---

## 2. Checklist de pre-work

Mandalo apenas confirmás la vacante, con **una semana de anticipación**.

> **Antes de la Sesión 1 — obligatorio**
>
> Son ~10 GB de descargas y una hora de tu tiempo. Si llegás sin esto hecho, la
> primera clase la vas a mirar en vez de hacerla.
>
> **Paso 1 — Setup base.** Seguí el [Lab 0](../labs/lab-00-setup-global.md) completo:
> WSL2 + Docker Desktop + uv + `uv sync`.
>
> **Paso 2 — Bajá las imágenes y los modelos:**
>
> ```bash
> docker compose pull
> ollama pull llama3.1
> ollama pull nomic-embed-text
> ```
>
> **Paso 3 — Cacheá los jars de Spark** (esto tarda 2-3 min la primera vez):
>
> ```bash
> python src/spark/01_test_spark.py
> ```
>
> **Paso 4 — Mandá TRES capturas** respondiendo este mail:
>
> ```bash
> docker compose up -d && docker ps    # captura 1: minio, nessie y vault corriendo
> ollama list                          # captura 2: los dos modelos
> python src/spark/01_test_spark.py    # captura 3: los números del 0 al 9
> ```
>
> **Sin las tres capturas no hay lugar en la cohorte.** No es un trámite: es lo que
> garantiza que las 2 h de clase se usen para aprender y no para debuggear setups.
>
> ¿Se te rompe algo? Abrí un issue en el repo o entrá por
> **GitHub Codespaces**, que te da el entorno andando en el navegador sin instalar nada.

!!! warning "Sostené la regla"
    Va a haber alguien que pida entrar sin el pre-work "porque lo hago el finde".
    Si cedés una vez, la Sesión 1 se te va en soporte técnico individual y perdés a
    los otros 24. La regla protege a la mayoría.

---

## 3. Guion de las 4 sesiones

### Reglas que se anuncian en el minuto 1

- **Cámara del instructor**: terminal a pantalla completa, fuente grande (16pt+).
- **Ellos ejecutan también.** No es una demo, es un taller.
- **Cero debugging individual en vivo.** Lo que se rompe va al canal; se resuelve
  en el office hours.
- **Todo se graba** y se comparte al día siguiente.

---

### Sesión 1 — Storage, formato y catálogo

*Bloques 1 y 2 del [runbook](student-runbook.md). Labs 1, 2 y 3.*

| Tiempo | Qué |
|---|---|
| 0:00-0:10 | **Empezá por el final.** Corré el RAG (`14_rag_answer_from_iceberg.py`) y mostrá el sistema terminado respondiendo con fuentes. "En 4 sesiones esto lo tenés vos." |
| 0:10-0:20 | Arquitectura: los 4 problemas (storage, formato de tabla, catálogo, compute) y qué pieza resuelve cada uno. |
| 0:20-0:45 | **MinIO**: levantar, crear buckets, subir el CSV. |
| 0:45-1:10 | **Iceberg**: crear tabla, insertar, ver snapshots. |
| 1:10-1:20 | ☕ Break |
| 1:20-1:35 | 🎯 **Momento click 1 — Time travel.** Consultar el snapshot viejo y ver que las filas nuevas no están. |
| 1:35-1:55 | 🎯 **Momento click 2 — Branching.** `04_nessie_commit_dev.py`: la misma tabla con `Jeremias` en `main` y `Jeremias DEV` en `dev`, al mismo tiempo. |
| 1:55-2:00 | Checkpoint y tarea. |

**Tarea**: dejar los checkpoints de los Bloques 1 y 2 en verde.

!!! note "El detalle que hace que la Sesión 2 funcione"
    Cuando en el Lab 2 consultes desde DuckDB con
    `iceberg_scan('s3://bronze/iceberg/warehouse/bronze_people')`, **detenete y
    señalá la incomodidad**: "estoy pasando una ruta, no un nombre de tabla".
    Nadie lo va a valorar hoy. En la Sesión 2 es el momento click más fuerte del curso.

---

### Sesión 2 — Compute y orquestación

*Bloques 3 y 4. Labs 4 y 5.*

| Tiempo | Qué |
|---|---|
| 0:00-0:10 | Checkpoint colectivo: "¿a quién le quedó rojo?" Se anota, no se debuggea. |
| 0:10-0:30 | 🎯 **Momento click 3 — El catálogo.** `05_attach_nessie_catalog.py`: DuckDB lista las tablas **por nombre**. Poné lado a lado la query de la Sesión 1 con la de ahora. Esa es la diferencia entre archivos sueltos y un Lakehouse. |
| 0:30-1:05 | **ETL bronze → silver** con Spark. Namespaces, `writeTo`, particionado. |
| 1:05-1:15 | ☕ Break |
| 1:15-1:50 | **Dagster**: assets, dependencias por nombre de parámetro, materialize, el grafo de lineage. |
| 1:50-2:00 | Checkpoint y tarea. |

**Tarea**: materializar `gold_people` y correr `pytest`.

---

### Sesión 3 — Secretos, licencias, IaC e IA

*Bloques 5 y 6. Labs 6, 7, 8 y 9.*

| Tiempo | Qué |
|---|---|
| 0:00-0:10 | Repaso rápido. |
| 0:10-0:35 | 🎯 **Momento click 4 — Vault.** `09_spark_with_vault.py` al lado de `utils.py`: las credenciales salieron del código fuente. |
| 0:35-0:55 | 🎤 **El bloque que te diferencia.** Abrí el `LICENSE` de Vault en vivo y leé `Licensor: International Business Machines Corporation`. BUSL vs open source, OpenBao y OpenTofu, y el cambio de una línea en el compose. |
| 0:55-1:05 | ☕ Break |
| 1:05-1:25 | **Terraform**: buckets y secreto declarativos, bloques `import`. |
| 1:25-1:50 | **IA**: embeddings de la bio guardados en Iceberg + SQL generator. Mostrá también un SQL generado **mal**. |
| 1:50-2:00 | Consigna del capstone. |

!!! success "Por qué el bloque de licencias va acá y no al final"
    Es tu contenido más memorable y el que más se comparte. Ponelo cuando todavía
    tenés atención, no en el minuto 110.

---

### Sesión 4 — RAG y Demo Day

*Bloque 7. Labs 10 y 11.*

| Tiempo | Qué |
|---|---|
| 0:00-0:25 | **RAG sobre la documentación del curso.** Primero sin RAG, después con RAG y fuentes. El lakehouse como vector store, sin vector DB. |
| 0:25-0:40 | Preguntas abiertas: qué cambia esto en producción. |
| 0:40-1:25 | 🏆 **Demo Day.** 8 demos de 5 min (anotate voluntarios en la Sesión 3). Cada uno comparte pantalla y muestra su pipeline andando. |
| 1:25-1:45 | Cierre: qué sigue (Polaris, Lakekeeper, streaming), cómo llevarlo a un cluster. |
| 1:45-2:00 | Certificados y networking. |

!!! important "El Demo Day es la pieza más importante del curso"
    No es un cierre simpático: es **la razón por la que la gente termina**. Saber que
    en 4 semanas tenés que mostrar tu pipeline funcionando delante de 25 colegas hace
    más por la tasa de finalización que cualquier precio de entrada.

    Anunciálo en la Sesión 1, no en la 3.

---

## 4. Después de la cohorte

- Subí las grabaciones: son el producto self-paced de la próxima edición.
- Pedí **un testimonio de una línea** a cada quien entregó capstone, el mismo día
  del Demo Day (después nadie contesta).
- Pasá las dudas del canal a **GitHub Discussions**: quedan indexadas y le sirven
  a la cohorte siguiente.
- Los que hicieron un capstone bueno son tus mejores candidatos a co-instructor.

## 5. Métricas que importan

| Métrica | Objetivo razonable |
|---|---|
| Postulaciones → aceptados | 40-60 % |
| Aceptados que completan el pre-work | > 80 % (si baja, el mail no es claro) |
| Asistencia Sesión 1 → Sesión 4 | > 60 % |
| Capstones entregados | > 40 % de los que empezaron |

Si la asistencia se cae entre la 2 y la 3, el problema casi siempre es que los
checkpoints quedaron rojos y la gente se sintió perdida. La solución no es más
contenido: es office hours entre esas dos sesiones.
