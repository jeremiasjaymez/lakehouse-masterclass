# Apéndice - Cómo documentar el proyecto

Este apéndice resume cómo mantener la documentación de esta masterclass sin interrumpir el recorrido principal de los labs.

## Cuándo conviene documentar

Documentar empieza a ser parte del trabajo técnico cuando el proyecto ya tiene:

- varios componentes o servicios;
- pasos manuales que otro integrante podría repetir mal;
- decisiones de arquitectura que conviene explicar una vez;
- un orden de aprendizaje que querés preservar.

En este repo, la documentación ya cumple esas cuatro condiciones.

## Estructura recomendada

La estructura actual busca separar navegación, contexto y contenido detallado:

- `docs/index.md`: portada corta.
- `docs/guide.md`: índice general de la masterclass.
- `docs/labs/`: un archivo por lab.
- `mkdocs.yml`: navegación y configuración del sitio.

Esta división hace que cada cambio sea más chico, más fácil de revisar y menos propenso a romper enlaces o duplicar contenido.

## Buenas prácticas para escribir labs

- Un lab por archivo.
- Un objetivo claro al comienzo.
- Prerrequisitos explícitos.
- Pasos en orden de ejecución real.
- Una sección de validación antes de cerrar.
- Un resultado esperado que deje claro cuándo el lab quedó completo.

Si un lab empieza a mezclar demasiados temas, conviene dividirlo antes de que se vuelva difícil de mantener.

## Buenas prácticas para MkDocs

En este proyecto, MkDocs funciona mejor cuando:

- la navegación en `mkdocs.yml` refleja la estructura real de `docs/`;
- cada página tiene un título claro;
- los bloques `note`, `tip`, `warning` e `important` se escriben con sintaxis de MkDocs;
- los enlaces internos son relativos al archivo actual;
- los bloques de código indican lenguaje cuando aplica.

Ejemplo de admonition:

```md
!!! note
    Este bloque se renderiza bien en Material for MkDocs.
```

## Flujo de trabajo recomendado

Para editar documentación sin romper el sitio:

1. Hacé el cambio en un archivo chico.
2. Revisá la navegación si agregaste o moviste páginas.
3. Ejecutá un build local.
4. Recién después seguí con el próximo cambio.

Comandos útiles:

```bash
./.venv-docs/bin/mkdocs build
./.venv-docs/bin/mkdocs serve
```

## Qué debería documentarse aparte

No todo merece vivir dentro de un lab. Conviene separar:

- apuntes de operación repetitiva;
- decisiones de arquitectura;
- convenciones del repo;
- troubleshooting frecuente;
- material de onboarding.

Si alguno de esos temas crece, puede transformarse en una nueva sección de documentación sin tocar la secuencia principal de labs.

## Criterio para seguir mejorando esta doc

La documentación va en la dirección correcta si:

- encontrar un lab lleva pocos clicks;
- cada página tiene un propósito claro;
- no hay contenido duplicado entre páginas;
- los pasos se pueden ejecutar en orden;
- el sitio compila sin warnings propios de navegación rota.

## Resultado esperado

Después de aplicar estas prácticas, deberías tener una documentación más fácil de navegar, mantener y extender a medida que la masterclass crece.