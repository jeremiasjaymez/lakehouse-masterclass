# Instalar el grupo docs en el venv del proyecto
uv sync --group docs

# Despues correr
```bash
export NO_MKDOCS_2_WARNING=1

mkdocs build
mkdocs serve
```

# Info
El contenido de docs/site es autogenerado con el comando build, así que se ignora en git.