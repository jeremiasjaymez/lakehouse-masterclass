#!/usr/bin/env bash
# Setup del entorno de la masterclass dentro del devcontainer.
# Equivale al Lab 0, pero automatizado: acá no hay que instalar WSL2 ni Docker.
set -euo pipefail

echo "==> Instalando uv"
curl -LsSf https://astral.sh/uv/0.11.14/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

echo "==> Instalando dependencias del proyecto (incluye docs)"
uv sync --group docs

echo "==> Preparando archivos de entorno"
[ -f .env ] || cp .env.example .env
if [ ! -f lakehouse_dagster/.env ]; then
  echo "DAGSTER_HOME=$(pwd)/.dagster" > lakehouse_dagster/.env
fi
mkdir -p .dagster data/silver data/gold

echo ""
echo "======================================================================"
echo " Entorno listo. El Lab 0 ya está hecho: tenés Python, Java y Docker."
echo ""
echo " Arrancá con:"
echo "   docker compose up -d          # MinIO + Nessie + Vault"
echo "   python src/spark/01_test_spark.py"
echo ""
echo " Para los labs de IA (9 y 11), instalá Ollama aparte:"
echo "   bash .devcontainer/setup-ollama.sh"
echo "======================================================================"
